# Icinga Director
[Icinga Director](https://icinga.com/docs/icinga-director/latest/) gère les
objets `CheckCommand`, `Service Template` et `Service` depuis son interface web
plutôt que par des fichiers de configuration écrits à la main. Les étapes
ci-dessous fonctionnent aussi bien pour l'installation native que pour l'image
[Docker](installation.md#docker).

1. **Créer la commande**
   - Allez dans *Icinga Director → Commands → Add*.
   - **Command name :** `check_opencloud_security`
   - **Command :**
     - Installation native : `/usr/lib/nagios/plugins/check-opencloud-security` (là où vous l'avez installé ou lié, voir [Installation](reference.md#installation)).
     - Docker : `/usr/bin/docker` (voir l'exemple de [CheckCommand Docker](installation.md#using-the-docker-image-instead) pour les arguments fixes requis `run`, `--rm` et le nom de l'image).
   - **Command type :** *Plugin Check Command*.

2. **Ajouter les arguments** sur le même objet Command (onglet *Fields* → *Add argument*) :

   | Argument     | Valeur                      | Description                         |
   |:-------------|:----------------------------|:------------------------------------|
   | `--host`     | `$address$` (ou un Data Field Director personnalisé, p. ex. `$opencloud_host$`) | Nom d'hôte, IP ou URL OpenCloud, obligatoire |
   | `--port`     | Data Field `$opencloud_port$`, facultatif | Port, p. ex. `9200` |
   | `--insecure` | Data Field conditionnel `$opencloud_insecure$` (booléen), facultatif | Instance à certificat auto-signé |
   | `--proxy`    | Data Field `$opencloud_proxy$`, facultatif | Proxy HTTP/HTTPS |
   | `--debug`    | Data Field conditionnel `$opencloud_debug$` (booléen), facultatif | Sortie de débogage détaillée |

   Ce sont les plus courants. Toutes les autres options, avec leur nom de
   variable, figurent dans [`contrib/icinga2/check_opencloud_security.conf`](../../contrib/icinga2/check_opencloud_security.conf) ;
   ajoutez-les de la même manière.

   Pour chaque argument facultatif, cochez *Skip this argument on empty value*
   afin que Director omette entièrement l'option lorsque le champ n'est pas
   renseigné.

3. **Exposer les champs aux services** en définissant les *Data Fields*
   correspondants sous la commande (onglet *Fields* → *Add data field*), p. ex.
   `opencloud_host`, `opencloud_port`, `opencloud_insecure`, `opencloud_debug` -
   puis définissez leur *Data Type* (`String` ou `Boolean`) et leur *Var Filter*
   selon les besoins.

4. **Créer un Service Template**
   - *Icinga Director → Service Templates → Add*.
   - **Check command :** `check_opencloud_security`.
   - **Check interval :** `24h` est une bonne valeur par défaut ; lisez la note
     de la section [Icinga2 / Nagios](installation.md#icinga2--nagios) avant de
     descendre nettement plus bas.
   - Laissez les Data Fields vides ici, afin qu'ils puissent être renseignés par
     service ou par hôte.

5. **L'appliquer à un hôte ou à un groupe d'hôtes**
   - *Icinga Director → Services → Add* (ou une *Service Apply Rule* pour tout un groupe d'hôtes).
   - Importez le Service Template créé ci-dessus.
   - Renseignez `opencloud_host` (ou appuyez-vous sur `$address$` si vous ne l'avez pas remplacé) ainsi que les champs facultatifs voulus.
   - Déployez la configuration depuis *Icinga Director → Deployments*.

Une fois déployé, Icinga2 invoque la commande exactement comme décrit dans la
section [Icinga2 / Nagios](installation.md#icinga2--nagios), que cela aboutisse
au binaire natif ou à un `docker run` en arrière-plan.

Pour déployer les mêmes objets sans l'interface web, voir
[Déploiement automatisé avec Ansible](ansible.md).

---

[Retour à l'index de la documentation](README.md) | [Retour au README principal](../../README.md)
