# Exemples {#worked-examples}

Ces exemples présentent les usages courants du scanner. Remplacez
`opencloud.example.com` par l’adresse de votre instance. Analysez uniquement les
systèmes que vous êtes autorisé à tester.

Des exemples détaillés sont disponibles pour [Kubernetes](kubernetes.md), les
[pipelines CI](ci.md), [Prometheus et Grafana](prometheus.md), les
[adaptateurs webhook](../webhook-recipes.md) et les [parcs d’instances](many-instances.md).

## Commandes de base {#the-basics}

```bash
# Contrôle minimal
check-opencloud-security --host opencloud.example.com

# Inclure le durcissement et les en-têtes de sécurité dans le rapport
check-opencloud-security --host opencloud.example.com --check-hardening

# Expliquer la note initiale, les causes de sa baisse
# et chaque identifiant du résultat
check-opencloud-security --host opencloud.example.com --check-hardening --debug

# Analyser plusieurs instances ; retenir l’état le plus défavorable
check-opencloud-security --host cloud-a.example.com --host cloud-b.example.com
```

## Choisir un canal de publication {#release-track-examples}

```bash
# Canal production : seules ses versions et leurs correctifs comptent ;
# aucune version rolling ne sera recommandée
check-opencloud-security --host opencloud.example.com --release-track production

# Canal rolling : le support cesse dès la publication de la version suivante
check-opencloud-security --host opencloud.example.com --release-track rolling

# Canal LTS : deux ans de correctifs rétroportés
check-opencloud-security --host opencloud.example.com --release-track lts

# Déduire le canal à partir de la version annoncée et du calendrier des versions
check-opencloud-security --host opencloud.example.com --release-track auto

# Avertir dès qu’une mise à jour du canal est disponible,
# sans attendre la fin du support
check-opencloud-security --host opencloud.example.com \
    --release-track production --update-warning
```

Une version plus récente ne bénéficie pas forcément d’un meilleur support. Si vous
déclarez `production` pour une instance qui utilise une version du canal rolling,
le scanner la signale comme *en avance* sur son canal. Il ne la considère ni comme
la version courante du canal, ni comme une version en fin de support. Ce dernier
état est réservé aux versions antérieures à la version courante du canal choisi.

## Accepter certains constats {#accepting-findings-you-are-not-going-to-fix}

```bash
# Le proxy inverse définit HSTS ; renforcer la CSP par défaut
# empêcherait l’interface web de fonctionner
check-opencloud-security --host opencloud.example.com --check-hardening \
    --ignore-hardening cspWithoutUnsafeInline \
    --ignore-hardening hstsPreload

# Liste séparée par des virgules, adaptée à une commande Icinga
# ou à une variable d’environnement
check-opencloud-security --host opencloud.example.com --check-hardening \
    --ignore-hardening 'cspWithoutUnsafeInline,hstsPreload'

# Motif générique pour les identifiants contenant un chemin ou un port
check-opencloud-security --host opencloud.example.com \
    --ignore-hardening 'debugPort:*'

# HTTP Basic reste activé pour un outil de migration ;
# accepter ce constat pendant cette période
check-opencloud-security --host opencloud.example.com --check-hardening \
    --ignore-hardening basicAuthDisabled

# Vérifier l’effet d’une exemption : --debug affiche
# les constats exemptés et les indique dans l’explication
check-opencloud-security --host opencloud.example.com --check-hardening \
    --ignore-hardening basicAuthDisabled --debug
```

## Réunir les réglages dans un fichier {#both-together-in-a-configuration-file}

Pour une configuration durable, préférez un fichier. Vous pouvez y expliquer chaque
exemption et préciser quand la réexaminer :

```yaml
# /etc/check-opencloud-security/config.yml
host: opencloud.example.com
check_hardening: true
update_warning: true

scanner:
  release_track: production
  ignore_hardenings:
    - cspWithoutUnsafeInline   # CSP par défaut ; la renforcer bloque l’interface web
    - hstsPreload              # le proxy inverse définit HSTS
    - 'debugPort:*'            # ports de débogage bloqués par le pare-feu
```

```bash
check-opencloud-security --config /etc/check-opencloud-security/config.yml
```

Les mêmes réglages sous forme de variables d’environnement, pour un conteneur ou une unité systemd :

```bash
export COS_HOST=opencloud.example.com
export COS_CHECK_HARDENING=1
export COS_SCANNER_RELEASE_TRACK=production
export COS_SCANNER_IGNORE_HARDENINGS='cspWithoutUnsafeInline;hstsPreload'
check-opencloud-security
```

## Instances hors de l’Internet public {#instances-that-are-not-on-the-public-internet}

```bash
# Proxy OpenCloud avec certificat autosigné
check-opencloud-security --host 10.0.0.5 --port 9200 --insecure

# HTTP derrière un répartiteur qui termine TLS
check-opencloud-security --host opencloud.internal --scheme http

# Adresse IPv6
check-opencloud-security --host '[2001:db8::1]'

# Réseau isolé : utiliser uniquement le calendrier fourni
check-opencloud-security --host opencloud.example.com --update-source bundled

# Limite GitHub atteinte ou mode hors ligne : définir la dernière version
check-opencloud-security --host opencloud.example.com --latest-version 7.2.3

# Omettre les ports de débogage : jusqu’à 15 secondes d’attente derrière un pare-feu
check-opencloud-security --host opencloud.example.com --no-debug-ports --timeout 5
```

## Seuils et notifications {#thresholds-and-notifications}

```bash
# Seuils plus stricts : avertissement à A, état critique à C
check-opencloud-security --host opencloud.example.com --warning 4 --critical 3

# Envoyer un webhook lorsque le contrôle devient critique
check-opencloud-security --host opencloud.example.com \
    --webhook-url https://hooks.example.com/opencloud \
    --webhook-header 'Authorization: Bearer secret://webhook_token'

# Instance de production, durcissement contrôlé, deux exemptions
# et notification pour tout état autre que OK
check-opencloud-security --host opencloud.example.com \
    --release-track production \
    --check-hardening \
    --ignore-hardening 'cspWithoutUnsafeInline,hstsPreload' \
    --update-warning \
    --warning 4 --critical 2 \
    --webhook-url https://hooks.example.com/opencloud \
    --webhook-on warning
```

## Définition d’un service Icinga2 {#icinga2-command-definition}

```
apply Service "opencloud-security" {
  import "generic-service"
  check_command = "check_opencloud_security"

  vars.opencloud_host           = host.address
  vars.opencloud_check_hardening = true
  vars.opencloud_release_track  = "production"
  vars.opencloud_ignore_hardening = "cspWithoutUnsafeInline,hstsPreload"

  assign where host.vars.opencloud == true
}
```

## Scanner autonome {#the-scanner-on-its-own}

```bash
# Résultat JSON pour un script ou une inspection ponctuelle
check-opencloud-scanner scan opencloud.example.com | jq '.rating, .lifecycle'

# Constats exemptés et contrôles supplémentaires enregistrés
check-opencloud-scanner scan opencloud.example.com | jq '.ignored, .extraChecks'
```
