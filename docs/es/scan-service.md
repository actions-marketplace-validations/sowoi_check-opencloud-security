# Ejecutar el escáner de OpenCloud como servicio HTTP local

Ejecute `check-opencloud-scanner serve` para ofrecer el escáner incorporado como
un servicio HTTP permanente. Así, varios consumidores pueden compartir un
resultado almacenado en caché para cada instancia. El
[README principal](../../README.md#running-the-scanner-as-a-service) enumera
los puntos de acceso y los requisitos del token; esta guía trata el
despliegue.

**No** se trata de la aplicación web pública: esa es
[el servicio de análisis](../webapp.md), que recibe una URL de cualquier
persona, la pone en cola y muestra la respuesta.

<!-- TOC -->
* [Ejecutar el escáner como servicio](#running-the-scanner-as-a-service)
  * [En un contenedor](#in-a-container)
  * [El archivo compose de monitorización](#the-monitoring-compose-file)
<!-- TOC -->


## En un contenedor {#in-a-container}

Sin un token, el servicio se niega a escuchar en cualquier interfaz que no sea
la de loopback. En un contenedor esto implica dos ajustes: escuchar en las
interfaces del contenedor para que el puerto publicado llegue al proceso, y
definir el token que lo permite.

```shell
docker run -d --name opencloud-scanner -p 127.0.0.1:8811:8811 \
  -e COS_SERVICE_LISTEN=0.0.0.0 \
  -e COS_SERVICE_TOKEN="$(openssl rand -hex 32)" \
  --entrypoint check-opencloud-scanner \
  check-opencloud-security serve

curl -H "Authorization: Bearer <token>" \
  'http://127.0.0.1:8811/api/scan?url=opencloud.example.com'
```

## El archivo compose de monitorización {#the-monitoring-compose-file}

El archivo ya preparado
[`docker/docker-compose.monitoring.yml`](../../docker/docker-compose.monitoring.yml)
inicia el escáner y un contenedor de comprobación, con comprobación de estado
y secretos de Docker incluidos:

```shell
# 1. create the secret files from the templates
cp secrets/scanner_token.example  secrets/scanner_token
cp secrets/releases_token.example secrets/releases_token

# 2. fill them with real values
openssl rand -hex 32 > secrets/scanner_token          # protects the service
printf '%s' '<github-token>' > secrets/releases_token
chmod 600 secrets/scanner_token secrets/releases_token

# 3. adjust COS_HOST in docker/docker-compose.monitoring.yml, then:
cd docker
docker compose -f docker-compose.monitoring.yml up -d scanner
docker compose -f docker-compose.monitoring.yml run --rm check
```

En cambio, un simple `docker compose up` en ese directorio inicia la aplicación
web pública; consulte [la aplicación web](../webapp.md). Configúrela con
**`docker/setup-wizard.py`** en lugar de editar un archivo compose: el asistente
pregunta en qué dirección debe estar disponible el servicio, con qué intensidad
puede analizar, quién puede borrar un resultado y qué termina TLS delante del
servicio. Después escribe un archivo compose comentado, un `.env` con la
contraseña de Redis y todas las demás credenciales a las que hace referencia
ese archivo y, si indica uno, la configuración correspondiente de nginx,
Apache, Caddy o Traefik. Es un único archivo Python que solo usa la biblioteca
estándar, así que funciona en un host que únicamente tenga Docker; consulte
[`docker/README.md`](../../docker/README.md#setting-up-the-whole-stack).

Todo lo que hay en `secrets/`, salvo las plantillas `*.example`, está excluido
de git; consulte [`secrets/README.md`](../../secrets/README.md).
