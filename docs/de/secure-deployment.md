# OpenCloud sicher betreiben

Der Scanner prüft den von außen sichtbaren Zustand einer OpenCloud-Instanz. Für einen sicheren Betrieb musst du zusätzlich Anmeldung, Protokollierung, Netzregeln, Datensicherung und den Umgang mit Freigaben gestalten. Dieser Leitfaden verbindet diese Aufgaben mit regelmäßigen Scans.

Die verlinkte OpenCloud-Dokumentation beschreibt die Einstellungen der jeweiligen Version. Prüfe vor einer Änderung und melde Abweichungen gern als [Issue](https://github.com/sowoi/check-opencloud-security/issues).

## Aufbau der Bereitstellung {#the-shape-of-a-defensible-deployment}

```
                    internet
                        │
                   443/tcp only
                        │
              ┌─────────▼─────────┐
              │   reverse proxy   │  TLS, HSTS, security headers,
              │  (nginx/Caddy/…)  │  rate limits, TRACE refused
              └─────────┬─────────┘
                        │  private network, no published ports
         ┌──────────────┼──────────────┐
         │              │              │
  ┌──────▼─────┐ ┌──────▼─────┐ ┌──────▼──────┐
  │ OpenCloud  │ │  identity  │ │    audit    │
  │   :9200    │ │  provider  │ │   service   │
  └──────┬─────┘ └────────────┘ └──────┬──────┘
         │                             │
   ┌─────▼──────┐               ┌──────▼──────┐
   │  storage   │               │  log sink   │  off-host, append-only
   └────────────┘               └─────────────┘
```

Der Aufbau verfolgt drei Ziele: einen kontrollierten öffentlichen Zugang, eine Anmeldung mit zweitem Faktor und Auditdaten, die außerhalb der Instanz aufbewahrt werden.

## 1. Externen Identitätsanbieter einrichten {#1-put-a-real-identity-provider-in-front}

### Gründe für einen zentralen Anbieter {#why-before-how}

OpenCloud bringt `idp` und `idm` für eine direkt nutzbare Anmeldung mit. Für eine kleine Einzelinstallation kann das genügen. In einer Organisation vereinfacht ein externer Anbieter die gemeinsame Verwaltung mehrerer Anwendungen:

- Zweite Faktoren wie TOTP, WebAuthn oder Passkeys zentral einrichten.
- Konten bei Eintritt, Wechsel oder Austritt an einer Stelle verwalten.
- Sitzungsdauer, Sperren und weitere Anmelderichtlinien festlegen.
- Anmeldeversuche im zuständigen System protokollieren.

Der Scanner zeigt den erkannten Anbieter unter `identityProvider` an. Bei externem Anbieter wird ein Basic-Auth-Befund von `medium` auf `low` abgestuft; siehe [Authentifizierung](../authentication.md#6-can-the-identity-provider-be-found-at-all-identityproviderdetected).

Die vollständigen Anleitungen für Keycloak, Authentik und Authelia stehen unter [Identitätsanbieter einrichten](../identity-providers.md).

### Gemeinsame OpenCloud-Einstellungen {#what-opencloud-needs-whichever-provider-you-pick}

Die Variablen sind unabhängig vom Anbieter. Quelle: [OpenCloud-Anleitung für externe IdPs](https://docs.opencloud.eu/docs/admin/configuration/authentication-and-user-management/external-idp).

| Variable | Funktion |
|:--|:--|
| `OC_OIDC_ISSUER` | Issuer-URL, etwa `https://id.example.com/realms/opencloud` |
| `OC_EXCLUDE_RUN_SERVICES` | `idp` ergänzen, um den eingebauten Anbieter beim Start auszuschließen |
| `PROXY_OIDC_ACCESS_TOKEN_VERIFY_METHOD` | `jwt` prüft Tokens anhand der veröffentlichten Schlüssel |
| `PROXY_OIDC_REWRITE_WELLKNOWN` | `true` verweist Clients über Discovery auf den konfigurierten Anbieter |
| `PROXY_USER_OIDC_CLAIM` | Identifizierender Claim, häufig `preferred_username` |
| `PROXY_USER_CS3_CLAIM` | Passendes OpenCloud-Attribut, häufig `username` |
| `PROXY_AUTOPROVISION_ACCOUNTS` | `true` legt bei der ersten Anmeldung ein Konto an |
| `PROXY_ROLE_ASSIGNMENT_DRIVER` | `oidc` für Rollen aus einem Claim, `default` für eine gemeinsame Standardrolle |
| `PROXY_ROLE_ASSIGNMENT_OIDC_CLAIM` | Claim für die Rollen, standardmäßig `roles` |
| `GRAPH_ASSIGN_DEFAULT_USER_ROLE` | Bei Rollen aus dem Anbieter auf `false` setzen |

Bei aktiviertem Autoprovisioning muss der Anbieter den Zugriff auf die OpenCloud-Anwendung begrenzen, etwa auf eine festgelegte Gruppe. Eine erfolgreiche Anmeldung am Anbieter allein soll nicht automatisch jedem Organisationskonto Zugriff auf OpenCloud geben.

Wenn Rollen aus OIDC-Claims kommen, deaktiviere die zusätzliche automatische Standardrolle mit `GRAPH_ASSIGN_DEFAULT_USER_ROLE=false`.

### Keycloak {#keycloak}

Die [Keycloak-Anleitung](../identity-providers.md#tutorial-a-keycloak) enthält alle Schritte. Die wesentlichen Einstellungen sind:

- Ein eigener Anwendungs-Realm oder ein geeigneter vorhandener Realm.
- Vier OpenID-Connect-Clients für Web, Desktop, Android und iOS mit den jeweils passenden IDs.
- Öffentliche Clients mit Authorization Code Flow und PKCE `S256`.
- Exakte Redirect-URIs, einschließlich der Loopback-Weiterleitung mit variablem Port für Desktop-Clients.
- Issuer wie `https://id.example.com/realms/opencloud`.

Ein *User Client Role*-Mapper kann Rollen im Claim `roles` bereitstellen. Richte eine passende Passwort- und Mehrfaktorrichtlinie ein und teste sie mindestens für administrative Konten.

### Authentik {#authentik}

Die [Authentik-Anleitung](../identity-providers.md#tutorial-b-authentik) beschreibt die Einrichtung für OpenCloud. Die mitgelieferte [Authentik-Stackkonfiguration](../authentik.md) dieses Projekts schützt dagegen den Scan-Dienst.

Für OpenCloud benötigst du öffentliche OAuth2/OpenID-Provider mit PKCE, passende Redirects und eine Gruppenzuordnung für den Anwendungszugriff. Übernimm den Issuer exakt, etwa `https://id.example.com/application/o/<application-slug>/` einschließlich Schrägstrich.

Die [Blueprints](../../authentik/blueprints) zeigen, wie Provider und Regeln als Dateien bereitgestellt werden können.

### Authelia {#authelia}

Die [Authelia-Anleitung](../identity-providers.md#tutorial-c-authelia) verwendet `configuration.yml`:

- Clients unter `identity_providers.oidc.clients` mit `public: true`, `require_pkce: true` und `pkce_challenge_method: S256`.
- Scopes `openid`, `profile`, `email` und `groups`.
- Issuer wie `https://auth.example.com`.
- Bei gruppenbasierter Rollenzuordnung `PROXY_ROLE_ASSIGNMENT_OIDC_CLAIM=groups`.

Eine passende Zugriffsregel verlangt zwei Faktoren:

```yaml
access_control:
  rules:
    - domain: opencloud.example.com
      policy: two_factor
```

### Basic Auth gesondert behandeln {#basic-authentication-is-the-hole-in-all-of-this}

WebDAV-, CalDAV-, CardDAV- und manche Backup-Clients verwenden HTTP Basic Auth statt OIDC. Mit `PROXY_ENABLE_BASIC_AUTH=true` steht ihnen ein Weg offen, der den interaktiven Anmeldeablauf mit zweitem Faktor nicht durchläuft.

Lass die Option deaktiviert, wenn sie nicht benötigt wird. Verwende für notwendige Clients eigene widerrufbare App-Tokens statt Kontopasswörtern. Der [Authentifizierungsleitfaden](../authentication.md) erklärt die Bewertung.

## 2. Audit-Log aktivieren und auswerten {#2-turn-the-audit-log-on-then-read-it}

### Audit-Dienst starten {#the-audit-service-does-not-run-by-default}

OpenClouds [Audit-Dienst](https://docs.opencloud.eu/docs/dev/server/services/audit/) gehört nicht zum Standard-Dienstsatz. Aktiviere ihn ausdrücklich:

```bash
# Add it to the services that run, alongside the default set.
OC_ADD_RUN_SERVICES=audit
```

Er erfasst unter anderem:

- Dateioperationen wie Erstellen, Löschen und Verschieben, einschließlich Papierkorb und Versionierung.
- Benutzerverwaltung wie das Anlegen und Löschen von Konten.
- Freigaben, öffentliche Links und Änderungen von Berechtigungen.

Der Scanner kann eine zu offene Freigaberichtlinie erkennen. Für tatsächlich ausgeführte Freigabeaktionen benötigst du dagegen Betriebs- und Auditdaten.

Die [Audit-Referenz](https://docs.opencloud.eu/docs/dev/server/services/audit/environment-variables) beschreibt die Konfiguration:

| Variable | Standard | Verwendung |
|:--|:--|:--|
| `AUDIT_LOG_TO_CONSOLE` | `true` | Für Weiterleitung über den Container-Logtreiber |
| `AUDIT_LOG_TO_FILE` | `false` | Dateiausgabe bei Bedarf aktivieren |
| `AUDIT_FILEPATH` | leer | Bei Dateiausgabe erforderlich |
| `AUDIT_FORMAT` | `json` | Für maschinelle Auswertung beibehalten |
| `AUDIT_LOG_LEVEL` | `error` | Auf den für die gewünschte Protokollierung erforderlichen Umfang setzen |
| `OC_EVENTS_ENDPOINT` | `127.0.0.1:9233` | Adresse des Event-Brokers |
| `AUDIT_EVENTS_AUTH_USERNAME` / `_PASSWORD` | leer | Zugangsdaten für einen über das Netz erreichbaren Broker |
| `AUDIT_EVENTS_ENABLE_TLS` | `false` | Bei Netzwerkverbindungen TLS aktivieren |

Prüfe nach der Einrichtung mit bekannten Testaktionen, ob die erwarteten Ereignisse tatsächlich ankommen. Ein gestarteter Prozess allein belegt keine vollständige Protokollierung.

### Logs außerhalb der Instanz speichern {#getting-the-log-off-the-box}

Leite Auditdaten an einen getrennten Sammler weiter:

```yaml
# docker-compose fragment: hand stdout to the host's journal, which a
# collector then forwards off the machine.
services:
  opencloud:
    logging:
      driver: journald
      options:
        tag: opencloud
```

Der sendende Dienst sollte Einträge hinzufügen, aber vorhandene Daten nicht löschen oder umschreiben dürfen. Verwende getrennte Berechtigungen und eine festgelegte Aufbewahrungsdauer, unabhängig davon, ob du Loki, einen Syslog-Server oder einen anderen Sammler einsetzen.

### Geeignete Alarmregeln {#what-to-actually-alert-on}

Beginne mit Ereignissen, die in deiner Umgebung konkrete Maßnahmen auslösen:

- Öffentliche Links ohne Passwort oder Ablaufdatum, besonders in sonst nicht geteilten Bereichen.
- Erweiterte Freigabeberechtigungen.
- Neue Konten oder administrative Rollen außerhalb des vorgesehenen Prozesses.
- Ungewöhnlich viele Downloads oder Löschvorgänge eines Kontos.
- Auffällige Anmeldungen aus den Logs des Identitätsanbieters, etwa gehäufte Fehlschläge oder unerwartete Ortswechsel.

### Aufbewahrung und Datenschutz {#retention-and-the-law}

Audit-Logs können personenbezogene Informationen über Datei- und Kontozugriffe enthalten. Lege Zweck, Zugriffsrechte und Aufbewahrungsdauer fest und setze die Löschung im Sammler um. Beziehe die zuständigen Datenschutzverantwortlichen in die für deine Organisation geltenden Anforderungen ein.

## 3. Netzwerkzugriffe beschränken {#3-firewall-it-properly}

### Öffentliche und interne Ports {#the-ports-and-which-of-them-belong-on-the-internet}

| Port | Zweck | Vorgesehener Zugriff |
|:--|:--|:--|
| 443 | Reverse Proxy | Öffentlich |
| 80 | HTTP | Nur für HTTPS-Weiterleitung oder geschlossen |
| 9200 | OpenCloud-Proxy | Nur intern hinter dem Reverse Proxy |
| 9233 | Event-Broker NATS | Nur intern |
| 9205, 9141, 9124, 9134, 9239 | Debug-Listener mit Metriken, Konfiguration und gegebenenfalls Profiling | Nur intern; standardmäßig Loopback |
| 22 | SSH | Verwaltungsnetz oder VPN |

Der Scanner prüft ausgewählte Backend- und Debug-Zugänge, nicht jede Firewall-Regel und nicht sämtliche Ports. Siehe [Öffentlich zugängliche Schnittstellen](../exposure.md).

### Docker und Host-Firewall {#a-host-firewall-that-works-with-docker}

Veröffentlichte Container-Ports werden über Docker-eigene Firewall-Regeln verarbeitet. Verlasse sich daher nicht allein auf eine Anzeige von UFW.

**An Loopback binden:**

```yaml
services:
  opencloud:
    ports:
      # Not "9200:9200" - that binds 0.0.0.0.
      - "127.0.0.1:9200:9200"
```

Wenn der Reverse Proxy im selben Docker-Netz liegt, kannst du die Host-Portfreigabe ganz weglassen und OpenCloud über den Dienstnamen erreichen.

**Ausgehende und weitergeleitete Pakete gezielt filtern:** Prüfe die Docker-Daemon-Konfiguration und die Regelkette Ihres verwendeten Backends:

```json
{
  "iptables": true,
  "ip-forward": true
}
```

Beispiel für `DOCKER-USER` bei einem iptables-Backend:

```bash
# Everything reaching a container from outside must come via the proxy.
iptables -I DOCKER-USER -i eth0 -p tcp --dport 9200 -j DROP
```

Ein nftables-Beispiel:

```
table inet filter {
  chain input {
    type filter hook input priority 0; policy drop;
    ct state established,related accept
    iif lo accept
    tcp dport { 80, 443 } accept
    tcp dport 22 ip saddr 10.0.0.0/8 accept
  }
}
```

Passe Regeln an Schnittstellen, Backend und vorhandene Regeln an. Prüfe die tatsächliche Erreichbarkeit von einem anderen Host aus. Für ausgewählte Ports kannst du `nmap -Pn -p 9200,9205,9233 opencloud.example.com` verwenden; der Scanner ergänzt seine eigenen konfigurierten Prüfungen:

```bash
check-opencloud-security --host opencloud.example.com --check-hardening --debug
```

### Ausgehende Verbindungen {#egress-matters-too}

Beschränke auch ausgehenden Verkehr auf die benötigten Ziele: DNS, Zeitdienst, Zertifikatsausstellung, Paketquellen sowie konfigurierte Speicher-, Mail- und Identitätsdienste. Welche Ausnahmen nötig sind, hängt von deiner Bereitstellung ab.

## 4. Host und Daten schützen {#4-underneath-it-all-the-host-and-the-data}

- Halte Betriebssystem und OpenCloud aktuell. Der Scanner erkennt den Release-Status, installiert aber keine Updates.
- Verschlüssele Datenträger entsprechend deinem Schutzbedarf und plane Schlüsselverwaltung und Wiederherstellung.
- Teste Backups durch Wiederherstellung und halte eine gegen Änderungen durch das Produktivsystem geschützte Kopie vor.
- Gib Dienstkonten nur die nötigen Rechte. Die [systemd-Beispiele](../../contrib/systemd) zeigen Härtungsoptionen; prüfe eigene Units mit `systemd-analyze security <unit>`.
- Trenne Reverse Proxy und Dateidienst mindestens in eigene Prozesse beziehungsweise Container mit passenden Zugriffsrechten.

## 5. Hinweise für Benutzer und Administration {#5-what-the-people-using-it-should-know}

Sichere Freigaben hängen auch von verständlichen Regeln und geeigneten Voreinstellungen ab. Besprich die folgenden Punkte mit den Personen, die OpenCloud verwenden.

### Für Benutzer {#for-everybody-with-an-account}

- Behandle öffentliche Links als Zugangsberechtigung und ergänze Passwort und Ablaufdatum, wenn die Freigabe dies erfordert.
- Prüfe den freigegebenen Ordner und seine Unterordner vor dem Teilen.
- Richte einen zweiten Faktor ein; nutze unterstützte Passkeys oder Sicherheitsschlüssel, wo möglich.
- Verwende eigene App-Tokens für Clients und widerrufe nicht mehr benötigte Tokens.
- Bereits heruntergeladene Dateien lassen sich durch das Zurücknehmen eines Links nicht zurückholen.
- Melde versehentliche Freigaben frühzeitig, damit Zugriffe begrenzt und Logs geprüft werden können.

### Für Administratoren {#for-administrators}

- Prüfe öffentliche Links und Berechtigungen regelmäßig.
- Dokumentiere den Austritt von Benutzern einschließlich IdP-Konto, App-Tokens und Freigaben.
- Ermittle typische Nutzungsmuster als Grundlage für Alarmregeln.
- Halte Ansprechpartner und Zuständigkeiten für Sicherheitsvorfälle fest.

## 6. Regelmäßige Scans einbinden {#6-where-this-scanner-fits-continuous-monitoring}

### Änderungen früh erkennen {#what-a-scheduled-scan-catches-that-a-one-off-audit-does-not}

Ein einmaliger Scan beschreibt nur einen Zeitpunkt. Später können Zertifikate ablaufen, Proxy-Regeln geändert, Debug-Ports veröffentlicht, Releases abgelöst oder neue Schwachstellen bekannt werden.

Regelmäßige Scans machen solche Änderungen aus dem gewählten Netzwerk sichtbar. Wähle ein Intervall passend zu Änderungsrisiko und Scanlast und überwache auch ausgebliebene Läufe.

### Beispielkonfiguration {#a-monitoring-setup-that-is-worth-having}

Starte mit diesem Aufruf und passe ihn anhand von [Zeitplanung](../scheduling.md) oder [Icinga2 / Nagios](../installation.md#icinga2--nagios) an:

```bash
check-opencloud-security \
  --host opencloud.example.com \
  --check-hardening \
  --baseline /var/lib/check-opencloud-security/baseline.json \
  --warn-on-new \
  --webhook-url https://hooks.example.com/opencloud \
  --webhook-on warning
```

- `--check-hardening` berücksichtigt Header und Härtungsmaßnahmen.
- `--baseline` mit `--warn-on-new` beschränkt wiederholte Alarme auf neue oder verschlechterte Befunde; siehe [Änderungsvergleich](../../README.md#reporting-only-what-changed).
- Ein Webhook gibt Ergebnisse an deinen Benachrichtigungsweg weiter.
- `--ignore-hardening` dokumentiert bewusst akzeptierte Befunde. Der Befund bleibt im Bericht sichtbar; siehe [Ausnahmen](../hardening.md#accepting-a-finding-you-are-not-going-to-fix).

Für mehrere Instanzen lies [Mehrere Instanzen prüfen](../many-instances.md), für Zeitreihen [Prometheus und Grafana](../prometheus.md).

### Grenzen des Scanners {#what-it-deliberately-will-not-tell-you}

- Inhalte, Berechtigungen und Abläufe hinter einer Anmeldung werden nicht vollständig geprüft.
- Die tatsächliche Durchsetzung eines zweiten Faktors und die Rollenzuordnung musst du am Anbieter testen.
- Betrieb und Auswertung des Audit-Logs sind von außen nicht nachweisbar.
- Portprüfungen zeigen nur die Wirkung bestimmter Netzregeln aus Sicht des Scanners.
- Es werden keine Exploits und keine erratenen Passwörter verwendet. Die dokumentierte Ausnahme betrifft veröffentlichte Demokonten.

Die vollständige Beschreibung steht unter [Grenzen des Scans](../scanner-checks.md#what-the-scan-deliberately-does-not-answer).

## Checkliste {#checklist}

Passe die Liste an deine Umgebung an:

- [ ] Öffentlicher Zugriff nur auf HTTPS und gegebenenfalls HTTP-Weiterleitung
- [ ] Backend- und Debug-Ports von außen geprüft und gesperrt
- [ ] Ausgehende Verbindungen auf benötigte Ziele begrenzt
- [ ] Geeigneter Identitätsanbieter eingerichtet
- [ ] Zweiter Faktor verpflichtend, mindestens für Administratoren
- [ ] Basic Auth deaktiviert oder notwendige Clients mit App-Tokens ausgestattet
- [ ] Automatische Standardrolle bei OIDC-Rollenzuordnung deaktiviert
- [ ] Autoprovisioning durch Anwendungs- oder Gruppenregeln begrenzt
- [ ] Audit-Dienst aktiv und erwartete Testereignisse nachgewiesen
- [ ] Auditdaten getrennt gespeichert, mit definierter Aufbewahrung
- [ ] Alarmregeln für Freigaben, Berechtigungen und Konten eingerichtet
- [ ] Vertrauenswürdige, automatisch erneuerte Zertifikate und passende DNS-Regeln
- [ ] Sicherheitsheader am öffentlichen Zugang geprüft
- [ ] CORS auf benötigte Ursprünge begrenzt
- [ ] Passwort- und Ablaufregeln für öffentliche Links festgelegt
- [ ] Backups getrennt aufbewahrt und Wiederherstellung getestet
- [ ] Host aktuell und OpenCloud innerhalb des Supportzeitraums
- [ ] Regelmäßige Scans und Benachrichtigungen getestet

## Weiterführende Anleitungen {#where-to-go-next}

| Seite | Inhalt |
|:--|:--|
| [Reverse Proxys](../reverse-proxy.md) | Konfigurationsbeispiele |
| [TLS](../tls.md) | Transport- und Zertifikatsprüfungen |
| [Öffentliche Schnittstellen](../exposure.md) | Dateien, Pfade und Debug-Ports |
| [Authentifizierung](../authentication.md) | IdP und Basic Auth |
| [Freigaben](../sharing.md) | Linkrichtlinien |
| [Zeitplanung](../scheduling.md) | systemd und cron |
| [Mehrere Instanzen](../many-instances.md) | Getrennte Konfigurationen und Baselines |
| [Prometheus und Grafana](../prometheus.md) | Metriken und Zeitreihen |
| [Was ist OpenCloud?](../what-is-opencloud.md) | Architektur und Hintergrund |

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
