# Den Scanner mit Docker ausführen

Mit dem veröffentlichten Container-Image führe denselben Scanner wie die [Webanwendung](../webapp.md) auf deinem eigenen Rechner aus. Du benötigst Docker, aber kein Konto bei diesem Dienst. Die Begrenzungen der öffentlichen Website gelten für den lokalen Scan nicht.

```shell
docker run --rm --entrypoint check-opencloud-security \
  okxo/opencloud-scanner:latest --host opencloud.example.com
```

Der Befehl gibt die Statuszeile aus, die auch ein Monitoring-System erhält:

```text
OK: Server is up to date. No known vulnerabilities.
OpenCloud 7.2.3 on opencloud.example.com, rating: A+, last scanned: 2026-08-25 09:41:12
Release lifecycle: 7.2 (production, track detected), current release
```

Der Exitcode ist `0` für OK, `1` für WARNING, `2` für CRITICAL oder `3` für UNKNOWN. Damit lässt sich der Aufruf auch in Skripten, Pipelines und Cronjobs verwenden.

> **Marken und Unabhängigkeit.** Dieses Projekt ist unabhängig und wird von OpenCloud GmbH weder unterstützt noch empfohlen. Es besteht keine Verbindung zu OpenCloud GmbH. „OpenCloud“ und zugehörige Marken gehören ihren jeweiligen Inhabern und dienen hier ausschließlich zur Bezeichnung der geprüften Software.

## Inhalt des Images {#what-the-image-is}

[`okxo/opencloud-scanner`](https://hub.docker.com/r/okxo/opencloud-scanner) wird aus diesem Repository gebaut und enthält beide Programme:

| Einstiegspunkt | Funktion |
|:--|:--|
| `check-opencloud-security` | Nagios-/Icinga-Plugin mit Statuszeile, Performancedaten und Exitcode |
| `check-opencloud-scanner` | Vollständiges JSON-Ergebnis oder Betrieb als HTTP-Dienst |

Standardmäßig startet das Image die Webanwendung. Deshalb setzen alle folgenden Aufrufe `--entrypoint`. Verwende für wiederholbare Abläufe einen festen Tag, beispielsweise `okxo/opencloud-scanner:1.9`, statt `latest`.

## Ergebnisse als JSON {#the-same-scan-as-json}

Das JSON-Dokument enthält Bewertung, Release-Lebenszyklus, Sicherheitshinweise und Prüfergebnisse, aus denen die Weboberfläche ihren Bericht erstellt:

```shell
docker run --rm --entrypoint check-opencloud-scanner \
  okxo/opencloud-scanner:latest scan opencloud.example.com
```

Mit `jq` wähle einzelne Felder aus:

```shell
docker run --rm --entrypoint check-opencloud-scanner \
  okxo/opencloud-scanner:latest scan opencloud.example.com \
  | jq '{rating, version, addresses, failed: [.extraChecks[] | select(.passed | not) | .id]}'
```

`addresses` enthält die während des Scans ermittelten IPv4- und IPv6-Adressen. Diese erscheinen im Webbericht unter „Aufgelöst zu“. Prüfe bei unerwarteten Befunden: Möglicherweise zeigt der DNS-Eintrag noch auf einen anderen Server.

## Häufige Varianten {#useful-variations}

Zu jedem Befund eine Erklärung ausgeben:

```shell
docker run --rm --entrypoint check-opencloud-security \
  okxo/opencloud-scanner:latest --host opencloud.example.com --debug
```

Einen bewusst akzeptierten Befund ausnehmen:

```shell
docker run --rm --entrypoint check-opencloud-security \
  okxo/opencloud-scanner:latest --host opencloud.example.com \
  --ignore-hardening basicAuthDisabled
```

Einen Release-Kanal ausdrücklich vorgeben:

```shell
docker run --rm --entrypoint check-opencloud-security \
  okxo/opencloud-scanner:latest --host opencloud.example.com \
  --release-track lts
```

Eine Instanz im eigenen Netzwerk prüfen:

```shell
docker run --rm --network host --entrypoint check-opencloud-security \
  okxo/opencloud-scanner:latest --host opencloud.internal.example.com
```

Dafür muss der Container die private Adresse erreichen und den Hostnamen auflösen können. Die Zielbeschränkung des öffentlichen Webdienstes gilt für diesen lokalen Aufruf nicht.

Für Container und Vorlagen kannst du Einstellungen auch über `COS_`-Umgebungsvariablen setzen. Die vollständige Zuordnung steht im [Haupt-README](../../README.md#environment-variables):

```shell
docker run --rm -e COS_HOST=opencloud.example.com \
  --entrypoint check-opencloud-security okxo/opencloud-scanner:latest
```

Wenn die Release-Quelle nicht kontaktiert werden soll oder kein Internetzugang besteht, deaktiviere die Update-Prüfung:

```shell
docker run --rm --entrypoint check-opencloud-security \
  okxo/opencloud-scanner:latest --host opencloud.example.com --no-update-check
```

## Einen kurzen Aufruf einrichten {#make-it-shorter}

Eine Shell-Funktion verkürzt wiederholte Aufrufe:

```shell
# ~/.bashrc or ~/.zshrc
opencloud-scan() {
  docker run --rm --entrypoint check-opencloud-security \
    okxo/opencloud-scanner:latest --host "$1" "${@:2}"
}
```

```shell
opencloud-scan opencloud.example.com --debug
```

## Ohne Docker {#without-docker}

Das Python-Paket ist auf PyPI verfügbar und lässt sich mit [`uv`](https://docs.astral.sh/uv/) oder `pipx` auch ohne Container ausführen:

```shell
uvx --from check-opencloud-security check-opencloud-security \
  --host opencloud.example.com
```

```shell
pipx run --spec check-opencloud-security check-opencloud-security \
  --host opencloud.example.com
```

## Weiterführende Anleitungen {#where-to-go-next}

- [Haupt-README](../../README.md): Optionen und Prüfungen.
- [Zeitplanung](../scheduling.md): systemd-Timer und Cronjobs.
- [CI-Pipelines](../ci.md): Ergebnisse in einer Pipeline auswerten.
- [Mehrere Instanzen](../many-instances.md): Konfiguration je Instanz und Änderungsvergleiche.
- [Webanwendung](../webapp.md): Browseroberfläche selbst betreiben.

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
