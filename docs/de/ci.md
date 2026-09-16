# OpenCloud security checks in CI pipelines

# Scans in CI-Pipelines

Eine geplante Pipeline eignet sich für regelmäßige Scans oder für Prüfungen aus einem anderen Netzwerk. Überwachen Sie auch, ob die Pipeline tatsächlich läuft: Ein ausgebliebener Job liefert keinen Scanstatus.

Für alle Plattformen gelten dieselben Voraussetzungen:

- **Der Runner muss die Instanz erreichen.** Für private Ziele benötigen Sie einen Runner mit Zugriff auf das interne Netzwerk.
- **Der Standort bestimmt das Ergebnis.** TLS, HTTPS-Weiterleitungen und Debug-Ports werden aus Sicht des Runner-Netzes geprüft.
- **Der Exitcode steuert den Jobstatus.** `0` bedeutet OK, `1` WARNING, `2` CRITICAL und `3` UNKNOWN. Über `--warning` und `--critical` bestimmen Sie die Bewertungsschwellen.

## GitHub Actions {#github-actions}

### Die mitgelieferte Action {#the-action}

```yaml
name: OpenCloud security check

on:
  schedule:
    - cron: "0 6 * * *"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: sowoi/check-opencloud-security@v1.16.0
        with:
          target: opencloud.example.com
          # Raises GitHub's anonymous rate limit for the release feed. The
          # token the job already has is enough; it needs no scopes.
          releases-token: ${{ github.token }}
```

Die Action installiert die festgelegte Version, scannt die Instanz, schreibt `opencloud-security.json` und ergänzt die Jobzusammenfassung. Standardmäßig schlägt der Job bei WARNING, CRITICAL oder UNKNOWN fehl.

**Verwenden Sie einen festen Tag.** Referenzdaten werden mit dem Paket ausgeliefert und können die Bewertung beeinflussen. `@v1.16.0` installiert genau Version 1.16.0. Bei einem Branch- oder SHA-Verweis ohne ausdrückliche Versionsangabe wird das neueste Release installiert und eine Warnung ausgegeben.

| Eingabe | Standard | Funktion |
|:--|:--|:--|
| `target` | erforderlich | Hostname oder URL der Instanz |
| `version` | festgelegter Tag | Zu installierende Plugin-Version |
| `format` | `json` | `json`, `sarif`, `junit` oder `nagios` |
| `output-file` | `opencloud-security.json` | Ausgabedatei |
| `fail-on` | `warning` | `warning`, `critical` oder `never` |
| `warning` / `critical` | Plugin-Standards | Bewertungsschwellen |
| `check-hardening` | `true` | Härtungsmaßnahmen berücksichtigen |
| `ignore-hardening` | keine | Kommagetrennte Kennungen der Ausnahmen |
| `release-track` | `auto` | `auto`, `rolling`, `production` oder `lts` |
| `releases-token` | keines | Token für die Release-Abfrage |
| `summary` | `true` | Ergebnis in die Jobzusammenfassung schreiben |
| `extra-args` | keine | Weitere Argumente unverändert übergeben |

Die Ausgaben heißen `exit-code`, `status`, `rating`, `rating-label`, `message` und `result-file`. Außer `exit-code` und `status` stehen sie nur bei `format: json` zur Verfügung:

```yaml
      - uses: sowoi/check-opencloud-security@v1.16.0
        id: scan
        with:
          target: opencloud.example.com
          fail-on: never

      - name: Open an issue when the grade drops below A
        if: steps.scan.outputs.rating < 4
        run: gh issue create --title "OpenCloud is rated ${{ steps.scan.outputs.rating-label }}"
        env:
          GH_TOKEN: ${{ github.token }}
```

Mit `fail-on: never` bleibt der Scan-Schritt erfolgreich. Ein späterer Schritt kann dann anhand der ausgegebenen Werte entscheiden, wie weiter verfahren wird.

Vergewissern Sie sich vor dem Einsatz, dass der Runner die Instanz erreicht. Für Ziele hinter einer Firewall eignet sich ein selbst betriebener Runner im passenden Netzwerk.

### Befunde im Code-Scanning-Dashboard {#feeding-the-code-scanning-dashboard}

`format: sarif` erzeugt SARIF 2.1.0 für den Security-Bereich von GitHub:

```yaml
permissions:
  contents: read
  security-events: write

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: sowoi/check-opencloud-security@v1.16.0
        with:
          target: opencloud.example.com
          format: sarif
          output-file: opencloud-security.sarif
          # Upload the findings even when they are bad enough to fail a build.
          fail-on: never

      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: opencloud-security.sarif
          category: opencloud-security
```

Lassen Sie den Scan-Schritt mit `fail-on: never` fortfahren, damit die Datei auch bei Befunden hochgeladen wird. Werten Sie die hochgeladenen Befunde anschließend aus.

### Installation im eigenen Workflow {#installing-it-yourself-instead}

Sie können das Paket auch selbst installieren und denselben Befehl ohne die Action ausführen:

```yaml
name: OpenCloud security check

on:
  schedule:
    - cron: "0 6 * * *"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - name: Install the check
        run: pipx install check-opencloud-security==1.1.0

      - name: Scan the instance
        env:
          COS_HOST: opencloud.example.com
          COS_CHECK_HARDENING: "true"
          COS_UPDATE_WARNING: "true"
          # Raises GitHub's anonymous rate limit for the release feed. The
          # token GITHUB_TOKEN gives the job is enough; it needs no scopes.
          COS_RELEASES_TOKEN: ${{ github.token }}
        run: check-opencloud-security
```

Legen Sie die Paketversion fest, damit ein neues Release mit geänderten Referenzdaten nicht unbemerkt die Pipeline verändert. Mit `workflow_dispatch` können Sie nach einer Korrektur sofort einen weiteren Scan starten.

### Ergebnisse weitergeben {#reporting-rather-than-failing}

Wenn nach dem Scan weitere Schritte laufen sollen, erfassen Sie den Status und schreiben Sie das Ergebnis in die Jobzusammenfassung:

```yaml
      - name: Scan the instance
        id: scan
        continue-on-error: true
        env:
          COS_HOST: opencloud.example.com
          COS_CHECK_HARDENING: "true"
        run: |
          set +e
          check-opencloud-security > result.txt
          state=$?
          set -e
          cat result.txt
          echo "state=$state" >> "$GITHUB_OUTPUT"

      - name: Summarise
        run: |
          {
            echo "### OpenCloud security check"
            echo '```'
            cat result.txt
            echo '```'
          } >> "$GITHUB_STEP_SUMMARY"
```

Alternativ versendet das Plugin über `--webhook-url` eine Nachricht; siehe [Webhook-Beispiele](../webhook-recipes.md). Auch dieser Versand setzt voraus, dass der Workflow ausgeführt wird. Er überwacht keine deaktivierten oder ausgebliebenen Jobs.

### Einzelne JSON-Felder auswerten {#the-json-document-instead}

Für eigene Prüfregeln verwenden Sie das vollständige JSON von `check-opencloud-scanner`. Die Felder sind im [Bibliotheks-README](../../opencloud_local_scan/README.md) dokumentiert.

```yaml
      - name: Scan and keep the result
        run: |
          check-opencloud-scanner scan --compact opencloud.example.com > scan.json
          jq -e '.EOL == false' scan.json \
            || { echo "::error::The installed release no longer receives security fixes"; exit 1; }

      - uses: actions/upload-artifact@v4
        with:
          name: opencloud-scan
          path: scan.json
```

`jq -e` liefert einen Fehlercode, wenn der Ausdruck falsch ist. Damit können Sie etwa `.EOL`, `.rating`, `.updates.available` oder `.lifecycle.daysRemaining` als Pipeline-Bedingung verwenden.

### Nachweis der OpenCloud-Kompatibilität {#opencloud-compatibility-evidence}

Der Workflow **real OpenCloud container** prüft wöchentlich ein anhand seines Digests festgelegtes Rolling-Image. Er testet Initialisierung, öffentlichen Statusendpunkt, Produktkennung, Versionsangabe und einen gültigen Bewertungsbereich. Eine neue Version gilt erst nach Prüfung dieser Ergebnisse als bestätigt.

| Nachweis | Grundlage | Erfolgskriterium | Prüfung |
|:--|:--|:--|:--|
| Hersteller-Container | `opencloudeu/opencloud-rolling@sha256:0bb9038f4c01ab187a014e97550435f5d45630731aed9341d87a0b40fe72fe3d` | Vollständiger Integrationstest besteht; gemeldete Version und öffentliches Verhalten werden geprüft | Workflow mit `candidate_image` starten und Baseline nur über einen geprüften Pull Request ändern |
| Release-Lebenszyklus | Mitgelieferter Zeitplan und tägliche konservative Aktualisierung | Bestehende Supportinformationen bleiben erhalten, Regressionstests bestehen | Pull Request zur Zeitplanaktualisierung prüfen |
| Sicherheitshinweise | Mitgelieferte Datenbank und tägliche konservative Aktualisierung | Neue Hinweise ergänzen die Daten ohne bekannte betroffene Bereiche zu entfernen | Pull Request zur Datenbankaktualisierung prüfen |

Die Automatisierung ändert keine Fixtures, Bewertungen oder Sicherheitserwartungen, nur um einen Kandidaten bestehen zu lassen. Änderungen am beobachteten Verhalten benötigen Release-Nachweise und nachvollziehbare Testanpassungen.

Der Workflow `Supply-chain checks` läuft bei Pull Requests, Pushes auf `main` und wöchentlich. Er exportiert die aufgelösten Abhängigkeiten aus `uv.lock`, prüft Core-, Web- und MCP-Pakete mit `pip-audit` und veröffentlicht eine CycloneDX-SBOM als Artefakt. Pushes und geplante Läufe erhalten außerdem eine GitHub-Sigstore-Attestierung, prüfbar mit `gh attestation verify`. Der Release-Workflow wiederholt dies für die ausgelieferte Laufzeitumgebung und attestiert Paketdateien und Webbundle.

## GitLab CI {#gitlab-ci}

```yaml
opencloud-security:
  image: python:3.13-slim
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
  variables:
    COS_HOST: opencloud.example.com
    COS_CHECK_HARDENING: "true"
  before_script:
    - pip install --no-cache-dir check-opencloud-security==1.1.0
  script:
    - check-opencloud-security
  # WARNING (1) is worth seeing without failing the pipeline outright.
  allow_failure:
    exit_codes: [1]
```

Mit `allow_failure.exit_codes` erlauben Sie ausgewählte Statuswerte. `1` toleriert WARNING; `3` toleriert einen nicht abgeschlossenen Scan. Entscheiden Sie ausdrücklich, ob ein solcher Fehler den Job scheitern lassen soll.

Legen Sie den Zeitplan unter *Build → Pipeline schedules* an. Der `rules`-Block beschränkt den Job auf geplante Durchläufe.

## Ein eigenes Container-Image verwenden {#using-the-container-image-instead-of-installing}

Bauen Sie das Plugin-Image wie unter [Docker](../installation.md#docker) beschrieben, übertragen Sie es in Ihre Registry und legen Sie den Tag fest. Es läuft als unprivilegierter Benutzer und enthält einen `HEALTHCHECK`:

```shell
docker build -f docker/Dockerfile \
  -t registry.example.com/check-opencloud-security:1.1.0 .
docker push registry.example.com/check-opencloud-security:1.1.0

docker run --rm \
  -e COS_HOST=opencloud.example.com \
  -e COS_CHECK_HARDENING=true \
  registry.example.com/check-opencloud-security:1.1.0
```

## Zugangsdaten sicher übergeben {#do-not-put-the-token-on-the-command-line}

Übergeben Sie Secrets über Umgebungsvariablen wie `COS_RELEASES_TOKEN` und `COS_WEBHOOK_URL` oder als [Secret-Verweis](../../README.md#configuration-file-and-secrets). Vermeiden Sie Zugangsdaten in ausgeschriebenen Kommandozeilen. Das Plugin maskiert Tokens in seiner Diagnoseausgabe, kann aber weder Shell-Traces noch die Logausgabe anderer Programme bereinigen.

---

[Zur Dokumentationsübersicht](../README.md) | [Zum Haupt-README](../../README.md)

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
