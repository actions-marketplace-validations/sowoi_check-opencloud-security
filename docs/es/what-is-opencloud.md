# Qué es OpenCloud

[OpenCloud](https://opencloud.eu/) es una plataforma de código abierto para
almacenar, sincronizar y compartir archivos. Este escáner está pensado para sus
canales de publicación, su configuración y sus puntos de acceso públicos. Esta
página explica la arquitectura en la que se basan esas comprobaciones.

<!-- TOC -->
* [Qué es OpenCloud](#what-opencloud-is)
  * [De dónde procede OpenCloud](#where-opencloud-comes-from)
  * [Cómo está estructurado OpenCloud](#how-opencloud-is-structured)
  * [Por qué importa para un análisis de seguridad](#why-this-matters-for-a-security-scan)
<!-- TOC -->

## De dónde procede OpenCloud {#where-opencloud-comes-from}

OpenCloud se desarrolla como un proyecto de código abierto independiente, con
sus propias versiones y su propio ciclo de soporte. Su servidor, escrito en Go,
utiliza las API de CS3 y componentes de Reva para el almacenamiento y la
colaboración. Consulte la
[documentación de OpenCloud](https://docs.opencloud.eu/) para las instrucciones
de despliegue y configuración.

Algunas interfaces públicas mantienen la compatibilidad con clientes
existentes. Por ejemplo, `/status.php` conserva un nombre de estilo PHP aunque
OpenCloud sea una aplicación Go. Su respuesta incluye tanto valores de
compatibilidad como la versión real de OpenCloud. La
[guía del punto de acceso de estado](../status-php.md) explica qué campos son
útiles para un escáner.

## Cómo está estructurado OpenCloud {#how-opencloud-is-structured}

OpenCloud combina servicios de autenticación, acceso a archivos, uso compartido
y su interfaz web. Las principales decisiones de despliegue influyen en lo que
puede ver un análisis externo:

| Componente | Aspecto operativo |
|:--|:--|
| Interfaz web y proxy | URL pública, terminación TLS, cabeceras de seguridad y cabeceras reenviadas |
| Proveedor de identidad | Política de inicio de sesión, registro de clientes, aprovisionamiento de cuentas y segundos factores |
| Almacenamiento | Organización de datos y metadatos, permisos, copias de seguridad y recuperación probada |
| Integraciones de ofimática y calendario | Configuración propia de cada servicio, credenciales y límites de red |
| Canal de publicación | Recomendaciones de actualización y periodo durante el que se publican correcciones |

Que el almacenamiento central de OpenCloud no use una base de datos relacional
no significa que el despliegue completo carezca de estado persistente. Los
proveedores de identidad y otras integraciones pueden tener sus propias bases
de datos y sus propios requisitos de copia de seguridad.

## Por qué importa para un análisis de seguridad {#why-this-matters-for-a-security-scan}

Un punto de acceso conocido no basta para identificar el software que hay
detrás. El escáner comprueba el producto notificado antes de aplicar los datos
de versiones, los avisos de seguridad y las reglas de configuración de
OpenCloud. Un producto distinto se rechaza en lugar de recibir una nota de
OpenCloud; consulte [Solución de problemas](../troubleshooting.md).

El resultado describe lo que el escáner pudo observar en la dirección enviada.
No puede verificar archivos privados, permisos de cuentas, la recuperación de
copias de seguridad ni todas las políticas de un proveedor de identidad. La
[guía de despliegue seguro](../secure-deployment.md) trata esas tareas
operativas por separado.
