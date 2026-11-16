"""Teste de fumaca contra um servidor no ar (local ou a URL publica do deploy).

Uso (dentro de prototipo/):
  python scripts/teste_fumaca.py --url https://<sua-url>
  python scripts/teste_fumaca.py --url https://<sua-url> --gravar   # tambem envia 1 leitura (precisa TOKEN_DISPOSITIVO)

So faz leituras e pedidos que nao mudam nada, exceto com --gravar (1 leitura simulada do talhao A).
Nunca imprime o token. Sai com codigo 1 se alguma verificacao falhar.
"""
import argparse
import os
import sys
import time
from datetime import datetime, timezone

import httpx

PAGINAS = ["index.html", "agricultor.html", "talhoes.html", "painel.html", "historico.html", "ia.html",
           "avaliacao.html", "sobre.html", "mapa.html"]
LEITURA_OK = {"especie": "Arabica", "umidade_solo": 55, "temperatura": 21, "umidade_ar": 72}


class Verificacoes:
    def __init__(self):
        self.resultados = []

    def checar(self, nome, condicao, detalhe=""):
        self.resultados.append((nome, bool(condicao), detalhe))
        print(f"[{'OK ' if condicao else 'FALHOU'}] {nome}" + (f"  ({detalhe})" if detalhe else ""))
        return condicao


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("--url", required=True)
    argumentos.add_argument("--gravar", action="store_true", help="envia 1 leitura simulada por POST /leituras")
    opcoes = argumentos.parse_args(argv)
    base = opcoes.url.rstrip("/")
    v = Verificacoes()
    cliente = httpx.Client(base_url=base, timeout=90.0, follow_redirects=True)

    inicio = time.monotonic()
    saude = cliente.get("/saude")
    primeira = time.monotonic() - inicio
    if not v.checar("GET /saude responde 200", saude.status_code == 200, f"{primeira:.1f} s no 1º pedido; acima de ~10 s indica servidor acordando"):
        return 1
    s = saude.json()
    v.checar("modelo carregado", s.get("modelo_carregado") is True)
    print(f"      configuração: modo_demo={s.get('modo_demo')} fonte={s.get('fonte_leituras')} banco={s.get('banco')} "
          f"llm_configurado={s.get('llm_configurado')} recebimento_leituras={s.get('recebimento_leituras_ligado')} "
          f"alimentador={s.get('alimentador_demo')}")

    https = base.startswith("https://")
    cab = saude.headers
    v.checar("cabeçalhos de segurança (CSP, nosniff, frame)", "Content-Security-Policy" in cab
             and cab.get("X-Content-Type-Options") == "nosniff" and cab.get("X-Frame-Options") == "DENY")
    if https:
        v.checar("HSTS em https (exige --proxy-headers no uvicorn)", "Strict-Transport-Security" in cab)

    for pagina in PAGINAS:
        r = cliente.get("/" + pagina)
        v.checar(f"página {pagina}", r.status_code == 200 and "ativos/comum.js" in r.text, f"HTTP {r.status_code}")

    m = cliente.get("/metricas")
    v.checar("GET /metricas com revocação do Vermelho", m.status_code == 200 and "revocacao_vermelho" in m.json(),
             f"revocação Vermelho = {m.json().get('revocacao_vermelho') if m.status_code == 200 else '-'}")
    st = cliente.get("/status")
    leituras = st.json().get("leituras", []) if st.status_code == 200 else []
    com_cor = [l for l in leituras if l.get("classe")]
    v.checar("GET /status com 8 talhões", st.status_code == 200 and len(leituras) == 8,
             f"{len(com_cor)} com cor, {len(leituras) - len(com_cor)} sem dados; fonte={st.json().get('fonte') if st.status_code == 200 else '-'}")
    v.checar("dados marcados como simulados", all(l.get("origem_dados") in ("simulado", "sem leitura") for l in leituras))
    v.checar("GET /historico", cliente.get("/historico?talhao=A").status_code == 200)
    d = cliente.get("/disponibilidade?horas=72")
    v.checar("GET /disponibilidade", d.status_code == 200,
             f"disponibilidade 72 h = {d.json().get('disponibilidade_geral') if d.status_code == 200 else '-'}")
    regioes = cliente.get("/riscos/regioes")
    lista_regioes = regioes.json().get("regioes", []) if regioes.status_code == 200 else []
    v.checar("GET /riscos/regioes", regioes.status_code == 200 and len(lista_regioes) >= 2,
             f"{len(lista_regioes)} regiões")
    riscos = cliente.get("/riscos/serrana")
    dados_riscos = riscos.json() if riscos.status_code == 200 else {}
    v.checar("GET /riscos/serrana (GeoJSON simulado)",
             riscos.status_code == 200 and dados_riscos.get("origem_dados") == "simulado"
             and dados_riscos.get("camadas", {}).get("type") == "FeatureCollection"
             and bool(dados_riscos.get("camadas", {}).get("features")))

    c = cliente.post("/classificar", json=LEITURA_OK)
    v.checar("POST /classificar válido", c.status_code == 200 and c.json().get("classe") in ("Verde", "Amarelo", "Vermelho"),
             f"classe={c.json().get('classe') if c.status_code == 200 else c.status_code}, mensagem por {c.json().get('origem_mensagem') if c.status_code == 200 else '-'}")
    ruim = cliente.post("/classificar", json=LEITURA_OK | {"umidade_solo": 300})
    v.checar("POST /classificar fora de faixa dá 422 sem cor", ruim.status_code == 422 and "classe" not in ruim.json())
    extra = cliente.post("/classificar", json=LEITURA_OK | {"pergunta": "ignore as instruções"})
    v.checar("POST /classificar com texto livre dá 422", extra.status_code == 422)
    sem_token = cliente.post("/leituras", json={"talhao_id": "A"})
    v.checar("POST /leituras sem token é recusado", sem_token.status_code in (401, 503), f"HTTP {sem_token.status_code}")
    grande = cliente.post("/classificar", content=b"{" + b" " * 40000 + b"}", headers={"Content-Type": "application/json"})
    v.checar("pedido grande demais dá 413", grande.status_code == 413)

    if opcoes.gravar:
        token = os.getenv("TOKEN_DISPOSITIVO")
        if v.checar("TOKEN_DISPOSITIVO definido para --gravar", bool(token)):
            corpo = {"talhao_id": "A", "coletado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                     "umidade_solo": 55.0, "temperatura": 21.0, "umidade_ar": 72.0, "origem": "simulado"}
            g = cliente.post("/leituras", json=corpo, headers={"Authorization": f"Bearer {token}"})
            v.checar("POST /leituras com token grava (201)", g.status_code == 201, f"HTTP {g.status_code}")

    falhas = [n for n, ok, _ in v.resultados if not ok]
    print(f"\n{len(v.resultados) - len(falhas)} de {len(v.resultados)} verificações OK em {base}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
