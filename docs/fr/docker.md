# Docker {#scanning-from-the-command-line-in-one-line}

Lancez le scanner sur votre machine avec l’image Docker publiée. Il utilise le même
scanner que le [service web](../webapp.md), se connecte directement à votre instance et n’est
pas soumis aux limites du site. Vous avez besoin de Docker, mais d’aucun compte sur ce service.

```shell
docker run --rm --entrypoint check-opencloud-security \
  okxo/opencloud-scanner:latest --host opencloud.example.com
```

La commande affiche la même sortie que celle reçue par un système de supervision :

```text
OK: Server is up to date. No known vulnerabilities.
OpenCloud 7.2.3 on opencloud.example.com, rating: A+, last scanned: 2026-08-25 09:41:12
Release lifecycle: 7.2 (production, track detected), current release
```

Le code de sortie suit la convention Nagios : `0` OK, `1` WARNING, `2` CRITICAL,
`3` UNKNOWN. Vous pouvez donc utiliser cette commande dans un script, un pipeline
ou une tâche cron.

> **Marques déposées.** Ce projet est indépendant. Il n’est ni affilié à OpenCloud
> GmbH, ni approuvé ou pris en charge par cette société. « OpenCloud » et les marques
> associées appartiennent à leurs propriétaires respectifs. Elles servent ici
> uniquement à identifier le logiciel analysé.

## Contenu de l’image {#what-the-image-is}

L’image [`okxo/opencloud-scanner`](https://hub.docker.com/r/okxo/opencloud-scanner)
est construite à partir de ce dépôt et contient deux commandes :

| Commande | Fonction |
|:--|:--|
| `check-opencloud-security` | Plugin Nagios/Icinga : état, données de performance et code de sortie |
| `check-opencloud-scanner` | Scanner autonome : résultat complet en JSON ou service HTTP |

Par défaut, l’image démarre l’application web. Chaque exemple utilise donc
`--entrypoint`. Pour conserver le même comportement lors des prochaines exécutions,
choisissez une version précise, comme `okxo/opencloud-scanner:1.9`, au lieu de `latest`.

## Obtenir le résultat en JSON {#the-same-scan-as-json}

Ce document contient toutes les données affichées par l’interface web : note,
cycle de vie de la version, avis de sécurité, contrôles et mesures correctives.

```shell
docker run --rm --entrypoint check-opencloud-scanner \
  okxo/opencloud-scanner:latest scan opencloud.example.com
```

Utilisez `jq` pour sélectionner les champs utiles :

```shell
docker run --rm --entrypoint check-opencloud-scanner \
  okxo/opencloud-scanner:latest scan opencloud.example.com \
  | jq '{rating, version, addresses, failed: [.extraChecks[] | select(.passed | not) | .id]}'
```

`addresses` contient les adresses IPv4 et IPv6 obtenues lors de la résolution du nom.
La page de résultat les affiche aussi sous **Resolved to**. Vérifiez-les si le résultat
vous surprend : le nom peut encore pointer vers une ancienne adresse.

## Variantes utiles {#useful-variations}

Afficher l’explication de chaque constat :

```shell
docker run --rm --entrypoint check-opencloud-security \
  okxo/opencloud-scanner:latest --host opencloud.example.com --debug
```

Accepter un constat, comme avec les cases à cocher du site :

```shell
docker run --rm --entrypoint check-opencloud-security \
  okxo/opencloud-scanner:latest --host opencloud.example.com \
  --ignore-hardening basicAuthDisabled
```

Évaluer la version selon un canal de publication précis au lieu du canal déduit
par le scanner :

```shell
docker run --rm --entrypoint check-opencloud-security \
  okxo/opencloud-scanner:latest --host opencloud.example.com \
  --release-track lts
```

Analyser une instance privée, par exemple un serveur de préproduction sur votre réseau
ou un nom connu uniquement de votre résolveur DNS :

```shell
docker run --rm --network host --entrypoint check-opencloud-security \
  okxo/opencloud-scanner:latest --host opencloud.internal.example.com
```

Le service hébergé refuse les adresses privées. Une analyse lancée sur votre propre
machine peut les atteindre.

Utiliser des variables d’environnement facilite la configuration d’une liste d’hôtes.
Chaque option possède une variable `COS_`, décrite dans le
[README principal](../README.md#environment-variables) :

```shell
docker run --rm -e COS_HOST=opencloud.example.com \
  --entrypoint check-opencloud-security okxo/opencloud-scanner:latest
```

Désactiver la recherche de mises à jour si la machine n’a pas accès à Internet ou
si vous ne souhaitez pas contacter le flux des versions :

```shell
docker run --rm --entrypoint check-opencloud-security \
  okxo/opencloud-scanner:latest --host opencloud.example.com --no-update-check
```

## Raccourcir la commande {#make-it-shorter}

Pour un usage fréquent, ajoutez une fonction à votre shell :

```shell
# ~/.bashrc or ~/.zshrc
opencloud-scan() {
  docker run --rm --entrypoint check-opencloud-security \
    okxo/opencloud-scanner:latest --host "$1" "${@:2}"
}
```

```shell
opencloud-scan opencloud.example.com --debug
```

## Sans Docker {#without-docker}

Le plugin est un programme Python publié sur PyPI. Vous pouvez l’exécuter avec
[`uv`](https://docs.astral.sh/uv/) ou `pipx`, sans conteneur :

```shell
uvx --from check-opencloud-security check-opencloud-security \
  --host opencloud.example.com
```

```shell
pipx run --spec check-opencloud-security check-opencloud-security \
  --host opencloud.example.com
```

## Pour aller plus loin {#where-to-go-next}

- [README principal](../README.md) : options et signification des contrôles.
- [Planification](scheduling.md) : exécution périodique avec systemd ou cron.
- [Analyse en CI](ci.md) : conditionner un pipeline à un champ du résultat.
- [Parc d’instances](many-instances.md) : un fichier par instance et des alertes sur les changements.
- [Service d’analyse public](../webapp.md) : héberger vous-même l’interface web.
