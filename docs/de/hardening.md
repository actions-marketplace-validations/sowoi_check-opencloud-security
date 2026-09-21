# Härtungsmaßnahmen und Ausnahmen

Die kurzen Kennungen der Härtungsmaßnahmen erscheinen in Alarmen und Berichten. Dieser Leitfaden erklärt die Befunde, die passenden Einstellungen und den Umgang mit bewusst akzeptierten Ausnahmen.

`--debug` zeigt die Erklärung direkt neben jedem Befund an. Wie die Maßnahmen in Ausgabe und Metriken eingehen, steht im [Haupt-README](../../README.md#hardening-checks).

## Bedeutung der Maßnahmen {#what-each-measure-means}

| Kennung | Bedeutung eines Fehlers | Einstellung |
|:--|:--|:--|
| `basicAuthDisabled` | HTTP Basic Auth ist verfügbar. Damit lassen sich Anmeldedaten pro Anfrage senden, ohne den interaktiven SSO-Ablauf mit zweitem Faktor zu durchlaufen. Für CalDAV-, CardDAV- und WebDAV-Clients kann dies erforderlich sein. Schweregrad `medium`, bei externem Identitätsanbieter `low`. | [`PROXY_ENABLE_BASIC_AUTH=false`][proxy-env], wenn Basic Auth nicht benötigt wird. Andernfalls App-Tokens statt Kontopasswörtern verwenden. |
| `cspWithoutUnsafeInline` | Die CSP erlaubt `unsafe-inline`. Dies entspricht der OpenCloud-Standardkonfiguration; Einzelheiten folgen unten. | Eigene `csp.yaml` über [`PROXY_CSP_CONFIG_FILE_LOCATION`][proxy-env] laden oder die Standardrichtlinie mit `PROXY_CSP_CONFIG_FILE_OVERRIDE_LOCATION` ersetzen. |
| `publicLinkPasswordEnforced` | Öffentliche Links können ohne Passwort erstellt werden. Standardmäßig verlangt OpenCloud ein Passwort für schreibgeschützte, aber nicht für beschreibbare Links. | [`OC_SHARING_PUBLIC_SHARE_MUST_HAVE_PASSWORD=true`][sharing-env] und `OC_SHARING_PUBLIC_WRITEABLE_SHARE_MUST_HAVE_PASSWORD=true`. |
| `passwordPolicyEnforced` | Linkpasswörter dürfen kürzer als acht Zeichen sein. Kontopasswörter unterliegen dagegen der Richtlinie des Identitätsanbieters. | [`OC_PASSWORD_POLICY_MIN_CHARACTERS`][link-password], Standard `8`, sowie die Einstellungen für Klein- und Großbuchstaben, Ziffern und Sonderzeichen. |
| `passwordPolicyComplexity` | Mindestens eine Anforderung an Kleinbuchstaben, Großbuchstaben, Ziffern oder Sonderzeichen wurde unter den Standard `1` abgesenkt. Bei deaktivierter Richtlinie ist das Ergebnis unbekannt. | [`OC_PASSWORD_POLICY_MIN_LOWERCASE_CHARACTERS`][link-password] und die entsprechenden Variablen für `MIN_UPPERCASE`, `MIN_DIGITS` und `MIN_SPECIAL_CHARACTERS` auf mindestens `1` setzen. |
| `hstsLongMaxAge` | `Strict-Transport-Security` enthält ein `max-age` unter einem Jahr. | Im vorgeschalteten Reverse Proxy prüfen. OpenCloud selbst sendet zehn Jahre. |
| `hstsPreload` | Im HSTS-Header fehlt die Direktive `preload`. Die Direktive allein belegt keine Aufnahme in eine Browserliste. | Im Reverse Proxy setzen, wenn alle Subdomains ausschließlich HTTPS verwenden können und eine Aufnahme in die Preload-Liste beabsichtigt ist. |
| `hstsPreloadEligible` | Der Header erfüllt nicht alle Voraussetzungen für Preloading: mindestens ein Jahr `max-age`, `includeSubDomains` und `preload`. OpenCloud lässt `includeSubDomains` standardmäßig weg. Der Befund steht unter `setup.advisoryChecks` und löst keinen Alarm aus. Eine tatsächliche Listeneintragung wird nicht geprüft; siehe [ADR 0037](../../adr/0037-preload-eligibility-is-measured-list-membership-is-not.md). | Zuerst HTTPS für alle Subdomains sicherstellen, dann `includeSubDomains` im Reverse Proxy ergänzen und die Domain bei [hstspreload.org](https://hstspreload.org/) einreichen. |
| `publicLinkExpirationEnforced` | OpenCloud setzt diese Capability fest auf `false`. Der Befund löst keinen Alarm aus. | Keine konfigurierbare Einstellung. |
| `userEnumerationRestricted` | Die Kontensuche ist auf gemeinsame Gruppen beschränkt. OpenCloud gibt diesen Zustand fest vor; die Prüfung besteht daher immer. | Keine konfigurierbare Einstellung. |
| `oidcPkceSupported` | Das Discovery-Dokument nennt `code_challenge_methods_supported`, enthält aber kein `S256`. Ohne dieses Feld wird kein Befund erzeugt; der eingebaute Anbieter lässt es weg. | PKCE mit `S256` beim Anbieter verlangen: in Keycloak über *Proof Key for Code Exchange*, bei Authentik für den öffentlichen Client, bei Authelia über `require_pkce`. |
| `oidcImplicitFlowDisabled` | `response_types_supported` bietet weiterhin `token` oder `id_token` vom Autorisierungsendpunkt an. Die Prüfung gilt nur für externe Anbieter; der eingebaute Anbieter lässt sich hier nicht umstellen. | Client auf Authorization Code Flow beschränken; in Keycloak Standard Flow aktivieren und Implicit Flow deaktivieren. |
| `oidcSigningAlgorithmStrong` | `id_token_signing_alg_values_supported` bietet `none` oder einen `HS`-Algorithmus an. Ein öffentlicher Client kann das dafür benötigte gemeinsame Geheimnis nicht schützen. Der eingebaute Anbieter verwendet `PS256`. | Nur asymmetrische Verfahren wie `RS256`, `PS256`, `ES256` oder `EdDSA` anbieten; `none` und `HS` entfernen. |
| `oidcEndpointsUseHttps` | Ein Endpunkt im Discovery-Dokument verwendet `http://`. Die Prüfung läuft nur, wenn die Instanz selbst über HTTPS antwortet; sonst erfasst bereits `httpsEnforced` das Problem. | Anbieter über HTTPS veröffentlichen und die öffentliche `https://`-Adresse als Issuer konfigurieren. |

[proxy-env]: https://docs.opencloud.eu/docs/dev/server/services/proxy/environment-variables
[sharing-env]: https://docs.opencloud.eu/docs/dev/server/services/sharing/environment-variables
[frontend-env]: https://docs.opencloud.eu/docs/dev/server/services/frontend/environment-variables
[link-password]: https://docs.opencloud.eu/docs/admin/configuration/link-password-policy

## Fest vorgegebene Werte {#measures-that-are-not-settings}

Zwei Maßnahmen lassen sich nicht konfigurieren:

- **`publicLinkExpirationEnforced`** ist im Frontend-Dienst fest auf `false` gesetzt. Es gibt keine Variable, mit der die Prüfung bestanden werden könnte.
- **`userEnumerationRestricted`** ist fest auf den eingeschränkten Zustand gesetzt und besteht daher immer.

Die Werte bleiben im Ergebnisdokument und in `--debug` sichtbar. Der Befund wird aus der Zeile „Missing hardening“, der Metrik `hardenings_missing` und dem Webhook ausgeschlossen, damit nicht behebbare Befunde keine dauerhaften Alarme erzeugen.

Auch `cspWithoutUnsafeInline` schlägt mit OpenClouds Standard-CSP fehl. Diese Richtlinie ist jedoch konfigurierbar. Teste eine strengere CSP vor dem Einsatz, da die Weboberfläche sowie Office- und Anmeldeintegrationen Inline-Skripte oder -Styles benötigen können. Näheres erklärt der [CSP-Leitfaden](../csp.md).

Aus Capabilities abgeleitete Prüfungen erscheinen nur, wenn die Instanz das jeweilige Feld tatsächlich liefert. Ältere Releases erhalten dadurch keine Befunde für unbekannte Einstellungen.

## Befunde bewusst ausnehmen {#accepting-a-finding-you-are-not-going-to-fix}

Eine Einstellung kann in deiner Umgebung erforderlich sein, etwa Basic Auth für ein Migrationstool. Mit `--ignore-hardening` kannst du einen solchen Befund anhand seiner Kennung aus der Alarmierung und Bewertung ausnehmen:

```bash
check-opencloud-security --host opencloud.example.com --check-hardening \
    --ignore-hardening cspWithoutUnsafeInline \
    --ignore-hardening basicAuthDisabled
```

Die Option ist wiederholbar, akzeptiert kommagetrennte Listen und unterstützt Shell-Platzhalter für Kennungen mit Pfad oder Port:

```bash
--ignore-hardening 'debugPort:*,exposed:/status.php'
```

Die Ausnahme gilt für Härtungsmaßnahmen, Headernamen, `httpsEnforced` und die Kennungen zusätzlicher Prüfungen. So wird beispielsweise `basicAuthDisabled` an allen Stellen einheitlich ausgenommen.

Ein ausgenommener Befund:

- senkt die Bewertung nicht mehr,
- erscheint nicht in `Missing hardening:` oder `Additional checks failed`,
- zählt nicht zu `hardenings_missing` oder `extra_checks_failed`,
- fehlt im Webhook-Payload,
- bleibt im JSON-Dokument mit `"ignored": true` erhalten und wird als `Ignored by configuration (n): ...` aufgeführt.

`--debug` erklärt den Befund weiterhin. Die Ausnahme ist dadurch auch für andere Personen nachvollziehbar.

Zwei Grenzen gelten immer:

- **Nur tatsächlich fehlgeschlagene Prüfungen werden ausgenommen.** Eine bestandene Prüfung wird nicht nachträglich als ignoriert markiert.
- **Das Supportende lässt sich nicht ausnehmen.** Eine Version ohne Sicherheitsupdates erhält auch mit `--ignore-hardening '*'` die End-of-Life-Bewertung.

Halte Ausnahmen möglichst in der Konfigurationsdatei fest und begründe jede davon in einem Kommentar:

```yaml
scanner:
  release_track: production
  ignore_hardenings:
    - cspWithoutUnsafeInline   # default csp.yaml, tightening it breaks the web UI
    - hstsPreload              # the reverse proxy sets its own HSTS header
```

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
