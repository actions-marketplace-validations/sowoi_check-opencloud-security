# Secrets dans la configuration

Gardez les identifiants hors du fichier de configuration en désignant leur source
plutôt que leur valeur. Les jetons GitHub, les URL de webhook et les jetons de
service peuvent être lus depuis un fichier, une variable d'environnement ou une
commande, au moment où ils sont nécessaires.

Le fichier lui-même, l'endroit où il est recherché et la correspondance entre ses
clés et les variables d'environnement sont décrits dans
[Fichier de configuration et secrets](reference.md#configuration-file-and-secrets) ;
`config/check-opencloud-security.example.yml` en est un exemple entièrement
commenté.

<!-- TOC -->
* [Secrets dans la configuration](#secrets-in-the-configuration)
  * [Formes de référence](#reference-forms)
  * [Hors d'un conteneur](#outside-a-container)
<!-- TOC -->


## Formes de référence {#reference-forms}

Quatre préfixes sont reconnus, partout où une valeur est attendue :

| Référence              | Se résout en                                                                                  |
|:-----------------------|:----------------------------------------------------------------------------------------------|
| `secret://nom`         | `<secrets.dir>/nom`, c'est-à-dire `/run/secrets/nom` pour les secrets Docker et Kubernetes     |
| `file:///chemin/vers/fichier` | Le contenu de ce fichier                                                                 |
| `env://VARIABLE`       | La valeur de cette variable d'environnement                                                   |
| `exec://commande --arg` | La sortie standard de cette commande (nécessite `secrets.allow_exec: true`)                  |

Vous pouvez aussi ajouter `_file` à n'importe quelle clé ou variable :
`COS_RELEASES_TOKEN_FILE=/run/secrets/token` ou `token_file: /run/secrets/token`.
Les sauts de ligne finaux sont supprimés, si bien que `echo secret > fichier`
fonctionne comme prévu.

## Hors d'un conteneur {#outside-a-container}

`secret://nom` cherche sous `secrets.dir` (`COS_SECRETS_DIR`), dont la valeur par
défaut est `/run/secrets` - exactement là où Docker et Kubernetes montent leurs
secrets. Hors d'un conteneur, faites-le pointer vers votre propre répertoire :

```shell
mkdir -p /etc/check-opencloud-security/secrets
printf '%s' '<github-token>' > /etc/check-opencloud-security/secrets/releases_token
chmod 600 /etc/check-opencloud-security/secrets/*

export COS_SECRETS_DIR=/etc/check-opencloud-security/secrets
check-opencloud-security --host opencloud.example.com \
  --release-token 'secret://releases_token'
```

Le dépôt fournit des modèles pour les deux fichiers dans
[`secrets/`](../../secrets/README.md) ; copiez-les et remplacez les valeurs
d'exemple.
