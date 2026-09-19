# Referencia de opciones de la CLI del escáner de seguridad de OpenCloud

Esta página enumera todas las opciones del complemento, su valor
predeterminado y la variable de entorno correspondiente. Úsela para consultar
un ajuste; el [README principal](../../README.md) explica los flujos de trabajo
y ofrece ejemplos.

La prioridad entre las tres formas de definir cualquier ajuste es siempre la
misma: **opción de línea de comandos > variable de entorno > archivo de
configuración > valor predeterminado.** Consulte
[Archivo de configuración y secretos](../../README.md#configuration-file-and-secrets)
para el archivo y [Variables de entorno](../../README.md#environment-variables)
para las reglas de nomenclatura.

<!-- TOC -->
* [Referencia de opciones de la CLI](#cli-option-reference)
  * [Comando](#command)
  * [Opciones](#options)
  * [Ajustes sin opción propia](#settings-with-no-flag-of-their-own)
  * [Siguientes pasos](#where-to-go-next)
<!-- TOC -->


`check-opencloud-security -h` imprime la misma lista en el terminal.

## Comando {#command}
```shell
check-opencloud-security --host <Hostname> --check-hardening
```

## Opciones {#options}
| Opción                        | Descripción | Valor predeterminado | Variable de entorno |
|:------------------------------|:------------|:---------------------|:--------------------|
| `-H, --host`                  | Dirección o direcciones del servidor OpenCloud: nombre de host, IP o URL, opcionalmente con puerto. Admite una lista separada por comas para comprobar varios hosts en una ejecución | **obligatorio** | `COS_HOST` |
| `-P, --proxy`                 | Dirección del servidor proxy | *Ninguno* | `COS_PROXY` |
| `-d, --debug`                 | Explica la nota y cada hallazgo; registro detallado | *False* | `COS_DEBUG` |
| `-w, --warning`               | Nota (0-5) igual o inferior a la cual la comprobación emite una advertencia | `3` (`C`) | `COS_WARNING` |
| `-c, --critical`              | Nota (0-5) igual o inferior a la cual la comprobación es crítica | `1` (`E`) | `COS_CRITICAL` |
| `--check-hardening`           | Notifica también las medidas de refuerzo y cabeceras de seguridad ausentes | *False* | `COS_CHECK_HARDENING` |
| `--timeout`                   | Tiempo de espera HTTP en segundos por solicitud | `10` | `COS_TIMEOUT` |
| `--port`                      | Puerto en el que escucha la instancia (el proxy propio de OpenCloud usa `9200`) | el de `--host`, si no `443` | `COS_SCANNER_TARGET_PORT` |
| `--scheme`                    | `https` o `http`; `https` recurre automáticamente a `http` | `https` | `COS_SCANNER_SCHEME` |
| `--insecure`                  | No verifica el certificado TLS de la instancia | *False* | `COS_INSECURE` |
| `--ca-file`                   | Paquete de CA en PEM para verificar un certificado TLS interno | *Ninguno* (almacén de confianza del sistema) | `COS_SCANNER_TLS_CA_FILE` |
| `--no-extra-checks`           | Comprueba solo el producto, la versión y las cabeceras de seguridad | *False* | `COS_NO_EXTRA_CHECKS` |
| `--no-debug-ports`            | No sondea los puertos de depuración de OpenCloud | *False* | `COS_NO_DEBUG_PORTS` |
| `--all-addresses`             | Comprueba también la versión, las cabeceras, el refuerzo y las cuentas de demostración en cada dirección resuelta | *False* | `COS_ALL_ADDRESSES` |
| `--login-throttling`          | Envía seis inicios de sesión fallidos para una cuenta inexistente e informa si se limitaron (nunca se califica) | *False* | `COS_LOGIN_THROTTLING` |
| `--concurrency`               | Máximo de trabajadores de host en paralelo; se usa uno por host hasta este límite | `5` | `COS_CONCURRENCY` |
| `--format`                    | Formato de salida de una sola ejecución: `nagios`, `prometheus`, `otlp`, `checkmk`, `json`, `sarif` o `junit` | `nagios` | `COS_FORMAT` |
| `--prometheus-listen-port`    | Sirve `/metrics` de forma nativa en este puerto hasta que se detenga | desactivado | `COS_PROMETHEUS_LISTEN_PORT` |
| `--prometheus-listen-addr`    | Dirección de escucha del exportador nativo de Prometheus | `127.0.0.1` | `COS_PROMETHEUS_LISTEN_ADDR` |
| `--scrape-interval`           | Segundos que se guardan en caché los resultados del exportador (`0` analiza en cada scrape) | `60` | `COS_SCRAPE_INTERVAL` |
| `--ignore-hardening`          | Medida de refuerzo o comprobación que se acepta; repetible, separada por comas y admite comodines | *Ninguno* | `COS_SCANNER_IGNORE_HARDENINGS` |
| `--release-track`             | Canal de publicación que sigue esta instancia: `rolling`, `production`, `lts` o `auto` | `auto` | `COS_SCANNER_RELEASE_TRACK` |
| `--update-source`             | De dónde procede la versión más reciente: `auto`, `feed`, `pinned`, `bundled`, `off` | `auto` | `COS_UPDATE_SOURCE` |
| `--release-feed`              | URL del canal de versiones | API de versiones de GitHub de `opencloud-eu/opencloud` | `COS_RELEASES_FEED_URL` |
| `--release-token`             | Token para el canal de versiones (eleva el límite de frecuencia de GitHub) | *Ninguno* | `COS_RELEASES_TOKEN` |
| `--latest-version`            | Versión más reciente, indicada explícitamente; implica `--update-source pinned` | *Ninguno* | `COS_RELEASES_LATEST_VERSION` |
| `--no-update-check`           | Desactiva la comprobación de actualizaciones (igual que `--update-source off`) | *False* | `COS_NO_UPDATE_CHECK` |
| `--update-warning`            | Notifica WARNING cuando hay una versión más reciente disponible | *False* | `COS_UPDATE_WARNING` |
| `--eol-warning DÍAS`          | Notifica WARNING cuando la línea llega al fin de vida en DÍAS días o menos (`0` lo desactiva) | `0` | `COS_EOL_WARNING` |
| `--baseline`                  | Archivo que recuerda los hallazgos de la última ejecución, con una entrada por host | *Ninguno* | `COS_BASELINE` |
| `--warn-on-new`               | Solo alerta sobre hallazgos nuevos o peores que en la línea base; requiere `--baseline` | *False* | `COS_WARN_ON_NEW` |
| `--diff-format`               | Muestra los cambios respecto a la línea base como `text`, `markdown` o Slack Block Kit `slack`/`json` | `text` | `COS_DIFF_FORMAT` |
| `--self-update-check`         | Avisa cuando hay una versión más reciente del complemento en PyPI; nunca cambia el código de salida | *False* | `COS_SELF_UPDATE_CHECK` |
| `--webhook-url`               | Punto de acceso opcional al que se notifica cuando la comprobación alcanza el estado configurado | *Ninguno* (desactivado) | `COS_WEBHOOK_URL` |
| `--webhook-on`                | Estado mínimo que activa el webhook (`critical`, `warning`, `unknown`, `always`) | `critical` | `COS_WEBHOOK_ON` |
| `--webhook-format`            | Forma del cuerpo del webhook: `generic` (el JSON propio del complemento), `slack`, `discord`, `ntfy` o `gotify` | `generic` | `COS_WEBHOOK_FORMAT` |
| `--webhook-header`            | Cabecera adicional para la solicitud del webhook; repetible | *Ninguno* | `COS_WEBHOOK_HEADERS` |
| `--webhook-secret`            | Secreto compartido; firma cada cuerpo del webhook con HMAC-SHA256 en `X-COS-Signature` | *Ninguno* (sin firma) | `COS_WEBHOOK_SECRET` |
| `--webhook-timeout`           | Tiempo de espera HTTP en segundos para la llamada al webhook | `10` | `COS_WEBHOOK_TIMEOUT` |
| `--allow-private-webhooks`    | Permite webhooks a direcciones privadas, de loopback o de enlace local | *False* | `COS_ALLOW_PRIVATE_WEBHOOKS` |
| `--webhook-digest`            | Con varios destinos `--host`, envía un único webhook combinado en lugar de uno por host | *False* | `COS_WEBHOOK_DIGEST` |
| `--retries`                   | Número de reintentos ante errores de red transitorios | `2` | `COS_RETRIES` |
| `--backoff-factor`            | Factor de espera exponencial (segundos) entre reintentos | `0.5` | `COS_BACKOFF_FACTOR` |
| `--config`                    | Ruta del archivo de configuración (`.json` como JSON, si no YAML) | detección automática | `COS_CONFIG_FILE` |
| `--configure`                 | Pide los ajustes de forma interactiva, los guarda y termina | — | — |
| `--upgrade-self [run\|check]` | Actualiza el complemento con pipx, uv o pip y termina; `check` imprime el comando en lugar de ejecutarlo | `run` si se indica sin valor | — |
| `--check-only`                | Solo con `--upgrade-self`: otra forma de escribir `--upgrade-self check` | — | — |
| `-V, --version`               | Muestra la versión instalada y termina | — | — |
| `-h, --help`                  | Muestra la ayuda y termina | — | — |

## Ajustes sin opción propia {#settings-with-no-flag-of-their-own}

El margen de caducidad de TLS, la lista de puertos de depuración y las fuentes
de avisos de seguridad no tienen opción de línea de comandos. Se configuran
mediante el [archivo de configuración](../../README.md#configuration-file-and-secrets)
o sus variables de entorno `COS_SCANNER_*`, y
[`config/check-opencloud-security.example.yml`](../../config/check-opencloud-security.example.yml)
los enumera todos con un comentario.

## Siguientes pasos {#where-to-go-next}

| Página | Para qué |
|:-----|:----|
| [README principal](../../README.md) | Para qué sirve cada una de estas opciones, con ejemplos prácticos |
| [Archivo de configuración y secretos](../../README.md#configuration-file-and-secrets) | Definir lo mismo en un archivo |
| [Salida legible por máquina](../output-formats.md) | `--format json`, `sarif` y `junit` en detalle |
| [Checkmk](../checkmk.md) | `--format checkmk` y la ejecución del complemento desde un servidor Checkmk |
| [Comprobar un conjunto de instancias](../many-instances.md) | `--host` con muchos destinos y un archivo de configuración por instancia |
| [Solución de problemas](../troubleshooting.md) | La referencia de códigos de salida |
