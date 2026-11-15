"""Mapa de riscos da regiao: modulo DEMONSTRATIVO de contexto de risco (ampliacao de escopo, docs/AMPLIACAO_DE_ESCOPO.md).

- Os riscos NAO entram no classificador (que segue com as 3 variaveis).
- A API serve camadas por regiao_id, nunca por coordenada: a localizacao do usuario fica so no navegador.
- Dados SIMULADOS e deterministicos (semente por regiao); orientacoes gerais fixas em orientacoes.json.
"""
from app.riscos.provedores import (REGIOES, TIPOS, ProvedorDeRiscos, ProvedorReal, ProvedorSimulado,
                                   carregar_orientacoes, provedor_ativo)

__all__ = ["REGIOES", "TIPOS", "ProvedorDeRiscos", "ProvedorReal", "ProvedorSimulado", "carregar_orientacoes",
           "provedor_ativo"]
