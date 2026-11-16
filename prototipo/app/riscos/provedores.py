"""Provedores de camadas de risco. Troque ProvedorSimulado por ProvedorReal quando houver fontes oficiais integradas."""
import json
import math
import zlib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

import numpy as np

CAMINHO_ORIENTACOES = Path(__file__).resolve().parent / "orientacoes.json"
FUSO = timezone(timedelta(hours=-3))

# Regioes de demonstracao. Coordenadas APROXIMADAS, escolhidas a mao so para centralizar o mapa.
REGIOES = {
    "serrana": {"id": "serrana", "nome": "Região serrana (Arábica)", "especie_principal": "Arabica",
                "municipios": ["Venda Nova do Imigrante", "Domingos Martins"],
                "centro": [-20.35, -40.92], "zoom": 10, "raio_km": 45},
    "norte": {"id": "norte", "nome": "Norte do Espírito Santo (Conilon)", "especie_principal": "Conilon",
              "municipios": ["São Mateus", "Linhares"],
              "centro": [-19.05, -40.00], "zoom": 9, "raio_km": 70},
}

# Cada tipo: cor, padrao do contorno (dashArray do Leaflet) e simbolo, para nao depender so de cor.
TIPOS = {
    "alagamento": {"nome": "Alagamento", "cor": "#1565C0", "padrao": None, "simbolo": "gota"},
    "chuvas_intensas": {"nome": "Chuvas intensas", "cor": "#6A1B9A", "padrao": "8 6", "simbolo": "nuvem"},
    "incendio": {"nome": "Incêndio", "cor": "#BF360C", "padrao": "2 6", "simbolo": "chama"},
    "deslizamento": {"nome": "Deslizamento de terra", "cor": "#5D4037", "padrao": "12 4 2 4", "simbolo": "encosta"},
    "pragas": {"nome": "Pragas", "cor": "#37474F", "padrao": "1 5", "simbolo": "inseto"},
}
NIVEIS = ["baixo", "medio", "alto"]
ROTULO_NIVEL = {"baixo": "Baixo", "medio": "Médio", "alto": "Alto"}

# "Por que esta marcado" (explicacao SIMULADA, sem diagnostico).
MOTIVOS = {
    "alagamento": "Área baixa, perto de curso d'água, com chuva acumulada na simulação.",
    "chuvas_intensas": "A simulação prevê chuva forte nas próximas horas nesta área.",
    "incendio": "Vários dias secos seguidos e vegetação seca na simulação.",
    "deslizamento": "Encosta íngreme com solo encharcado na simulação.",
    "pragas": "Época do ano e clima favoráveis a pragas do café na simulação (não é diagnóstico).",
}


@lru_cache(maxsize=1)
def carregar_orientacoes():
    return json.loads(CAMINHO_ORIENTACOES.read_text(encoding="utf-8"))


class ProvedorDeRiscos(ABC):
    nome = "abstrato"
    origem = "simulado"

    def regioes(self):
        return list(REGIOES.values())

    @abstractmethod
    def camadas(self, regiao_id, agora=None):
        """Devolve um GeoJSON FeatureCollection com as areas de risco da regiao."""


class ProvedorSimulado(ProvedorDeRiscos):
    """Areas de risco SIMULADAS, deterministicas por regiao e por dia (mesmo dia, mesmo mapa)."""
    nome = "simulado"
    origem = "simulado"

    def camadas(self, regiao_id, agora=None):
        regiao = REGIOES[regiao_id]
        agora = (agora or datetime.now(timezone.utc)).astimezone(FUSO)
        dia = agora.date().toordinal()
        gerador = np.random.default_rng([zlib.crc32(regiao_id.encode()), dia])
        lat0, lng0 = regiao["centro"]
        raio_graus = regiao["raio_km"] / 111.0
        atualizado = agora.replace(minute=0, second=0, microsecond=0)
        feicoes = []
        for tipo in TIPOS:
            for n in range(int(gerador.integers(2, 5))):
                distancia = raio_graus * math.sqrt(gerador.random()) * 0.85
                angulo = gerador.random() * 2 * math.pi
                clat = lat0 + distancia * math.sin(angulo)
                clng = lng0 + distancia * math.cos(angulo) / math.cos(math.radians(lat0))
                nivel = NIVEIS[int(gerador.choice(3, p=[0.45, 0.35, 0.20]))]
                feicoes.append({
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [self._poligono(gerador, clat, clng, raio_graus)]},
                    "properties": {
                        "id": f"{regiao_id}-{tipo}-{n + 1}", "tipo": tipo, "tipo_nome": TIPOS[tipo]["nome"],
                        "nivel": nivel, "nivel_rotulo": ROTULO_NIVEL[nivel], "motivo": MOTIVOS[tipo],
                        "atualizado_em": atualizado.isoformat(), "origem": "simulado",
                    },
                })
        return {"type": "FeatureCollection", "features": feicoes}

    @staticmethod
    def _poligono(gerador, clat, clng, raio_graus):
        """Poligono irregular fechado ao redor do centro (coordenadas GeoJSON: [lng, lat])."""
        tamanho = raio_graus * (0.06 + 0.10 * gerador.random())
        vertices = []
        for k in range(8):
            a = k / 8 * 2 * math.pi
            r = tamanho * (0.6 + 0.5 * gerador.random())
            vertices.append([round(clng + r * math.cos(a) / math.cos(math.radians(clat)), 5), round(clat + r * math.sin(a), 5)])
        return vertices + [vertices[0]]


class ProvedorReal(ProvedorDeRiscos):
    """ESBOCO, nao implementado. Fontes candidatas (a verificar) em docs/riscos_fontes_reais.md.

    Ao implementar: buscar alertas/areas por regiao no servidor (nunca com a coordenada do usuario), registrar a
    fonte e a data de cada camada, tratar falhas com o provedor simulado DESLIGADO (mostrar "dados indisponiveis",
    nunca dados simulados como se fossem reais) e respeitar as regras de uso de cada fonte.
    """
    nome = "real"
    origem = "oficial"

    def camadas(self, regiao_id, agora=None):
        raise NotImplementedError("ProvedorReal ainda não foi implementado: veja docs/riscos_fontes_reais.md")


_provedor = ProvedorSimulado()


def provedor_ativo():
    return _provedor
