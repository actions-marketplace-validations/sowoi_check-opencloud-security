# Exécuter le scanner comme un service

Lancez `check-opencloud-scanner serve` pour rendre le scanner intégré
disponible sous forme de service HTTP persistant. Plusieurs consommateurs
peuvent alors partager un résultat mis en cache pour chaque instance. Le
[README principal](reference.md#running-the-scanner-as-a-service) énumère les
points d'accès et les exigences en matière de jeton ; ce guide traite du
déploiement.

Pour une interface de navigateur avec file d'attente de scans, utilisez
l'[application web publique](web-service.md), qui est distincte.

<!-- TOC -->
* [Exécuter le scanner comme un service](#running-the-scanner-as-a-service)
  * [Dans un conteneur](#in-a-container)
  * [Le fichier compose de supervision](#the-monitoring-compose-file)
<!-- TOC -->


## Dans un conteneur {#in-a-container}

Le service refuse d'écouter ailleurs que sur la boucle locale sans jeton. Dans
un conteneur, écoutez sur les interfaces du conteneur afin que le port publié
atteigne le processus, et définissez un jeton pour authentifier les requêtes.

```shell
docker run -d --name opencloud-scanner -p 127.0.0.1:8811:8811 \
  -e COS_SERVICE_LISTEN=0.0.0.0 \
  -e COS_SERVICE_TOKEN="$(openssl rand -hex 32)" \
  --entrypoint check-opencloud-scanner \
  check-opencloud-security serve

curl -H "Authorization: Bearer <token>" \
  'http://127.0.0.1:8811/api/scan?url=opencloud.example.com'
```

## Le fichier compose de supervision {#the-monitoring-compose-file}

Un fichier prêt à l'emploi,
[`docker/docker-compose.monitoring.yml`](../../docker/docker-compose.monitoring.yml),
démarre le scanner ainsi qu'un conteneur de contrôle, avec un contrôle de santé
et des secrets Docker :

```shell
# 1. create the secret files from the templates
cp secrets/scanner_token.example  secrets/scanner_token
cp secrets/releases_token.example secrets/releases_token

# 2. fill them with real values
openssl rand -hex 32 > secrets/scanner_token          # protects the service
printf '%s' '<github-token>' > secrets/releases_token
chmod 600 secrets/scanner_token secrets/releases_token

# 3. adjust COS_HOST in docker/docker-compose.monitoring.yml, then:
cd docker
docker compose -f docker-compose.monitoring.yml up -d scanner
docker compose -f docker-compose.monitoring.yml run --rm check
```

Le simple `docker compose up` dans ce répertoire démarre en revanche
l'application web publique - voir [l'application web](web-service.md).
Installez cette dernière avec **`docker/setup-wizard.py`** plutôt qu'en
modifiant un fichier compose : l'assistant demande à quelle adresse le service
doit être joignable, avec quelle intensité il peut scanner, qui peut effacer un
résultat et ce qui termine le TLS en amont, puis il écrit un fichier compose
commenté, un `.env` contenant le mot de passe Redis et tous les autres
identifiants auxquels ce fichier fait référence, et - si vous en nommez un - la
configuration nginx, Apache, Caddy ou Traefik correspondante. C'est un unique
fichier Python n'utilisant que la bibliothèque standard : il fonctionne donc sur
un hôte doté de Docker et de rien d'autre - voir
[`docker/README.md`](../../docker/README.md#setting-up-the-whole-stack).

Tout ce qui se trouve dans `secrets/`, à l'exception des modèles `*.example`,
est ignoré par git - voir [`secrets/README.md`](../../secrets/README.md).
