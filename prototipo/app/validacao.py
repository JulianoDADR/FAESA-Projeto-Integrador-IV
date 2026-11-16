"""Validacao da entrada. Uma leitura invalida NUNCA chega ao classificador nem gera cor de semaforo."""
import math

from app.faixas import variaveis

ESPECIES = ("Arabica", "Conilon")
CAMPOS = ("especie", "umidade_solo", "temperatura", "umidade_ar")

# Faixas fisicamente plausiveis (nao sao faixas agronomicas), lidas de config/faixas.json.
LIMITES = {nome: (float(info["limite_fisico"][0]), float(info["limite_fisico"][1]), info["nome"], info["unidade"])
           for nome, info in variaveis().items()}


class ErroValidacao(Exception):
    def __init__(self, erros):
        super().__init__("; ".join(erros))
        self.erros = erros


def validar_leitura(dados):
    """Recebe o corpo da requisicao e devolve um dicionario limpo, ou levanta ErroValidacao."""
    if not isinstance(dados, dict):
        raise ErroValidacao(["Envie os dados da leitura em formato de objeto."])

    erros = []
    # Somente campos estruturados: qualquer texto livre extra e recusado (mitigacao de prompt injection).
    extras = sorted(str(k) for k in dados if k not in CAMPOS)
    if extras:
        erros.append("Campo não permitido: " + ", ".join(extras) + ". Só aceitamos espécie e as três leituras.")

    especie = dados.get("especie")
    if especie is None:
        erros.append("Falta informar a espécie (Arabica ou Conilon).")
    elif especie not in ESPECIES:
        erros.append("Espécie desconhecida. Use Arabica ou Conilon.")

    limpo = {"especie": especie}
    for campo, (minimo, maximo, nome, unidade) in LIMITES.items():
        valor = dados.get(campo)
        if valor is None:
            erros.append(f"Falta informar: {nome.lower()}.")
        elif isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor):
            erros.append(f"{nome} precisa ser um número.")
        elif not minimo <= valor <= maximo:
            erros.append(f"{nome} fora do possível ({minimo:g} a {maximo:g} {unidade}). Confira o sensor.")
        else:
            limpo[campo] = float(valor)

    if erros:
        raise ErroValidacao(erros)
    return limpo
