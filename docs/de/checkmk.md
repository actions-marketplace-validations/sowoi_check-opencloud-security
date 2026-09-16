# Checkmk einrichten

Checkmk kann die Nagios-Ausgabe des Plugins direkt lesen. Du kannst den Scan auf dem Checkmk-Server oder auf einem Host mit Checkmk-Agent ausführen:

| | [Aktiver Check](#1-an-active-check-on-the-checkmk-server) | [Lokaler Check](#2-a-local-check-on-an-agent-host) |
|:--|:--|:--|
| Ausführung | Checkmk-Server | Agent-Host |
| Netzwerkzugriff | Vom Monitoring-Netz aus | Vom Netz des Agent-Hosts aus |
| Plugin-Installation | Auf dem Checkmk-Server | Auf dem Agent-Host |
| Konfiguration | Weboberfläche | Vom Agent ausgeführtes Skript |
| Ausgabe | `nagios`, der Standard | `--format checkmk` |

Verwende einen aktiven Check, wenn der Checkmk-Server die Instanz erreicht. Für interne Netze, die nur ein Agent-Host erreicht, eignet sich der lokale Check.

Ersetze in den Beispielen `opencloud.example.com` durch eine Instanz, die Du prüfst dürfen.

## 1. Aktiver Check auf dem Checkmk-Server {#1-an-active-check-on-the-checkmk-server}

Installiere das Plugin auf dem Checkmk-Server als Site-Benutzer:

```shell
pipx install check-opencloud-security
```

Der [Installationsleitfaden](../installation.md) beschreibt weitere Wege über uv, pip und einen Checkout. `check-opencloud-security --version` zeigt die installierte Version.

Lege unter **Setup > Services > Other services > Integrate Nagios plugins** eine Regel an:

- **Service description:** `OpenCloud security opencloud.example.com`
- **Command line:** `check-opencloud-security --host opencloud.example.com --check-hardening`

Weise die Regel dem Host zu, unter dem der Service erscheinen soll. Das tatsächliche Scanziel bestimmt weiterhin `--host`.

Checkmk liest den Status aus dem Exitcode, die Zusammenfassung aus der ersten Ausgabezeile, weitere Zeilen als Details und die Werte hinter `|` als Metriken. Die [Performancedaten](../../README.md#performance-data) enthalten `rating`, `vulnerabilities`, `hardenings_missing`, `extra_checks_failed`, `update_available`, `support_days_left`, `cert_days_left` und `time` einschließlich Schwellwerten.

Prüfe das Intervall unter **Setup > Services > Service monitoring rules > Normal check interval for service checks**. Ein Scan erzeugt mehrere HTTP-Anfragen und TCP-Verbindungen; ein minütlicher Check ist für diese Konfigurationsprüfung meist unnötig. Wähle beispielsweise eine Stunde oder länger.

## 2. Lokaler Check auf einem Agent-Host {#2-a-local-check-on-an-agent-host}

Ein lokaler Check führt den Scanner auf einem Host aus, der die Instanz erreichen kann. Der Agent übernimmt dessen Ausgabe als Service dieses Hosts.

`--format checkmk` erzeugt das dafür benötigte Format:

```shell
check-opencloud-security --host opencloud.example.com --format checkmk
```

```text
0 "OpenCloud_Security_opencloud.example.com" rating=5|vulnerabilities=0|hardenings_missing=0|extra_checks_failed=0|update_available=0|support_days_left=284|cert_days_left=67|execution_time=4.120 OK: Server is up to date. No known vulnerabilities.
```

Die vier durch einzelne Leerzeichen getrennten Felder sind Status, Dienstname in Anführungszeichen, Metriken und Detailtext. Mehrere Hosts ergeben je eine Zeile und damit einen Service pro Instanz.

### Installation {#installing-it}

Das Skript [`contrib/checkmk/opencloud_security`](../../contrib/checkmk/opencloud_security) enthält den Aufruf. Es verwendet dieselben `COS_`-Umgebungsvariablen wie die Beispiele für [cron und systemd](../scheduling.md):

```shell
sudo install -m 0755 contrib/checkmk/opencloud_security \
    /usr/lib/check_mk_agent/local/3600/opencloud_security
```

Das Unterverzeichnis `3600` legt das Cache-Intervall des Agents in Sekunden fest. Der Scan läuft damit höchstens stündlich; dazwischen liefert der Agent die zwischengespeicherte Ausgabe. Direkt unter `local/` würde das Skript bei jedem Agent-Aufruf laufen. Passt du das Intervall an deinen Bedarf an.

Bei Installation über `.deb` oder `.rpm` liegt die Vorlage unter `/usr/share/doc/check-opencloud-security/checkmk-local-check.sh`. Kopiere sie selbst in das Agent-Verzeichnis.

Setze das Ziel im Skript oder in einer vom Agent gelesenen Umgebungsdatei:

```shell
COS_HOST=opencloud.example.com
# OpenCloud self-signs its certificate unless a proxy terminates TLS for it.
#COS_SCANNER_VERIFY_TLS=false
```

Suche anschließend unter **Setup > Hosts**, auf der *Services*-Seite des Hosts, mit *Full service scan* nach dem neuen Service.

### Bedeutung der Statuswerte {#what-the-states-mean}

Der Status entspricht den Exitcodes des Plugins und berücksichtigt dieselben [Schwellwerte](../../README.md#rating-thresholds), Ausnahmen und End-of-Life-Regeln:

- `0` OK: Bewertung oberhalb der Warnschwelle beziehungsweise kein neuer Befund bei entsprechend konfiguriertem Baseline-Vergleich.
- `1` WARN: Warnschwelle erreicht oder ein entsprechend bewerteter Härtungsbefund.
- `2` CRIT: kritische Schwelle erreicht oder eine bekannte Schwachstelle.
- `3` UNKNOWN: Scan konnte nicht abgeschlossen werden.

Das mitgelieferte Skript gibt auch dann eine Zeile aus, wenn das Plugin fehlt oder durch einen Timeout beendet wurde. Ohne Ausgabe könnte der lokale Service aus der Erkennung verschwinden, statt einen Fehler zu melden.

### Metriken {#the-metrics}

Die Messwerte entsprechen den Nagios-Performancedaten mit zwei Anpassungen:

- **Keine Schwellwerte:** Das Plugin liefert den fertigen Status. Checkmk berechnet ihn nicht über den lokalen Status `P` erneut.
- **Keine Einheit im Zahlenwert:** Aus `time=4.120s` wird `execution_time=4.120`.

| Metrik | Bedeutung |
|:--|:--|
| `rating` | `0` bis `5`, wobei `5` für A+ steht; fehlt ohne ermittelbare Bewertung |
| `vulnerabilities` | Bekannte Sicherheitshinweise für die erkannte Version |
| `hardenings_missing` | Fehlende Härtungsmaßnahmen; fehlt ohne `--check-hardening` |
| `extra_checks_failed` | Fehlgeschlagene Zusatzprüfungen, etwa TLS, Pfade, Cookies und Header |
| `update_available` | `1` bei verfügbarer neuerer Version; fehlt bei deaktivierter Update-Prüfung |
| `support_days_left` | Tage bis zum Supportende; danach negativ |
| `cert_days_left` | Tage bis zum Zertifikatsablauf; danach negativ |
| `execution_time` | Scandauer in Sekunden |

Nicht ermittelte Werte werden weggelassen und nicht als Null ausgegeben.

## Benachrichtigungen einrichten {#alerting-on-it}

Beide Varianten erzeugen reguläre Checkmk-Services. Benachrichtigungen, Wartungszeiten und Bestätigungen funktionieren wie bei anderen Services.

- Richte zeitnahe Benachrichtigungen für **CRIT** ein.
- Stelle `support_days_left` dar und warne rechtzeitig vor dem Supportende. Sobald die Version nicht mehr unterstützt wird, fällt die Bewertung auf F.

Mit [`--baseline` und `--warn-on-new`](../baseline.md) kann die Alarmierung auf neue oder verschlechterte Befunde beschränkt werden. Das Supportende und weitere Verschlechterungen werden dadurch nicht unterdrückt.

## Weitere Anleitungen {#see-also}

- [Installation](../installation.md), einschließlich Icinga2-/Nagios-Objekten.
- [Ausgabeformate](../output-formats.md) im Vergleich.
- [Zeitplanung](../scheduling.md) mit systemd und cron.
- [Prometheus und Grafana](../prometheus.md) für zusätzliche Dashboards.

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
