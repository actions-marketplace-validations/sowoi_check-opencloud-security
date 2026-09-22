# Regelmäßige Scans mit systemd oder cron

Auch ohne Icinga2 oder Nagios kannst du Scans zeitgesteuert ausführen. Unter [`contrib/`](../../contrib) liegen Vorlagen für:

- [systemd-Service](../../contrib/systemd/check-opencloud-security.service) und [Timer](../../contrib/systemd/check-opencloud-security.timer)
- [Umgebungsvariablen für systemd](../../contrib/systemd/check-opencloud-security.env.example)
- [Cronjob](../../contrib/cron/check-opencloud-security.cron)

Damit diese Dateien für dich geschrieben werden, mit den gerade konfigurierten Einstellungen darin, führe `check-opencloud-scanner configure --export-monitoring systemd` aus - siehe [`configure`](scanner-cli.md#configure-write-a-configuration-file). Die folgenden Dateien sind die Vorlagen dafür.

Der separate [Refresh-Timer](../../contrib/systemd/check-opencloud-security-refresh.timer) hält Release-Zeitplan und Schwachstellendatenbank aktuell. Konfiguriere den Scanner vor dem Aktivieren so, dass er beide Dateien unter `/var/lib/check-opencloud-security` liest. Der Aktualisierungsbefehl prüft die Dokumente und schreibt sie atomar.

## systemd-Timer {#systemd-timer}

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

Beide Beispiele verwenden ausschließlich [Umgebungsvariablen](../../README.md#environment-variables). Programmdatei und Docker-Image bleiben auf allen Hosts gleich; du passt nur die Umgebungsdatei oder den Cron-Eintrag an.

Cron und systemd übernehmen weder den `PATH` noch die übrigen Variablen deiner Login-Shell. Verwende deshalb den vollständigen Pfad zu `check-opencloud-security` und setze `COS_HOST` ausdrücklich. Weitere Hinweise stehen unter [Fehlersuche](../troubleshooting.md).

In Kubernetes übernimmt ein [`CronJob`](../kubernetes.md) diese Aufgabe. Für mehrere Instanzen lies [Mehrere Instanzen prüfen](../many-instances.md).

---

[Zur Dokumentationsübersicht](../README.md) | [Zum Haupt-README](../../README.md)

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
