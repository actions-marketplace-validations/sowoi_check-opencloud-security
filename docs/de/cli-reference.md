# CLI-Optionen des Monitoring-Plugins

Hier findest du alle Optionen von `check-opencloud-security`, ihre Standardwerte und die zugehörigen Umgebungsvariablen. Das [Haupt-README](../../README.md) erklärt den Einsatz mit Beispielen.

Es gilt stets **Kommandozeile > Umgebungsvariable > Konfigurationsdatei > Standard**. Details stehen unter [Konfiguration](../../README.md#configuration-file-and-secrets) und [Umgebungsvariablen](../../README.md#environment-variables). `check-opencloud-security -h` zeigt die Optionen im Terminal.

## Befehl {#command}

```shell
check-opencloud-security --host <Hostname> --check-hardening
```

## Optionen {#options}

| Option | Beschreibung | Standard | Umgebungsvariable |
|:--|:--|:--|:--|
| `-H, --host`                  | OpenCloud-Adresse als Hostname, IP oder URL, optional mit Port; mehrere Hosts durch Kommas trennen | **erforderlich**                                    | `COS_HOST`                      |
| `-P, --proxy`                 | Adresse des ausgehenden Proxys | keiner                                          | `COS_PROXY`                     |
| `-d, --debug`                 | Bewertung und Befunde erklären; ausführliche Diagnoseausgabe | `false`                                         | `COS_DEBUG`                     |
| `-w, --warning`               | Ab dieser Bewertung oder darunter WARNING melden | `3` (`C`)                                       | `COS_WARNING`                   |
| `-c, --critical`              | Ab dieser Bewertung oder darunter CRITICAL melden | `1` (`E`)                                       | `COS_CRITICAL`                  |
| `--check-hardening`           | Fehlende Härtungsmaßnahmen und Sicherheitsheader berücksichtigen | `false`                                         | `COS_CHECK_HARDENING`           |
| `--timeout`                   | HTTP-Zeitlimit pro Anfrage in Sekunden | `10`                                            | `COS_TIMEOUT`                   |
| `--port`                      | Zielport; OpenClouds eigener Proxy verwendet 9200 | aus `--host`, sonst `443`                       | `COS_SCANNER_TARGET_PORT`       |
| `--scheme`                    | Protokoll: https oder http; HTTPS kann auf HTTP zurückfallen | `https`                                         | `COS_SCANNER_SCHEME`            |
| `--insecure`                  | TLS-Zertifikatsprüfung deaktivieren | `false`                                         | `COS_INSECURE`                  |
| `--ca-file`                   | PEM-CA-Bundle für ein internes Zertifikat | keiner (System-Vertrauensspeicher)                     | `COS_SCANNER_TLS_CA_FILE`       |
| `--no-extra-checks`           | Nur Produkt, Version und Sicherheitsheader prüfen | `false`                                         | `COS_NO_EXTRA_CHECKS`           |
| `--no-debug-ports`            | OpenCloud-Debug-Ports nicht prüfen | `false`                                         | `COS_NO_DEBUG_PORTS`            |
| `--all-addresses`             | Version, Header, Härtung und Demokonten auf allen aufgelösten Adressen prüfen | `false`                                         | `COS_ALL_ADDRESSES`             |
| `--login-throttling`          | Sechs fehlgeschlagene Anmeldungen für ein nicht existierendes Konto senden und melden, ob sie gebremst wurden (nie bewertet) | `false` | `COS_LOGIN_THROTTLING` |
| `--concurrency`               | Maximale Zahl paralleler Host-Worker | `5`                                             | `COS_CONCURRENCY`               |
| `--format`                    | Ausgabeformat: nagios, prometheus, otlp, checkmk, json, sarif oder junit | `nagios`                                        | `COS_FORMAT`                    |
| `--prometheus-listen-port`    | Dauerhaften Exporter mit /metrics auf diesem Port starten | deaktiviert                                        | `COS_PROMETHEUS_LISTEN_PORT`    |
| `--prometheus-listen-addr`    | Bind-Adresse des Prometheus-Exporters | `127.0.0.1`                                     | `COS_PROMETHEUS_LISTEN_ADDR`    |
| `--scrape-interval`           | Ergebnisse des Exporters so viele Sekunden cachen; 0 scannt bei jedem Abruf | `60`                                            | `COS_SCRAPE_INTERVAL`           |
| `--ignore-hardening`          | Befund ausnehmen; wiederholbar, kommagetrennt und mit Platzhaltern | keiner                                          | `COS_SCANNER_IGNORE_HARDENINGS` |
| `--release-track`             | Release-Kanal: rolling, production, lts oder auto | `auto`                                          | `COS_SCANNER_RELEASE_TRACK`     |
| `--update-source`             | Updatequelle: auto, feed, pinned, bundled oder off | `auto`                                          | `COS_UPDATE_SOURCE`             |
| `--release-feed`              | URL der Release-Quelle | GitHub-Release-API von `opencloud-eu/opencloud` | `COS_RELEASES_FEED_URL`         |
| `--release-token`             | Token für die Release-Abfrage | keiner                                          | `COS_RELEASES_TOKEN`            |
| `--latest-version`            | Neueste Version ausdrücklich vorgeben; setzt update-source auf pinned | keiner                                          | `COS_RELEASES_LATEST_VERSION`   |
| `--no-update-check`           | Update-Prüfung deaktivieren | `false`                                         | `COS_NO_UPDATE_CHECK`           |
| `--update-warning`            | Bei einem verfügbaren Update WARNING melden | `false`                                         | `COS_UPDATE_WARNING`            |
| `--eol-warning TAGE`          | WARNING melden, wenn die Release-Linie in höchstens TAGE Tagen ihr Supportende erreicht (`0` ist aus) | `0`                                             | `COS_EOL_WARNING`               |
| `--baseline`                  | Baseline-Datei mit einem Eintrag pro Host | keiner                                          | `COS_BASELINE`                  |
| `--warn-on-new`               | Nur bei neuen oder verschlechterten Befunden alarmieren; benötigt --baseline | `false`                                         | `COS_WARN_ON_NEW`               |
| `--diff-format`               | Vergleich als text, markdown oder Slack Block Kit mit slack/json ausgeben | `text`                                          | `COS_DIFF_FORMAT`               |
| `--self-update-check`         | Auf eine neuere Plugin-Version auf PyPI hinweisen; Exitcode unverändert lassen | `false`                                         | `COS_SELF_UPDATE_CHECK`         |
| `--webhook-url`               | Webhook-Ziel für Benachrichtigungen | keiner (deaktiviert)                               | `COS_WEBHOOK_URL`               |
| `--webhook-on`                | Niedrigster auslösender Status: critical, warning, unknown oder always | `critical`                                      | `COS_WEBHOOK_ON`                |
| `--webhook-format`            | Webhook-Format: generic, slack, discord, ntfy oder gotify | `generic`                                       | `COS_WEBHOOK_FORMAT`            |
| `--webhook-header`            | Zusätzlicher Webhook-Header; wiederholbar | keiner                                          | `COS_WEBHOOK_HEADERS`           |
| `--webhook-secret`            | Gemeinsames Geheimnis für HMAC-SHA256-Signaturen in X-COS-Signature | keiner (unsigniert)                               | `COS_WEBHOOK_SECRET`            |
| `--webhook-timeout`           | HTTP-Zeitlimit des Webhooks in Sekunden | `10`                                            | `COS_WEBHOOK_TIMEOUT`           |
| `--allow-private-webhooks`    | Webhooks zu privaten, Loopback- oder Link-Local-Adressen erlauben | `false`                                         | `COS_ALLOW_PRIVATE_WEBHOOKS`    |
| `--webhook-digest`            | Benachrichtigungen mehrerer Hosts eines Aufrufs zusammenfassen | `false`                                         | `COS_WEBHOOK_DIGEST`            |
| `--retries`                   | Wiederholungen bei vorübergehenden Netzwerkfehlern | `2`                                             | `COS_RETRIES`                   |
| `--backoff-factor`            | Faktor für exponentielle Wartezeiten zwischen Wiederholungen, in Sekunden | `0.5`                                           | `COS_BACKOFF_FACTOR`            |
| `--config`                    | Konfigurationsdatei; .json als JSON, andere Endungen als YAML | automatisch gesucht                                 | `COS_CONFIG_FILE`               |
| `--configure`                 | Interaktive Konfiguration speichern und beenden | —                                               | —                               |
| `--upgrade-self [run\|check]` | Mit pipx, uv oder pip aktualisieren; check zeigt nur den Befehl | `run` ohne angegebenen Wert                | —                               |
| `--check-only`                | Alternative Schreibweise für --upgrade-self check | —                                               | —                               |
| `-V, --version`               | Installierte Version anzeigen und beenden | —                                               | —                               |
| `-h, --help`                  | Hilfe anzeigen und beenden | —                                               | —                               |

## Einstellungen ohne eigene CLI-Option {#settings-with-no-flag-of-their-own}

Das Warnfenster für den Zertifikatsablauf, die Liste der Debug-Ports und die Advisory-Quellen werden über die [Konfigurationsdatei](../../README.md#configuration-file-and-secrets) oder `COS_SCANNER_*`-Variablen gesetzt. Die [Beispielkonfiguration](../../config/check-opencloud-security.example.yml) beschreibt jede Einstellung.

## Weiterführende Anleitungen {#where-to-go-next}

| Seite | Inhalt |
|:--|:--|
| [Haupt-README](../../README.md) | Erläuterungen und Beispiele |
| [Konfigurationsdatei und Zugangsdaten](../../README.md#configuration-file-and-secrets) | Einstellungen dauerhaft speichern |
| [Ausgabeformate](../output-formats.md) | JSON, SARIF, JUnit und Metriken |
| [Checkmk](../checkmk.md) | Aktive und lokale Checks |
| [Mehrere Instanzen](../many-instances.md) | Hostlisten und getrennte Konfigurationsdateien |
| [Fehlersuche](../troubleshooting.md) | Fehlermeldungen und Exitcodes |

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
