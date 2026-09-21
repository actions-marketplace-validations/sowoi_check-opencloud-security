# Comprobaciones de Content-Security-Policy

Una Content-Security-Policy (CSP) indica al navegador qué orígenes pueden
aportar scripts, estilos, marcos y otros contenidos. Una política bien
configurada puede limitar los efectos de contenido y scripts inyectados. El
escáner comprueba si la cabecera está presente y si su política de scripts
permite determinadas formas de ejecución insegura.

<!-- TOC -->
* [Content-Security-Policy: qué comprueba este escáner y por qué](#content-security-policy-what-this-scanner-checks-and-why)
  * [1. ¿Está presente la cabecera?](#1-is-the-header-present-at-all)
  * [2. ¿Es realmente restrictiva la política?: `cspWithoutUnsafeInline`](#2-is-the-policy-actually-restrictive-cspwithoutunsafeinline)
  * [Cómo corregirlo](#fixing-it)
  * [Gravedad y efecto en la nota](#severity-and-rating-impact)
<!-- TOC -->


## 1. ¿Está presente la cabecera? {#1-is-the-header-present-at-all}

`Content-Security-Policy` es una de las ocho cabeceras que se comprueban en
`setup.headers` (con `--check-hardening`, o siempre en el resultado web). Su
ausencia es un hallazgo por sí misma:

> Nada restringe desde dónde se pueden cargar scripts, estilos y marcos.

OpenCloud incluye una política de forma predeterminada, así que la falta de la
cabecera en una instancia en producción casi siempre significa que un proxy
inverso situado delante la ha eliminado, no que OpenCloud no la haya enviado.
Consulte [Proxies inversos](../reverse-proxy.md) para ver el conjunto de
cabeceras que busca esta comprobación, escrito para nginx, Apache, Caddy,
Traefik y HAProxy.

## 2. ¿Es realmente restrictiva la política?: `cspWithoutUnsafeInline` {#2-is-the-policy-actually-restrictive-cspwithoutunsafeinline}

Tener *una* cabecera CSP no es lo mismo que tener una útil. La comprobación de
refuerzo `cspWithoutUnsafeInline` lee la directiva `script-src` (o
`default-src` si falta `script-src`) y falla cuando contiene `unsafe-inline` o
`unsafe-eval`:

- **`unsafe-inline`** permite que el marcado inyectado o un manejador de
  eventos se ejecuten directamente, justo lo que una CSP pretende impedir.
- **`unsafe-eval`** permite que un fragmento ya presente en el código cargado
  convierta en código una entrada controlada por un atacante mediante `eval()`
  o el constructor `Function`.

**Esta comprobación falla en una instancia de OpenCloud estándar sin
modificar.** El `csp.yaml` predeterminado contiene `unsafe-inline` en
`script-src` y `style-src`, porque la interfaz web depende actualmente de
scripts y estilos en línea. La comprobación lo notifica en lugar de
excusarlo, pero corregirlo implica publicar una CSP propia y probar la
interfaz con ella; a diferencia de la mayoría de los hallazgos, por sí solo no
demuestra una configuración incorrecta.

Hay una excepción incorporada: una política que combina `unsafe-inline` con un
nonce o un hash (el patrón habitual de implantación de `strict-dynamic`)
**no** falla esta comprobación. Todos los navegadores que entienden los nonces
ignoran `unsafe-inline` cuando hay uno, así que la palabra clave solo sirve de
respaldo para navegadores demasiado antiguos para entender el nonce. Mantenerla
de esa forma es la manera recomendada por los organismos de estándares para
dar soporte a navegadores antiguos y nuevos con la misma cabecera.

## Cómo corregirlo {#fixing-it}

Apunte `PROXY_CSP_CONFIG_FILE_LOCATION` a un `csp.yaml` sin `unsafe-inline` ni
`unsafe-eval`, o use `PROXY_CSP_CONFIG_FILE_OVERRIDE_LOCATION` para sustituir
por completo la política predeterminada. Para seguir dando soporte a
navegadores antiguos, pase a una política basada en nonces o hashes con
`strict-dynamic` en lugar de eliminar `unsafe-inline` sin más. Pruébela antes:
la interfaz web depende actualmente de scripts y estilos en línea, así que una
política estricta probablemente romperá la interfaz y cualquier servicio de
ofimática o de identidad conectado hasta que se ajuste.

Referencia:
[variables de entorno del servicio proxy de OpenCloud](https://docs.opencloud.eu/docs/dev/server/services/proxy/environment-variables).

## Gravedad y efecto en la nota {#severity-and-rating-impact}

`cspWithoutUnsafeInline` es un indicador de refuerzo, que solo se notifica con
`--check-hardening` (o siempre en el resultado web), y por sí solo no limita la
nota como lo hace una entrada fallida de `extraChecks`; consulte
[Comprobaciones de refuerzo](../../README.md#hardening-checks) para ver en qué
se diferencian los indicadores de refuerzo de los hallazgos que limitan la
nota. El hallazgo de cabecera ausente es una comprobación adicional `header:` y
sí limita la nota cuando se usa `--check-hardening`; consulte la tabla de
comprobaciones adicionales en
[la guía de comprobaciones](../scanner-checks.md#what-the-scanner-checks).
