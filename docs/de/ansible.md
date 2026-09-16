# Deploy the OpenCloud Security Scanner with Ansible

# Bereitstellung mit Ansible

Die Playbooks unter [`ansible/`](../../ansible/README.md) installieren und konfigurieren das Plugin auf einem oder mehreren Icinga2-Hosts. Sie unterstützen die native Installation und Docker und legen die in [Icinga Director](../icinga-director.md) sowie [Icinga2 / Nagios](../installation.md#icinga2--nagios) beschriebenen `CheckCommand`- und `Service`-Objekte an.

Dieser Leitfaden erklärt die ersten Schritte. Die vollständige, mit den Rollen gepflegte Referenz finden Sie im [Ansible-README](../../ansible/README.md).

## Die passende Rolle wählen {#which-role-to-use}

| Rolle | Installation | Geeignet für |
|:--|:--|:--|
| `opencloud_check_native` | Eigenes virtualenv mit Symlink im Nagios-Plugin-Verzeichnis | Monitoring-Hosts mit Python |
| `opencloud_check_docker` | Auf dem Zielhost gebautes Image, aufgerufen mit `docker run` | Hosts, auf denen keine Python-Pakete installiert werden sollen |

Beide Rollen erzeugen dieselben Icinga2-Objekte. Beim Wechsel zwischen ihnen müssen Sie die Service-Definition nicht neu schreiben.

## Erste Schritte {#quick-start}

```shell
cd ansible
cp inventory.example.ini inventory.ini
$EDITOR inventory.ini   # the Icinga2 hosts, and opencloud_check_host per host

# Native (virtualenv) install:
ansible-playbook -i inventory.ini playbooks/deploy_native.yml

# ... or the Docker install:
ansible-galaxy collection install -r requirements.yml
ansible-playbook -i inventory.ini playbooks/deploy_docker.yml
```

Die Playbooks sind idempotent: Ein erneuter Aufruf stellt den gewünschten Zustand wieder her und dient auch zur Aktualisierung. Dabei werden Plugin-Version und Icinga2-Objekte abgeglichen.

## Den Check konfigurieren {#configuring-the-check}

Die Variablen `opencloud_check_*` entsprechen den `COS_*`-Umgebungsvariablen und CLI-Optionen in der [Optionstabelle](../cli-reference.md#options). Ein Beispiel für einen Hosteintrag:

```ini
[icinga_hosts]
monitoring.example.com

[icinga_hosts:vars]
opencloud_check_host=opencloud.example.com
opencloud_check_port=9200
opencloud_check_check_hardening=true
opencloud_check_update_warning=true
opencloud_check_interval=24h
```

Setzen Sie `opencloud_check_host` ausdrücklich. Der Standard `inventory_hostname` passt nur, wenn auf dem angesprochenen Host tatsächlich die zu prüfende OpenCloud-Instanz läuft.

Verwenden Sie für `opencloud_check_interval` zunächst `24h` oder mehr. Jeder Durchlauf führt einen vollständigen Scan gegen die Instanz aus. Für die meisten Versions- und Konfigurationsprüfungen sind Abfragen im Minutentakt nicht nötig.

Die [Variablenreferenz](../../ansible/README.md#variable-reference) enthält auch die rollenspezifischen Einstellungen.

## Änderungen an einer Rolle prüfen {#before-you-commit-a-change-to-the-role}

Führen Sie `ansible-lint` aus dem Verzeichnis `ansible/` aus. Vom Repository-Stamm aus wird die vorgesehene Konfiguration nicht korrekt angewendet und es können unzutreffende Meldungen entstehen.

```shell
cd ansible
ansible-lint
ansible-playbook -i inventory.ini playbooks/deploy_native.yml --syntax-check
```

---

[Zur Dokumentationsübersicht](../README.md) | [Zum Haupt-README](../../README.md)

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
