# Scan a fleet with the OpenCloud Security Scanner

# Mehrere Instanzen prüfen

Bei mehreren Instanzen unterscheiden sich oft Port, Release-Kanal und akzeptierte Befunde. Dieser Leitfaden zeigt gemeinsame Aufrufe, getrennte Konfigurationsdateien und die automatisierte Ausführung über mehrere Hosts.

## Ein Befehl für mehrere Hosts {#one-command-several-hosts}

`--host` akzeptiert eine kommagetrennte Liste. Das Plugin scannt die Hosts nacheinander, gibt eine Zusammenfassung und einen Abschnitt pro Host aus und beendet sich mit dem schwerwiegendsten Status. Siehe [Mehrere Hosts prüfen](../../README.md#checking-multiple-hosts).

```shell
check-opencloud-security --check-hardening \
  --host opencloud1.example.com,opencloud2.example.com:9200,[2001:db8::1]
```

Alle weiteren Optionen gelten für die gesamte Liste. Nutzen Sie getrennte Aufrufe, wenn einzelne Instanzen andere Einstellungen wie `--insecure` oder abweichende Ausnahmen benötigen.

Ein gemeinsamer Monitoring-Check hat auch nur einen gemeinsamen Statusverlauf. Für getrennte Historien und Alarme richten Sie einen Check pro Instanz ein.

`--webhook-digest` fasst die Webhook-Benachrichtigungen dieser Hostliste zu höchstens einer Nachricht zusammen. Es werden nur Hosts berücksichtigt, die `--webhook-on` erfüllen. Die Zusammenfassung gilt innerhalb eines Prozesses. Bei getrennten Aufrufen, etwa in der folgenden Dateischleife, sendet weiterhin jeder Aufruf seinen eigenen Webhook.

## Eine Konfigurationsdatei pro Instanz {#one-configuration-file-per-instance}

Speichern Sie die instanzspezifischen Einstellungen in jeweils einer Datei:

```yaml
# /etc/check-opencloud-security/prod-eu.yml
host: opencloud-eu.example.com
check_hardening: true
update_warning: true

scanner:
  target_port: 9200
  release_track: production
  ignore_hardenings:
    # The reverse proxy owns this header; the instance cannot set it.
    - hstsPreload

releases:
  mode: auto
  token: secret://releases_token
```

```shell
check-opencloud-security --config /etc/check-opencloud-security/prod-eu.yml
```

Es gilt die Reihenfolge **Kommandozeile > Umgebungsvariable > Konfigurationsdatei > Standard**. Für einzelne Durchläufe können Sie Dateieinstellungen daher gezielt überschreiben. Die vollständige Syntax einschließlich `secret://` steht unter [Konfigurationsdatei und Zugangsdaten](../../README.md#configuration-file-and-secrets).

Erstellen Sie die erste Datei mit `check-opencloud-security --configure --config /etc/check-opencloud-security/prod-eu.yml` und verwenden Sie sie als Vorlage für weitere Instanzen.

## Alle Dateien durchlaufen {#a-loop-over-the-files}

Eine Schleife führt die Checks aus und fasst die Exitcodes zusammen:

```shell
#!/bin/sh
# Scan every configured instance; exit with the worst state seen.
set -u

worst=0
rank() { case "$1" in 2) echo 3 ;; 1) echo 2 ;; 3) echo 1 ;; *) echo 0 ;; esac; }

for config in /etc/check-opencloud-security/*.yml; do
  check-opencloud-security --config "$config" || state=$?
  state="${state:-0}"
  [ "$(rank "$state")" -gt "$(rank "$worst")" ] && worst="$state"
  unset state
done

exit "$worst"
```

Die Funktion `rank` bildet die tatsächliche Reihenfolge der Nagios-Status ab: `CRITICAL` (2), `WARNING` (1), `UNKNOWN` (3), `OK` (0). Ein rein numerischer Vergleich würde diese Priorität falsch wiedergeben.

## Den Standort des Scanners wählen {#where-the-checks-should-run-from}

Der Netzwerkstandort bestimmt, was der Scanner beobachten kann:

- Eine interne Instanz benötigt einen Scanner mit Zugriff auf das interne Netzwerk. Öffnen Sie dafür nicht unnötig die Firewall nach außen.
- TLS und HTTPS-Weiterleitungen werden so bewertet, wie sie am gewählten Zugangspunkt erscheinen. Terminiert ein Loadbalancer TLS, misst der Scanner dessen Verbindung.
- Debug-Port-Prüfungen sollten aus einem Netzwerk erfolgen, aus dem diese Ports nicht erreichbar sein sollen. Ein lokaler Scan auf dem Server kann andere Ergebnisse liefern als ein externer Scan.

Wenn mehrere Dashboards oder Skripte dasselbe Ergebnis benötigen, können sie den Cache eines nahe bei den Instanzen betriebenen [Scan-Dienstes](../../README.md#running-the-scanner-as-a-service) nutzen. Das Monitoring-Plugin führt seine Scans weiterhin selbst aus und ruft diesen Dienst nicht auf.

## Ausnahmen regelmäßig prüfen {#keeping-the-waivers-honest}

Prüfen Sie `ignore_hardenings` regelmäßig auf Einträge, die nicht mehr benötigt werden:

- Ein ausgenommener Befund bleibt mit `"ignored": true` im Ergebnis und wird von `--debug` erklärt. Siehe [Befunde ausnehmen](../hardening.md#accepting-a-finding-you-are-not-going-to-fix).
- Nur tatsächlich fehlgeschlagene Prüfungen werden als ignoriert markiert. Eine bestandene Prüfung wird dadurch nicht zu einem ignorierten Befund.

Vergleichen Sie dazu einen Scan ohne Ausnahmen mit dem bisherigen Ergebnis:

```shell
for config in /etc/check-opencloud-security/*.yml; do
  echo "== $config"
  COS_SCANNER_IGNORE_HARDENINGS="" check-opencloud-security --config "$config" --debug \
    | grep -E 'ignored|waived|FAIL'
done
```

`publicLinkExpirationEnforced` benötigt keine Ausnahme. OpenCloud gibt den Wert fest vor; der Scanner erfasst ihn, nimmt ihn aber aus Alarmierung, `hardenings_missing` und Webhook aus. Siehe [Fest vorgegebene Werte](../hardening.md#measures-that-are-not-settings).

## Nur bei Änderungen alarmieren {#only-alerting-on-what-changed}

Mit einer Baseline und `--warn-on-new` können Sie bekannte, unveränderte Befunde von der erneuten Alarmierung ausnehmen:

```shell
for config in /etc/check-opencloud-security/*.yml; do
  check-opencloud-security --config "$config" \
      --baseline /var/lib/check_opencloud/baseline.json \
      --warn-on-new
done
```

Eine Datei kann die Baselines aller Hosts enthalten, auch bei einer kommagetrennten `--host`-Liste.

Beachten Sie dabei:

- Der Monitoring-Benutzer benötigt Schreibrechte auf das Verzeichnis. Die Datei wird atomar und nur für den Eigentümer zugänglich geschrieben. Ein Schreibfehler wird gemeldet, ändert aber nicht die Bewertung der Instanz.
- Verwenden Sie konsistente Hostangaben. `opencloud.example.com` und `https://opencloud.example.com/` werden gleich normalisiert. Eine IP-Adresse wie `10.0.0.5` wird dagegen nicht mit dem zugehörigen DNS-Namen zusammengeführt.

Versionen nach ihrem Supportende lösen weiterhin bei jedem Durchlauf einen Alarm aus. Details stehen unter [Nur Änderungen melden](../../README.md#reporting-only-what-changed).

Aktivieren Sie `--self-update-check` für einen der Aufrufe, um von neuen Plugin-Versionen zu erfahren. Die Abfrage wird einen Tag zwischengespeichert und beeinflusst den Exitcode nicht.

## Zeitplanung {#scheduling-the-whole-thing}

- Icinga2: ein `Service` pro Host, gegebenenfalls über eine Hostgruppe; siehe [Icinga Director](../icinga-director.md) oder [Ansible](../ansible.md).
- Ohne Monitoring-System: die Dateischleife über einen [systemd-Timer oder Cronjob](../scheduling.md) starten.
- Kubernetes: einen [`CronJob`](../kubernetes.md) verwenden.

Verteilen Sie die Startzeiten. Gleichzeitige Scans belasten Netzwerk und Release-Quelle und teilen sich gegebenenfalls deren Ratenlimit.

---

[Zur Dokumentationsübersicht](../README.md) | [Zum Haupt-README](../../README.md)

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
