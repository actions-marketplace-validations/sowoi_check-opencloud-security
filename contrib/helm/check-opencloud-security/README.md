# check-opencloud-security Helm chart

The two Kubernetes workloads from
[`docs/kubernetes.md`](../../../docs/kubernetes.md), as a chart: a `CronJob`
that scans instances on a schedule, and - off by default - the shared scan
service several consumers can query.

The chart is not published to a registry. Install it from a checkout of this
repository, which is also how you read what it will create before it creates
it.

```shell
helm install opencloud-security contrib/helm/check-opencloud-security \
  --namespace monitoring --create-namespace \
  --set image.tag=<the release you pinned> \
  --set 'cronJob.hosts={opencloud.example.com}'
```

`image.tag` has no default on purpose. The release schedule and the newest
known OpenCloud version ship *inside* the image, so which tag you run is part
of the verdict; the chart refuses to render without one rather than following
`latest` into a changed answer.

## What goes where

| Value | |
|:--|:--|
| `image.repository`, `image.tag` | The image you built and pushed - see [Docker](../../../docs/installation.md#docker) |
| `cronJob.hosts` | The instances to scan. Several are one Job, and the worst result decides the exit code |
| `cronJob.schedule` | Daily is right. Each run is a real scan, not a lookup |
| `cronJob.checkHardening` | On by default, as in every other deployment this project ships |
| `cronJob.ignoreHardenings` | Findings you have accepted, by identifier - see [Hardening](../../../docs/hardening.md) |
| `cronJob.webhook` | Send the result somewhere with its reason attached - see [Webhook recipes](../../../docs/webhook-recipes.md) |
| `cronJob.extraArgs` | Any flag the values above do not cover, verbatim |
| `scanService.enabled` | The shared service. Only if several consumers need the same result |
| `scanService.networkPolicy` | Which instances that service may reach |

The exit code is what decides whether the Job failed, so a WARNING or CRITICAL
result surfaces as a failed Job with no extra glue. Note that
`cronJob.format: prometheus` and `otlp` exit `0` whatever the instance scored -
useful when something downstream reads the output, wrong when the Job's own
success is the signal.

## No credential is written by this chart

Every secret is read from a `Secret` you created, named in
`cronJob.existingSecret` / `scanService.existingSecret`. A values file is
committed, copied and templated by whatever deploys it, and a token in one
outlives every place you remember putting it.

```shell
kubectl create secret generic opencloud-security --namespace monitoring \
  --from-literal=releases-token='<github-token>' \
  --from-literal=webhook-url='https://hooks.example.com/…' \
  --from-literal=service-token="$(openssl rand -hex 32)"
```

`releases-token` is optional: without it the update check queries GitHub
anonymously, sharing sixty requests an hour with everything else leaving that
address. The scan service's token is not optional - the chart refuses to
render the service without one, because an untokened scan service will scan
any host anybody who can reach the pod names.

## The scan service and the network

```yaml
scanService:
  enabled: true
  existingSecret: opencloud-security
  networkPolicy:
    enabled: true
    allowedTargets:
      - cidr: 192.0.2.10/32
        ports: [9200]
```

A scan service that can reach the whole cluster is a request forgery engine
with a REST API. `allowedTargets` may not be empty when the policy is on: a
`NetworkPolicy` with no egress rule is not a restriction somebody forgot to
fill in, it is a different policy entirely.

The plugin never talks to this service - it always scans in process - so the
`CronJob` above needs none of this.

---

This project is not affiliated with, endorsed by or sponsored by OpenCloud
GmbH. "OpenCloud" and related marks belong to their respective owners and are
used only to identify the software being checked.
