# Den MCP-Endpunkt des OpenCloud Security Scanners mit Authentik schützen

Dieser Leitfaden richtet den Scan-Webdienst zusammen mit
[Authentik](https://goauthentik.io) ein. Der MCP-Endpunkt `/mcp` verlangt damit
von Beginn an ein gültiges Zugriffstoken. Website und HTTP-API bleiben öffentlich.

Die Anmeldung beschränkt den Zugang zu MCP. Rate Limits, Ziel-Cooldown,
SSRF-Schutz und Warteschlange gelten für angemeldete Agenten genauso wie für
andere Aufrufer.

## So funktioniert die Anmeldung {#how-it-works}

Der Scan-Webdienst prüft Tokens als OAuth-2.0-Resource-Server. Er verwaltet keine
Benutzerkonten, Anmeldesitzungen oder Client-Geheimnisse und stellt keine Tokens aus.

1. Der Agent sendet `Authorization: Bearer <token>`.
2. Der Dienst prüft die Signatur mit den veröffentlichten Schlüsseln des
   Providers (JWKS).
3. Issuer, Audience, Ablaufdatum und gegebenenfalls geforderte Scopes müssen passen.
4. Eine fehlgeschlagene Prüfung führt zu **401**.

Tokens werden weder gespeichert noch protokolliert. Die Signaturschlüssel
werden zwischengespeichert und bei Rotation nachgeladen; es erfolgt keine
Provider-Anfrage für jedes Token.

Ohne Token verweist der `WWW-Authenticate`-Header gemäß RFC 9728 auf
`/.well-known/oauth-protected-resource/mcp`. Dieses öffentliche Dokument nennt
den Autorisierungsserver. Die gleichen Angaben stehen unter `/.well-known/ai.json`.

## Den Stack starten {#running-the-stack}

`docker/docker-compose.authentik.yml` enthält den vollständigen Stack:
Webanwendung, Scan-Worker, Redis, Authentik-Server, PostgreSQL und
Authentik-Worker. Starte ihn mit:

```bash
cd docker
./authentik-env.sh                                  # writes .env, once
docker compose -f docker-compose.authentik.yml up -d
```

Öffne anschließend **<http://127.0.0.1:9000/if/flow/initial-setup/>** und
setze das Passwort für `akadmin`. Der abschließende Schrägstrich ist
notwendig. Dieser Einrichtungsablauf steht nur einmal zur Verfügung.
Bei der ersten Anmeldung wird zusätzlich ein zweiter Faktor eingerichtet.

Die Compose-Datei koppelt `COS_WEB_MCP_AUTH_ENABLED` an
`${COS_WEB_ENABLE_MCP:-true}`. Solange MCP in diesem Stack aktiv ist, verlangt
es damit eine Anmeldung. Provider und Anwendung legt ein Blueprint an.

`authentik-env.sh` erzeugt folgende Werte in `docker/.env`, ohne bereits
vorhandene zu überschreiben:

| Variable | Zweck |
|:--|:--|
| `COS_REDIS_PASSWORD` | Passwort für den Redis-Speicher des Scanners |
| `AUTHENTIK_SECRET_KEY` | Kryptografischer Schlüssel der Authentik-Installation |
| `AUTHENTIK_PG_PASS` | PostgreSQL-Passwort |
| `AUTHENTIK_CLIENT_ID` | OAuth-Client-ID und erwartete Audience |
| `AUTHENTIK_CLIENT_SECRET` | OAuth-Client-Geheimnis |
| `COS_WEB_PURGE_TOKEN` | Separater Berechtigungsnachweis zum Löschen von Scandaten |

Sichere diese Datei zusammen mit den Authentik-Daten. Insbesondere muss
`AUTHENTIK_SECRET_KEY` bei einer Wiederherstellung erhalten bleiben.
Für einen über den eigenen Rechner hinaus erreichbaren Dienst setze:

```bash
AUTHENTIK_URL=https://sso.example.com \
COS_WEB_PUBLIC_BASE_URL=https://scanner.example.com \
  docker compose -f docker-compose.authentik.yml up -d
```

Die separate Compose-Datei verhindert, dass die verpflichtenden
Authentik-Variablen auch beim normalen Stack verlangt werden. Compose prüft
solche Variablen in jeder eingelesenen Datei, selbst bei nicht gewählten Profilen.

Hinweise zum Aufbau:

- Authentik verwendet in der hier eingesetzten Version PostgreSQL für seine
  Sitzungen, Caches und Aufgaben. Der Scanner nutzt einen eigenen Redis.
- PostgreSQL ist auf ein Image festgelegt. Authentik verwendet sein
  Debian-basiertes Image; ein Alpine-Image ist hier nicht vorgesehen.
- Der Worker erhält keinen Docker-Socket. Automatisch verwaltete Outpost-Container
  werden in diesem Stack nicht benötigt.
- Daten liegen in den benannten Volumes `authentik_database`, `authentik_media`,
  `authentik_templates` und `authentik_certs`.
- Belasse die interne Zeitzone bei UTC und binde keine lokale
  `/etc/localtime` oder `/etc/timezone` ein.

## E-Mail-Versand einrichten {#sending-mail}

Richte SMTP ein, damit Passwort-Wiederherstellungslinks zugestellt werden
können. Ohne externen Mailserver bleibt die lokale Zustellung im Container.
Server und Worker müssen dieselben Einstellungen erhalten: Der Server sendet
Testnachrichten, der Worker die übrigen Nachrichten.

| Variable | Standard | Bedeutung |
|:--|:--|:--|
| `AUTHENTIK_EMAIL_HOST` | leer | SMTP-Server; leer bedeutet lokale Zustellung |
| `AUTHENTIK_EMAIL_PORT` | `587` | Üblicherweise 587 für STARTTLS, 465 für implizites TLS |
| `AUTHENTIK_EMAIL_USERNAME` | leer | SMTP-Benutzername, falls erforderlich |
| `AUTHENTIK_EMAIL_PASSWORD` | leer | SMTP-Passwort |
| `AUTHENTIK_EMAIL_USE_TLS` | `true` | Verbindung mit STARTTLS absichern |
| `AUTHENTIK_EMAIL_USE_SSL` | `false` | TLS ab Verbindungsaufbau |
| `AUTHENTIK_EMAIL_TIMEOUT` | `10` | Wartezeit in Sekunden |
| `AUTHENTIK_EMAIL_FROM` | `authentik@localhost` | Absenderadresse |

Aktiviere `USE_TLS` und `USE_SSL` nicht gleichzeitig. Wähle die
Variante, die Ihr Mailserver unterstützt:

```bash
cat >> docker/.env <<'EOF'
AUTHENTIK_EMAIL_HOST=smtp.example.com
AUTHENTIK_EMAIL_PORT=587
AUTHENTIK_EMAIL_USERNAME=authentik@example.com
AUTHENTIK_EMAIL_PASSWORD=the-password
AUTHENTIK_EMAIL_USE_TLS=true
AUTHENTIK_EMAIL_USE_SSL=false
AUTHENTIK_EMAIL_FROM=authentik@example.com
EOF
docker compose -f docker-compose.authentik.yml up -d
```

`authentik-env.sh` hinterlegt die Namen auskommentiert in `.env` und erhält
bereits gesetzte Werte. Sende unter **System → Settings → Email** eine
Testnachricht und prüfe anschließend auch das Worker-Log:

```bash
docker compose -f docker-compose.authentik.yml logs -f authentik_worker
```

Der Setup-Assistent fragt diese Angaben ebenfalls ab. Das Passwort liest er
aus `AUTHENTIK_EMAIL_PASSWORD`, damit es nicht als Kommandozeilenargument in
Prozessliste oder Shell-Verlauf erscheint.

## Was der Blueprint anlegt {#what-the-blueprint-created}

`authentik/blueprints/opencloud-scanner.yaml` wird unter `/blueprints/custom`
eingebunden und vom Worker angewendet. Seine Einträge verwenden `state: created`:
Fehlende Objekte werden angelegt; spätere manuelle Änderungen bleiben erhalten.

| Objekt oder Einstellung | Wert |
|:--|:--|
| Anwendung | `OpenCloud security scanner`, Slug `opencloud-scanner` |
| Provider | `check-opencloud-security`, OAuth2/OpenID Connect, confidential |
| Client-ID und Geheimnis | `AUTHENTIK_CLIENT_ID` und `AUTHENTIK_CLIENT_SECRET` |
| Grants | `authorization_code`, `refresh_token`, `client_credentials` |
| Signaturschlüssel | `authentik Self-signed Certificate` |
| Scopes | `openid`, `profile`, `email`, `offline_access` |
| Issuer-Modus | je Provider |

Der **Signaturschlüssel** ist erforderlich. Ohne ihn signiert Authentik mit dem
Client-Geheimnis (HS256); der Scan-Webdienst akzeptiert nur asymmetrisch
signierte Tokens. Die **Client-ID** ist zugleich die Audience und wird auf der
Scanner-Seite als `COS_WEB_MCP_AUTH_AUDIENCE` eingelesen.

| Endpunkt | Beispiel |
|:--|:--|
| Issuer | `https://sso.example.com/application/o/opencloud-scanner/` |
| Discovery | `https://sso.example.com/application/o/opencloud-scanner/.well-known/openid-configuration` |
| JWKS | `https://sso.example.com/application/o/opencloud-scanner/jwks/` |
| Token | `https://sso.example.com/application/o/token/` |

Der Token-Endpunkt wählt die Anwendung anhand von `client_id`; Discovery und
JWKS verwenden den Anwendungs-Slug. Übernimm den Issuer aus der Discovery,
damit er mit dem Wert in den Tokens übereinstimmt.

Ein fehlerhafter Blueprint verhindert den Authentik-Start nicht. Prüfe bei
abgewiesenen Tokens auf einem neuen Stack zuerst **Customisation → Blueprints**.
Bei einem bestehenden Authentik kannst du dieselben Werte über
**Applications → Applications → Create with wizard** einrichten.

## Zweiter Faktor für alle Benutzer {#a-second-factor-for-everybody}

`opencloud-mfa.yaml` ändert die vorhandene Stufe
`default-authentication-mfa-validation`: Konten ohne zweiten Faktor müssen
nun einen einrichten, statt diese Prüfung zu überspringen.

| Einstellung | Verhalten |
|:--|:--|
| Konto ohne zweiten Faktor | Einrichtung vor Abschluss der Anmeldung |
| Angebotene Verfahren | TOTP-App und WebAuthn-Sicherheitsschlüssel oder Passkey |
| Später akzeptiert | TOTP, WebAuthn und selbst erzeugte Wiederherstellungscodes |
| Erneute Anwendung | Stündlich durch `state: present` |

### Ablauf für Benutzer {#what-the-person-sees}

1. Nach dem Passwort erscheint bei der ersten Anmeldung *Configure an authenticator*.
2. Für TOTP: QR-Code mit einer Authenticator-App scannen und den angezeigten
   sechsstelligen Code bestätigen.
3. Für WebAuthn: Sicherheitsschlüssel oder Passkey im Browser registrieren.
4. Spätere Anmeldungen verlangen nach dem Passwort den eingerichteten Faktor.
5. Unter **Settings → MFA Devices → Enroll → Static tokens** lassen sich
   Wiederherstellungscodes erzeugen. Bewahre diese getrennt vom Gerät auf.

Mehrere Faktoren sind möglich. Ein zusätzliches Gerät erleichtert den Zugang,
wenn das erste verloren geht.

### Durchsetzung und Wiederherstellung {#how-it-is-enforced}

Der Blueprint ändert die vorhandene Stufe, sodass Benutzer nicht zweimal nach
einem Faktor gefragt werden. Zum Aufheben der Vorgabe entferne zunächst
die Blueprint-Datei und ändern danach die bestehende Stufeneinstellung.

`client_credentials` verwendet keinen interaktiven Anmeldeablauf; Servicekonten
benötigen daher keinen TOTP-Code. Verlorene Faktoren kann ein Administrator
unter **Directory → Users → MFA Authenticators** entfernen. Bei der nächsten
Anmeldung muss der Benutzer einen neuen Faktor einrichten.

## Konten über eine Einladung einrichten {#accounts-without-the-admin-interface}

`docker/setup-wizard.py` fragt die zugelassenen Benutzernamen ab. Namen aus
`COS_WEB_ADMIN_USERS` werden automatisch aufgenommen. Der Assistent schreibt:

| Ziel | Inhalt |
|:--|:--|
| `.env` | `AUTHENTIK_ENROLLMENT_TOKEN` und `AUTHENTIK_BOOTSTRAP_PASSWORD` |
| Compose-Datei | `COS_AUTHENTIK_ACCOUNTS` und `COS_WEB_ADMIN_USERS` für beide Authentik-Container |
| Blueprint-Verzeichnis | Enrollment- und MFA-Blueprint neben den Provider-Blueprints |

Er zeigt anschließend eine Einladungsadresse mit Platzhalter:

```
https://sso.example.com/if/flow/opencloud-scanner-enrollment/?itoken=<AUTHENTIK_ENROLLMENT_TOKEN>
```

Der enthaltene Token ist ein Geheimnis. Die vollständige Adresse erzeuge
mit dem ausgegebenen Befehl aus `.env`:

```
echo "https://sso.example.com/if/flow/opencloud-scanner-enrollment/?itoken=$(sed -n 's/^AUTHENTIK_ENROLLMENT_TOKEN=//p' .env)"
```

Die eingeladenen Personen geben Benutzername, E-Mail und Passwort ein und
richten einen zweiten Faktor ein. Namen aus der Operator-Liste werden dabei
der Gruppe `opencloud-scanner-operators` zugeordnet.

Die Einladung ist dreifach begrenzt:

- Nur Namen aus `COS_AUTHENTIK_ACCOUNTS` sind zugelassen; eine leere Liste lässt
  niemanden zu.
- Ein bereits vorhandener Benutzername kann nicht erneut registriert werden.
- Ohne den passenden Token wird der Ablauf vor dem Formular abgewiesen.

Behandle die Adresse bis zur abgeschlossenen Registrierung aller Personen
wie ein Passwort. Neue Namen ergänze durch erneutes Ausführen des
Assistenten. Zum Ungültigmachen der Adresse ersetze
`AUTHENTIK_ENROLLMENT_TOKEN` durch eine neue UUID und starten Authentik neu.
Wer nach dem Passwort, aber vor dem zweiten Faktor abbricht, hat bereits ein
Konto und setzt die Einrichtung bei der normalen Anmeldung fort.

`akadmin` bleibt für Wiederherstellungsaufgaben erhalten.
`AUTHENTIK_BOOTSTRAP_PASSWORD` setzt sein Passwort nur beim ersten Start einer
neuen Datenbank und schließt damit den initialen Einrichtungsablauf. Auf
vorhandene Konten hat die Variable keine Wirkung.

Beim manuell gestarteten `docker-compose.authentik.yml` ist ohne Enrollment-Token
keine Einladung aktiv. Lege Konten dann wie unter
[Zugang zu MCP vergeben](#adding-somebody-who-may-use-the-endpoint) beschrieben an.
`--non-interactive` gibt keinen Link aus; Bilde ihn aus öffentlicher
Authentik-Adresse und Token entsprechend dem Kommentar in der Compose-Datei.

## Operator-Zugang zu /admin {#an-operator-for-admin}

Für den Operator-Bereich müssen zwei Freigaben zusammenpassen:

| Stelle | Erforderliche Freigabe |
|:--|:--|
| Authentik | Mitgliedschaft in `opencloud-scanner-operators` für die gebundene Anwendung |
| Scan-Webdienst | Derselbe Benutzername in `COS_WEB_ADMIN_USERS` |

### Mit dem Assistenten {#with-the-wizard}

Aktiviere im Setup-Assistenten den Operator-Bereich und trage unter
`admin_users` den gewünschten Benutzernamen ein. Die Liste der anzulegenden
Authentik-Konten enthält ihn automatisch.

Starte den Stack und erzeuge den Einladungslink aus `.env`.
Die Person registriert den exakt angegebenen Namen, wählt ein Passwort und
richtet einen zweiten Faktor ein. Danach ist der Zugang zu
`https://scan.example.com/admin` möglich.

Für weitere Operatoren führe den Assistenten im selben Verzeichnis erneut
aus, ergänzen die Liste, starten die betroffenen Container mit den neuen
Einstellungen und vergeben die Einladung.

### Manuell in Authentik {#by-hand-in-the-authentik-interface}

Diese Variante eignet sich für vorhandene Konten oder eine bestehende
Authentik-Installation.

**1. Als `akadmin` anmelden.** Das Bootstrap-Passwort aus `.env` gilt nur, wenn
diese Datei bei der ersten Datenbankinitialisierung verwendet wurde. Für einen
zeitlich begrenzten Wiederherstellungszugang:

```bash
docker compose exec authentik_worker ak create_recovery_key 10 akadmin
```

Öffne den ausgegebenen Pfad an der öffentlichen Authentik-Adresse innerhalb
von zehn Minuten und setze ein Passwort. Auch `akadmin` muss einen zweiten
Faktor einrichten.

**2. Konto anlegen.** Unter **Directory → Users → New User → Internal User**
trage den Namen exakt wie in `COS_WEB_ADMIN_USERS` ein. Eine E-Mail-Adresse
erlaubt die Passwort-Wiederherstellung.

**3. Passwort vergeben lassen.** Verwende **Email recovery link** oder
**Create recovery link**; alternativ steht **Set password** zur Verfügung.

**4. Gruppe zuweisen.** Unter **Groups → Add to existing group** wähle
`opencloud-scanner-operators`. Authentik-Superuserrechte sind dafür nicht nötig.

**5. Anmeldung prüfen.** Die Person öffnet `/admin`, meldet sich bei Authentik
an, richtet den zweiten Faktor ein und kehrt zum Scan-Webdienst zurück.

Konto und Gruppenzuordnung lassen sich auch über die Shell anlegen. Kopiere jeden Befehl als einzelne Zeile, da `ak shell -c` die Zeichenfolge als
Python-Skript ausführt:

```bash
# Create the account with no usable password; hand them a recovery link after.
docker compose exec authentik_worker ak shell -c "from authentik.core.models import User; u = User(username='scanokko', email='scanokko@example.com', name='scanokko'); u.set_unusable_password(); u.save(); print('CREATED')" 2>&1 | grep -E 'CREATED|Error'
docker compose exec authentik_worker ak create_recovery_key 60 scanokko

# Put it in the operator group.
docker compose exec authentik_worker ak shell -c "from authentik.core.models import Group, User; Group.objects.get(name='opencloud-scanner-operators').users.add(User.objects.get(username='scanokko')); print('ADDED')" 2>&1 | grep -E 'ADDED|Error|DoesNotExist'
```

Der zeitlich begrenzte Link aus `create_recovery_key` erlaubt der Person, selbst
ein Passwort zu setzen.

### Zugang kontrollieren {#checking-it}

Prüfe die Gruppenzuordnung:

```bash
docker compose exec authentik_worker ak shell -c "from authentik.core.models import Group; g = Group.objects.get(name='opencloud-scanner-operators'); print('IN_GROUP', g.users.filter(username='scanokko').exists())" 2>&1 | grep -E 'IN_GROUP|Error|DoesNotExist'
```

Teste auch ein Konto außerhalb der Gruppe: Authentik muss dessen Zugang
ablehnen. Unter **Events → Logs** stehen Konto und betroffene Anwendung.

## Den Webdienst mit dem Provider verbinden {#pointing-the-scanner-at-it}

Der mitgelieferte Authentik-Stack setzt diese Werte bereits. Für einen eigenen
Provider konfiguriere `web_app` entsprechend:

```yaml
COS_WEB_PUBLIC_BASE_URL: "https://scanner.example.com"
COS_WEB_MCP_AUTH_ENABLED: "true"
COS_WEB_MCP_AUTH_ISSUER: "https://sso.example.com/application/o/opencloud-scanner/"
COS_WEB_MCP_AUTH_AUDIENCE: "<the provider's client ID>"
```

| Einstellung | Bedeutung |
|:--|:--|
| `COS_WEB_MCP_AUTH_ENABLED` | Token für `/mcp` verlangen; standardmäßig aus |
| `COS_WEB_MCP_AUTH_ISSUER` | Issuer aus der Discovery; abschließender Schrägstrich wird toleriert |
| `COS_WEB_MCP_AUTH_AUDIENCE` | Erwarteter Wert in `aud`; bei Authentik die Client-ID; bei aktiver Anmeldung erforderlich |
| `COS_WEB_MCP_AUTH_JWKS_URL` | Abweichende Schlüsseladresse statt `<issuer>/jwks/` |
| `COS_WEB_MCP_AUTH_RESOURCE_URL` | Abweichende MCP-Adresse statt `<public base URL>/mcp` |
| `COS_WEB_MCP_AUTH_SCOPES` | Erforderliche Scopes, durch `;` getrennt; leer bedeutet keine zusätzliche Scope-Vorgabe |

Bei aktiver Anmeldung verweigert der Dienst den Start, wenn Issuer oder Audience
fehlen, keine öffentliche Basis- oder Resource-URL vorliegt oder die
Resource-URL außerhalb von Loopback unverschlüsseltes HTTP verwendet.
Ein ausgeschalteter MCP-Endpunkt darf dagegen auch bei aktivierter
Authentifizierung ausgeschaltet bleiben.

Die Audience verhindert, dass Tokens für andere Anwendungen desselben
Providers hier akzeptiert werden. Deshalb sind sowohl eine leere
`COS_WEB_MCP_AUTH_AUDIENCE` als auch Tokens ohne passendes `aud` unzulässig.

## Zugang zu MCP vergeben {#adding-somebody-who-may-use-the-endpoint}

Eine Authentik-Anwendung ohne Bindungen steht grundsätzlich allen Konten dieser
Installation offen. Beschränke sie vor der allgemeinen Nutzung auf eine
Gruppe. Der Scan-Webdienst prüft keine Benutzernamen oder Gruppenclaims; die
Entscheidung, wer ein Token erhält, liegt beim Provider.

### Gruppe und Anwendungsbindung {#a-group-and-the-binding-that-makes-it-mean-something}

1. Unter **Directory → Groups → Create** lege `opencloud-scanner` ohne
   Superuserrechte an.
2. Öffne **Applications → Applications → OpenCloud security scanner →
   Policy / Group / User Bindings → Bind existing Group/User**.
3. Wähle die Gruppe und den Policy-Modus **any**.

Prüfe mit einem Konto außerhalb der Gruppe, dass keine Autorisierung
möglich ist. Fehlgeschlagene Versuche erscheinen unter **Events → Logs**.

### Benutzerkonten {#the-person}

Lege ein internes Konto mit Benutzername und E-Mail an. Lass die
Person das Passwort per Wiederherstellungslink setzen und nimm das Konto
in `opencloud-scanner` auf. Ein MCP-Client mit OAuth-Unterstützung führt die
Anmeldung anschließend im Browser durch. Der zweite Faktor wird beim ersten
Anmelden eingerichtet.

### Servicekonten für automatisierte Aufrufe {#the-agent-that-is-nobody}

Für Cronjobs, CI und Server-Agenten lege unter **Directory → Users →
New User → Service Account** ein eigenes Servicekonto pro Aufrufer an.
Bewahre das einmal angezeigte App-Passwort auf und nimm das Konto
in `opencloud-scanner` auf.

Prüfe die Ablaufzeit des App-Passworts und plane die Erneuerung unter
**Directory → Tokens and App passwords**. Separate Konten erlauben es, einen
Aufrufer zu sperren, ohne die Zugangsdaten aller anderen zu ersetzen.
Servicekonten haben keinen Zugang zur normalen Benutzer- oder Adminoberfläche.

## Ein Token abrufen {#getting-a-token}

| Aufrufer | Verfahren oder Zugangsdaten |
|:--|:--|
| Person im Browser | Authorization Code mit Passwort und zweitem Faktor |
| Agent für eine Person | Benutzername und App-Passwort dieser Person |
| Automatisierter Dienst | Benutzername und App-Passwort eines Servicekontos |

Bei expliziten Servicekonten identifizieren Benutzername und App-Passwort das
Konto. Client-ID und Client-Geheimnis gehören zum OAuth-Provider. Daneben
unterstützt Authentik einen Abruf nur mit Client-Zugangsdaten; dessen Verhalten
ist unten gesondert beschrieben.

### Mit einem Servicekonto {#as-a-service-account}

```bash
curl -s https://sso.example.com/application/o/token/ \
  -d grant_type=client_credentials \
  -d client_id="$AUTHENTIK_CLIENT_ID" \
  -d client_secret="$AUTHENTIK_CLIENT_SECRET" \
  -d username="scanner-agent" \
  -d password="$APP_PASSWORD" \
  -d scope="openid" | jq -r .access_token
```

`username` und `password` gehören zum Servicekonto; `client_id` und
`client_secret` stammen aus `.env`. Fordere die konfigurierten Scopes an.
Ohne zusätzliche Scope-Vorgaben genügt hier `openid`.

Für Clients mit nur einem Geheimnisfeld kann der Benutzername eingebettet werden:

```bash
curl -s https://sso.example.com/application/o/token/ \
  -d grant_type=client_credentials \
  -d client_id="$AUTHENTIK_CLIENT_ID" \
  -d client_secret="$(printf '%s:%s' scanner-agent "$APP_PASSWORD" | base64 -w0)" \
  -d scope="openid" | jq -r .access_token
```

### Nur mit Client-Zugangsdaten {#without-naming-an-account-at-all}

Ohne Benutzernamen legt Authentik für diesen Abruf ein Servicekonto namens
`ak-check-opencloud-security-client_credentials` an:

```bash
curl -s https://sso.example.com/application/o/token/ \
  -d grant_type=client_credentials \
  -d client_id="$AUTHENTIK_CLIENT_ID" \
  -d client_secret="$AUTHENTIK_CLIENT_SECRET" \
  -d scope="openid" | jq -r .access_token
```

Das eignet sich für einen ersten Funktionstest. Bei gemeinsamer Nutzung lassen
sich einzelne Aufrufer jedoch nicht getrennt sperren. Sobald eine Gruppenbindung
besteht, muss auch dieses erzeugte Konto der Gruppe angehören. Verwende
für den dauerhaften Betrieb getrennte Servicekonten.

### Interaktive Anmeldung {#as-a-person}

Ein OAuth-fähiger MCP-Client findet den Provider über die 401-Antwort und die
Resource-Metadaten, öffnet den Browser und übernimmt das Token nach der Anmeldung.
Der Blueprint erlaubt Loopback-Weiterleitungen auf `127.0.0.1` mit variablem
Port und verwendet den Ablauf ohne zusätzliche Zustimmungsseite.

Falls der Client eine Registrierung benötigt, lege ihn unter
**Applications → Providers** an. Dynamische Registrierung ist bei Authentik
standardmäßig deaktiviert und setzt einen Registrierungstoken voraus.

### Den Token prüfen {#reading-the-token-you-got}

Lies bei Problemen zunächst die Claims aus. Das Dekodieren allein
verifiziert noch keine Signatur:

```bash
python -c 'import base64,json,sys;p=sys.argv[1].split(".")[1];print(json.dumps(json.loads(base64.urlsafe_b64decode(p+"="*(-len(p)%4))),indent=2))' "$TOKEN"
```

| Claim | Erwarteter Wert |
|:--|:--|
| `iss` | `COS_WEB_MCP_AUTH_ISSUER` |
| `aud` | Enthält `COS_WEB_MCP_AUTH_AUDIENCE` |
| `exp` | Liegt in der Zukunft |
| `scope` | Enthält alle geforderten Scopes |
| `sub` | Vom Provider vergeben; vom Scan-Webdienst nicht ausgewertet |

rufst du anschließend MCP auf:

```bash
curl -s https://scanner.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

Eine Werkzeugliste bestätigt den erfolgreichen Zugriff. Bei 401 prüfe
Issuer, Audience, Ablaufdatum, Signaturalgorithmus und Scopes. Verwende ein
Token für mehrere Aufrufe bis zu seinem Ablauf, statt für jede Anfrage ein neues
anzufordern. Die hier verwendeten JWTs werden lokal anhand der JWKS geprüft.

## Einen Agenten konfigurieren {#configuring-an-agent}

Viele MCP-Clients unterstützen einen statischen Header:

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

OAuth-fähige Clients können den Provider anhand der MCP-Adresse ermitteln;
gegebenenfalls ist eine manuelle Client-Registrierung erforderlich.
Die [MCP-Anleitung](../mcp.md) enthält Beispiele für die jeweiligen Clients.

## Scandaten löschen: separate Berechtigung {#erasure-which-is-a-different-credential}

`erase_instance_data` benötigt zusätzlich `COS_WEB_PURGE_TOKEN`. Bei einem
offenen MCP-Endpunkt steht dieser Wert in `Authorization`. Mit
Provider-Anmeldung gehört dieser Header dem Zugriffstoken; die Löschberechtigung
wird dann ausschließlich über `X-Purge-Authorization` übergeben:

```json
"headers": {
  "Authorization": "Bearer ${input:token}",
  "X-Purge-Authorization": "Bearer ${input:purge_token}"
}
```

Beide Werte kommen aus den HTTP-Headern, nicht aus Werkzeugargumenten.

## Betrieb hinter einem Reverse Proxy {#behind-a-reverse-proxy}

Authentik bildet den Issuer anhand des übergebenen Hosts. Lass den Proxy
den richtigen öffentlichen `Host` erhalten und `X-Forwarded-Proto` passend zur
Verbindung setzen. Ergänze bei Bedarf die Proxy-Adresse in
`AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS`. Authentik benötigt einen eigenen
Hostnamen statt eines Unterpfads.

Der Scan-Webdienst benötigt `COS_WEB_PUBLIC_BASE_URL` für seine öffentlichen
Metadaten. Die erwartete Token-Audience wird separat über
`COS_WEB_MCP_AUTH_AUDIENCE` festgelegt. Beispiele enthält der
[Reverse-Proxy-Leitfaden](../reverse-proxy.md).

## Sicherung {#backing-it-up}

Sichere folgende Bestandteile:

| Bestandteil | Speicherort | Zweck |
|:--|:--|:--|
| `AUTHENTIK_SECRET_KEY` | `docker/.env` | Kryptografischer Schlüssel der Installation |
| PostgreSQL | `authentik_database` | Konten, Gruppen, Abläufe, Richtlinien, Provider, Tokens und Zertifikate |
| Medien | `authentik_media` | Hochgeladene Bilder |
| Zertifikate und Vorlagen | `authentik_certs`, `authentik_templates` | Zusätzlich abgelegte Dateien |

```bash
cd docker
stack="-f docker-compose.authentik.yml"
stamp=$(date +%F)

# The database, as SQL, with the drop-and-create statements a clean restore
# needs.
docker compose $stack exec -T authentik_postgresql \
  pg_dump -U authentik -d authentik --clean --create \
  > "authentik-db-$stamp.sql"

# The volumes that are not the database.
for volume in media templates certs; do
  docker run --rm \
    -v "$(basename "$PWD")_authentik_$volume:/from:ro" \
    -v "$PWD:/to" alpine \
    tar czf "/to/authentik-$volume-$stamp.tar.gz" -C /from .
done

# And the secrets, without which none of the above is worth anything.
cp .env "authentik-env-$stamp.backup"
```

Compose stellt den Projektnamen vor die Volume-Namen. Mit `docker volume ls`
siehst du die tatsächlichen Namen. Der Datenbankdump enthält Zugangsdaten und
Schlüssel: Verschlüssele die Sicherung, bewahre sie außerhalb des
Hosts auf und teste eine Wiederherstellung.

## Wiederherstellung {#restoring-it}

```bash
cd docker
stack="-f docker-compose.authentik.yml"

# The secret key first, and it must be the one that was in use when the dump
# was taken.
cp authentik-env-2026-08-21.backup .env

docker compose $stack down
docker compose $stack up -d authentik_postgresql

docker compose $stack exec -T authentik_postgresql \
  psql -U authentik -d postgres < authentik-db-2026-08-21.sql

for volume in media templates certs; do
  docker run --rm \
    -v "$(basename "$PWD")_authentik_$volume:/to" \
    -v "$PWD:/from:ro" alpine \
    tar xzf "/from/authentik-$volume-2026-08-21.tar.gz" -C /to
done

docker compose $stack up -d
```

Stelle zunächst mit der zur Sicherung passenden PostgreSQL-Hauptversion
wieder her und führe danach gegebenenfalls ein Upgrade durch.
Der Scan-Webdienst hält keine eigenen Provider-Konten; seine Konfiguration
muss erhalten bleiben, die Signaturschlüssel lädt er erneut.

## Fehler eingrenzen {#when-it-does-not-work}

| Symptom | Was Du prüfst sollten |
|:--|:--|
| Startfehler zu Issuer, Resource-URL oder HTTPS | Vollständigkeit der MCP-Authentifizierungseinstellungen |
| Ständig 401 | `iss`, `aud`, Ablaufdatum, Scopes und Provider-Schlüssel |
| Token mit `alg: HS256` | Asymmetrischen Signaturschlüssel am Provider auswählen und neues Token abrufen |
| 401 nach zunächst erfolgreicher Nutzung | Token abgelaufen; Client muss es erneuern |
| Jedes Authentik-Konto erhält Zugang | Anwendungsbindung an `opencloud-scanner` fehlt |
| Token-Abruf scheitert bereits bei Authentik | Konto und Gruppenbindung; **Events → Logs** |
| Abruf nur mit Client-Geheimnis scheitert nach Gruppenbindung | Erzeugtes Servicekonto fehlt in der Gruppe |
| `invalid_grant` bei `client_credentials` | App-Passwort verwenden, kein normales Passwort und keinen API-Token |
| Einladung verweigert Zugriff | Enrollment-Token und Blueprint-Status prüfen |
| Benutzername für Einladung nicht zugelassen | `COS_AUTHENTIK_ACCOUNTS` ergänzen und Container neu starten |
| Benutzername bereits vergeben | Normale Anmeldung statt erneuter Registrierung |
| Zweiter Faktor verloren | Administrator entfernt das betroffene Gerät; anschließend neu einrichten |
| Bootstrap-Passwort funktioniert nicht | Es gilt nur für die erste Datenbankinitialisierung; Wiederherstellungslink erzeugen |
| Anmeldung erfolgreich, danach kein `/admin` | Gruppe `opencloud-scanner-operators` und exakten Eintrag in `COS_WEB_ADMIN_USERS` prüfen |
| PostgreSQL meldet falsches Passwort | `.env` muss zum initialisierten Volume passen; `POSTGRES_PASSWORD` ändert vorhandene Datenbankkonten nicht |
| Keine Wiederherstellungs-E-Mail | SMTP für Server und Worker konfigurieren |
| Kein `WWW-Authenticate` bei 401 | Proxy entfernt möglicherweise den Header |
| MCP unerwartet offen | Tatsächliche Container-Variable und `mcp.authentication.type` in `/.well-known/ai.json` prüfen |
| JWKS-Abruf liefert 404 | Internen Alias `authentik-server` statt Hostnamen mit Unterstrich verwenden |
| Blueprint erscheint nicht | Leserechte für uid 1000 prüfen; Verzeichnis 755, YAML-Dateien 644 |
| PostgreSQL 18 beanstandet Volume-Pfad | Volume unter `/var/lib/postgresql` einbinden; ältere Hauptversionen erfordern eine Migration |
| `Address family not supported by protocol` | Auf Hosts ohne IPv6 alle drei `AUTHENTIK_LISTEN__*`-Listener einschließlich Metriken auf IPv4 setzen |

Kontrolliere nach Konfigurationsänderungen auch den nicht angemeldeten Zugriff:

```bash
curl -s https://scanner.example.com/.well-known/ai.json | jq .mcp.authentication
curl -s https://scanner.example.com/.well-known/oauth-protected-resource/mcp | jq
curl -si https://scanner.example.com/mcp -X POST -d '{}' | grep -i www-authenticate
```

## Einen anderen Provider verwenden {#using-a-provider-that-is-not-authentik}

Auch andere Provider sind geeignet, wenn sie JWT-Zugriffstokens asymmetrisch
signieren und die öffentlichen Schlüssel als JWKS bereitstellen. Setze
Issuer und Audience entsprechend den tatsächlichen Claims und bei Bedarf
`COS_WEB_MCP_AUTH_JWKS_URL`.

Akzeptiert werden RS256, RS384, RS512, ES256, ES384 und ES512. HS256 und `none`
sind ausgeschlossen. Authentik wird als selbst betreibbare Open-Source-Variante
mitgeliefert.

---

Dies ist ein unabhängiges Community-Projekt. Es ist weder mit OpenCloud GmbH
noch mit Authentik Security, Inc. Verbunden und wird von diesen Unternehmen
nicht unterstützt. Die genannten Marken gehören ihren jeweiligen Inhabern.

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
