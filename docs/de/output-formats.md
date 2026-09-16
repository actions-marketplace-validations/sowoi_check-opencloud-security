# Ausgabeformate

Standardmäßig gibt das Plugin eine Nagios-Statuszeile mit Performancedaten aus. Mit `--format` (`COS_FORMAT`) wähle stattdessen ein Format für Skripte, Dashboards oder CI-Pipelines.

`json`, `sarif` und `junit` erzeugen jeweils **ein gemeinsames Dokument für alle gescannten Hosts**. Das Format bleibt auch bei nur einem Host gleich.

Die Exitcodes behalten ihre Nagios-Bedeutung: `0` für OK, `1` für WARNING, `2` für CRITICAL und `3` für UNKNOWN. Eine CI-Pipeline kann damit den Status auswerten und das Dokument zusätzlich als Artefakt speichern. Die Metrikformate `prometheus` und `otlp` bilden eine Ausnahme: Du gibst Befunde als Messwerte aus und beenden den Prozess mit `0`.

## `json` {#json}

Ein JSON-Array mit einem Objekt pro Host, auch bei nur einer Instanz. Die Objekte entsprechen dem unter [Webhook-Benachrichtigungen](../../README.md#webhook-notifications) beschriebenen Ergebnisdokument. Dieses Format eignet sich für die Weiterverarbeitung in Skripten oder anderen Diensten.

```shell
check-opencloud-security --host opencloud.example.com --format json
```

## `sarif` {#sarif}

[SARIF](https://sarifweb.azurewebsites.net/) 2.1.0 eignet sich für Code-Scanning-Dashboards, etwa in GitHub. Die Befunde stammen aus denselben Härtungsprüfungen, Zusatzprüfungen, Schwachstellendaten und Supportinformationen wie die Textausgabe.

```shell
check-opencloud-security --host opencloud.example.com --format sarif \
  > opencloud-security.sarif
```

In GitHub Actions kannst du die Datei anschließend hochladen. `continue-on-error: true` stellt sicher, dass der Upload auch bei einem nicht erfolgreichen Scanstatus ausgeführt wird:

```yaml
- name: Scan OpenCloud
  run: |
    check-opencloud-security --host opencloud.example.com --format sarif \
      > opencloud-security.sarif
  continue-on-error: true
- uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: opencloud-security.sarif
```

## `junit` {#junit}

JUnit-XML enthält eine `<testsuite>` pro Host und einen `<testcase>` pro Befund. Ein Testfall `rating` ist immer enthalten, damit auch ein Host ohne Befunde im Bericht erscheint.

```shell
check-opencloud-security --host opencloud.example.com --format junit \
  > opencloud-security.xml
```

Richte den JUnit-Reporter Ihres CI-Systems auf diese Datei aus, um die Befunde als Testergebnisse anzuzeigen.

## `checkmk` {#checkmk}

Das Format erzeugt eine [Checkmk-Local-Check-Zeile](../checkmk.md) pro Host: Status, Dienstname in Anführungszeichen, Metriken und Detailtext.

```shell
check-opencloud-security --host opencloud.example.com --format checkmk
```

Mehrere Hosts ergeben mehrere Zeilen und damit mehrere Services. Das Format ist für Checks auf dem Agent-Host vorgesehen. Ein aktiver Check auf dem Checkmk-Server kann die standardmäßige `nagios`-Ausgabe direkt lesen. Der [Checkmk-Leitfaden](../checkmk.md) erklärt beide Varianten und ihre Metriken.

## `otlp` {#otlp}

Dieses Format gibt die Prometheus-Metriken als OTLP/JSON aus. Ein `ExportMetricsServiceRequest` enthält alle gescannten Hosts und kann per OTLP/HTTP an `POST /v1/metrics` eines OpenTelemetry-Collectors gesendet werden.

```shell
check-opencloud-security --host opencloud.example.com --format otlp \
  | curl -sf -X POST http://collector.example.com:4318/v1/metrics \
      -H 'Content-Type: application/json' --data-binary @-
```

Das Plugin schreibt nur das Dokument auf die Standardausgabe. Den Versand übernimm beispielsweise mit `curl` im bestehenden Timer. Collector-Adresse, Proxy und Zugangsdaten konfiguriere beim Versand.

Jeder Host wird über das Attribut `host` unterschieden. Alle Metriken sind Gauges, also aktuelle Messwerte. Namen und Werte entsprechen dem Prometheus-Exporter; je nach Backend können Attributnamen anders abgebildet werden. Die gemeinsame Tabelle steht unter [Prometheus und Grafana](../prometheus.md#what-the-exporter-publishes).

Wie `--format prometheus` beendet sich dieses Format auch bei Befunden mit `0`. Ein fehlgeschlagener Scan liefert `opencloud_security_scrape_success 0`. Wenn der Exitcode die Alarmierung steuern soll, verwende `nagios`, `json`, `sarif` oder `junit`.

## Das passende Format wählen {#choosing-a-format}

| Format | Einsatz |
|:--|:--|
| `nagios` | Standard für Monitoring mit Statuszeile und Exitcode |
| `prometheus` | Metriken für Scraping oder Textfile Collector; siehe [Prometheus und Grafana](../prometheus.md) |
| `otlp` | Dieselben Metriken für einen OpenTelemetry-Collector unter `/v1/metrics` |
| `json` | Ergebnisse in eigenen Programmen verarbeiten |
| `sarif` | Befunde in einem Code-Scanning-Dashboard anzeigen |
| `junit` | Befunde als Testergebnisse in CI anzeigen |
| `checkmk` | Lokaler Check auf einem Checkmk-Agent-Host |

[Scans in CI-Pipelines](../ci.md) zeigt vollständige Beispiele für GitHub Actions und GitLab CI, einschließlich der Auswertung einzelner JSON-Felder.

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
