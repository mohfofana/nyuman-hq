# Nyuman HQ : un seul conteneur pour le serveur et le site.
# 1) on compile le site, 2) on le sert avec le serveur Python.

FROM node:22-alpine AS site
WORKDIR /web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
COPY server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY server/ ./
COPY --from=site /web/dist ./web_dist

# Le site compilé et les fichiers envoyés (montés sur un disque qui survit aux mises à jour).
ENV HQ_WEB_DIR=/app/web_dist HQ_UPLOAD_DIR=/data/uploads
RUN mkdir -p /data/uploads
EXPOSE 8030
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8030", "--proxy-headers", "--forwarded-allow-ips", "*"]
