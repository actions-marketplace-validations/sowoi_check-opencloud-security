# Cookie-Attribute prüfen

Der Scanner untersucht die `Set-Cookie`-Header der öffentlichen Antworten auf vier Schutzmaßnahmen. Er speichert keine Cookie-Werte. Geprüft werden nur die Attribute der Cookies, die OpenCloud oder ein vorgeschalteter Proxy tatsächlich sendet.

Setzt die untersuchte Antwort keine Cookies, erscheinen diese Prüfungen nicht im Ergebnis. Es liegen dann keine Cookie-Attribute zur Bewertung vor.

## 1. HTTPS verlangen: `cookieSecure` {#1-does-the-cookie-require-https-cookiesecure}

Ohne `Secure` kann der Browser ein Cookie auch über unverschlüsseltes HTTP senden, sofern die übrigen Regeln dies zulassen. Wird es dabei mitgelesen, kann ein Angreifer den Wert möglicherweise wiederverwenden.

**Behebung:** Setze `Secure` für Cookies, die ausschließlich über HTTPS übertragen werden sollen. Bei TLS-Terminierung im Reverse Proxy kann es sich um dessen Sitzungs- oder CSRF-Cookies handeln. Die Konfiguration gehört dann in den Proxy; siehe [Reverse Proxys](../reverse-proxy.md).

## 2. Zugriff durch Seitenskripte begrenzen: `cookieHttpOnly` {#2-can-page-scripts-read-the-cookie-cookiehttponly}

Ohne `HttpOnly` kann JavaScript auf der Seite das Cookie über `document.cookie` lesen. Bei einer XSS-Schwachstelle kann dadurch auch der Cookie-Wert gestohlen werden. Besonders relevant ist dies für Sitzungscookies.

**Behebung:** Setze `HttpOnly`, wenn das Cookie nicht von einem Browserskript gelesen werden muss. Einige CSRF-Verfahren sowie Funktionen für Einstellungen oder Einwilligungen benötigen Cookies, die JavaScript lesen kann. Prüfe daher die Funktion des jeweiligen Cookies, bevor du das Attribut ergänzt.

## 3. Websiteübergreifende Anfragen begrenzen: `cookieSameSite` {#3-is-the-cookie-sent-on-cross-site-requests-cookiesamesite}

`SameSite` legt fest, wann der Browser ein Cookie bei websiteübergreifenden Anfragen mitsendet, und kann so zum Schutz vor CSRF beitragen. Browser wenden bei einem fehlenden Attribut eigene Standardregeln an. Die Prüfung verlangt eine ausdrückliche Einstellung, damit das Verhalten nicht davon abhängt.

**Behebung:** Verwende `SameSite=Lax` oder `SameSite=Strict`, sofern die Anwendung keinen websiteübergreifenden Ablauf mit `SameSite=None` benötigt. `None` erfordert zusätzlich `Secure`. `Lax` erlaubt unter anderem bestimmte Navigationen auf oberster Ebene, etwa das Öffnen eines geteilten Links.

## 4. Cookie-Präfixe verwenden: `cookiePrefix` {#4-does-the-cookie-name-carry-a-prefix-cookieprefix}

Die Präfixe `__Host-` und `__Secure-` verpflichten unterstützende Browser dazu, beim Setzen eines Cookies zusätzliche Regeln zu prüfen. `__Secure-` verlangt `Secure` und einen sicheren Ursprung. `__Host-` verlangt außerdem `Path=/` und verbietet `Domain`. Das bindet das Cookie an den Host und erschwert das Überschreiben durch eine benachbarte Subdomain.

Die Prüfung unterscheidet zwei Fälle:

- **Ungültiges Präfix:** Ein Cookie heißt etwa `__Host-…`, besitzt aber `Domain`, einen anderen Pfad als `/` oder kein `Secure`. Browser, die die Präfixregeln unterstützen, lehnen es ab. Die Detailmeldung nennt die verletzte Regel.
- **Kein beobachtetes Cookie verwendet ein Präfix.** Der Scanner meldet die fehlende zusätzliche Schutzmaßnahme.

**Behebung:** Benenne das Sitzungscookie in `__Host-<name>` um und setze `Secure`, `Path=/` und kein `Domain`. Muss das Cookie über Subdomains hinweg gelten, kommt `__Secure-<name>` infrage. Nimm die Änderung dort vor, wo das Cookie erzeugt wird: in OpenCloud, im Reverse Proxy oder beim Identitätsanbieter.

## Schweregrad und Bewertung {#severity-and-rating-impact}

Die vier Prüfungen gehören zu `extraChecks` und erscheinen, sobald ein Cookie beobachtet wird. `cookieSecure` hat `high`, `cookieHttpOnly` hat `medium`, `cookieSameSite` und `cookiePrefix` haben `low`. Bei einem Fehler begrenzen sie die Note entsprechend auf `C`, `A` oder `A+`; siehe [Prüfübersicht](../scanner-checks.md#what-the-scanner-checks).

Mit `scanner.extra_checks_rating: false` bleiben die Befunde sichtbar, ohne die Note zu beeinflussen. `--no-extra-checks` deaktiviert die zusätzlichen Prüfungen vollständig.

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
