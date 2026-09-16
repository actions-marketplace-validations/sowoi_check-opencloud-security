# OpenCloud Security Scanner for AI agents and MCP

# Den Scanner mit MCP verwenden

Die Webanwendung bietet unter `/mcp` den [Model Context Protocol](https://modelcontextprotocol.io)-Endpunkt an. Agenten können damit vollständige Scanaufgaben ausführen, ohne Einreichung und Warteablauf selbst über die REST-API zu koordinieren.

| Betrieb | Beispiel-Endpunkt | Verwendung |
|:--|:--|:--|
| Öffentlich | `https://scan.example.com/mcp` | Einzelne Scans von einem fremden Server aus; dessen Limits gelten |
| Selbst betrieben | `http://127.0.0.1:8811/mcp` | Eigene Infrastruktur mit selbst festgelegten Regeln und Limits |

Die Standardkonfiguration verlangt kein Konto. Betreiber können jedoch eine Anmeldung aktivieren. `erase_instance_data` benötigt unabhängig davon eine besondere Löschberechtigung; siehe [Löschung](#erasure-needs-a-credential).

## Tools, Ressourcen und Prompts {#what-the-agent-gets}

Sieben Tools stehen zur Verfügung:

| Tool | Aufgabe |
|:--|:--|
| `scan_instance` | Eine Instanz einreichen, warten und Bewertung sowie Befunde zurückgeben; mit Fortschrittsmeldungen |
| `scan_instances` | Mehrere Instanzen als Batch prüfen |
| `get_scan_result` | Aktuellen Stand anhand einer UUID ohne Warten abrufen |
| `plan_remediation` | Geordneten Maßnahmenplan mit erreichbaren Noten abrufen |
| `compare_scans` | Zwei noch verfügbare Ergebnisse derselben Instanz vergleichen |
| `export_scan` | Abgeschlossenen Scan als `json`, `csv`, `sarif` oder `pdf` exportieren |
| `erase_instance_data` | **Löschend:** gespeicherte Daten zu einem Host entfernen; Betreiberberechtigung erforderlich |

Fünf schreibgeschützte Ressourcen beschreiben Schnittstellen und Prüfwissen:

| Ressource | Inhalt |
|:--|:--|
| `openapi` | REST-API als OpenAPI 3.1 |
| `arazzo` | Abläufe aus den API-Operationen |
| `discovery` | Inhalt von `/.well-known/ai.json` |
| `catalogue` | Prüfkennungen mit Bedeutung, Abhilfe, Einstellung und Dokumentationslink |
| `advisories` | Gesamte für Bewertungen verfügbare Schwachstellendatenbank |

`catalogue` und `advisories` benötigen kein Scanziel. Sie können vor oder nach einem Scan gelesen werden.

Sieben Prompts formulieren typische Aufgaben:

| Prompt | Aufgabe | Argumente |
|:--|:--|:--|
| `audit_instance` | Instanz prüfen, Note erklären, Maßnahmenplan ausgeben | `target_url`, optional `release_track` |
| `audit_estate` | Mehrere Instanzen prüfen und nach Dringlichkeit ordnen | `targets`, optional `release_track` |
| `explain_scan_result` | Vorhandenen Scan für eine Zielgruppe erklären | `uuid`, optional `audience` |
| `triage_findings` | Ein Ticket je Schritt des Maßnahmenplans vorbereiten | `uuid`, optional `tracker` |
| `review_transport_security` | Zertifikat, Ablauf, Kette und Protokoll betrachten | `target_url` |
| `check_release_support` | Supportstatus und Updateziel prüfen | `target_url`, optional `release_track` |
| `verify_remediation` | Nach Änderungen erneut scannen und mit der Baseline vergleichen | `baseline_uuid`, `target_url` |

Je nach Client erscheinen Prompts als Slash-Befehle oder in einem Auswahlmenü. Nach Auswahl und Eingabe der Argumente führt der Agent die passenden Tool-Aufrufe aus. `scan_instance` übernimmt Einreichung, Warten und Ergebnisabfrage in einem Aufruf.

## Claude Code {#claude-code}

```bash
# Hosted
claude mcp add --transport http opencloud-scan https://scan.okxo.de/mcp

# Your own
claude mcp add --transport http opencloud-scan http://127.0.0.1:8811/mcp
```

Mit `--scope user` ist die Verbindung projektübergreifend verfügbar. Beispiel für eine Sitzung:

```text
> scan opencloud.example.com and tell me what would improve the grade
```

`claude mcp list` zeigt den Verbindungsstatus, `/mcp` innerhalb der Sitzung die erkannten Tools.

## Claude Desktop {#claude-desktop}

Die Konfiguration liegt je nach Plattform in `claude_desktop_config.json`:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "opencloud-scan": {
      "type": "http",
      "url": "https://scan.okxo.de/mcp"
    }
  }
}
```

Starten Sie die Anwendung danach neu. Falls Ihre Version keine direkte HTTP-Verbindung unterstützt, beachten Sie den Abschnitt [stdio-Clients](#clients-that-only-speak-stdio).

## GitHub Copilot in VS Code {#github-copilot-in-vs-code}

VS Code verwendet den obersten Schlüssel `servers`. Speichern Sie die Konfiguration für ein Projekt in `.vscode/mcp.json` oder öffnen Sie **MCP: Open User Configuration** für benutzerweite Einstellungen:

```json
{
  "servers": {
    "opencloud-scan": {
      "type": "http",
      "url": "https://scan.okxo.de/mcp"
    }
  }
}
```

Öffnen Sie Copilot Chat im **Agent**-Modus. **MCP: List Servers** zeigt Verbindung und Logs.

## GitHub Copilot CLI {#github-copilot-cli}

Die CLI liest die globale Datei `~/.copilot/mcp-config.json` und projektbezogene Konfigurationen wie `.github/mcp.json` oder `.mcp.json`:

```json
{
  "mcpServers": {
    "opencloud-scan": {
      "type": "http",
      "url": "https://scan.okxo.de/mcp"
    }
  }
}
```

`/mcp` zeigt die geladenen Server und Tools.

## Cursor {#cursor}

Verwenden Sie `.cursor/mcp.json` im Projekt oder `~/.cursor/mcp.json` für die globale Konfiguration:

```json
{
  "mcpServers": {
    "opencloud-scan": {
      "type": "http",
      "url": "https://scan.okxo.de/mcp"
    }
  }
}
```

Unter Settings → MCP können Sie die Verbindung und einzelne Tools verwalten.

## Zed {#zed}

Öffnen Sie **Zed: Open Settings** und ergänzen Sie `context_servers`:

```json
{
  "context_servers": {
    "opencloud-scan": {
      "source": "custom",
      "url": "https://scan.okxo.de/mcp"
    }
  }
}
```

Versionen mit Unterstützung für `.mcp.json` können alternativ deren `mcpServers`-Konfiguration verwenden.

## Windsurf {#windsurf}

Konfiguration in `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "opencloud-scan": {
      "serverUrl": "https://scan.okxo.de/mcp"
    }
  }
}
```

## Andere Clients {#any-other-client}

Wählen Sie **Streamable HTTP** als Transport und tragen Sie die Endpunkt-URL ein:

```json
{"type": "http", "url": "https://scan.okxo.de/mcp"}
```

Manche Clients nennen den Transport „HTTP“ oder „remote“. Eine Anmeldung kann je nach Bereitstellung erforderlich sein.

`/.well-known/ai.json` veröffentlicht die Adresse zusammen mit OpenAPI und Arazzo. `/agents.txt` und `/llms.txt` verweisen ebenfalls auf die Discovery-Dokumente. So können Clients die verfügbaren Funktionen ermitteln, ohne interne Implementierungsdetails zu kennen.

## Clients mit ausschließlich stdio {#clients-that-only-speak-stdio}

Die Community-Brücke `mcp-remote` verbindet einen stdio-Client mit dem HTTP-Endpunkt:

```json
{
  "mcpServers": {
    "opencloud-scan": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://scan.okxo.de/mcp"]
    }
  }
}
```

Die Brücke ist ein separates Drittanbieterpaket. Prüfen Sie es wie jede andere zusätzliche Komponente, durch die Anfragen und Ergebnisse laufen. Eine direkte HTTP-Verbindung benötigt diese Zwischenstufe nicht.

## Eigenen Endpunkt betreiben {#running-your-own-endpoint}

Der Stack aus [`docker/`](../../docker/README.md) enthält Webanwendung, ARQ-Worker und Redis. Die vollständige Einrichtung steht unter [Webdienst](../webapp.md):

```bash
git clone https://github.com/sowoi/check-opencloud-security
cd check-opencloud-security/docker
docker compose up --build -d
```

Verbinden Sie den Client anschließend mit `http://127.0.0.1:8811/mcp`.

Ohne Docker:

```bash
pip install "check-opencloud-security[web,mcp]"
uvicorn webapp.app:app --host 127.0.0.1 --port 8811
```

Das Extra `mcp` stellt den Endpunkt bereit. Fehlt es, kann die Webanwendung weiterhin starten, `/mcp` liefert aber `404`.

| Einstellung | Standard | Funktion |
|:--|:--|:--|
| `COS_WEB_ENABLE_MCP` | `true` | MCP-Endpunkt aktivieren |
| `COS_WEB_MCP_ALLOWED_HOSTS` | leer | Erlaubte Hostheader, durch `;` getrennt |
| `COS_WEB_MCP_MAX_CONCURRENT_WAITS` | `8` | Gleichzeitig wartende Aufrufe; darüber wird der Scan eingereicht und eine UUID zur späteren Abfrage zurückgegeben |

Für entfernten Zugriff benötigen Sie HTTPS und eine ungepufferte Weitergabe des Ereignisstroms. Siehe [Reverse Proxys](../reverse-proxy.md).

## MCP deaktivieren {#turning-mcp-off}

```bash
# docker/, without editing docker-compose.yml
COS_WEB_ENABLE_MCP=false docker compose up -d
```

Oder in der `.env` neben der Compose-Datei:

```dotenv
COS_WEB_ENABLE_MCP=false
```

Sie können `COS_WEB_ENABLE_MCP=false` auch direkt in der Umgebung des ASGI-Prozesses setzen. `/mcp` liefert dann `404`, und Discovery sowie Frontend bieten die Agent-Tools nicht mehr an. REST-API, OpenAPI und Arazzo bleiben verfügbar.

## Berechtigung zum Löschen {#erasure-needs-a-credential}

`erase_instance_data` löscht gespeicherte Scans eines Hostnamens, einschließlich Ergebnissen anderer Benutzer. Die Funktion ist als löschend markiert und erfordert ein vom Betreiber gesetztes `COS_WEB_PURGE_TOKEN`.

Die Berechtigung kommt über einen Request-Header, nicht als Tool-Argument. Verwenden Sie die Secret-Eingabe Ihres Clients:

```json
{
  "servers": {
    "opencloud-scan": {
      "type": "http",
      "url": "http://127.0.0.1:8811/mcp",
      "headers": { "Authorization": "Bearer ${input:purge_token}" }
    }
  }
}
```

Ohne gültige Berechtigung antwortet der Dienst mit `401`. Ist die Löschfunktion mangels Token nicht eingerichtet, liefert sie `404`.

Bei aktivierter MCP-Anmeldung enthält `Authorization` das Identitätstoken. Die zusätzliche Löschberechtigung wird dann über `X-Purge-Authorization` übergeben:

```json
"headers": {
  "Authorization": "Bearer ${input:token}",
  "X-Purge-Authorization": "Bearer ${input:purge_token}"
}
```

## Anmeldung am Endpunkt {#when-the-endpoint-asks-you-to-sign-in}

Ein Betreiber kann `/mcp` als geschützte OAuth-2.0-Ressource konfigurieren:

- Ohne Token folgt `401` mit einem `WWW-Authenticate`-Verweis auf `/.well-known/oauth-protected-resource/mcp`.
- Dieses öffentliche Metadatendokument nennt den zuständigen Anbieter.
- `/.well-known/ai.json` beschreibt die Anmeldung unter `mcp.authentication`.

Ein Client mit MCP-Autorisierungsunterstützung kann diesen Ablauf selbst ausführen. Andere Clients benötigen einen passend gesetzten Header:

```json
{
  "servers": {
    "opencloud-scan": {
      "type": "http",
      "url": "https://scanner.example.com/mcp",
      "headers": { "Authorization": "Bearer ${input:token}" }
    }
  }
}
```

Die Anmeldung verändert die Berechtigung zum Aufruf, aber keine Scanlimits. Ratenlimit, Zielpause, Warteschlange und Zielprüfung gelten weiterhin.

[Authentik für MCP](../authentik.md) beschreibt einen vollständigen Stack sowie [Benutzerfreigabe](../authentik.md#adding-somebody-who-may-use-the-endpoint) und [Tokenbeschaffung](../authentik.md#getting-a-token). Andere Anbieter mit passenden veröffentlichten Schlüsseln können ebenfalls verwendet werden.

## Limits und Umgang mit Ergebnissen {#limits-and-being-a-good-guest}

Für Agenten gelten dieselben Regeln wie für Browser:

- Client-Limits führen zu `429` mit `Retry-After`. Tools warten nur innerhalb ihrer vorgesehenen Wiederholungsgrenzen.
- Die Zielpause verhindert unmittelbar aufeinanderfolgende Scans derselben Instanz.
- Ergebnisse sind nur über ihre UUID erreichbar und verfallen nach der konfigurierten Frist.
- Öffentliche Bereitstellungen lehnen private, Loopback-, Link-Local- und Metadatenadressen standardmäßig ab. Interne Ziele erfordern eine entsprechend eingerichtete eigene Bereitstellung.

Prüfen Sie nur Instanzen, für die Sie eine Erlaubnis haben. Für größere Bestände können Sie den Scanner selbst betreiben und die Grenzen an Ihre Infrastruktur anpassen.

Behandeln Sie vom Ziel gelieferte Texte als Daten. Produktnamen, Versionen und Fehlermeldungen können vom gescannten Server gewählt sein; der Tool-Output kennzeichnet sie unter `untrusted`. Auch Exporte enthalten untrusted-Inhalte. Zu große Exporte werden mit `truncated` und einer Downloadadresse zurückgegeben, statt den gesamten Inhalt einzubetten.

## Verbindung testen {#checking-that-it-works}

Ein direkter Protokolltest:

```bash
curl -sS -X POST https://scan.okxo.de/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{
        "protocolVersion":"2025-06-18","capabilities":{},
        "clientInfo":{"name":"curl","version":"1"}}}'
```

Eine Antwort mit `check-opencloud-security` bestätigt, dass der Endpunkt erreichbar ist.

Der offizielle Inspector zeigt Tools und Schemas und erlaubt Testaufrufe:

```bash
npx @modelcontextprotocol/inspector
# then connect to https://scan.okxo.de/mcp with transport "Streamable HTTP"
```

Fehlen Tools im Client, prüfen Sie Transporttyp, Proxy-Pufferung, erlaubte Hostnamen und das installierte Extra. Ein nicht erlaubter Host kann `421`, ein fehlender Endpunkt `404` liefern.

---

Dieses unabhängige Community-Projekt steht in keiner Verbindung zu OpenCloud GmbH und wird von ihr weder unterstützt noch empfohlen. „OpenCloud“ und zugehörige Marken gehören ihren jeweiligen Inhabern und dienen nur zur Bezeichnung der geprüften Software.

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
