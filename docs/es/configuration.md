# Secretos en la configuración del escáner de seguridad de OpenCloud

Mantenga las credenciales fuera del archivo de configuración haciendo
referencia a su origen. Los tokens de GitHub, las URL de webhooks y los tokens
de servicio pueden leerse de un archivo, de una variable de entorno o de un
comando en el momento en que se necesitan.

El propio archivo, su ubicación y la correspondencia entre sus claves y las
variables de entorno se describen en
[Archivo de configuración y secretos](../../README.md#configuration-file-and-secrets);
`config/check-opencloud-security.example.yml` es un ejemplo comentado por completo.

<!-- TOC -->
* [Secretos en la configuración](#secrets-in-the-configuration)
  * [Formas de referencia](#reference-forms)
  * [Fuera de un contenedor](#outside-a-container)
<!-- TOC -->


## Formas de referencia {#reference-forms}

Se admiten cuatro prefijos en cualquier lugar donde se espere un valor:

| Referencia             | Se resuelve como                                                                  |
|:-----------------------|:----------------------------------------------------------------------------------|
| `secret://name`        | `<secrets.dir>/name`, es decir, `/run/secrets/name` para secretos de Docker y Kubernetes |
| `file:///path/to/file` | El contenido de ese archivo                                                       |
| `env://VARIABLE`       | El valor de esa variable de entorno                                               |
| `exec://command --arg` | La salida estándar de ese comando (requiere `secrets.allow_exec: true`)           |

Como alternativa, añada `_file` a cualquier clave o variable:
`COS_RELEASES_TOKEN_FILE=/run/secrets/token` o `token_file: /run/secrets/token`.
Los saltos de línea finales se eliminan, así que `echo secret > file` funciona
como se espera.

## Fuera de un contenedor {#outside-a-container}

`secret://name` busca dentro de `secrets.dir` (`COS_SECRETS_DIR`), cuyo valor
predeterminado es `/run/secrets`, justo donde Docker y Kubernetes montan sus
secretos. Fuera de un contenedor, indique su propio directorio:

```shell
mkdir -p /etc/check-opencloud-security/secrets
printf '%s' '<github-token>' > /etc/check-opencloud-security/secrets/releases_token
chmod 600 /etc/check-opencloud-security/secrets/*

export COS_SECRETS_DIR=/etc/check-opencloud-security/secrets
check-opencloud-security --host opencloud.example.com \
  --release-token 'secret://releases_token'
```

El repositorio incluye plantillas para ambos archivos en
[`secrets/`](../../secrets/README.md); cópielas y sustituya los valores de
ejemplo.
