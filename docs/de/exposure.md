# Exposed path and debug endpoint checks explained

# Öffentlich zugängliche Dateien und Debug-Schnittstellen

OpenCloud liefert normalerweise weder Verzeichnislisten noch Konfigurationsdateien, private Schlüssel oder seine Identitätsdatenbank über HTTP aus. Diese Prüfungen suchen nach einem vorgeschalteten Webserver, der solche Dateien freigibt, und nach Debug-Schnittstellen, die privat bleiben sollten.

Vor den Pfadprüfungen ruft der Scanner einen nicht existierenden Kontrollpfad ab. Die Single-Page-Anwendung von OpenCloud kann auch dort mit `200` ihre normale HTML-Oberfläche liefern. Erst eine davon abweichende Antwort gilt deshalb als Hinweis auf einen tatsächlich vorhandenen Pfad.

## 1. Verzeichnisindex: `directoryListing` {#1-is-a-directory-index-being-served-directorylisting}

Eine Seite nach dem Muster `Index of /` deutet auf einen direkt veröffentlichten Dateibaum hin. OpenCloud erzeugt solche Verzeichnislisten nicht selbst.

**Behebung:** Lassen Sie den Webserver Anfragen an OpenCloud weiterleiten, statt das Installationsverzeichnis auszuliefern. Deaktivieren Sie Verzeichnisindizes zusätzlich, etwa mit `autoindex off` in nginx oder `Options -Indexes` in Apache. Siehe [Reverse Proxys](../reverse-proxy.md).

## 2. Lesbare Installationsdateien: `exposed:<path>` {#2-is-a-specific-deployment-file-readable-exposedpath}

Der Scanner prüft eine feste Liste:

| Pfad | Schweregrad |
|:--|:--|
| `/opencloud.yaml` | critical |
| `/config/opencloud.yaml` | critical |
| `/.opencloud/config/opencloud.yaml` | critical |
| `/proxy/server.key` | critical |
| `/idm/opencloud.boltdb` | critical |
| `/.env` | critical |
| `/docker-compose.yml` | high |
| `/storage/users/` | high |
| `/.git/config` | high |

Die Dateien können Einstellungen, Zugangsdaten, TLS-Schlüssel und Identitätsdaten enthalten. Ein Treffer deutet auf ein öffentlich erreichbares Installationsverzeichnis oder einen Git-Checkout hin.

**Behebung:** Beenden Sie die Dateiauslieferung und prüfen Sie anschließend, dass die genannten Pfade `404` liefern. Behandeln Sie tatsächlich lesbare Geheimnisse als offengelegt: Tauschen Sie betroffene Schlüssel und Zugangsdaten aus und untersuchen Sie einen möglichen unbefugten Zugriff.

## 3. Öffentliche Debug-Pfade: `debugEndpoint:<path>` {#3-is-a-debug-endpoint-publicly-readable-debugendpointpath}

`/metrics`, `/config` und `/debug/pprof/` werden an der öffentlichen Adresse geprüft. Sie können Betriebsdaten, Konfiguration oder Profiling-Funktionen zugänglich machen und gehören auf interne Debug-Schnittstellen.

**Behebung:** Veröffentlichen Sie diese Pfade nicht über den öffentlichen Reverse Proxy. Lassen Sie Debug-Listener standardmäßig auf `127.0.0.1` lauschen, gesteuert durch `OC_DEBUG_ADDR` und die dienstspezifischen `*_DEBUG_ADDR`-Variablen. Benötigte Metrikzugriffe sollten über das interne Netz erfolgen.

## 4. Erreichbare Debug-Ports: `debugPort:<port>` {#4-is-a-service-debug-port-reachable-debugportport}

Der Scanner verbindet sich mit den Standard-Debug-Ports oder der Liste in `scanner.debug_ports`. Diese Listener sind normalerweise an `127.0.0.1` gebunden. Externe Erreichbarkeit entsteht häufig durch Container-Portfreigaben.

**Behebung:** Entfernen Sie die öffentliche Portzuordnung und beschränken Sie den Zugriff auf Loopback oder das erforderliche interne Netz.

## 5. Direkter Backend-Zugriff: `backendPortClosed` {#5-is-the-backend-reachable-directly-bypassing-the-proxy-backendportclosed}

Ein öffentlich erreichbarer Port `9200` kann den vorgeschalteten Reverse Proxy umgehen. Dessen zusätzliche TLS-Regeln, Header oder Zugriffskontrollen greifen dann für diese Verbindung nicht.

**Behebung:** Entfernen Sie die öffentliche Portfreigabe und binden Sie das Backend an Loopback oder ein privates Container-Netz, das nur der Reverse Proxy erreichen muss.

## 6. CORS-Ursprünge: `corsOriginRestricted` {#6-who-may-read-a-response-cross-origin-corsoriginrestricted}

CORS legt fest, welche fremden Ursprünge Antworten im Browser lesen dürfen. Der Scanner prüft, ob die API einen beliebigen Ursprung erlaubt, insbesondere zusammen mit Zugangsdaten.

Die dokumentierten Standardwerte sind `OC_CORS_ALLOW_ORIGINS=*` und `OC_CORS_ALLOW_CREDENTIALS=true`; siehe [Graph-Umgebungsvariablen](https://docs.opencloud.eu/docs/dev/server/services/graph/environment-variables). Entscheidend ist die tatsächlich gesendete Antwort, da Middleware den angefragten Ursprung auch zurückspiegeln kann.

Die Anfrage an `/graph/v1.0/me` enthält den Testursprung `https://cors-probe.check-opencloud-security.invalid`. Der reservierte Name wird nicht aufgelöst oder kontaktiert.

| Antwort | Bewertung |
|:--|:--|
| Testursprung gespiegelt und `Access-Control-Allow-Credentials: true` | critical: beliebiger Ursprung mit erlaubten Zugangsdaten |
| `Access-Control-Allow-Origin: null` mit Zugangsdaten | critical: auch Sandbox-Frames können den Ursprung `null` verwenden |
| Testursprung ohne erlaubte Zugangsdaten gespiegelt | medium: breite Lesefreigabe |
| Wörtliches `*`, mit oder ohne Zugangsdaten | medium: Browser erlauben die Kombination mit Zugangsdaten nicht |
| Ein anderer, ausdrücklich benannter Ursprung | bestanden |
| Kein `Access-Control-Allow-Origin` | bestanden |

**Behebung:** Beschränken Sie `OC_CORS_ALLOW_ORIGINS` auf die tatsächlich benötigten Ursprünge. Setzen Sie `OC_CORS_ALLOW_CREDENTIALS=false`, wenn keiner dieser Abläufe Zugangsdaten benötigt. Dienstspezifische Variablen wie `GRAPH_CORS_ALLOW_ORIGINS` und `OCS_CORS_ALLOW_ORIGINS` überschreiben die gemeinsame Vorgabe.

## 7. TRACE-Antworten: `traceMethodDisabled` {#7-is-the-request-echoed-back-tracemethoddisabled}

`TRACE` fordert eine Rückgabe der empfangenen Anfrage an. Die Antwort kann dabei Header enthalten, die entlang des Verbindungswegs ergänzt wurden. Der Scanner prüft diese unnötige Diagnosefunktion; er sendet dafür keine Zugangsdaten.

OpenCloud implementiert `TRACE` nicht selbst. Eine Echo-Antwort stammt daher aus einer vorgeschalteten Komponente. `200` allein genügt nicht als Nachweis: Die Antwort muss wie die gesendete Anfrage aussehen, etwa über `Content-Type: message/http` oder die zurückgegebene Request-Zeile.

`TRACE` ist nach RFC 9110 eine sichere Methode und soll den Zielzustand nicht verändern.

**Behebung:** Deaktivieren Sie `TRACE` am Proxy. Apache bietet `TraceEnable off`; nginx lehnt die Methode normalerweise mit `405` ab. Bei weiterleitenden Regeln in nginx, Traefik oder Caddy beschränken Sie die erlaubten Methoden entsprechend.

## 8. Administrationsoberfläche eines Dokumenteditors: `companionAdminConsole` {#8-is-a-second-services-console-published-beside-the-instance-companionadminconsole}

Ein WOPI-Editor wie Collabora Online oder OnlyOffice kann über denselben Ursprung wie OpenCloud veröffentlicht werden. Seine Administrationsoberfläche kann Sitzungen und Betriebsinformationen anzeigen und gehört nicht an den öffentlichen Zugang.

Der Scanner sucht unter `/hosting/discovery` nach einem Dokument mit Wurzelelement `wopi-discovery`. Erst nach diesem Nachweis prüft er den Konsolenpfad. `companionEditorHttps` untersucht zusätzlich die im Dokument veröffentlichten Editor-Adressen auf `http://`.

Ist unter diesem Ursprung kein Backend nachweisbar, erscheinen beide Befunde nicht. Der Scanner folgt keinem aus dem Dokument übernommenen Hostnamen, da sonst die gescannte Instanz das nächste Verbindungsziel bestimmen könnte. Einen separat betriebenen Editor müssen Sie mit dafür geeigneten Prüfungen untersuchen. Siehe [ADR 0036](../../adr/0036-a-companion-service-is-probed-only-where-the-scan-was-pointed.md).

**Behebung:** Sperren Sie den Administrationspfad am Reverse Proxy und veröffentlichen Sie nur die für den Editor benötigten Pfade. Verwenden Sie HTTPS für die Editor-Adressen.

## Schweregrad und Bewertung {#severity-and-rating-impact}

Diese Befunde gehören zu `extraChecks` und benötigen kein `--check-hardening`. Sie werden bewertet, wenn die jeweilige Prüfung ausgeführt werden kann. Kritische Befunde begrenzen die Note auf `D`, hohe auf `C`; die vollständige Zuordnung steht in der [Prüfübersicht](../scanner-checks.md#what-the-scanner-checks).

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
