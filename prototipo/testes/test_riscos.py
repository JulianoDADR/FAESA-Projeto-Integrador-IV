"""Etapa 3: mapa de riscos (modulo demonstrativo). Esquema do GeoJSON, orientacoes e privacidade da localizacao."""
import math
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app import explicacao, riscos

WEB = Path(__file__).resolve().parent.parent / "web"


@pytest.mark.parametrize("regiao", list(riscos.REGIOES))
def test_esquema_das_camadas_de_risco(cliente, regiao):
    d = cliente.get(f"/riscos/{regiao}").json()
    assert d["origem_dados"] == "simulado" and d["regiao"]["id"] == regiao
    assert "Dados simulados" in d["aviso"] and "199" in d["aviso"] and "193" in d["aviso"]
    camadas = d["camadas"]
    assert camadas["type"] == "FeatureCollection" and camadas["features"]
    assert {f["properties"]["tipo"] for f in camadas["features"]} == set(riscos.TIPOS)  # os 5 riscos aparecem
    centro, raio_km = d["regiao"]["centro"], d["regiao"]["raio_km"]
    for f in camadas["features"]:
        p = f["properties"]
        assert f["type"] == "Feature" and f["geometry"]["type"] == "Polygon"
        anel = f["geometry"]["coordinates"][0]
        assert len(anel) >= 4 and anel[0] == anel[-1]  # poligono fechado
        assert p["tipo"] in riscos.TIPOS and p["nivel"] in ("baixo", "medio", "alto")
        assert p["nivel_rotulo"] in ("Baixo", "Médio", "Alto") and p["motivo"] and p["origem"] == "simulado"
        datetime.fromisoformat(p["atualizado_em"])
        lng, lat = anel[0]
        distancia_km = math.dist((lat, lng), centro) * 111
        assert distancia_km < raio_km * 1.6  # dentro (aproximadamente) da regiao
    for tipo, info in d["tipos"].items():
        assert info["cor"].startswith("#") and info["simbolo"] and info["o_que_fazer"] and info["fonte_oficial"]


def test_camadas_sao_deterministicas_por_regiao_e_dia():
    provedor = riscos.ProvedorSimulado()
    dia = datetime(2026, 11, 15, 15, tzinfo=timezone.utc)
    assert provedor.camadas("serrana", dia) == provedor.camadas("serrana", dia)
    assert provedor.camadas("serrana", dia) != provedor.camadas("norte", dia)


def test_regiao_desconhecida_e_regioes(cliente):
    assert cliente.get("/riscos/marte").status_code == 404
    regioes = cliente.get("/riscos/regioes").json()["regioes"]
    assert {r["id"] for r in regioes} == set(riscos.REGIOES)
    assert all(len(r["centro"]) == 2 and r["raio_km"] > 0 and r["municipios"] for r in regioes)


def test_provedor_real_e_so_um_esboco():
    with pytest.raises(NotImplementedError):
        riscos.ProvedorReal().camadas("serrana")


# ---------- orientacoes: gerais, com fonte oficial, sem dose, produto ou manejo ----------
def test_toda_orientacao_tem_fonte_oficial_e_nenhuma_dose_produto_ou_manejo():
    orientacoes = riscos.carregar_orientacoes()
    assert set(orientacoes["tipos"]) == set(riscos.TIPOS)
    for tipo, info in orientacoes["tipos"].items():
        assert info["fonte_oficial"].strip(), tipo
        assert len(info["o_que_fazer"]) >= 2, tipo
        for texto in info["o_que_fazer"]:
            assert not explicacao._DOSE_VOLUME.search(texto), texto
            assert not explicacao._PRODUTOS.search(texto), texto
            assert not explicacao._MANEJO.search(texto), texto
            assert not re.search(r"\d", texto), texto  # nenhum numero (dose, volume, calendario) nas orientacoes


def test_numeros_de_emergencia_marcados_para_conferencia():
    emergencia = riscos.carregar_orientacoes()["emergencia"]
    assert emergencia["defesa_civil"] == "199" and emergencia["bombeiros"] == "193"
    assert emergencia["situacao"] in ("verificar", "confirmado") and emergencia["nota"]


# ---------- privacidade: a coordenada do usuario nao sai do navegador ----------
def test_mapa_so_chama_a_api_com_o_nome_da_regiao():
    html = (WEB / "mapa.html").read_text(encoding="utf-8")
    chamadas = re.findall(r"chamarApi\(([^)]*)\)", html)
    assert chamadas, "a página deveria chamar a API"
    for argumento in chamadas:
        assert not re.search(r"lat|lng|lon|coords|local|posicao", argumento, re.I), argumento
    assert "fetch(" not in html and "XMLHttpRequest" not in html and "sendBeacon" not in html
    assert "localStorage" not in html and "sessionStorage" not in html


def test_api_de_riscos_nao_aceita_coordenada(cliente):
    # nao ha rota por coordenada: um pedido com lat/lng nao muda nada nem e usado
    com = cliente.get("/riscos/serrana?lat=-20.3&lng=-40.9").json()
    sem = cliente.get("/riscos/serrana").json()
    assert com["camadas"] == sem["camadas"]
