# El comando check-opencloud-scanner

El paquete instala dos comandos.

- **`check-opencloud-security`** es el complemento de monitorización. Analiza
  una instancia, *juzga* el resultado con umbrales y termina con `0`-`3` para
  Nagios o Icinga. Sus opciones están en la
  [referencia de opciones de la CLI](../cli-reference.md).
- **`check-opencloud-scanner`** es todo lo demás. Ofrece el documento de
  resultado sin procesar, compara dos de ellos, explica un hallazgo, actualiza
  los datos de referencia y ejecuta el servicio de análisis. Nunca aplica un
  umbral de advertencia ni crítico.

Esta página es la referencia del segundo.

<!-- TOC -->
* [El comando `check-opencloud-scanner`](#the-check-opencloud-scanner-command)
  * [Opciones globales](#global-options)
  * [`scan`: imprimir el documento de resultado](#scan---print-the-result-document)
  * [`diff`: qué ha cambiado entre dos resultados guardados](#diff---what-changed-between-two-saved-results)
  * [`explain`: qué significa un hallazgo y cómo corregirlo](#explain---what-a-finding-means-and-how-to-fix-it)
  * [`refresh-data`: actualizar el calendario de versiones y los avisos de seguridad](#refresh-data---update-the-release-schedule-and-advisories)
  * [`serve`: el servicio de análisis](#serve---the-scan-service)
  * [`configure`: escribir un archivo de configuración](#configure---write-a-configuration-file)
  * [Códigos de salida](#exit-codes)
<!-- TOC -->


## Opciones globales {#global-options}

Van **antes** del subcomando:

```bash
check-opencloud-scanner -c /etc/check-opencloud-security/config.yml -v scan opencloud.example.com
```

| Opción | Qué hace |
|:--|:--|
| `-c, --config` | Archivo de configuración. `.json` se lee como JSON, cualquier otra cosa como YAML |
| `-v, --verbose` | Más registro en stderr: `-v` para información, `-vv` para depuración |

Sin `-c`, se usa el primer archivo que exista, en este orden:

1. `./.env.json`
2. `./check-opencloud-security.yml`
3. `./check-opencloud-security.yaml`
4. `~/.config/check-opencloud-security/.env.json`
5. `/etc/check-opencloud-security/.env.json`
6. `/etc/check-opencloud-security/config.yml`
7. `/etc/check-opencloud-security/config.yaml`

Es la misma búsqueda que hace el complemento. Las variables de entorno `COS_`
se aplican por encima del archivo, y las opciones por encima de ambos.
Consulte [Secretos en la configuración](../configuration.md).

## `scan`: imprimir el documento de resultado {#scan-print-the-result-document}

```bash
check-opencloud-scanner scan opencloud.example.com
check-opencloud-scanner scan --compact opencloud.example.com > result.json
check-opencloud-scanner scan cloud1.example.com cloud2.example.com | jq '.[].rating'
```

Imprime el documento de resultado JSON del escáner: la nota y su explicación,
el ciclo de vida, cada comprobación, TLS y las coincidencias con avisos de
seguridad, todo con claves en camelCase. No imprime ningún veredicto. Un host
imprime un objeto. Varios hosts imprimen un array, en el orden indicado.

| Opción | Qué hace |
|:--|:--|
| `--compact` | Imprime el documento en una línea en lugar de con sangría |
| `--scheme {https,http}` | Cómo llegar a la instancia |
| `--port` | Sustituye el puerto |
| `--timeout` | Segundos permitidos para cada solicitud |
| `--insecure` | No verifica el certificado TLS de la instancia |
| `--ca-file` | Paquete de CA en PEM con el que verificar un certificado interno |
| `--no-extra-checks` | Solo producto, versión y cabeceras |
| `--no-debug-ports` | No sondea los puertos de depuración de OpenCloud |
| `--all-addresses` | Repite las comprobaciones clave en cada dirección a la que se resuelve el nombre |
| `--concurrency` | Sondeos en paralelo dentro de un análisis. Predeterminado `1` |
| `--no-update-check` | No busca la versión de OpenCloud más reciente |

Las exclusiones, el canal de publicación y las fuentes de avisos proceden del
archivo de configuración o del entorno, exactamente igual que en el
complemento.

Una instancia que no se puede analizar no interrumpe la ejecución. Su entrada
pasa a ser `{"host": ..., "error": ...}`, los demás hosts se siguen analizando
y el comando termina con `1`:

```json
{
  "host": "opencloud.example.com",
  "error": "https://opencloud.example.com/status.php is unreachable"
}
```

El documento es lo que consumen las [canalizaciones de CI](../ci.md) y
[Prometheus](../prometheus.md), y lo que compara `diff`, descrito más abajo. El
[README de la biblioteca del escáner](../../opencloud_local_scan/README.md)
describe sus campos.

## `diff`: qué ha cambiado entre dos resultados guardados {#diff-what-changed-between-two-saved-results}

```bash
check-opencloud-scanner scan opencloud.example.com > before.json
# ... change something on the instance ...
check-opencloud-scanner scan opencloud.example.com > after.json
check-opencloud-scanner diff before.json after.json
```

```text
opencloud.example.com: 2026-09-15 17:42:21.524291 -> 2026-09-15 17:42:22.737103
New since last run (15): check:debugEndpoint:/config, check:debugEndpoint:/debug/pprof/, check:debugEndpoint:/metrics, check:demoUsersDisabled, check:directoryListing (+10 more)
Security check: + debugEndpoint:/config
Security check: + demoUsersDisabled
...
Hardening: + Content-Security-Policy
...
Rating: A+ (5) -> D (2)
```

Lee dos archivos y no analiza nada. `+` marca un hallazgo que ha aparecido,
`-` uno que se ha resuelto y `~` uno que sigue abierto pero ahora pesa de otra
manera. También notifica cualquier cambio en la nota, la
versión y el horizonte de soporte. Responde a "¿ha funcionado la corrección?"
y "¿qué ha cambiado la actualización?" sin mantener un archivo de línea base.
Para una comprobación que recuerda por sí misma su última ejecución, consulte
[Notificar solo lo que ha cambiado](../baseline.md).

| Opción | Qué hace |
|:--|:--|
| `--format text` | Líneas legibles, como arriba. Es el valor predeterminado |
| `--format markdown` | Una tabla Markdown, para una incidencia o un comentario en una pull request |
| `--format side-by-side` | Los dos análisis en dos columnas, un hallazgo por fila |
| `--format json` | La comparación estructurada que lleva el webhook del complemento |
| `--format slack` | JSON de Slack Block Kit |
| `--category NOMBRE` | Mostrar solo un área. Se puede repetir |
| `--all-findings` | Listar todos los hallazgos medidos, no solo los que se movieron |
| `--exit-zero` | Termina siempre con `0` |
| `--allow-different-hosts` | Compara resultados de dos instancias distintas |

**Termina con `1` cuando el segundo resultado es peor**, así que una
canalización puede condicionarse a él. Termina con `0` cuando nada ha
empeorado, también cuando solo se han resuelto hallazgos. `--exit-zero`
desactiva ese control.

Termina con `2`, sin comparar nada, cuando no puede dar una respuesta honesta:

- **los dos archivos describen instancias distintas.** "¿Ha funcionado la
  corrección?" es una pregunta sobre una sola instancia, y dos hosts comparados
  por error dan una respuesta equivocada que nadie nota. Use
  `--allow-different-hosts` si es lo que pretendía.
- **un archivo no es un documento de resultado** de `scan`. Por ejemplo, no
  tiene nota, o es la entrada de error de una instancia que no se pudo
  analizar.

### Severidad, hallazgo por hallazgo {#severity-finding-by-finding}

Cada comparación termina con los hallazgos fallidos contados por severidad:

```text
~ exposed:/config/opencloud.yaml [exposure]: severity high -> critical
Failing by severity: critical 0 -> 1, high 1 -> 1, medium 0 -> 1, low 1 -> 0
```

La línea `~` es lo que una comparación de dos listas de nombres no puede producir. Un control que fallaba en `high` y ahora falla en `critical` nunca entra ni sale del conjunto de controles fallidos, así que [la línea base](../baseline.md) calla al respecto - con razón, porque según su definición nada ha empeorado -, mientras que la calificación que ese control limita ha bajado un grado. La severidad de cada lado procede de los propios documentos, nunca del catálogo de hoy: un análisis archivado el mes pasado es prueba sobre el mes pasado.

Un hallazgo exceptuado se cuenta aquí y se muestra como `waived`, porque una excepción es la decisión de no recibir alertas y no la afirmación de que el hallazgo haya desaparecido.

### Lado a lado {#side-by-side}

```bash
check-opencloud-scanner diff before.json after.json --format side-by-side
```

```text
opencloud.example.com
Rating: A+ (5) -> C (3)
Lifecycle: EOL: False -> True
Version: 3.4.0 -> 3.3.0

Finding                           2026-09-15T17:42:21+00:00  2026-09-22T09:03:11+00:00
--------------------------------  -------------------------  -------------------------
+ CVE-2026-0001                   not listed                 FAIL high
+ cspWithoutUnsafeInline          ok                         FAIL medium
~ exposed:/config/opencloud.yaml  FAIL high                  FAIL critical
- Referrer-Policy                 FAIL low                   ok
```

Cada fila indica ambos lados, de modo que quien lee no tiene que reconstruirlos a partir de una lista de cambios. `--all-findings` añade los hallazgos que no se movieron, lo que convierte la vista de «qué ha cambiado» en «qué encontraron los dos análisis».

`not measured` y `not listed` son respuestas distintas y nunca se mezclan: un control ausente de un documento no se realizó ([ADR 0064](https://github.com/sowoi/check-opencloud-security/blob/main/adr/0064-a-scan-records-what-it-did-not-measure.md)), mientras que un aviso ausente no afectaba a esa versión. Ninguno de los dos es un resultado correcto.

### Un área cada vez {#one-area-at-a-time}

`--category` acota la comparación y toma un valor de uno de dos espacios de nombres:

- **una categoría de hallazgo** - `cookies`, `authentication`, `sharing`, `exposure`, `embedding`, `lifecycle`, `proxy`, `headers`, `transport`, `advisory` - conserva solo los hallazgos sobre esa área de la instancia.
- **una categoría de cambio** - `instance`, `referenceData`, `scanner`, `policy`, `unknown` - conserva solo la explicación de *por qué* difieren los dos análisis. Véase [Datos de referencia](reference-data.md) para saber por qué una calificación puede moverse sin que la instancia haya cambiado.

```bash
check-opencloud-scanner diff before.json after.json --category transport
check-opencloud-scanner diff before.json after.json --category instance
```

Cada espacio de nombres se filtra solo cuando se le da un valor, así que `--category transport` deja intacta la explicación y `--category instance` deja intactos los hallazgos. La opción se puede repetir, y un valor desconocido se rechaza con el código de salida `2` en lugar de no mostrar nada: una errata que imprimiera una comparación vacía se leería como «no ha cambiado nada».

Una explicación filtrada omite las líneas `[limitation]`, porque estas matizan la comparación entera y no una de sus categorías.

## `explain`: qué significa un hallazgo y cómo corregirlo {#explain-what-a-finding-means-and-how-to-fix-it}

```bash
check-opencloud-scanner explain basicAuthDisabled
```

```text
basicAuthDisabled: HTTP Basic authentication is enabled
    The instance answers with a 'WWW-Authenticate: Basic' challenge, so usernames and passwords can be replayed on every request without going through the identity provider, ...
    Setting: PROXY_ENABLE_BASIC_AUTH
    Fix: Set PROXY_ENABLE_BASIC_AUTH=false (the default) if nothing needs it. ...
    Docs: https://docs.opencloud.eu/docs/dev/server/services/proxy/environment-variables
```

Busca los identificadores en el catálogo incluido en el paquete. Es el mismo
texto que muestran la salida `--debug` del complemento, el resultado del
análisis y la aplicación web. No lee ninguna configuración, no necesita red y
no analiza nada, así que funciona en cualquier host donde esté instalado el
paquete.

```bash
check-opencloud-scanner explain cspWithoutUnsafeInline Referrer-Policy   # several at once
check-opencloud-scanner explain exposed:/config/opencloud.yaml          # parameterised ids too
check-opencloud-scanner explain --list                                  # every identifier, one per line
check-opencloud-scanner explain --list --category cookies               # one category
check-opencloud-scanner explain --format json cookieSecure              # for a script
check-opencloud-scanner explain                                         # the whole catalogue
```

| Opción | Qué hace |
|:--|:--|
| `--list` | Imprime solo los identificadores en lugar de las explicaciones |
| `--category` | Solo una categoría: `cookies`, `authentication`, `sharing`, `exposure`, `embedding`, `lifecycle`, `proxy`, `headers` o `transport` |
| `--format {text,json}` | JSON devuelve `id`, `category`, `title`, `meaning`, `remediation`, `reference`, `setting` y `actionable` para cada entrada |

Un identificador que el catálogo no conoce termina con `1` y sugiere los más
parecidos:

```text
ERROR check_opencloud.cli: No catalogue entry for 'cookieSecur'. Did you mean: cookieSecure, cookieSameSite, cookiePrefix? Run `explain --list` for every identifier this build knows.
```

Los identificadores son los que llevan los hallazgos en la línea de alerta, en
`extraChecks[].id` y en `hardenings`, y los que nombra una exclusión. Para un
tratamiento más extenso, página a página, consulte
[Medidas de refuerzo, una por una](../hardening.md) y
[Qué lee el escáner](../scanner-checks.md).

## `refresh-data`: actualizar el calendario de versiones y los avisos de seguridad {#refresh-data-update-the-release-schedule-and-advisories}

```bash
check-opencloud-scanner refresh-data --output-dir /var/lib/check-opencloud-security
```

Descarga del repositorio de este proyecto el calendario de versiones y la
base de datos de avisos revisados, verifica su firma y los escribe en
`--output-dir`. Imprime las dos rutas y termina con `0`. Ante cualquier fallo
no escribe nada y termina con `1`.

| Opción | Valor predeterminado | Qué hace |
|:--|:--|:--|
| `--output-dir` | `~/.cache/check-opencloud-security` | Dónde se guardan los dos archivos |
| `--timeout` | `30` | Segundos permitidos para cada solicitud |
| `--schedule-url` | *(ninguno)* | Una página de ciclo de vida o réplica, descargada sin verificar |
| `--advisory-url` | *(ninguno)* | Un punto de acceso OSV o réplica, descargado sin verificar |

Los archivos no tienen efecto hasta que la configuración apunta a ellos. La
comprobación de firma necesita el extra `signing`. Hay una trampa fácil de
pasar por alto: un archivo de calendario que la comprobación no puede leer
desactiva la comprobación de fin de vida. Todo esto se explica en
[Mantener al día el calendario de versiones y los avisos de seguridad](../reference-data.md).

## `serve`: el servicio de análisis {#serve-the-scan-service}

```bash
check-opencloud-scanner serve
check-opencloud-scanner serve --listen 0.0.0.0 --token "$(cat /run/secrets/scanner_token)"
```

Ejecuta el escáner como un pequeño servicio HTTP, para que varios
consumidores compartan un resultado en caché por instancia en lugar de que
cada uno la vuelva a analizar.

| Opción | Valor predeterminado | Ajuste |
|:--|:--|:--|
| `--listen` | `127.0.0.1` | `service.listen` / `COS_SERVICE_LISTEN` |
| `--port` | `8811` | `service.port` / `COS_SERVICE_PORT` |
| `--cache-ttl` | `900` segundos | `service.cache_ttl` / `COS_SERVICE_CACHE_TTL` |
| `--token` | *(ninguno)* | `service.token` / `COS_SERVICE_TOKEN` |
| `--concurrency` | `1` | Sondeos en paralelo dentro de un análisis |
| `--insecure` | desactivado | No verifica los certificados de las instancias analizadas |

**Escuchar en cualquier interfaz que no sea loopback sin un token impide el
arranque.** Imprime `UNKNOWN: ...` en stderr y termina con `3`, un código que
un supervisor no reiniciará una y otra vez. Los puntos de acceso se enumeran
en el [README principal](../../README.md#running-the-scanner-as-a-service), y
su ejecución en un contenedor se explica en
[Ejecutar el escáner como servicio](../scan-service.md).

No es la aplicación web pública. Esa es
[el servicio público de análisis](../webapp.md).

## `configure`: escribir un archivo de configuración {#configure-write-a-configuration-file}

```bash
check-opencloud-scanner configure
check-opencloud-scanner -c /etc/check-opencloud-security/.env.json configure
```

Pide los ajustes de forma interactiva, explica cada uno y los guarda como
JSON, legible solo por el propietario. Ofrece `./.env.json`,
`~/.config/check-opencloud-security/.env.json` y
`/etc/check-opencloud-security/.env.json`, todos ellos lugares que la búsqueda
anterior encuentra automáticamente. `-c` indica otra ruta. Es el mismo
asistente que `check-opencloud-security --configure`.

| Opción | Qué hace |
|:--|:--|
| `--all` | Recorre los ajustes opcionales sin preguntar antes |
| `--force` | Sustituye un archivo existente sin pedir confirmación |
| `--no-test-scan` | No ofrece un análisis de prueba del host antes de guardar |

## Códigos de salida {#exit-codes}

**No** son los códigos de Nagios del complemento. Un `scan` que encuentra una
instancia con nota F sigue terminando con `0`, porque juzgar el resultado es
tarea del complemento.

| Subcomando | `0` | `1` | `2` | `3` |
|:--|:--|:--|:--|:--|
| `scan` | Se han analizado todos los hosts | Al menos un host no se pudo analizar | Configuración no válida | - |
| `diff` | Nada ha empeorado | El resultado posterior es peor | Los archivos no se pueden comparar | - |
| `explain` | Impreso | Identificador desconocido o categoría vacía | - | - |
| `refresh-data` | Se han escrito ambos archivos | No se ha escrito nada; consulte stderr | - | - |
| `serve` | Detenido con normalidad | - | Configuración no válida | Se negó a arrancar, p. ej. escucha amplia sin token |

Los argumentos de línea de comandos no válidos terminan con `2` en todos los
subcomandos, como es habitual en argparse.
