# Icinga Director

[Icinga Director](https://icinga.com/docs/icinga-director/latest/) verwaltet `CheckCommand`, `Service Template` und `Service` über eine Weboberfläche. Die folgende Einrichtung funktioniert sowohl mit der nativen Installation als auch mit dem [Docker-Image](../installation.md#docker).

1. **CheckCommand anlegen**
   - Öffne *Icinga Director → Commands → Add*.
   - Setze **Command name** auf `check_opencloud_security`.
   - Wähle als **Command** bei nativer Installation `/usr/lib/nagios/plugins/check-opencloud-security` oder den tatsächlichen Installationspfad; siehe [Installation](../../README.md#installation).
   - Für Docker verwende `/usr/bin/docker`. Die festen Argumente `run`, `--rm` und der Image-Name stehen im [Docker-CheckCommand-Beispiel](../installation.md#using-the-docker-image-instead).
   - Wähle **Command type: Plugin Check Command**.

2. **Argumente hinzufügen** (*Fields → Add argument*):

   | Argument | Wert | Bedeutung |
   |:--|:--|:--|
   | `--host` | `$address$` oder ein eigenes Datenfeld wie `$opencloud_host$` | Hostname, IP oder URL der OpenCloud-Instanz; erforderlich |
   | `--port` | Optionales Datenfeld `$opencloud_port$` | Port, z. B. `9200` |
   | `--insecure` | Optionales boolesches Set-if-Datenfeld `$opencloud_insecure$` | Zertifikatsprüfung deaktivieren, etwa bei selbstsignierten Zertifikaten |
   | `--proxy` | Optionales Datenfeld `$opencloud_proxy$` | HTTP-/HTTPS-Proxy |
   | `--debug` | Optionales boolesches Set-if-Datenfeld `$opencloud_debug$` | Ausführliche Diagnoseausgabe |

   Das sind die gängigen. Jede weitere Option steht mit ihrem Variablennamen in [`contrib/icinga2/check_opencloud_security.conf`](../../contrib/icinga2/check_opencloud_security.conf); lege sie genauso an.

   Aktiviere bei optionalen Argumenten *Skip this argument on empty value*. Director lässt das Argument dann weg, wenn kein Wert gesetzt ist.

3. **Datenfelder für Services bereitstellen**
   - Lege unter *Fields → Add data field* die passenden Felder an, etwa `opencloud_host`, `opencloud_port`, `opencloud_insecure` und `opencloud_debug`.
   - Wähle den passenden *Data Type* (`String` oder `Boolean`) und bei Bedarf einen *Var Filter*.

4. **Service-Vorlage anlegen**
   - Öffne *Icinga Director → Service Templates → Add*.
   - Setze **Check command** auf `check_opencloud_security`.
   - Beginne mit einem **Check interval** von `24h`. Lies vor kürzeren Intervallen den Hinweis unter [Icinga2 / Nagios](../installation.md#icinga2--nagios).
   - Lass die Datenfelder hier leer, damit sie je Service oder Host gesetzt werden können.

5. **Vorlage einem Host oder einer Hostgruppe zuweisen**
   - Öffne *Icinga Director → Services → Add*. Für eine Hostgruppe verwende eine *Service Apply Rule*.
   - Importiere die erstellte Service-Vorlage.
   - Setze `opencloud_host` und die benötigten optionalen Felder. Wenn du `$address$` beibehalten hast, ist kein eigenes Hostfeld nötig.
   - Übernimm die Konfiguration unter *Icinga Director → Deployments*.

Icinga2 führt anschließend den nativen Befehl oder `docker run` wie unter [Icinga2 / Nagios](../installation.md#icinga2--nagios) beschrieben aus.

Damit das `Service`-Objekt aus einer gerade erstellten Konfiguration für dich geschrieben wird, mit bereits eingetragenen Schwellwerten und Release-Track, führe `check-opencloud-scanner configure --export-monitoring icinga` aus - siehe [`configure`](scanner-cli.md#configure-write-a-configuration-file). Das `CheckCommand` aus Schritt 1 wird weiterhin benötigt.

Für die automatisierte Bereitstellung derselben Objekte steht [Ansible](../ansible.md) zur Verfügung.

---

[Zur Dokumentationsübersicht](../README.md) | [Zum Haupt-README](../../README.md)

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
