# Run the OpenCloud Security Scanner on Kubernetes

# Kubernetes

Auf Kubernetes können Sie den Scanner als zeitgesteuerten `CronJob` oder als dauerhaftes `Deployment` des [Scan-Dienstes](../../README.md#running-the-scanner-as-a-service) betreiben. Der Dienst eignet sich für mehrere Anwendungen, die ein Ergebnis gemeinsam nutzen; für regelmäßige Prüfungen genügt meist der CronJob.

Bauen Sie das Image wie unter [Docker](../installation.md#docker) beschrieben und übertragen Sie es in Ihre Registry. Ersetzen Sie in den Beispielen `registry.example.com/check-opencloud-security:1.1.0`. Verwenden Sie einen festen Tag, da Release-Zeitplan und bekannte Versionen Teil des Images sind.

## Helm-Chart {#the-helm-chart}

[`contrib/helm/check-opencloud-security`](../../contrib/helm/check-opencloud-security) enthält beide Varianten. Das Chart wird aus einem Checkout installiert und ist nicht in einer Registry veröffentlicht:

```shell
helm install opencloud-security contrib/helm/check-opencloud-security \
  --namespace monitoring --create-namespace \
  --set image.tag=<the release you pinned> \
  --set 'cronJob.hosts={opencloud.example.com,other.example.com}'
```

Dieser Aufruf richtet den zeitgesteuerten Scan ein. Mit `scanService.enabled=true` ergänzen Sie den Dienst. Die jeweils benötigten Werte müssen ausdrücklich gesetzt werden:

| Wert | Grund |
|:--|:--|
| `image.tag` | Die im Image enthaltenen Referenzdaten sollen mit einer bekannten Version festgelegt sein |
| `cronJob.hosts` | Der aktivierte CronJob benötigt mindestens ein Scanziel |
| `scanService.existingSecret` | Der aktivierte Scan-Dienst benötigt ein vorhandenes Secret für sein Token |
| `scanService.networkPolicy.allowedTargets` | Die aktivierte NetworkPolicy benötigt die erlaubten Ziele für ausgehende Verbindungen |

Das Chart erzeugt keine Zugangsdaten. Erstellen Sie die Secrets vorher und verweisen Sie darauf. Die vollständige Wertetabelle steht im [Chart-README](../../contrib/helm/check-opencloud-security/README.md).

Die folgenden Manifeste können Sie auch direkt anwenden oder als Grundlage für die Prüfung des gerenderten Charts verwenden.

## Zeitgesteuerter Scan {#a-scheduled-scan}

Ein `CronJob` entspricht dem [systemd-Timer](../scheduling.md). Da Kubernetes den Exitcode auswertet, erscheinen WARNING und CRITICAL als fehlgeschlagene Jobs.

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

Das Image läuft bereits als unprivilegierter Benutzer `nagios`. Für dieses Beispiel kann das Root-Dateisystem mit `readOnlyRootFilesystem` schreibgeschützt bleiben.

`COS_RELEASES_TOKEN` ist optional. Ohne Token erfolgt die GitHub-Update-Abfrage anonym und teilt das IP-bezogene Kontingent mit anderen Anfragen. Siehe [Update-Prüfung](../../README.md#update-check).

```shell
kubectl create secret generic opencloud-security \
  --namespace monitoring --from-literal=releases-token='<github-token>'

# Run it once now instead of waiting for the schedule:
kubectl create job --from=cronjob/opencloud-security opencloud-security-now \
  --namespace monitoring
kubectl logs job/opencloud-security-now --namespace monitoring
```

## Ergebnisse versenden {#sending-the-result-somewhere}

Mit einem Webhook erhalten Sie neben dem Jobstatus auch den Grund für den Befund. Siehe [Webhook-Beispiele](../webhook-recipes.md) und [Uptime Kuma](../webhook-recipes.md#uptime-kuma):

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

Verwenden Sie für Push-Empfänger `--webhook-on=always`, wenn auch erfolgreiche Durchläufe gemeldet werden sollen. Beim Standard `critical` erfährt der Empfänger nur von kritischen Ergebnissen und kann einen erfolgreichen Lauf nicht von einem ausgebliebenen Job unterscheiden.

## Scan-Dienst {#the-scan-service}

Der Dienst stellt einen gemeinsamen Ergebniscache für Dashboards, Skripte und andere Verbraucher bereit. Das Monitoring-Plugin verwendet ihn nicht; es führt seine Scans selbst aus.

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

`/healthz` ist ohne Token erreichbar und eignet sich als Probe. Alle anderen Endpunkte erfordern ein Token:

```shell
kubectl run curl --rm -it --image=curlimages/curl --restart=Never -- \
  curl -sS -H "Authorization: $TOKEN" \
  'http://opencloud-scanner.monitoring:8811/api/scan?url=opencloud.example.com'
```

Beschränken Sie die ausgehenden Verbindungen des Pods mit einer `NetworkPolicy` auf die vorgesehenen Instanzen. Wer den Dienst aufrufen darf, sollte ihn nicht auf beliebige interne Clusterziele richten können.

---

[Zur Dokumentationsübersicht](../README.md) | [Zum Haupt-README](../../README.md)

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
