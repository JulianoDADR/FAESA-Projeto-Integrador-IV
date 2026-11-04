# Registro do uso de IA no desenvolvimento

Conforme a seção 11 do edital do Projeto Integrador IV, todo o processo de engenharia de software feito com apoio de IA é registrado aqui, com o prompt utilizado. Quem usa a IA faz o registro no mesmo commit do material gerado ou revisado.

## Modelo de registro

```markdown
## Registro de uso de IA — AAAA-MM-DD
- **Integrante:** Nome (usuário Git)
- **Ferramenta / modelo:**
- **Tarefa:**
- **Prompt utilizado:**
  > (colar o prompt completo)
- **Resultado (resumo):**
- **O que foi aproveitado / alterado:**
- **Como foi validado:**
- **Arquivos/commit relacionados:**
```

---

## Registro de uso de IA — 2026-11-04 (1/3): conferência do relatório C1 com o edital
- **Integrante:** Juliano Dantas (JulianoDADR)
- **Ferramenta / modelo:** Claude Code (Claude Sonnet 5.5)
- **Tarefa:** comparar o relatório do projeto com o edital do PI-IV e apontar lacunas para o C1.
- **Prompt utilizado:**
  > De acordo com o edital, meu relatório está correto da C1?
  > (anexos: o edital em PDF e o relatório em PDF)
- **Resultado (resumo):** lista de pontos conformes e de lacunas: componente de IA sem LLM, deploy e plataforma web não previstos, comunidade sem caracterização, área temática e ODS ausentes, falta de registro do uso de IA, commits de apenas 3 integrantes, marcador de merge no README e erros de numeração e sumário.
- **O que foi aproveitado / alterado:** todos os pontos viraram itens de correção do relatório e do repositório.
- **Como foi validado:** histórico de commits conferido diretamente no GitHub; revisão do grupo pendente.
- **Arquivos/commit relacionados:** relatório revisado em `docs/`.

## Registro de uso de IA — 2026-11-04 (2/3): redação dos textos complementares
- **Integrante:** Juliano Dantas (JulianoDADR)
- **Ferramenta / modelo:** Claude Code (Claude Sonnet 5.5)
- **Tarefa:** redigir os textos que faltavam: enquadramento e ODS, componente de IA, arquitetura de implantação, comunidade com dados oficiais, indicadores com metas, registro de uso de IA.
- **Prompt utilizado:**
  > Sim por favor
  > (resposta à oferta de redigir os textos complementares do relatório)
- **Resultado (resumo):** textos em português para as seções 1.1, 5.7, 6.4, 7.7, 8.4, 9.1 e 9.2, com pendências sinalizadas.
- **O que foi aproveitado / alterado:** textos incorporados ao relatório. As metas dos indicadores são propostas e devem ser ajustadas pelo grupo.
- **Como foi validado:** números da comunidade conferidos nos documentos de origem (apresentação da SEAG-ES e artigo da Revista Ifes Ciência). Conferência no SIDRA/IBGE e revisão do grupo: pendentes.
- **Arquivos/commit relacionados:** `docs/Relatorio_AgroAnalise_Projeto_Integrador_IV.docx`, `docs/fontes.md`.

## Registro de uso de IA — 2026-11-04 (3/3): montagem do relatório revisado e organização do repositório
- **Integrante:** Juliano Dantas (JulianoDADR)
- **Ferramenta / modelo:** Claude Code (Claude Sonnet 5.5)
- **Tarefa:** reconstruir o relatório em Word com as correções, gerar o PDF e organizar o repositório (README, fontes e registro de IA).
- **Prompt utilizado:**
  > Minha conta tá logada aqui no GitHub Desktop, também tenho acesso aos documentos do trabalho. Faça toda a C1
- **Resultado (resumo):** relatório em .docx e .pdf com numeração e sumário corrigidos; README sem o marcador de merge; pasta `docs/` com fontes e este registro.
- **O que foi aproveitado / alterado:** a ser conferido pelo grupo antes da entrega. Pendências marcadas em amarelo no relatório: recorte regional dos testes, participantes reais ou simulados e responsabilidades por integrante.
- **Como foi validado:** conferência visual do PDF gerado; revisão do grupo pendente.
- **Arquivos/commit relacionados:** commit que adiciona este registro.
