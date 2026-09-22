# Content-Security-Policy : ce que ce scanner vérifie, et pourquoi

Une Content-Security-Policy (CSP) indique au navigateur quelles sources sont
autorisées à fournir des scripts, des styles, des cadres et d'autres contenus.
Une politique bien configurée peut limiter les effets d'un contenu ou de scripts
injectés. Le scanner vérifie si l'en-tête est présent et si sa politique
relative aux scripts autorise certaines formes d'exécution dangereuse.

<!-- TOC -->
* [Content-Security-Policy : ce que ce scanner vérifie, et pourquoi](#content-security-policy-what-this-scanner-checks-and-why)
  * [1. L'en-tête est-il seulement présent](#1-is-the-header-present-at-all)
  * [2. La politique est-elle réellement restrictive : `cspWithoutUnsafeInline`](#2-is-the-policy-actually-restrictive-cspwithoutunsafeinline)
  * [Comment corriger](#fixing-it)
  * [Gravité et effet sur la note](#severity-and-rating-impact)
<!-- TOC -->


## 1. L'en-tête est-il seulement présent {#1-is-the-header-present-at-all}

`Content-Security-Policy` fait partie des huit en-têtes contrôlés sous
`setup.headers` (avec `--check-hardening`, ou systématiquement dans le résultat
web). Son absence constitue à elle seule un constat :

> Rien ne restreint les origines depuis lesquelles scripts, styles et cadres
> peuvent être chargés.

OpenCloud fournit une politique par défaut : sur une instance en production, un
en-tête manquant signifie donc presque toujours qu'un proxy inverse placé devant
elle l'a supprimé, et non qu'OpenCloud a omis de l'envoyer - voir
[Proxys inverses](reverse-proxy.md) pour l'ensemble d'en-têtes recherché par ce
contrôle, détaillé pour nginx, Apache, Caddy, Traefik et HAProxy.

## 2. La politique est-elle réellement restrictive : `cspWithoutUnsafeInline` {#2-is-the-policy-actually-restrictive-cspwithoutunsafeinline}

Avoir *un* en-tête CSP n'est pas la même chose qu'en avoir un utile. Le contrôle
de durcissement `cspWithoutUnsafeInline` lit la directive `script-src` (à défaut
`default-src` lorsque `script-src` est absente) et échoue lorsqu'elle contient
`unsafe-inline` ou `unsafe-eval` :

- **`unsafe-inline`** permet à du balisage injecté ou à un gestionnaire
  d'événement de s'exécuter directement - précisément ce qu'une CSP existe pour
  empêcher.
- **`unsafe-eval`** permet à un mécanisme déjà présent dans le code chargé de
  transformer une entrée contrôlée par un attaquant en code, via `eval()` ou le
  constructeur `Function`.

**Ce contrôle échoue sur une instance OpenCloud d'origine, non modifiée.** Le
fichier `csp.yaml` par défaut contient `unsafe-inline` dans `script-src` et
`style-src`, car l'interface web dépend actuellement de scripts et de styles en
ligne. Le contrôle le signale plutôt que de l'excuser, mais y remédier suppose
de fournir une CSP personnalisée et de tester l'interface avec elle : ce n'est
pas en soi la preuve d'une mauvaise configuration, contrairement à la plupart
des autres constats.

Une exception est prévue : une politique qui associe `unsafe-inline` à un nonce
ou à une empreinte (le schéma de déploiement standard `strict-dynamic`) ne fait
**pas** échouer ce contrôle. Tout navigateur qui comprend les nonces ignore
`unsafe-inline` lorsqu'un nonce est présent ; le mot-clé n'est donc qu'une
solution de repli pour les navigateurs trop anciens pour comprendre le nonce, et
le conserver sous cette forme est la méthode recommandée par les organismes de
normalisation pour prendre en charge anciens et nouveaux navigateurs avec le
même en-tête.

## Comment corriger {#fixing-it}

Faites pointer `PROXY_CSP_CONFIG_FILE_LOCATION` vers un `csp.yaml` dépourvu
d'`unsafe-inline` et d'`unsafe-eval`, ou
`PROXY_CSP_CONFIG_FILE_OVERRIDE_LOCATION` pour remplacer entièrement la
politique par défaut. Pour continuer à prendre en charge les navigateurs plus
anciens, adoptez une politique fondée sur des nonces ou des empreintes avec
`strict-dynamic` plutôt que de supprimer purement et simplement
`unsafe-inline`. Testez d'abord : l'interface web s'appuie actuellement sur des
scripts et des styles en ligne, une politique stricte risque donc de casser
l'interface ainsi que tout service bureautique ou fournisseur d'identité
connecté avant d'avoir été ajustée.

Référence :
[variables d'environnement du service proxy d'OpenCloud](https://docs.opencloud.eu/docs/dev/server/services/proxy/environment-variables).

## Gravité et effet sur la note {#severity-and-rating-impact}

`cspWithoutUnsafeInline` est un indicateur de durcissement, signalé uniquement
avec `--check-hardening` (ou systématiquement dans le résultat web), et il ne
plafonne pas à lui seul la note comme le fait une entrée `extraChecks` en échec -
voir [Contrôles de durcissement](reference.md#hardening-checks) pour la
différence entre indicateurs de durcissement et constats plafonnants. Le constat
d'en-tête manquant est, lui, un contrôle supplémentaire `header:` et plafonne
bien la note lorsque `--check-hardening` est activé - voir le tableau des
contrôles supplémentaires dans
[le README principal](scanner-checks.md#what-the-scanner-checks).
