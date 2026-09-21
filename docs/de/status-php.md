# Warum OpenCloud auf /status.php antwortet

OpenCloud ist in Go geschrieben. Der Pfad `/status.php` bezeichnet kein PHP-Skript, sondern einen Kompatibilitätsendpunkt für bestehende Clients.

## Herkunft des Pfads {#where-the-path-comes-from}

OpenCloud ging aus ownCloud Infinite Scale (oCIS) hervor und verwendet die [CS3-APIs](https://github.com/cs3org) und [Reva](https://github.com/cs3org/reva). Der ursprüngliche ownCloud-Server bot `/status.php` an, damit Synchronisationsclients, Apps und Monitoring-Skripte vor der Anmeldung Produkt und Version abfragen konnten. Kompatible Nachfolger beantworten diesen Pfad weiterhin.

Der gemeinsame Endpunkt reicht jedoch nicht aus, um alle diese Produkte nach denselben Regeln zu bewerten. Meldet er ein anderes Produkt als OpenCloud, beendet dieser Scanner die Prüfung. Weitere Hinweise findest du unter [Fehlersuche](../troubleshooting.md) und [Was ist OpenCloud?](../what-is-opencloud.md).

Im OpenCloud-Quellcode registriert das eingebundene Reva-Paket die Route:

```go
// vendor/github.com/opencloud-eu/reva/v2/internal/http/services/owncloud/ocdav/ocdav.go
return []string{"/status.php", "/status", "/remote.php/dav/public-files/", ...}
...
case "status.php", "status":
    s.doStatus(w, r)
```

`/status.php` und `/status` erreichen denselben Handler. Die Endung `.php` bleibt erhalten, weil Clients genau diesen Pfad erwarten.

## Welche Werte der Handler liefert {#what-the-handler-actually-returns}

Der Handler `doStatus` baut die Antwort aus einem Struct-Literal auf:

```go
// vendor/github.com/opencloud-eu/reva/v2/internal/http/services/owncloud/ocdav/status.go
status := &ocs.Status{
    Installed:      true,
    Maintenance:    false,
    NeedsDBUpgrade: false,
    Version:        s.c.Version,
    VersionString:  s.c.VersionString,
    Edition:        s.c.Edition,
    ProductName:    s.c.ProductName,
    ProductVersion: s.c.ProductVersion,
    Product:        s.c.Product,
}
```

`Installed`, `Maintenance` und `NeedsDBUpgrade` sind fest auf `true`, `false` und `false` gesetzt. Diese Werte werden weder aus dem aktuellen Betriebszustand noch aus einer Datenbank oder Datei gelesen. Eine Instanz mit diesem Handler liefert daher dieselben Werte während des Starts, einer Bereitstellung und des normalen Betriebs. OpenCloud verwendet zudem keine SQL-Datenbank mit Schema-Upgrades, wie der Feldname `needsDbUpgrade` vermuten lässt.

`Version`, `VersionString`, `Edition`, `ProductName`, `ProductVersion` und `Product` stammen aus der Dienstkonfiguration `s.c`. `Version` und `VersionString` dienen allerdings als feste Kompatibilitätsangaben für ältere Clients. Die tatsächliche Release-Version steht in `ProductVersion`; siehe [Die Version richtig lesen](../scanner-checks.md#reading-the-version-correctly).

## Welche Felder der Scanner auswertet {#what-this-scanner-reads-from-it-and-what-it-does-not}

Der Scanner liest `product` und `productname`, um OpenCloud zu erkennen, sowie `productversion` für Supportstatus, Sicherheitshinweise und Updates. [Versionsangaben prüfen](../lifecycle.md) erklärt, was bei einer fehlenden Versionsnummer passiert.

`installed`, `maintenance` und `needsDbUpgrade` werden nicht bewertet, da ihre festen Werte keine Aussage über den aktuellen Betrieb erlauben. Frühere Scanner-Versionen leiteten daraus die Befunde `maintenanceMode`, `installed` und `databaseUpgrade` ab. Diese Prüfungen wurden entfernt, nachdem die festgelegten Antworten im OpenCloud-Quellcode bestätigt worden waren.

Falls OpenCloud diese Felder künftig aus dem tatsächlichen Zustand berechnet, muss die Bewertung erneut anhand des Handlers geprüft werden. Maßgeblich ist der Quellcode der jeweiligen Version.

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
