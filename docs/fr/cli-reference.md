# Référence des options de la CLI

Cette page énumère chaque option du plugin, sa valeur par défaut et la variable
d'environnement correspondante. Utilisez-la pour retrouver un réglage ; le
[README principal](reference.md) explique les flux de travail et fournit des
exemples.

La priorité entre les trois façons de définir un réglage est toujours la même :
**option de ligne de commande > variable d'environnement > fichier de
configuration > valeur par défaut.** Voir [Fichier de configuration et
secrets](reference.md#configuration-file-and-secrets) pour le fichier, et
[Variables d'environnement](reference.md#environment-variables) pour les règles
de nommage.

<!-- TOC -->
* [Référence des options de la CLI](#cli-option-reference)
  * [Commande](#command)
  * [Options](#options)
  * [Réglages sans option dédiée](#settings-with-no-flag-of-their-own)
  * [Pour aller plus loin](#where-to-go-next)
<!-- TOC -->


`check-opencloud-security -h` affiche la même liste dans le terminal.

## Commande {#command}
```shell
check-opencloud-security --host <Hostname> --check-hardening
```

## Options {#options}
| Option                        | Description                                                                                                                                  | Valeur par défaut                               | Variable d'environnement        |
|:------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------|:------------------------------------------------|:--------------------------------|
| `-H, --host`                  | Adresse(s) du serveur OpenCloud : nom d'hôte, IP ou URL, éventuellement avec un port. Accepte une liste séparée par des virgules pour contrôler plusieurs hôtes en une exécution | **obligatoire**                | `COS_HOST`                      |
| `-P, --proxy`                 | Adresse du serveur proxy                                                                                                                     | *Aucune*                                        | `COS_PROXY`                     |
| `-d, --debug`                 | Expliquer la note et chaque constat ; journalisation détaillée                                                                               | *False*                                         | `COS_DEBUG`                     |
| `--profile`                   | Jeu de seuils nommé : `strict`, `ops` ou `lenient`. Détermine les réglages de jugement que vous n'avez pas définis vous-même                  | *Aucun*                                         | `COS_PROFILE`                   |
| `--policy`                    | Fichier de politique reprenant les exigences de l'organisation : `minimum_rating`, `required_hardenings`, `forbidden`. Une exigence non satisfaite est CRITICAL | *Aucun*                       | `COS_POLICY`                    |
| `-w, --warning`               | Note (0-5) à laquelle ou en dessous de laquelle le contrôle avertit                                                                          | `3` (`C`)                                       | `COS_WARNING`                   |
| `-c, --critical`              | Note (0-5) à laquelle ou en dessous de laquelle le contrôle est critique                                                                     | `1` (`E`)                                       | `COS_CRITICAL`                  |
| `--check-hardening`           | Signaler aussi les mesures de durcissement et les en-têtes de sécurité manquants                                                             | *False*                                         | `COS_CHECK_HARDENING`           |
| `--timeout`                   | Délai HTTP en secondes par requête                                                                                                           | `10`                                            | `COS_TIMEOUT`                   |
| `--port`                      | Port sur lequel écoute l'instance (le proxy d'OpenCloud utilise `9200`)                                                                      | d'après `--host`, sinon `443`                   | `COS_SCANNER_TARGET_PORT`       |
| `--scheme`                    | `https` ou `http` ; `https` bascule automatiquement vers `http` en dernier recours                                                            | `https`                                         | `COS_SCANNER_SCHEME`            |
| `--insecure`                  | Ne pas vérifier le certificat TLS de l'instance                                                                                              | *False*                                         | `COS_INSECURE`                  |
| `--ca-file`                   | Paquet d'autorités de certification PEM servant à vérifier un certificat TLS interne                                                         | *Aucun* (magasin de confiance du système)       | `COS_SCANNER_TLS_CA_FILE`       |
| `--no-extra-checks`           | Ne contrôler que le produit, la version et les en-têtes de sécurité                                                                          | *False*                                         | `COS_NO_EXTRA_CHECKS`           |
| `--no-debug-ports`            | Ne pas sonder les ports de débogage d'OpenCloud                                                                                              | *False*                                         | `COS_NO_DEBUG_PORTS`            |
| `--all-addresses`             | Contrôler aussi la version, les en-têtes, le durcissement et les comptes de démonstration sur chaque adresse résolue                         | *False*                                         | `COS_ALL_ADDRESSES`             |
| `--login-throttling`          | Envoyer six tentatives de connexion échouées pour un compte inexistant et indiquer si elles ont été limitées (jamais noté)                   | *False*                                         | `COS_LOGIN_THROTTLING`          |
| `--concurrency`               | Nombre maximal d'hôtes traités en parallèle ; un par hôte jusqu'à ce plafond                                                                 | `5`                                             | `COS_CONCURRENCY`               |
| `--format`                    | Format de sortie ponctuel : `nagios`, `prometheus`, `otlp`, `checkmk`, `summary`, `json`, `sarif` ou `junit`                                  | `nagios`                                        | `COS_FORMAT`                    |
| `--prometheus-listen-port`    | Servir `/metrics` en natif sur ce port jusqu'à l'arrêt                                                                                       | désactivé                                       | `COS_PROMETHEUS_LISTEN_PORT`    |
| `--prometheus-listen-addr`    | Adresse d'écoute de l'exportateur Prometheus natif                                                                                           | `127.0.0.1`                                     | `COS_PROMETHEUS_LISTEN_ADDR`    |
| `--scrape-interval`           | Secondes de mise en cache des résultats de l'exportateur (`0` relance un scan à chaque collecte)                                             | `60`                                            | `COS_SCRAPE_INTERVAL`           |
| `--ignore-hardening`          | Mesure de durcissement ou contrôle à accepter ; répétable, séparable par des virgules et acceptant les jokers                                | *Aucun*                                         | `COS_SCANNER_IGNORE_HARDENINGS` |
| `--waive-until`               | Accepter un contrôle jusqu'à une échéance, `MOTIF|EXPIRATION|RAISON`, répétable                                                               | *Aucun*                                         | `COS_SCANNER_TEMPORARY_WAIVERS` |
| `--release-track`             | Branche de versions suivie par cette instance : `rolling`, `production`, `lts` ou `auto`                                                      | `auto`                                          | `COS_SCANNER_RELEASE_TRACK`     |
| `--update-source`             | Provenance de la version la plus récente : `auto`, `feed`, `pinned`, `bundled`, `off`                                                        | `auto`                                          | `COS_UPDATE_SOURCE`             |
| `--release-feed`              | URL du flux des versions                                                                                                                     | API des releases GitHub de `opencloud-eu/opencloud` | `COS_RELEASES_FEED_URL`     |
| `--release-token`             | Jeton pour le flux des versions (relève la limite de débit GitHub)                                                                           | *Aucun*                                         | `COS_RELEASES_TOKEN`            |
| `--latest-version`            | Version la plus récente, indiquée explicitement ; implique `--update-source pinned`                                                          | *Aucune*                                        | `COS_RELEASES_LATEST_VERSION`   |
| `--no-update-check`           | Désactiver la vérification des mises à jour (équivaut à `--update-source off`)                                                               | *False*                                         | `COS_NO_UPDATE_CHECK`           |
| `--update-warning`            | Signaler WARNING lorsqu'une version plus récente est disponible                                                                              | *False*                                         | `COS_UPDATE_WARNING`            |
| `--eol-warning DAYS`          | Signaler WARNING lorsque la branche de versions atteint sa fin de vie sous DAYS jours (`0` désactive)                                         | `0`                                             | `COS_EOL_WARNING`               |
| `--baseline`                  | Fichier mémorisant les constats de la dernière exécution, une entrée par hôte                                                                | *Aucun*                                         | `COS_BASELINE`                  |
| `--warn-on-new`               | N'alerter que sur les constats nouveaux ou aggravés par rapport à la référence ; nécessite `--baseline`                                      | *False*                                         | `COS_WARN_ON_NEW`               |
| `--verify-remediation`        | Remesurer uniquement les identifiants de constats nommés (répétable, séparable par des virgules) au lieu d'un scan complet ; voir [Vérifier une correction](reference.md#verifying-a-fix) | *Aucun* | - |
| `--diff-format`               | Afficher les changements par rapport à la référence en `text`, `markdown`, ou en Slack Block Kit `slack`/`json`                               | `text`                                          | `COS_DIFF_FORMAT`               |
| `--self-update-check`         | Signaler qu'une version plus récente du plugin est publiée sur PyPI ; ne change jamais le code de sortie                                     | *False*                                         | `COS_SELF_UPDATE_CHECK`         |
| `--webhook-url`               | Point d'accès facultatif notifié lorsque le contrôle atteint l'état configuré                                                                | *Aucun* (désactivé)                             | `COS_WEBHOOK_URL`               |
| `--webhook-on`                | État le plus bas déclenchant le webhook (`critical`, `warning`, `unknown`, `always`)                                                         | `critical`                                      | `COS_WEBHOOK_ON`                |
| `--webhook-format`            | Forme du corps du webhook : `generic` (le JSON propre au plugin), `slack`, `discord`, `ntfy` ou `gotify`                                      | `generic`                                       | `COS_WEBHOOK_FORMAT`            |
| `--webhook-header`            | En-tête supplémentaire pour la requête du webhook, répétable                                                                                 | *Aucun*                                         | `COS_WEBHOOK_HEADERS`           |
| `--webhook-secret`            | Secret partagé ; signe chaque corps de webhook en HMAC-SHA256 dans `X-COS-Signature`                                                          | *Aucun* (non signé)                             | `COS_WEBHOOK_SECRET`            |
| `--webhook-timeout`           | Délai HTTP en secondes pour l'appel du webhook                                                                                               | `10`                                            | `COS_WEBHOOK_TIMEOUT`           |
| `--allow-private-webhooks`    | Autoriser les webhooks vers des adresses privées, de boucle locale ou link-local                                                             | *False*                                         | `COS_ALLOW_PRIVATE_WEBHOOKS`    |
| `--webhook-digest`            | Avec plusieurs cibles `--host`, envoyer un seul webhook combiné au lieu d'un par hôte                                                        | *False*                                         | `COS_WEBHOOK_DIGEST`            |
| `--retries`                   | Nombre de nouvelles tentatives en cas d'erreur réseau transitoire                                                                            | `2`                                             | `COS_RETRIES`                   |
| `--backoff-factor`            | Facteur d'attente exponentielle (secondes) entre deux tentatives                                                                             | `0.5`                                           | `COS_BACKOFF_FACTOR`            |
| `--config`                    | Chemin du fichier de configuration (`.json` en JSON, sinon YAML)                                                                             | découvert automatiquement                       | `COS_CONFIG_FILE`               |
| `--configure`                 | Demander les réglages de façon interactive, les enregistrer, puis quitter                                                                    | —                                               | —                               |
| `--upgrade-self [run\|check]` | Mettre à jour le plugin avec pipx, uv ou pip, puis quitter ; `check` affiche la commande au lieu de l'exécuter                                | `run` lorsqu'il est fourni sans valeur          | —                               |
| `--check-only`                | Uniquement avec `--upgrade-self` : autre écriture de `--upgrade-self check`                                                                  | —                                               | —                               |
| `-V, --version`               | Afficher la version installée et quitter                                                                                                     | —                                               | —                               |
| `-h, --help`                  | Afficher l'aide et quitter                                                                                                                   | —                                               | —                               |

## Réglages sans option dédiée {#settings-with-no-flag-of-their-own}

La fenêtre d'expiration TLS, la liste des ports de débogage et les sources
d'avis de sécurité n'ont pas d'option de ligne de commande. Ils se configurent
par le [fichier de configuration](reference.md#configuration-file-and-secrets)
ou par leurs variables d'environnement `COS_SCANNER_*`, et
[`config/check-opencloud-security.example.yml`](../../config/check-opencloud-security.example.yml)
les énumère toutes avec un commentaire.

## Pour aller plus loin {#where-to-go-next}

| Page | Pourquoi |
|:-----|:----|
| [README principal](reference.md) | À quoi sert chacune de ces options, avec des exemples détaillés |
| [Fichier de configuration et secrets](reference.md#configuration-file-and-secrets) | Définir les mêmes réglages dans un fichier |
| [Sortie exploitable par une machine](output-formats.md) | `--format json`, `sarif` et `junit` en détail |
| [Checkmk](checkmk.md) | `--format checkmk`, et l'exécution du plugin depuis un serveur Checkmk |
| [Contrôler un parc d'instances](many-instances.md) | `--host` avec de nombreuses cibles, et un fichier de configuration par instance |
| [Dépannage](troubleshooting.md) | La référence des codes de sortie |
