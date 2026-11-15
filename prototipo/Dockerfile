# Imagem do AgroAnálise (API + páginas). Construída a partir da pasta prototipo/.
#   docker build -t agroanalise .   &&   docker run -p 8000:8000 --env-file .env agroanalise
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
# O modelo é gerado no build, com a mesma versão do scikit-learn instalada acima (o .pkl versionado não entra na imagem).
RUN python ml/treinar.py --salvar

RUN useradd --create-home agro && mkdir -p dados && chown -R agro /app
USER agro

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"8000\")}/saude', timeout=4)"

# --proxy-headers: o IP real do visitante vem do X-Forwarded-For do provedor (usado no limite de pedidos e no https).
CMD ["sh", "-c", "uvicorn app.principal:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
