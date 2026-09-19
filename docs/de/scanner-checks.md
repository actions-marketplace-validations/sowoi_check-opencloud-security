# Was der OpenCloud Security Scanner liest und was nicht

Diese Übersicht beschreibt, welche Daten der Scanner von einer Instanz abruft,
welche Prüfungen die Bewertung beeinflussen und wo eine Prüfung von außen an
Grenzen stößt. Einzelheiten findest du in den Leitfäden zu [TLS](../tls.md),
[CSP](../csp.md), [Cookies](../cookies.md), [Authentifizierung](../authentication.md),
[Freigaben](../sharing.md), [öffentlich erreichbaren Diensten](../exposure.md),
[Einbettung](../embedding.md) und [Release-Unterstützung](../lifecycle.md).

## Was der Scanner prüft {#what-the-scanner-checks}

Der Scanner liest folgende Informationen direkt von der Instanz:

- Produkt, Edition und `productversion` aus `/status.php`. Ein anderes Produkt
  wird abgewiesen, da dessen Versionen und Sicherheitsmeldungen nicht zur
  OpenCloud-Datenbank passen. Die Felder `maintenance`, `installed` und
  `needsDbUpgrade` sind in OpenCloud fest vorgegeben und werden deshalb nicht
  als Zustandsprüfung verwendet; siehe [Status-Endpunkt](../status-php.md).
- Die beim Scan aufgelösten IPv4- und IPv6-Adressen. Sie stehen unter `addresses`
  im Ergebnis und dienen nur zur Einordnung. Bei direkter Eingabe einer
  IP-Adresse oder fehlgeschlagener Namensauflösung bleibt die Liste leer.
- Funktionen und Einstellungen aus `/ocs/v1.php/cloud/capabilities`.
  Dieser Endpunkt und `/status.php` sind ohne Anmeldung lesbar.
- Die Header `Strict-Transport-Security`, `Content-Security-Policy`,
  `X-Content-Type-Options`, `X-Frame-Options`,
  `X-Permitted-Cross-Domain-Policies`, `X-Robots-Tag`, `X-XSS-Protection` und
  `Referrer-Policy`. Sie erscheinen unter `setup.headers`.
- Vier weitere Header unter `setup.advisoryHeaders`: `Permissions-Policy`,
  `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy` und
  `Cross-Origin-Embedder-Policy`. OpenCloud setzt sie standardmäßig nicht.
  Fehlende Werte werden erklärt, lösen aber weder einen Alarm noch eine
  schlechtere Bewertung aus. Teste insbesondere
  `Cross-Origin-Embedder-Policy: require-corp` mit deiner Office-Integration,
  bevor du den Header aktivierst; eingebundene Dienste müssen dazu passende
  Ressourcenfreigaben senden. Siehe [ADR 0028](../../adr/0028-headers-no-opencloud-sends-are-reported-but-never-alerted.md).
- `securityTxtPublished` unter `setup.advisoryChecks`: Enthält
  `/.well-known/security.txt` einen `Contact`-Eintrag gemäß RFC 9116?
  HTTP 200 allein reicht nicht aus. Auch diese Beobachtung bleibt ohne Alarm,
  da OpenCloud die Datei nicht mitliefert; siehe [ADR 0034](../../adr/0034-an-advisory-observation-need-not-be-a-header.md).
- `hstsPreloadEligible` prüft unter `setup.advisoryChecks`, ob der HSTS-Header
  mindestens ein Jahr Laufzeit sowie `includeSubDomains` und `preload` enthält.
  `hstsPreload` erfasst dagegen nur den Wunsch nach Aufnahme. OpenClouds
  Standardheader enthält kein `includeSubDomains`; der zusätzliche Hinweis
  beeinflusst daher die Bewertung nicht. Die tatsächliche Mitgliedschaft in
  einer Browserliste wird nicht abgefragt; siehe [ADR 0037](../../adr/0037-preload-eligibility-is-measured-list-membership-is-not.md).
- Aus Headern und Capabilities abgeleitete Maßnahmen unter `hardenings`.
- Bekannte Schwachstellen anhand der [lokalen Datenbank](../../README.md#advisory-database)
  und die daraus berechnete Bewertung von `0` bis `5`.

Die folgenden zusätzlichen Prüfungen erscheinen unter `extraChecks`.
Mit `--no-extra-checks` lass sich ausschalten.

| Prüfung | Schweregrad | Was ein Fehlschlag bedeutet |
|:--|:--|:--|
| `httpsAvailable`, `tlsHandshake`, `tlsProtocol` | kritisch/hoch | Nur HTTP erreichbar, TLS-Verbindung fehlgeschlagen oder Protokoll älter als TLS 1.2 |
| `tlsCertificate`, `tlsTrusted` | hoch/mittel | Zertifikat abgelaufen, innerhalb von `scanner.tls_min_days` ablaufend oder nicht vertrauenswürdig |
| `tlsDeprecatedProtocol` | hoch | TLS 1.0 oder 1.1 wird weiterhin angenommen |
| `tlsHostname` | hoch | Zertifikat gilt nicht für den angefragten Namen |
| `tlsChain` | mittel | Zwischenzertifikat fehlt in der gesendeten Kette |
| `tlsCertificateLifetime` | niedrig | Laufzeit überschreitet den Prüfgrenzwert von 398 Tagen |
| `tlsCipherSuite` | mittel | Ausgehandelte Cipher Suite ist schwach oder bietet keine Forward Secrecy |
| `tlsCertificatePolicy` | mittel | Schwacher Schlüssel oder MD5-/SHA-1-Signatur |
| `tlsAddressParity` | mittel | IPv4 und IPv6 liefern unterschiedliche TLS-Dienste oder eine Adresse ist unerreichbar |
| `addressParity` | hoch/mittel | Mit `--all-addresses`: Abweichende Version, Header, Schutzmaßnahmen oder Demo-Konten; alternativ eine unerreichbare Adresse |
| `tlsCaaRecord` | niedrig | Kein CAA-Eintrag beschränkt die ausstellenden Zertifizierungsstellen |
| `tlsDnssec` | niedrig | Die Zone ist nicht signiert; ohne auswertbare DNSSEC-Antwort entfällt die Prüfung |
| `companionAdminConsole` | hoch | Verwaltungskonsole des auf derselben Origin veröffentlichten Office-Dienstes erreichbar |
| `companionEditorHttps` | hoch | WOPI-Discovery nennt Editor-Adressen mit unverschlüsseltem HTTP |
| `cookieSecure`, `cookieHttpOnly`, `cookieSameSite` | hoch bis niedrig | Ein beobachtetes Cookie enthält das jeweilige Attribut nicht |
| `cookiePrefix` | niedrig | Kein beobachtetes Cookie nutzt `__Host-`/`__Secure-`, oder die zugehörigen Anforderungen sind nicht erfüllt |
| `tlsOcspStapling` | niedrig | Keine angeheftete OCSP-Antwort trotz Responder im Zertifikat |
| `tlsCertificateTransparency` | mittel | Öffentlich vertrauenswürdiges Zertifikat enthält keine eingebetteten SCTs |
| `tlsEarlyData` | niedrig | TLS-1.3-Sitzungstickets erlauben 0-RTT-Daten ohne Replay-Schutz |
| `corsOriginRestricted` | kritisch/mittel | Beliebige Origins dürfen API-Antworten lesen; mit Zugangsdaten kritisch |
| `traceMethodDisabled` | mittel | Der Server spiegelt eine TRACE-Anfrage |
| `forwardedHostIgnored` | mittel | Ein vom Aufrufer gesetzter Hostname erscheint in veröffentlichten Anmelde-URLs |
| `header:<name>` | hoch bis niedrig | Ein bewerteter Sicherheitsheader fehlt oder ist zu schwach |
| `authentication:/remote.php/dav/files/`, `/graph/v1.0/users`, `/ocs/v1.php/cloud/user` | kritisch/hoch | Ein geschützter Endpunkt antwortet ohne erforderliche Anmeldung |
| `exposed:/opencloud.yaml`, `/proxy/server.key`, `/idm/opencloud.boltdb`, `/.env`, `/docker-compose.yml`, `/storage/users/`, `/.git/config` | kritisch/hoch | Interne Dateien sind über den Reverse Proxy öffentlich abrufbar |
| `directoryListing` | kritisch | Verzeichnisauflistung statt Weboberfläche |
| `demoUsersDisabled` | kritisch | Dokumentierte Demo-Zugangsdaten funktionieren noch |
| `debugEndpoint:/metrics`, `/config`, `/debug/pprof/` | kritisch/hoch | Debug-Endpunkte öffentlich erreichbar |
| `debugPort:<port>` | hoch | Debug-Port von außen erreichbar |
| `backendPortClosed` | hoch | Dieselbe Instanz ist unter Port 9200 am Reverse Proxy vorbei erreichbar |
| `webEmbedDelegatedAuthenticationRestricted` | kritisch | Delegierte iframe-Anmeldung ohne ausdrückliche Einschränkung der vertrauenswürdigen Origin |
| `webEmbedMessageOriginRestricted` | hoch | Embed-Nachrichten vertrauen jeder übergeordneten Origin |
| `basicAuthDisabled` | mittel | Der Proxy bietet weiterhin HTTP Basic Auth an |
| `identityProviderDetected` | niedrig | Kein Identity Provider über OIDC-Discovery oder Weiterleitung erkennbar |
| `reverseProxyDetected` | niedrig | Kein Hinweis auf einen vorgeschalteten Reverse Proxy |
| `versionDisclosure:Server`, `webfingerVersionDisclosure` | niedrig | Exakte Versionen ohne Anmeldung lesbar |

Fehlgeschlagene Zusatzprüfungen begrenzen die Note: kritisch auf `D`, hoch auf
`C`, mittel auf `A`, niedrig auf `A+`. Mit `scanner.extra_checks_rating: false`
bleiben die Ergebnisse sichtbar, beeinflussen die Note aber nicht.

OpenClouds Weboberfläche beantwortet auch unbekannte Pfade häufig mit HTTP 200
und der Startseite. Der Scanner ruft deshalb zunächst einen nicht existierenden
Pfad ab. Eine Datei gilt nur dann als offengelegt, wenn ihre Antwort von dieser
Vergleichsantwort abweicht.

### Wer die Anmeldung übernimmt {#who-signs-users-in}

Über `/.well-known/openid-configuration` und gegebenenfalls dessen
Weiterleitung ermittelt der Scanner den Identity Provider. Ein Issuer auf
einem anderen Host weist auf einen externen Anbieter hin:

```json
{"identityProvider": {"detected": true, "external": true,
                      "issuer": "https://id.example.com", "vendor": "Keycloak"}}
```

Das Ergebnis beschreibt die Architektur, ohne den eingebauten Provider
abzuwerten. Lediglich `basicAuthDisabled` fällt bei externem Provider von
`medium` auf `low`. Für diese Erkennung liest der Scanner nur das
Discovery-Dokument und den `Location`-Header; er meldet sich nicht an.

Ist kein Provider erkennbar, schlägt `identityProviderDetected` mit `low` fehl.
Prüfe dann insbesondere, ob der Reverse Proxy `/.well-known/`
weiterleitet. [OpenClouds Anleitung][opencloud-idp] beschreibt die Einrichtung.

### Die Demo-Konten {#the-demo-accounts}

Nennt die Discovery den eingebauten Provider der Instanz, prüft der Scanner
zusätzlich die veröffentlichten Demo-Zugangsdaten.
`IDM_CREATE_DEMO_USERS=true` legt fünf [dokumentierte Konten][opencloud-demo-users]
an; `dennis` besitzt Administratorrechte. Funktioniert eine Anmeldung, ist
`demoUsersDisabled` kritisch und begrenzt die Note auf `D`.

Dies ist die einzige Prüfung, die Zugangsdaten sendet. SIE verwendet nur die
veröffentlichten Paare und ausschließlich den Provider auf der Origin der
Instanz. Externe Identity Provider werden damit nicht angesprochen. Das
Ausschalten der Einstellung löscht vorhandene Konten nicht: Entferne diese
zusätzlich.

### Was vor der Instanz steht {#what-is-in-front-of-the-instance}

`reverseProxy` erfasst Hinweise auf einen vorgeschalteten Dienst, etwa einen
entsprechenden `Server`-Header oder `Via`:

```json
{"reverseProxy": {"detected": true, "vendor": "Nginx", "evidence": "Server: nginx"}}
```

Ohne solche Hinweise schlägt `reverseProxyDetected` mit `low` fehl. Das beweist
nicht, dass ein Proxy fehlt: Traefik und HAProxy geben sich standardmäßig nicht
zu erkennen, und andere Proxys können ihre Kennung entfernen.

`forwardedHostIgnored` prüft, ob ein Aufrufer die veröffentlichten Anmelde-URLs
beeinflussen kann. Dazu fordert der Scanner die OIDC-Discovery zweimal mit
einem erfundenen Hostnamen an, einmal in `Host`, einmal in
`X-Forwarded-Host`. Er sucht diesen Namen in Weiterleitungen sowie in `issuer`,
`authorization_endpoint`, `token_endpoint`, `end_session_endpoint` und `jwks_uri`:

```json
{"id": "forwardedHostIgnored", "severity": "medium", "passed": false,
 "detail": "A host name the caller supplied is published back: X-Forwarded-Host comes back as the issuer it publishes"}
```

Solche URLs bestimmen das Ziel einer Anmeldung. Ohne weitere Bedingungen
betrifft die manipulierte Antwort zunächst den Aufrufer selbst; deshalb ist der
Schweregrad `medium`. Ein gemeinsamer Cache oder ungeprüft weitergereichte
Client-Header können die Wirkung auf andere Benutzer ausweiten. Setze
`OC_URL` und lass den Proxy die Forwarded-Header selbst festlegen.

Wird nur `Host` in einer Weiterleitung wiederholt, prüfe auch den
Standard-VHost. Ohne ausdrückliche Ablehnung unbekannter Namen kann der Proxy
sie an den zuerst geladenen Dienst weitergeben; siehe
[häufige Proxy-Fehler](../reverse-proxy.md#mistakes-that-cost-a-grade).
Ein Hostname im Text einer Fehlerseite zählt nicht als Befund. Fehlt ein
Discovery-Dokument vollständig, bleibt die Prüfung ohne Ergebnis.

### Alternative Dienste (HTTP/3) {#alternative-services-http3}

`alternativeServices` hält fest, was die Instanz im `Alt-Svc`-Header
ankündigt. Ein `h3`-Eintrag bringt jeden Browser dazu, HTTP/3 über **UDP** auf
dem genannten Port zu versuchen - ein Listener, den eine Firewall für TCP 443
womöglich nicht abdeckt und den ein Reverse Proxy einschalten kann, ohne dass
du es bewusst entschieden hast.

```json
{"alternativeServices": {"advertised": true, "http3": true,
  "entries": [{"protocol": "h3", "host": "", "port": 443, "udp": true}],
  "header": "h3=\":443\"; ma=86400"}}
```

Das ist eine Beobachtung und wird nie bewertet: HTTP/3 ist keine Schwäche,
nur etwas, das du bewusst in der Firewall freigeben solltest. Das Plugin gibt
dazu eine Detailzeile aus. Die angekündigte Adresse wird nie geprüft - sie
ist eine Angabe des Ziels, keine Origin, auf die der Scan gerichtet wurde
([ADR 0036](../../adr/0036-a-companion-service-is-probed-only-where-the-scan-was-pointed.md)).
`Alt-Svc: clear` gilt als nichts angekündigt; ohne Antwort ist der Schlüssel
`null`.

### Fehlgeschlagene Anmeldungen (optional) {#failed-sign-ins-opt-in}

Mit `--login-throttling` (`COS_LOGIN_THROTTLING` oder
`scanner.check_login_throttling`) sendet der Scan nacheinander sechs
fehlgeschlagene Anmeldungen für ein zufälliges Konto, das es nicht geben kann,
und hält fest, ob die Instanz sie gebremst hat - ein HTTP `429` oder ein
`Retry-After`-Header:

```json
{"loginThrottling": {"tested": true, "attempts": 4, "throttled": true,
  "evidence": "HTTP 429, Retry-After: 30", "statuses": [401, 401, 401, 429]}}
```

Standardmäßig ist das aus. Gefragt wird nur der eingebaute Identitätsanbieter,
und zwar nach allen anderen Prüfungen, damit ein `429` die Demo-Konten nicht
verdeckt. Bewertet wird es nie: Viele Installationen bremsen über ein längeres
Zeitfenster oder auf einer Ebene, die ein kurzer Versuch nicht erreicht - "nicht
gebremst" ist also ein Anlass, nachzusehen, kein Urteil. Der öffentliche
Webdienst sendet diese Anmeldungen nie
([ADR 0069](../../adr/0069-login-throttling-is-observed-only-when-the-operator-asks.md)).
Ohne die Option ist der Schlüssel `null`.

### Office- und Kalenderanbindungen {#office-and-calendar-integrations}

Zwei Beobachtungen sind ohne Anmeldung möglich:

- `/app/list` nennt tatsächlich registrierte App-Provider. Der fest vorgegebene
  Block `app_providers` in den Capabilities eignet sich dafür nicht.
- Eine Weiterleitung oder Anmeldeaufforderung unter `/.well-known/caldav` weist
  auf einen angebundenen Kalenderdienst hin; eine Standardinstanz antwortet 404.

```json
{"integrations": {"office": {"detected": true, "apps": ["Collabora"], "groupware": false},
                  "calendar": {"detected": true, "advertised": true}}}
```

Diese Informationen ändern die Bewertung nicht. Gesonderte Prüfungen greifen,
wenn ein Office-Dienst auf derselben Origin veröffentlicht wird und unter
`/hosting/discovery` antwortet: `companionAdminConsole` prüft den Pfad der
Verwaltungskonsole, `companionEditorHttps` die angekündigten Editor-Adressen.

Der Scanner folgt keinem fremden Editor-Host aus dem Dokument. Andernfalls
könnte die geprüfte Instanz das nächste Verbindungsziel bestimmen. Bei einem
separaten Host fehlen diese Befunde; prüfe den Office-Dienst mit dafür
geeigneten Werkzeugen. Siehe [ADR 0036](../../adr/0036-a-companion-service-is-probed-only-where-the-scan-was-pointed.md).

### Was ein Scan von außen nicht beantworten kann {#what-the-scan-deliberately-does-not-answer}

- **Audit-Protokollierung:** Der interne Audit-Dienst veröffentlicht keinen
  Endpunkt, an dem seine Aktivierung erkennbar wäre.
- **Korrekte Integration:** Ein registrierter App-Provider sagt nichts über
  WOPI-Geheimnisse, Berechtigungen oder die Einstellungen des anderen Dienstes.
- **Geschützte Inhalte:** Der Scanner verwendet keine Benutzerzugänge. Die
  ausdrücklich beschriebenen Demo-Zugangsdaten sind die einzige Ausnahme.
- **Firewall, Anmelderichtlinien und Backups:** Diese musst du im Betrieb
  gesondert kontrollieren.

Der Leitfaden [OpenCloud sicher betreiben](../secure-deployment.md) behandelt diese
Aufgaben, einschließlich Identity Provider, Audit-Logs, Docker-Ports und der
Einbindung regelmäßiger Scans.

[opencloud-idp]: https://docs.opencloud.eu/docs/admin/configuration/authentication-and-user-management/external-idp
[opencloud-demo-users]: https://docs.opencloud.eu/docs/admin/resources/demo-user/

## Die richtige Versionsnummer lesen {#reading-the-version-correctly}

`/status.php` liefert drei Versionsfelder:

```json
{"version":"0.1.0.0","versionstring":"0.1.0","productversion":"7.4.0"}
```

Nur `productversion` nennt das tatsächliche Release. `version` und
`versionstring` sind Kompatibilitätswerte. Der Scanner bevorzugt
`productversion`, verwendet ersatzweise die Capabilities und setzt
`legacyVersion: true`, wenn nur ein Platzhalter verfügbar ist. Prüfe auch
in deinen Monitoring-Skripten, welches Feld du auswertest.

## Debug-Ports {#debug-ports}

OpenCloud-Dienste haben Debug-Listener für `/healthz`, `/readyz`, `/metrics`,
`/config` und `/debug/pprof`. Darüber können Versionsdaten und Konfigurationen
sichtbar werden; Profiling-Endpunkte erlauben zusätzlich das Starten einer
Profilerhebung. Die Listener binden standardmäßig an Loopback. Eine Antwort
von außerhalb kann auf eine zu weit gefasste Portfreigabe hinweisen.

Der Scanner prüft diese fünf Ports:

| Port | Dienst |
|:--|:--|
| 9205 | proxy |
| 9141 | frontend |
| 9124 | graph |
| 9134 | idp |
| 9239 | idm |

Jeder Verbindungsversuch wartet bis zu drei Sekunden; nacheinander sind das bis
zu 15 Sekunden. Mit `--no-debug-ports` entfällt die Prüfung. Die Parallelität
innerhalb eines Scans steuert `scanner.concurrency`; weitere Einstellungen:

```yaml
scanner:
  check_debug_ports: true
  debug_ports: [9205, 9141]
  debug_port_timeout: 1
```

### Scans beschleunigen {#speeding-the-scan-up}

Die meiste Laufzeit entfällt auf Netzwerkantworten. `scanner.concurrency`
führt Prüfungen einer Instanz parallel aus; `--concurrency` begrenzt dagegen
die gleichzeitig geprüften [Hosts](../../README.md#checking-multiple-hosts).
Mehr Parallelität verkürzt Wartezeiten, erhöht aber die gleichzeitige Last.

Die Reihenfolge und Bewertung der Befunde bleiben gleich. Werte über `32`
werden begrenzt. Eine gemeinsame Einstellung für alle Hosts:

```yaml
scanner:
  concurrency: 8
```

## Alle aufgelösten Adressen vergleichen {#every-resolved-address}

Ein normaler Scan erreicht nur eine der aufgelösten Adressen. Bei mehreren
Servern kann dadurch eine abweichend konfigurierte Installation unbemerkt
bleiben. `tlsAddressParity` vergleicht lediglich die TLS-Identität einer IPv4-
und einer IPv6-Adresse.

`--all-addresses` (`COS_ALL_ADDRESSES`, `scanner.check_all_addresses`) wiederholt
für jede aufgelöste Adresse nacheinander:

- die Versionsabfrage über `/status.php` oder die Capabilities,
- die bewerteten Sicherheitsheader, verglichen nach Prüfergebnis statt nach
  wechselnden Werten wie CSP-Nonces,
- Schutzmaßnahmen aus Startseite, Capabilities, Anmeldeaufforderung und Provider,
- die Prüfung der Demo-Zugangsdaten.

Zertifikatskette, CAA, DNSSEC und Debug-Ports werden nicht erneut geprüft.
`Host` und SNI behalten den ursprünglichen Namen; nur das Verbindungsziel
wechselt. Die Adressen stammen ausschließlich aus der Namensauflösung.
Bei ausgeschaltetem `scanner.ipv6_enabled` entfallen IPv6-Adressen.

`addressParity` vergleicht mit der ersten Adresse:

| Abweichung | Schweregrad |
|:--|:--|
| Demo-Anmeldung funktioniert nur an einer weiteren Adresse | wie `demoUsersDisabled` |
| Andere Release-Version | hoch |
| Header oder Schutzmaßnahme besteht nur auf einem Teil der Adressen | mittel |
| Eine aufgelöste Adresse antwortet nicht | mittel |

Ausgenommene Prüfungen werden nicht verglichen. Bei nur einer Adresse entfällt
der Befund samt Zusatzanfragen. `addressObservations` enthält die Messungen.

Die Funktion ist standardmäßig aus. SIE verursacht etwa ein Dutzend Anfragen
je Adresse einschließlich Demo-Anmeldung. Server hinter einer einzigen
Loadbalancer-Adresse, rotierende DNS-Antworten und GeoDNS schränken die
Aussagekraft ein. Der öffentliche Webdienst verwendet sie nicht; siehe
[ADR 0042](../../adr/0042-every-resolved-address-is-compared-only-when-the-operator-asks.md).

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
