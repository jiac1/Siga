#!/bin/sh
# Punto de entrada de los contenedores Django.
#   web      servidor gunicorn (por defecto)
#   migrar   aplica migraciones y datos base (tarea única de ECS en cada despliegue)
#   *        cualquier otro comando (p. ej. "python manage.py shell")
set -e

# En AWS la contraseña de RDS llega como secreto separado (DB_PASSWORD) y se
# arma DATABASE_URL aquí, codificando caracteres especiales.
if [ -z "$DATABASE_URL" ] && [ -n "$DB_HOST" ]; then
  DATABASE_URL=$(python -c "import os,urllib.parse as u; print('postgres://%s:%s@%s:%s/%s?sslmode=require' % (u.quote(os.environ['DB_USER']), u.quote(os.environ['DB_PASSWORD'], safe=''), os.environ['DB_HOST'], os.environ.get('DB_PORT','5432'), os.environ['DB_NAME']))")
  export DATABASE_URL
fi
case "$DJANGO_SERVICIO" in
  mapa-calor) WSGI_MODULE=heatmap_project.wsgi ;;
  *)          WSGI_MODULE=config.wsgi ;;
esac

case "$1" in
  web)
    exec gunicorn "$WSGI_MODULE:application" \
      --bind "0.0.0.0:${PORT:-8000}" \
      --workers "${GUNICORN_WORKERS:-3}" \
      --threads "${GUNICORN_THREADS:-2}" \
      --timeout "${GUNICORN_TIMEOUT:-120}" \
      --access-logfile - --error-logfile - \
      --forwarded-allow-ips="${GUNICORN_FORWARDED_ALLOW_IPS:-*}"
    ;;
  migrar)
    case "$DJANGO_SERVICIO" in
      core)
        python /usr/local/bin/asegurar_bd.py
        python manage.py migrate --noinput
        python manage.py cargar_catalogo
        python manage.py inicializar_suite
        ;;
      estres-malla)
        python /usr/local/bin/asegurar_bd.py
        python manage.py migrate --noinput
        python manage.py inicializar_mallaiq
        ;;
      *) echo "mapa-calor no tiene base de datos: nada que migrar" ;;
    esac
    ;;
  *)
    exec "$@"
    ;;
esac
