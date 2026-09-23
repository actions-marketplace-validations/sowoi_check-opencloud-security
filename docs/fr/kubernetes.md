# Kubernetes

Exécutez le scanner comme un `CronJob` planifié, ou déployez le [service
d’analyse HTTP](../../README.md#running-the-scanner-as-a-service) lorsque plusieurs
consommateurs ont besoin d’un résultat partagé. Ces deux options sont indépendantes ;
un CronJob suffit pour la plupart des vérifications planifiées.

L'image est construite depuis ce dépôt ; voir
[Docker](installation.md#docker). Publiez-la dans votre registre et remplacez
`registry.example.com/check-opencloud-security:1.1.0` ci-dessous. Utilisez un
tag fixe plutôt que `latest` : le calendrier des versions et la dernière
version OpenCloud connue sont intégrés à l'image, donc le tag exécuté fait
partie du résultat.

<!-- TOC -->
* [Kubernetes](#kubernetes)
  * [Le chart Helm](#the-helm-chart)
  * [Une analyse planifiée](#a-scheduled-scan)
  * [Transmettre le résultat](#sending-the-result-somewhere)
  * [Le service d’analyse](#the-scan-service)
<!-- TOC -->


## Le chart Helm {#the-helm-chart}

[`contrib/helm/check-opencloud-security`](../../contrib/helm/check-opencloud-security)
regroupe les deux manifestes ci-dessous. Installez-le depuis une copie du dépôt :
il n’est pas publié dans un registre, et l’examen des objets rendus avant
l’installation fait partie du contrôle de sécurité :

```shell
helm install opencloud-security contrib/helm/check-opencloud-security \
  --namespace monitoring --create-namespace \
  --set image.tag=<the release you pinned> \
  --set 'cronJob.hosts={opencloud.example.com,other.example.com}'
```

Cela installe l’analyse planifiée et rien d’autre ; `scanService.enabled=true`
ajoute le service décrit plus bas. Quatre valeurs n’ont pas de valeur par
défaut, et une installation qui en omet une est refusée au lieu d’être rendue :

| Valeur | Pourquoi elle n’a pas de valeur par défaut |
|:--|:--|
| `image.tag` | Le calendrier des versions est livré dans l’image : `latest` permettrait au verdict de changer sous une alerte en cours |
| `cronJob.hosts` | Un Job sans hôte n’analyse rien, chaque jour, tout en ayant l’air d’une supervision |
| `scanService.existingSecret` | Un service d’analyse sans jeton analyse n’importe quel hôte indiqué par quiconque atteint le pod |
| `scanService.networkPolicy.allowedTargets` | Une politique sans règle de sortie est une autre politique, pas une politique inachevée |

Chaque identifiant est lu dans un `Secret` que vous avez créé et nommé ; le
chart n’en écrit aucun, car un fichier de valeurs peut être versionné et copié,
et un jeton qu’il contient serait copié avec lui. Le
[README du chart](../../contrib/helm/check-opencloud-security/README.md)
contient le tableau complet des valeurs.

La suite de cette page montre ce que rend le chart, pour qui préfère appliquer
directement le YAML ou le lire avant l’installation.


## Une analyse planifiée {#a-scheduled-scan}

Un `CronJob` est l’équivalent le plus proche du timer systemd décrit dans
[Planification](scheduling.md). Le code de sortie décide si la tâche a échoué :
Kubernetes présente donc un résultat WARNING ou CRITICAL comme une tâche en
échec, sans aucun intermédiaire.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: opencloud-security
  namespace: monitoring
spec:
  # Daily is right. Each run is a real scan of a real instance, not a lookup.
  schedule: "17 6 * * *"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 7
  jobTemplate:
    spec:
      # The plugin never retries the whole check itself; a rerun would only
      # scan the instance again a second later.
      backoffLimit: 0
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: check
              image: registry.example.com/check-opencloud-security:1.1.0
              args:
                - --host=opencloud.example.com
                - --port=9200
                - --check-hardening
                - --update-warning
              env:
                - name: COS_RELEASES_TOKEN
                  valueFrom:
                    secretKeyRef:
                      name: opencloud-security
                      key: releases-token
              resources:
                requests: {cpu: 50m, memory: 64Mi}
                limits: {memory: 256Mi}
              securityContext:
                allowPrivilegeEscalation: false
                readOnlyRootFilesystem: true
                capabilities:
                  drop: ["ALL"]
```

L’image s’exécute déjà avec l’utilisateur non privilégié `nagios` et n’écrit
rien : `readOnlyRootFilesystem` ne coûte donc rien.

`COS_RELEASES_TOKEN` est facultatif. Sans lui, la vérification des mises à jour
interroge GitHub de façon anonyme, et soixante requêtes par heure sont
partagées avec tout le reste du trafic sortant de cette adresse - voir
[Vérification des mises à jour](../../README.md#update-check).

```shell
kubectl create secret generic opencloud-security \
  --namespace monitoring --from-literal=releases-token='<github-token>'

# Run it once now instead of waiting for the schedule:
kubectl create job --from=cronjob/opencloud-security opencloud-security-now \
  --namespace monitoring
kubectl logs job/opencloud-security-now --namespace monitoring
```

## Transmettre le résultat {#sending-the-result-somewhere}

Une tâche en échec est un signal grossier. Ajoutez le webhook : le résultat
arrive alors accompagné de sa raison - voir les [exemples de webhooks](webhooks.md)
et [Uptime Kuma](webhooks.md#uptime-kuma) :

```yaml
              args:
                - --host=opencloud.example.com
                - --check-hardening
                - --webhook-url=$(WEBHOOK_URL)
                - --webhook-on=always
              env:
                - name: WEBHOOK_URL
                  valueFrom:
                    secretKeyRef: {name: opencloud-security, key: webhook-url}
```

`--webhook-on=always` compte pour un récepteur de type push : avec la valeur
par défaut `critical`, il n’a de nouvelles du contrôle qu’en cas de problème et
ne peut pas distinguer une instance saine d’une tâche qui ne s’est jamais
exécutée.

## Le service d’analyse {#the-scan-service}

Ne l’exécutez que si plusieurs consommateurs ont besoin du même résultat. Le
plugin ne l’utilise pas (il analyse toujours dans son propre processus) : ce
service sert donc aux tableaux de bord, aux scripts et aux systèmes de
supervision secondaires.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opencloud-scanner
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels: {app: opencloud-scanner}
  template:
    metadata:
      labels: {app: opencloud-scanner}
    spec:
      containers:
        - name: scanner
          image: registry.example.com/check-opencloud-security:1.1.0
          command: ["check-opencloud-scanner"]
          args: ["serve", "--port=8811", "--cache-ttl=900"]
          ports:
            - containerPort: 8811
          env:
            # Without a token every endpoint is open to anyone who can reach
            # the pod, and the scanner will scan any host they name.
            - name: COS_SERVICE_TOKEN
              valueFrom:
                secretKeyRef: {name: opencloud-security, key: service-token}
          livenessProbe:
            httpGet: {path: /healthz, port: 8811}
            periodSeconds: 30
          readinessProbe:
            httpGet: {path: /healthz, port: 8811}
            periodSeconds: 10
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
---
apiVersion: v1
kind: Service
metadata:
  name: opencloud-scanner
  namespace: monitoring
spec:
  selector: {app: opencloud-scanner}
  ports:
    - port: 8811
      targetPort: 8811
```

`/healthz` ne demande pas de jeton, ce qui permet de l’utiliser comme sonde.
Tous les autres points de terminaison en exigent un :

```shell
kubectl run curl --rm -it --image=curlimages/curl --restart=Never -- \
  curl -sS -H "Authorization: $TOKEN" \
  'http://opencloud-scanner.monitoring:8811/api/scan?url=opencloud.example.com'
```

Donnez au pod une `NetworkPolicy` qui ne lui permet d’atteindre que les
instances que vous analysez réellement. Un service d’analyse qui peut atteindre
tout le cluster est une machine à falsifier des requêtes dotée d’une API REST.

---

[Retour à l’index de la documentation](../README.md) | [Retour au README principal](../../README.md)
