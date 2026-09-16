# OpenCloud Security Scanner in Icinga Director

# Icinga Director

[Icinga Director](https://icinga.com/docs/icinga-director/latest/) verwaltet `CheckCommand`, `Service Template` und `Service` über eine Weboberfläche. Die folgende Einrichtung funktioniert sowohl mit der nativen Installation als auch mit dem [Docker-Image](../installation.md#docker).

1. **CheckCommand anlegen**
   - Öffnen Sie *Icinga Director → Commands → Add*.
   - Setzen Sie **Command name** auf `check_opencloud_security`.
   - Wählen Sie als **Command** bei nativer Installation `/usr/lib/nagios/plugins/check-opencloud-security` oder den tatsächlichen Installationspfad; siehe [Installation](../../README.md#installation).
   - Für Docker verwenden Sie `/usr/bin/docker`. Die festen Argumente `run`, `--rm` und der Image-Name stehen im [Docker-CheckCommand-Beispiel](../installation.md#using-the-docker-image-instead).
   - Wählen Sie **Command type: Plugin Check Command**.

2. **Argumente hinzufügen** (*Fields → Add argument*):

   | Argument | Wert | Bedeutung |
   |:--|:--|:--|
   | `--host` | `$address$` oder ein eigenes Datenfeld wie `$opencloud_host$` | Hostname, IP oder URL der OpenCloud-Instanz; erforderlich |
   | `--port` | Optionales Datenfeld `$opencloud_port$` | Port, z. B. `9200` |
   | `--insecure` | Optionales boolesches Set-if-Datenfeld `$opencloud_insecure$` | Zertifikatsprüfung deaktivieren, etwa bei selbstsignierten Zertifikaten |
   | `--proxy` | Optionales Datenfeld `$opencloud_proxy$` | HTTP-/HTTPS-Proxy |
   | `--debug` | Optionales boolesches Set-if-Datenfeld `$opencloud_debug$` | Ausführliche Diagnoseausgabe |

   Aktivieren Sie bei optionalen Argumenten *Skip this argument on empty value*. Director lässt das Argument dann weg, wenn kein Wert gesetzt ist.

3. **Datenfelder für Services bereitstellen**
   - Legen Sie unter *Fields → Add data field* die passenden Felder an, etwa `opencloud_host`, `opencloud_port`, `opencloud_insecure` und `opencloud_debug`.
   - Wählen Sie den passenden *Data Type* (`String` oder `Boolean`) und bei Bedarf einen *Var Filter*.

4. **Service-Vorlage anlegen**
   - Öffnen Sie *Icinga Director → Service Templates → Add*.
   - Setzen Sie **Check command** auf `check_opencloud_security`.
   - Beginnen Sie mit einem **Check interval** von `24h`. Lesen Sie vor kürzeren Intervallen den Hinweis unter [Icinga2 / Nagios](../installation.md#icinga2--nagios).
   - Lassen Sie die Datenfelder hier leer, damit sie je Service oder Host gesetzt werden können.

5. **Vorlage einem Host oder einer Hostgruppe zuweisen**
   - Öffnen Sie *Icinga Director → Services → Add*. Für eine Hostgruppe verwenden Sie eine *Service Apply Rule*.
   - Importieren Sie die erstellte Service-Vorlage.
   - Setzen Sie `opencloud_host` und die benötigten optionalen Felder. Wenn Sie `$address$` beibehalten haben, ist kein eigenes Hostfeld nötig.
   - Übernehmen Sie die Konfiguration unter *Icinga Director → Deployments*.

Icinga2 führt anschließend den nativen Befehl oder `docker run` wie unter [Icinga2 / Nagios](../installation.md#icinga2--nagios) beschrieben aus.

Für die automatisierte Bereitstellung derselben Objekte steht [Ansible](../ansible.md) zur Verfügung.

---

[Zur Dokumentationsübersicht](../README.md) | [Zum Haupt-README](../../README.md)

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
