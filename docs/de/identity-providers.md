# Externe Identitätsanbieter einrichten

Dieser Leitfaden beschreibt die Anmeldung an OpenCloud mit **Keycloak**, **Authentik** oder **Authelia**. Wähle einen Anbieter passend zu deiner vorhandenen Infrastruktur. [OpenCloud sicher betreiben](../secure-deployment.md#1-put-a-real-identity-provider-in-front) erklärt die Rolle eines externen Anmeldeanbieters im Gesamtkonzept.

Die Anmeldung ergänzt Firewall, Reverse Proxy, Audit-Log und Updates. Diese Maßnahmen bleiben auch mit einem externen Anbieter erforderlich.

## Voraussetzungen {#before-you-start}

Lege die öffentlichen Namen vor der Einrichtung fest. Spätere Änderungen am Issuer können bestehende Sitzungen und gespeicherte Client-Tokens ungültig machen.

| Name | Beispiel | Zweck |
|:--|:--|:--|
| Instanz | `opencloud.example.com` | OpenCloud-Adresse |
| Anbieter | `id.example.com` | Anmeldedienst |
| Realm oder Anwendung | `opencloud` | Interne Zuordnung beim Anbieter |

Du benötigst außerdem:

- Eine bereits funktionierende OpenCloud-Instanz über HTTPS.
- Von den beteiligten Clients vertraute Zertifikate für beide Namen.
- DNS-Auflösung beider Namen aus dem Container-Netz und aus den Client-Netzen.
- Einen getesteten Rückweg zur bisherigen Anmeldung. Halte während der Umstellung einen administrativen Zugang bereit und entferne `idp` erst nach erfolgreicher Prüfung aus dem Dienstsatz.

## Gemeinsame Anforderungen {#what-every-provider-has-to-produce}

Client-IDs, Redirect-URIs und Scopes richten sich nach den OpenCloud-Anwendungen. Du musst beim Anbieter und in OpenCloud zusammenpassen.

### Vier Clients registrieren {#the-four-clients}

| Client | Standard-ID | Redirect-URIs | Scopes |
|:--|:--|:--|:--|
| Web | `web` | `https://opencloud.example.com/`, `https://opencloud.example.com/oidc-callback.html`, `https://opencloud.example.com/oidc-silent-redirect.html` | `openid profile email groups` |
| Desktop | `OpenCloudDesktop` | `http://127.0.0.1`, `http://localhost` | `openid profile email groups offline_access` |
| Android | `OpenCloudAndroid` | `oc://android.opencloud.eu` | `openid profile email groups offline_access` |
| iOS | `OpenCloudIOS` | `oc://ios.opencloud.eu`, `oc.ios://ios.opencloud.eu` | `openid profile email groups offline_access` |

Der Webclient benötigt alle drei Redirect-URIs: den Einstieg, den Abschluss der Anmeldung und die stille Erneuerung der Sitzung. Fehlt `oidc-silent-redirect.html`, können Sitzungen nach zunächst erfolgreicher Anmeldung scheitern.

`offline_access` ist in diesen Beispielen für Desktop und Mobilgeräte vorgesehen, damit sie Refresh-Tokens erhalten. Der Webclient wird ohne diesen Scope eingerichtet.

Wenn du Client-IDs änderst, passe auch `WEBFINGER_WEB_OIDC_CLIENT_ID` und die entsprechenden `ANDROID`-, `IOS`- und `DESKTOP`-Variablen an. Sonst verwenden die Clients andere IDs als der Anbieter kennt.

### Öffentliche Clients mit PKCE {#why-they-are-all-public-clients}

Web-, Desktop- und Mobilclients laufen auf Geräten der Benutzer und können ein gemeinsames Client-Geheimnis nicht vertraulich halten. Registriere sie als **öffentliche Clients mit Authorization Code Flow und PKCE**. Verwende die Challenge-Methode `S256`. Ein statisch eingebautes Client-Secret bietet bei diesen Clients keinen verlässlichen Geheimnisschutz.

## OpenCloud konfigurieren {#what-opencloud-needs-whichever-provider-you-pick}

Sobald der Anbieter bereitsteht, setze die OpenCloud-Variablen. Die [OpenCloud-Anleitung für externe IdPs](https://docs.opencloud.eu/docs/admin/configuration/authentication-and-user-management/external-idp) ist die weiterführende Referenz:

```shell
# The provider, and turning the built-in one off.
OC_OIDC_ISSUER="https://id.example.com/realms/opencloud"
OC_EXCLUDE_RUN_SERVICES="idp"

# Verify tokens against the provider's published keys rather than asking it
# on every single request.
PROXY_OIDC_ACCESS_TOKEN_VERIFY_METHOD="jwt"
PROXY_OIDC_REWRITE_WELLKNOWN="true"

# Who a token belongs to, and the OpenCloud attribute it is matched against.
PROXY_USER_OIDC_CLAIM="preferred_username"
PROXY_USER_CS3_CLAIM="username"

# Create the account on first sign-in, and where its fields come from.
PROXY_AUTOPROVISION_ACCOUNTS="true"
PROXY_AUTOPROVISION_CLAIM_USERNAME="preferred_username"
PROXY_AUTOPROVISION_CLAIM_EMAIL="email"
PROXY_AUTOPROVISION_CLAIM_DISPLAYNAME="name"
PROXY_AUTOPROVISION_CLAIM_GROUPS="groups"

# Roles from a claim - and the default role switched off, or everybody gets
# that one as well.
PROXY_ROLE_ASSIGNMENT_DRIVER="oidc"
PROXY_ROLE_ASSIGNMENT_OIDC_CLAIM="roles"
GRAPH_ASSIGN_DEFAULT_USER_ROLE="false"

# The client IDs, published to OpenCloud's own clients through WebFinger.
WEBFINGER_WEB_OIDC_CLIENT_ID="web"
WEBFINGER_DESKTOP_OIDC_CLIENT_ID="OpenCloudDesktop"
WEBFINGER_ANDROID_OIDC_CLIENT_ID="OpenCloudAndroid"
WEBFINGER_IOS_OIDC_CLIENT_ID="OpenCloudIOS"
```

Prüfe besonders die Zugriffsentscheidungen:

- `PROXY_AUTOPROVISION_ACCOUNTS=true` erstellt bei der ersten Anmeldung ein Konto. Beschränke deshalb beim Anbieter, wer die OpenCloud-Anwendung verwenden darf, etwa über eine Gruppe.
- Bei `PROXY_ROLE_ASSIGNMENT_DRIVER=oidc` setze `GRAPH_ASSIGN_DEFAULT_USER_ROLE=false`, damit die automatische Standardrolle nicht zusätzlich vergeben wird.

Starte OpenCloud nach Änderungen neu. Insbesondere `OC_EXCLUDE_RUN_SERVICES` wird beim Start gelesen.

## Anleitung A: Keycloak {#tutorial-a-keycloak}

Keycloak eignet sich besonders, wenn bereits ein Realm, Benutzerföderation oder umfangreiche Rollenzuordnung vorhanden ist.

**1. Dienst starten:** Das Beispiel verwendet eine Datenbank und einen vorgeschalteten TLS-Proxy:

```yaml
services:
  keycloak:
    image: quay.io/keycloak/keycloak:latest
    command: ["start", "--optimized"]
    environment:
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://keycloak-db:5432/keycloak
      KC_DB_USERNAME: keycloak
      KC_DB_PASSWORD_FILE: /run/secrets/kc_db_password
      KC_HOSTNAME: https://id.example.com
      KC_PROXY_HEADERS: xforwarded
      KC_HTTP_ENABLED: "true"
      # Bootstrap only. Create a real administrator, then remove these two
      # and restart - they are a password in an environment variable.
      KC_BOOTSTRAP_ADMIN_USERNAME: admin
      KC_BOOTSTRAP_ADMIN_PASSWORD_FILE: /run/secrets/kc_bootstrap
    secrets: [kc_db_password, kc_bootstrap]
    depends_on: [keycloak-db]
```

`KC_PROXY_HEADERS: xforwarded` erlaubt Keycloak, die vom kontrollierten Proxy übergebene öffentliche Adresse zu berücksichtigen.

**2. Realm anlegen:** Öffne *Realms → Create realm* und erstellst du `opencloud`. Der Realm `master` bleibt der Keycloak-Verwaltung vorbehalten.

Der Issuer lautet dann:

```
https://id.example.com/realms/opencloud
```

**3. Vier Clients anlegen:** Verwende unter *Clients → Create client* die [oben aufgeführten Werte](#the-four-clients):

- **Client type:** OpenID Connect.
- **Client authentication:** aus, für öffentliche Clients.
- **Authentication flow:** Standard Flow. Deaktiviere Direct Access Grants und nicht benötigte Flows.
- **Valid redirect URIs:** die passenden Werte je Client. Der Desktop-Client benötigt Loopback-Weiterleitungen mit seinem zur Laufzeit gewählten Port; prüfe die vom Anbieter unterstützte Schreibweise für `http://127.0.0.1/*` und `http://localhost/*`.
- **Web origins:** `https://opencloud.example.com` für den Webclient.
- **Proof Key for Code Exchange Code Challenge Method:** unter *Advanced → Advanced settings* auf `S256` setzen.

**4. Claims zuordnen:** Unter *Client scopes → `<client>-dedicated` → Add mapper → By configuration*:

- Einen **Group Membership**-Mapper für `groups`, mit *Full group path* aus. Sonst wird beispielsweise `/finance` statt `finance` geliefert.
- Bei Rollenvergabe aus Keycloak einen **User Client Role**-Mapper für `roles`.

Stelle die Claims im Access-Token und in der Userinfo-Antwort bereit. Ein Claim nur im ID-Token genügt für diese Zuordnung nicht.

**5. Zweiten Faktor verlangen:** aktiviere *Configure OTP* unter *Authentication → Required actions* und verwende einen Browser-Flow, der den zweiten Faktor tatsächlich verlangt. Teste auch die erste Einrichtung eines Faktors.

**6. OpenCloud umstellen:** Setze die oben beschriebenen Variablen und starte die Instanz neu.

## Anleitung B: Authentik {#tutorial-b-authentik}

Authentik eignet sich für mehrere Anwendungen mit eigenen Gruppen- und Zugriffsregeln sowie für eine dateibasierte Bereitstellung über Blueprints.

Die Authentik-Konfiguration dieses Repositorys schützt den [MCP-Endpunkt des Scan-Dienstes](../authentik.md) und dessen Betreiberbereich. Sie konfiguriert nicht automatisch die Anmeldung deiner OpenCloud-Instanz. Die [Blueprints](../../authentik/blueprints) können jedoch als Beispiel dienen.

**1. Dienst installieren:** Folge der [Authentik-Installationsanleitung](https://docs.goauthentik.io/install-config/install/docker-compose). Stelle sicher, dass `https://id.example.com` aus allen beteiligten Netzen mit vertrauenswürdigem Zertifikat erreichbar ist.

**2. Gruppen-Mapping anlegen:** Unter *Customisation → Property mappings → Create → Scope mapping*:

- **Name:** `OpenCloud groups`
- **Scope name:** `groups`
- **Expression:**

  ```python
  return {"groups": [group.name for group in request.user.ak_groups.all()]}
  ```

Mappings für `openid`, `profile` und `email` sind bereits vorhanden. Ergänze das Gruppen-Mapping für die OpenCloud-Zuordnung.

**3. Vier Provider anlegen:** Unter *Applications → Providers → Create → OAuth2/OpenID Provider* registriere die Clients aus der [Tabelle](#the-four-clients):

- **Client type:** Public, mit PKCE.
- **Client ID und Redirect URIs:** passend zur Anwendung.
- Verwende beim Einsatz regulärer Ausdrücke exakt begrenzte Redirect-Muster, etwa `http://127\.0\.0\.1(:[0-9]+)?` für den Loopback-Eingang, und beachte den gewählten URI-Abgleichmodus.
- **Scopes:** die Standard-Mappings und `OpenCloud groups`, für native Clients zusätzlich die benötigte Offline-Berechtigung.
- **Signing key:** ein konfigurierter Signaturschlüssel.
- **Authorization flow:** für eine vertrauenswürdige interne Anwendung beispielsweise `implicit consent`.

**4. Anwendung und Gruppe zuordnen:** Erstelle unter *Applications → Applications → Create* die Anwendung `opencloud` mit dem Webprovider. Beschränke sie unter *Policies / Group / User bindings* auf die vorgesehene Gruppe. Prüfe die entsprechende Zugriffsregel auch für die übrigen Clients.

Diese Zuordnung bestimmt, wer bei aktiviertem Autoprovisioning ein OpenCloud-Konto erhält.

**5. Issuer übernehmen:** Lies den tatsächlichen Wert am Provider ab:

```
https://id.example.com/application/o/opencloud/
```

Der abschließende Schrägstrich gehört zum Issuer und muss in OpenCloud identisch stehen.

**6. OpenCloud umstellen:** Setze die gemeinsamen Variablen und starte neu.

## Anleitung C: Authelia {#tutorial-c-authelia}

Authelia lässt sich über eine Konfigurationsdatei einrichten und passt häufig zu einer bereits vorhandenen Proxy-Authentifizierung.

**1. Dienst und Sitzungsspeicher starten:**

```yaml
services:
  authelia:
    image: ghcr.io/authelia/authelia:latest
    volumes:
      - ./authelia:/config
    environment:
      AUTHELIA_IDENTITY_PROVIDERS_OIDC_HMAC_SECRET_FILE: /run/secrets/oidc_hmac
      AUTHELIA_IDENTITY_PROVIDERS_OIDC_ISSUER_PRIVATE_KEY_FILE: /run/secrets/oidc_key
    secrets: [oidc_hmac, oidc_key]
```

Erzeuge die benötigten Geheimnisse vor dem ersten Start:

```shell
docker run --rm ghcr.io/authelia/authelia:latest \
    authelia crypto rand --length 64 --charset alphanumeric
docker run --rm -v "$PWD/authelia:/keys" ghcr.io/authelia/authelia:latest \
    authelia crypto pair rsa generate --bits 4096 --directory /keys
```

**2. Clients registrieren:** Lege unter `identity_providers.oidc.clients` in `configuration.yml` alle vier Clients an. Das Beispiel zeigt den Webclient; passt du für die übrigen IDs, Redirects und Scopes an:

```yaml
identity_providers:
  oidc:
    clients:
      - client_id: 'web'
        client_name: 'OpenCloud'
        public: true
        authorization_policy: 'two_factor'
        require_pkce: true
        pkce_challenge_method: 'S256'
        token_endpoint_auth_method: 'none'
        scopes: ['openid', 'profile', 'email', 'groups']
        redirect_uris:
          - 'https://opencloud.example.com/'
          - 'https://opencloud.example.com/oidc-callback.html'
          - 'https://opencloud.example.com/oidc-silent-redirect.html'
        response_types: ['code']
        grant_types: ['authorization_code']

      - client_id: 'OpenCloudDesktop'
        client_name: 'OpenCloud Desktop'
        public: true
        authorization_policy: 'two_factor'
        require_pkce: true
        pkce_challenge_method: 'S256'
        token_endpoint_auth_method: 'none'
        scopes: ['openid', 'profile', 'email', 'groups', 'offline_access']
        redirect_uris: ['http://127.0.0.1', 'http://localhost']
        response_types: ['code']
        grant_types: ['authorization_code', 'refresh_token']

      - client_id: 'OpenCloudAndroid'
        client_name: 'OpenCloud Android'
        public: true
        authorization_policy: 'two_factor'
        require_pkce: true
        pkce_challenge_method: 'S256'
        token_endpoint_auth_method: 'none'
        scopes: ['openid', 'profile', 'email', 'groups', 'offline_access']
        redirect_uris: ['oc://android.opencloud.eu']
        response_types: ['code']
        grant_types: ['authorization_code', 'refresh_token']

      - client_id: 'OpenCloudIOS'
        client_name: 'OpenCloud iOS'
        public: true
        authorization_policy: 'two_factor'
        require_pkce: true
        pkce_challenge_method: 'S256'
        token_endpoint_auth_method: 'none'
        scopes: ['openid', 'profile', 'email', 'groups', 'offline_access']
        redirect_uris: ['oc://ios.opencloud.eu', 'oc.ios://ios.opencloud.eu']
        response_types: ['code']
        grant_types: ['authorization_code', 'refresh_token']
```

`authorization_policy: 'two_factor'` verlangt den zweiten Faktor für den jeweiligen Client.

**3. Zugriffsregel ergänzen:** Wenn der Reverse Proxy auch Forward Auth verwendet, muss die passende Regel für die Instanz gelten:

```yaml
access_control:
  default_policy: 'deny'
  rules:
    - domain: 'opencloud.example.com'
      policy: 'two_factor'
```

**4. Issuer übernehmen:** Bei dieser Konfiguration ist es die Basisadresse ohne Pfad und ohne abschließenden Schrägstrich:

```
https://id.example.com
```

**5. OpenCloud umstellen:** Setze die gemeinsamen Variablen und starte neu.

## Einrichtung prüfen {#verifying-it-actually-worked}

**1. Discovery-Dokument abrufen:**

```shell
curl -fsS https://id.example.com/.well-known/openid-configuration | \
    python3 -m json.tool | head -20
```

`issuer` muss exakt mit `OC_OIDC_ISSUER` übereinstimmen, einschließlich eines abschließenden Schrägstrichs.

**2. OpenCloud-Zuordnung prüfen:** Bei `PROXY_OIDC_REWRITE_WELLKNOWN=true` sollte die Abfrage über OpenCloud auf den konfigurierten Anbieter verweisen:

```shell
curl -fsS https://opencloud.example.com/.well-known/openid-configuration | \
    python3 -c 'import json,sys; print(json.load(sys.stdin)["issuer"])'
```

Erscheint weiterhin der eingebaute Anbieter, prüfe die wirksame Konfiguration, `OC_EXCLUDE_RUN_SERVICES` und den Neustart.

**3. Anmeldung testen:** Verwende ein privates Browserfenster. Prüfe Kontoanlage, Gruppen, Rollen und den verpflichtenden zweiten Faktor. Teste auch einen Benutzer, der keinen Zugriff erhalten soll.

**4. Scan ausführen:**

```shell
check-opencloud-security --host opencloud.example.com --check-hardening --debug
```

Prüfe `identityProviderDetected` und die vier `oidc*`-Angaben, soweit sie aus dem öffentlich erreichbaren Dokument ermittelt werden konnten. [Authentifizierung](../authentication.md) erklärt die einzelnen Befunde. Ein Scan kann weder eine korrekte Gruppenzuordnung noch die tatsächliche Durchsetzung des zweiten Faktors bestätigen; dafür ist der Anmeldungstest erforderlich.

## Bestehende Konten migrieren {#moving-an-instance-that-already-has-accounts}

Bei einer Umstellung müssen die Identitäten des Anbieters den vorhandenen OpenCloud-Konten zugeordnet werden. `PROXY_USER_OIDC_CLAIM` und `PROXY_USER_CS3_CLAIM` bestimmen diese Zuordnung. Stimmen beispielsweise `preferred_username` und `username` nicht überein, kann Autoprovisioning ein zweites, leeres Konto anlegen.

1. Exportiere die vorhandenen Benutzernamen und gleiche sie vorab mit dem Anbieter ab.
2. Bereite den externen Anbieter vor und halte den bisherigen Anmeldeweg als Rückfall bereit.
3. Teste ein vorhandenes Konto und prüfe, dass es seinen bisherigen Speicherbereich erreicht.
4. Nimm den eingebauten `idp` erst nach erfolgreicher Prüfung über `OC_EXCLUDE_RUN_SERVICES` außer Betrieb und starte neu.
5. Lass `PROXY_ENABLE_BASIC_AUTH=false`, wenn kein Client es benötigt. Für notwendige WebDAV-, CalDAV- oder Backup-Zugriffe verwende App-Tokens; siehe [Basic Auth](../secure-deployment.md#basic-authentication-is-the-hole-in-all-of-this).

## Fehlersuche {#troubleshooting}

| Symptom | Mögliche Ursache |
|:--|:--|
| `invalid issuer` oder Tokenfehler | `OC_OIDC_ISSUER` weicht vom veröffentlichten Wert ab, etwa beim Schrägstrich |
| Browser funktioniert, Desktop-Anmeldung hängt | DNS aus dem Container-Netz oder Loopback-Redirect fehlerhaft |
| Anmeldung funktioniert nur bis zur Erneuerung | `oidc-silent-redirect.html` fehlt |
| Desktop bleibt nach Neustart nicht angemeldet | `offline_access` oder Refresh-Token-Konfiguration fehlt |
| Zu viele Berechtigungen | Automatische Standardrolle trotz Rollen-Claim aktiv |
| Zweites leeres Konto | Claim-Zuordnung stimmt nicht mit bestehendem Benutzerattribut überein |
| Gruppen passen nicht | Keycloak liefert vollständige Pfade wie `/finance` |
| Unberechtigte Benutzer erhalten Konten | Autoprovisioning ohne passende Anwendungsbeschränkung |
| Eingebauter Anbieter weiterhin erkannt | Dienstkonfiguration oder Neustart nicht wirksam |

## Weitere Anleitungen {#where-to-go-next}

| Seite | Inhalt |
|:--|:--|
| [Sicherer Betrieb](../secure-deployment.md) | Audit-Log, Firewall und weitere Schutzmaßnahmen |
| [Authentifizierung](../authentication.md) | Prüfungen des Scanners |
| [Reverse Proxys](../reverse-proxy.md) | TLS und Weiterleitungsheader |
| [TLS](../tls.md) | Zertifikate und Transportprüfungen |
| [Authentik für MCP](../authentik.md) | Anmeldung am Scan-Dienst |
| [Härtungsmaßnahmen](../hardening.md) | Bedeutung und Behandlung der Befunde |

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
