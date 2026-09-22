# Dépannage

**`UNKNOWN: ... /status.php is unreachable`**
Le plugin scanne l'instance lui-même avec son scanner intégré : l'hôte de
supervision doit donc pouvoir l'atteindre directement. Vérifiez qu'il parvient à
se connecter, et rappelez-vous que le proxy d'OpenCloud écoute sur **9200**, et
non sur 443 : `--host opencloud.example.com:9200` ou `--port 9200`.

**`UNKNOWN: No OpenCloud instance found at ...`**
`/status.php` n'a pas répondu par un document d'état OpenCloud. Soit autre chose
qu'OpenCloud se trouve à cette adresse, soit un proxy inverse placé devant ne
transmet pas `/status.php`. Relancez avec `--debug` pour voir la réponse.

**`UNKNOWN: ... is not an OpenCloud instance: /status.php reports ownCloud`**
ownCloud et Nextcloud servent le même `/status.php` - OpenCloud a hérité ce
point d'accès d'eux - l'adresse a donc bien répondu, mais pas pour OpenCloud.
Leurs versions, leurs avis de sécurité et leurs valeurs de durcissement par
défaut diffèrent, et les noter selon le calendrier de versions d'OpenCloud
produirait une réponse assurée à propos du mauvais logiciel : le scan s'arrête
plutôt que de deviner. Voir [Ce qu'est OpenCloud, et en quoi il diffère
d'ownCloud et de Nextcloud](what-is-opencloud.md#why-this-matters-for-a-security-scan)
pour comprendre pourquoi les trois sont assez proches pour partager un point
d'accès, mais pas assez pour partager une note.

**Erreurs de certificat sur une instance neuve**
`opencloud init` crée un certificat auto-signé. Passez `--insecure` (la chaîne
non approuvée reste signalée, elle cesse simplement de peser sur la note), ou
placez devant l'instance un proxy inverse doté d'un vrai certificat.

**La version semble fausse (`0.1.0`)**
C'est le champ historique figé, et non la version - voir [Lire correctement la
version](scanner-checks.md#reading-the-version-correctly). Le plugin signale
`legacyVersion` lorsque l'instance n'a rien proposé de mieux ; mettre l'instance
à jour, ou laisser le plugin accéder à
`/ocs/v1.php/cloud/capabilities`, résout le problème.

**Tous les chemins sont signalés comme exposés**
Quelque chose devant l'instance répond `200` à tout, y compris au chemin que le
scanner sonde précisément pour détecter ce cas. Vérifiez la règle de repli du
proxy inverse.

**Des en-têtes de sécurité sont signalés manquants alors qu'OpenCloud les envoie**
Un proxy placé devant l'instance les supprime, ou répond avant OpenCloud.
[Proxys inverses](reverse-proxy.md) donne l'ensemble d'en-têtes recherché par ce
contrôle, détaillé pour nginx, Apache, Caddy, Traefik et HAProxy.

**Le contrôle est lent**
Le sondage des ports de débogage coûte jusqu'à `debug_port_timeout` secondes par
port sur un hôte protégé par pare-feu. Utilisez `--no-debug-ports`, abaissez
`COS_SCANNER_DEBUG_PORT_TIMEOUT`, raccourcissez la liste des ports, ou scannez
en parallèle avec `--concurrency` (voir [Accélérer le
scan](scanner-checks.md#speeding-the-scan-up)).

**`UNKNOWN` sur la vérification des mises à jour / limite de débit GitHub**
Soixante requêtes API anonymes par heure et par adresse IP sont partagées avec
tout le reste de cette adresse. Fournissez `--release-token`, ou utilisez
`--update-source bundled` / `pinned` pour éviter complètement le réseau.

**Docker : `permission denied while trying to connect to the Docker socket`**
L'utilisateur qui exécute Icinga2, cron ou systemd doit être autorisé à dialoguer
avec le démon Docker - ajoutez-le au groupe `docker`, ou exécutez le contrôle
via `sudo`, selon votre politique de sécurité.

**Rien ne se passe / aucune sortie depuis cron ou systemd**
- Les unités cron et systemd n'ont pas, par défaut, le `PATH` ni l'environnement
  d'un shell de connexion - utilisez le chemin complet vers
  `check-opencloud-security` et définissez `COS_HOST` explicitement (voir
  [Planification](scheduling.md)).
- Consultez les journaux avec
  `journalctl -u check-opencloud-security.service` (systemd) ou votre fichier de
  journal configuré (cron, voir le fichier cron d'exemple).

**`--warn-on-new` signale OK alors que quelque chose ne va manifestement pas**
C'est sa raison d'être : avec une référence, seuls les constats nouveaux ou
aggravés par rapport à la dernière exécution modifient l'état. L'état complet
reste affiché, et la ligne commençant par `Suppressed by --warn-on-new:` nomme
l'état qu'aurait eu l'exécution sans cela. Supprimez le fichier de référence pour
repartir de zéro, ou retirez l'option pour voir l'état réel à chaque exécution.
La fin de vie est la seule chose qu'il ne masque jamais. Voir [Signaler
uniquement ce qui a changé](reference.md#reporting-only-what-changed).

**`--warn-on-new needs --baseline PATH`**
Sans fichier où mémoriser l'exécution précédente, l'option signalerait
indéfiniment « rien de nouveau ». Donnez-lui un chemin accessible en écriture à
l'utilisateur de supervision, p. ex.
`/var/lib/check_opencloud/baseline.json`.

**`Baseline could not be written`**
Le répertoire n'existe pas et ne peut pas être créé, ou l'utilisateur de
supervision ne peut pas y écrire. Le verdict sur l'instance n'en est pas affecté -
cette ligne en est toute la conséquence - mais tant que ce n'est pas corrigé,
rien n'est mémorisé et `--warn-on-new` traitera chaque exécution comme la
première.

**Aucune note de `--self-update-check`**
Le résultat est mis en cache pour une journée : supprimez
`${XDG_CACHE_HOME:-~/.cache}/check-opencloud-security/pypi-version.json` pour
interroger de nouveau. L'option reste également silencieuse lorsque PyPI est
injoignable, lorsqu'un proxy la bloque, et lorsque la version installée est plus
récente que la version publiée - l'état normal d'une copie de travail du code
source. Elle ne change jamais le code de sortie.

**Référence des codes de sortie**

| Code de sortie | Signification |
|:----------|:-----------|
| `0`       | OK         |
| `1`       | WARNING    |
| `2`       | CRITICAL   |
| `3`       | UNKNOWN    |

**Toujours bloqué ?** Ouvrez un ticket avec la sortie de `--debug` (les jetons y
sont masqués), en utilisant le modèle
[wrong finding](https://github.com/sowoi/check-opencloud-security/issues/new?template=wrong_finding.yml)
si le contrôle a signalé quelque chose que vous estimez incorrect. Ne collez
jamais un nom d'hôte de production ni un identifiant dans un fil public - voir
[CODE_OF_CONDUCT.md](../../CODE_OF_CONDUCT.md).

---

[Retour à l'index de la documentation](README.md) | [Retour au README principal](../../README.md)
