# TLS and certificate checks explained

# TLS- und Zertifikatsprüfungen

Der Scanner untersucht die TLS-Verbindung zur Instanz oder zu ihrem vorgeschalteten Proxy: Protokoll, Zertifikat, Zertifikatskette und ausgehandelte Cipher Suite. Ergänzend prüft er DNS-Angaben und vergleicht gegebenenfalls IPv4 und IPv6. Dafür ist kein besonderer Zugriff auf die Instanz nötig.

## 1. TLS-Verbindung aufbauen: `tlsHandshake`, `httpsAvailable` {#1-can-a-tls-connection-be-made-at-all-tlshandshake-httpsavailable}

- **`httpsAvailable`** schlägt mit `critical` fehl, wenn HTTPS nicht verwendet werden konnte und der Scan auf HTTP zurückfällt. Über diesen Weg besteht kein Transportschutz.
- **`tlsHandshake`** meldet einen fehlgeschlagenen TLS-Verbindungsaufbau, auch bei deaktivierter Zertifikatsprüfung. Der Port bietet dann möglicherweise kein TLS oder keine mit dem Client kompatiblen Parameter an.

Die Weiterleitung von HTTP auf HTTPS prüft separat `httpsEnforced`; siehe [Reverse Proxys](../reverse-proxy.md#two-findings-decided-here-that-are-not-headers).

## 2. Vertrauenswürdiges Zertifikat: `tlsTrusted` {#2-is-the-certificate-trusted-tlstrusted}

`opencloud init` erzeugt zunächst ein selbstsigniertes Zertifikat. Ein entsprechender Befund ist deshalb bei einer neuen Instanz zu erwarten. Unter [Selbstsignierte Instanzen](#self-signed-instances) wird beschrieben, wie der Scanner die übrigen Messungen trotzdem durchführt.

## 3. TLS-Versionen: `tlsProtocol`, `tlsDeprecatedProtocol` {#3-is-the-protocol-current-tlsprotocol-tlsdeprecatedprotocol}

TLS 1.0 und 1.1 sind seit RFC 8996 veraltet.

- **`tlsProtocol`** prüft, ob die tatsächlich ausgehandelte Verbindung mindestens TLS 1.2 verwendet.
- **`tlsDeprecatedProtocol`** prüft zusätzlich mit kurzen, auf ältere Versionen beschränkten Verbindungen, ob der Server diese noch akzeptiert. Eine erfolgreiche TLS-1.3-Verbindung allein belegt nicht, dass ältere Versionen deaktiviert sind.

Entfernen Sie veraltete Versionen aus der Serverkonfiguration, statt nur neuere zu bevorzugen.

## 4. Passender Hostname: `tlsHostname` {#4-does-the-certificate-cover-this-name-tlshostname}

Die Subject Alternative Names des Zertifikats müssen den gescannten Namen abdecken. Ein Zertifikat für eine andere Domain oder nur für `localhost` kann die Identität der angesprochenen Instanz nicht bestätigen.

## 5. Vollständige Zertifikatskette: `tlsChain` {#5-is-the-chain-complete-tlschain}

Eine unvollständige Kette, häufig durch ein fehlendes Zwischenzertifikat, kann in einem Browser mit Cache funktionieren und in anderen Clients scheitern. Liefern Sie das Serverzertifikat zusammen mit allen benötigten Zwischenzertifikaten aus, üblicherweise als `fullchain`. Das Root-Zertifikat wird normalerweise nicht mitgesendet.

## 6. Gültigkeitsdauer {#6-is-the-certificate-about-to-expire-or-issued-for-too-long}

- **`tlsCertificate`** prüft die verbleibende Gültigkeit gegen `scanner.tls_min_days`, standardmäßig 14 Tage. Prüfen Sie bei einem Befund die automatische Erneuerung und ob der TLS-Prozess das neue Zertifikat geladen hat.
- **`tlsCertificateLifetime`** meldet mit `low`, wenn die gesamte ausgestellte Laufzeit die im Scanner festgelegte Grenze von 398 Tagen überschreitet. Dies ist der Prüfwert dieser Implementierung und keine Aussage über die jeweils aktuellen Ausstellungsregeln öffentlicher Zertifizierungsstellen.

## 7. Cipher Suite und Zertifikatseigenschaften {#7-is-the-negotiated-cipher-suite-and-certificate-policy-sound}

- **`tlsCipherSuite`** bewertet die tatsächlich ausgehandelte Suite. Es wird nicht jede vom Server möglicherweise unterstützte Suite aufgezählt. Veraltete Primitive wie `NULL`, `RC4`, `3DES`/`DES-`, `MD5`, `CCM_8` oder fehlende Forward Secrecy führen zum Befund.
- **`tlsCertificatePolicy`** prüft auf RSA-Schlüssel unter 2048 Bit, EC-Schlüssel unter 256 Bit sowie MD5- oder SHA-1-Signaturen.

## 8. IPv4 und IPv6 vergleichen: `tlsAddressParity` {#8-do-ipv4-and-ipv6-present-the-same-service-tlsaddressparity}

Wenn beide Adressfamilien vorliegen, vergleicht der Scanner je einen TLS-Endpunkt. Unterschiedliche Zertifikate oder ein veralteter IPv6-Listener können dazu führen, dass Besucher je nach Verbindung einen anderen Sicherheitszustand sehen.

Diese Prüfung vergleicht die TLS-Identität, nicht sämtliche Backend-Einstellungen. Für mehrere Adressen mit demselben Zertifikat ergänzt `--all-addresses` die Prüfung `addressParity`; siehe [Alle aufgelösten Adressen](../scanner-checks.md#every-resolved-address).

## 9. Zertifikatsausstellung begrenzen: `tlsCaaRecord` {#9-is-certificate-issuance-restricted-tlscaarecord}

Ein DNS-CAA-Eintrag benennt die Zertifizierungsstellen, die für eine Domain ausstellen dürfen. Der Scanner prüft nur den genauen Zielnamen, nicht die übergeordneten Domains nach dem vollständigen RFC-8659-Suchverfahren. Ein fehlender Eintrag wird als `low` gemeldet. Die Änderung erfolgt in der DNS-Zone:

```
example.com. CAA 0 issue "letsencrypt.org"
```

## 9a. DNSSEC: `tlsDnssec` {#9a-can-the-address-itself-be-trusted-tlsdnssec}

DNSSEC ermöglicht die Prüfung signierter DNS-Antworten. Der Scanner befragt ausschließlich den bereits in `/etc/resolv.conf` konfigurierten Resolver. Er untersucht, ob dieser die Antwort validiert hat, Signaturen liefert oder die DNSSEC-Anfrage überhaupt unterstützt.

| Antwort | Ergebnis |
|:--|:--|
| Resolver meldet erfolgreiche Validierung | bestanden |
| Signaturen vorhanden, ohne gemeldete Validierung | bestanden als Nachweis einer signierten Zone; keine eigene vollständige Validierung |
| Weder Validierung noch Signaturen, DNSSEC-Anfrage aber verstanden | fehlgeschlagen |
| DNSSEC nicht unterstützt oder keine Antwort | Prüfung fehlt im Ergebnis |

Der Befund hat `low`. Aktivieren Sie DNSSEC bei Ihrem DNS-Anbieter und veröffentlichen Sie den zugehörigen DS-Eintrag in der übergeordneten Zone. Siehe [ADR 0038](../../adr/0038-a-dnssec-answer-nobody-could-have-given-is-not-a-finding.md).

## 10. OCSP-Stapling: `tlsOcspStapling` {#10-is-revocation-actually-checkable-tlsocspstapling}

Wenn das Zertifikat einen OCSP-Responder nennt, prüft der Scanner, ob der Server eine Statusantwort im Handshake mitliefert. Ohne Stapling müssen unterstützende Clients den Status separat abfragen oder auf diese Prüfung verzichten. Der Befund hat `low` und entfällt bei Zertifikaten ohne OCSP-Responder.

## 11. Certificate Transparency: `tlsCertificateTransparency` {#11-was-the-certificate-published-to-a-log-tlscertificatetransparency}

Certificate-Transparency-Logs machen die Ausstellung öffentlicher Zertifikate nachvollziehbar. Der Scanner zählt eingebettete Signed Certificate Timestamps (SCTs) im bereits abgerufenen Zertifikat. Er verwendet dafür dieselbe `openssl x509 -text`-Auswertung wie für Schlüssel und Signaturalgorithmus und fragt keine Logs ab.

Fehlende eingebettete SCTs werden mit `medium` gemeldet. Dies ist eine begrenzte Zertifikatsprüfung und keine vollständige Prüfung aller Wege, auf denen ein Client CT-Nachweise erhalten kann.

Die Prüfung läuft nur bei einer Kette zu einer öffentlichen Vertrauenswurzel und wenn das lokale OpenSSL die Erweiterung auswerten kann. Andernfalls fehlt der Befund. Selbstsignierte und private Zertifikate werden dadurch nicht pauschal abgewertet.

**Behebung:** Prüfen Sie die Ausstellung bei Ihrer Zertifizierungsstelle und lassen Sie bei Bedarf ein Zertifikat mit eingebetteten SCTs ausstellen.

## 12. TLS Early Data: `tlsEarlyData` {#12-is-a-replayable-0-rtt-flight-invited-tlsearlydata}

TLS 1.3 kann bei einer wiederaufgenommenen Sitzung Daten schon mit dem ersten Verbindungsaufbau senden. Dieses 0-RTT-Verfahren verkürzt die Wartezeit, schützt die frühen Daten aber auf TLS-Ebene nicht vor Wiederholung.

Der Scanner liest `Max Early Data` aus den Session-Tickets desselben `openssl s_client`-Aufrufs, der auch Stapling untersucht. Er prüft nicht, wie die Anwendung wiederholte Anfragen behandelt. Deshalb hat der Befund `low`. Fehlt eine auswertbare Angabe, bleibt das Ergebnis unbekannt.

**Behebung:** Deaktivieren Sie Early Data am TLS-Endpunkt, wenn Sie es nicht gezielt benötigen. Lassen Sie es nur aktiv, wenn die Anwendung die damit verbundenen Wiederholungsrisiken berücksichtigt.

## Grenzen der Messung {#what-is-deliberately-left-unmeasured}

Wenn das lokale OpenSSL ein altes TLS-Protokoll nicht mehr unterstützt, kann der Scanner dessen Annahme durch den Server nicht prüfen. Fehlt `openssl`, können unter anderem Stapling-Messungen entfallen. Solche Prüfungen werden nicht als bestanden ausgegeben.

Auch nicht vertrauenswürdige Zertifikate werden ausgelesen. Der Scanner dekodiert sie im DER-Format unabhängig von der Vertrauensprüfung, damit Ablaufdatum, Namen und Aussteller weiterhin sichtbar sind.

## Selbstsignierte Instanzen {#self-signed-instances}

Der Verbindungsaufbau erfolgt in dieser Reihenfolge:

1. HTTPS mit Zertifikatsprüfung.
2. Falls nötig HTTPS ohne Verifikation; `tlsTrusted` bleibt als Fehler sichtbar.
3. Falls nötig HTTP; dies führt zu `httpsAvailable` mit `critical`.

`--insecure` (`COS_INSECURE`) überspringt die Verifikationsanforderung. Eine nicht vertrauenswürdige Kette bleibt im Bericht, senkt dann aber die Note nicht. Für interne Zertifizierungsstellen können Sie stattdessen ein eigenes CA-Bundle konfigurieren.

## Schweregrad und Bewertung {#severity-and-rating-impact}

Die Prüfungen gehören zu `extraChecks`. Fehler begrenzen die Note entsprechend ihrem Schweregrad: `critical → D`, `high → C`, `medium → A`, `low → A+`. Die [Härtungsprüfungen](../../README.md#hardening-checks) erklären den Unterschied zu Härtungswerten; die [Prüfübersicht](../scanner-checks.md#what-the-scanner-checks) nennt alle Schweregrade.

## Weitere Informationen {#reference}

Der Leitfaden zu [Reverse Proxys](../reverse-proxy.md) behandelt HTTP-Header und Weiterleitungen zusätzlich zur TLS-Konfiguration.

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
