"""Fontes de leituras dos talhoes. As paginas consomem a API e nao sabem qual fonte esta ativa.

- FonteDeLeituras: interface.
- FonteSimulada: leituras SIMULADAS, deterministicas (mesmo passo => mesma leitura), sem estado no servidor.
- FonteBanco: leituras gravadas pelo gateway (Etapa 4).

O simulador anda em "passos": cada passo = 10 minutos de tempo simulado. O passo atual vem do relogio
(um passo a cada SEGUNDOS_POR_PASSO segundos reais); a interface pode pedir outro passo para pausar ou acelerar.
O modelo e simples e so serve para demonstrar: o solo seca aos poucos e e reposto em ciclos (como uma irrigacao
ou chuva, que o sistema NAO aciona), a temperatura sobe a tarde, a umidade do ar cai com o calor e ha dias com chuva.
"""
import math
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import numpy as np

SEMENTE = 2026
MINUTOS_POR_PASSO = 10
PASSOS_POR_DIA = 24 * 60 // MINUTOS_POR_PASSO
SEGUNDOS_POR_PASSO = 3

PROPRIEDADE = "Sítio Demonstração (fictício)"

# Parametros ilustrativos de cada ponto de monitoramento (nao representam lavouras reais).
#   solo_topo/solo_fundo: umidade do solo logo apos a reposicao e no fim do ciclo de secagem
#   ciclo: duracao do ciclo de secagem, em passos; fase: deslocamento do ciclo
#   temp_desvio/ar_desvio: microclima do ponto; instavel: sensor que cai de vez em quando
TALHOES = [
    {"id": "A", "nome": "Talhão A", "local": "Encosta sombreada", "especie": "Arabica",
     "solo_topo": 68, "solo_fundo": 44, "ciclo": 180, "fase": 0, "temp_desvio": -1.0, "ar_desvio": 4},
    {"id": "B", "nome": "Talhão B", "local": "Meia encosta", "especie": "Arabica",
     "solo_topo": 64, "solo_fundo": 30, "ciclo": 150, "fase": 40, "temp_desvio": 0.0, "ar_desvio": 0},
    {"id": "C", "nome": "Talhão C", "local": "Topo do morro", "especie": "Arabica",
     "solo_topo": 58, "solo_fundo": 16, "ciclo": 130, "fase": 90, "temp_desvio": 1.5, "ar_desvio": -6},
    {"id": "D", "nome": "Talhão D", "local": "Baixada úmida", "especie": "Arabica",
     "solo_topo": 80, "solo_fundo": 58, "ciclo": 200, "fase": 20, "temp_desvio": -0.5, "ar_desvio": 8},
    {"id": "E", "nome": "Talhão E", "local": "Lavoura nova", "especie": "Conilon",
     "solo_topo": 66, "solo_fundo": 38, "ciclo": 160, "fase": 10, "temp_desvio": 0.0, "ar_desvio": 0},
    {"id": "F", "nome": "Talhão F", "local": "Face norte, mais quente", "especie": "Conilon",
     "solo_topo": 60, "solo_fundo": 20, "ciclo": 120, "fase": 70, "temp_desvio": 3.0, "ar_desvio": -8},
    {"id": "G", "nome": "Talhão G", "local": "Perto do córrego", "especie": "Conilon",
     "solo_topo": 72, "solo_fundo": 45, "ciclo": 170, "fase": 110, "temp_desvio": -1.0, "ar_desvio": 5},
    {"id": "H", "nome": "Talhão H", "local": "Sensor com falhas", "especie": "Conilon",
     "solo_topo": 62, "solo_fundo": 36, "ciclo": 140, "fase": 55, "temp_desvio": 0.5, "ar_desvio": -2,
     "instavel": True},
]
CLIMA = {"Arabica": {"base": 21.0, "amplitude": 4.0}, "Conilon": {"base": 26.0, "amplitude": 4.5}}


def passo_atual(agora=None):
    agora = agora or datetime.now(timezone.utc)
    return int(agora.timestamp() // SEGUNDOS_POR_PASSO)


def hora_simulada(passo):
    minutos = (passo % PASSOS_POR_DIA) * MINUTOS_POR_PASSO
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


class FonteDeLeituras(ABC):
    """Contrato de qualquer fonte de leituras (simulada ou banco)."""
    nome = "abstrata"
    origem = "simulado"

    @abstractmethod
    def talhoes(self):
        """Lista de talhoes (id, nome, local, especie)."""

    @abstractmethod
    def leituras(self, passo=None):
        """Leitura mais recente de cada talhao. Valores ausentes = None (sensor sem dados)."""

    @abstractmethod
    def historico(self, talhao_id, horas=24, passo=None):
        """Uma leitura por hora, da mais antiga para a mais recente."""


class FonteSimulada(FonteDeLeituras):
    nome = "simulada"
    origem = "simulado"

    def __init__(self, semente=SEMENTE):
        self.semente = semente
        self._por_id = {t["id"]: t for t in TALHOES}

    def talhoes(self):
        return [{k: t[k] for k in ("id", "nome", "local", "especie")} | {"propriedade": PROPRIEDADE}
                for t in TALHOES]

    def _ruido(self, indice, passo):
        return np.random.default_rng([self.semente, indice, passo]).normal(0, 1, 3)

    def _choveu(self, passo):
        """Dia com chuva simulada (cerca de 1 em 3) entre 14h e 17h; devolve o passo de inicio ou None."""
        dia = passo // PASSOS_POR_DIA
        if np.random.default_rng([self.semente, 999, dia]).random() >= 0.35:
            return None
        inicio = dia * PASSOS_POR_DIA + 14 * 60 // MINUTOS_POR_PASSO
        return inicio if passo >= inicio else None

    def _sem_sinal(self, talhao, passo):
        # Sensor instavel: fica sem enviar dados em 1 de cada 5 janelas de 20 passos.
        return talhao.get("instavel", False) and (passo // 20) % 5 == 0

    def leitura(self, talhao_id, passo):
        talhao = self._por_id[talhao_id]
        indice = TALHOES.index(talhao)
        base = {"talhao_id": talhao_id, "especie": talhao["especie"], "passo": passo,
                "hora_simulada": hora_simulada(passo), "origem": self.origem}
        if self._sem_sinal(talhao, passo):
            return base | {"umidade_solo": None, "temperatura": None, "umidade_ar": None}

        ruido = self._ruido(indice, passo)
        # Solo: secagem linear dentro do ciclo, reposta no inicio de cada ciclo.
        k = (passo + talhao["fase"]) % talhao["ciclo"]
        solo = talhao["solo_topo"] - (talhao["solo_topo"] - talhao["solo_fundo"]) * k / talhao["ciclo"]
        # Clima: pico de temperatura por volta das 15h.
        clima = CLIMA[talhao["especie"]]
        hora = (passo % PASSOS_POR_DIA) * MINUTOS_POR_PASSO / 60
        temperatura = clima["base"] + talhao["temp_desvio"] + clima["amplitude"] * math.sin((hora - 9) / 24 * 2 * math.pi)
        ar = 80 + talhao["ar_desvio"] - 2.2 * (temperatura - clima["base"])
        # Chuva simulada: molha o solo (efeito que vai sumindo), esfria e umedece o ar.
        inicio_chuva = self._choveu(passo)
        if inicio_chuva is not None:
            desde = passo - inicio_chuva
            solo += 18 * math.exp(-desde / 36)
            if desde < 18:
                temperatura -= 3.5
                ar = max(ar, 93)
        return base | {
            "umidade_solo": round(float(np.clip(solo + 1.2 * ruido[0], 2, 98)), 1),
            "temperatura": round(float(np.clip(temperatura + 0.4 * ruido[1], 6, 41)), 1),
            "umidade_ar": round(float(np.clip(ar + 1.5 * ruido[2], 20, 99)), 1),
            "chovendo": inicio_chuva is not None and passo - inicio_chuva < 18,
        }

    def leituras(self, passo=None):
        passo = passo_atual() if passo is None else passo
        return [self.leitura(t["id"], passo) for t in TALHOES]

    def historico(self, talhao_id, horas=24, passo=None):
        passo = passo_atual() if passo is None else passo
        por_hora = 60 // MINUTOS_POR_PASSO
        return [self.leitura(talhao_id, passo - por_hora * (horas - 1 - i)) for i in range(horas)]


_fonte_ativa = FonteSimulada()


def fonte_ativa():
    return _fonte_ativa
