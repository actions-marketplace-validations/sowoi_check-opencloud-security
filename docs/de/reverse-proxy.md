# Reverse proxy the OpenCloud Security Scanner

# Reverse Proxys einrichten

Die Anforderungen unterscheiden sich danach, ob der Proxy vor OpenCloud oder vor dem Scan-Webdienst steht:

- **Vor OpenCloud** beeinflusst er die gemessenen TLS-Einstellungen, Header und Zugriffskontrollen. Siehe [OpenCloud absichern](#in-front-of-opencloud).
- **Vor dem Scan-Webdienst** muss er Client-Adressen verlässlich weitergeben und lange API- beziehungsweise MCP-Antworten zulassen. Siehe [Scan-Webdienst veröffentlichen](#in-front-of-the-scan-service).

Die Beispiele behandeln nginx, Apache, Caddy, Traefik und HAProxy. Ersetzen Sie `opencloud.example.com` und `scan.example.com` durch Ihre eigenen Namen.

## Vor OpenCloud {#in-front-of-opencloud}

OpenClouds eigener Proxy liefert bereits Sicherheitsheader. Fehlen sie im Scan, prüfen Sie, ob eine vorgeschaltete Komponente sie entfernt oder die Anfrage selbst beantwortet.

### Erwartete Header {#the-headers-this-check-looks-for}

| Header | Akzeptierter Wert |
|:--|:--|
| `Strict-Transport-Security` | `max-age`; ab einem Jahr besteht zusätzlich `hstsLongMaxAge`, mit `preload` auch `hstsPreload` |
| `Content-Security-Policy` | Nicht leere Richtlinie; unsichere Skriptfreigaben werden separat geprüft |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `SAMEORIGIN` |
| `X-Permitted-Cross-Domain-Policies` | `none` |
| `X-Robots-Tag` | Nicht leer |
| `X-XSS-Protection` | Nicht leer; wird wegen OpenClouds Standardheader erfasst, obwohl moderne Browser ihn nicht mehr auswerten |
| `Referrer-Policy` | Nicht leer |

Setzen Sie HSTS nur auf HTTPS-Antworten. Browser ignorieren diesen Header über unverschlüsseltes HTTP.

### Weitere Proxy-Prüfungen {#two-findings-decided-here-that-are-not-headers}

| Kennung | Verhalten für ein positives Ergebnis |
|:--|:--|
| `httpsEnforced` | Port 80 leitet direkt auf `https://` um oder ist nicht erreichbar |
| `reverseProxyDetected` | Ein Header wie `Server` oder `Via` deutet auf einen Proxy hin |

`httpsEnforced` prüft eine Antwort auf Port 80, ohne der Weiterleitung zu folgen. Ein `200`, eine Weiterleitung auf HTTP oder erst ein späterer HTTPS-Schritt genügen nicht. Ein geschlossener oder gefilterter Port besteht die Prüfung.

`reverseProxyDetected` ist eine Erkennungshilfe und verändert die Note nicht. Traefik und HAProxy müssen sich nicht über Header zu erkennen geben. Ein negatives Ergebnis belegt daher keinen fehlenden Proxy.

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

Bei der üblichen `add_header`-Vererbung übernimmt ein `location`-Block die übergeordneten Header nur, wenn er keine eigenen `add_header`-Direktiven enthält. Wiederholen Sie die benötigten Header in solchen Blöcken oder verwenden Sie eine dazu passende gemeinsame Konfiguration.

Die CSP ist im Beispiel absichtlich nicht neu gesetzt. OpenCloud liefert seine eigene Richtlinie. Überschreiben Sie sie nur nach Prüfung der tatsächlich fehlenden oder ungeeigneten Richtlinie und testen Sie anschließend die Oberfläche.

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

Benötigt werden `mod_headers`, `mod_proxy`, `mod_proxy_http` und `mod_ssl`. Apache ergänzt `X-Forwarded-For` selbst; setzen Sie die Client-Adresse nicht zusätzlich doppelt.

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

Caddy übernimmt TLS und die HTTP-Weiterleitung und setzt die üblichen `X-Forwarded-*`-Header. Die gezeigten `header`-Direktiven ersetzen vorhandene Backend-Werte.

### Traefik {#traefik}

Labels am OpenCloud-Container:

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

Konfigurieren Sie HSTS im Headers-Middleware über `stsSeconds`. Eine zusätzliche Vorgabe über `customResponseHeaders` kann dadurch überschrieben werden. HSTS wird auf dem TLS-Router gesendet.

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

`set-header` ersetzt einen vorhandenen Wert. Verwenden Sie hier nicht `add-header`, um doppelte HSTS-Header zu vermeiden.

### Häufige Fehler {#mistakes-that-cost-a-grade}

- **Header fehlen auf Fehlerantworten.** Verwenden Sie bei nginx `add_header ... always` und bei Apache `Header always set`, wenn der Header auch auf solchen Antworten benötigt wird.
- **Der Proxy antwortet selbst.** Eine Wartungs- oder Fehlerseite kann die Produkt- und Versionserkennung verhindern. Siehe [Fehlersuche](../troubleshooting.md).
- **Ungeprüfte Weiterleitungsheader.** Überschreiben Sie vom Client gelieferte Werte am Netzrand oder richten Sie eine eindeutig definierte Vertrauenskette ein.
- **Fremdes `X-Forwarded-Host`.** Wenn OpenCloud daraus öffentliche URLs erzeugt, meldet der Scanner `forwardedHostIgnored`. Setzen Sie `OC_URL` und einen kontrollierten Hostheader im Proxy, etwa `proxy_set_header X-Forwarded-Host $host;` zusammen mit geprüften virtuellen Hosts.
- **Kein ablehnender Standardhost.** nginx oder Apache können unbekannte Hostnamen an den ersten virtuellen Host weiterreichen. Dessen Weiterleitung kann dann den fremden Namen übernehmen, obwohl OpenCloud korrekt konfiguriert ist. Prüfen Sie dies mit:

  ```bash
  curl -sI -H "Host: unknown.invalid" https://opencloud.example.com/.well-known/openid-configuration
  ```

  Ein expliziter nginx-Standardhost kann unbekannte Namen ablehnen:

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

  Unter Apache kann der erste `<VirtualHost>` je Port mit `Redirect 403 /` ablehnen. Caddy und Traefik routen unbekannte Namen normalerweise nicht an eine konfigurierte Site.
- **Die Oberfläche bleibt über HTTP erreichbar.** Leiten Sie direkt auf HTTPS um oder schließen Sie Port 80; siehe `httpsEnforced` oben.
- **Nicht vertrauenswürdiges Zertifikat.** Ein selbstsigniertes, abgelaufenes oder unpassendes Zertifikat bleibt ein TLS-Befund, unabhängig von den Headern.

## Vor dem Scan-Webdienst {#in-front-of-the-scan-service}

Die [Webanwendung](../webapp.md) liefert ihre eigenen Sicherheitsheader einschließlich CSP. Der Proxy muss vor allem die Client-Adresse korrekt übergeben und lange Antworten beziehungsweise Ereignisströme unterstützen.

[`docker/setup-wizard.py`](../../docker/setup-wizard.py) kann die Konfiguration für nginx, Apache, Caddy oder Traefik erzeugen. Bei einer Authentik-Bereitstellung ergänzt er auch Forward Auth für `/admin` und den virtuellen Host für den Anmeldeanbieter. Die folgenden Abschnitte dienen auch als Referenz für manuell eingerichtete Proxys.

### Anforderungen des Dienstes {#what-the-service-needs-from-a-proxy}

- **Verlässliche Client-Adresse:** Geben Sie `X-Forwarded-For` weiter und aktivieren Sie `COS_WEB_TRUST_FORWARDED_FOR=true`. Setzen Sie `COS_WEB_TRUSTED_PROXY_HOPS` auf die Zahl der von Ihnen kontrollierten Proxys. Der Dienst liest die entsprechende Adresse von rechts. Ein zu hoher Wert kann vom Client kontrollierte Einträge erreichen; ein zu niedriger fasst Besucher unter einer Proxy-Adresse zusammen.
- **Ausreichende Zeitlimits:** Scans, Exporte und wartende MCP-Aufrufe können länger dauern. Wählen Sie mindestens 120 Sekunden für entsprechende Antworten und ein zum MCP-Ablauf passendes längeres Limit.
- **Kein Puffern auf `/mcp`:** Der Ereignisstrom muss fortlaufend weitergegeben werden.
- **Unveränderte Discovery-Pfade:** Leiten Sie `/.well-known/ai.json`, `/openapi.json`, `/arazzo.json`, `/robots.txt` und `/sitemap.xml` an die Anwendung weiter. Eigene ACME-Regeln dürfen sie nicht abfangen.
- **Öffentliche Basisadresse:** Setzen Sie `COS_WEB_PUBLIC_BASE_URL` für kanonische Links, Sitemap und Discovery-URLs.

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

Dazu die Umgebung:

```bash
COS_WEB_TRUST_FORWARDED_FOR=true
COS_WEB_TRUSTED_PROXY_HOPS=1
COS_WEB_PUBLIC_BASE_URL=https://scan.example.com
COS_WEB_MCP_ALLOWED_HOSTS=scan.example.com
```

`COS_WEB_MCP_ALLOWED_HOSTS` begrenzt die für MCP akzeptierten Hostnamen. Setzen Sie die Liste passend zur öffentlichen Adresse, auch wenn der Proxy den Host bereits kontrolliert.

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

Beachten Sie die Reihenfolge der Proxy-Regeln: Die besondere Behandlung von `/mcp` darf nicht von der allgemeinen Weiterleitung übergangen werden.

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

`flush_interval -1` deaktiviert das Puffern für den Ereignisstrom. Bei einem einzelnen Caddy-Proxy verwenden Sie `COS_WEB_TRUST_FORWARDED_FOR=true` und `COS_WEB_TRUSTED_PROXY_HOPS=1`.

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

Ergänzen Sie die statische Konfiguration:

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

Traefik ergänzt `X-Forwarded-For`. Bei einem einzelnen kontrollierten Proxy liest der Dienst mit `COS_WEB_TRUSTED_PROXY_HOPS=1` den rechten, von Traefik gesetzten Eintrag. Bei weiteren Proxys passen Sie den Wert an die tatsächliche kontrollierte Kette an.

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

`timeout tunnel` berücksichtigt langlebige Verbindungen; stimmen Sie es zusammen mit `timeout server` auf den MCP-Betrieb ab.

### Einrichtung prüfen {#checking-the-result}

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

Prüfen Sie das Client-Limit mit zwei getrennten Adressen. Erreicht eine Adresse ihr `COS_WEB_IP_RATE_LIMIT`, sollte sie `429` erhalten. Die zweite sollte weiterhin Anfragen stellen können, sofern keine andere Begrenzung greift. Werden beide gemeinsam begrenzt, prüfen Sie die weitergegebene Client-Adresse.

---

Dieses unabhängige Community-Projekt steht in keiner Verbindung zu OpenCloud GmbH und wird von ihr weder unterstützt noch empfohlen. „OpenCloud“ und zugehörige Marken gehören ihren jeweiligen Inhabern und dienen hier nur zur Bezeichnung der geprüften Software.

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
