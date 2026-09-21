# Solución de problemas del escáner de seguridad de OpenCloud

**`UNKNOWN: ... /status.php is unreachable`**
El complemento analiza la instancia directamente con su escáner incorporado,
así que el host de monitorización necesita llegar a ella. Compruebe que puede
conectarse y recuerde que el proxy propio de OpenCloud escucha en el puerto
**9200**, no en el 443: `--host opencloud.example.com:9200` o `--port 9200`.

**`UNKNOWN: No OpenCloud instance found at ...`**
`/status.php` no respondió con un documento de estado de OpenCloud. O bien en
esa dirección hay algo distinto de OpenCloud, o bien un proxy inverso situado
delante no reenvía `/status.php`. Ejecute con `--debug` para ver la respuesta.

**`UNKNOWN: ... is not an OpenCloud instance: /status.php reports ownCloud`**
ownCloud y Nextcloud sirven el mismo `/status.php` (OpenCloud heredó de ellos
ese punto de acceso), así que la dirección respondió, pero no en nombre de
OpenCloud. Sus versiones, avisos de seguridad y valores predeterminados de
refuerzo son distintos, y evaluarlos con el calendario de versiones de
OpenCloud daría una respuesta segura sobre el software equivocado, así que el
análisis se detiene en lugar de adivinar. Consulte
[Qué es OpenCloud y en qué se diferencia de ownCloud y Nextcloud](../what-is-opencloud.md#why-this-matters-for-a-security-scan)
para entender por qué los tres son lo bastante parecidos para compartir un
punto de acceso, pero no para compartir una nota.

**Errores de certificado en una instancia recién instalada**
`opencloud init` crea un certificado autofirmado. Use `--insecure` (la cadena
no fiable se sigue notificando, solo deja de restar en la nota) o coloque
delante de la instancia un proxy inverso con un certificado real.

**La versión parece incorrecta (`0.1.0`)**
Es el campo heredado fijo, no la versión real; consulte
[Leer la versión correctamente](../scanner-checks.md#reading-the-version-correctly).
El complemento notifica `legacyVersion` cuando la instancia no ofrece nada
mejor; se resuelve actualizando la instancia o permitiendo que el complemento
llegue a `/ocs/v1.php/cloud/capabilities`.

**Todas las rutas se notifican como expuestas**
Algo situado delante de la instancia responde `200` a todo, incluida la ruta
que el escáner consulta precisamente para detectarlo. Revise la regla de
respaldo del proxy inverso.

**Se notifica la falta de cabeceras de seguridad, aunque OpenCloud las envía**
Un proxy situado delante de la instancia las elimina o responde antes que
OpenCloud. [Proxies inversos](../reverse-proxy.md) contiene el conjunto de
cabeceras que busca esta comprobación, escrito para nginx, Apache, Caddy,
Traefik y HAProxy.

**La comprobación es lenta**
El sondeo de puertos de depuración cuesta hasta `debug_port_timeout` segundos
por puerto en un host protegido por cortafuegos. Use `--no-debug-ports`, reduzca
`COS_SCANNER_DEBUG_PORT_TIMEOUT`, acorte la lista de puertos o analice en
paralelo con `--concurrency` (consulte
[Acelerar el análisis](../scanner-checks.md#speeding-the-scan-up)).

**`UNKNOWN` en la comprobación de actualizaciones / límite de frecuencia de GitHub**
Las sesenta solicitudes anónimas a la API por hora y dirección IP se comparten
con todo lo demás que use esa dirección. Indique `--release-token`, o use
`--update-source bundled` / `pinned` para no acceder a la red.

**Docker: `permission denied while trying to connect to the Docker socket`**
El usuario que ejecuta Icinga2, cron o systemd necesita permiso para
comunicarse con el daemon de Docker: añádalo al grupo `docker` o ejecute la
comprobación mediante `sudo`, según su política de seguridad.

**No ocurre nada / no hay salida desde cron o systemd**
- Las unidades de cron y systemd no tienen por defecto el `PATH` ni el entorno
  de un shell de inicio de sesión: use la ruta completa de
  `check-opencloud-security` y defina `COS_HOST` explícitamente (consulte
  [Programación](../scheduling.md)).
- Revise los registros con `journalctl -u check-opencloud-security.service`
  (systemd) o en el archivo de registro que haya configurado (cron; consulte
  el archivo de cron de ejemplo).

**`--warn-on-new` informa OK aunque algo está claramente mal**
Para eso sirve: con una línea base, solo los hallazgos nuevos o peores que en
la ejecución anterior cambian el estado. El estado completo se sigue
imprimiendo, y la línea que empieza por `Suppressed by --warn-on-new:` indica
el estado que habría tenido la ejecución. Borre el archivo de línea base para
empezar de nuevo, o quite la opción para ver el estado real en cada ejecución.
El fin de vida es lo único que nunca suprime. Consulte
[Notificar solo lo que ha cambiado](../../README.md#reporting-only-what-changed).

**`--warn-on-new needs --baseline PATH`**
Sin un archivo en el que recordar la ejecución anterior, la opción informaría
de "nada nuevo" para siempre. Indique una ruta en la que pueda escribir el
usuario de monitorización, p. ej. `/var/lib/check_opencloud/baseline.json`.

**`Baseline could not be written`**
El directorio no existe y no se puede crear, o el usuario de monitorización no
puede escribir en él. El veredicto sobre la instancia no se ve afectado (esta
línea es la única consecuencia), pero hasta que se corrija no se recuerda
nada, así que `--warn-on-new` tratará cada ejecución como la primera.

**No aparece ninguna nota de `--self-update-check`**
El resultado se guarda en caché durante un día: borre
`${XDG_CACHE_HOME:-~/.cache}/check-opencloud-security/pypi-version.json` para
volver a consultar. Tampoco dice nada cuando PyPI no está disponible, cuando un
proxy lo bloquea o cuando la versión instalada es más reciente que la
publicada, que es lo normal en una copia de trabajo del código fuente. Nunca
cambia el código de salida.

**Referencia de códigos de salida**

| Código de salida | Significado |
|:----------|:-----------|
| `0`       | OK         |
| `1`       | WARNING    |
| `2`       | CRITICAL   |
| `3`       | UNKNOWN    |

**¿Sigue sin resolverse?** Abra una incidencia con la salida de `--debug` (los
tokens se ocultan en ella), usando la plantilla
[wrong finding](https://github.com/sowoi/check-opencloud-security/issues/new?template=wrong_finding.yml)
si la comprobación notificó algo que considera incorrecto. Nunca pegue un
nombre de host de producción ni una credencial en un hilo público; consulte
[CODE_OF_CONDUCT.md](../../CODE_OF_CONDUCT.md).

---

[Volver al índice de la documentación](../README.md) | [Volver al README principal](../../README.md)
