# Intégration Checkmk

Checkmk peut lire directement la sortie du plugin Nagios. Exécutez-le comme contrôle
actif sur le serveur Checkmk ou comme contrôle local sur un hôte équipé de l’agent.
Choisissez la machine qui peut atteindre l’instance depuis le réseau à tester.

| | [Contrôle actif](#1-an-active-check-on-the-checkmk-server) | [Contrôle local](#2-a-local-check-on-an-agent-host) |
|:--|:--|:--|
| Exécution | Serveur Checkmk | Hôte équipé de l’agent Checkmk |
| Réseau d’origine | Réseau de supervision | Réseau de cet hôte |
| Installation du plugin | Serveur Checkmk | Hôte de l’agent |
| Configuration | Interface web | Script exécuté par l’agent |
| Format de sortie | `nagios` (par défaut) | `--format checkmk` |

Privilégiez le **contrôle actif** si le serveur Checkmk peut atteindre l’instance.
Sa configuration est centralisée et ne nécessite aucune installation sur un autre
hôte. Checkmk lit directement la sortie habituelle du plugin.

Remplacez `opencloud.example.com` par votre adresse. Analysez uniquement les
instances dont vous êtes responsable.

## 1. Contrôle actif sur le serveur Checkmk {#1-an-active-check-on-the-checkmk-server}

Installez le plugin sur le serveur Checkmk avec le compte du site :

```shell
pipx install check-opencloud-security
```

Le guide d’[installation](installation.md) décrit aussi uv, pip et l’installation
depuis le dépôt. `check-opencloud-security --version` affiche la version installée.

Dans l’interface web, ouvrez **Setup > Services > Other services > Integrate
Nagios plugins**, puis créez une règle :

- **Service description** : `OpenCloud security opencloud.example.com`
- **Command line** : `check-opencloud-security --host opencloud.example.com --check-hardening`

Affectez-la à l’hôte auquel le service doit être rattaché. Ce rattachement ne définit
pas la cible : l’analyse vise toujours l’adresse fournie à `--host`.

Checkmk lit l’état dans le code de sortie, le résumé sur la première ligne, les
détails sur les lignes suivantes et les métriques après `|`. Les
[données de performance](../README.md#performance-data) utilisent déjà le format
Nagios, seuils compris : `rating`, `vulnerabilities`, `hardenings_missing`,
`extra_checks_failed`, `update_available`, `support_days_left`, `cert_days_left`,
`upgrade_path_complete` et `time`.

L’intervalle par défaut est d’une minute. Une analyse effectue environ vingt
requêtes HTTP et cinq connexions TCP. Un contrôle horaire suffit généralement
pour une note qui évolue avec la configuration. Réglez cet intervalle dans
**Setup > Services > Service monitoring rules > Normal check interval for service checks**.

## 2. Contrôle local sur un hôte équipé de l’agent {#2-a-local-check-on-an-agent-host}

Si le serveur Checkmk ne peut pas atteindre l’instance, lancez l’analyse depuis un
hôte qui le peut. L’agent exécute un script local et transforme sa sortie en service.

`--format checkmk` produit le format attendu par l’agent :

```shell
check-opencloud-security --host opencloud.example.com --format checkmk
```

```text
0 "OpenCloud_Security_opencloud.example.com" rating=5|vulnerabilities=0|hardenings_missing=0|extra_checks_failed=0|update_available=0|support_days_left=284|cert_days_left=67|execution_time=4.120 OK: Server is up to date. No known vulnerabilities.
```

La ligne contient quatre champs séparés par une espace : état, nom du service entre
guillemets, métriques et description. Plusieurs valeurs `--host` produisent plusieurs
lignes, donc un service par instance.

### Installation {#installing-it}

Le script [`contrib/checkmk/opencloud_security`](../../contrib/checkmk/opencloud_security)
exécute cette commande. Il utilise les mêmes variables `COS_` que les
[exemples cron et systemd](scheduling.md), sans nécessiter de modification du script :

```shell
sudo install -m 0755 contrib/checkmk/opencloud_security \
    /usr/lib/check_mk_agent/local/3600/opencloud_security
```

**Le répertoire `3600` définit l’intervalle.** Un script placé directement dans
`local/` s’exécute à chaque appel de l’agent, soit généralement chaque minute.
Le sous-répertoire numérique indique la durée du cache en secondes : ici, l’analyse
s’exécute au plus une fois par heure. Les appels intermédiaires reçoivent le résultat
mis en cache. Adaptez cette durée à vos besoins ; `3600` convient à la plupart des cas.

Les paquets `.deb` et `.rpm` fournissent ce script comme exemple dans
`/usr/share/doc/check-opencloud-security/checkmk-local-check.sh`. Ils ne l’installent
pas automatiquement dans le répertoire de l’agent.

Définissez la cible dans le script ou dans un fichier d’environnement lu par l’agent :

```shell
COS_HOST=opencloud.example.com
# OpenCloud self-signs its certificate unless a proxy terminates TLS for it.
#COS_SCANNER_VERIFY_TLS=false
```

Lancez ensuite la découverte du service : **Setup > Hosts**, page *Services* de
l’hôte, puis *Full service scan*.

### Signification des états {#what-the-states-mean}

L’état reprend celui du plugin : `0`, `1`, `2` ou `3`. Les mêmes
[seuils de notation](../README.md#rating-thresholds), exemptions et règles de fin de
support s’appliquent. Checkmk ne recalcule pas le verdict :

- `0` OK : note supérieure à `--warning`, sans nouveau constat.
- `1` WARN : note inférieure ou égale à `--warning`, ou mesure de durcissement manquante.
- `2` CRIT : note inférieure ou égale à `--critical`, ou vulnérabilité connue applicable.
- `3` UNKNOWN : analyse impossible à terminer.

Le script fourni affiche toujours une ligne, même si le plugin manque ou si l’agent
l’interrompt après expiration du délai. Sans sortie, Checkmk retirerait le service
de l’hôte au lieu de le signaler comme UNKNOWN.

### Métriques {#the-metrics}

Les mesures portent les mêmes noms que dans la sortie Nagios, avec deux adaptations :

- **Sans seuils.** Checkmk n’évalue les seuils d’un contrôle local que si l’état vaut
  `P`. Le plugin détermine lui-même l’état ; les métriques contiennent donc uniquement les valeurs.
- **Sans suffixe d’unité.** Chaque valeur doit être numérique.
  `time=4.120s` devient ainsi `execution_time=4.120`.

| Métrique | Signification |
|:--|:--|
| `rating` | Note de `0` à `5` (`5` = A+). Absente si aucune note n’a pu être établie |
| `vulnerabilities` | Avis de sécurité connus applicables à la version détectée |
| `hardenings_missing` | Mesures manquantes. **Absente sans `--check-hardening`**, pour distinguer un contrôle non effectué d’un résultat sans défaut |
| `extra_checks_failed` | Contrôles supplémentaires en échec : TLS, chemins exposés, cookies, en-têtes |
| `update_available` | `1` si une version plus récente existe. Absente si la recherche de mises à jour est désactivée |
| `support_days_left` | Jours avant la fin des correctifs pour cette branche ; valeur négative ensuite |
| `cert_days_left` | Jours avant expiration du certificat ; valeur négative ensuite |
| `upgrade_path_complete` | `1` si la mise à jour recommandée corrige tous les avis connus, sinon `0` ; absente sans avis |
| `execution_time` | Durée de l’analyse en secondes |

Une mesure non effectuée est omise. Elle n’apparaît donc pas comme un zéro dans les graphiques.

## Alertes {#alerting-on-it}

Les deux méthodes produisent un service Checkmk ordinaire. Notifications, périodes
de maintenance et acquittements fonctionnent comme pour les autres services.
Deux réglages sont utiles :

- Déclencher immédiatement une alerte **CRIT** pour une vulnérabilité connue ou une version en fin de support.
- Tracer `support_days_left` et lui attribuer un seuil. Cette valeur diminue même sans
  changement sur l’instance. Lorsqu’elle devient négative, la note passe à F.

`--baseline` et `--warn-on-new` ([signaler seulement les changements](baseline.md))
fonctionnent avec les deux méthodes. Ils évitent de répéter les constats déjà
acceptés lors d’un contrôle automatisé. Ils ne masquent jamais une fin de support
ni une nouvelle baisse de la note.

## Voir aussi {#see-also}

- [Installation](installation.md) : inclut les définitions Icinga2/Nagios.
- [Formats de sortie](output-formats.md) : comparaison des valeurs de `--format`.
- [Planification](scheduling.md) : minuterie systemd, cron et variables d’environnement.
- [Prometheus et Grafana](prometheus.md) : collecte et graphiques en dehors de Checkmk.
