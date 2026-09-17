# Release-Zeitplan und Schwachstellendaten aktualisieren

Der Scanner bewertet den Supportstatus anhand eines Release-Zeitplans und bekannte Schwachstellen anhand einer Datenbank. Beide Dateien werden mit dem Paket ausgeliefert. Wenn Paketupdates seltener erfolgen, können neuere Releases oder Sicherheitshinweise darin fehlen.

`check-opencloud-scanner refresh-data` aktualisiert diese Daten unabhängig vom Programm. Dieser Leitfaden beschreibt die Quellen, ihre Prüfung und die Einrichtung eines täglichen Laufs.

## Wann eine Aktualisierung sinnvoll ist {#when-you-need-it}

- **Die installierte OpenCloud-Version fehlt im Zeitplan.** Im Ergebnis steht dann `"scheduleStale": true`; siehe [Release-Lebenszyklus](../release-lifecycle.md).
- **Seit dem Paketbau wurden Sicherheitshinweise veröffentlicht.** Die gebündelte Datenbank kennt sie noch nicht.
- **Du aktualisierst das Scanner-Paket nach einem eigenen Zeitplan.** Die Referenzdaten sollen trotzdem aktuell bleiben.

Regelmäßige Paketupdates liefern ebenfalls neue Daten. Die [Webanwendung](../webapp.md) besitzt eigene Aktualisierungen zur Laufzeit und benötigt diesen Befehl nicht.

## Aktualisierung ausführen {#running-a-refresh}

```bash
check-opencloud-scanner refresh-data --output-dir /var/lib/check-opencloud-security
```

Bei Erfolg nennt der Befehl die beiden geschriebenen Dateien und liefert Exitcode `0`:

```text
/var/lib/check-opencloud-security/release_schedule.json
/var/lib/check-opencloud-security/vulnerabilities.json
```

| Option | Standard | Funktion |
|:--|:--|:--|
| `--output-dir` | `~/.cache/check-opencloud-security` | Zielverzeichnis; wird bei Bedarf angelegt |
| `--timeout` | `30` | Zeitlimit pro Anfrage in Sekunden |
| `--schedule-url` | keine | Alternative Lebenszyklusseite oder Spiegelquelle; ohne Signaturprüfung |
| `--advisory-url` | keine | Alternativer OSV-Endpunkt oder Spiegelquelle; ohne Signaturprüfung |

Bei Netzwerkfehlern, unzulässigen Dokumenten oder ungültigen Signaturen endet der Befehl mit `1` und einer Meldung auf stderr. Erst wenn beide Dokumente akzeptiert sind, werden Dateien ersetzt. Fehlerhafte Quelldaten überschreiben dadurch nicht den vorhandenen Stand.

Mit `-vv` siehst du die Signaturprüfung im Detail:

```bash
check-opencloud-scanner -vv refresh-data --output-dir /var/lib/check-opencloud-security
```

## Quellen und Datenprüfung {#where-the-data-comes-from-and-how-it-is-checked}

Standardmäßig lädt der Befehl `release_schedule.json` und `vulnerabilities.json` aus dem Branch `main` dieses Projekts. Er ruft dabei weder OSV noch die OpenCloud-Lebenszyklusseite direkt ab. Die Dateien gelangen über die Datenaktualisierungs-Workflows und deren Pull Requests in das Repository. Siehe [ADR 0027](../../adr/0027-refreshed-reference-data-is-attested-not-merely-fetched.md).

### Signaturprüfung {#signature-verification}

Der Workflow `attest-security-data.yml` attestiert Änderungen an beiden Dateien auf `main` mit [Sigstore](https://www.sigstore.dev/). Die Prüfung verlangt die Identität genau dieses Workflows, Branches und Repositorys. Eine Signatur aus einem beliebigen anderen Workflow genügt nicht.

Dafür wird das optionale Extra `signing` benötigt:

```bash
pipx install 'check-opencloud-security[signing]'
```

Bei einer bestehenden pipx-Installation ergänze `--force`. Weitere Installationswege stehen unter [Installation](../installation.md).

| Ergebnis | Verhalten |
|:--|:--|
| Signatur gültig | Dokument wird nach den weiteren Prüfungen verwendet |
| Signatur nicht prüfbar | Warnung; es gelten nur die Strukturprüfungen. Mögliche Ursachen sind ein fehlendes Extra, nicht erreichbare Prüfquellen oder eine noch fehlende Attestierung |
| Vorhandene Signatur ungültig | Abbruch mit `1`; es wird nichts geschrieben |

Ohne das Extra erscheint pro Datei eine Warnung, der Lauf kann dennoch erfolgreich sein:

```text
WARNING check_opencloud.refresh_data: Refreshing the release schedule without verifying its signature: the 'signing' extra (sigstore) is not installed. Install the 'signing' extra (pip install check-opencloud-security[signing]) to verify it.
```

In diesem Fall ist die Herkunft nicht kryptografisch geprüft. Installiere `signing`, wenn du die Attestierungen verifizieren möchtest.

### Immer geltende Prüfungen {#the-checks-that-apply-either-way}

Eine gültige Signatur ersetzt keine Inhaltsprüfung. Deshalb gelten unabhängig davon folgende Regeln:

- **Der Zeitplan muss alle gebündelten Versionslinien behalten.** Eine verkürzte Quelle darf bekannte Supportinformationen nicht entfernen.
- **Die Datenbank muss verwertbare Einträge enthalten.** Mindestens ein Sicherheitshinweis und Versionsgrenzen pro Hinweis sind erforderlich. Ein beidseitig unbeschränkter Bereich würde alle Releases erfassen.
- **Dateien werden einzeln atomar ersetzt.** Leser sehen keine teilweise geschriebene Datei.

## Die aktualisierten Dateien verwenden {#using-the-refreshed-files}

Der Befehl ändert keine Dateien im installierten Paket. Trage die neuen Pfade in die Konfiguration ein:

```yaml
scanner:
  release_schedule: /var/lib/check-opencloud-security/release_schedule.json
  vulnerability_db:
    - /var/lib/check-opencloud-security/vulnerabilities.json
```

Oder setze die Umgebungsvariablen:

```bash
COS_SCANNER_RELEASE_SCHEDULE=/var/lib/check-opencloud-security/release_schedule.json
COS_SCANNER_VULNERABILITY_DB=/var/lib/check-opencloud-security/vulnerabilities.json
```

Die Einstellungen unterscheiden sich:

- `release_schedule` **ersetzt** den gebündelten Zeitplan.
- `vulnerability_db` **ergänzt** die gebündelte Datenbank. Doppelte Kennungen werden zusammengeführt.

Plugin und `check-opencloud-scanner scan` lesen dieselben Einstellungen. Prüfe das Ergebnis über die JSON-Ausgabe:

```bash
check-opencloud-scanner -c /etc/check-opencloud-security/config.yml \
    scan opencloud.example.com | jq '.advisorySources, .lifecycle.scheduleUpdated'
```

`scheduleUpdated` sollte das Datum des aktualisierten Zeitplans zeigen; `advisorySources` sollte die zusätzliche Datei aufführen.

**Prüfe die Lesbarkeit nach jeder Änderung von Pfad oder Benutzer:**

- Eine fehlende oder unlesbare Zeitplandatei deaktiviert die End-of-Life-Prüfung. Es gibt keinen Rückfall auf die gebündelte Datei. Die Ausgabe meldet `Release lifecycle: unknown (no release schedule available)`, `scheduleUpdated` ist `null`. Eine eigentlich nicht mehr unterstützte Version kann dadurch allein anhand der übrigen Prüfungen bewertet werden.
- Eine fehlende oder unlesbare Advisory-Datei wird mit einer Warnung auf stderr übersprungen. SIE kann trotzdem in `advisorySources` stehen; kontrolliere daher auch die Warnmeldungen.

## Täglicher Lauf mit systemd {#running-it-daily-with-systemd}

Unter [`contrib/systemd/`](../../contrib/systemd) liegen der [Refresh-Service](../../contrib/systemd/check-opencloud-security-refresh.service) und der [Timer](../../contrib/systemd/check-opencloud-security-refresh.timer). `StateDirectory=` erlaubt dem Service das Schreiben unter `/var/lib/check-opencloud-security`. Der Timer läuft täglich mit einer zufälligen Verzögerung von bis zu einer Stunde und holt ausgefallene Läufe nach.

```bash
sudo cp contrib/systemd/check-opencloud-security-refresh.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now check-opencloud-security-refresh.timer
sudo systemctl start check-opencloud-security-refresh.service   # a first run now
journalctl -u check-opencloud-security-refresh.service
```

**Aktualisierung und Check brauchen passende Dateirechte.** Die erzeugten Dateien haben Modus `0600`. Der Service verwendet standardmäßig `User=check-opencloud-security`; ein Check als `nagios` oder `icinga` kann diese Dateien daher nicht lesen. Verwende denselben Benutzer oder passe den Aktualisierungsdienst über ein Drop-in an:

```bash
sudo systemctl edit check-opencloud-security-refresh.service
# [Service]
# User=nagios
```

`ExecStart=` erwartet `/usr/bin/check-opencloud-scanner`, den Installationspfad der `.deb`- und `.rpm`-Pakete. Bei pipx oder pip passt du ihn an. Alternativ verwende einen täglichen Cronjob; siehe [Zeitplanung](../scheduling.md).

## Spiegelquellen und Rechner ohne Internetzugang {#mirrors-and-hosts-without-internet-access}

Der Standardabruf benötigt HTTPS-Zugriff auf `raw.githubusercontent.com`, für die Verifikation außerdem auf die GitHub-Attestierungs-API und die Sigstore-Vertrauensdaten.

**Auf einem anderen Rechner aktualisieren:** Führe dort einen verifizierten Refresh mit `signing` aus und übertrage beide Dateien über einen vertrauenswürdigen Weg auf den isolierten Rechner. Die Dateien benötigen dort keine weiteren Quellen.

**Eine interne Spiegelquelle verwenden:** `--schedule-url` erwartet eine Kopie der OpenCloud-Lebenszyklusseite. `--advisory-url` erwartet einen OSV-kompatiblen Abfrageendpunkt; dessen Antwort ergänzt die gebündelte Datenbank:

```bash
check-opencloud-scanner refresh-data \
    --output-dir /var/lib/check-opencloud-security \
    --schedule-url https://mirror.example.com/opencloud/lifecycle/ \
    --advisory-url https://mirror.example.com/osv/v1/query
```

Bei diesen Optionen entfällt die Signaturprüfung mit einem ausdrücklichen Hinweis. Die Strukturprüfungen bleiben aktiv. Verwende nur Quellen, deren Bereitstellung du kontrollierst.

## Eigene Sicherheitshinweise {#your-own-advisories}

`scanner.vulnerability_db` akzeptiert eine Liste von Dateien. Du kannst eigene Hinweise neben den aktualisierten Daten einbinden. Unterstützt werden das native Format `{"advisories": [...]}`, das GitHub-Advisory-API-Format und OSV-Dokumente. Das [Haupt-README](../../README.md#advisory-database) erklärt die Zuordnung zu Versionen. `scanner.vulnerability_feed` fragt stattdessen bei jedem Scan einen Feed ab.

## Weitere Hinweise {#points-worth-knowing}

- Der Refresh ändert ausschließlich Daten. Neue Prüfungen und Bewertungsregeln benötigen weiterhin ein Paketupdate.
- Eine leere Liste `vulnerabilities` bedeutet nur, dass kein konfigurierter Datenbankeintrag zur Version passt. Sie ist kein Nachweis umfassender Sicherheit.
- Aktualisiere die Dateien, die der Check tatsächlich liest. Das Standardziel liegt im Home-Verzeichnis des ausführenden Benutzers.
- Die [Webanwendung](../webapp.md) nutzt eigene Aktualisierungen in ihrem laufenden Betrieb.

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
