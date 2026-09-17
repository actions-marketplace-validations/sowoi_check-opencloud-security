# Comprobaciones de atributos de cookies

El escáner examina las cabeceras `Set-Cookie` de las respuestas públicas en
busca de cuatro protecciones de cookies. Lee los atributos que definen
OpenCloud o su proxy inverso y no conserva los valores de las cookies.

Si la respuesta no define ninguna cookie, estas comprobaciones se omiten. Una
comprobación que no se ha realizado no se notifica como superada.

<!-- TOC -->
* [Atributos de cookies: qué comprueba este escáner y por qué](#cookie-attributes-what-this-scanner-checks-and-why)
  * [1. ¿Exige la cookie HTTPS?: `cookieSecure`](#1-does-the-cookie-require-https-cookiesecure)
  * [2. ¿Pueden leer la cookie los scripts de la página?: `cookieHttpOnly`](#2-can-page-scripts-read-the-cookie-cookiehttponly)
  * [3. ¿Se envía la cookie en solicitudes entre sitios?: `cookieSameSite`](#3-is-the-cookie-sent-on-cross-site-requests-cookiesamesite)
  * [4. ¿Lleva el nombre de la cookie un prefijo?: `cookiePrefix`](#4-does-the-cookie-name-carry-a-prefix-cookieprefix)
  * [Gravedad y efecto en la nota](#severity-and-rating-impact)
<!-- TOC -->


## 1. ¿Exige la cookie HTTPS?: `cookieSecure` {#1-does-the-cookie-require-https-cookiesecure}

Una cookie sin `Secure` se enviará por una conexión HTTP sin cifrar si el
navegador llega a abrir una con el mismo host: basta con un enlace `http://`
perdido, una redirección mixta o un portal cautivo. En ese momento, la cookie
atraviesa la red en texto claro y cualquiera que la haya visto puede
reutilizarla.

**Corrección:** defina `Secure` en todas las cookies que emitan el proxy
inverso o la aplicación. Si la instancia termina TLS en un proxy inverso, suele
tratarse de la cookie de sesión o CSRF del propio proxy y no de una que defina
OpenCloud; consulte [Proxies inversos](../reverse-proxy.md) para el conjunto de
cabeceras que lee esta comprobación.

## 2. ¿Pueden leer la cookie los scripts de la página?: `cookieHttpOnly` {#2-can-page-scripts-read-the-cookie-cookiehttponly}

Sin `HttpOnly`, los scripts que se ejecutan en la página pueden leer una cookie
mediante `document.cookie`. En las cookies de sesión, esto aumenta el impacto
de un script inyectado. Algunos diseños de tokens CSRF requieren
deliberadamente acceso desde JavaScript, así que evalúe la finalidad de la
cookie antes de cambiar el atributo.

**Corrección:** use `HttpOnly` en las cookies que los scripts no necesitan
leer, sobre todo en las de sesión. Confirme los requisitos de la aplicación
antes de aplicar el atributo a todas las cookies.

## 3. ¿Se envía la cookie en solicitudes entre sitios?: `cookieSameSite` {#3-is-the-cookie-sent-on-cross-site-requests-cookiesamesite}

`SameSite` controla cuándo incluye el navegador una cookie en solicitudes entre
sitios. Muchos navegadores actuales aplican un comportamiento similar a Lax
cuando se omite, pero un valor explícito deja claro el comportamiento previsto.
La comprobación notifica la ausencia del atributo; no demuestra que sea posible
un ataque CSRF.

**Corrección:** defina `SameSite=Lax` o `SameSite=Strict`, salvo que un flujo
entre sitios documentado necesite realmente `SameSite=None` (que además exige
`Secure`). `Lax` es adecuado para la mayoría de las cookies de sesión: sigue
permitiendo que una navegación de nivel superior, como hacer clic en un enlace
compartido, llegue con la sesión iniciada.

## 4. ¿Lleva el nombre de la cookie un prefijo?: `cookiePrefix` {#4-does-the-cookie-name-carry-a-prefix-cookieprefix}

Los prefijos en el nombre de una cookie añaden reglas para definirla. Los
navegadores compatibles exigen que las cookies `__Secure-` se definan de forma
segura con `Secure`. `__Host-` exige además `Path=/` y prohíbe `Domain`, lo que
vincula la cookie al host que la definió. Esto ayuda a impedir que un
subdominio hermano defina una cookie competidora para el dominio superior. No
aísla las cookies por puerto.

La comprobación notifica dos fallos distintos, porque tienen la misma
corrección:

- **Una cookie que declara un prefijo cuyas reglas no cumple**: `__Host-` con
  un atributo `Domain`, con un `Path` distinto de `/` o sin `Secure`. Los
  navegadores compatibles rechazan una cookie así, por lo que no es una
  debilidad teórica: la sesión que transporta deja de funcionar sin avisar. El
  detalle indica qué regla se ha incumplido.
- **Ninguna cookie observada lleva prefijo**, que es el estado normal de una
  instancia que nadie ha modificado.

**Corrección:** cambie el nombre de la cookie de sesión a `__Host-<name>` y
defínala con `Secure`, `Path=/` y sin atributo `Domain`, o use
`__Secure-<name>` cuando realmente tenga que compartirse entre subdominios. Si
la cookie la define un proxy inverso o un proveedor de identidad y no
OpenCloud, cámbiele el nombre allí.

## Gravedad y efecto en la nota {#severity-and-rating-impact}

Las cuatro son `extraChecks` y se notifican siempre que se observa una cookie:
`cookieSecure` con gravedad `high`, `cookieHttpOnly` con `medium`, y
`cookieSameSite` y `cookiePrefix` con `low`. Cada una limita la nota por sí
sola, igual que cualquier otra comprobación adicional fallida (`high` -> `C`,
`medium` -> `A`, `low` -> `A+`; consulte la tabla de comprobaciones adicionales
en [la guía de comprobaciones](../scanner-checks.md#what-the-scanner-checks)).
Defina `scanner.extra_checks_rating: false` para notificarlas sin que afecten a
la nota, o `--no-extra-checks` para omitirlas por completo.
