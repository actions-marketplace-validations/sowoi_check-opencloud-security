# Formats de sortie {#machine-readable-output---format-json-sarif-junit}

Par défaut, le plugin affiche une ligne d’état Nagios et des données de performance.
Utilisez `--format` (`COS_FORMAT`) pour choisir un format destiné aux scripts,
tableaux de bord ou pipelines CI.

`--format json`, `--format sarif` et `--format junit` produisent **un document
combiné pour tous les hôtes analysés**, même si `--host` n’en contient qu’un.
La sortie reste donc un document JSON, SARIF ou XML valide, quel que soit le
nombre d’adresses.

**Le code de sortie conserve sa signification Nagios** : `0` (OK), `1` (WARNING),
`2` (CRITICAL), `3` (UNKNOWN). Une étape CI peut utiliser ce code comme un contrôle
Icinga. Le document est un résultat supplémentaire. Les formats de métriques
`prometheus` et `otlp` font exception : ils rapportent les constats sous forme
d’échantillons et terminent avec le code `0`.

<!-- TOC -->
* [Formats de sortie](#machine-readable-output---format-json-sarif-junit)
  * [`json`](#json)
  * [`sarif`](#sarif)
  * [`junit`](#junit)
  * [`checkmk`](#checkmk)
  * [`otlp`](#otlp)
  * [Choisir un format](#choosing-a-format)
<!-- TOC -->

## `json` {#json}

Un tableau JSON contient les documents décrits dans
[Notifications webhook](../README.md#webhook-notifications), à raison d’un objet
par hôte. La sortie reste un tableau pour un seul hôte. Utilisez ce format pour
traiter les résultats dans un script, un tableau de bord ou un autre système de
supervision.

```shell
check-opencloud-security --host opencloud.example.com --format json
```

## `sarif` {#sarif}

[SARIF](https://sarifweb.azurewebsites.net/) 2.1.0 convient aux tableaux de bord
d’analyse de code, dont celui de GitHub. Les constats proviennent des mêmes données
que la sortie texte : durcissement manquant, contrôles supplémentaires en échec,
vulnérabilités et fin de vie. Seule leur présentation change.

```shell
check-opencloud-security --host opencloud.example.com --format sarif \
  > opencloud-security.sarif
```

Chaque constat contient la correction proposée et le lien vers la documentation
(`help`, `helpUri`), la gravité et la catégorie (`security-severity`,
`problem.severity`, `tags`), les versions concernées par un avis (`affectedRanges`,
`fixedIn`) et une empreinte stable (`partialFingerprints`). Cette empreinte permet
de suivre une même alerte entre les exécutions. `run.properties.hosts` indique la
note, la version et l’état de fin de vie de chaque hôte.

Dans GitHub Actions, envoyez le fichier à l’analyse de code. Le réglage
`continue-on-error: true` empêche un code de sortie non nul d’arrêter la tâche avant
l’envoi. Les constats restent donc consultables même si l’analyse signale une
mauvaise note :

```yaml
- name: Scan OpenCloud
  run: |
    check-opencloud-security --host opencloud.example.com --format sarif \
      > opencloud-security.sarif
  continue-on-error: true
- uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: opencloud-security.sarif
```

## `junit` {#junit}

Le document JUnit XML contient une `<testsuite>` par hôte et un `<testcase>` par
constat. Un cas **`rating` est toujours présent**, afin qu’un hôte sans problème
apparaisse aussi dans le rapport. La plupart des outils JUnit interprètent
l’absence de cas comme une absence d’exécution.

```shell
check-opencloud-security --host opencloud.example.com --format junit \
  > opencloud-security.xml
```

La même méthode fonctionne dans tout système CI capable de présenter un rapport
JUnit. Configurez son outil de rapport pour lire le fichier produit.

## `checkmk` {#checkmk}

Une ligne de [contrôle local Checkmk](checkmk.md) par hôte contient l’état, le nom
du service entre guillemets, les métriques et les détails à lire par l’agent.

```shell
check-opencloud-security --host opencloud.example.com --format checkmk
```

Ce format produit une ligne par service, donc plusieurs lignes pour plusieurs
hôtes. Il sert uniquement aux contrôles exécutés par l’agent. Un serveur Checkmk
qui lance le plugin comme contrôle actif lit directement le format `nagios` par
défaut. Le [guide Checkmk](checkmk.md) décrit les deux méthodes et leurs métriques.

## `otlp` {#otlp}

Ce format reprend les métriques Prometheus dans un document OTLP/JSON : un
`ExportMetricsServiceRequest` pour tous les hôtes. Un collecteur OpenTelemetry
accepte ce document à `POST /v1/metrics` via OTLP/HTTP.

```shell
check-opencloud-security --host opencloud.example.com --format otlp \
  | curl -sf -X POST http://collector.example.com:4318/v1/metrics \
      -H 'Content-Type: application/json' --data-binary @-
```

Le plugin affiche le document sans contacter le collecteur. La destination, le
proxy et les identifiants d’accès se configurent dans la commande d’envoi. Vous
pouvez la lancer avec `curl` depuis le même timer que le contrôle, sans installer
de bibliothèque d’instrumentation dans le plugin.

Plusieurs hôtes produisent plusieurs points par métrique, distingués par l’attribut
`host`, comme dans une collecte Prometheus. Chaque métrique est une jauge, c’est-à-dire
une valeur mesurée à un instant donné. Les noms, attributs et valeurs sont identiques
à ceux de l’exportateur. Le guide [Prometheus et Grafana](prometheus.md#what-the-exporter-publishes)
contient le tableau commun aux deux formats.

Comme `--format prometheus`, **ce format termine avec le code `0`, même si
l’instance aurait déclenché une alerte**. Une analyse en échec produit
`opencloud_security_scrape_success 0`. Le système de métriques peut ainsi distinguer
une instance inaccessible d’une tâche qui ne s’exécute plus. Si vous avez besoin
d’un code de sortie d’alerte, utilisez `nagios`, `json`, `sarif` ou `junit`.

## Choisir un format {#choosing-a-format}

| Format | Utilisation |
|:-----------|:-------------------------------------------------------------------------|
| `nagios` | Format par défaut : le système de supervision lit le code de sortie et la ligne d’état |
| `prometheus` | Collecte directe ou collecteur textfile ; voir [Prometheus et Grafana](prometheus.md) |
| `otlp` | Envoi des mêmes métriques à un collecteur OpenTelemetry sur `/v1/metrics` |
| `json` | Traitement automatique du résultat |
| `sarif` | Affichage des constats dans un tableau de bord d’analyse de code, comme GitHub ou GitLab |
| `junit` | Affichage des constats sous forme de résultats de tests dans un système CI |
| `checkmk` | Exécution comme contrôle local par un agent [Checkmk](checkmk.md) |

Le guide [Exécuter le contrôle en CI](ci.md) détaille les étapes GitHub Actions et
GitLab CI. Il explique aussi comment conditionner un pipeline à un champ JSON du
résultat.
