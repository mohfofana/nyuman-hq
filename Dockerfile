# Nyuman HQ : une seule image. L'interface React est construite, puis servie par le serveur FastAPI.

# 1) L'interface
FROM node:24-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

# 2) Le serveur
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    HQ_WEB_DIR=../web/dist \
    HQ_UPLOADS_DIR=/data/uploads

WORKDIR /app/api
COPY api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ ./
COPY --from=web /web/dist /app/web/dist

# Le serveur ne tourne pas en administrateur ; les captures des retours vont dans un volume.
RUN useradd --uid 1000 --create-home hq && mkdir -p /data/uploads && chown -R hq:hq /data
USER hq

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/sante', timeout=4)"

# Un seul worker : la présence et le direct sont en mémoire. Délai court à l'arrêt : les flux en direct se reconnectent seuls.
CMD ["uvicorn", "drivers.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", \
     "--proxy-headers", "--forwarded-allow-ips", "*", "--timeout-graceful-shutdown", "2"]
