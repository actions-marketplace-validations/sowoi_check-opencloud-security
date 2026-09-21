# Fehlersuche

**`UNKNOWN: ... /status.php is unreachable`**

Der Monitoring-Host muss die Instanz direkt erreichen können, da das Plugin den Scan selbst ausführt. Prüfe Adresse und Port. OpenClouds eigener Proxy lauscht auf **9200**; verwende dafür `--host opencloud.example.com:9200` oder `--port 9200`.

**`UNKNOWN: No OpenCloud instance found at ...`**

`/status.php` liefert kein OpenCloud-Statusdokument. Prüfe, ob an der Adresse OpenCloud läuft und der Reverse Proxy diesen Pfad weiterleitet. `--debug` zeigt die Antwort.

**`UNKNOWN: ... Is not an OpenCloud instance: /status.php reports ownCloud`**

Der Endpunkt antwortet, meldet aber ein anderes Produkt. Da dessen Releases, Schwachstellen und Standardeinstellungen von OpenCloud abweichen, beendet der Scanner die Prüfung. Weitere Hintergründe stehen unter [Was ist OpenCloud?](../what-is-opencloud.md#why-this-matters-for-a-security-scan).

**Zertifikatsfehler bei einer neuen Instanz**

`opencloud init` erzeugt ein selbstsigniertes Zertifikat. Mit `--insecure` kannst du die Prüfung fortsetzen: Die nicht vertrauenswürdige Kette bleibt sichtbar, beeinflusst die Note aber nicht. Alternativ stelle einen Reverse Proxy mit einem vertrauenswürdigen Zertifikat davor.

**Die Versionsnummer wirkt falsch (`0.1.0`)**

Dies ist die feste Kompatibilitätsangabe, nicht die tatsächliche Release-Version. Siehe [Die Version richtig lesen](../scanner-checks.md#reading-the-version-correctly). Wenn keine bessere Angabe verfügbar ist, meldet das Plugin `legacyVersion`. Aktualisiere die Instanz oder ermögliche den Zugriff auf `/ocs/v1.php/cloud/capabilities`.

**Alle Pfade werden als öffentlich zugänglich gemeldet**

Prüfe die Fallback-Regel des Reverse Proxys. Möglicherweise liefert er auch für nicht existierende Pfade `200`, einschließlich des Kontrollpfads des Scanners.

**Sicherheitsheader fehlen, obwohl OpenCloud sie sendet**

Ein vorgeschalteter Proxy kann Header entfernen oder die Anfrage selbst beantworten. [Reverse Proxys](../reverse-proxy.md) enthält die benötigten Einstellungen für nginx, Apache, Caddy, Traefik und HAProxy.

**Der Scan dauert lange**

Die Prüfung eines von der Firewall blockierten Debug-Ports kann jeweils `debug_port_timeout` Sekunden dauern. Verwende `--no-debug-ports`, reduziere `COS_SCANNER_DEBUG_PORT_TIMEOUT` oder die Portliste, oder führe Anfragen mit `--concurrency` parallel aus. Siehe [Scans beschleunigen](../scanner-checks.md#speeding-the-scan-up).

**`UNKNOWN` bei der Update-Prüfung oder GitHub-Ratenlimit**

Ohne Token steht pro IP-Adresse nur ein gemeinsames Kontingent für API-Anfragen zur Verfügung. Hinterlege `--release-token` oder verwende `--update-source bundled` beziehungsweise `pinned`, um die Abfrage ohne Netzwerkzugriff durchzuführen.

**Docker: `permission denied while trying to connect to the Docker socket`**

Der Benutzer von Icinga2, cron oder systemd braucht Zugriff auf den Docker-Daemon. Richte diesen entsprechend deiner Sicherheitsvorgaben ein, etwa über die Gruppe `docker` oder einen gezielt erlaubten `sudo`-Aufruf.

**Keine Ausgabe von cron oder systemd**

- Verwende den vollständigen Programmpfad und setze `COS_HOST` ausdrücklich. Beide übernehmen die Umgebung einer Login-Shell nicht automatisch; siehe [Zeitplanung](../scheduling.md).
- Lies bei systemd das Log mit `journalctl -u check-opencloud-security.service`, bei cron die konfigurierte Logdatei.

**`--warn-on-new` meldet trotz eines Problems OK**

Mit Baseline beeinflussen nur neue oder verschlechterte Befunde den Status. Der vollständige Zustand steht weiterhin in der Ausgabe; `Suppressed by --warn-on-new:` nennt den regulären Status. Entferne die Option, wenn jeder Durchlauf diesen Status zurückgeben soll, oder lösche die Baseline-Datei für einen Neustart des Vergleichs. Das Supportende wird nie unterdrückt. Siehe [Nur Änderungen melden](../../README.md#reporting-only-what-changed).

**`--warn-on-new needs --baseline PATH`**

Gib eine Baseline-Datei an, die der Monitoring-Benutzer schreiben darf, etwa `/var/lib/check_opencloud/baseline.json`.

**`Baseline could not be written`**

Prüfe, ob das Verzeichnis existiert oder angelegt werden darf und der Monitoring-Benutzer Schreibrechte besitzt. Die Bewertung der Instanz bleibt unverändert. Solange keine Baseline gespeichert wird, behandelt `--warn-on-new` jeden Durchlauf als ersten Scan.

**Kein Hinweis von `--self-update-check`**

Das Ergebnis wird einen Tag zwischengespeichert. Für eine erneute Abfrage lösche `${XDG_CACHE_HOME:-~/.cache}/check-opencloud-security/pypi-version.json`. Es erscheint auch dann kein Hinweis, wenn PyPI nicht erreichbar ist, ein Proxy die Abfrage blockiert oder die installierte Version neuer als das veröffentlichte Release ist. Die Update-Prüfung verändert den Exitcode nicht.

**Exitcodes**

| Exitcode | Bedeutung |
|:--|:--|
| `0` | OK |
| `1` | WARNING |
| `2` | CRITICAL |
| `3` | UNKNOWN |

**Weitere Hilfe**

Erstelle ein Issue mit der `--debug`-Ausgabe. Bei einem unzutreffenden Befund verwende die Vorlage [Wrong finding](https://github.com/sowoi/check-opencloud-security/issues/new?template=wrong_finding.yml). Tokens werden in der Diagnoseausgabe maskiert; prüfe die Ausgabe dennoch vor dem Veröffentlichen und entferne produktive Hostnamen und Zugangsdaten. Siehe [Verhaltenskodex](../../CODE_OF_CONDUCT.md).

---

[Zur Dokumentationsübersicht](../README.md) | [Zum Haupt-README](../../README.md)

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
