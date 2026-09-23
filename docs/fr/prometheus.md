# Prometheus et Grafana {#prometheus-and-grafana}

Le plugin intègre un exportateur Prometheus. Lancez-le avec
`--prometheus-listen-port 9102` pour exposer `/metrics`. Il conserve le résultat
pendant `--scrape-interval` secondes (60 par défaut) : une collecte durant ce délai
ne déclenche pas de nouvelle analyse. Utilisez `0` si chaque collecte doit en lancer
une. L’adresse d’écoute par défaut est `127.0.0.1`. N’utilisez
`--prometheus-listen-addr 0.0.0.0` que si un pare-feu ou une politique réseau limite
l’accès aux collecteurs autorisés. Dans un conteneur, ce réglage est nécessaire,
ainsi que la publication du port :

```shell
docker run --rm -p 9102:9102 check-opencloud-security \
  --host opencloud.example.com --prometheus-listen-port 9102 \
  --prometheus-listen-addr 0.0.0.0
```

Pour une tâche ponctuelle, `--format=prometheus` affiche les métriques au format
texte puis se termine. `--format=otlp` affiche les mêmes métriques dans le document
OTLP/JSON attendu par un collecteur OpenTelemetry. Aucun de ces modes ne nécessite
de dépendance supplémentaire.

Les exemples de collecteur textfile et de Pushgateway ci-dessous conviennent
lorsqu’une analyse planifiée répond mieux au besoin qu’un exportateur permanent.

Si vous utilisez déjà Icinga2, ses modules Graphite/InfluxDB récupèrent directement
les [données de performance](../README.md#performance-data) du plugin.

<!-- TOC -->
* [Prometheus et Grafana](#prometheus-and-grafana)
  * [Fichiers à copier](#the-files-to-copy)
  * [Métriques publiées par l’exportateur](#what-the-exporter-publishes)
  * [Données à représenter](#what-there-is-to-graph)
  * [Collecteur textfile de node_exporter](#node_exporter-textfile-collector)
  * [Pushgateway](#pushgateway)
  * [Collecteur OpenTelemetry](#opentelemetry-collector)
  * [Règles d’alerte](#alerting-rules)
  * [Grafana](#grafana)
<!-- TOC -->

## Fichiers à copier {#the-files-to-copy}

Deux fichiers dans [`contrib/`](../../contrib/README.md) utilisent les noms des
métriques de l’exportateur intégré :

| Fichier | Utilisation |
|:--|:--|
| [`contrib/prometheus/alerts.yml`](../../contrib/prometheus/alerts.yml) | Copiez-le dans `/etc/prometheus/rules/` et ajoutez-le à `rule_files:` |
| [`contrib/grafana/dashboard.json`](../../contrib/grafana/dashboard.json) | Dans Grafana, choisissez Dashboards, New, Import, puis la source de données |

```shell
cp contrib/prometheus/alerts.yml /etc/prometheus/rules/opencloud-security.yml
promtool check rules /etc/prometheus/rules/opencloud-security.yml
```

Le sélecteur `Instance` permet d’utiliser ce tableau de bord pour plusieurs cibles.
Réglez les délais d’alerte selon le temps de réaction souhaité et la fréquence des
analyses. Plusieurs collectes peuvent contenir le même résultat en cache.

Les exemples qui suivent le tableau des métriques proposent une autre méthode :
une analyse planifiée dont `jq` transforme le JSON en métriques personnalisées.
Leurs noms, plus courts, diffèrent de ceux des deux fichiers fournis ci-dessus.

## Métriques publiées par l’exportateur {#what-the-exporter-publishes}

| Métrique | Étiquettes | Signification |
|:--|:--|:--|
| `opencloud_security_rating_score` | `host`, `domain`, `product`, `version` | Note de `0` à `5`, où `5` est la meilleure |
| `opencloud_security_end_of_life` | `host`, `release_type` | `1` lorsque la version ne reçoit plus de correctifs |
| `opencloud_security_support_days_remaining` | `host`, `release_type` | Jours de support restants ; **aucun échantillon** si la fin de vie n’est pas encore datée |
| `opencloud_security_vulnerabilities_total` | `host`, `severity` | Avis de sécurité qui concernent la version détectée |
| `opencloud_security_hardenings_missing_total` | `host` | Mesures de durcissement manquantes |
| `opencloud_security_failed_extra_checks_total` | `host` | Contrôles supplémentaires en échec |
| `opencloud_security_update_available` | `host`, `target_version` | `1` si une version plus récente existe |
| `opencloud_security_certificate_days_remaining` | `host` | Jours avant l’expiration du certificat présenté ; valeur négative après expiration, aucun échantillon en HTTP simple |
| `opencloud_security_upgrade_path_complete` | `host`, `target_version` | `1` si la mise à jour recommandée corrige toutes les vulnérabilités connues ; aucun échantillon sinon |
| `opencloud_security_waiver_days_remaining` | `host` | Jours avant la fin d’une exemption `--waive-until` qui laisse un contrôle en échec alerter de nouveau ; aucun échantillon si aucun contrôle en échec ne dépend d’une échéance |
| `opencloud_security_coverage_inconclusive_total` | `host` | Contrôles exécutés par l’analyse sans conclusion |
| `opencloud_security_coverage_not_checked_total` | `host` | Contrôles que l’analyse n’a pas exécutés |
| `opencloud_security_scan_duration_seconds` | `host` | Durée de l’analyse |
| `opencloud_security_scrape_success` | `host` | `0` si l’analyse a échoué |

Une analyse en échec ne publie que les deux dernières métriques. Les constats de
l’analyse précédente ne sont pas republiés. L’instance reste donc sans verdict,
plutôt qu’avec un verdict périmé. Le tableau de bord affiche pour cette raison
`opencloud_security_scrape_success` en premier.

`opencloud_security_end_of_life` est une métrique distincte du nombre de jours
restants. Une version rolling ou production sans date de fin de vie annoncée ne
publie aucun nombre de jours : une date inconnue ne doit pas déclencher une alerte
qui signifierait « expire aujourd’hui ».

## Données à représenter {#what-there-is-to-graph}

Chaque exécution affiche des données de performance après `|` :

```
rating=5;@0:3;@0:1;0;5 vulnerabilities=0;;;0; time=1.234s;;;0;
```

| Métrique | Signification |
|:-------|:--------|
| `rating` | De `0` à `5` : `5` correspond à A+ et `0` à F ; `U` si l’analyse a échoué |
| `vulnerabilities` | Vulnérabilités connues de la version installée |
| `time` | Durée de l’analyse en secondes |
| `hardenings_missing` | Mesures de durcissement manquantes, uniquement avec `--check-hardening` |
| `extra_checks_failed` | Contrôles supplémentaires en échec |
| `update_available` | `1` si une version plus récente existe |
| `support_days_left` | Jours de support restants ; valeur négative après la fin du support |
| `waiver_days_left` | Jours avant la fin d’une exemption temporaire ; absente si aucune ne masque un contrôle en échec |
| `coverage_inconclusive` | Contrôles que l’analyse n’a pas pu trancher |
| `coverage_not_checked` | Contrôles que l’analyse n’a pas exécutés |

Une alerte sur `support_days_left` permet de repérer une version qui ne reçoit
plus de correctifs.

## Collecteur textfile de node_exporter {#node_exporter-textfile-collector}

Le JSON du scanner est plus facile à traiter que la ligne de données de performance.
Cet exemple utilise donc `check-opencloud-scanner` et transforme le résultat avec
`jq`. Écrivez dans un fichier temporaire, puis renommez-le : node_exporter ne doit
pas lire un fichier partiellement écrit.

```shell
#!/bin/sh
# /usr/local/bin/opencloud-metrics - run from a systemd timer, see scheduling.md
set -eu

HOST="opencloud.example.com"
OUT="/var/lib/node_exporter/textfile_collector/opencloud_security.prom"
TMP="$(mktemp "${OUT}.XXXXXX")"

check-opencloud-scanner scan --compact "$HOST" > /tmp/opencloud-scan.json || true

jq -r --arg host "$HOST" '
  if .error then
    "opencloud_scan_success{host=\"\($host)\"} 0"
  else
    "opencloud_scan_success{host=\"\($host)\"} 1",
    "opencloud_security_rating{host=\"\($host)\"} \(.rating)",
    "opencloud_end_of_life{host=\"\($host)\"} \(if .EOL then 1 else 0 end)",
    "opencloud_vulnerabilities{host=\"\($host)\"} \(.vulnerabilities | length)",
    "opencloud_update_available{host=\"\($host)\"} \(if .updates.available then 1 else 0 end)",
    "opencloud_support_days_left{host=\"\($host)\"} \(.lifecycle.daysRemaining // 0)",
    "opencloud_failed_checks{host=\"\($host)\"} \([.extraChecks[] | select(.passed == false and .ignored == false)] | length)",
    "opencloud_version_info{host=\"\($host)\",version=\"\(.version)\",track=\"\(.releaseType)\"} 1"
  end' /tmp/opencloud-scan.json > "$TMP"

mv "$TMP" "$OUT"
chmod 644 "$OUT"
```

`opencloud_scan_success` signale les échecs d’analyse. Sans cette métrique, une
analyse en échec pourrait sembler saine, car les autres valeurs restent en place
jusqu’au remplacement du fichier.

`lifecycle.daysRemaining` vaut `null` si la date de fin de vie n’est pas connue.
C’est le cas d’une version rolling ou production qui expire à la sortie de sa
successeure. Le `// 0` ci-dessus convertit cette valeur en `0`. Si vos alertes
interprètent cela comme « expire aujourd’hui », omettez plutôt la ligne avec
`select(.lifecycle.daysRemaining != null)`.

## Pushgateway {#pushgateway}

Utilisez le même JSON avec une autre destination. Prévoyez une clé de regroupement
par hôte : si les analyses d’un hôte s’arrêtent, sa dernière valeur reste visible
sans se mélanger à celles des autres hôtes.

```shell
check-opencloud-scanner scan --compact opencloud.example.com \
  | jq -r '
      "# TYPE opencloud_security_rating gauge",
      "opencloud_security_rating \(.rating)",
      "# TYPE opencloud_support_days_left gauge",
      "opencloud_support_days_left \(.lifecycle.daysRemaining // 0)"' \
  | curl -sS --data-binary @- \
      http://pushgateway.example.com:9091/metrics/job/opencloud_security/instance/opencloud.example.com
```

Pushgateway ne supprime pas les métriques de lui-même. Quand vous retirez une
instance, supprimez son groupe pour éviter les alertes sur un serveur qui n’existe
plus :

```shell
curl -X DELETE http://pushgateway.example.com:9091/metrics/job/opencloud_security/instance/opencloud.example.com
```

## Collecteur OpenTelemetry {#opentelemetry-collector}

`--format otlp` produit un document OTLP/JSON `ExportMetricsServiceRequest` avec
les métriques du tableau. Un collecteur le reçoit à `/v1/metrics` via OTLP/HTTP.
Le plugin affiche le document ; `curl` l’envoie depuis le même
[timer systemd ou la même tâche cron](scheduling.md) que l’analyse :

```shell
check-opencloud-security --host opencloud.example.com,other.example.com \
  --format otlp \
  | curl -sf -X POST http://collector.example.com:4318/v1/metrics \
      -H 'Content-Type: application/json' --data-binary @-
```

Les noms de métriques et l’attribut `host` sont ceux de l’exportateur. Les requêtes
prévues pour une collecte fonctionnent donc aussi avec les données du collecteur.
Seules les conventions d’étiquetage de votre système peuvent nécessiter une
adaptation des règles d’alerte. L’adresse du collecteur, le proxy et les
identifiants d’accès restent dans les arguments de `curl`.

Une analyse en échec publie `opencloud_security_scrape_success` à `0`, avec sa
durée et sans constats. L’échec reste ainsi visible, sans reprendre les chiffres
de la dernière analyse réussie.

## Règles d’alerte {#alerting-rules}

Pour l’exportateur intégré, copiez
[`contrib/prometheus/alerts.yml`](../../contrib/prometheus/alerts.yml). Ce fichier
est maintenu et testé avec les noms de métriques réellement publiés.

Les règles ci-dessous utilisent les noms personnalisés produits par **`jq`** dans
les deux exemples précédents :

```yaml
groups:
  - name: opencloud-security
    rules:
      - alert: OpenCloudEndOfLife
        expr: opencloud_end_of_life == 1
        for: 1h
        labels: {severity: critical}
        annotations:
          summary: "{{ $labels.host }} runs an OpenCloud release with no security fixes"

      - alert: OpenCloudSupportRunningOut
        expr: opencloud_support_days_left < 30 and opencloud_support_days_left > 0
        for: 6h
        labels: {severity: warning}
        annotations:
          summary: "{{ $labels.host }} loses support in {{ $value }} days"

      - alert: OpenCloudRatingDropped
        expr: opencloud_security_rating <= 3
        for: 1h
        labels: {severity: warning}
        annotations:
          summary: "{{ $labels.host }} is rated {{ $value }}/5"

      - alert: OpenCloudScanFailing
        # A scan that no longer runs is the failure mode that hides all others.
        expr: opencloud_scan_success == 0 or absent(opencloud_scan_success)
        for: 2h
        labels: {severity: warning}
        annotations:
          summary: "The OpenCloud security scan has not produced a result"
```

Dans Prometheus, `for:` mesure la durée pendant laquelle une expression reste vraie
au fil des évaluations. Il ne compte pas les nouvelles analyses. Avec une analyse
quotidienne, `for: 5m` attend cinq minutes pendant lesquelles le même échec en cache
reste visible ; il n’attend pas une seconde analyse quotidienne.

## Grafana {#grafana}

Importez [`contrib/grafana/dashboard.json`](../../contrib/grafana/dashboard.json)
et choisissez votre source Prometheus. Le tableau de bord affiche d’abord l’état
de l’analyse, puis la note et le cycle de vie, l’évolution de la note, les constats
non résolus, les avis par gravité et les versions de chaque instance.

Pour créer votre propre tableau, utilisez un panneau de type stat avec des seuils
à `3` (jaune) et `1` (rouge), comme les seuils par défaut du plugin. La note va de
`0` à `5`, où une valeur élevée est meilleure. Associez les valeurs aux lettres
utilisées dans la sortie : `5 → A+`, `4 → A`, `3 → C`, `2 → D`, `1 → E`, `0 → F`.
Cela évite de les lire comme une note scolaire sur cinq.

Affichez la version dans un tableau voisin. La note signale un problème ; la
version aide à déterminer si une mise à jour peut le résoudre.

---

[Retour à l’index de la documentation](../../README.md) | [Retour au README principal](../README.md)
