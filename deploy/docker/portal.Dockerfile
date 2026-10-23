# syntax=docker/dockerfile:1.7
# Portal estático + gateway local (solo para docker-compose). En AWS el portal
# se publica en S3 + CloudFront y este contenedor no se usa.
FROM nginx:1.27-alpine
COPY services/portal/ /usr/share/nginx/html/
COPY deploy/nginx/gateway.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
