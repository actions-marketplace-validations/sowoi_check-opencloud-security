# Nur Änderungen melden

Mit `--baseline` speichert das Plugin die Befunde eines Durchlaufs und vergleicht den nächsten Scan damit. Zusammen mit `--warn-on-new` kannst du die Alarmierung auf neue oder verschlechterte Befunde beschränken. Bereits bekannte Probleme bleiben im Bericht sichtbar.

Eine Kurzfassung findest du im [Haupt-README](../../README.md#reporting-only-what-changed). Dieser Leitfaden erklärt die Vergleichsformate, die Kriterien für Verschlechterungen und den Umgang mit der Baseline-Datei.

## Baseline speichern und vergleichen {#writing-and-comparing-a-baseline}

Gib mit `--baseline` die Datei an, in der die Befunde gespeichert und beim nächsten Durchlauf zum Vergleich gelesen werden:

```bash
check-opencloud-security -H opencloud.example.com \
    --check-hardening \
    --baseline /var/lib/check_opencloud/baseline.json
```

Ohne weitere Optionen ergänzt das Plugin nur die Ausgabe um eine Zeile `Baseline: ...`. Mit `--warn-on-new` beeinflusst der Vergleich auch die Alarmierung:

```bash
check-opencloud-security -H opencloud.example.com \
    --check-hardening \
    --baseline /var/lib/check_opencloud/baseline.json \
    --warn-on-new
```

Solange keine neuen oder verschlechterten Befunde vorliegen, meldet das Plugin `OK`. Bei einer Verschlechterung gilt wieder der reguläre Status. Der vollständige Zustand wird in beiden Fällen ausgegeben:

```
OK: nothing new since the last run (WARNING state unchanged).
OpenCloud 7.2.3 on opencloud.example.com, rating: C, last scanned: 2026-01-14
Missing hardening: cspWithoutUnsafeInline (run with --debug for what each means and how to fix it)
Baseline: No new findings since 2026-01-14T09:00:00+00:00 (1 known issue(s) unchanged)
Suppressed by --warn-on-new: this run would otherwise be WARNING (WARNING: 1 hardening measure(s) missing, but no known vulnerabilities.)
```

Der Vergleich zeigt hinzugekommene und behobene CVEs, Änderungen an Härtungsmaßnahmen und zusätzlichen Prüfungen sowie Änderungen an Bewertung, Supportende, Supportzeitraum und installierter oder empfohlener Version. `text` eignet sich für Logs und ist der Standard. Für eine Zusammenfassung in GitHub Actions oder einen Pull-Request-Kommentar verwende Markdown:

```shell
check-opencloud-security -H opencloud.example.com \
  --baseline /var/lib/check_opencloud/baseline.json \
  --diff-format markdown >> "$GITHUB_STEP_SUMMARY"
```

`--diff-format slack` oder `json` erzeugt Slack-Block-Kit-JSON. Bei einem konfigurierten Webhook enthält `baseline_diff` jeden Vergleich. Das Slack-Format ergänzt auf oberster Ebene außerdem die Blöcke und das farbige Banner für eingehende Webhooks:

```shell
check-opencloud-security -H opencloud.example.com \
  --baseline /var/lib/check_opencloud/baseline.json \
  --diff-format slack --webhook-url 'https://hooks.slack.com/services/<token>' \
  --webhook-on always
```

## Was als Verschlechterung zählt {#what-counts-as-a-regression}

- Ein neuer Befund: etwa eine weitere Schwachstelle, eine weggefallene Schutzmaßnahme, eine erstmals fehlgeschlagene Zusatzprüfung oder ein neu verfügbares Update.
- Eine niedrigere Bewertung als beim vorherigen Durchlauf.
- **Eine Version nach ihrem Supportende, bei jedem Scan.** Da sie keine Sicherheitsupdates mehr erhält, unterdrückt eine Baseline diesen Alarm niemals.

## Konfigurationsänderungen {#configuration-drift}


Eine Baseline merkt sich auch den **Konfigurations-Fingerabdruck** des Scans:
gruppierte Digests davon, wie die Instanz eingerichtet ist - Transport,
Header, Freigaben, Anmeldung, Proxy - und nichts davon, worauf. Ein Lauf, bei
dem Note und Befunde gleich geblieben sind, sagt trotzdem, wenn die
Installation das nicht ist:

```text
Baseline: No new findings since 2026-09-14T06:00:00Z, but the configuration changed (headers, proxy)
```

Gemeldet werden nur die Gruppennamen. Was die Einstellung jetzt sagt, steht
weder in der Baseline-Datei noch in der Ausgabe oder im Webhook - nur ein Hash
davon -, also kann die Datei neben dem übrigen Monitoring-Zustand liegen, ohne
zu veröffentlichen, wie die Instanz konfiguriert ist.

Eine Änderung wird gemeldet, nicht bewertet: Sie erzeugt keinen Befund, macht
keinen Lauf zur Verschlechterung und ändert nie den Exit-Code. Eine Baseline
aus der Zeit vor den Fingerabdrücken meldet schlicht keine Änderung - die
ehrliche Antwort für eine Datei, die es nicht sagen kann.

## Verhalten und Dateirechte {#points-worth-knowing}

- Der erste Durchlauf meldet den regulären Status und legt die Baseline an. Ohne Vergleichsdaten wird nichts unterdrückt.
- Eine Datei enthält einen Eintrag pro Host und kann für eine kommagetrennte `--host`-Liste verwendet werden.
- Mit `--ignore-hardening` ausgenommene Befunde und von OpenCloud fest vorgegebene Maßnahmen bleiben wie in der Alarmzeile unberücksichtigt.
- `--warn-on-new` ohne `--baseline` wird abgelehnt, da der Vergleich eine gespeicherte Ausgangslage benötigt.
- Kann die Datei nicht geschrieben werden, erscheint ein Hinweis in der Ausgabe. Die Bewertung der Instanz bleibt davon unberührt.
- Die Datei wird atomar geschrieben und ist nur für den Eigentümer zugänglich. Verwende ein Verzeichnis des Monitoring-Benutzers, etwa `/var/lib/check_opencloud/`.

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
