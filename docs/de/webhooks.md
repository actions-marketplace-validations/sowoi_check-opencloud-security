# OpenCloud security scanner webhook recipes

# Webhook-Beispiele

Der [Webhook](../../README.md#webhook-notifications) sendet standardmäßig das JSON-Ergebnis des Plugins. Mit `--webhook-format` können Sie direkt Slack-, Discord-, ntfy- oder Gotify-Nachrichten erzeugen. Für andere Empfänger verwenden Sie das generische Dokument oder einen eigenen Adapter.

Dabei gelten zwei Regeln:

- **Ein Zustellfehler verändert den Checkstatus nicht.** Das Plugin ergänzt `Webhook delivery failed` und behält den gemessenen Exitcode bei.
- **Schützen Sie URL und Tokens.** Webhook-URLs enthalten häufig bereits die Zugangsberechtigung. Verwenden Sie `COS_WEBHOOK_URL` oder einen Secret-Verweis in der [Konfiguration](../../README.md#configuration-file-and-secrets).

## Die wichtigsten Felder {#the-payload-in-short}

| Feld | Bedeutung |
|:--|:--|
| `status`, `exit_code` | OK, WARNING, CRITICAL oder UNKNOWN und der Code `0` bis `3` |
| `message` | Lesbare Begründung |
| `rating`, `rating_label` | Bewertung `0` bis `5` und Note A+ bis F |
| `host`, `product_version` | Instanz und installierte Version |
| `eol` | Ob das Supportende erreicht ist |
| `update.availableVersion` | Empfohlenes Update |
| `failed_extra_checks`, `missing_hardenings` | Befunde |

Bei einem fehlgeschlagenen Scan stehen nur `plugin`, `plugin_version`, `timestamp`, `host`, `status`, `exit_code` und `message` zur Verfügung. Empfänger müssen mit einem fehlenden `rating` umgehen können.

## Vollständiger Payload {#the-full-payload}

Beispiel eines generischen Dokuments für eine Version nach dem Supportende:

```json
{
  "plugin": "check-opencloud-security",
  "plugin_version": "1.0.0",
  "timestamp": "2026-08-07T10:12:33.123456+00:00",
  "host": "opencloud.example.com",
  "status": "CRITICAL",
  "exit_code": 2,
  "message": "CRITICAL: The 7.3 rolling release line is end-of-life and has no security fixes. Upgrade to 7.4.0.",
  "rating": 0,
  "rating_label": "F",
  "product": "OpenCloud",
  "product_version": "7.3.0",
  "domain": "opencloud.example.com",
  "scanned_at": "2026-08-12 15:24:13.978540",
  "eol": true,
  "release_type": "rolling",
  "lifecycle": {
    "line": "7.3",
    "releaseType": "rolling",
    "state": "endOfLife",
    "released": "2026-07-14",
    "endOfLife": "2026-08-03",
    "daysRemaining": -9,
    "latestOnLine": null,
    "upgradeTo": "7.4.0",
    "reason": "rolling release, unsupported since 2026-08-03",
    "scheduleStale": false,
    "scheduleUpdated": "2026-08-12",
    "scheduleSource": "https://docs.opencloud.eu/docs/admin/resources/lifecycle/",
    "scheduleNote": null
  },
  "vulnerability_count": 0,
  "vulnerabilities": [],
  "missing_hardenings": [],
  "failed_extra_checks": ["exposed:/opencloud.yaml"],
  "scan_backend": "local",
  "scan_uuid": "6a1d1bd0-...",
  "update": {"available": true, "version": "7.3.0", "availableVersion": "7.4.0", "releasedAt": "2026-08-03", "source": "feed", "error": null, "track": "rolling", "newestRelease": null},
  "duration_seconds": 1.234
}
```

`scan_backend` ist immer `"local"` und bezeichnet den eingebauten Scanner. Bei einem Scanfehler werden nur die oben genannten gemeinsamen Felder gesendet.

## Generischer Empfänger {#a-generic-receiver}

Log-Pipelines, Webhook-Sammler sowie n8n- oder Node-RED-Abläufe können das JSON unverändert übernehmen:

```shell
export COS_WEBHOOK_URL='https://collector.example.com/hooks/opencloud'
export COS_WEBHOOK_HEADERS='Authorization: Bearer abc123; X-Env: prod'
check-opencloud-security --host opencloud.example.com --webhook-on warning
```

`--webhook-on` legt fest, welche Statuswerte eine Nachricht auslösen. Die Stufen `critical`, `warning`, `unknown` und `always` schließen jeweils die schwerwiegenderen Statuswerte ein.

## Signatur prüfen {#verifying-the-signature}

`--webhook-secret` oder `COS_WEBHOOK_SECRET` ergänzt eine HMAC-Signatur. Ein Empfänger mit demselben Geheimnis kann damit die Nachricht verifizieren:

```shell
export COS_WEBHOOK_SECRET='a-long-random-string'
check-opencloud-security --host opencloud.example.com --webhook-on warning
```

Jeder POST enthält anschließend:

```
X-COS-Signature: sha256=<hex>
```

`<hex>` ist die HMAC-SHA256-Signatur der **unveränderten Request-Bytes**. Prüfen Sie genau den empfangenen Body. Erneutes Serialisieren des JSON kann Leerzeichen oder Schlüsselreihenfolge verändern und ergibt dann einen anderen Hash.

```python
import hashlib
import hmac

def verify(raw_body: bytes, header: str, secret: str) -> bool:
    """raw_body must be the untouched request body, not a re-serialised dict."""
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, header or "")
```

Verwenden Sie `hmac.compare_digest` für den Vergleich. In FastAPI liefert `await request.body()` die Rohdaten, in Flask `request.get_data()`. Lesen Sie den Body vor dem Parsen, wenn Ihr Framework sonst nur ein JSON-Objekt bereitstellt.

- Die Signatur umfasst auch die von `slack`, `discord`, `ntfy` und `gotify` erzeugten Dokumente. Die Dienste selbst müssen den zusätzlichen Header nicht auswerten.
- Ohne konfiguriertes Geheimnis wird kein Signaturheader gesendet. Ein Empfänger mit Signaturpflicht muss eine solche Anfrage ablehnen.
- Behandeln Sie das Signaturgeheimnis wie jede andere Zugangsinformation und halten Sie es aus ausgeschriebenen Kommandozeilen heraus.

## Uptime Kuma {#uptime-kuma}

Ein **Push**-Monitor erwartet regelmäßige Meldungen und kann dadurch auch ausgebliebene Läufe erkennen.

**1. Monitor anlegen:** Wählen Sie *Add New Monitor → Push* und benennen Sie den Monitor nach der Instanz. Uptime Kuma liefert eine URL wie `https://kuma.example.com/api/push/<token>`. Setzen Sie das Heartbeat-Intervall etwas höher als das tatsächliche Scanintervall, damit ein langsamer Lauf nicht sofort als Ausfall gilt.

**2. Webhook konfigurieren:** Mit `--webhook-on always` werden auch erfolgreiche Durchläufe gemeldet:

```shell
check-opencloud-security --host opencloud.example.com \
  --webhook-url 'https://kuma.example.com/api/push/<token>' \
  --webhook-on always
```

Oder verwenden Sie eine Konfigurationsdatei:

```yaml
host: opencloud.example.com
webhook:
  url: secret://kuma_push_url
  on: always
```

**3. Regelmäßig ausführen:** Richten Sie einen [systemd-Timer](../scheduling.md#systemd-timer) oder [Cronjob](../scheduling.md#cron) ein. Bleibt die Meldung länger als das Heartbeat-Intervall aus, erkennt Uptime Kuma einen Ausfall.

Prüfen Sie, welche Status- und Detailfelder Ihr Push-Empfänger tatsächlich auswertet. Der generische JSON-Payload enthält:

| Feld | Inhalt |
|:--|:--|
| `status` / `exit_code` | Pluginstatus |
| `message` | Begründung |
| `rating`, `rating_label` | Zahlenwert und Note |
| `product_version`, `eol` | Version und Supportende |
| `update.availableVersion` | Empfohlenes Update |
| `duration_seconds` | Scandauer |

Ein Wrapper kann alternativ nur dann einen erfolgreichen Heartbeat senden, wenn das Plugin mit `0` endet:

```shell
check-opencloud-security --host opencloud.example.com \
  && curl -fsS 'https://kuma.example.com/api/push/<token>?status=up' \
  || curl -fsS 'https://kuma.example.com/api/push/<token>?status=down&msg=opencloud'
```

Diese Variante meldet vor allem Anwesenheit beziehungsweise Ausfall. Für differenzierte Statusmeldungen muss der Empfänger die Pluginwerte in sein eigenes Push-Protokoll übersetzen.

## Slack, Mattermost und Discord {#slack-mattermost-discord}

Für die üblichen Nachrichtenformate ist kein Adapter nötig:

```shell
check-opencloud-security --host opencloud.example.com \
  --webhook-url https://hooks.slack.com/services/... \
  --webhook-format slack
```

Mattermost akzeptiert das Slack-Format ebenso wie passende Webhook-Eingänge von [matrix-hookshot](https://matrix-org.github.io/matrix-hookshot/). Discord bietet einen kompatiblen Eingang unter `<webhook-url>/slack`.

Für zusätzliche Felder, eigene Farben oder abweichende Empfänger können Sie einen Adapter verwenden:

```python
#!/usr/bin/env python3
"""Forward a check-opencloud-security notification to a Slack-style webhook."""
import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

SLACK_URL = os.environ["SLACK_WEBHOOK_URL"]
COLOURS = {"OK": "#2eb886", "WARNING": "#daa038", "CRITICAL": "#a30200", "UNKNOWN": "#767676"}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        text = f"*{payload['host']}* - {payload['status']}\n{payload['message']}"
        if payload.get("rating_label"):
            text += f"\nRating {payload['rating_label']}, OpenCloud {payload.get('product_version', '?')}"

        body = json.dumps({
            "attachments": [{
                "color": COLOURS.get(payload["status"], "#767676"),
                "text": text,
            }]
        }).encode()
        request = urllib.request.Request(
            SLACK_URL, data=body, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(request, timeout=10):
            pass

        self.send_response(204)
        self.end_headers()


HTTPServer(("127.0.0.1", 8099), Handler).serve_forever()
```

Binden Sie ihn an Loopback und betreiben Sie ihn neben dem Check. Ein ungeschützter öffentlicher Adapter könnte von Dritten zum Versand von Chatnachrichten verwendet werden.

## ntfy und Gotify {#ntfy-and-gotify}

Beide Formate sind eingebaut:

```shell
check-opencloud-security --host opencloud.example.com \
  --webhook-url https://ntfy.example.com/opencloud \
  --webhook-format ntfy

check-opencloud-security --host opencloud.example.com \
  --webhook-url https://gotify.example.com/message \
  --webhook-header 'X-Gotify-Key: ...' \
  --webhook-format gotify
```

**ntfy:** Geben Sie die Topic-URL an. Das Plugin übernimmt das Topic in das JSON und sendet an die Wurzel desselben Servers, wie es das ntfy-JSON-Protokoll verlangt. Protokoll, Host und Port bleiben gleich. Eine URL ohne Topic wird beim Start abgelehnt. Siehe [ADR 0040](../../adr/0040-a-push-format-may-rewrite-the-path-never-the-host.md).

**Gotify:** Verwenden Sie möglichst `X-Gotify-Key` über einen Webhook-Header statt `?token=...` in der URL. So landet das Token nicht in üblichen URL-Logs vorgeschalteter Komponenten. `--webhook-secret` kann den Body unabhängig davon signieren.

Die Priorität folgt dem Status: CRITICAL wird bei ntfy `urgent` und bei Gotify `8`, WARNING `default` beziehungsweise `5`, UNKNOWN `high` beziehungsweise `5`. OK wird nur mit `always` gesendet und verwendet die niedrigste Priorität.

### Versand über einen Wrapper {#doing-it-in-a-wrapper-instead}

Ein Wrapper eignet sich für die vollständige Textausgabe oder eigene Prioritätsregeln:

```shell
#!/bin/sh
set -eu
output="$(check-opencloud-security --host opencloud.example.com --check-hardening)" || state=$?
state="${state:-0}"

case "$state" in
  0) exit 0 ;;                       # nothing to say
  1) priority=default ;;
  2) priority=urgent ;;
  *) priority=high ;;
esac

printf '%s' "$output" | curl -sS \
  -H "Title: OpenCloud security check" \
  -H "Priority: $priority" \
  -H "Tags: warning" \
  -d @- https://ntfy.example.com/opencloud
```

`|| state=$?` erfasst den Pluginstatus. Ohne diese Behandlung könnte `set -e` das Skript gerade bei einem meldepflichtigen Befund beenden.

## Alertmanager {#alertmanager}

Die v2-API erwartet eine Liste von Alerts:

```shell
check-opencloud-security --host opencloud.example.com --webhook-url \
  http://127.0.0.1:8098/  # an adapter that posts to /api/v2/alerts
```

```json
[{
  "labels": {
    "alertname": "OpenCloudSecurity",
    "instance": "opencloud.example.com",
    "severity": "critical"
  },
  "annotations": {"summary": "<message from the payload>"},
  "startsAt": "<timestamp from the payload>"
}]
```

Senden Sie nur Statuswerte, die alarmieren sollen, und stimmen Sie Ablaufzeit und Wiederholungsintervall auf den Scanplan ab. Wenn Sie bereits Metriken bereitstellen, ist die Anbindung über [Prometheus](../prometheus.md) meist einfacher.

## Empfänger ohne erreichbare Instanz testen {#testing-a-receiver-without-an-instance}

Ein nicht existierender Host zusammen mit `--webhook-on always` erzeugt eine echte Benachrichtigung im Fehlerformat:

```shell
check-opencloud-security --host does-not-exist.example.com \
  --webhook-url http://127.0.0.1:8099/ --webhook-on always
```

Für das vollständige Erfolgsformat verwenden Sie eine Instanz, die Sie prüfen dürfen. `--debug` protokolliert die Zustellung, aber nicht den Body. Um den Payload zu prüfen, verwenden Sie einen lokalen Testempfänger, der POST-Anfragen annimmt und deren Body anzeigt.

---

[Zur Dokumentationsübersicht](../README.md) | [Zum Haupt-README](../../README.md)

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
