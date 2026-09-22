# Déploiement automatisé avec Ansible

Les playbooks de [`ansible/`](../../ansible/README.md) installent et configurent
le plugin sur un ou plusieurs hôtes Icinga2, au moyen d'une installation native
ou de Docker. Ils créent également les objets `CheckCommand` et `Service`
décrits dans [Icinga Director](icinga-director.md) et
[Icinga2 / Nagios](installation.md#icinga2--nagios).

Cette page est la version courte.
[`ansible/README.md`](../../ansible/README.md) fait référence, et c'est ce
fichier qui est tenu à jour avec les rôles eux-mêmes.

<!-- TOC -->
* [Déploiement automatisé avec Ansible](#automated-deployment-with-ansible)
  * [Quel rôle utiliser](#which-role-to-use)
  * [Démarrage rapide](#quick-start)
  * [Configurer le contrôle](#configuring-the-check)
  * [Avant de valider une modification du rôle](#before-you-commit-a-change-to-the-role)
<!-- TOC -->


## Quel rôle utiliser {#which-role-to-use}

| Rôle | Installe | À utiliser lorsque |
|:-----|:---------|:------------|
| `opencloud_check_native` | Le plugin dans un virtualenv dédié, lié symboliquement dans le répertoire des plugins Nagios | L'hôte de supervision dispose de Python et vous voulez le moins de pièces mobiles possible |
| `opencloud_check_docker` | L'image, construite sur l'hôte cible et invoquée par `docker run` | Vous préférez ne pas installer de paquets Python sur l'hôte de supervision |

Les deux rôles écrivent les mêmes objets Icinga2 : un hôte peut donc passer de
l'un à l'autre sans réécrire la définition de service.

## Démarrage rapide {#quick-start}

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

Les playbooks sont idempotents : les relancer est donc aussi la façon de mettre
à jour, car la version du plugin et les objets Icinga2 sont reconvergés à chaque
exécution.

## Configurer le contrôle {#configuring-the-check}

Chaque réglage est une variable `opencloud_check_*`, en correspondance directe
avec les variables d'environnement `COS_*` et les options de la ligne de
commande du [tableau des options](cli-reference.md#options). Une entrée d'hôte
réaliste :

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

`opencloud_check_host` vaut par défaut `inventory_hostname`, ce qui est correct
lorsque l'agent de supervision s'exécute sur l'hôte OpenCloud lui-même, et
incorrect dans la plupart des autres cas - définissez-le explicitement.

Laissez `opencloud_check_interval` à `24h` ou davantage. Chaque exécution est un
scan réel d'une instance réelle, et non une consultation en cache, et rien dans
la note d'une instance ne change d'une minute à l'autre.

Toutes les autres options du `CheckCommand` - `--eol-warning`,
`--release-track`, `--ignore-hardening` et les autres - se définissent via
`opencloud_check_extra_vars`, une table associant le nom de la variable
personnalisée, privé de son préfixe `opencloud_`, à sa valeur ; une liste répète
l'option une fois par élément.

```ini
opencloud_check_extra_vars={"eol_warning": 30, "ignore_hardening": ["hstsPreload"]}
```

Le tableau complet des variables, y compris celles propres à chaque rôle, se
trouve dans [`ansible/README.md`](../../ansible/README.md#variable-reference).

## Avant de valider une modification du rôle {#before-you-commit-a-change-to-the-role}

`ansible-lint` n'est propre que lorsqu'il est lancé depuis `ansible/` ; depuis
la racine du dépôt, il signale des dizaines de faux positifs.

```shell
cd ansible
ansible-lint
ansible-playbook -i inventory.ini playbooks/deploy_native.yml --syntax-check
```

---

[Retour à l'index de la documentation](../README.md) | [Retour au README principal](../../README.md)
