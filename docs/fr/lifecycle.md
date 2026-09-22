# Divulgation de la version et du cycle de vie : ce que ce scanner vérifie, et pourquoi

Ces contrôles déterminent si le scanner connaît la version en cours d'exécution
et si l'instance la publie à des endroits inutiles. Ils complètent la
[détection de fin de vie](reference.md#end-of-life-detection) et la
vérification des mises à jour, qui ont toutes deux besoin d'un numéro de version
fiable.

<!-- TOC -->
* [Divulgation de la version et du cycle de vie : ce que ce scanner vérifie, et pourquoi](#version-and-lifecycle-disclosure-what-this-scanner-checks-and-why)
  * [1. La version en cours a-t-elle pu être déterminée : `versionDetection`](#1-could-the-running-version-be-determined-at-all-versiondetection)
  * [2. Un en-tête de réponse publie-t-il la version : `versionDisclosure:<header>`](#2-does-a-response-header-publish-the-version-versiondisclosureheader)
  * [3. Le document webfinger publie-t-il la version : `webfingerVersionDisclosure`](#3-does-the-webfinger-document-publish-the-version-webfingerversiondisclosure)
  * [Gravité et effet sur la note](#severity-and-rating-impact)
<!-- TOC -->


## 1. La version en cours a-t-elle pu être déterminée : `versionDetection` {#1-could-the-running-version-be-determined-at-all-versiondetection}

`/status.php` renvoie jusqu'à trois champs ayant l'apparence d'une version, et
un seul d'entre eux correspond à la version réelle - voir [Lire correctement la
version](scanner-checks.md#reading-the-version-correctly) pour savoir ce que
sont les deux autres et pourquoi ils existent, et [Pourquoi OpenCloud répond
encore à `/status.php`](status-php.md) pour l'origine de ce point d'accès et de
ses champs figés. Ce contrôle échoue lorsque `productversion` est absent et que
seuls les champs de compatibilité historiques `version`/`versionstring` ont été
renvoyés.

Sans la version réelle, le scanner ne peut ni faire correspondre les avis de
sécurité ni déterminer le statut de support et les mises à jour disponibles. Ces
contrôles ne sont pas exécutés lorsque la version manque, et leurs résultats
restent donc inconnus.

**En cas d'échec :** vérifiez si un élément placé devant l'instance réécrit ou
supprime des champs de la réponse `/status.php`, et si la version est
suffisamment ancienne pour être antérieure à la publication même de
`productversion`. Tant qu'une version réelle n'est pas renvoyée, considérez
toute partie du résultat dépendant de la version comme inconnue plutôt que comme
saine.

## 2. Un en-tête de réponse publie-t-il la version : `versionDisclosure:<header>` {#2-does-a-response-header-publish-the-version-versiondisclosureheader}

Les en-têtes de réponse `Server` et `X-Powered-By` sont examinés chacun à la
recherche de tout ce qui ressemble à un numéro de version (un chiffre, un point,
un autre chiffre). Publier un numéro de version n'est pas en soi une
vulnérabilité, mais cela aide les attaquants à repérer les vulnérabilités
connues à cibler. Les deux constats sont classés `low`.

**Correction :** supprimez ou neutralisez l'en-tête dans le proxy inverse -
`server_tokens off` sous Nginx, `ServerTokens Prod` sous Apache - ou retirez-le
purement et simplement. Voir [Proxys inverses](reverse-proxy.md) pour la
directive équivalente sous Caddy, Traefik et HAProxy.

## 3. Le document webfinger publie-t-il la version : `webfingerVersionDisclosure` {#3-does-the-webfinger-document-publish-the-version-webfingerversiondisclosure}

`/.well-known/webfinger` est interrogé sans authentification (comme le ferait
n'importe quel client de fédération) et sa réponse est examinée à la recherche
de la version en cours, de la même façon que les deux en-têtes ci-dessus. Il
s'agit de la même catégorie de constat que `versionDisclosure` - une divulgation
d'information de faible gravité, non une vulnérabilité - simplement lue dans un
document JSON plutôt que dans un en-tête.

**Correction :** supprimez la version de la réponse webfinger dans le proxy
inverse, ou acceptez cette divulgation et donnez plutôt la priorité au maintien
à jour de l'instance : la version ne présente d'intérêt comme renseignement que
tant qu'un avis de sécurité connu visant précisément cette version n'est pas
corrigé.

## Gravité et effet sur la note {#severity-and-rating-impact}

Les trois sont des `extraChecks`, signalés et plafonnant la note à chaque scan -
`versionDetection` en `medium` (plafonne la note à `A`), les deux contrôles de
divulgation en `low` (la plafonnent à `A+`) - voir le tableau des contrôles
supplémentaires dans [le README principal](scanner-checks.md#what-the-scanner-checks).
Aucun ne nécessite `--check-hardening`, et aucun ne se confond avec la
[note de fin de vie](reference.md#end-of-life-detection) : une version à jour
mais entièrement divulguée et une version en fin de vie mais bien dissimulée
sont jugées sur des axes totalement différents.
