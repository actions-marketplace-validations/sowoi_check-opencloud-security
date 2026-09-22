# El escáner de seguridad de OpenCloud en Icinga Director

[Icinga Director](https://icinga.com/docs/icinga-director/latest/) gestiona los
objetos `CheckCommand`, `Service Template` y `Service` desde su interfaz web, en
lugar de con archivos de configuración escritos a mano. Los pasos siguientes
sirven tanto para la instalación nativa como para la imagen de
[Docker](../installation.md#docker).

1. **Cree el comando**
   - Vaya a *Icinga Director → Commands → Add*.
   - **Command name:** `check_opencloud_security`
   - **Command:**
     - Instalación nativa: `/usr/lib/nagios/plugins/check-opencloud-security` (o donde lo haya instalado o enlazado; consulte [Instalación](../../README.md#installation)).
     - Docker: `/usr/bin/docker` (consulte el ejemplo de [CheckCommand con Docker](../installation.md#using-the-docker-image-instead) para los argumentos fijos obligatorios `run`, `--rm` y el nombre de la imagen).
   - **Command type:** *Plugin Check Command*.

2. **Añada los argumentos** en el mismo objeto de comando (pestaña *Fields* → *Add argument*):

   | Argumento    | Valor                       | Descripción                        |
   |:-------------|:----------------------------|:------------------------------------|
   | `--host`     | `$address$` (o un Data Field propio de Director, p. ej. `$opencloud_host$`) | Nombre de host, IP o URL de OpenCloud; obligatorio |
   | `--port`     | Data Field `$opencloud_port$`, opcional | Puerto, p. ej. `9200` |
   | `--insecure` | Data Field de tipo set-if `$opencloud_insecure$` (booleano), opcional | Instancia con certificado autofirmado |
   | `--proxy`    | Data Field `$opencloud_proxy$`, opcional | Proxy HTTP/HTTPS |
   | `--debug`    | Data Field de tipo set-if `$opencloud_debug$` (booleano), opcional | Salida de depuración detallada |

   Estos son los habituales. Todas las demás opciones, con el nombre de su variable, están en [`contrib/icinga2/check_opencloud_security.conf`](../../contrib/icinga2/check_opencloud_security.conf); añádelas de la misma forma.

   En cada argumento opcional, marque *Skip this argument on empty value* para
   que Director omita la opción por completo cuando el campo no tenga valor.

3. **Ponga los campos a disposición de los servicios** definiendo los *Data
   Fields* correspondientes en el comando (pestaña *Fields* → *Add data
   field*), p. ej. `opencloud_host`, `opencloud_port`, `opencloud_insecure`,
   `opencloud_debug`; después ajuste su *Data Type* (`String` o `Boolean`) y su
   *Var Filter* según sea necesario.

4. **Cree una plantilla de servicio**
   - *Icinga Director → Service Templates → Add*.
   - **Check command:** `check_opencloud_security`.
   - **Check interval:** `24h` es un buen valor predeterminado; lea la nota de
     [Icinga2 / Nagios](../installation.md#icinga2--nagios) antes de reducirlo mucho.
   - Deje aquí vacíos los Data Fields para poder rellenarlos por servicio o por host.

5. **Aplíquela a un host o a un grupo de hosts**
   - *Icinga Director → Services → Add* (o una *Service Apply Rule* para todo un grupo de hosts).
   - Importe la plantilla de servicio creada antes.
   - Rellene `opencloud_host` (o confíe en `$address$` si no lo ha sustituido) y los campos opcionales que necesite.
   - Despliegue la configuración desde *Icinga Director → Deployments*.

Una vez desplegado, Icinga2 ejecuta el comando exactamente como se describe en
la sección [Icinga2 / Nagios](../installation.md#icinga2--nagios), tanto si
detrás está el binario nativo como `docker run`.

Para que el objeto `Service` se escriba a partir de una configuración que
acaba de crear, con sus umbrales y su serie de publicación ya rellenados,
ejecute `check-opencloud-scanner configure --export-monitoring icinga`:
consulte [`configure`](scanner-cli.md#configure-write-a-configuration-file). El
`CheckCommand` del paso 1 sigue haciendo falta.

Para desplegar los mismos objetos sin la interfaz web, consulte
[Despliegue automatizado con Ansible](../ansible.md).

---

[Volver al índice de la documentación](../README.md) | [Volver al README principal](../../README.md)
