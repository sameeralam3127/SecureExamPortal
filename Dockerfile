FROM node:20-alpine AS frontend-build

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
ARG VITE_API_BASE_URL=/api
ARG VITE_GOOGLE_CLIENT_ID=
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID
RUN npm run build


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=frontend-build /frontend/dist /usr/share/nginx/html
COPY docker/single-image-nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/start-single-image.sh /usr/local/bin/start-single-image.sh

RUN chmod +x /usr/local/bin/start-single-image.sh

EXPOSE 80

CMD ["/usr/local/bin/start-single-image.sh"]
