# TLS et certificats {#tls-and-certificates-what-this-scanner-checks-and-why}

Le scanner examine la connexion TLS, le certificat du serveur et les
enregistrements DNS associés. Ces contrôles décrivent la connexion vue depuis
le réseau du scanner. Ils ne recensent pas toutes les configurations qu’un
autre client pourrait rencontrer.

## 1. Peut-on établir une connexion TLS : `tlsHandshake`, `httpsAvailable` {#1-can-a-tls-connection-be-made-at-all-tlshandshake-httpsavailable}

Le scanner commence par tenter une connexion. Deux échecs sont possibles :

- **`httpsAvailable`** (critique) : HTTPS est inutilisable et le scanner se
  replie sur `http://`. Les identifiants, cookies de session et fichiers
  circulent sans chiffrement. Tout intermédiaire peut les lire ou les
  modifier. C’est le problème le plus grave décrit sur cette page.
- **`tlsHandshake`** : un port TLS répond, mais aucune connexion ne peut être
  établie, même sans vérification du certificat. Tous les autres contrôles TLS
  nécessitent une connexion. L’instance ne sert peut-être pas TLS sur ce port,
  ou propose une configuration que le client ne peut pas négocier.

La redirection de HTTP vers HTTPS relève d’un autre indicateur,
`httpsEnforced`, évalué au niveau du proxy. Voir
[Deux constats qui ne portent pas sur les en-têtes](reverse-proxy.md#two-findings-decided-here-that-are-not-headers).

## 2. Le certificat est-il reconnu : `tlsTrusted` {#2-is-the-certificate-trusted-tlstrusted}

`opencloud init` génère un **certificat autosigné** si aucun autre certificat
n’est configuré. Une chaîne non reconnue est donc le constat TLS le plus
courant sur une nouvelle instance. Ce seul constat ne signifie pas que le
déploiement est défectueux. La section [Instances avec certificat autosigné](#self-signed-instances)
explique comment le scanner traite ce cas automatiquement.

## 3. Le protocole est-il à jour : `tlsProtocol`, `tlsDeprecatedProtocol` {#3-is-the-protocol-current-tlsprotocol-tlsdeprecatedprotocol}

La RFC 8996 a rendu TLS 1.0 et 1.1 obsolètes en 2021. Les navigateurs actuels
les refusent.

- **`tlsProtocol`** échoue si la connexion du scanner utilise une version
  antérieure à TLS 1.2.
- **`tlsDeprecatedProtocol`** répond à une question distincte : après la
  négociation normale, le scanner ouvre une connexion brève en imposant
  chacune des versions obsolètes. Un serveur peut négocier TLS 1.3 avec un
  client récent et accepter encore TLS 1.0 ou 1.1 avec un autre. La version
  **la plus ancienne acceptée** détermine ce qu’un attaquant peut imposer.
  Désactivez les anciennes versions ; donner la priorité à la plus récente
  ne suffit pas.

## 4. Le certificat couvre-t-il ce nom : `tlsHostname` {#4-does-the-certificate-cover-this-name-tlshostname}

Aucun nom alternatif du certificat ne correspond à l’hôte analysé : mauvais
domaine, `localhost` ou absence de noms alternatifs. Le nom commun seul ne
suffit plus depuis des années. Les clients ne peuvent pas distinguer ce cas
d’une interception et refusent donc la connexion.

## 5. La chaîne est-elle complète : `tlsChain` {#5-is-the-chain-complete-tlschain}

Les certificats envoyés par le serveur ne permettent pas de remonter à une
racine du magasin public de confiance. Il manque généralement un certificat
intermédiaire. Un navigateur de bureau peut masquer ce problème en utilisant
un intermédiaire en cache ou en le téléchargeant. Les clients mobiles, outils
en ligne de commande et appels entre machines ne disposent pas toujours de
ce cache et échouent. Servez la chaîne complète : le certificat du serveur,
puis tous les intermédiaires, sans la racine. Les autorités la fournissent
généralement dans un fichier `fullchain`.

## 6. Le certificat expire-t-il bientôt ou a-t-il une durée excessive ? {#6-is-the-certificate-about-to-expire-or-issued-for-too-long}

Deux contrôles distincts portent sur la durée de validité :

- **`tlsCertificate`** : il reste moins de `scanner.tls_min_days` jours de
  validité (14 par défaut). Le certificat finira par expirer si personne
  n’agit. Vérifiez le renouvellement automatique et le rechargement du
  certificat dans le processus qui sert réellement TLS.
- **`tlsCertificateLifetime`** (faible) : la durée totale dépasse le seuil de
  398 jours du scanner. Cela peut indiquer une autorité privée ou une émission
  manuelle. Si la clé est compromise, un certificat valable plusieurs années
  peut rester utilisable longtemps. Une courte durée impose des
  renouvellements plus fréquents.

## 7. La suite cryptographique et le certificat sont-ils sûrs ? {#7-is-the-negotiated-cipher-suite-and-certificate-policy-sound}

- **`tlsCipherSuite`** évalue la suite négociée par ce scan, sans prétendre
  recenser toutes celles proposées à d’autres clients. Il échoue en présence
  d’un mécanisme ancien (`NULL`, `RC4`, `3DES`/`DES-`, `MD5`, `CCM_8`) ou
  d’une suite sans confidentialité persistante.
- **`tlsCertificatePolicy`** échoue si le certificat utilise une clé faible
  (RSA de moins de 2048 bits, EC de moins de 256 bits) ou une signature
  MD5/SHA-1. Ces paramètres sont insuffisants même si le certificat n’a pas
  expiré.

## 8. IPv4 et IPv6 présentent-ils le même service : `tlsAddressParity` {#8-do-ipv4-and-ipv6-present-the-same-service-tlsaddressparity}

Si un nom d’hôte publie les deux familles d’adresses, le scanner compare leurs
points d’accès TLS. Les visiteurs peuvent utiliser l’une ou l’autre. Un
service IPv6 oublié peut présenter un ancien certificat, une configuration
obsolète du proxy ou ne plus répondre, malgré une configuration IPv4 correcte.

Le scanner compare une adresse par famille et uniquement l’identité TLS.
Plusieurs nœuds qui partagent un certificat présentent la même identité,
quel que soit leur contenu. Pour détecter un nœud dont la configuration n’a
pas été mise à jour, utilisez `addressParity` avec `--all-addresses`. Voir
[Toutes les adresses résolues](scanner-checks.md#every-resolved-address).

## 9. L’émission de certificats est-elle restreinte : `tlsCaaRecord` {#9-is-certificate-issuance-restricted-tlscaarecord}

Un enregistrement DNS **CAA** (Certification Authority Authorization) indique
quelles autorités peuvent émettre un certificat pour un domaine. Sans cet
enregistrement, toute autorité publiquement reconnue peut recevoir une
demande, et pas seulement celle que vous utilisez. Ce constat de gravité
faible porte uniquement sur le nom exact analysé, sans remonter les domaines
parents comme le prévoit la RFC 8659. La correction concerne la zone DNS,
jamais un paramètre OpenCloud :

```
example.com. CAA 0 issue "letsencrypt.org"
```

## 9a. L’adresse est-elle authentifiée : `tlsDnssec` {#9a-can-the-address-itself-be-trusted-tlsdnssec}

Tous les contrôles précédents utilisent une adresse fournie par un résolveur.
Sans **DNSSEC**, sa réponse n’est pas signée. Une réponse falsifiée en chemin
peut donc paraître authentique. L’enregistrement CAA arrive par le même canal
et peut lui aussi être falsifié.

Le scanner interroge le résolveur de la machine, défini dans
`/etc/resolv.conf`, jamais un résolveur public. Il demande le nom analysé avec
le bit DNSSEC activé, puis vérifie si le résolveur a validé la réponse, si elle
contient des signatures et si le résolveur comprend DNSSEC.

Ce dernier point explique l’absence possible du constat. Un résolveur qui ne
comprend pas DNSSEC peut donner le même résultat qu’une zone non signée.
Signaler un échec dans ce cas pénaliserait l’instance pour une limite du réseau
du scanner.

| Réponse du résolveur | `tlsDnssec` |
|:--------------------|:------------|
| Il a validé la réponse | réussi |
| Il transmet les signatures sans les valider | réussi : la zone est signée, ce qui relève de l’opérateur |
| Aucun des deux, mais il comprend la question | **échec** : la zone n’est pas signée |
| Il ne comprend pas DNSSEC ou ne répond pas | absent du résultat |

Ce constat est de gravité faible. La correction concerne la zone du domaine :
activez sa signature chez le fournisseur DNS, puis publiez l’enregistrement DS
dans la zone **parente**. Sans délégation signée, la zone reste sans protection.
Voir [ADR 0038](../../adr/0038-a-dnssec-answer-nobody-could-have-given-is-not-a-finding.md).

## 10. La révocation est-elle vérifiable : `tlsOcspStapling` {#10-is-revocation-actually-checkable-tlsocspstapling}

Le certificat indique un serveur OCSP, mais le serveur TLS ne joint pas sa
réponse de révocation à la négociation. Chaque client doit alors interroger
l’autorité lui-même, ce qui lui révèle les visites. Si le serveur OCSP est
lent, les clients ignorent souvent la vérification au lieu de refuser la
connexion. Ce constat est de gravité faible : de nombreuses autorités
actuelles, dont Let’s Encrypt, ne publient plus de serveur OCSP. Ce contrôle
ne s’applique pas à leurs certificats.

## 11. Le certificat figure-t-il dans un journal public : `tlsCertificateTransparency` {#11-was-the-certificate-published-to-a-log-tlscertificatetransparency}

Certificate Transparency est un registre public de certificats émis par les
autorités publiques, auquel on peut uniquement ajouter des entrées. Il permet
au propriétaire d’un domaine de repérer un certificat émis à tort pour son
nom avant qu’il ne soit utilisé.

L’autorité intègre des **horodatages de certificat signés** (SCT) dans le
certificat. Le scanner les compte dans le certificat déjà reçu, avec le même
appel `openssl x509 -text` que celui qui lit la clé et l’algorithme de
signature. Aucun processus ni connexion supplémentaire n’est nécessaire.

Le contrôle cherche précisément les SCT intégrés au certificat. Leur absence
produit un constat `medium`, mais ne prouve pas à elle seule qu’un navigateur
refusera la connexion. Les preuves Certificate Transparency peuvent être
transmises par d’autres mécanismes.

`tlsCertificateTransparency` est évalué uniquement si la chaîne aboutit à une
racine publique. Les certificats privés ou autosignés sont exclus. Si
l’OpenSSL local ne peut pas décoder l’extension, le constat est omis, sans être
considéré comme réussi.

**Correction :** faites réémettre le certificat par une autorité qui intègre
les SCT. Les autorités publiques, dont Let’s Encrypt, le font depuis des
années. Un certificat reconnu sans SCT provient probablement d’une autorité
privée ajoutée au magasin de confiance du client.

## 12. Le serveur accepte-t-il les données 0-RTT rejouables : `tlsEarlyData` {#12-is-a-replayable-0-rtt-flight-invited-tlsearlydata}

TLS 1.3 permet à un client qui reprend une session d’envoyer sa première
requête avec la négociation : ce sont les données anticipées, ou « 0-RTT ».
Cela économise un aller-retour, mais TLS ne protège pas ces données contre le
rejeu. Toute personne qui les enregistre peut les renvoyer, sans que le
serveur puisse distinguer la copie de l’original.

Pour un service de fichiers, une requête de déplacement, de copie ou de
suppression pourrait ainsi être rejouée. Un serveur correctement configuré
limite 0-RTT aux requêtes idempotentes, dont la répétition ne change pas le
résultat. Le protocole ne permet toutefois pas de vérifier cette restriction.
Le constat reste donc de gravité `low`.

Le scanner lit la limite `Max Early Data` annoncée dans les tickets de
session, au cours de la même négociation `openssl s_client` que le contrôle
OCSP stapling. Si le serveur n’indique aucune limite, par exemple en TLS 1.2
ou avec certaines configurations interdisant ces données, l’état est inconnu
et non « accepté ».

**Correction :** désactivez les données anticipées sur le composant qui
termine TLS. `ssl_early_data` vaut `off` par défaut dans nginx. Caddy et
Traefik ne l’activent pas. Ne les conservez que si un problème de latence
mesuré le justifie **et** si l’application rejette les requêtes non
idempotentes rejouées.

## Ce qui n’est pas mesuré {#what-is-deliberately-left-unmeasured}

**Un contrôle non effectué n’est jamais déclaré réussi.** Si la version
locale d’OpenSSL refuse TLS 1.0, elle ne peut pas déterminer si le serveur
l’accepterait. Sans exécutable `openssl`, le scanner ne peut pas vérifier
OCSP stapling. Dans les deux cas, le contrôle est absent du résultat.

**Un certificat non reconnu reste analysé.** `getpeercert()` ne renvoie rien
pour un pair non vérifié. Le scanner récupère donc le certificat au format
DER et le décode séparément. Il peut ainsi lire sa date d’expiration, les noms
couverts et l’émetteur, même si la chaîne n’est pas reconnue.

## Instances avec certificat autosigné {#self-signed-instances}

Le scanner traite automatiquement les certificats autosignés ou non reconnus :

1. Il essaie HTTPS avec vérification du certificat. Si la connexion réussit,
   tous les contrôles précédents s’appliquent normalement.
2. Il essaie HTTPS sans vérification. Le scan continue et signale l’échec de
   `tlsTrusted`. Le résultat complet reste disponible avec ce constat.
3. Il essaie HTTP et signale `httpsAvailable` de gravité critique.

`--insecure` (`COS_INSECURE`) supprime l’exigence de vérification de l’étape 1.
La chaîne non reconnue reste dans le résultat, mais ne réduit plus la note.
Utilisez cette option pour une instance dont vous savez que le certificat
est autosigné. Les problèmes inattendus sur les autres instances restent
ainsi visibles.

## Gravité et effet sur la note {#severity-and-rating-impact}

Chaque contrôle de cette page est une entrée `extraChecks`. Un échec plafonne
la note : critique → `D`, élevée → `C`, moyenne → `A`, faible → `A+`.
La section [Contrôles de durcissement](../README.md#hardening-checks) explique
la différence avec les simples indicateurs de durcissement. Le tableau des
[contrôles du scanner](scanner-checks.md#what-the-scanner-checks) donne la
liste complète des gravités.

## Référence {#reference}

Le guide [Proxys inverses](reverse-proxy.md) décrit les en-têtes à configurer
devant OpenCloud. Cette page concerne uniquement la couche TLS.
