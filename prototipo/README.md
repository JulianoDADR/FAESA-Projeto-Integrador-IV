# AgroAnálise: protótipo navegável (C2)

Protótipo demonstrativo do semáforo de cafezais. **Todos os dados são simulados** (o Arduino ainda não está montado) e
**as faixas de Ideal/Atenção/Crítico são provisórias, não são parâmetros agronômicos validados.**

O classificador (Scikit-Learn) decide a classe; o LLM (GroqCloud) apenas reformula a mensagem. Sem chave ou com falha,
o sistema usa mensagens-padrão e o semáforo continua funcionando.

## Rodar em 5 comandos (a partir da pasta `prototipo/`)

```bash
python -m venv .venv && .venv\Scripts\activate      # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
python ml/treinar.py                                # gera dataset, modelo.pkl e metricas.json
uvicorn app.principal:app                           # sobe API + páginas
# abra http://localhost:8000
```

Atalho: `python executar_demo.py` treina se faltar o modelo e sobe o servidor.

## LLM (opcional)

Copie `.env.example` para `.env` e preencha `GROQ_API_KEY` (e, se quiser, `GROQ_MODELO`; padrão `llama-3.1-8b-instant`).
A chave nunca é gravada no código nem no repositório (`.env` está no `.gitignore`).
Sem chave, as respostas trazem `origem_mensagem: "padrao"`.

## Testes

```bash
python -m pytest -v
```

Nenhum teste usa a rede: o LLM é simulado com `monkeypatch`.

## Rotas

`GET /saude` · `POST /classificar` (`?simular_falha_llm=true` para mostrar o fallback) · `GET /metricas` · `GET /cenarios` · `GET /historico`

Páginas: `index`, `painel`, `historico`, `ia` (chama a API de verdade), `avaliacao`, `sobre`.

## Limites do protótipo

- Dados 100% simulados, com semente fixa; nenhuma medição real.
- Rótulos gerados por regras sobre as mesmas variáveis de entrada: as métricas validam o pipeline, não a eficácia em campo.
- Sem acionamento de irrigação, diagnóstico de doenças, recomendação agronômica, login, banco em nuvem ou deploy (C3).
- Sem dados pessoais.
