# Actualiser les données de référence {#keeping-the-release-schedule-and-advisories-current}

Le scanner utilise un calendrier des versions pour déterminer leur état de support
et une base d’avis de sécurité pour identifier les vulnérabilités connues. Ces
données sont fournies avec le paquet et peuvent vieillir entre ses mises à jour.
Une actualisation séparée permet de reconnaître les nouvelles versions et les
nouveaux avis.

`check-opencloud-scanner refresh-data` actualise ces données sans mettre le paquet
à jour. Ce guide décrit les sources, les contrôles, la planification quotidienne
et les réglages nécessaires pour utiliser les fichiers obtenus.

<!-- TOC -->
* [Actualiser les données de référence](#keeping-the-release-schedule-and-advisories-current)
  * [Quand les actualiser](#when-you-need-it)
  * [Lancer une actualisation](#running-a-refresh)
  * [Sources et contrôles des données](#where-the-data-comes-from-and-how-it-is-checked)
    * [Vérification de la signature](#signature-verification)
    * [Contrôles systématiques](#the-checks-that-apply-either-way)
  * [Utiliser les fichiers actualisés](#using-the-refreshed-files)
  * [Exécution quotidienne avec systemd](#running-it-daily-with-systemd)
  * [Miroirs et hôtes sans accès à Internet](#mirrors-and-hosts-without-internet-access)
  * [Vos propres avis de sécurité](#your-own-advisories)
  * [Points à retenir](#points-worth-knowing)
<!-- TOC -->

## Quand les actualiser {#when-you-need-it}

- **L’analyse détecte une version absente du calendrier.** La ligne du cycle de
  vie indique que la version est plus récente que les données fournies et le
  résultat contient `"scheduleStale": true`. Voir le [cycle de vie des versions](release-lifecycle.md).
- **Un avis a été publié après la construction du paquet.** La base fournie ne le
  connaît pas. L’analyse peut donc ne signaler aucune vulnérabilité connue pour
  une version qui en a une.
- **Vous conservez une version fixe du paquet** et le mettez à jour selon votre
  propre calendrier.

Si vous mettez rapidement le paquet à jour, vous recevez les mêmes données par
cette voie. Le [service public d’analyse](../webapp.md) actualise lui-même ses
données pendant son fonctionnement et n’a pas besoin de cette commande.

## Lancer une actualisation {#running-a-refresh}

```bash
check-opencloud-scanner refresh-data --output-dir /var/lib/check-opencloud-security
```

En cas de réussite, la commande affiche les deux fichiers écrits et termine avec
le code `0` :

```text
/var/lib/check-opencloud-security/release_schedule.json
/var/lib/check-opencloud-security/vulnerabilities.json
```

| Option | Valeur par défaut | Fonction |
|:--|:--|:--|
| `--output-dir` | `~/.cache/check-opencloud-security` | Répertoire des deux fichiers, créé au besoin |
| `--timeout` | `30` | Délai maximal de chaque requête, en secondes |
| `--schedule-url` | *(aucune)* | Lire le calendrier depuis cette page ou ce miroir, **sans vérifier la signature** ; voir [Miroirs](#mirrors-and-hosts-without-internet-access) |
| `--advisory-url` | *(aucune)* | Interroger ce point d’accès OSV ou ce miroir, **sans vérifier la signature** |

Tout échec termine avec le code `1` et sa cause sur stderr : erreur réseau,
document rejeté ou signature incorrecte. Aucun fichier n’est écrit tant que les
deux documents n’ont pas passé les contrôles. Les fichiers précédents restent donc
disponibles en cas d’échec. Vous pouvez planifier la commande avec cron ou un timer.

Ajoutez `-vv` pour voir la vérification de chaque signature :

```bash
check-opencloud-scanner -vv refresh-data --output-dir /var/lib/check-opencloud-security
```

## Sources et contrôles des données {#where-the-data-comes-from-and-how-it-is-checked}

Par défaut, la commande lit `release_schedule.json` et `vulnerabilities.json`
depuis la branche `main` du dépôt de ce projet. Elle ne consulte pas directement
OSV ni la page du cycle de vie d’OpenCloud. Les mainteneurs ont déjà examiné et
fusionné ces fichiers dans les demandes de fusion ouvertes par les tâches
quotidiennes du projet. Voir l’[ADR 0027](../../adr/0027-refreshed-reference-data-is-attested-not-merely-fetched.md).

### Vérification de la signature {#signature-verification}

À chaque modification de ces fichiers sur `main`, le workflow
`attest-security-data.yml` du dépôt produit une attestation
[Sigstore](https://www.sigstore.dev/). La commande la récupère et vérifie qu’elle
provient de ce workflow, sur `main`, dans ce dépôt. Une signature issue d’une autre
exécution GitHub Actions ne suffit pas.

La vérification nécessite l’option d’installation `signing`. Elle reste facultative
car elle ajoute environ une douzaine de paquets :

```bash
pipx install 'check-opencloud-security[signing]'
```

Pour l’ajouter à une installation pipx existante, relancez la commande avec
`--force`. Le guide [Installation du plugin](installation.md) donne les commandes
équivalentes pour uv et pip.

Trois résultats sont possibles :

| Résultat | Conséquence |
|:--|:--|
| La signature est valide | Le document est utilisé |
| La signature n’a pas pu être vérifiée | Un avertissement est émis, puis seuls les contrôles structurels ci-dessous s’appliquent. Causes possibles : option `signing` absente, GitHub ou racine de confiance Sigstore inaccessible, attestation pas encore publiée |
| Une signature est présente et **incorrecte** | La commande s’arrête avec le code `1` sans rien écrire |

Sans l’option `signing`, chaque exécution affiche cet avertissement pour chaque
fichier et peut tout de même réussir :

```text
WARNING check_opencloud.refresh_data: Refreshing the release schedule without verifying its signature: the 'signing' extra (sigstore) is not installed. Install the 'signing' extra (pip install check-opencloud-security[signing]) to verify it.
```

Cet avertissement signifie que l’origine des données n’est pas vérifiée.
Installez l’option `signing` sur les hôtes qui doivent vérifier cette origine.

### Contrôles systématiques {#the-checks-that-apply-either-way}

Une signature valide prouve l’origine du document, pas la cohérence de son contenu.
Les contrôles suivants s’appliquent donc avec ou sans signature :

- **Le calendrier doit conserver toutes les lignes de version.** Chaque ligne
  connue du calendrier fourni avec le paquet doit encore être présente. Une page
  tronquée ou remaniée ne peut ainsi faire passer une ancienne version pour une
  version encore prise en charge.
- **La base d’avis doit contenir des entrées exploitables.** Elle doit contenir
  au moins un avis, et chaque avis doit définir au moins une borne de version.
  Sans borne, un avis concernerait toutes les versions d’OpenCloud.
- **Chaque fichier est remplacé de façon atomique.** Aucun lecteur ne voit un
  fichier partiellement écrit.

## Utiliser les fichiers actualisés {#using-the-refreshed-files}

La commande écrit uniquement des fichiers, sans modifier le paquet installé.
Indiquez au contrôle où les lire :

```yaml
scanner:
  release_schedule: /var/lib/check-opencloud-security/release_schedule.json
  vulnerability_db:
    - /var/lib/check-opencloud-security/vulnerabilities.json
```

Ou utilisez les variables d’environnement :

```bash
COS_SCANNER_RELEASE_SCHEDULE=/var/lib/check-opencloud-security/release_schedule.json
COS_SCANNER_VULNERABILITY_DB=/var/lib/check-opencloud-security/vulnerabilities.json
```

Les deux réglages ont des effets différents :

- `release_schedule` **remplace** le calendrier fourni.
- `vulnerability_db` **complète** la base fournie. Les entrées sont dédupliquées
  par identifiant ; vous pouvez donc ajouter le fichier actualisé sans doublons.

Le plugin et `check-opencloud-scanner scan` lisent les mêmes réglages. Vérifiez
leur effet dans la sortie JSON :

```bash
check-opencloud-scanner -c /etc/check-opencloud-security/config.yml \
    scan opencloud.example.com | jq '.advisorySources, .lifecycle.scheduleUpdated'
```

`scheduleUpdated` doit contenir la date du calendrier actualisé et
`advisorySources` doit mentionner le fichier actualisé.

**Vérifiez les deux après tout changement de chemin ou d’utilisateur :**

- **Un calendrier absent ou illisible désactive le contrôle de fin de vie.**
  Le calendrier fourni n’est pas utilisé en remplacement. La sortie indique
  `Release lifecycle: unknown (no release schedule available)`,
  `scheduleUpdated` vaut `null` et aucun message n’apparaît sans `-vv`. Une
  version en fin de vie est alors notée uniquement sur sa configuration. Lors
  des tests, une instance 2.3.0 normalement CRITICAL a obtenu `OK` et `A+`.
- **Un fichier d’avis absent ou illisible est ignoré avec un avertissement** sur
  stderr : `Advisory file ... does not exist` ou
  `Ignoring advisory file ...: Permission denied`. Un fichier illisible apparaît
  quand même dans `advisorySources` : consultez aussi les avertissements.

## Exécution quotidienne avec systemd {#running-it-daily-with-systemd}

[`contrib/systemd/`](../../contrib/systemd/) fournit un service ponctuel durci,
[`check-opencloud-security-refresh.service`](../../contrib/systemd/check-opencloud-security-refresh.service),
et son timer,
[`check-opencloud-security-refresh.timer`](../../contrib/systemd/check-opencloud-security-refresh.timer).
Le service ne peut écrire que dans `/var/lib/check-opencloud-security`, via
`StateDirectory=`. Le timer l’exécute chaque jour avec un décalage aléatoire d’au
plus une heure et rattrape les exécutions manquées pendant un arrêt.

```bash
sudo cp contrib/systemd/check-opencloud-security-refresh.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now check-opencloud-security-refresh.timer
sudo systemctl start check-opencloud-security-refresh.service   # a first run now
journalctl -u check-opencloud-security-refresh.service
```

**Utilisez le même utilisateur que pour le contrôle.** Les fichiers ne sont
lisibles que par leur propriétaire (mode `0600`). L’unité fournie utilise
`User=check-opencloud-security`. Un contrôle exécuté sous `nagios` ou `icinga` ne
peut donc pas lire ces fichiers, ce qui désactive le contrôle de fin de vie sans
alerte explicite. Voir [Utiliser les fichiers actualisés](#using-the-refreshed-files).
Exécutez le contrôle sous le même compte, ou modifiez l’utilisateur du service :

```bash
sudo systemctl edit check-opencloud-security-refresh.service
# [Service]
# User=nagios
```

`ExecStart=` attend `/usr/bin/check-opencloud-scanner`, le chemin installé par les
paquets `.deb` et `.rpm`. Adaptez-le pour pipx ou pip. Sans systemd, utilisez une
tâche cron quotidienne ; voir [Planification](scheduling.md).

## Miroirs et hôtes sans accès à Internet {#mirrors-and-hosts-without-internet-access}

Une actualisation par défaut nécessite un accès HTTPS à `raw.githubusercontent.com`
et, pour vérifier la signature, à l’API d’attestation GitHub et à la racine de
confiance Sigstore. Deux méthodes conviennent aux hôtes sans ces accès.

**Actualisez les données ailleurs, puis copiez les fichiers.** Lancez la commande
avec `signing` sur une machine connectée, vérifiez sa réussite, puis copiez les
deux fichiers aux mêmes chemins sur l’hôte isolé. Ils sont autonomes et vous avez
déjà vérifié leur origine.

**Utilisez un miroir.** `--schedule-url` accepte une copie de la page du cycle de
vie d’OpenCloud. `--advisory-url` accepte un point d’accès compatible OSV, dont la
réponse complète la base fournie :

```bash
check-opencloud-scanner refresh-data \
    --output-dir /var/lib/check-opencloud-security \
    --schedule-url https://mirror.example.com/opencloud/lifecycle/ \
    --advisory-url https://mirror.example.com/osv/v1/query
```

Ces deux options désactivent la vérification de signature et le signalent à chaque
exécution. Les contrôles structurels restent actifs. Utilisez-les pour un miroir
interne que vous maîtrisez, pas pour contourner une signature incorrecte.

## Vos propres avis de sécurité {#your-own-advisories}

`scanner.vulnerability_db` accepte une liste : vous pouvez ajouter votre fichier
à côté du fichier actualisé. Trois formats sont reconnus sans conversion :
`{"advisories": [...]}`, le format de l’API GitHub Advisory et les documents OSV.
Le [README principal](../README.md#advisory-database) décrit ces formats et les
règles qui associent un avis à une version. `scanner.vulnerability_feed` interroge
un flux à chaque analyse au lieu de lire un fichier.

## Points à retenir {#points-worth-knowing}

- **Une actualisation modifie uniquement les données.** Les nouveaux contrôles,
  constats et règles de notation nécessitent une mise à jour du paquet.
- **Une liste `vulnerabilities` vide ne garantit pas l’absence de vulnérabilité.**
  Aucun avis des bases configurées ne correspond à cette version. Les contrôles de
  configuration déterminent aussi une grande partie de la note.
- **Actualisez les fichiers effectivement lus par le contrôle.** Le répertoire
  par défaut dépend du compte qui lance la commande. Une actualisation sous root
  ne change donc rien pour un contrôle sous `nagios`.
- **L’application web n’utilise pas cette commande.** Elle actualise son calendrier
  et ses avis pendant son fonctionnement, sans retirer les données déjà connues.
  Voir le [service public d’analyse](../webapp.md).
