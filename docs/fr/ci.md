# Pipelines CI {#running-the-check-from-ci}

Un pipeline d’intégration continue (CI) peut analyser régulièrement une instance ou
la vérifier depuis un autre réseau. Surveillez aussi son exécution : une tâche qui
ne démarre pas ne produit aucun résultat.

Trois points s’appliquent à toutes les plateformes :

- **L’exécuteur doit atteindre l’instance.** Pour une instance derrière votre pare-feu,
  utilisez un exécuteur que vous hébergez sur le réseau concerné.
- **L’analyse reflète le réseau de l’exécuteur.** Les contrôles TLS, HTTPS et des ports
  de débogage mesurent ce qui est accessible depuis ce réseau.
- **Le code de sortie représente le résultat :** `0` OK, `1` WARNING, `2` CRITICAL,
  `3` UNKNOWN. Un code non nul fait échouer le pipeline. Les options `--warning`
  et `--critical` définissent donc ses seuils.

## GitHub Actions {#github-actions}

### Utiliser l’action {#the-action}

```yaml
name: OpenCloud security check

on:
  schedule:
    - cron: "0 6 * * *"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: sowoi/check-opencloud-security@v1.16.0
        with:
          target: opencloud.example.com
          # Raises GitHub's anonymous rate limit for the release feed. The
          # token the job already has is enough; it needs no scopes.
          releases-token: ${{ github.token }}
```

Cette étape installe la version indiquée, analyse l’instance, écrit
`opencloud-security.json` et ajoute le résultat au résumé de la tâche. Elle fait
échouer la tâche pour WARNING, CRITICAL ou UNKNOWN.

**Choisissez un tag précis.** Le paquet contient le calendrier des versions et la
dernière version OpenCloud connue. La version du plugin influence donc le verdict.
`@v1.16.0` installe exactement la version 1.16.0. Une référence de branche ou de
commit SHA installe la dernière version publiée et le signale par un avertissement.

| Entrée | Valeur par défaut | Fonction |
|:--|:--|:--|
| `target` | *obligatoire* | Nom d’hôte ou URL de l’instance |
| `version` | Tag choisi | Version du plugin à installer |
| `format` | `json` | `json`, `sarif`, `junit` ou `nagios` |
| `output-file` | `opencloud-security.json` | Fichier de sortie |
| `fail-on` | `warning` | `warning`, `critical` ou `never` |
| `warning` / `critical` | Valeurs du plugin | Seuils de notation |
| `check-hardening` | `true` | Inclure les mesures de durcissement dans le résultat |
| `ignore-hardening` | *aucune* | Identifiants exemptés, séparés par des virgules |
| `release-track` | `auto` | `auto`, `rolling`, `production` ou `lts` |
| `releases-token` | *aucun* | Jeton pour augmenter la limite de requêtes du flux des versions |
| `summary` | `true` | Ajouter le résultat au résumé de la tâche |
| `extra-args` | *aucun* | Autres arguments, transmis tels quels |

Les sorties sont `exit-code`, `status`, `rating`, `rating-label`, `message` et
`result-file`. Seules les deux premières sont disponibles hors du format `json` ;
les autres sont lues dans le document JSON :

```yaml
      - uses: sowoi/check-opencloud-security@v1.16.0
        id: scan
        with:
          target: opencloud.example.com
          fail-on: never

      - name: Open an issue when the grade drops below A
        if: steps.scan.outputs.rating < 4
        run: gh issue create --title "OpenCloud is rated ${{ steps.scan.outputs.rating-label }}"
        env:
          GH_TOKEN: ${{ github.token }}
```

Avec `fail-on: never`, l’étape réussit toujours. Une étape suivante peut alors agir
selon le résultat, par exemple ouvrir un ticket.

L’exécuteur doit pouvoir atteindre l’instance. Un exécuteur hébergé ne peut pas
traverser votre pare-feu. Utilisez un exécuteur local ou analysez l’instance depuis
le réseau sur lequel elle est publiée.

### Alimenter le tableau des analyses de sécurité {#feeding-the-code-scanning-dashboard}

`format: sarif` produit un document SARIF 2.1.0 accepté par l’onglet Security de
GitHub. Les constats y apparaissent avec leur historique :

```yaml
permissions:
  contents: read
  security-events: write

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: sowoi/check-opencloud-security@v1.16.0
        with:
          target: opencloud.example.com
          format: sarif
          output-file: opencloud-security.sarif
          # Upload the findings even when they are bad enough to fail a build.
          fail-on: never

      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: opencloud-security.sarif
          category: opencloud-security
```

Conservez `fail-on: never` pour permettre l’envoi du fichier, puis appliquez votre
politique aux constats importés. Sinon, l’échec de l’étape peut empêcher leur envoi.

### Installer le plugin directement {#installing-it-yourself-instead}

L’action installe le même paquet et lance la même commande que vous pouvez utiliser
vous-même. Une installation directe convient si vous avez besoin d’une étape que
l’action ne propose pas ou si vous souhaitez éviter cette dépendance.

```yaml
name: OpenCloud security check

on:
  schedule:
    - cron: "0 6 * * *"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - name: Install the check
        run: pipx install check-opencloud-security==1.1.0

      - name: Scan the instance
        env:
          COS_HOST: opencloud.example.com
          COS_CHECK_HARDENING: "true"
          COS_UPDATE_WARNING: "true"
          # Raises GitHub's anonymous rate limit for the release feed. The
          # token GITHUB_TOKEN gives the job is enough; it needs no scopes.
          COS_RELEASES_TOKEN: ${{ github.token }}
        run: check-opencloud-security
```

Fixez la version installée. Le calendrier fourni et la dernière version OpenCloud
connue participent au verdict. Sans version fixe, une nouvelle publication du
plugin peut modifier le résultat du pipeline.

Conservez `workflow_dispatch` pour relancer le contrôle après une correction sans
attendre la prochaine exécution planifiée.

### Publier le résultat sans faire échouer la tâche {#reporting-rather-than-failing}

L’échec d’un workflow planifié ne notifie que la personne qui l’a modifié en dernier.
Vous pouvez laisser la tâche réussir et publier son résultat dans le résumé :

```yaml
      - name: Scan the instance
        id: scan
        continue-on-error: true
        env:
          COS_HOST: opencloud.example.com
          COS_CHECK_HARDENING: "true"
        run: |
          set +e
          check-opencloud-security > result.txt
          state=$?
          set -e
          cat result.txt
          echo "state=$state" >> "$GITHUB_OUTPUT"

      - name: Summarise
        run: |
          {
            echo "### OpenCloud security check"
            echo '```'
            cat result.txt
            echo '```'
          } >> "$GITHUB_STEP_SUMMARY"
```

Vous pouvez aussi utiliser `--webhook-url` pour envoyer directement le résultat ;
voir les [exemples de webhooks](../webhook-recipes.md). Ces deux méthodes nécessitent
que le workflow s’exécute. Si les exécutions planifiées sont désactivées, aucun
résumé ni webhook n’est produit.

### Exploiter le document JSON {#the-json-document-instead}

Pour appliquer une règle, alimenter un tableau de bord ou créer automatiquement
un ticket, utilisez le scanner autonome. Il affiche le résultat complet, dont les
champs sont décrits dans le [README de la bibliothèque](../../opencloud_local_scan/README.md).

```yaml
      - name: Scan and keep the result
        run: |
          check-opencloud-scanner scan --compact opencloud.example.com > scan.json
          jq -e '.EOL == false' scan.json \
            || { echo "::error::The installed release no longer receives security fixes"; exit 1; }

      - uses: actions/upload-artifact@v4
        with:
          name: opencloud-scan
          path: scan.json
```

`jq -e` renvoie un code non nul si l’expression est fausse. Vous pouvez ainsi faire
dépendre la réussite du pipeline d’un champ. Les champs `.EOL`, `.rating`,
`.updates.available` et `.lifecycle.daysRemaining` sont particulièrement utiles.

### Preuves de compatibilité OpenCloud {#opencloud-compatibility-evidence}

Le workflow du dépôt utilisant un **véritable conteneur OpenCloud** conserve comme
référence l’empreinte immuable d’une image rolling examinée. Chaque semaine, il
vérifie que le conteneur démarre, publie le chemin de statut attendu, s’identifie
comme OpenCloud, annonce une version et produit une note dans les limites prévues.
L’image indique sa version exacte pendant le test. La compatibilité avec une
nouvelle version n’est déclarée qu’après examen de ces résultats.

| Preuve | Référence | Conditions de compatibilité | Examen |
|:--|:--|:--|:--|
| Intégration avec le conteneur officiel | `opencloudeu/opencloud-rolling@sha256:0bb9038f4c01ab187a014e97550435f5d45630731aed9341d87a0b40fe72fe3d` | Test complet réussi, version annoncée et comportement observable examinés | Lancer le workflow avec `candidate_image` ; modifier la référence dans une pull request examinée |
| Cycle de vie des versions | Calendrier fourni et actualisation quotidienne conservatrice | Conservation des informations de support existantes et réussite des tests de non-régression | Examiner la pull request d’actualisation du calendrier |
| Avis de sécurité | Base fournie et actualisation quotidienne conservatrice | Ajout de preuves sans supprimer les plages de versions déjà connues comme affectées | Examiner la pull request d’actualisation des avis |

L’automatisation ne modifie jamais les données de test, les notes ni les attentes
de sécurité pour faire réussir une image candidate. Tout changement de réponse,
d’en-tête, de chemin ou de propriété de sécurité exige des preuves liées à la
version et une modification de test qui les cite.

Le workflow `Supply-chain checks` s’exécute sur les pull requests, les envois vers
`main` et chaque semaine. Il exporte les dépendances résolues de `uv.lock`, exécute
`pip-audit` sur les dépendances du cœur, du web et de MCP, puis publie un inventaire
logiciel SBOM CycloneDX comme artefact. Les exécutions planifiées et celles déclenchées
par un envoi reçoivent aussi une attestation GitHub Sigstore. Vérifiez-la avec
`gh attestation verify`. Le workflow de publication répète ces contrôles sur
l’environnement d’exécution exact livré avec chaque paquet et atteste les paquets
ainsi que l’archive web.

## GitLab CI {#gitlab-ci}

```yaml
opencloud-security:
  image: python:3.13-slim
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
  variables:
    COS_HOST: opencloud.example.com
    COS_CHECK_HARDENING: "true"
  before_script:
    - pip install --no-cache-dir check-opencloud-security==1.1.0
  script:
    - check-opencloud-security
  # WARNING (1) is worth seeing without failing the pipeline outright.
  allow_failure:
    exit_codes: [1]
```

`allow_failure.exit_codes` associe directement les états du plugin aux règles
GitLab. La valeur `1` tolère WARNING. Ajouter `3` tolère une analyse inachevée,
mais cet échec mérite généralement une intervention.

Ajoutez la planification dans *Build → Pipeline schedules*. Le bloc `rules` évite
l’exécution de cette tâche dans les pipelines ordinaires de commit.

## Utiliser une image de conteneur {#using-the-container-image-instead-of-installing}

Cet exemple construit l’image du plugin depuis le dépôt. Vous pouvez aussi utiliser
l’image publiée `okxo/opencloud-scanner` avec
`--entrypoint check-opencloud-security`.

```shell
docker build -f docker/Dockerfile \
  -t registry.example.com/check-opencloud-security:1.1.0 .
docker push registry.example.com/check-opencloud-security:1.1.0

docker run --rm \
  -e COS_HOST=opencloud.example.com \
  -e COS_CHECK_HARDENING=true \
  registry.example.com/check-opencloud-security:1.1.0
```

## Ne pas placer les jetons dans la ligne de commande {#do-not-put-the-token-on-the-command-line}

Les journaux CI peuvent être accessibles à plusieurs personnes. Un jeton passé
avec `--release-token` peut y apparaître. Utilisez les variables d’environnement
`COS_RELEASES_TOKEN`, `COS_WEBHOOK_URL` ou une
[référence de secret](../README.md#configuration-file-and-secrets). Le plugin masque
les jetons dans sa propre sortie de débogage, mais pas dans les traces du shell.

---

[Retour à l’index de documentation](../../README.md) | [Retour au README principal](../README.md)
