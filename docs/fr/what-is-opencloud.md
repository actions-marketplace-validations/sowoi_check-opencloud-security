# Ce qu'est OpenCloud

[OpenCloud](https://opencloud.eu/) est une plateforme open source de stockage,
de synchronisation et de partage de fichiers. Ce scanner est conçu pour ses
branches de versions, sa configuration et ses points d'accès publics. Cette page
explique l'architecture qui sous-tend ces contrôles.

<!-- TOC -->
* [Ce qu'est OpenCloud](#what-is-opencloud)
  * [D'où vient OpenCloud](#where-opencloud-comes-from)
  * [Comment OpenCloud est structuré](#how-opencloud-is-structured)
  * [Pourquoi cela compte pour un scan de sécurité](#why-this-matters-for-a-security-scan)
<!-- TOC -->

## D'où vient OpenCloud {#where-opencloud-comes-from}

OpenCloud est développé comme un projet open source indépendant, avec ses
propres versions et son propre cycle de support. Son serveur écrit en Go
s'appuie sur les API CS3 et les composants Reva pour le stockage et la
collaboration. Consultez la
[documentation OpenCloud](https://docs.opencloud.eu/) pour les instructions de
déploiement et de configuration.

Certaines interfaces publiques conservent la compatibilité avec les clients
existants. Par exemple, `/status.php` porte toujours un nom de style PHP alors
qu'OpenCloud est une application Go. Sa réponse contient à la fois des valeurs
de compatibilité et la version réelle d'OpenCloud. Le [guide du point d'accès
d'état](status-php.md) explique quels champs sont utiles à un scanner.

## Comment OpenCloud est structuré {#how-opencloud-is-structured}

OpenCloud réunit des services d'authentification, d'accès aux fichiers, de
partage et son interface web. Les principaux choix de déploiement déterminent ce
qu'un scan externe peut observer :

| Composant | Point d'attention opérationnel |
|:--|:--|
| Interface web et proxy | URL publique, terminaison TLS, en-têtes de sécurité et en-têtes transmis |
| Fournisseur d'identité | Politique de connexion, enregistrement des clients, provisionnement des comptes et second facteur |
| Stockage | Organisation des données et des métadonnées, permissions, sauvegardes et restaurations testées |
| Intégrations bureautiques et d'agenda | Configuration de service distincte, identifiants et cloisonnement réseau |
| Branche de versions | Recommandations de mise à jour et période pendant laquelle des correctifs sont disponibles |

L'absence de base de données relationnelle dans le stockage central d'OpenCloud
ne signifie pas que l'ensemble du déploiement est sans état persistant. Les
fournisseurs d'identité et d'autres intégrations peuvent avoir leurs propres
bases de données et leurs propres besoins de sauvegarde.

## Pourquoi cela compte pour un scan de sécurité {#why-this-matters-for-a-security-scan}

Un point d'accès familier ne suffit pas à identifier le logiciel qui se trouve
derrière. Le scanner vérifie le produit annoncé avant d'appliquer les données de
version, les avis de sécurité et les règles de configuration d'OpenCloud. Un
produit différent est refusé plutôt que de se voir attribuer une note OpenCloud ;
voir [Dépannage](troubleshooting.md).

Le résultat décrit ce que le scanner a pu observer à l'adresse soumise. Il ne
peut pas vérifier les fichiers privés, les permissions des comptes, la
restauration des sauvegardes ni l'ensemble des politiques d'un fournisseur
d'identité. Le [guide de déploiement sécurisé](secure-deployment.md) traite de
ces tâches opérationnelles distinctes.
