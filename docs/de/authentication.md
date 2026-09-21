# Authentifizierung prüfen

Der Scanner prüft den Schutz von Endpunkten, HTTP Basic Auth, bekannte Demokonten und die öffentlich erkennbaren Anmeldeeinstellungen. Dazu liest er die Capabilities und das OpenID-Connect-Discovery-Dokument. Er errät keine Zugangsdaten. Die einzige Prüfung mit Passwörtern verwendet die unten beschriebenen veröffentlichten Demozugänge. Weitere Grenzen stehen unter [Prüfumfang](../scanner-checks.md#what-the-scan-deliberately-does-not-answer).

## 1. Geschützte Endpunkte: `authentication:<path>` {#1-do-protected-endpoints-actually-require-a-session-authenticationpath}

Diese Pfade werden ohne Zugangsdaten abgefragt:

| Pfad | Schweregrad |
|:--|:--|
| `/remote.php/dav/files/` | critical |
| `/graph/v1.0/users` | critical |
| `/ocs/v1.php/cloud/user` | high |

`401`, `403`, `405`, `501`, eine Weiterleitung zur Anmeldung und `404` gelten für diese Prüfung als geschützter Zugriff. `405` und `501` können entstehen, wenn ein Proxy `GET` auf einer WebDAV-Sammlung nicht unterstützt; `404` deckt absichtlich verborgene Pfade ab. Andere Antworten, insbesondere `200` mit geschützten Inhalten, führen zum Befund. Ein nicht erreichbarer Endpunkt wird hier als bestanden behandelt, da ein Netzwerkfehler keinen offenen Zugriff belegt.

**Bei einem Befund:** Rufe den genannten Pfad selbst auf und prüfe die Antwort. Auch eine eigene Fehlerseite eines Proxys oder Caches kann die Ursache sein. Sind tatsächlich geschützte Daten ohne Sitzung zugänglich, schließe den Zugriff und behandle die betreffenden Inhalte als offengelegt.

## 2. HTTP Basic Auth: `basicAuthDisabled` {#2-does-the-proxy-still-offer-http-basic-authentication-basicauthdisabled}

Ein `Basic`-Challenge im Header `WWW-Authenticate` zeigt, dass der Endpunkt Benutzername und Passwort pro Anfrage akzeptiert. Dieser Weg durchläuft nicht die interaktive Anmeldung des Identitätsanbieters mit dessen zweitem Faktor.

CalDAV-, CardDAV- und viele WebDAV-Clients benötigen diesen Mechanismus. Der Scanner bewertet ihn deshalb mit `medium`, bei erkanntem externem Anbieter für die interaktive Anmeldung mit `low`. Siehe [Anmeldeanbieter erkennen](../scanner-checks.md#who-signs-users-in).

**Behebung:** Setze `PROXY_ENABLE_BASIC_AUTH=false`, wenn kein Client Basic Auth benötigt. Andernfalls verwende widerrufbare App-Tokens statt Kontopasswörtern.

## 3. Veröffentlichte Demokonten: `demoUsersDisabled` {#3-do-the-documented-demo-accounts-still-sign-in-demousersdisabled}

`IDM_CREATE_DEMO_USERS=true` legt fünf Konten an, darunter ein Administratorkonto. Namen und Passwörter stehen in der [OpenCloud-Dokumentation][opencloud-demo-users]. Der Scanner testet ausschließlich diese Paare und nur dann, wenn zuvor der eingebaute Identitätsanbieter der Instanz erkannt wurde. Externe Anbieter werden nicht mit Demopasswörtern angesprochen.

Funktionierende Demozugänge sind ein `critical`-Befund und begrenzen die Note auf `D`.

**Behebung:** Setze `IDM_CREATE_DEMO_USERS=false` und lösche bereits angelegte Demokonten. Die Einstellung allein entfernt sie nicht. Untersuche einen öffentlich erreichbaren funktionierenden Administrator-Demozugang als möglichen unbefugten Zugriff, da das Passwort veröffentlicht ist.

## 4. Kontensuche: `userEnumerationRestricted` {#4-is-account-search-restricted-to-shared-groups-userenumerationrestricted}

Die Capabilities geben an, ob Benutzer nur innerhalb gemeinsamer Gruppen gesucht werden können. Aktuelle OpenCloud-Versionen legen den eingeschränkten Zustand fest im Code fest. Die Prüfung bleibt erfasst, um Änderungen dieser Capability sichtbar zu machen.

**Bei einem abweichenden Ergebnis:** Derzeit gibt es keine konfigurierbare Einstellung für diesen Wert. Er beschreibt die OpenCloud-Implementierung.

## 5. Mindestlänge von Linkpasswörtern: `passwordPolicyEnforced` {#5-is-the-link-password-policy-strong-enough-passwordpolicyenforced}

Der Scanner vergleicht `password_policy.min_characters` mit `8`. Dies betrifft **Passwörter öffentlicher Freigabelinks**, nicht Kontopasswörter. Ob Links überhaupt ein Passwort benötigen, wird unter [Freigaben](../sharing.md) geprüft.

**Behebung:** Setze `OC_PASSWORD_POLICY_DISABLED=false` und `OC_PASSWORD_POLICY_MIN_CHARACTERS` auf mindestens `8`. Die [Linkpasswort-Richtlinie][link-password] beschreibt weitere Anforderungen und Sperrlisten.

## 5a. Zeichenanforderungen: `passwordPolicyComplexity` {#5a-does-it-still-ask-for-more-than-length-passwordpolicycomplexity}

OpenCloud verlangt standardmäßig mindestens einen Kleinbuchstaben, einen Großbuchstaben, eine Ziffer und ein Sonderzeichen. Die Prüfung liest die vier Mindestwerte und besteht, wenn jeder mindestens `1` ist.

Die Prüfung ergänzt die Mindestlängenprüfung, ohne deren bisherige Bedeutung zu verändern. Ein langes Passwort könnte die Längenprüfung bestehen, obwohl die konfigurierten Zeichenanforderungen abgesenkt wurden.

Die Prüfung erscheint nur, wenn alle vier Werte veröffentlicht werden. Eine deaktivierte Richtlinie wird durch `passwordPolicyEnforced` erfasst; fehlende Einzelwerte werden nicht als Fehler ausgelegt.

**Behebung:** Setze `OC_PASSWORD_POLICY_MIN_LOWERCASE_CHARACTERS`, `OC_PASSWORD_POLICY_MIN_UPPERCASE_CHARACTERS`, `OC_PASSWORD_POLICY_MIN_DIGITS` und `OC_PASSWORD_POLICY_MIN_SPECIAL_CHARACTERS` auf mindestens `1`.

## 6. Identitätsanbieter erkennen: `identityProviderDetected` {#6-can-the-identity-provider-be-found-at-all-identityproviderdetected}

Der Scanner ruft `/.well-known/openid-configuration` einmal ab, ohne Weiterleitungen zu folgen:

- Bei `200` mit JSON liest er `issuer`.
- Bei einer Weiterleitung wertet er `Location` relativ zur Instanz aus.
- Fehlt eine absolute HTTP(S)-URL mit Hostnamen, schlägt die Erkennung fehl.

Es werden weder Formulare ausgefüllt noch Zugangsdaten gesendet. Häufig verhindert ein Proxy die Weiterleitung von `/.well-known/`; eine fehlgeschlagene Erkennung begrenzt deshalb die Note nicht.

Liegt der Issuer auf einem anderen Host, wird der Anbieter als extern gekennzeichnet. Erkannte Produkte wie Keycloak, Authentik oder Authelia werden mit ihren Sicherheitshinweisen verknüpft. Weder ein externer noch der eingebaute Anbieter ist für sich genommen ein Befund.

**Behebung:** Prüfe die Weiterleitung von `/.well-known/` im [Reverse Proxy](../reverse-proxy.md) und die Konfiguration des tatsächlich verwendeten Anbieters.

## 7. Einstellungen im Discovery-Dokument {#7-what-the-discovery-document-says-about-how-sign-in-is-protected}

Vier weitere Prüfungen werten dieselbe Antwort aus und benötigen keine zusätzliche HTTP-Anfrage. Grundlage sind ausschließlich öffentlich veröffentlichte Angaben; siehe [ADR 0022](../../adr/0022-identity-provider-versions-require-public-evidence.md).

| Kennung | Feld | Fehlerbedingung |
|:--|:--|:--|
| `oidcPkceSupported` | `code_challenge_methods_supported` | `S256` fehlt unter den genannten Methoden |
| `oidcImplicitFlowDisabled` | `response_types_supported` | Ein Typ liefert `token` oder `id_token` vom Autorisierungsendpunkt |
| `oidcSigningAlgorithmStrong` | `id_token_signing_alg_values_supported` | Enthält `none` oder einen `HS`-Algorithmus |
| `oidcEndpointsUseHttps` | `issuer` und Endpunkt-URLs | Eine Adresse verwendet `http://` |

`code_challenge_methods_supported` stammt aus [OAuth 2.0 Authorization Server Metadata](https://www.rfc-editor.org/rfc/rfc8414.html#section-2). Ein reiner OIDC-Anbieter muss dieses Feld nicht veröffentlichen.

**Fehlende Felder werden nicht als Fehler bewertet.** Insbesondere veröffentlicht OpenClouds eingebauter Anbieter kein `code_challenge_methods_supported`; daraus lässt sich kein fehlender PKCE-Schutz ableiten.

**`oidcImplicitFlowDisabled` gilt nur für externe Anbieter.** Der eingebaute Anbieter [libregraph/lico][lico] bietet festgelegte implizite und hybride Antworttypen an, die sich nicht umkonfigurieren lassen. Bei externen Anbietern können die Flows dagegen eingeschränkt werden; siehe [Keycloak absichern](../secure-deployment.md#keycloak).

**`oidcEndpointsUseHttps` wird nur bei einer über HTTPS erreichten Instanz bewertet.** Bei einem HTTP-Scan erfasst bereits `httpsEnforced` das Transportproblem. Relevant ist hier eine HTTPS-Instanz, deren Anbieter weiterhin HTTP-Adressen veröffentlicht, etwa wegen einer falsch konfigurierten öffentlichen URL hinter einem Proxy.

`none` bezeichnet unsignierte ID-Tokens. `HS`-Verfahren verwenden ein gemeinsames Client-Geheimnis, das öffentliche OpenCloud-Clients nicht vertraulich halten können. Der eingebaute Anbieter verwendet `PS256` und besteht die Algorithmusprüfung.

## Weitere Discovery-Felder {#what-else-is-in-that-document-and-why-none-of-it-is-checked}

Folgende Felder werden nicht bewertet. Die Einordnung beruht auf `InitializeMetadata` in `oidc/provider/provider.go` von [libregraph/lico][lico]:

| Feld | Grund |
|:--|:--|
| `token_endpoint_auth_methods_supported` | `client_secret_basic` ist nicht allein problematisch; `none` wird von öffentlichen Clients benötigt. Lico bietet beides an. |
| `request_object_signing_alg_values_supported` | Betrifft Request-Objekte, nicht ID-Tokens. OpenCloud-Clients verwenden diese Objekte nicht. |
| `scopes_supported`, `claims_supported` | Beschreiben mögliche Anfragen, nicht die tatsächlich erteilten Berechtigungen eines Clients. |
| `subject_types_supported` | lico liefert `public`. `pairwise` ist eine Datenschutzfunktion für andere Einsatzmodelle und keine allgemeine Voraussetzung. |
| `registration_endpoint` | Ein vorhandener Endpunkt belegt keine offene Registrierung. Eine mögliche Tokenpflicht ist daraus nicht erkennbar. |

## Schweregrad und Bewertung {#severity-and-rating-impact}

`authentication:<path>` und `demoUsersDisabled` sind Zusatzprüfungen mit den oben genannten Schweregraden und begrenzen die Note bei einem Fehler. Die [Prüfübersicht](../scanner-checks.md#what-the-scanner-checks) enthält die Zuordnung.

`basicAuthDisabled`, `userEnumerationRestricted`, `passwordPolicyEnforced`, `passwordPolicyComplexity`, `identityProviderDetected` und die vier `oidc*`-Kennungen sind außerdem Härtungsangaben. Diese werden mit `--check-hardening` berücksichtigt und im Webbericht immer angezeigt. Ein fehlgeschlagener Härtungswert allein senkt die numerische Note nicht, kann aber einen sonst erfolgreichen Plugin-Status auf WARNING setzen. Nicht konfigurierbare Werte sind von dieser Alarmierung ausgenommen. Siehe [Härtungsprüfungen](../../README.md#hardening-checks).

[opencloud-demo-users]: https://docs.opencloud.eu/docs/admin/resources/demo-user/
[link-password]: https://docs.opencloud.eu/docs/admin/configuration/link-password-policy
[lico]: https://github.com/libregraph/lico

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
