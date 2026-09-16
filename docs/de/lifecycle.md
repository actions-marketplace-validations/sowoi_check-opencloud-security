# Version and lifecycle disclosure checks explained

# Versionsangaben prüfen

Drei Prüfungen befassen sich mit der Erkennung und Offenlegung der laufenden Version. Sie ergänzen die [End-of-Life-Erkennung](../../README.md#end-of-life-detection) und die Update-Prüfung: Beide können nur arbeiten, wenn die tatsächliche OpenCloud-Version bekannt ist.

## 1. Version erkennen: `versionDetection` {#1-could-the-running-version-be-determined-at-all-versiondetection}

`/status.php` kann drei Felder mit Versionsangaben liefern, von denen nur eines die tatsächliche OpenCloud-Version enthält. [Die Version richtig lesen](../scanner-checks.md#reading-the-version-correctly) erklärt die Unterschiede; [der Leitfaden zu `/status.php`](../status-php.md) beschreibt den Ursprung der Kompatibilitätsfelder. Diese Prüfung schlägt fehl, wenn `productversion` fehlt und nur die älteren Felder `version` und `versionstring` vorliegen.

Ohne die tatsächliche Version lassen sich weder Sicherheitshinweise zuordnen noch Supportstatus und verfügbare Updates bestimmen. Diese Teile des Berichts sind dann unbekannt; sie gelten nicht als bestanden.

**Bei einem Fehler:** Prüfen Sie, ob ein vorgeschalteter Proxy Felder aus `/status.php` entfernt oder umschreibt. Auch eine alte OpenCloud-Version, die noch kein `productversion` ausgibt, kommt als Ursache infrage. Behandeln Sie alle versionsabhängigen Ergebnisse als unbekannt, bis eine verlässliche Versionsangabe vorliegt.

## 2. Version in HTTP-Headern: `versionDisclosure:<header>` {#2-does-a-response-header-publish-the-version-versiondisclosureheader}

Der Scanner sucht in `Server` und `X-Powered-By` nach Versionsmustern aus Ziffer, Punkt und weiterer Ziffer. Die Angabe allein ist keine Schwachstelle, erleichtert aber die Suche nach passenden bekannten Angriffen. Beide Befunde haben deshalb den Schweregrad `low`.

**Behebung:** Unterdrücken oder kürzen Sie die Versionsangabe im Reverse Proxy, etwa mit `server_tokens off` in nginx oder `ServerTokens Prod` in Apache. Sie können den betreffenden Header auch vollständig entfernen. Entsprechende Einstellungen für Caddy, Traefik und HAProxy finden Sie unter [Reverse Proxys](../reverse-proxy.md).

## 3. Version im Webfinger-Dokument: `webfingerVersionDisclosure` {#3-does-the-webfinger-document-publish-the-version-webfingerversiondisclosure}

Der Scanner ruft `/.well-known/webfinger` ohne Anmeldung ab und sucht in der Antwort nach einer Versionsangabe. Wie bei den HTTP-Headern handelt es sich um eine Offenlegung von Informationen mit dem Schweregrad `low`, hier in einem JSON-Dokument.

**Behebung:** Entfernen Sie die Versionsangabe über den Reverse Proxy aus der Webfinger-Antwort. Wenn Sie die Offenlegung bewusst akzeptieren, halten Sie die Instanz aktuell: Besonders hilfreich ist die Angabe für Angreifer, solange bekannte Schwachstellen dieser Version ungepatcht sind.

## Schweregrad und Bewertung {#severity-and-rating-impact}

Alle drei Prüfungen gehören zu `extraChecks` und benötigen kein `--check-hardening`. `versionDetection` hat den Schweregrad `medium` und begrenzt die Note auf `A`; die Offenlegungsprüfungen haben `low` und begrenzen sie auf `A+`. Details stehen in der [Prüfübersicht](../scanner-checks.md#what-the-scanner-checks).

Diese Befunde sind von der [End-of-Life-Bewertung](../../README.md#end-of-life-detection) unabhängig. Eine verborgene Versionsnummer verlängert den Support einer veralteten Version nicht.

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
