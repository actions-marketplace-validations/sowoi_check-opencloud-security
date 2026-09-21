# Comprobaciones de divulgación de versión y ciclo de vida

Estas comprobaciones determinan si el escáner conoce la versión en ejecución y
si la instancia la publica en lugares innecesarios. Complementan la
[detección de fin de vida](../../README.md#end-of-life-detection) y la
comprobación de actualizaciones, que necesitan un número de versión fiable.

<!-- TOC -->
* [Divulgación de versión y ciclo de vida: qué comprueba este escáner y por qué](#version-and-lifecycle-disclosure-what-this-scanner-checks-and-why)
  * [1. ¿Se pudo determinar la versión en ejecución?: `versionDetection`](#1-could-the-running-version-be-determined-at-all-versiondetection)
  * [2. ¿Publica alguna cabecera de respuesta la versión?: `versionDisclosure:<header>`](#2-does-a-response-header-publish-the-version-versiondisclosureheader)
  * [3. ¿Publica el documento webfinger la versión?: `webfingerVersionDisclosure`](#3-does-the-webfinger-document-publish-the-version-webfingerversiondisclosure)
  * [Gravedad y efecto en la nota](#severity-and-rating-impact)
<!-- TOC -->


## 1. ¿Se pudo determinar la versión en ejecución?: `versionDetection` {#1-could-the-running-version-be-determined-at-all-versiondetection}

`/status.php` notifica hasta tres campos con forma de versión, y solo uno de
ellos es la versión real. Consulte
[Leer la versión correctamente](../scanner-checks.md#reading-the-version-correctly)
para saber qué son los otros dos y por qué existen, y
[Por qué OpenCloud sigue respondiendo a `/status.php`](../status-php.md) para
el origen del punto de acceso y de sus campos fijos. Esta comprobación falla
cuando falta `productversion` y solo se reciben los campos de compatibilidad
heredados `version`/`versionstring`.

Esto va más allá del propio hallazgo: sin una versión real no se puede
relacionar ningún aviso de seguridad ni determinar el estado de fin de vida o
de actualización. Un resultado sin este campo no está simplemente incompleto:
las comprobaciones que dependen de la versión no se han ejecutado, y un
informe que las diera por superadas afirmaría haber verificado algo que nunca
vio.

**Si falla:** compruebe si algo situado delante de la instancia reescribe o
elimina campos de la respuesta de `/status.php`, y si la versión es tan antigua
que realmente es anterior a la publicación de `productversion`. Hasta que se
reciba una versión real, trate todas las partes del resultado que dependen de
la versión como desconocidas, no como correctas.

## 2. ¿Publica alguna cabecera de respuesta la versión?: `versionDisclosure:<header>` {#2-does-a-response-header-publish-the-version-versiondisclosureheader}

En las cabeceras de respuesta `Server` y `X-Powered-By` se busca cualquier cosa
que parezca un número de versión (una cifra, un punto y otra cifra). Ninguna de
las dos es una vulnerabilidad por sí misma: solo indica a quien observa qué
avisos de seguridad probar primero. Por eso ambas se califican como `low` y no
con una gravedad mayor.

**Corrección:** elimine o simplifique la cabecera en el proxy inverso
(`server_tokens off` en Nginx, `ServerTokens Prod` en Apache) o suprímala por
completo. Consulte [Proxies inversos](../reverse-proxy.md) para la directiva
equivalente en Caddy, Traefik y HAProxy.

## 3. ¿Publica el documento webfinger la versión?: `webfingerVersionDisclosure` {#3-does-the-webfinger-document-publish-the-version-webfingerversiondisclosure}

Se solicita `/.well-known/webfinger` sin autenticación (como haría cualquier
cliente de federación) y se busca en su respuesta la versión en ejecución, del
mismo modo que en las dos cabeceras anteriores. Es la misma clase de hallazgo
que `versionDisclosure` (divulgación de información de gravedad baja, no una
vulnerabilidad), solo que se lee de un documento JSON en lugar de una cabecera.

**Corrección:** elimine la versión de la respuesta de webfinger en el proxy
inverso, o acepte la divulgación y dé prioridad a mantener la instancia
actualizada: la versión solo es información útil para un atacante mientras
siga sin corregirse un aviso de seguridad conocido para esa versión exacta.

## Gravedad y efecto en la nota {#severity-and-rating-impact}

Las tres son `extraChecks`, se notifican y limitan la nota en cada análisis:
`versionDetection` con gravedad `medium` (limita la nota a `A`) y las dos
comprobaciones de divulgación con `low` (la limitan a `A+`). Consulte la tabla
de comprobaciones adicionales en
[la guía de comprobaciones](../scanner-checks.md#what-the-scanner-checks).
Ninguna requiere `--check-hardening`, y ninguna equivale a la
[calificación de fin de vida](../../README.md#end-of-life-detection): una
versión actual y totalmente visible y una versión sin soporte y bien oculta se
evalúan en ejes completamente distintos.
