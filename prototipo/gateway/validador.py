"""Validacao das leituras no gateway (relatorio, secoes 7.3 e 10.2). Criterios documentados para serem reproduziveis:

1. mensagem incompleta ou fora do formato        -> descarta ("mensagem incompleta")
2. DHT11 devolveu nan                              -> descarta ("falha no DHT11")
3. leitura bruta do solo no extremo do ADC (<=5 ou >=1018): fio solto ou curto -> descarta ("sensor de solo desconectado")
4. valor fora do fisicamente possivel (config/faixas.json, limite_fisico) -> descarta ("fora da faixa")
5. mesmo numero de sequencia N ja visto para o ponto (reenvio)            -> descarta ("duplicada")
6. salto maior que o limite em relacao a mediana das ultimas 5 leituras validas do ponto -> descarta ("oscilacao abrupta").
   Se o salto se repetir em CONFIRMACOES_DE_NOVO_NIVEL leituras seguidas, o novo nivel e aceito (mudanca real,
   como uma chuva forte), para o ponto nao ficar descartando para sempre.

A mediana (NumPy) evita que uma unica leitura ruim anterior "contamine" a comparacao.
"""
import json
import math
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from gateway.protocolo import Calibracao, LinhaInvalida, interpretar

_CONFIG = json.loads((Path(__file__).resolve().parent.parent / "config" / "faixas.json").read_text(encoding="utf-8"))
LIMITES_FISICOS = {v: tuple(info["limite_fisico"]) for v, info in _CONFIG["variaveis"].items()}
SALTO_MAXIMO = {"umidade_solo": 25.0, "temperatura": 8.0, "umidade_ar": 30.0}
JANELA_MEDIANA = 5
CONFIRMACOES_DE_NOVO_NIVEL = 3
ADC_EXTREMO_BAIXO, ADC_EXTREMO_ALTO = 5, 1018


@dataclass
class Resultado:
    valida: bool
    motivo: str = ""
    leitura: dict = field(default_factory=dict)


class Validador:
    def __init__(self, calibracao=None, talhao_padrao=None, talhoes_conhecidos=None):
        self.calibracao = calibracao or Calibracao()
        self.talhao_padrao = talhao_padrao
        self.talhoes_conhecidos = set(talhoes_conhecidos) if talhoes_conhecidos else None
        self._recentes = defaultdict(lambda: deque(maxlen=JANELA_MEDIANA))
        self._sequencias = defaultdict(lambda: deque(maxlen=32))
        self._saltos_seguidos = defaultdict(int)

    def validar(self, linha):
        try:
            bruto = interpretar(linha)
        except LinhaInvalida as erro:
            return Resultado(False, f"mensagem incompleta ({erro})")
        ponto = bruto["P"] or self.talhao_padrao
        if not ponto:
            return Resultado(False, "mensagem incompleta (sem ponto de monitoramento)")
        if self.talhoes_conhecidos is not None and ponto not in self.talhoes_conhecidos:
            return Resultado(False, f"ponto desconhecido ({ponto})")
        if math.isnan(bruto["T"]) or math.isnan(bruto["U"]):
            return Resultado(False, "falha no DHT11 (nan)")
        if bruto["S"] <= ADC_EXTREMO_BAIXO or bruto["S"] >= ADC_EXTREMO_ALTO:
            return Resultado(False, "sensor de solo desconectado ou em curto")

        leitura = {"talhao_id": ponto, "umidade_solo": round(self.calibracao.para_percentual(bruto["S"]), 1),
                   "temperatura": round(bruto["T"], 1), "umidade_ar": round(bruto["U"], 1)}
        for variavel, (minimo, maximo) in LIMITES_FISICOS.items():
            if not minimo <= leitura[variavel] <= maximo:
                return Resultado(False, f"fora da faixa ({variavel}={leitura[variavel]})")

        if bruto["N"] is not None:
            if bruto["N"] in self._sequencias[ponto]:
                return Resultado(False, "duplicada (mesmo número de sequência)")
            self._sequencias[ponto].append(bruto["N"])

        recentes = self._recentes[ponto]
        if len(recentes) >= 3:
            mediana = np.median(np.array([[r[v] for v in SALTO_MAXIMO] for r in recentes]), axis=0)
            salto = next((v for i, v in enumerate(SALTO_MAXIMO) if abs(leitura[v] - mediana[i]) > SALTO_MAXIMO[v]), None)
            if salto:
                self._saltos_seguidos[ponto] += 1
                if self._saltos_seguidos[ponto] < CONFIRMACOES_DE_NOVO_NIVEL:
                    return Resultado(False, f"oscilação abrupta ({salto})")
                recentes.clear()  # o salto se confirmou: novo nivel real
        self._saltos_seguidos[ponto] = 0
        recentes.append(leitura)
        return Resultado(True, leitura=leitura)
