# Pourquoi OpenCloud répond encore à `/status.php`

OpenCloud est écrit en Go. Sa route `/status.php` est un point d'accès de
compatibilité destiné aux clients existants, et non un script PHP.

<!-- TOC -->
* [Pourquoi OpenCloud répond encore à `/status.php`](#why-opencloud-still-answers-statusphp)
  * [D'où vient ce chemin](#where-the-path-comes-from)
  * [Ce que le gestionnaire renvoie réellement](#what-the-handler-actually-returns)
  * [Ce que ce scanner y lit, et ce qu'il n'y lit pas](#what-this-scanner-reads-from-it-and-what-it-does-not)
<!-- TOC -->


## D'où vient ce chemin {#where-the-path-comes-from}

Ce point d'accès préserve une interface cliente familière, alors qu'OpenCloud
la sert depuis du code Go. Le suffixe `.php` n'implique pas que PHP s'exécute
sur le serveur. Plusieurs produits exposent un point d'accès compatible : le
scanner vérifie donc le produit annoncé avant d'appliquer des règles propres à
OpenCloud. Voir [Ce qu'est OpenCloud](what-is-opencloud.md) pour l'architecture
et [Dépannage](troubleshooting.md) pour les échecs d'identification du produit.

```go
// vendor/github.com/opencloud-eu/reva/v2/internal/http/services/owncloud/ocdav/ocdav.go
return []string{"/status.php", "/status", "/remote.php/dav/public-files/", ...}
...
case "status.php", "status":
    s.doStatus(w, r)
```

`/status.php` et la forme plus courte `/status` aboutissent au même
gestionnaire. L'orthographe `.php` n'est conservée que parce que des clients la
demandent encore sous ce nom exact ; rien dans la réponse n'est produit par PHP.

## Ce que le gestionnaire renvoie réellement {#what-the-handler-actually-returns}

Le gestionnaire qui répond aux deux chemins est `doStatus`, et sa réponse est un
littéral de structure, non une interrogation d'un quelconque état courant :

```go
// vendor/github.com/opencloud-eu/reva/v2/internal/http/services/owncloud/ocdav/status.go
status := &ocs.Status{
    Installed:      true,
    Maintenance:    false,
    NeedsDBUpgrade: false,
    Version:        s.c.Version,
    VersionString:  s.c.VersionString,
    Edition:        s.c.Edition,
    ProductName:    s.c.ProductName,
    ProductVersion: s.c.ProductVersion,
    Product:        s.c.Product,
}
```

`Installed`, `Maintenance` et `NeedsDBUpgrade` valent littéralement `true`,
`false` et `false` - pas `s.c.quelquechose`, rien lu dans une base de données,
rien lu dans un fichier sur disque. Toute instance OpenCloud ayant jamais
embarqué ce gestionnaire renvoie exactement ces trois mêmes valeurs, qu'elle
vienne de démarrer, qu'elle soit en cours de déploiement ou qu'elle tourne
depuis un an. OpenCloud n'a d'ailleurs pas de base de données au sens où le nom
du champ le laisse entendre : il stocke les données dans le système de fichiers
et dans des stockages objet, et non dans une base SQL à migrations de schéma ;
« `needsDbUpgrade` » décrit donc un état que l'architecture même d'OpenCloud ne
connaît pas.

Les champs restants - `Version`, `VersionString`, `Edition`, `ProductName`,
`ProductVersion`, `Product` - proviennent de `s.c`, la configuration du service
lui-même, et varient bien selon la version compilée. `Version` et
`VersionString` sont eux-mêmes des valeurs historiques figées, conservées pour
les anciens clients de synchronisation ; seul `ProductVersion` correspond à la
version réelle - voir
[Lire correctement la version](scanner-checks.md#reading-the-version-correctly).

## Ce que ce scanner y lit, et ce qu'il n'y lit pas {#what-this-scanner-reads-from-it-and-what-it-does-not}

Ce scanner lit `product`/`productname` (afin de refuser ownCloud et Nextcloud
plutôt que de les noter) et `productversion` (la version réelle, utilisée pour
les contrôles de fin de vie et de mise à jour - voir [Divulgation de la version
et du cycle de vie](lifecycle.md) pour ce qui dépend de ce champ et pour la
façon dont le scan réagit lorsqu'il manque). Il ne contrôle ni `installed`, ni
`maintenance`, ni `needsDbUpgrade` : un contrôle qui réussit toujours -
indépendamment de ce qui se passe réellement sur le serveur - serait pire que
pas de contrôle du tout, car un résultat au vert laisserait croire que le
scanner a vérifié quelque chose qu'il n'a en réalité pas pu observer. Des
versions antérieures de ce scanner signalaient bien des constats
`maintenanceMode`, `installed` et `databaseUpgrade` issus de ces champs ; ils
ont été supprimés une fois la réponse figée ci-dessus confirmée dans le code
source d'OpenCloud lui-même.

Si une future version d'OpenCloud se met à calculer ces champs à partir d'un
état réel, c'est le code source ci-dessus qu'il faudra consulter : il fait
autorité, et non ce document, qui ne fait que le citer à la date de rédaction.
