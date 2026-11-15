"""Protocolo de linha entre o Arduino e o gateway (texto, uma leitura por linha, terminada em \\n).

    P:A;N:128;S:432;T:27.5;U:61

    P  ponto de monitoramento (talhao). Opcional: sem P, o gateway usa o --talhao configurado.
    N  numero de sequencia do Arduino (0..65535, volta a 0). Opcional; serve para descartar reenvios.
    S  leitura BRUTA do sensor de umidade do solo (ADC do Arduino, 0..1023). Obrigatorio.
    T  temperatura do ar em graus Celsius (DHT11). Obrigatorio; "nan" quando o DHT11 falha.
    U  umidade relativa do ar em % (DHT11). Obrigatorio; "nan" quando o DHT11 falha.

CALIBRACAO PENDENTE: a conversao da leitura bruta do solo para % usa dois pontos PROVISORIOS (sensor no ar seco e
mergulhado em agua). O relatorio (secao 7.3) trata a calibracao por tipo de solo como etapa essencial: o grupo deve
medir os valores do sensor real e ajustar BRUTO_SECO e BRUTO_MOLHADO (ou passar --bruto-seco/--bruto-molhado).
"""
import math
from dataclasses import dataclass

BRUTO_SECO = 850     # PROVISORIO: valor tipico de sensor resistivo/capacitivo no ar seco
BRUTO_MOLHADO = 400  # PROVISORIO: valor tipico com o sensor na agua
ADC_MAXIMO = 1023
CAMPOS_OBRIGATORIOS = ("S", "T", "U")


class LinhaInvalida(ValueError):
    """Mensagem incompleta ou fora do formato."""


@dataclass(frozen=True)
class Calibracao:
    bruto_seco: float = BRUTO_SECO
    bruto_molhado: float = BRUTO_MOLHADO

    def para_percentual(self, bruto):
        """Converte a leitura bruta em % (linear entre os dois pontos; maior bruto = mais seco). Limita a 0..100."""
        percentual = (self.bruto_seco - bruto) / (self.bruto_seco - self.bruto_molhado) * 100
        return max(0.0, min(100.0, percentual))

    def para_bruto(self, percentual):
        """Inverso de para_percentual (usado so pelo gerador simulado)."""
        return round(self.bruto_seco - percentual / 100 * (self.bruto_seco - self.bruto_molhado))


def interpretar(linha):
    """Devolve um dicionario {P, N, S, T, U} com tipos convertidos, ou levanta LinhaInvalida."""
    texto = linha.strip()
    if not texto:
        raise LinhaInvalida("linha vazia")
    campos = {}
    for parte in texto.split(";"):
        if ":" not in parte:
            raise LinhaInvalida(f"trecho sem ':' ({parte!r})")
        chave, valor = parte.split(":", 1)
        chave, valor = chave.strip().upper(), valor.strip()
        if chave in campos:
            raise LinhaInvalida(f"campo {chave} repetido")
        campos[chave] = valor
    faltando = [c for c in CAMPOS_OBRIGATORIOS if c not in campos or campos[c] == ""]
    if faltando:
        raise LinhaInvalida("mensagem incompleta: falta " + ", ".join(faltando))
    try:
        resultado = {"S": int(campos["S"]), "T": float(campos["T"]), "U": float(campos["U"])}
        resultado["N"] = int(campos["N"]) if campos.get("N") else None
    except ValueError:
        raise LinhaInvalida("valor que não é número")
    resultado["P"] = campos.get("P") or None
    if not 0 <= resultado["S"] <= ADC_MAXIMO:
        raise LinhaInvalida(f"leitura bruta do solo fora de 0..{ADC_MAXIMO}")
    return resultado


def formatar(ponto, sequencia, bruto_solo, temperatura, umidade_ar):
    """Monta uma linha do protocolo (usado pelo gerador simulado e documentado para o sketch do Arduino)."""
    def numero(x):
        return "nan" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.1f}"
    partes = ([f"P:{ponto}"] if ponto else []) + ([f"N:{sequencia}"] if sequencia is not None else [])
    return ";".join(partes + [f"S:{bruto_solo}", f"T:{numero(temperatura)}", f"U:{numero(umidade_ar)}"])
