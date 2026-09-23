# Surface d’exposition publique {#exposed-paths-and-debug-endpoints-what-this-scanner-checks-and-why}

OpenCloud ne publie normalement ni index de répertoire, ni fichiers de déploiement,
ni clés privées, ni base d’identités par HTTP. Ces contrôles recherchent les fichiers
exposés par un serveur web ou un proxy inverse, ainsi que les interfaces de débogage
qui devraient rester privées.

Avant ces contrôles, le scanner demande un chemin inexistant et mémorise la réponse.
L’interface OpenCloud est une application monopage : elle renvoie sa page principale
avec le statut HTTP `200` même pour un chemin inconnu. Le seul statut `200` ne prouve
donc aucune exposition. Pour tous les contrôles ci-dessous, la réponse doit aussi
différer de cette réponse de référence.

## 1. Index de répertoire : `directoryListing` {#1-is-a-directory-index-being-served-directorylisting}

Le serveur a renvoyé une page de type `Index of /`. OpenCloud n’en produit jamais.
Un serveur web dessert donc directement le répertoire de déploiement. Cette même
configuration peut exposer les fichiers recherchés par le contrôle suivant.

**Correction :** cessez de servir le répertoire comme contenu statique. Configurez
le serveur web comme proxy inverse vers l’adresse d’OpenCloud. Désactivez également
l’indexation des répertoires : `autoindex off` pour Nginx, `Options -Indexes` pour
Apache. Voir les [proxys inverses](reverse-proxy.md).

## 2. Fichiers de déploiement accessibles : `exposed:<path>` {#2-is-a-specific-deployment-file-readable-exposedpath}

Le scanner demande une liste fixe de chemins qui ne doivent jamais être accessibles par HTTP :

| Chemin | Gravité |
|:--|:--|
| `/opencloud.yaml` | critical |
| `/config/opencloud.yaml` | critical |
| `/.opencloud/config/opencloud.yaml` | critical |
| `/proxy/server.key` | critical |
| `/idm/opencloud.boltdb` | critical |
| `/.env` | critical |
| `/docker-compose.yml` | high |
| `/storage/users/` | high |
| `/.git/config` | high |

`opencloud.yaml` et `.env` contiennent des paramètres et des secrets,
`proxy/server.key` contient la clé privée TLS et `idm/opencloud.boltdb` contient
les identités. Une réponse positive indique que le répertoire de déploiement, ou
sa copie Git, est accessible, comme pour `directoryListing`.

**Correction :** configurez un proxy vers OpenCloud au lieu d’exposer ses fichiers.
Vérifiez ensuite que chaque chemin signalé répond `404`. Considérez les données
accessibles comme divulguées : remplacez la clé TLS et les identifiants présents
dans `opencloud.yaml` ou `.env`. Examinez les comptes créés pendant l’exposition
de la base d’identités.

## 3. Interfaces de débogage publiques : `debugEndpoint:<path>` {#3-is-a-debug-endpoint-publicly-readable-debugendpointpath}

Le scanner vérifie `/metrics`, `/config` et `/debug/pprof/` sur l’adresse publique.
Ces chemins doivent rester sur l’interface de débogage locale d’OpenCloud.
`/metrics` et `/config` révèlent la configuration et l’état interne. Lorsqu’il est
activé, `/debug/pprof/` permet de déclencher un profilage du processus : il divulgue
des informations et peut consommer des ressources importantes.

**Correction :** ne publiez pas les chemins `/debug` via le proxy. Conservez
`127.0.0.1` comme adresse d’écoute, valeur par défaut de `OC_DEBUG_ADDR` et des
variables `*_DEBUG_ADDR` propres aux services. Si un collecteur de métriques doit
y accéder, utilisez le réseau interne.

## 4. Ports de débogage accessibles : `debugPort:<port>` {#4-is-a-service-debug-port-reachable-debugportport}

Chaque service OpenCloud possède aussi un port de débogage, lié par défaut à
`127.0.0.1`. Le scanner tente une connexion directe aux ports par défaut ou à ceux
définis dans `scanner.debug_ports`. Un port accessible a été publié, généralement
par une redirection de port de conteneur.

**Correction :** supprimez cette redirection et conservez l’écoute sur `127.0.0.1`.
Si nécessaire, accédez aux ports depuis le réseau interne.

## 5. Accès direct au serveur : `backendPortClosed` {#5-is-the-backend-reachable-directly-bypassing-the-proxy-backendportclosed}

Le port `9200` dessert OpenCloud sans les protections ajoutées par le proxy inverse.
Un client qui l’atteint directement contourne la terminaison TLS, les en-têtes de
sécurité et les limites de débit du proxy. Les contrôles réussis sur l’adresse
publique ne garantissent donc pas la protection de cet accès direct.

**Correction :** supprimez la publication du port `9200`. Liez le serveur à l’interface
locale ou au réseau privé des conteneurs, pour que seul le proxy puisse le joindre.

## 6. Lecture depuis une autre origine : `corsOriginRestricted` {#6-who-may-read-a-response-cross-origin-corsoriginrestricted}

Ce contrôle vérifie quels sites peuvent lire les réponses de l’instance dans un
navigateur. La politique de même origine empêche normalement une page sur
`attacker.example` de lire une réponse d’OpenCloud. Le mécanisme CORS
(Cross-Origin Resource Sharing) permet au serveur d’autoriser certaines origines.

Par défaut, [`OC_CORS_ALLOW_ORIGINS` vaut `*` et `OC_CORS_ALLOW_CREDENTIALS` vaut
`true`](https://docs.opencloud.eu/docs/dev/server/services/graph/environment-variables).
Avec cette combinaison, un composant intermédiaire renvoie souvent la valeur
`Origin` reçue au lieu du caractère `*`. Cela contourne le refus du navigateur
d’accepter un joker avec des identifiants.

Le scanner demande `/graph/v1.0/me` avec l’origine
`https://cors-probe.check-opencloud-security.invalid`. Le suffixe `.invalid`, réservé
par la RFC 2606, ne peut pas être résolu. Il examine ensuite la réponse :

| Réponse de l’instance | Verdict |
|:--|:--|
| Origine du test renvoyée avec `Access-Control-Allow-Credentials: true` | **critical** : tout site peut faire envoyer la session OpenCloud du visiteur et lire la réponse |
| `Access-Control-Allow-Origin: null`, avec identifiants | **critical** : une iframe isolée peut envoyer l’origine `null` |
| Origine du test renvoyée sans identifiants | **medium** : expose les données déjà accessibles sans authentification |
| Joker `*`, avec ou sans identifiants | **medium** : le navigateur refuse la combinaison avec identifiants |
| Une autre origine précise | **Réussite** : configuration attendue |
| Aucun en-tête `Access-Control-Allow-Origin` | **Réussite** |

**Correction :** limitez `OC_CORS_ALLOW_ORIGINS` aux origines qui doivent appeler
l’API : interface web et éventuelles applications bureautiques ou clientes hébergées
ailleurs. Définissez `OC_CORS_ALLOW_CREDENTIALS=false`, sauf si l’une de ces applications
doit envoyer une session. Les variables propres aux services, comme
`GRAPH_CORS_ALLOW_ORIGINS` et `OCS_CORS_ALLOW_ORIGINS`, remplacent le réglage commun
lorsqu’un service nécessite une liste différente.

## 7. Renvoi de la requête : `traceMethodDisabled` {#7-is-the-request-echoed-back-tracemethoddisabled}

`TRACE` demande au serveur de renvoyer la requête, en-têtes compris, dans le corps
de la réponse. Les cookies, l’en-tête `Authorization` ou les en-têtes ajoutés par
le proxy peuvent alors devenir du texte lisible par un script qui ne pouvait pas
les lire directement.

OpenCloud n’implémente pas `TRACE`. Si l’instance y répond, c’est le proxy ou le
serveur applicatif placé devant elle qui le fait. Le statut `200` ne suffit pas :
le corps doit ressembler à la requête envoyée, avec `Content-Type: message/http`
ou la ligne de requête reproduite.

La RFC 9110 définit `TRACE` comme une méthode sûre : elle renvoie la requête sans
modifier l’état du serveur. Le plugin peut donc l’utiliser lors de contrôles réguliers.

**Correction :** refusez `TRACE` dans le composant placé devant l’instance.
Pour Apache, utilisez `TraceEnable off`. nginx répond déjà `405`, sauf si une règle
transmet toutes les méthodes au serveur. Avec Traefik et Caddy, limitez les méthodes
transmises.

## 8. Console d’un service associé : `companionAdminConsole` {#8-is-a-second-services-console-published-beside-the-instance-companionadminconsole}

Un éditeur WOPI, comme Collabora Online ou OnlyOffice, peut être publié sur la même
origine qu’OpenCloud lorsque le proxy lui transmet `/hosting` et `/browser`.
Sa console d’administration affiche les sessions documentaires, leurs utilisateurs
et la configuration du serveur. Elle peut aussi fermer les sessions. Un seul mot
de passe partagé la protège, sans limitation de débit devant elle.

Le scanner demande `/hosting/discovery` et exige l’élément racine `wopi-discovery`
défini par WOPI. Le statut HTTP seul ne suffit pas, car OpenCloud renvoie sa page
HTML pour les chemins inconnus. Le scanner ne demande le chemin de la console
qu’après avoir reçu ce document.

Le contrôle `companionEditorHttps` examine les adresses d’éditeur publiées dans le
même document. Une adresse `http://` transmet sans chiffrement le document et le
jeton de session. Un navigateur sur une page HTTPS bloque également cette iframe.

**Si aucun éditeur n’est publié sur cette origine, les deux contrôles sont absents.**
Ils ne sont pas déclarés réussis. La plupart des déploiements utilisent un autre
hôte pour l’éditeur. Le scanner ne suit pas cet hôte depuis le document de découverte :
l’instance analysée pourrait ainsi choisir la prochaine adresse contactée.
Lancez une analyse distincte de cet hôte. Voir
[ADR 0036](../../adr/0036-a-companion-service-is-probed-only-where-the-scan-was-pointed.md).

**Correction :** bloquez le chemin de la console dans le proxy qui publie l’éditeur.
Seuls les chemins nécessaires à l’édition doivent être publics. Un mot de passe de
console offre une protection plus faible, car il protège à lui seul toutes les
sessions documentaires du serveur.

## Gravité et effet sur la note {#severity-and-rating-impact}

Tous ces contrôles figurent dans `extraChecks`. Ils s’exécutent à chaque analyse
et peuvent plafonner la note : `D` pour une gravité `critical`, `C` pour `high`.
Voir le [tableau des contrôles supplémentaires](scanner-checks.md#what-the-scanner-checks).
Ils ne dépendent pas de `--check-hardening` : un fichier de configuration exposé
ou un port de débogage ouvert est toujours signalé.
