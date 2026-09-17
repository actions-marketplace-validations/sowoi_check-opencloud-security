# Por qué OpenCloud sigue respondiendo a /status.php

OpenCloud está escrito en Go. Su ruta `/status.php` es un punto de acceso de
compatibilidad para clientes existentes, no un script PHP.

<!-- TOC -->
* [Por qué OpenCloud sigue respondiendo a `/status.php`](#why-opencloud-still-answers-statusphp)
  * [De dónde procede la ruta](#where-the-path-comes-from)
  * [Qué devuelve realmente el manejador](#what-the-handler-actually-returns)
  * [Qué lee este escáner de ella y qué no](#what-this-scanner-reads-from-it-and-what-it-does-not)
<!-- TOC -->


## De dónde procede la ruta {#where-the-path-comes-from}

El punto de acceso conserva una interfaz conocida por los clientes, aunque
OpenCloud lo sirve desde código Go. El sufijo `.php` no implica que el servidor
ejecute PHP. Varios productos ofrecen un punto de acceso compatible, por lo que
el escáner comprueba el producto notificado antes de aplicar reglas
específicas de OpenCloud. Consulte [Qué es OpenCloud](../what-is-opencloud.md)
para la arquitectura y [Solución de problemas](../troubleshooting.md) para los
fallos de identificación del producto.

```go
// vendor/github.com/opencloud-eu/reva/v2/internal/http/services/owncloud/ocdav/ocdav.go
return []string{"/status.php", "/status", "/remote.php/dav/public-files/", ...}
...
case "status.php", "status":
    s.doStatus(w, r)
```

Tanto `/status.php` como la forma más corta `/status` llegan al mismo
manejador. La grafía `.php` se mantiene solo porque los clientes siguen
solicitándola con ese nombre exacto; nada de la respuesta lo genera PHP.

## Qué devuelve realmente el manejador {#what-the-handler-actually-returns}

El manejador que responde a ambas rutas es `doStatus`, y su respuesta es un
literal de estructura, no una consulta a ningún estado real:

```go
// vendor/github.com/opencloud-eu/reva/v2/internal/http/services/owncloud/ocdav/status.go
status := &ocs.Status{
    Installed:      true,
    Maintenance:    false,
    NeedsDBUpgrade: false,
    Version:        s.c.Version,
    VersionString:  s.c.VersionString,
    Edition:        s.c.Edition,
    ProductName:    s.c.ProductName,
    ProductVersion: s.c.ProductVersion,
    Product:        s.c.Product,
}
```

`Installed`, `Maintenance` y `NeedsDBUpgrade` son los literales `true`/`false`/
`false`: no proceden de `s.c.something`, ni de una base de datos, ni de un
archivo en disco. Todas las instancias de OpenCloud que han incluido este
manejador devuelven exactamente esos tres valores, tanto si acaban de
arrancar como si están en pleno despliegue o llevan un año en marcha. OpenCloud
tampoco tiene una base de datos en el sentido que sugiere el nombre del campo:
guarda los datos en el sistema de archivos y en backends de almacenamiento de
objetos, no en una base de datos SQL con migraciones de esquema, así que
"`needsDbUpgrade`" describe un estado que la propia arquitectura de OpenCloud
no tiene.

Los demás campos (`Version`, `VersionString`, `Edition`, `ProductName`,
`ProductVersion`, `Product`) proceden de `s.c`, la configuración del propio
servicio, y sí varían según la compilación. `Version` y `VersionString` son a
su vez marcadores fijos heredados que se conservan para clientes de
sincronización antiguos; solo `ProductVersion` es la versión real. Consulte
[Leer la versión correctamente](../scanner-checks.md#reading-the-version-correctly).

## Qué lee este escáner de ella y qué no {#what-this-scanner-reads-from-it-and-what-it-does-not}

Este escáner lee `product`/`productname` (para rechazar ownCloud y Nextcloud en
lugar de calificarlos) y `productversion` (la versión real, utilizada en las
comprobaciones de fin de vida y de actualización; consulte
[Divulgación de versión y ciclo de vida](../lifecycle.md) para saber qué
depende de ese campo y cómo se comporta el análisis cuando falta). No comprueba
`installed`, `maintenance` ni `needsDbUpgrade`: una comprobación que siempre se
supera, pase lo que pase realmente en el servidor, sería peor que no tener
ninguna, porque un resultado en verde daría a entender que el escáner ha
verificado algo que no podía observar. Versiones anteriores de este escáner sí
notificaban hallazgos `maintenanceMode`, `installed` y `databaseUpgrade` a
partir de estos campos; se eliminaron cuando se confirmó en el propio código
fuente de OpenCloud que la respuesta anterior es fija.

Si una futura versión de OpenCloud empieza a calcular estos campos a partir de
un estado real, el código fuente citado arriba es el lugar que hay que
consultar: es la respuesta autorizada, no este documento, que solo lo cita tal
como era en el momento de escribirlo.
