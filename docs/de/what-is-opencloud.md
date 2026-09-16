# Was ist OpenCloud?

[OpenCloud](https://opencloud.eu/) ist eine quelloffene Plattform zum Speichern, Synchronisieren und Teilen von Dateien. Dieser Scanner ist auf ihre Versionen, Einstellungen und Bereitstellungsweise zugeschnitten. Ein kompatibler Statusendpunkt allein genügt nicht, um andere Produkte damit zu bewerten.

## Herkunft {#where-opencloud-comes-from}

OpenCloud entstand als Fork von ownCloud Infinite Scale (oCIS), einer in Go geschriebenen Neuentwicklung des ownCloud-Servers. OpenCloud GmbH wurde mit Unterstützung der [Heinlein-Gruppe](https://www.heinlein-support.de/) gegründet. Die [Mitteilung zur Gründung](https://opencloud.eu/en/press/heinlein-group-strengthens-open-source-ecosystem-germany-founding-opencloud-gmbh) beschreibt den Hintergrund.

OpenCloud und oCIS teilen technische Grundlagen wie die [CS3-APIs](https://github.com/cs3org) und [Reva](https://github.com/cs3org/reva). Der Endpunkt `/status.php` stammt aus dem älteren Client-Protokoll und bleibt für die Kompatibilität erhalten. Er wird in OpenCloud nicht durch PHP ausgeführt; siehe [Der Statusendpunkt](../status-php.md).

Seit dem Fork wird OpenCloud eigenständig weiterentwickelt, unter anderem beim Dateispeicher und bei Integrationen. Der Server steht unter der Apache License 2.0.

## Architektur und Betrieb {#how-opencloud-is-structured}

| Bereich | OpenCloud |
|:--|:--|
| Serversprache | Go |
| Aufbau | Dienste auf Grundlage von CS3/Reva |
| Metadaten | Im Dateisystem neben den Dateidaten statt in einer klassischen SQL-Anwendungsdatenbank |
| Schwerpunkt | Dateiverwaltung, Freigaben und Zusammenarbeit |
| Release-Modell | Parallele Rolling-, Production- und LTS-Kanäle |
| Serverlizenz | Apache License 2.0 |

Diese Architektur hat Folgen für Betrieb und Wartung. Es gibt beispielsweise kein SQL-Schema-Upgrade, wie es das Kompatibilitätsfeld `needsDbUpgrade` vermuten lässt. Der Handler setzt dieses Feld fest auf `false`; siehe [Antwort des Statusendpunkts](../status-php.md#what-the-handler-actually-returns).

Für Backups müssen trotzdem die verwendeten Speicher, Metadaten, Konfigurationen und gegebenenfalls externe Dienste berücksichtigt werden. Eine von außen erreichbare Dateiplattform zeigt dem Scanner nur einen Teil dieses Betriebszustands.

## Bedeutung für den Sicherheitsscan {#why-this-matters-for-a-security-scan}

Verwandte Produkte können denselben `/status.php`-Pfad beantworten, besitzen aber eigene Releases, Sicherheitshinweise und Standardkonfigurationen. Eine Bewertung mit den falschen Referenzdaten wäre irreführend.

Der Scanner prüft deshalb `product` und `productname` und bewertet nur eine als OpenCloud erkannte Instanz. Bei einem anderen Produkt musst du das passende Prüfwerkzeug verwenden; siehe [Fehlersuche](../troubleshooting.md).

Dieses Projekt ist unabhängig von OpenCloud GmbH. „OpenCloud“ und zugehörige Marken gehören ihren jeweiligen Inhabern und werden hier nur zur Bezeichnung der geprüften Software verwendet. Der vollständige Hinweis steht in der [Dokumentationsübersicht](../README.md).

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
