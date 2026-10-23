# syntax=docker/dockerfile:1.7
# Imagen común para los servicios Django de Suite UNAB (core, mapa-calor, estres-malla).
# Construir desde la raíz del repositorio:
#   docker build -f deploy/docker/django.Dockerfile --build-arg SERVICIO=core -t suite-unab/core .
ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

FROM base AS dependencias
ARG SERVICIO
COPY packages/suite-sso /opt/suite-sso
COPY services/${SERVICIO}/requirements.txt /tmp/requirements.txt
RUN pip install --prefix=/install -r /tmp/requirements.txt /opt/suite-sso

FROM base AS final
ARG SERVICIO
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION} \
    DJANGO_SERVICIO=${SERVICIO} \
    SUITE_DATA_DIR=/app/data \
    PORT=8000
RUN groupadd --system app && useradd --system --gid app --home /app app
COPY --from=dependencias /install /usr/local
COPY services/${SERVICIO}/ /app/
COPY data/ /app/data/
COPY deploy/docker/entrypoint.sh deploy/docker/asegurar_bd.py /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh \
 && DEBUG=True SECRET_KEY=collectstatic SUITE_SSO_SECRET=collectstatic-only-0123456789abcdef0123 \
    python manage.py collectstatic --noinput -v0 \
 && rm -f /app/db.sqlite3 && chown -R app:app /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/{os.environ.get(\"URL_PREFIX\",\"\")}salud/', timeout=4)"
ENTRYPOINT ["entrypoint.sh"]
CMD ["web"]
