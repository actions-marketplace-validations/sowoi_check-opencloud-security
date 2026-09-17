# Programar análisis de seguridad de OpenCloud con systemd y cron

Programe análisis periódicos con un temporizador de systemd o con cron si no
utiliza Icinga2 ni Nagios. Los ejemplos de [`contrib/`](../../contrib/)
incluyen archivos de servicio, de temporizador y de entorno que puede adaptar a
su instalación:

- [`contrib/systemd/check-opencloud-security.service`](../../contrib/systemd/check-opencloud-security.service)
  y [`.timer`](../../contrib/systemd/check-opencloud-security.timer)
- [`contrib/systemd/check-opencloud-security.env.example`](../../contrib/systemd/check-opencloud-security.env.example)

El temporizador independiente
[`check-opencloud-security-refresh.timer`](../../contrib/systemd/check-opencloud-security-refresh.timer)
mantiene al día el calendario de versiones y la base de datos de avisos de
seguridad del escáner. Configure el escáner para que lea los dos archivos de
`/var/lib/check-opencloud-security` antes de activarlo; el comando de
actualización valida ambos documentos y los escribe de forma atómica.
- [`contrib/cron/check-opencloud-security.cron`](../../contrib/cron/check-opencloud-security.cron)

<!-- TOC -->
* [Programación sin Icinga2 / Nagios](#scheduling-without-icinga2--nagios)
  * [Temporizador de systemd](#systemd-timer)
  * [cron](#cron)
<!-- TOC -->


## Temporizador de systemd {#systemd-timer}
```shell
sudo mkdir -p /etc/check-opencloud-security
sudo cp contrib/systemd/check-opencloud-security.env.example /etc/check-opencloud-security/env
sudo $EDITOR /etc/check-opencloud-security/env   # set COS_HOST (and any other options)

sudo cp contrib/systemd/check-opencloud-security.service /etc/systemd/system/
sudo cp contrib/systemd/check-opencloud-security.timer /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now check-opencloud-security.timer

# Run it once immediately to verify the setup:
sudo systemctl start check-opencloud-security.service
journalctl -u check-opencloud-security.service
```

## cron {#cron}
```shell
sudo cp contrib/cron/check-opencloud-security.cron /etc/cron.d/check-opencloud-security
sudo chmod 644 /etc/cron.d/check-opencloud-security
sudo $EDITOR /etc/cron.d/check-opencloud-security   # set COS_HOST (and any other options)
```

Ambos ejemplos configuran la comprobación únicamente mediante
[variables de entorno](../../README.md#environment-variables), de modo que el
mismo binario o la misma imagen de Docker se reutiliza sin cambios en todos los
hosts: solo cambia el archivo de entorno o la entrada de cron.

Hay dos detalles que suelen causar problemas, y ambos se tratan en
[Solución de problemas](../troubleshooting.md): ni cron ni systemd tienen el
`PATH` ni el entorno de un shell de inicio de sesión, así que utilice la ruta
completa de `check-opencloud-security` y defina `COS_HOST` explícitamente.

En un clúster, el equivalente es un `CronJob`; consulte
[Kubernetes](../kubernetes.md). Para más de unas pocas instancias, consulte
[Comprobar un conjunto de instancias](../many-instances.md).

---

[Volver al índice de la documentación](../README.md) | [Volver al README principal](../../README.md)
