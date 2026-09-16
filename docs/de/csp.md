# Content-Security-Policy prüfen

Eine Content-Security-Policy (CSP) legt fest, welche Quellen der Browser für Skripte, Styles, Frames und andere Inhalte verwenden darf. Eine passende Richtlinie kann die Auswirkungen eingeschleuster Inhalte und Skripte begrenzen. Der Scanner prüft sowohl das Vorhandensein des Headers als auch bestimmte Freigaben für Skriptausführung.

## 1. Ist der Header vorhanden? {#1-is-the-header-present-at-all}

`Content-Security-Policy` gehört zu den acht Headern unter `setup.headers`. Das Plugin berücksichtigt sie mit `--check-hardening`; im Webbericht werden sie immer angezeigt. Ein fehlender Header wird als eigener Befund gemeldet:

> Die Antwort enthält keine CSP, die die Quellen für Skripte, Styles und Frames einschränkt.

OpenCloud liefert standardmäßig eine CSP. Fehlt sie, prüfe zuerst, ob ein vorgeschalteter Reverse Proxy den Header entfernt oder selbst antwortet. Beispiele für nginx, Apache, Caddy, Traefik und HAProxy stehen unter [Reverse Proxys](../reverse-proxy.md).

## 2. Skriptausführung einschränken: `cspWithoutUnsafeInline` {#2-is-the-policy-actually-restrictive-cspwithoutunsafeinline}

Eine vorhandene CSP kann weiterhin weitreichende Ausnahmen erlauben. `cspWithoutUnsafeInline` liest `script-src` oder ersatzweise `default-src` und sucht nach `unsafe-inline` und `unsafe-eval`:

- **`unsafe-inline`** kann Inline-Skripte und Ereignisbehandler zulassen, sofern keine wirksame Nonce- oder Hash-Regel diese Freigabe ersetzt.
- **`unsafe-eval`** erlaubt die Ausführung von Zeichenfolgen als Code, etwa über `eval()` oder den `Function`-Konstruktor.

**Die unveränderte OpenCloud-Standardkonfiguration besteht diese Prüfung nicht.** Die mitgelieferte `csp.yaml` enthält `unsafe-inline` in `script-src` und `style-src`. Das Webfrontend benötigt derzeit Inline-Skripte und -Styles. Der Befund weist deshalb nicht automatisch auf einen Einrichtungsfehler hin. Eine strengere CSP muss mit der Oberfläche und ihren Integrationen getestet werden.

Die Prüfung akzeptiert `unsafe-inline`, wenn die Richtlinie zugleich eine Nonce oder einen Hash enthält. Browser mit Unterstützung dafür ignorieren dann die allgemeine Inline-Freigabe in der betreffenden Quellenliste. Für ältere Browser kann sie als Rückfallregel erhalten bleiben.

## Die Richtlinie anpassen {#fixing-it}

Verweise mit `PROXY_CSP_CONFIG_FILE_LOCATION` auf eine eigene `csp.yaml` oder ersetze die Standardrichtlinie über `PROXY_CSP_CONFIG_FILE_OVERRIDE_LOCATION`. Entferne nicht benötigte Freigaben für `unsafe-inline` und `unsafe-eval`. Eine Nonce- oder Hash-basierte Richtlinie, gegebenenfalls mit `strict-dynamic`, setzt passende Änderungen an den ausgelieferten Skripten voraus.

Teste die Weboberfläche sowie Office- und Anmeldeintegrationen vor der Übernahme. Eine strengere Richtlinie kann benötigte Skripte oder Styles blockieren.

Referenz: [Umgebungsvariablen des OpenCloud-Proxy-Dienstes](https://docs.opencloud.eu/docs/dev/server/services/proxy/environment-variables).

## Schweregrad und Bewertung {#severity-and-rating-impact}

`cspWithoutUnsafeInline` ist eine Härtungsmaßnahme. Sie wird mit `--check-hardening` berücksichtigt und im Webbericht immer angezeigt. Allein begrenzt sie die Note nicht wie ein fehlgeschlagener `extraChecks`-Eintrag. Den Unterschied erklären die [Härtungsprüfungen](../../README.md#hardening-checks).

Der fehlende CSP-Header wird dagegen als `header:`-Zusatzprüfung bewertet und begrenzt die Note, wenn `--check-hardening` aktiv ist. Siehe [Prüfübersicht](../scanner-checks.md#what-the-scanner-checks).

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
