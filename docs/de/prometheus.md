# OpenCloud security metrics for Prometheus and Grafana

# Prometheus, Grafana und OpenTelemetry

Das Plugin enthält einen Prometheus-Exporter. Mit `--prometheus-listen-port 9102` stellt es `/metrics` bereit. Ergebnisse werden für `--scrape-interval` Sekunden zwischengespeichert, standardmäßig 60. Nur bei `0` löst jeder Abruf einen neuen Scan aus.

Der Exporter lauscht standardmäßig auf `127.0.0.1`. Für einen Container oder entfernte Scraper verwenden Sie `--prometheus-listen-addr 0.0.0.0` und beschränken den Zugriff über Firewall oder NetworkPolicy:

```shell
docker run --rm -p 9102:9102 check-opencloud-security \
  --host opencloud.example.com --prometheus-listen-port 9102 \
  --prometheus-listen-addr 0.0.0.0
```

Für einzelne Durchläufe gibt `--format=prometheus` die Metriken als Text aus und beendet sich. `--format=otlp` liefert dieselben Werte als OTLP/JSON für einen OpenTelemetry-Collector. Dafür sind keine zusätzlichen Python-Abhängigkeiten nötig.

Die folgenden Textfile-Collector- und Pushgateway-Beispiele eignen sich für zeitgesteuerte Scans. Bei Icinga2 können die Graphite-/InfluxDB-Writer stattdessen direkt die [Performancedaten](../../README.md#performance-data) übernehmen.

## Vorgefertigte Regeln und Dashboard {#the-files-to-copy}

Unter [`contrib/`](../../contrib/README.md) liegen zwei Dateien für die Metriknamen des nativen Exporters:

| Datei | Verwendung |
|:--|:--|
| [`contrib/prometheus/alerts.yml`](../../contrib/prometheus/alerts.yml) | Nach `/etc/prometheus/rules/` kopieren und in `rule_files:` eintragen |
| [`contrib/grafana/dashboard.json`](../../contrib/grafana/dashboard.json) | In Grafana über Dashboards → New → Import laden und Datenquelle wählen |

```shell
cp contrib/prometheus/alerts.yml /etc/prometheus/rules/opencloud-security.yml
promtool check rules /etc/prometheus/rules/opencloud-security.yml
```

Das Dashboard bietet eine Auswahl nach `Instance` und kann damit mehrere Hosts darstellen. Passen Sie Scanintervall, Scrape-Intervall und die Dauer `for:` der Alarmregeln gemeinsam an. `for:` misst, wie lange eine Bedingung bei der Regelauswertung ununterbrochen erfüllt ist; es zählt keine unabhängigen Scans.

Die späteren Beispiele mit `jq` verwenden eigene, kürzere Metriknamen. Die beiden mitgelieferten Dateien passen zu den Namen des nativen Exporters, nicht zu diesen Beispielen.

## Metriken des Exporters {#what-the-exporter-publishes}

| Metrik | Labels | Bedeutung |
|:--|:--|:--|
| `opencloud_security_rating_score` | `host`, `domain`, `product`, `version` | Bewertung von `0` bis `5`; `5` ist die beste Note |
| `opencloud_security_end_of_life` | `host`, `release_type` | `1`, sobald die Version keine Sicherheitsupdates mehr erhält |
| `opencloud_security_support_days_remaining` | `host`, `release_type` | Verbleibende Supporttage; fehlt, wenn noch kein Enddatum feststeht |
| `opencloud_security_vulnerabilities_total` | `host`, `severity` | Zur Version passende Sicherheitshinweise |
| `opencloud_security_hardenings_missing_total` | `host` | Fehlende Härtungsmaßnahmen |
| `opencloud_security_failed_extra_checks_total` | `host` | Fehlgeschlagene Zusatzprüfungen |
| `opencloud_security_update_available` | `host`, `target_version` | `1`, wenn eine neuere Version verfügbar ist |
| `opencloud_security_scan_duration_seconds` | `host` | Scandauer |
| `opencloud_security_scrape_success` | `host` | `0`, wenn der zugrunde liegende Scan fehlgeschlagen ist |

Bei einem fehlgeschlagenen Scan erscheinen nur Dauer und Erfolgsstatus. Frühere Befunde werden nicht erneut als aktuell ausgegeben. Prüfen Sie deshalb zuerst `opencloud_security_scrape_success`.

`opencloud_security_end_of_life` ist von der Zahl verbleibender Tage getrennt. Bei Rolling und Production kann das Ende noch undatiert sein, da es vom nächsten Release abhängt. Eine fehlende Tageszahl bedeutet nicht, dass der Support heute endet.

## Nagios-Performancedaten darstellen {#what-there-is-to-graph}

Jeder reguläre Plugin-Aufruf gibt hinter `|` Performancedaten aus:

```
rating=5;@0:3;@0:1;0;5 vulnerabilities=0;;;0; time=1.234s;;;0;
```

| Metrik | Bedeutung |
|:--|:--|
| `rating` | `0` bis `5`, also F bis A+; `U` bei fehlgeschlagenem Scan |
| `vulnerabilities` | Bekannte Schwachstellen der installierten Version |
| `time` | Scandauer in Sekunden |
| `hardenings_missing` | Fehlende Härtungsmaßnahmen; nur mit `--check-hardening` |
| `extra_checks_failed` | Fehlgeschlagene Zusatzprüfungen |
| `update_available` | `1` bei verfügbarer neuerer Version |
| `support_days_left` | Verbleibende Supporttage; nach dem Enddatum negativ |

Mit `support_days_left` können Sie rechtzeitig vor einem bekannten Supportende warnen.

## Textfile Collector von node_exporter {#node_exporter-textfile-collector}

Dieses Beispiel verwendet das JSON von `check-opencloud-scanner` und wandelt es mit `jq` um. Die Ausgabe wird zuerst in eine temporäre Datei geschrieben und dann umbenannt, damit node_exporter keine unvollständige Datei liest.

```shell
#!/bin/sh
# /usr/local/bin/opencloud-metrics - run from a systemd timer, see scheduling.md
set -eu

HOST="opencloud.example.com"
OUT="/var/lib/node_exporter/textfile_collector/opencloud_security.prom"
TMP="$(mktemp "${OUT}.XXXXXX")"

check-opencloud-scanner scan --compact "$HOST" > /tmp/opencloud-scan.json || true

jq -r --arg host "$HOST" '
  if .error then
    "opencloud_scan_success{host=\"\($host)\"} 0"
  else
    "opencloud_scan_success{host=\"\($host)\"} 1",
    "opencloud_security_rating{host=\"\($host)\"} \(.rating)",
    "opencloud_end_of_life{host=\"\($host)\"} \(if .EOL then 1 else 0 end)",
    "opencloud_vulnerabilities{host=\"\($host)\"} \(.vulnerabilities | length)",
    "opencloud_update_available{host=\"\($host)\"} \(if .updates.available then 1 else 0 end)",
    "opencloud_support_days_left{host=\"\($host)\"} \(.lifecycle.daysRemaining // 0)",
    "opencloud_failed_checks{host=\"\($host)\"} \([.extraChecks[] | select(.passed == false and .ignored == false)] | length)",
    "opencloud_version_info{host=\"\($host)\",version=\"\(.version)\",track=\"\(.releaseType)\"} 1"
  end' /tmp/opencloud-scan.json > "$TMP"

mv "$TMP" "$OUT"
chmod 644 "$OUT"
```

`opencloud_scan_success` macht einen fehlgeschlagenen Scan sichtbar. Ohne einen eigenen Erfolgswert könnten zuletzt gespeicherte Messwerte weiterhin wie ein aktuelles Ergebnis aussehen.

`lifecycle.daysRemaining` ist `null`, wenn das Supportende noch nicht datiert ist. Im Beispiel wird daraus mit `// 0` eine Null. Wenn Ihre Alarme dies als „endet heute“ interpretieren, lassen Sie diese Metrik stattdessen mit `select(.lifecycle.daysRemaining != null)` weg.

## Pushgateway {#pushgateway}

Verwenden Sie einen eigenen Gruppierungsschlüssel pro Host, um Ergebnisse getrennt zu halten:

```shell
check-opencloud-scanner scan --compact opencloud.example.com \
  | jq -r '
      "# TYPE opencloud_security_rating gauge",
      "opencloud_security_rating \(.rating)",
      "# TYPE opencloud_support_days_left gauge",
      "opencloud_support_days_left \(.lifecycle.daysRemaining // 0)"' \
  | curl -sS --data-binary @- \
      http://pushgateway.example.com:9091/metrics/job/opencloud_security/instance/opencloud.example.com
```

Pushgateway bewahrt die letzte übertragene Metrik auf. Löschen Sie die Gruppe, wenn Sie eine Instanz außer Betrieb nehmen:

```shell
curl -X DELETE http://pushgateway.example.com:9091/metrics/job/opencloud_security/instance/opencloud.example.com
```

## OpenTelemetry-Collector {#opentelemetry-collector}

`--format otlp` erzeugt einen OTLP/JSON-`ExportMetricsServiceRequest` für `/v1/metrics`. Das Plugin schreibt das Dokument; `curl` sendet es, beispielsweise aus demselben [systemd-Timer oder Cronjob](../scheduling.md):

```shell
check-opencloud-security --host opencloud.example.com,other.example.com \
  --format otlp \
  | curl -sf -X POST http://collector.example.com:4318/v1/metrics \
      -H 'Content-Type: application/json' --data-binary @-
```

Metriknamen und das Attribut `host` entsprechen dem Exporter. Berücksichtigen Sie bei Abfragen die Label-Konventionen Ihres Backends. Collector-Adresse, Proxy und Zugangsdaten werden beim Versand konfiguriert.

Auch ein fehlgeschlagener Scan liefert `opencloud_security_scrape_success` mit `0` und die Dauer, aber keine Befunde. So lässt sich ein nicht erreichbares Ziel von einem erfolgreichen Scan unterscheiden.

## Alarmregeln {#alerting-rules}

Für den nativen Exporter verwenden Sie [`contrib/prometheus/alerts.yml`](../../contrib/prometheus/alerts.yml). Diese Datei wird mit den tatsächlich ausgegebenen Metriknamen gepflegt und getestet.

Die folgenden Regeln verwenden dagegen die kürzeren Namen der `jq`-Beispiele:

```yaml
groups:
  - name: opencloud-security
    rules:
      - alert: OpenCloudEndOfLife
        expr: opencloud_end_of_life == 1
        for: 1h
        labels: {severity: critical}
        annotations:
          summary: "{{ $labels.host }} runs an OpenCloud release with no security fixes"

      - alert: OpenCloudSupportRunningOut
        expr: opencloud_support_days_left < 30 and opencloud_support_days_left > 0
        for: 6h
        labels: {severity: warning}
        annotations:
          summary: "{{ $labels.host }} loses support in {{ $value }} days"

      - alert: OpenCloudRatingDropped
        expr: opencloud_security_rating <= 3
        for: 1h
        labels: {severity: warning}
        annotations:
          summary: "{{ $labels.host }} is rated {{ $value }}/5"

      - alert: OpenCloudScanFailing
        # A scan that no longer runs is the failure mode that hides all others.
        expr: opencloud_scan_success == 0 or absent(opencloud_scan_success)
        for: 2h
        labels: {severity: warning}
        annotations:
          summary: "The OpenCloud security scan has not produced a result"
```

Wählen Sie `for:` nach der gewünschten Verzögerung und der Verfügbarkeit der Messwerte. Ein gecachtes Ergebnis kann eine Bedingung über mehrere Auswertungen erfüllen, ohne dass inzwischen ein neuer Scan stattgefunden hat.

## Grafana {#grafana}

Importieren Sie [`contrib/grafana/dashboard.json`](../../contrib/grafana/dashboard.json) und wählen Sie die Prometheus-Datenquelle. Das Dashboard zeigt Scanstatus, Note und Supportstatus, den Bewertungsverlauf, offene Befunde, Sicherheitshinweise nach Schweregrad und die installierten Versionen.

Für ein eigenes Dashboard verwenden Sie eine Skala von `0` bis `5`, bei der höhere Werte besser sind. Schwellwerte bei `3` (gelb) und `1` (rot) entsprechen den Plugin-Standards. Ordnen Sie die Zahlen den Noten zu: `5 → A+`, `4 → A`, `3 → C`, `2 → D`, `1 → E`, `0 → F`.

Zeigen Sie die Version neben der Bewertung an, damit ein möglicher Updatebedarf direkt erkennbar ist.

---

[Zur Dokumentationsübersicht](../README.md) | [Zum Haupt-README](../../README.md)

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
