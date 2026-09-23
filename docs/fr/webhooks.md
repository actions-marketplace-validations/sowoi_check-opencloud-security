# Notifications par webhook {#webhook-recipes}

Le [webhook](../README.md#webhook-notifications) envoie par défaut le document
JSON du plugin, avec le statut et tous les constats. Le récepteur reçoit ainsi
le verdict complet. `--webhook-format` permet d’envoyer directement le format
[Slack ou Discord](#slack-mattermost-discord), ou une notification push pour
[ntfy ou Gotify](#ntfy-and-gotify). Pour les autres récepteurs, adaptez le
document JSON générique au format attendu.

Deux règles s’appliquent à tous les exemples :

- **L’échec d’un webhook ne change jamais le résultat du contrôle.** Le plugin
  ajoute `Webhook delivery failed` et conserve le code de sortie mesuré.
  Une panne de notification ne peut donc ni masquer ni inventer une
  vulnérabilité.
- **Ne mettez jamais l’URL dans la ligne de commande.** Elle contient souvent
  le secret d’accès. Utilisez `COS_WEBHOOK_URL` ou `secret://` dans le fichier
  de configuration. Voir [Configuration et secrets](../README.md#configuration-file-and-secrets).

## Les principaux champs {#the-payload-in-short}

Voici les champs les plus utiles du [document complet](#the-full-payload) :

| Champ | Utilité |
|:------|:--------|
| `status`, `exit_code` | `OK` / `WARNING` / `CRITICAL` / `UNKNOWN` et `0`–`3` |
| `message` | Explication sur une ligne, lisible par une personne |
| `rating`, `rating_label` | Note de `0` à `5` et libellé de `A+` à `F` |
| `host`, `product_version` | Instance et version analysées |
| `eol` | Indique si la version ne reçoit plus de correctifs de sécurité |
| `update.availableVersion` | Version vers laquelle mettre à jour |
| `failed_extra_checks`, `missing_hardenings` | Constats détaillés |

Un scan qui échoue entièrement ne contient que `plugin`, `plugin_version`,
`timestamp`, `host`, `status`, `exit_code` et `message`. Tout récepteur qui
utilise `rating` doit accepter son absence.

## Le document complet {#the-full-payload}

Exemple du format `generic` pour une version en fin de vie :

```json
{
  "plugin": "check-opencloud-security",
  "plugin_version": "1.0.0",
  "timestamp": "2026-08-07T10:12:33.123456+00:00",
  "host": "opencloud.example.com",
  "status": "CRITICAL",
  "exit_code": 2,
  "message": "CRITICAL: The 7.3 rolling release line is end-of-life and has no security fixes. Upgrade to 7.4.0.",
  "rating": 0,
  "rating_label": "F",
  "product": "OpenCloud",
  "product_version": "7.3.0",
  "domain": "opencloud.example.com",
  "scanned_at": "2026-08-12 15:24:13.978540",
  "eol": true,
  "release_type": "rolling",
  "lifecycle": {
    "line": "7.3",
    "releaseType": "rolling",
    "state": "endOfLife",
    "released": "2026-07-14",
    "endOfLife": "2026-08-03",
    "daysRemaining": -9,
    "latestOnLine": null,
    "upgradeTo": "7.4.0",
    "reason": "rolling release, unsupported since 2026-08-03",
    "scheduleStale": false,
    "scheduleUpdated": "2026-08-12",
    "scheduleSource": "https://docs.opencloud.eu/docs/admin/resources/lifecycle/",
    "scheduleNote": null
  },
  "vulnerability_count": 0,
  "vulnerabilities": [],
  "missing_hardenings": [],
  "failed_extra_checks": ["exposed:/opencloud.yaml"],
  "scan_backend": "local",
  "scan_uuid": "6a1d1bd0-...",
  "update": {"available": true, "version": "7.3.0", "availableVersion": "7.4.0", "releasedAt": "2026-08-03", "source": "feed", "error": null, "track": "rolling", "newestRelease": null},
  "duration_seconds": 1.234
}
```

`scan_backend` vaut toujours `"local"`. Ce champ indique comment le résultat
a été obtenu. Un récepteur qui traite aussi les documents de scanners distants
peut ainsi les distinguer sans se baser sur le nom du plugin.

Les notifications d’échec du scan ne contiennent que les champs communs :
`plugin`, `plugin_version`, `timestamp`, `host`, `status`, `exit_code`, `message`.

## Récepteur générique {#a-generic-receiver}

Tout service qui accepte du JSON arbitraire peut recevoir le document sans
modification : chaîne de traitement de journaux, collecteur de webhooks ou
flux n8n ou Node-RED.

```shell
export COS_WEBHOOK_URL='https://collector.example.com/hooks/opencloud'
export COS_WEBHOOK_HEADERS='Authorization: Bearer abc123; X-Env: prod'
check-opencloud-security --host opencloud.example.com --webhook-on warning
```

`--webhook-on` détermine quand envoyer une notification. Chaque niveau inclut
les états plus graves : `critical`, `warning`, `unknown`, `always`.

## Vérifier la signature {#verifying-the-signature}

L’URL d’un webhook est souvent sa seule protection. `--webhook-secret` ou
`COS_WEBHOOK_SECRET` ajoute une signature avec secret partagé pour que le
récepteur distingue une notification authentique d’une notification forgée :

```shell
export COS_WEBHOOK_SECRET='a-long-random-string'
check-opencloud-security --host opencloud.example.com --webhook-on warning
```

Chaque requête POST contient alors :

```
X-COS-Signature: sha256=<hex>
```

`<hex>` est le **HMAC-SHA256 du corps brut de la requête**, calculé avec le
secret. Le plugin sérialise le corps une seule fois et envoie exactement ces
octets. Le récepteur doit vérifier les octets reçus sans réencoder le document
JSON : une différence d’espacement ou d’ordre des clés change l’empreinte.

```python
import hashlib
import hmac

def verify(raw_body: bytes, header: str, secret: str) -> bool:
    """raw_body must be the untouched request body, not a re-serialised dict."""
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, header or "")
```

Utilisez `hmac.compare_digest` plutôt que `==`. Une comparaison qui s’arrête
à la première différence peut révéler la partie correcte d’une signature
essayée.

Avec FastAPI, lisez le corps brut avec `await request.body()` ; avec Flask,
utilisez `request.get_data()`. Un framework qui ne fournit qu’un objet déjà
analysé ne permet pas de vérifier cette signature. Lisez alors le corps avant
son analyse.

Trois précisions :

- **La signature couvre tout le document envoyé**, y compris les formats
  `--webhook-format slack`, `discord`, `ntfy` et `gotify`. Ces services
  ignorent l’en-tête ; d’autres récepteurs peuvent le vérifier.
- **Sans secret configuré, aucun en-tête de signature n’est envoyé.** Un
  récepteur qui exige une signature doit rejeter les requêtes sans cet en-tête.
- **Le secret donne accès au service.** Comme l’URL, gardez-le hors de la
  ligne de commande. Voir [Configuration et secrets](../README.md#configuration-file-and-secrets).

## Uptime Kuma {#uptime-kuma}

Uptime Kuma n’a pas de système de plugins. Son moniteur **Push** attend des
appels réguliers sur une URL, ce que le webhook peut fournir. La configuration
comporte trois étapes.

**1. Créez le moniteur.** Dans Uptime Kuma, choisissez *Add New Monitor*, puis
le type **Push**, et donnez-lui le nom de l’instance. Uptime Kuma affiche une
*Push URL* comme `https://kuma.example.com/api/push/<token>`. Réglez *Heartbeat
Interval* légèrement au-dessus de l’intervalle du contrôle : par exemple,
300 secondes pour un contrôle toutes les quatre minutes. Un scan lent ne sera
ainsi pas immédiatement signalé comme une panne.

**2. Dirigez le webhook vers cette URL** avec `--webhook-on always` pour
signaler aussi les résultats sains. Sinon, Uptime Kuma ne recevrait que les
échecs et interpréterait le silence comme une panne :

```shell
check-opencloud-security --host opencloud.example.com \
  --webhook-url 'https://kuma.example.com/api/push/<token>' \
  --webhook-on always
```

Préférez le fichier de configuration pour éviter d’afficher le jeton dans la
liste des processus :

```yaml
host: opencloud.example.com
webhook:
  url: secret://kuma_push_url
  on: always
```

**3. Planifiez l’exécution.** Voir [Minuterie systemd](scheduling.md#systemd-timer)
ou [cron](scheduling.md#cron). Uptime Kuma signale une panne lorsqu’aucun appel
n’arrive dans l’intervalle prévu. Il détecte donc aussi un plugin qui ne peut
plus s’exécuter.

Un moniteur Push enregistre le statut fourni selon son propre protocole. Ne
comptez pas sur lui pour interpréter le JSON générique du plugin comme un
verdict OpenCloud. Pour transmettre l’état mesuré, convertissez le résultat en
paramètres `status` et `msg` de l’URL Push. Ces champs peuvent servir à écrire
un adaptateur :

| Champ du document | Information pour Uptime Kuma |
|:------------------|:----------------------------|
| `status` / `exit_code` | `OK`, `WARNING`, `CRITICAL` ou `UNKNOWN` |
| `message` | Explication sur une ligne pour l’alerte |
| `rating`, `rating_label` | Note de `0` à `5` et libellé de `A` à `F` |
| `product_version`, `eol` | Version OpenCloud et fin de sa maintenance |
| `update.availableVersion` | Version recommandée pour la mise à jour |
| `duration_seconds` | Durée du scan |

Pour signaler tout résultat autre que OK comme une panne, utilisez un script
qui envoie le statut Push adapté :

```shell
check-opencloud-security --host opencloud.example.com \
  && curl -fsS 'https://kuma.example.com/api/push/<token>?status=up' \
  || curl -fsS 'https://kuma.example.com/api/push/<token>?status=down&msg=opencloud'
```

Un appel régulier direct permet de détecter les exécutions manquantes.
Utilisez le script ou un adaptateur qui interprète le résultat si le moniteur
doit aussi refléter l’état du contrôle de sécurité.

## Slack, Mattermost, Discord {#slack-mattermost-discord}

Ces services attendent leur propre format JSON. `--webhook-format slack` ou
`--webhook-format discord` l’envoie directement, sans adaptateur :

```shell
check-opencloud-security --host opencloud.example.com \
  --webhook-url https://hooks.slack.com/services/... \
  --webhook-format slack
```

Mattermost accepte aussi le format `slack`, ainsi que le connecteur webhook du
pont Matrix [matrix-hookshot](https://matrix-org.github.io/matrix-hookshot/).
Il n’existe pas de format `matrix` séparé, car ces services partagent le même
contrat de webhook. Discord accepte aussi `slack` à l’adresse
`<webhook-url>/slack` si vous préférez une pièce jointe simple à un encart.

L’adaptateur suivant sert aux besoins que les formats intégrés ne couvrent
pas : couleurs personnalisées, champs supplémentaires ou récepteur dont le
format diffère légèrement de Slack ou Discord.

```python
#!/usr/bin/env python3
"""Forward a check-opencloud-security notification to a Slack-style webhook."""
import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

SLACK_URL = os.environ["SLACK_WEBHOOK_URL"]
COLOURS = {"OK": "#2eb886", "WARNING": "#daa038", "CRITICAL": "#a30200", "UNKNOWN": "#767676"}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        text = f"*{payload['host']}* - {payload['status']}\n{payload['message']}"
        if payload.get("rating_label"):
            text += f"\nRating {payload['rating_label']}, OpenCloud {payload.get('product_version', '?')}"

        body = json.dumps({
            "attachments": [{
                "color": COLOURS.get(payload["status"], "#767676"),
                "text": text,
            }]
        }).encode()
        request = urllib.request.Request(
            SLACK_URL, data=body, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(request, timeout=10):
            pass

        self.send_response(204)
        self.end_headers()


HTTPServer(("127.0.0.1", 8099), Handler).serve_forever()
```

Écoutez uniquement sur localhost et exécutez l’adaptateur à côté du contrôle.
Un adaptateur accessible à distance devient un relais ouvert vers votre
messagerie.

Discord accepte un document compatible à `<webhook-url>/slack`. Mattermost
accepte directement le format Slack.

## ntfy et Gotify {#ntfy-and-gotify}

Ces deux formats sont intégrés et ne nécessitent aucun adaptateur :

```shell
check-opencloud-security --host opencloud.example.com \
  --webhook-url https://ntfy.example.com/opencloud \
  --webhook-format ntfy

check-opencloud-security --host opencloud.example.com \
  --webhook-url https://gotify.example.com/message \
  --webhook-header 'X-Gotify-Key: ...' \
  --webhook-format gotify
```

**Pour ntfy, indiquez l’URL du sujet.** ntfy ne lit une publication JSON qu’à
la racine du serveur et prend le sujet dans le document. Le plugin extrait
donc le sujet de l’URL configurée, puis envoie le document à la racine du même
serveur. Le schéma, l’hôte et le port restent identiques : la protection SSRF
vérifie bien l’adresse qui reçoit la requête. Une URL sans sujet est refusée
au démarrage, au lieu de provoquer une erreur 400 à chaque notification.
C’est le seul format qui réécrit l’URL, et seul le chemin change. Voir
[ADR 0040](../../adr/0040-a-push-format-may-rewrite-the-path-never-the-host.md).

**Pour Gotify, gardez si possible le jeton hors de l’URL.** `?token=...`
fonctionne et le plugin le masque dans ses journaux. Toutefois,
`--webhook-header 'X-Gotify-Key: ...'` le retire entièrement de l’URL, y
compris dans les journaux des proxys intermédiaires. Dans les deux cas,
`--webhook-secret` signe toujours le corps avec `X-COS-Signature`.

La priorité suit l’état : CRITICAL utilise `urgent` pour ntfy et 8 pour
Gotify ; WARNING utilise `default` et 5 ; UNKNOWN utilise `high` et 5.
Un état OK, envoyé uniquement avec `--webhook-on always`, utilise la priorité
la plus basse pour confirmer l’exécution sans déranger les destinataires.

### Utiliser un script intermédiaire {#doing-it-in-a-wrapper-instead}

Cette solution permet d’envoyer le texte complet du plugin plutôt que son
résumé, ou de choisir vos propres priorités. Elle convient aussi à d’autres
services de notification d’échec :

```shell
#!/bin/sh
set -eu
output="$(check-opencloud-security --host opencloud.example.com --check-hardening)" || state=$?
state="${state:-0}"

case "$state" in
  0) exit 0 ;;                       # nothing to say
  1) priority=default ;;
  2) priority=urgent ;;
  *) priority=high ;;
esac

printf '%s' "$output" | curl -sS \
  -H "Title: OpenCloud security check" \
  -H "Priority: $priority" \
  -H "Tags: warning" \
  -d @- https://ntfy.example.com/opencloud
```

Conservez `|| state=$?` : le code de sortie du plugin représente le résultat.
Sans cette clause, `set -e` arrêterait le script au moment où il faut envoyer
une notification.

## Alertmanager {#alertmanager}

L’API v2 d’Alertmanager attend une liste d’alertes. Une alerte cesse d’être
active quand elle n’est plus renouvelée :

```shell
check-opencloud-security --host opencloud.example.com --webhook-url \
  http://127.0.0.1:8098/  # an adapter that posts to /api/v2/alerts
```

```json
[{
  "labels": {
    "alertname": "OpenCloudSecurity",
    "instance": "opencloud.example.com",
    "severity": "critical"
  },
  "annotations": {"summary": "<message from the payload>"},
  "startsAt": "<timestamp from the payload>"
}]
```

N’envoyez une alerte que pour les états qui doivent déclencher une
notification. Laissez-la expirer au lieu de la résoudre manuellement : le
prochain scan peut n’arriver que le lendemain, et une résolution anticipée
masquerait une instance encore vulnérable. Si vous publiez déjà des
métriques, passez par [Prometheus et Grafana](prometheus.md).

## Tester un récepteur sans instance {#testing-a-receiver-without-an-instance}

`--webhook-on always` avec un hôte inexistant envoie un vrai document d’échec.
C’est souvent ce format que les récepteurs traitent mal :

```shell
check-opencloud-security --host does-not-exist.example.com \
  --webhook-url http://127.0.0.1:8099/ --webhook-on always
```

Pour tester le format d’un scan réussi, utilisez une instance qui vous
appartient. `--debug` indique qu’un webhook a été envoyé et vers quelle
adresse, mais n’affiche pas le corps. Pour le lire, utilisez un récepteur de
test qui affiche les requêtes reçues.

---

[Retour à l’index de la documentation](../../README.md) | [Retour au README principal](../README.md)
