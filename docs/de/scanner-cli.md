# Die Befehle von check-opencloud-scanner

Das Paket installiert zwei Programme:

- **`check-opencloud-security`** führt Scans aus und liefert anhand der Schwellwerte Nagios-/Icinga-Statuscodes von `0` bis `3`. Seine Optionen stehen in der [CLI-Referenz](../cli-reference.md).
- **`check-opencloud-scanner`** gibt das vollständige Ergebnis aus, vergleicht gespeicherte Scans, erklärt Befunde, aktualisiert Referenzdaten und betreibt den HTTP-Dienst. Es wendet keine WARNING- oder CRITICAL-Schwellwerte an.

Diese Seite beschreibt das zweite Programm.

## Globale Optionen {#global-options}

Globale Optionen stehen **vor** dem Unterbefehl:

```bash
check-opencloud-scanner -c /etc/check-opencloud-security/config.yml -v scan opencloud.example.com
```

| Option | Funktion |
|:--|:--|
| `-c, --config` | Konfigurationsdatei; `.json` wird als JSON, andere Endungen als YAML gelesen |
| `-v, --verbose` | Zusätzliche Meldungen auf stderr: `-v` für Info, `-vv` für Debug |

Ohne `-c` wird die erste vorhandene Datei aus dieser Reihenfolge verwendet:

1. `./.env.json`
2. `./check-opencloud-security.yml`
3. `./check-opencloud-security.yaml`
4. `~/.config/check-opencloud-security/.env.json`
5. `/etc/check-opencloud-security/.env.json`
6. `/etc/check-opencloud-security/config.yml`
7. `/etc/check-opencloud-security/config.yaml`

Das Plugin verwendet dieselbe Suche. `COS_`-Umgebungsvariablen überschreiben Dateieinstellungen; Kommandozeilenoptionen haben die höchste Priorität. Siehe [Zugangsdaten in der Konfiguration](../configuration.md).

## `scan`: Ergebnisdokument ausgeben {#scan-print-the-result-document}

```bash
check-opencloud-scanner scan opencloud.example.com
check-opencloud-scanner scan --compact opencloud.example.com > result.json
check-opencloud-scanner scan cloud1.example.com cloud2.example.com | jq '.[].rating'
```

Der Befehl gibt das JSON-Dokument mit Bewertung, Begründung, Lebenszyklus, Prüfungen, TLS-Messungen und Sicherheitshinweisen aus. Die Schlüssel verwenden camelCase. Ein Host ergibt ein Objekt, mehrere Hosts ein Array in der angegebenen Reihenfolge. Es wird kein Nagios-Status daraus abgeleitet.

| Option | Funktion |
|:--|:--|
| `--compact` | JSON ohne Einrückung in einer Zeile ausgeben |
| `--scheme {https,http}` | Protokoll für den Verbindungsaufbau |
| `--port` | Port überschreiben |
| `--timeout` | Zeitlimit pro Anfrage in Sekunden |
| `--insecure` | TLS-Zertifikatsprüfung deaktivieren |
| `--ca-file` | PEM-CA-Bundle für interne Zertifikate |
| `--no-extra-checks` | Nur Produkt, Version und Header prüfen |
| `--no-debug-ports` | Debug-Port-Prüfungen überspringen |
| `--all-addresses` | Wesentliche Prüfungen auf allen aufgelösten Adressen wiederholen |
| `--concurrency` | Parallele Anfragen innerhalb eines Scans; Standard `1` |
| `--no-update-check` | Neueste OpenCloud-Version nicht abfragen |

Ausnahmen, Release-Kanal und Advisory-Quellen werden wie beim Plugin über Konfiguration oder Umgebung festgelegt.

Ein nicht scanbarer Host erhält den Eintrag `{"host": ..., "error": ...}`. Weitere Hosts werden trotzdem geprüft; der Befehl endet dann mit `1`:

```json
{
  "host": "opencloud.example.com",
  "error": "https://opencloud.example.com/status.php is unreachable"
}
```

Das Dokument eignet sich für [CI-Pipelines](../ci.md), [Prometheus](../prometheus.md) und den Vergleich mit `diff`. Das [Bibliotheks-README](../../opencloud_local_scan/README.md) beschreibt die Felder.

## `diff`: gespeicherte Ergebnisse vergleichen {#diff-what-changed-between-two-saved-results}

```bash
check-opencloud-scanner scan opencloud.example.com > before.json
# ... change something on the instance ...
check-opencloud-scanner scan opencloud.example.com > after.json
check-opencloud-scanner diff before.json after.json
```

```text
opencloud.example.com: 2026-09-15 17:42:21.524291 -> 2026-09-15 17:42:22.737103
New since last run (15): check:debugEndpoint:/config, check:debugEndpoint:/debug/pprof/, check:debugEndpoint:/metrics, check:demoUsersDisabled, check:directoryListing (+10 more)
Security check: + debugEndpoint:/config
Security check: + demoUsersDisabled
...
Hardening: + Content-Security-Policy
...
Rating: A+ (5) -> D (2)
```

Der Befehl liest zwei Dateien und führt keinen Scan aus. `+` kennzeichnet neue, `-` behobene und `~` weiterhin offene Befunde mit geändertem Schweregrad. Er zeigt außerdem Änderungen an Bewertung, Version und Supportzeitraum. Für einen automatisch gespeicherten Vergleich mit dem letzten Lauf verwende stattdessen eine [Baseline](../baseline.md).

| Option | Funktion |
|:--|:--|
| `--format text` | Lesbare Textzeilen; Standard |
| `--format markdown` | Markdown-Tabelle für Tickets oder Kommentare |
| `--format side-by-side` | Beide Scans als zwei Spalten, ein Befund je Zeile |
| `--format json` | Strukturierter Vergleich wie im Plugin-Webhook |
| `--format slack` | Slack-Block-Kit-JSON |
| `--category NAME` | Nur einen Bereich zeigen; mehrfach angebbar |
| `--all-findings` | Alle gemessenen Befunde auflisten, nicht nur die veränderten |
| `--exit-zero` | Erfolgreiche Vergleiche unabhängig von Verschlechterungen mit `0` beenden |
| `--allow-different-hosts` | Ergebnisse unterschiedlicher Instanzen vergleichen |

Bei einer Verschlechterung im zweiten Ergebnis ist der Exitcode `1`, andernfalls `0`. `--exit-zero` unterdrückt diesen Fehlerstatus für Vergleiche.

Exitcode `2` bedeutet, dass kein Vergleich möglich ist:

- Die Dateien stammen von unterschiedlichen Instanzen und `--allow-different-hosts` wurde nicht gesetzt.
- Eine Datei ist kein verwertbares Ergebnis von `scan`, etwa weil die Bewertung fehlt oder sie nur einen Scanfehler enthält.

### Schweregrad, Befund für Befund {#severity-finding-by-finding}

Jeder Vergleich endet mit einer Zählung der fehlgeschlagenen Befunde nach Schweregrad:

```text
~ exposed:/config/opencloud.yaml [exposure]: severity high -> critical
Failing by severity: critical 0 -> 1, high 1 -> 1, medium 0 -> 1, low 1 -> 0
```

Die `~`-Zeile ist das, was ein Vergleich zweier Namenslisten nicht ausdrücken kann. Ein Check, der vorher bei `high` und jetzt bei `critical` fehlschlägt, tritt nie in die Menge der fehlschlagenden Checks ein oder aus ihr heraus - die [Baseline](../baseline.md) schweigt dazu also zu Recht -, während die Bewertung, die er deckelt, eine Note tiefer liegt. Der Schweregrad jeder Seite stammt aus den Dokumenten selbst, nie aus dem heutigen Katalog: Ein letzten Monat archivierter Scan ist ein Beleg für letzten Monat.

Ein per Waiver ausgenommener Befund wird hier mitgezählt und als `waived` dargestellt, denn ein Waiver ist die Entscheidung, nicht alarmiert zu werden, und keine Aussage darüber, dass der Befund weg ist.

### Nebeneinander {#side-by-side}

```bash
check-opencloud-scanner diff before.json after.json --format side-by-side
```

```text
opencloud.example.com
Rating: A+ (5) -> C (3)
Lifecycle: EOL: False -> True
Version: 3.4.0 -> 3.3.0

Finding                           2026-09-15T17:42:21+00:00  2026-09-22T09:03:11+00:00
--------------------------------  -------------------------  -------------------------
+ CVE-2026-0001                   not listed                 FAIL high
+ cspWithoutUnsafeInline          ok                         FAIL medium
~ exposed:/config/opencloud.yaml  FAIL high                  FAIL critical
- Referrer-Policy                 FAIL low                   ok
```

Jede Zeile nennt beide Seiten, sodass du sie dir nicht aus einer Änderungsliste zusammensuchen musst. `--all-findings` ergänzt die unveränderten Befunde und macht aus „was hat sich geändert" ein „was haben die beiden Scans gefunden".

`not measured` und `not listed` sind verschiedene Antworten und werden nie vermischt: Ein Check, der im Dokument fehlt, wurde nicht durchgeführt ([ADR 0064](https://github.com/sowoi/check-opencloud-security/blob/main/adr/0064-a-scan-records-what-it-did-not-measure.md)), während ein fehlender Sicherheitshinweis auf diese Version nicht zutraf. Beides ist kein Bestanden.

### Ein Bereich nach dem anderen {#one-area-at-a-time}

`--category` schränkt den Vergleich ein und nimmt einen Wert aus einem von zwei Namensräumen:

- **eine Befundkategorie** - `cookies`, `authentication`, `sharing`, `exposure`, `embedding`, `lifecycle`, `proxy`, `headers`, `transport`, `advisory` - behält nur die Befunde zu diesem Bereich der Instanz.
- **eine Änderungskategorie** - `instance`, `referenceData`, `scanner`, `policy`, `unknown` - behält nur die Erklärung, *warum* sich die beiden Scans unterscheiden. Siehe [Referenzdaten](reference-data.md) dazu, warum sich eine Note ändern kann, ohne dass sich die Instanz verändert hat.

```bash
check-opencloud-scanner diff before.json after.json --category transport
check-opencloud-scanner diff before.json after.json --category instance
```

Jeder Namensraum wird nur gefiltert, wenn du einen Wert dafür angibst: `--category transport` lässt die Erklärung unangetastet, `--category instance` die Befunde. Die Option ist mehrfach angebbar, und ein unbekannter Wert wird mit Exitcode `2` abgelehnt, statt stillschweigend nichts zu zeigen - ein Tippfehler, der einen leeren Vergleich ausgibt, liest sich wie „nichts hat sich geändert".

Eine gefilterte Erklärung lässt die `[limitation]`-Zeilen weg, weil diese den gesamten Vergleich einschränken und nicht eine einzelne Kategorie davon.

## `explain`: Befunde erklären {#explain-what-a-finding-means-and-how-to-fix-it}

```bash
check-opencloud-scanner explain basicAuthDisabled
```

```text
basicAuthDisabled: HTTP Basic authentication is enabled
    The instance answers with a 'WWW-Authenticate: Basic' challenge, so usernames and passwords can be replayed on every request without going through the identity provider, ...
    Setting: PROXY_ENABLE_BASIC_AUTH
    Fix: Set PROXY_ENABLE_BASIC_AUTH=false (the default) if nothing needs it. ...
    Docs: https://docs.opencloud.eu/docs/dev/server/services/proxy/environment-variables
```

Der Befehl sucht Kennungen im mitgelieferten Katalog und zeigt dieselben Erklärungen wie `--debug` und die Webanwendung. Er liest keine Konfiguration, benötigt kein Netzwerk und führt keinen Scan aus.

```bash
check-opencloud-scanner explain cspWithoutUnsafeInline Referrer-Policy   # several at once
check-opencloud-scanner explain exposed:/config/opencloud.yaml          # parameterised ids too
check-opencloud-scanner explain --list                                  # every identifier, one per line
check-opencloud-scanner explain --list --category cookies               # one category
check-opencloud-scanner explain --format json cookieSecure              # for a script
check-opencloud-scanner explain                                         # the whole catalogue
```

| Option | Funktion |
|:--|:--|
| `--list` | Nur Kennungen ausgeben |
| `--category` | Auf `cookies`, `authentication`, `sharing`, `exposure`, `embedding`, `lifecycle`, `proxy`, `headers` oder `transport` beschränken |
| `--format {text,json}` | JSON mit `id`, `category`, `title`, `meaning`, `remediation`, `reference`, `setting` und `actionable` ausgeben |

Bei einer unbekannten Kennung endet der Befehl mit `1` und schlägt ähnliche Kennungen vor:

```text
ERROR check_opencloud.cli: No catalogue entry for 'cookieSecur'. Did you mean: cookieSecure, cookieSameSite, cookiePrefix? Run `explain --list` for every identifier this build knows.
```

Die Kennungen entsprechen den Werten in der Alarmzeile, in `extraChecks[].id`, in `hardenings` und in den Ausnahmelisten. Ausführlichere Erklärungen stehen unter [Härtungsmaßnahmen](../hardening.md) und [Prüfumfang](../scanner-checks.md).

## `refresh-data`: Referenzdaten aktualisieren {#refresh-data-update-the-release-schedule-and-advisories}

```bash
check-opencloud-scanner refresh-data --output-dir /var/lib/check-opencloud-security
```

Der Befehl lädt Release-Zeitplan und Schwachstellendatenbank aus dem Projekt-Repository, prüft sie und schreibt sie nach `--output-dir`. Die Signaturprüfung benötigt das Extra `signing`; nicht prüfbare Signaturen führen zu einer Warnung, ungültige Signaturen zum Abbruch. Bei Erfolg werden beide Pfade ausgegeben und der Exitcode ist `0`. Ein abgelehnter Refresh schreibt nichts und endet mit `1`.

| Option | Standard | Funktion |
|:--|:--|:--|
| `--output-dir` | `~/.cache/check-opencloud-security` | Zielverzeichnis |
| `--timeout` | `30` | Zeitlimit pro Anfrage in Sekunden |
| `--schedule-url` | keine | Alternative Lebenszyklusseite ohne Signaturprüfung |
| `--advisory-url` | keine | Alternativer OSV-Endpunkt ohne Signaturprüfung |

Trage die Dateien anschließend in die Konfiguration ein und prüfe ihre Lesbarkeit unter dem Benutzer des Checks. Eine unlesbare eigene Zeitplandatei deaktiviert die End-of-Life-Prüfung. Details stehen unter [Referenzdaten aktualisieren](../reference-data.md).

## `serve`: HTTP-Dienst betreiben {#serve-the-scan-service}

```bash
check-opencloud-scanner serve
check-opencloud-scanner serve --listen 0.0.0.0 --token "$(cat /run/secrets/scanner_token)"
```

Der HTTP-Dienst stellt mehreren Verbrauchern ein zwischengespeichertes Ergebnis pro Instanz bereit.

| Option | Standard | Einstellung |
|:--|:--|:--|
| `--listen` | `127.0.0.1` | `service.listen` / `COS_SERVICE_LISTEN` |
| `--port` | `8811` | `service.port` / `COS_SERVICE_PORT` |
| `--cache-ttl` | `900` Sekunden | `service.cache_ttl` / `COS_SERVICE_CACHE_TTL` |
| `--token` | keines | `service.token` / `COS_SERVICE_TOKEN` |
| `--concurrency` | `1` | Parallele Anfragen innerhalb eines Scans |
| `--insecure` | aus | Zertifikatsprüfung der gescannten Instanzen deaktivieren |

Außerhalb von Loopback verlangt der Dienst ein Token. Fehlt es, erscheint `UNKNOWN: ...` auf stderr und der Prozess endet mit `3`. Die Endpunkte stehen im [Haupt-README](../../README.md#running-the-scanner-as-a-service), Containerbeispiele unter [Scan-Dienst](../scan-service.md).

Die [öffentliche Webanwendung](../webapp.md) mit Browseroberfläche und Warteschlange ist ein separater Dienst.

## `configure`: Konfigurationsdatei erstellen {#configure-write-a-configuration-file}

```bash
check-opencloud-scanner configure
check-opencloud-scanner -c /etc/check-opencloud-security/.env.json configure
```

Der Assistent erklärt die Einstellungen und speichert sie als JSON mit Dateirechten nur für den Eigentümer. Er bietet `./.env.json`, `~/.config/check-opencloud-security/.env.json` und `/etc/check-opencloud-security/.env.json` an; über `-c` kannst du einen anderen Pfad wählen. Es ist derselbe Assistent wie bei `check-opencloud-security --configure`.

| Option | Funktion |
|:--|:--|
| `--all` | Optionale Einstellungen ohne vorherige Auswahl durchgehen |
| `--force` | Vorhandene Datei ohne Rückfrage ersetzen |
| `--no-test-scan` | Vor dem Speichern keinen Testscan anbieten |

## Exitcodes {#exit-codes}

Die Scanner-CLI verwendet eigene Exitcodes. Ein erfolgreich gescannter Host mit Note F führt bei `scan` weiterhin zu `0`; die Nagios-Bewertung übernimmt das Plugin.

| Unterbefehl | `0` | `1` | `2` | `3` |
|:--|:--|:--|:--|:--|
| `scan` | Alle Hosts gescannt | Mindestens ein Host nicht scanbar | Ungültige Konfiguration | – |
| `diff` | Keine Verschlechterung | Zweites Ergebnis schlechter | Dateien nicht vergleichbar | – |
| `explain` | Ausgabe erstellt | Unbekannte Kennung oder leere Kategorie | – | – |
| `refresh-data` | Beide Dateien geschrieben | Nichts geschrieben; siehe stderr | – | – |
| `serve` | Regulär beendet | – | Ungültige Konfiguration | Start verweigert, etwa ohne Token außerhalb von Loopback |

Ungültige Kommandozeilenargumente führen bei allen Unterbefehlen zu Exitcode `2`.

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
