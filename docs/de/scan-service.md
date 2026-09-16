# Run the OpenCloud scanner as a local HTTP service

# Den Scanner als HTTP-Dienst betreiben

`check-opencloud-scanner serve` betreibt den eingebauten Scanner als dauerhaften HTTP-Dienst. Mehrere lokale Anwendungen können dadurch ein zwischengespeichertes Ergebnis gemeinsam nutzen. Das [Haupt-README](../../README.md#running-the-scanner-as-a-service) beschreibt die Endpunkte und die Tokenpflicht beim Lauschen außerhalb von Loopback. Hier geht es um die Bereitstellung.

Für einen Dienst mit Browseroberfläche und Warteschlange verwenden Sie die separate [Webanwendung](../webapp.md).

## Im Container {#in-a-container}

Außerhalb von Loopback startet der Dienst nur mit einem Token. Im Container sind daher zwei Einstellungen nötig: Der Prozess muss auf den Container-Schnittstellen lauschen, damit der veröffentlichte Port ihn erreicht, und ein Token muss die Zugriffe schützen.

```shell
docker run -d --name opencloud-scanner -p 127.0.0.1:8811:8811 \
  -e COS_SERVICE_LISTEN=0.0.0.0 \
  -e COS_SERVICE_TOKEN="$(openssl rand -hex 32)" \
  --entrypoint check-opencloud-scanner \
  check-opencloud-security serve

curl -H "Authorization: Bearer <token>" \
  'http://127.0.0.1:8811/api/scan?url=opencloud.example.com'
```

## Die Compose-Datei für Monitoring {#the-monitoring-compose-file}

[`docker/docker-compose.monitoring.yml`](../../docker/docker-compose.monitoring.yml) startet den Scanner und einen Check-Container mit Healthcheck und Docker-Secrets:

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

Ein einfaches `docker compose up` in diesem Verzeichnis startet dagegen die [öffentliche Webanwendung](../webapp.md). Für deren Einrichtung steht **`docker/setup-wizard.py`** bereit. Der Assistent fragt Adresse, Scanlimits, Löschberechtigungen und TLS-Terminierung ab. Er schreibt eine kommentierte Compose-Datei, eine `.env` mit den benötigten Zugangsdaten und auf Wunsch die Konfiguration für nginx, Apache, Caddy oder Traefik. Er benötigt Python und dessen Standardbibliothek; zusätzliche Python-Pakete sind nicht erforderlich. Näheres steht im [Docker-README](../../docker/README.md#setting-up-the-whole-stack).

Git ignoriert im Verzeichnis `secrets/` alle Dateien außer den Vorlagen `*.example`. Details finden Sie im [Secrets-README](../../secrets/README.md).

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
