# Ejecutar el escáner de seguridad de OpenCloud en Kubernetes

Ejecute el escáner como un `CronJob` programado, o despliegue el
[servicio HTTP de análisis](../../README.md#running-the-scanner-as-a-service)
cuando varios consumidores necesiten un resultado compartido. Son opciones
independientes; para la mayoría de las comprobaciones programadas basta con un
CronJob.

La imagen se construye a partir de este repositorio; consulte
[Docker](../installation.md#docker). Súbala a su propio registro y sustituya
`registry.example.com/check-opencloud-security:1.1.0` en los ejemplos
siguientes. Fije una etiqueta en lugar de usar `latest`: el calendario de
versiones y la versión de OpenCloud más reciente conocida van *dentro* de la
imagen, así que la etiqueta que ejecute forma parte del veredicto.

<!-- TOC -->
* [Kubernetes](#kubernetes)
  * [El chart de Helm](#the-helm-chart)
  * [Un análisis programado](#a-scheduled-scan)
  * [Enviar el resultado a otro sistema](#sending-the-result-somewhere)
  * [El servicio de análisis](#the-scan-service)
<!-- TOC -->


## El chart de Helm {#the-helm-chart}

[`contrib/helm/check-opencloud-security`](../../contrib/helm/check-opencloud-security)
empaqueta los dos manifiestos siguientes. Instálelo desde una copia del
repositorio: no se publica en ningún registro, y leer lo que va a crear forma
parte del objetivo:

```shell
helm install opencloud-security contrib/helm/check-opencloud-security \
  --namespace monitoring --create-namespace \
  --set image.tag=<the release you pinned> \
  --set 'cronJob.hosts={opencloud.example.com,other.example.com}'
```

Eso instala el análisis programado y nada más; `scanService.enabled=true`
añade el servicio descrito más abajo. Cuatro valores no tienen valor
predeterminado, y una instalación que omita alguno se rechaza en lugar de
generarse:

| Valor | Por qué no tiene valor predeterminado |
|:--|:--|
| `image.tag` | El calendario de versiones va dentro de la imagen, así que `latest` permitiría que el veredicto cambiara bajo una alerta activa |
| `cronJob.hosts` | Un Job sin host no analiza nada, cada día, mientras aparenta ser monitorización |
| `scanService.existingSecret` | Un servicio de análisis sin token analiza cualquier host que indique quien llegue al pod |
| `scanService.networkPolicy.allowedTargets` | Una política sin regla de salida es otra política, no una política sin terminar |

Todas las credenciales se leen de un `Secret` que usted ha creado y nombrado;
el chart no escribe ninguna, porque un archivo de valores se confirma en el
repositorio y se copia, y un token que ha estado en uno no se olvida
fácilmente. El
[README del chart](../../contrib/helm/check-opencloud-security/README.md)
contiene la tabla completa de valores.

El resto de esta página es lo que genera el chart, para quien prefiera aplicar
el YAML directamente o leerlo antes de instalar.


## Un análisis programado {#a-scheduled-scan}

Un `CronJob` es lo más parecido al temporizador de systemd de
[Programación](../scheduling.md). El código de salida decide si el trabajo ha
fallado, así que Kubernetes muestra un resultado WARNING o CRITICAL como un
trabajo fallido sin ningún componente adicional.

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

La imagen ya se ejecuta como el usuario sin privilegios `nagios` y no escribe
nada, así que `readOnlyRootFilesystem` no tiene ningún coste.

`COS_RELEASES_TOKEN` es opcional. Sin él, la comprobación de actualizaciones
usa GitHub de forma anónima, y las sesenta solicitudes por hora se comparten
con todo lo demás que sale desde esa dirección; consulte
[Comprobación de actualizaciones](../../README.md#update-check).

```shell
kubectl create secret generic opencloud-security \
  --namespace monitoring --from-literal=releases-token='<github-token>'

# Run it once now instead of waiting for the schedule:
kubectl create job --from=cronjob/opencloud-security opencloud-security-now \
  --namespace monitoring
kubectl logs job/opencloud-security-now --namespace monitoring
```

## Enviar el resultado a otro sistema {#sending-the-result-somewhere}

Un trabajo fallido es una señal poco precisa. Añada el webhook y el resultado
llegará con el motivo adjunto; consulte
[Recetas de webhooks](../webhook-recipes.md) y
[Uptime Kuma](../webhook-recipes.md#uptime-kuma):

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

`--webhook-on=always` es importante para un receptor de tipo push: con el
valor predeterminado `critical` solo recibe noticias de la comprobación cuando
algo va mal, y no puede distinguir una instancia sana de un trabajo que nunca
se ejecutó.

## El servicio de análisis {#the-scan-service}

Ejecútelo solo si varios consumidores necesitan el mismo resultado. El
complemento no se comunica con él (siempre analiza dentro de su propio
proceso), así que está pensado para paneles, scripts y sistemas de
monitorización secundarios.

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

`/healthz` no necesita token, lo que permite usarlo como sonda. Todos los demás
puntos de acceso sí lo necesitan:

```shell
kubectl run curl --rm -it --image=curlimages/curl --restart=Never -- \
  curl -sS -H "Authorization: $TOKEN" \
  'http://opencloud-scanner.monitoring:8811/api/scan?url=opencloud.example.com'
```

Asigne al pod una `NetworkPolicy` que solo le permita llegar a las instancias
que realmente analiza. Un servicio de análisis que puede llegar a todo el
clúster es un motor de falsificación de solicitudes con API REST.

---

[Volver al índice de la documentación](../README.md) | [Volver al README principal](../../README.md)
