# Attributs de cookie : ce que ce scanner vérifie, et pourquoi

Le scanner examine les en-têtes `Set-Cookie` des réponses publiques à la
recherche de quatre protections de cookie. Il lit les attributs définis par
OpenCloud ou par son proxy inverse et ne conserve aucune valeur de cookie.

Si la réponse ne définit aucun cookie, ces contrôles sont omis. Un contrôle non
effectué n'est pas signalé comme réussi.

<!-- TOC -->
* [Attributs de cookie : ce que ce scanner vérifie, et pourquoi](#cookie-attributes-what-this-scanner-checks-and-why)
  * [1. Le cookie exige-t-il HTTPS : `cookieSecure`](#1-does-the-cookie-require-https-cookiesecure)
  * [2. Les scripts de la page peuvent-ils lire le cookie : `cookieHttpOnly`](#2-can-page-scripts-read-the-cookie-cookiehttponly)
  * [3. Le cookie est-il envoyé lors de requêtes intersites : `cookieSameSite`](#3-is-the-cookie-sent-on-cross-site-requests-cookiesamesite)
  * [4. Le nom du cookie porte-t-il un préfixe : `cookiePrefix`](#4-does-the-cookie-name-carry-a-prefix-cookieprefix)
  * [Gravité et effet sur la note](#severity-and-rating-impact)
<!-- TOC -->


## 1. Le cookie exige-t-il HTTPS : `cookieSecure` {#1-does-the-cookie-require-https-cookiesecure}

Un cookie dépourvu de `Secure` sera transmis sur une connexion HTTP en clair dès
que le navigateur en établira une vers le même hôte - un lien `http://` égaré,
une redirection mixte ou un portail captif suffisent. Dès lors, le cookie
traverse le réseau en clair et peut être rejoué par quiconque l'a vu passer.

**Correction :** activez `Secure` sur chaque cookie émis par le proxy inverse ou
par l'application. Si l'instance termine le TLS dans un proxy inverse, il s'agit
généralement du cookie de session ou du cookie CSRF du proxy lui-même plutôt que
d'un cookie posé par OpenCloud - voir [Proxys inverses](reverse-proxy.md) pour
l'ensemble d'en-têtes que lit ce contrôle.

## 2. Les scripts de la page peuvent-ils lire le cookie : `cookieHttpOnly` {#2-can-page-scripts-read-the-cookie-cookiehttponly}

Sans `HttpOnly`, les scripts exécutés dans la page peuvent lire un cookie via
`document.cookie`. Pour les cookies de session, cela aggrave les conséquences
d'un script injecté. Certaines conceptions de jeton CSRF exigent délibérément un
accès depuis JavaScript : évaluez donc l'usage du cookie avant de modifier
l'attribut.

**Correction :** utilisez `HttpOnly` pour les cookies que les scripts n'ont pas
besoin de lire, en particulier les cookies de session. Vérifiez les besoins de
l'application avant d'appliquer l'attribut à tous les cookies.

## 3. Le cookie est-il envoyé lors de requêtes intersites : `cookieSameSite` {#3-is-the-cookie-sent-on-cross-site-requests-cookiesamesite}

`SameSite` détermine quand le navigateur inclut un cookie dans les requêtes
intersites. De nombreux navigateurs actuels appliquent une valeur par défaut
proche de `Lax` lorsque l'attribut est absent, mais une valeur explicite rend le
comportement voulu sans ambiguïté. Le contrôle signale l'absence de l'attribut ;
il ne démontre pas qu'une attaque CSRF est possible.

**Correction :** définissez `SameSite=Lax` ou `SameSite=Strict`, sauf si un flux
intersite documenté nécessite réellement `SameSite=None` (qui exige en outre
`Secure`). `Lax` convient à la plupart des cookies de session : il autorise
encore une navigation de premier niveau, par exemple l'ouverture d'un lien
partagé, en arrivant déjà connecté.

## 4. Le nom du cookie porte-t-il un préfixe : `cookiePrefix` {#4-does-the-cookie-name-carry-a-prefix-cookieprefix}

Les préfixes de nom de cookie ajoutent des règles au moment de poser un cookie.
Les navigateurs qui les prennent en charge exigent que les cookies `__Secure-`
soient posés de façon sécurisée avec `Secure`. `__Host-` impose en plus `Path=/`
et interdit `Domain`, liant ainsi le cookie à l'hôte qui l'a posé. Cela
contribue à empêcher un sous-domaine voisin de poser un cookie concurrent sur le
domaine parent. En revanche, cela n'isole pas les cookies par port.

Le contrôle signale deux échecs différents, car ils ont une seule et même
correction :

- **Un cookie qui revendique un préfixe dont il ne respecte pas les règles** -
  `__Host-` accompagné d'un attribut `Domain`, avec un `Path` autre que `/`, ou
  sans `Secure`. Les navigateurs concernés rejettent un tel cookie : il ne
  s'agit donc pas d'une faiblesse théorique, car la session qu'il porte cesse
  silencieusement de fonctionner. Le détail indique quelle règle a été enfreinte.
- **Aucun cookie observé ne porte de préfixe**, ce qui est l'état ordinaire
  d'une instance que personne n'a modifiée.

**Correction :** renommez le cookie de session en `__Host-<nom>` et posez-le
avec `Secure`, `Path=/` et sans attribut `Domain` - ou en `__Secure-<nom>`
lorsqu'il doit réellement être partagé entre sous-domaines. Lorsque le cookie
provient d'un proxy inverse ou d'un fournisseur d'identité plutôt que
d'OpenCloud, renommez-le à cet endroit.

## Gravité et effet sur la note {#severity-and-rating-impact}

Les quatre sont des `extraChecks`, signalés dès qu'un cookie est observé -
`cookieSecure` en `high`, `cookieHttpOnly` en `medium`, `cookieSameSite` et
`cookiePrefix` en `low` - et chacun plafonne la note à lui seul, comme tout
autre contrôle supplémentaire en échec (`high` -> `C`, `medium` -> `A`,
`low` -> `A+` ; voir le tableau des contrôles supplémentaires dans
[le README principal](scanner-checks.md#what-the-scanner-checks)). Définissez
`scanner.extra_checks_rating: false` pour les signaler sans toucher à la note,
ou `--no-extra-checks` pour les ignorer purement et simplement.
