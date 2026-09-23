# Proxys inverses {#reverse-proxies}

Deux composants peuvent se trouver derrière un proxy inverse, avec des
besoins différents.

- **Devant une instance OpenCloud**, le proxy est évalué par le contrôle.
  La plupart des constats sur les en-têtes dépendent de sa configuration.
  S’il supprime un en-tête envoyé par OpenCloud, il dégrade le résultat de
  l’instance. Voir [Devant OpenCloud](#in-front-of-opencloud).
- **Devant le service de scan** de ce dépôt, le proxy doit permettre la
  limitation des requêtes et laisser assez de temps aux scans pour se
  terminer. Voir [Devant le service de scan](#in-front-of-the-scan-service).

Les deux sections donnent des configurations pour nginx, Apache httpd, Caddy,
Traefik et HAProxy. Remplacez `opencloud.example.com` et `scan.example.com`
par vos noms d’hôtes. Le dépôt ne contient aucun nom d’instance réelle.

## Devant OpenCloud {#in-front-of-opencloud}

Le service proxy d’OpenCloud envoie déjà les en-têtes de sécurité. Un constat
sur les en-têtes signifie donc généralement qu’un intermédiaire les a
supprimés ou a répondu avant OpenCloud. Les ajouter au proxy corrige les
deux situations.

### En-têtes attendus {#the-headers-this-check-looks-for}

| En-tête | Valeur acceptée par le contrôle |
|:--------|:------------------------------|
| `Strict-Transport-Security` | Tout `max-age`. Un an ou plus valide aussi `hstsLongMaxAge` ; `preload` valide `hstsPreload` |
| `Content-Security-Policy` | Toute politique non vide. La présence de `unsafe-inline` fait échouer séparément `cspWithoutUnsafeInline` |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `SAMEORIGIN` |
| `X-Permitted-Cross-Domain-Policies` | `none` |
| `X-Robots-Tag` | Toute valeur non vide |
| `X-XSS-Protection` | Toute valeur non vide. Les navigateurs modernes l’ignorent ; il est contrôlé parce qu’OpenCloud l’envoie |
| `Referrer-Policy` | Toute valeur non vide |

Envoyez-les uniquement sur HTTPS. Les navigateurs ignorent
`Strict-Transport-Security` dans une réponse HTTP non chiffrée.

### Deux constats qui ne portent pas sur les en-têtes {#two-findings-decided-here-that-are-not-headers}

Ce sont des indicateurs de durcissement et non des contrôles supplémentaires.
Ils ne diminuent pas la note à eux seuls, mais font passer l’état à WARNING.
Vous pouvez les exempter avec `--ignore-hardening`.

| Indicateur | Condition de réussite |
|:-----------|:----------------------|
| `httpsEnforced` | Une requête `http://` sur le port 80 reçoit une redirection dont `Location` commence par `https://`, ou le port 80 ne répond pas |
| `reverseProxyDetected` | La réponse contient un indice de proxy : un en-tête `Server` caractéristique ou un en-tête `Via` |

**`httpsEnforced`** est mesuré sans suivre les redirections. Le scanner
interroge `/` sur le port 80 une fois et lit `Location`. Une redirection vers
une autre adresse HTTP, un `200` qui sert l’interface ou une chaîne qui
n’atteint HTTPS qu’au deuxième saut échouent. Un port 80 fermé ou filtré
**réussit** : aucune communication HTTP non chiffrée n’est possible.

**`reverseProxyDetected`** repose sur les indices disponibles et ne change
jamais la note. Traefik et HAProxy ne s’annoncent pas par défaut. Un
déploiement correct peut donc échouer à ce contrôle. Vérifiez la présence
d’un proxy avant de conclure à un défaut. Si vous devez en installer un,
les exemples suivants donnent une configuration habituelle.

### nginx {#nginx}

```nginx
server {
    listen 443 ssl http2;
    server_name opencloud.example.com;

    ssl_certificate     /etc/ssl/opencloud/fullchain.pem;
    ssl_certificate_key /etc/ssl/opencloud/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    # always: also on 4xx and 5xx, which is where a missing header hides.
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Permitted-Cross-Domain-Policies "none" always;
    add_header X-Robots-Tag "noindex, nofollow" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    client_max_body_size 0;          # uploads are not the proxy's business
    proxy_request_buffering off;

    location / {
        proxy_pass http://127.0.0.1:9200;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $remote_addr;   # overwrite, never append
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade           $http_upgrade;
        proxy_set_header Connection        $connection_upgrade;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}

server {
    listen 80;
    server_name opencloud.example.com;
    return 308 https://$host$request_uri;
}
```

Dans nginx, `add_header` **ne s’additionne pas entre les niveaux**. Un seul
`add_header` dans un bloc `location` annule tous ceux du bloc `server`.
Si vous en ajoutez un dans `location`, répétez-y la liste complète.

`Content-Security-Policy` est volontairement absent de cet exemple. OpenCloud
envoie sa propre politique. Une politique écrite manuellement dans le proxy
peut casser l’interface. Ajoutez-en une seulement si le contrôle la signale
absente et si aucun composant derrière le proxy ne l’envoie.

### Apache httpd {#apache-httpd}

```apache
<VirtualHost *:443>
    ServerName opencloud.example.com

    SSLEngine on
    SSLCertificateFile      /etc/ssl/opencloud/fullchain.pem
    SSLCertificateKeyFile   /etc/ssl/opencloud/privkey.pem
    SSLProtocol             -all +TLSv1.2 +TLSv1.3

    # 'always' is the condition, not the flag: it covers error responses too.
    Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Permitted-Cross-Domain-Policies "none"
    Header always set X-Robots-Tag "noindex, nofollow"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"

    ProxyPreserveHost On
    ProxyPass        / http://127.0.0.1:9200/ timeout=3600
    ProxyPassReverse / http://127.0.0.1:9200/
    RequestHeader set X-Forwarded-Proto "https"
</VirtualHost>
```

Les modules `mod_headers`, `mod_proxy`, `mod_proxy_http` et `mod_ssl` sont
nécessaires. Apache ajoute lui-même le client à `X-Forwarded-For`. Ne le
faites pas aussi manuellement, sinon l’adresse figurera deux fois.

### Caddy {#caddy}

```caddyfile
opencloud.example.com {
    encode zstd gzip

    header {
        Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
        X-Permitted-Cross-Domain-Policies "none"
        X-Robots-Tag "noindex, nofollow"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
    }

    reverse_proxy 127.0.0.1:9200 {
        transport http {
            read_timeout 1h
        }
    }
}
```

Caddy termine TLS, redirige automatiquement le port 80 et définit
`X-Forwarded-For`, `X-Forwarded-Proto` et `X-Forwarded-Host`. Sa directive
`header` remplace l’en-tête reçu du serveur en amont. Vous pouvez donc la
conserver même si OpenCloud envoie de nouveau ses propres en-têtes.

### Traefik {#traefik}

Ajoutez ces étiquettes au conteneur OpenCloud :

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.opencloud.rule=Host(`opencloud.example.com`)"
  - "traefik.http.routers.opencloud.entrypoints=websecure"
  - "traefik.http.routers.opencloud.tls.certresolver=letsencrypt"
  - "traefik.http.services.opencloud.loadbalancer.server.port=9200"
  - "traefik.http.routers.opencloud.middlewares=opencloud-headers"
  - "traefik.http.middlewares.opencloud-headers.headers.stsSeconds=63072000"
  - "traefik.http.middlewares.opencloud-headers.headers.stsIncludeSubdomains=true"
  - "traefik.http.middlewares.opencloud-headers.headers.stsPreload=true"
  - "traefik.http.middlewares.opencloud-headers.headers.contentTypeNosniff=true"
  - "traefik.http.middlewares.opencloud-headers.headers.frameDeny=false"
  - "traefik.http.middlewares.opencloud-headers.headers.customFrameOptionsValue=SAMEORIGIN"
  - "traefik.http.middlewares.opencloud-headers.headers.referrerPolicy=strict-origin-when-cross-origin"
  - "traefik.http.middlewares.opencloud-headers.headers.customResponseHeaders.X-Permitted-Cross-Domain-Policies=none"
  - "traefik.http.middlewares.opencloud-headers.headers.customResponseHeaders.X-Robots-Tag=noindex, nofollow"
  - "traefik.http.middlewares.opencloud-headers.headers.customResponseHeaders.X-XSS-Protection=1; mode=block"
```

`stsSeconds` est le seul moyen de configurer HSTS dans le middleware d’en-têtes
de Traefik. Une valeur `Strict-Transport-Security` placée dans
`customResponseHeaders` est remplacée. Traefik n’envoie HSTS que sur un
routeur TLS, ce qui convient ici.

### HAProxy {#haproxy}

```haproxy
frontend https-in
    bind :443 ssl crt /etc/ssl/opencloud/opencloud.pem alpn h2,http/1.1
    http-request redirect scheme https unless { ssl_fc }

    http-response set-header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
    http-response set-header X-Content-Type-Options "nosniff"
    http-response set-header X-Frame-Options "SAMEORIGIN"
    http-response set-header X-Permitted-Cross-Domain-Policies "none"
    http-response set-header X-Robots-Tag "noindex, nofollow"
    http-response set-header X-XSS-Protection "1; mode=block"
    http-response set-header Referrer-Policy "strict-origin-when-cross-origin"

    default_backend opencloud

backend opencloud
    option forwardfor
    http-request set-header X-Forwarded-Proto https
    timeout server 1h
    server oc1 127.0.0.1:9200 check
```

`set-header` remplace la valeur existante. `add-header` ajouterait un deuxième
en-tête, ce qu’il faut éviter pour `Strict-Transport-Security`.

### Erreurs qui dégradent le résultat {#mistakes-that-cost-a-grade}

- **En-têtes envoyés uniquement avec `200`.** `add_header` dans nginx et
  `Header set` dans Apache, sans `always`, omettent les réponses d’erreur.
  Le scanner lit les en-têtes de la réponse reçue : leur absence sur une
  redirection ou un 401 est donc signalée.
- **Proxy qui répond avant OpenCloud.** Une page de maintenance, une passerelle
  d’authentification ou une erreur de CDN peut être analysée à la place
  d’OpenCloud. Si le contrôle trouve un autre produit ou aucune version,
  vérifiez les intermédiaires. Voir [Dépannage](troubleshooting.md).
- **Ajout à un `X-Forwarded-For` fourni par le client.** Ce contrôle ne le
  signale pas, mais cela peut fausser les limites et journaux d’audit derrière
  le proxy. Remplacez cet en-tête à l’entrée du réseau.
- **Transmission du `X-Forwarded-Host` du client.** Le contrôle
  `forwardedHostIgnored` échoue si l’instance utilise cette valeur dans ses
  URL publiques. Le scanner demande le document de découverte avec un nom
  d’hôte inexistant, puis cherche ce nom dans `issuer` et les points d’accès
  qui recevront la prochaine connexion. Définissez `OC_URL` et construisez
  l’en-tête à partir de la configuration du proxy
  (`proxy_set_header X-Forwarded-Host $host;`). Un hôte virtuel par défaut
  qui refuse les noms inconnus protège aussi l’en-tête `Host`.
- **Absence de serveur par défaut.** Pour un `Host` sans `server_name`
  correspondant, nginx utilise le premier bloc `server` chargé sur ce port,
  parfois celui d’une autre application. Apache utilise le premier
  `<VirtualHost>`. Si ce site redirige avec `$host`, le nom de test revient
  dans `Location`. `forwardedHostIgnored` échoue alors avec
  `Host comes back as the address it redirects to`, même si OpenCloud n’a
  jamais reçu la requête et si `OC_URL` est correct. Un certificat ou des
  en-têtes différents avec un `Host` inventé permettent de le repérer :

  ```bash
  curl -sI -H "Host: unknown.invalid" https://opencloud.example.com/.well-known/openid-configuration
  ```

  Définissez un serveur par défaut qui refuse tous les noms non servis.
  Dans les autres sites, écrivez les redirections avec leur propre nom
  plutôt qu’avec `$host` :

  ```nginx
  server {
      listen 80 default_server;
      listen [::]:80 default_server;
      listen 443 ssl default_server;
      listen [::]:443 ssl default_server;
      server_name _;
      ssl_reject_handshake on;   # nginx 1.19.4 and later; no certificate needed
      return 444;
  }
  ```

  Dans Apache, le premier `<VirtualHost>` de chaque port doit ne rien servir
  (`Redirect 403 /`). Caddy et Traefik ne dirigent pas les noms inconnus vers
  un site ; ils ne nécessitent pas cet ajout.
- **Interface accessible en HTTP.** Une redirection suffit : le scanner la
  suit et évalue la destination. En revanche, servir aussi l’interface en
  HTTP fait échouer [`httpsEnforced`](#two-findings-decided-here-that-are-not-headers).
- **Certificat autosigné ou expiré.** Une connexion non reconnue est un
  problème TLS qu’aucun en-tête ne peut corriger.

## Devant le service de scan {#in-front-of-the-scan-service}

L’application web de ce dépôt, décrite dans [`docs/webapp.md`](../webapp.md),
est un service ASGI sur un seul port. Elle envoie ses en-têtes de sécurité,
dont une `Content-Security-Policy` sans `unsafe-inline`. Le proxy doit surtout
transmettre l’adresse réelle du client et attendre la fin du scan.

**Vous n’avez pas besoin de copier ces configurations à la main.**
[`docker/setup-wizard.py`](../../docker/setup-wizard.py) génère la configuration
nginx, Apache, Caddy ou Traefik avec le nom d’hôte et le port. Si la pile
inclut son fournisseur d’identité, il ajoute aussi l’authentification déléguée
devant `/admin` et un site Authentik sur son nom d’hôte public. Les exemples
suivants servent aussi de référence pour les déploiements manuels.

### Besoins du service {#what-the-service-needs-from-a-proxy}

- **Adresse réelle du client.** La limitation des requêtes et le délai entre
  scans d’une même cible empêchent l’utilisation abusive du scanner public.
  Les deux utilisent l’adresse du client. Transmettez `X-Forwarded-For`,
  activez `COS_WEB_TRUST_FORWARDED_FOR=true` et réglez
  `COS_WEB_TRUSTED_PROXY_HOPS` si plusieurs de vos proxys sont traversés.

  L’application lit ce nombre d’entrées à partir de la **droite**. Un proxy
  qui ajoute une entrée est donc aussi sûr qu’un proxy qui remplace
  l’en-tête : la valeur du client reste à gauche de l’entrée ajoutée par
  votre proxy. Comptez uniquement les proxys **que vous exploitez**. Un
  nombre trop faible identifie un proxy plutôt que le visiteur ; un nombre
  trop élevé atteint une valeur contrôlée par le client.
- **Délais supérieurs à la durée du scan.** Un scan prend quelques secondes à
  une minute. Un export PDF ou un appel MCP `scan_instance` peut durer
  plusieurs minutes. Prévoyez au moins 120 secondes, davantage pour MCP.
- **Aucune mise en tampon sur `/mcp`.** Le point d’accès Model Context
  Protocol renvoie un flux d’événements. La mise en tampon empêche le client
  de les recevoir à temps.
- **Chemins de découverte inchangés.** `/.well-known/ai.json`, `/openapi.json`,
  `/arazzo.json`, `/robots.txt` et `/sitemap.xml` doivent atteindre
  l’application sans réécriture. Si le proxy traite lui-même
  `/.well-known/`, comme certaines configurations ACME, excluez ce fichier.
- **Adresse publique explicite.** Réglez `COS_WEB_PUBLIC_BASE_URL` sur
  l’adresse utilisée par les visiteurs. Elle sert aux liens canoniques,
  au plan du site et aux URL absolues du document de découverte.
  L’application ne peut pas la déduire derrière un proxy.

### nginx {#nginx_1}

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

server {
    listen 443 ssl http2;
    server_name scan.example.com;

    ssl_certificate     /etc/ssl/scan/fullchain.pem;
    ssl_certificate_key /etc/ssl/scan/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8811;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        # Overwrite. Appending would let a client choose its own rate limit.
        proxy_set_header X-Forwarded-For   $remote_addr;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_read_timeout 300s;
    }

    # The MCP endpoint streams. Buffering it breaks every agent session.
    location /mcp {
        proxy_pass http://127.0.0.1:8811;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For   $remote_addr;
        proxy_set_header Connection        "";
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding off;
        proxy_read_timeout 3600s;
    }

    location /static/ {
        proxy_pass http://127.0.0.1:8811;
        proxy_cache_valid 200 1h;
        expires 1h;
    }
}
```

Puis configurez :

```bash
COS_WEB_TRUST_FORWARDED_FOR=true
COS_WEB_TRUSTED_PROXY_HOPS=1
COS_WEB_PUBLIC_BASE_URL=https://scan.example.com
COS_WEB_MCP_ALLOWED_HOSTS=scan.example.com
```

`COS_WEB_MCP_ALLOWED_HOSTS` protège le point d’accès MCP contre le rebinding
DNS. Il peut rester vide si le proxy impose déjà le nom d’hôte, mais le
renseigner ajoute une vérification utile en cas de mauvaise transmission de
`Host`.

### Apache httpd {#apache-httpd_1}

```apache
<VirtualHost *:443>
    ServerName scan.example.com

    SSLEngine on
    SSLCertificateFile    /etc/ssl/scan/fullchain.pem
    SSLCertificateKeyFile /etc/ssl/scan/privkey.pem

    ProxyPreserveHost On
    RequestHeader set X-Forwarded-Proto "https"

    # The client, and only the client. mod_remoteip first if you are behind
    # another proxy, so that %a is the address you actually want to forward.
    RequestHeader set X-Forwarded-For "%{REMOTE_ADDR}e"

    # The event stream must not be buffered or the session never starts.
    <Location "/mcp">
        ProxyPass        http://127.0.0.1:8811/mcp flushpackets=on timeout=3600
        ProxyPassReverse http://127.0.0.1:8811/mcp
        SetEnv proxy-sendchunked 1
        SetEnv no-gzip 1
    </Location>

    ProxyPass        / http://127.0.0.1:8811/ timeout=300
    ProxyPassReverse / http://127.0.0.1:8811/
</VirtualHost>
```

L’ordre compte : le bloc `<Location "/mcp">` doit précéder le `ProxyPass /`
général. Sinon, cette dernière règle s’applique et réactive la mise en tampon.

### Caddy {#caddy_1}

```caddyfile
scan.example.com {
    encode zstd gzip

    # Streaming, and a timeout long enough for a scan to finish.
    reverse_proxy /mcp* 127.0.0.1:8811 {
        flush_interval -1
        transport http {
            read_timeout 1h
        }
    }

    reverse_proxy 127.0.0.1:8811 {
        transport http {
            read_timeout 5m
        }
    }
}
```

`flush_interval -1` désactive la mise en tampon nécessaire au flux
d’événements. Caddy construit `X-Forwarded-For` depuis la connexion et ignore
la valeur du client. `COS_WEB_TRUST_FORWARDED_FOR=true` convient donc avec
`COS_WEB_TRUSTED_PROXY_HOPS=1`, sa valeur par défaut.

### Traefik {#traefik_1}

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.scan.rule=Host(`scan.example.com`)"
  - "traefik.http.routers.scan.entrypoints=websecure"
  - "traefik.http.routers.scan.tls.certresolver=letsencrypt"
  - "traefik.http.services.scan.loadbalancer.server.port=8811"
  # Do not buffer the MCP event stream; Traefik streams by default, so the
  # only thing to get right is the timeout on the entrypoint.
  - "traefik.http.services.scan.loadbalancer.responseForwarding.flushInterval=1ms"
```

Dans la configuration statique :

```yaml
entryPoints:
  websecure:
    address: ":443"
    transport:
      respondingTimeouts:
        readTimeout: 0        # a submission may hold the connection
        writeTimeout: 0       # a scan may take a minute, an MCP call longer
        idleTimeout: 300s
```

Traefik remplace `X-Real-Ip` et **ajoute** une entrée à `X-Forwarded-For`.
L’application lit l’en-tête depuis la droite et prend donc l’entrée de
Traefik. Utilisez `COS_WEB_TRUST_FORWARDED_FOR=true` et
`COS_WEB_TRUSTED_PROXY_HOPS=1`. Si un CDN précède aussi Traefik, comptez les
deux intermédiaires et réglez la valeur sur `2`.

### HAProxy {#haproxy_1}

```haproxy
frontend scan-in
    bind :443 ssl crt /etc/ssl/scan/scan.pem alpn h2,http/1.1
    http-request set-header X-Forwarded-Proto https
    # set-header, not add-header: the client does not get a vote.
    http-request set-header X-Forwarded-For %[src]
    default_backend scan

backend scan
    option http-server-close
    no option http-buffer-request
    timeout server 1h
    timeout tunnel 1h
    server scan1 127.0.0.1:8811 check
```

`timeout tunnel` maintient le flux MCP ouvert. `timeout server` seul peut
fermer la connexion en cours de session.

### Vérifier le résultat {#checking-the-result}

```bash
# The client address the service actually sees, through the proxy.
curl -sS https://scan.example.com/healthz

# Discovery must be reachable, unauthenticated, and JSON.
curl -sS https://scan.example.com/.well-known/ai.json | head -c 200
curl -sSo /dev/null -w '%{http_code}\n' https://scan.example.com/openapi.json
curl -sSo /dev/null -w '%{http_code}\n' https://scan.example.com/arazzo.json

# The absolute URLs in the discovery document must be the public ones, not
# 127.0.0.1 - if they are wrong, COS_WEB_PUBLIC_BASE_URL is not set.
curl -sS https://scan.example.com/.well-known/ai.json | grep -o 'https://[^"]*' | head

# MCP: an initialise that answers is a proxy that is not buffering.
curl -sS -X POST https://scan.example.com/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{
        "protocolVersion":"2025-06-18","capabilities":{},
        "clientInfo":{"name":"curl","version":"1"}}}'
```

Testez la limite depuis deux adresses. Sur une machine, dépassez
`COS_WEB_IP_RATE_LIMIT` et vérifiez la réponse **429**. Depuis une deuxième
adresse, vérifiez qu’une soumission reste acceptée. Si cette adresse est
aussi limitée, le proxy ne transmet probablement pas l’adresse du client et
tous les visiteurs partagent le même quota.

---

Ce projet communautaire est indépendant. Il n’est ni affilié à OpenCloud
GmbH, ni approuvé ou soutenu par cette société. « OpenCloud » et les marques
associées appartiennent à leurs propriétaires respectifs. Elles servent
uniquement à identifier le logiciel contrôlé.
