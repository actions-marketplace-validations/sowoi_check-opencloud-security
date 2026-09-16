# OpenCloud in einem iframe einbetten

Der OpenCloud-Webclient kann als Dateiauswahl oder Vorschau in eine andere Anwendung eingebettet werden. Die übergeordnete Seite und der eingebettete Client tauschen über `postMessage` Nachrichten aus. Bei delegierter Authentifizierung kann die übergeordnete Seite außerdem eine Sitzung an den Client übergeben.

Der Scanner liest das öffentliche `/config.json` und prüft, welchen Ursprüngen der eingebettete Client vertraut. Ein Ursprung besteht aus Protokoll, Host und Port. Kann `/config.json` nicht gelesen werden oder enthält es keinen `embed`-Block, gelten beide Prüfungen als bestanden, da keine Einbettungskonfiguration zur Prüfung vorliegt.

## 1. Nachrichten auf vertrauenswürdige Ursprünge beschränken: `webEmbedMessageOriginRestricted` {#1-does-the-embed-accept-messages-from-any-origin-webembedmessageoriginrestricted}

Der Scanner liest `options.embed.messagesOrigin`. Bei `WEB_OPTION_EMBED_MESSAGES_ORIGIN=*` akzeptiert der eingebettete Client `postMessage`-Nachrichten von jeder Seite, die ihn einbettet. So kann auch eine fremde Website den Client in einem versteckten oder irreführend dargestellten Frame laden und als übergeordnete Seite Nachrichten senden.

**Behebung:** Setze `WEB_OPTION_EMBED_MESSAGES_ORIGIN` auf den genauen Ursprung der erlaubten Seite, also Protokoll, Host und Port ohne Platzhalter oder Pfad. Deaktiviere die Einbettung, wenn sie nicht benötigt wird.

## 2. Delegierte Authentifizierung absichern: `webEmbedDelegatedAuthenticationRestricted` {#2-does-delegated-authentication-accept-an-unvalidated-origin-webembeddelegatedauthenticationrestricted}

Bei delegierter Authentifizierung übergibt die übergeordnete Seite ihre Sitzung an den eingebetteten Client. Dadurch entfällt eine zweite Anmeldung. Die Prüfung schlägt fehl, wenn `delegateAuthentication` auf `true` steht und `delegateAuthenticationOrigin` leer ist. Der Client würde dann eine Sitzung annehmen, ohne den Ursprung der übergeordneten Seite zu prüfen.

Da dies die Authentifizierung betrifft, hat der Befund den Schweregrad `critical`; die unbeschränkte Nachrichtenübermittlung hat `high`.

**Behebung:** Trage den genauen vertrauenswürdigen Ursprung unter `WEB_OPTION_EMBED_DELEGATE_AUTHENTICATION_ORIGIN` ein oder deaktiviere die delegierte Authentifizierung. Eine aktivierte delegierte Authentifizierung mit gesetztem Ursprung löst diesen Befund nicht aus.

## Schweregrad und Bewertung {#severity-and-rating-impact}

Beide Prüfungen gehören zu `extraChecks` und benötigen kein `--check-hardening`. Wenn `/config.json` einen `embed`-Block liefert, begrenzt `webEmbedMessageOriginRestricted` bei einem Fehler die Note auf `C` (`high`), `webEmbedDelegatedAuthenticationRestricted` auf `D` (`critical`). Siehe auch die [Prüfübersicht](../scanner-checks.md#what-the-scanner-checks).

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
