"""The French translation of :mod:`webapp.locales.en`."""

from __future__ import annotations

MESSAGES: dict[str, str] = {
    # ---------------------------------------------------------------- site
    # --------------------------------------------- l'espace d'exploitation
    "admin.title": "Espace d'exploitation",
    "admin.description": "État du service, données de référence et journal d'audit.",
    "admin.kicker": "Exploitation",
    "admin.tabs.aria": "Espace d'exploitation",
    "admin.tabs.overview": "Vue d'ensemble",
    "admin.tabs.configuration": "Configuration",
    "admin.tabs.rules": "Règles",
    "admin.config.title": "Configuration",
    "admin.config.lede": "Toutes les variables COS_WEB_* lues par ce service et leurs valeurs actuellement effectives.",
    "admin.config.scope": "Voici les paramètres effectifs de ce processus web au démarrage. OpenCloud et le worker d’analyse ont leur propre configuration. Pour les secrets, seule leur présence est indiquée.",
    "admin.config.source.environment": "Définie",
    "admin.config.source.default": "Par défaut",
    "admin.config.secret.set": "Définie (valeur masquée)",
    "admin.config.unset": "Non définie",
    "admin.config.default": "Valeur par défaut documentée :",
    "admin.config.unknown.kicker": "Vérifiez l'orthographe",
    "admin.config.unknown.heading": "Variables que ce service ne lit pas",
    "admin.config.unknown.lede": "Ces noms portent le préfixe COS_WEB_ mais ne correspondent à aucun réglage : ils ne changent donc rien. Une faute de frappe laisse ici la valeur par défaut en vigueur. Les valeurs ne sont pas affichées.",
    "admin.config.group.storage": "Stockage et workers",
    "admin.config.group.scanning": "Déroulement d'une analyse",
    "admin.config.group.targets": "Ce qui peut être analysé",
    "admin.config.group.limits": "Limites de débit et protection contre les abus",
    "admin.config.group.approval": "Approbation des cibles",
    "admin.config.group.network": "Adresse publique, proxy et indexation",
    "admin.config.group.reference": "Données de versions et d'avis",
    "admin.config.group.interfaces": "Documentation de l'API et point d'accès pour agents",
    "admin.config.group.mcp_auth": "Connexion au point d'accès pour agents",
    "admin.config.group.admin": "Espace opérateur",
    "admin.config.group.audit": "Journal d'audit",
    "admin.config.group.protection": "Effacement, signatures et chiffrement",
    "admin.config.group.frontend": "Frontend",
    "admin.rules.title": "Règles en vigueur",
    "admin.rules.lede": "Comment une note est établie et quelles règles ce déploiement applique aux requêtes, avec les valeurs actuellement utilisées.",
    "admin.rules.scope": "Lu dans la configuration avec laquelle ce processus a démarré et dans les constantes du code qui les applique : une règle listée ici est une règle que le service applique maintenant. Rien sur cette page ne nomme une cible ni un visiteur.",
    "admin.rules.on": "Appliquée",
    "admin.rules.off": "Désactivée",
    "admin.rules.variables": "Définie par",
    "admin.rules.rating.kicker": "Notes",
    "admin.rules.rating.heading": "Comment une instance est notée",
    "admin.rules.rating.lede": "La note est celle du scanner ; ce service ne fait que l'afficher. Voici les règles qu'il applique à chaque analyse ici.",
    "admin.rules.rating.scale": "L'échelle",
    "admin.rules.rating.caps": "Ce qu'une vérification échouée peut faire à la note",
    "admin.rules.rating.version.title": "La version fixe la note de départ",
    "admin.rules.rating.version.body": "Le statut de support de la branche et chaque avis publié concernant la version décident du point de départ d'une note. Les vérifications échouées ne peuvent que la plafonner.",
    "admin.rules.rating.overrides.title": "Fin de support et canal de versions",
    "admin.rules.rating.shared.title": "Un plafond par gravité",
    "admin.rules.rating.extra.title": "Les vérifications supplémentaires comptent dans la note",
    "admin.rules.rating.extra.body": "La sécurité du transport, les en-têtes et les autres vérifications supplémentaires plafonnent la note comme les vérifications de durcissement, au lieu d'apparaître seulement dans le rapport.",
    "admin.rules.rating.waivers.title": "Exemptions qu'un visiteur peut choisir",
    "admin.rules.rating.waivers.body": "{count} vérifications de durcissement peuvent être exemptées dans le formulaire. Une vérification exemptée ne plafonne plus la note et reste marquée dans le rapport ; la fin de support ne peut pas être exemptée.",
    "admin.rules.rating.track.title": "Canal de versions",
    "admin.rules.rating.track.body": "Sans choix dans le formulaire, le canal est {track}. Le canal change la notation d'une version, jamais l'intensité avec laquelle l'instance est sondée.",
    "admin.rules.rating.reference.title": "Données de référence pour la notation",
    "admin.rules.rating.reference.body": "{advisories} avis dans la base ; calendrier des versions daté du {schedule}.",
    "admin.rules.rating.more": "La <a href=\"/grades\">page des notes</a> explique chaque note aux visiteurs dans les mêmes termes.",
    "admin.rules.group.submissions": "Limites de soumission",
    "admin.rules.group.submissions.lede": "À quelle fréquence un client peut demander, et comment le service se comporte sous charge.",
    "admin.rules.group.probe": "Blocage anti-sondage",
    "admin.rules.group.probe.lede": "Limites appliquées aux demandes répétées vers des cibles qui ne peuvent pas être analysées.",
    "admin.rules.group.targets": "Ce qui peut être analysé",
    "admin.rules.group.targets.lede": "Vérifié avant toute connexion, puis à chaque redirection.",
    "admin.rules.group.scanner": "Avec quelle intensité un hôte est sondé",
    "admin.rules.group.scanner.lede": "Les paramètres utilisés pour chaque analyse de ce déploiement. Aucune requête ne peut les modifier.",
    "admin.rules.group.operator": "Identifiants et actions de l'opérateur",
    "admin.rules.group.operator.lede": "Limites des rares appels qui demandent un identifiant ou appuient sur un bouton.",
    "admin.rules.rule.client_limit.title": "Limite par client",
    "admin.rules.rule.client_limit.body": "Au plus {limit} soumissions par client toutes les {window}. Une adresse IPv4 est un client ; un client IPv6 est son /{ipv6}.",
    "admin.rules.rule.daily_cap.title": "Plafond journalier",
    "admin.rules.rule.daily_cap.body": "Au plus {limit} soumissions par client toutes les {window}, en plus de la limite par client.",
    "admin.rules.rule.target_cooldown.title": "Délai par cible",
    "admin.rules.rule.target_cooldown.body": "La même instance peut être analysée une fois toutes les {cooldown}, quel que soit le demandeur.",
    "admin.rules.rule.batch.title": "Taille d'un lot",
    "admin.rules.rule.batch.body": "Un lot contient au plus {limit} cibles, et chacune compte pour toutes les limites.",
    "admin.rules.rule.queue.title": "La surcharge fait la queue",
    "admin.rules.rule.queue.body": "{workers} analyses tournent en même temps ; les autres soumissions attendent dans l'ordre et ne sont jamais refusées pour cause de charge.",
    "admin.rules.rule.agent_wait.title": "Limite des nouvelles tentatives automatiques",
    "admin.rules.rule.agent_wait.body": "MCP et les workflows attendent eux-mêmes un Retry-After d'au plus {wait}, dans la limite de {attempts} tentatives. Au-delà, la réponse est renvoyée à l'appelant.",
    "admin.rules.rule.probe_block.title": "Blocage après des avertissements répétés",
    "admin.rules.rule.probe_block.body": "{limit} avertissements en {window} bloquent le réseau du client pendant {block}.",
    "admin.rules.rule.probe_escalation.title": "Les blocages répétés s'allongent",
    "admin.rules.rule.probe_escalation.body": "Un réseau bloqué de nouveau dans les {repeat} suivant son dernier blocage attend {factor} fois plus longtemps à chaque fois : {steps}.",
    "admin.rules.rule.probe_network.title": "Le blocage couvre un réseau",
    "admin.rules.rule.probe_network.body": "Un blocage s'applique au /{ipv4} IPv4 et au /{ipv6} IPv6 du client, pour que l'adresse suivante ne puisse pas le contourner.",
    "admin.rules.rule.strike_scans.title": "Une analyse qui ne trouve pas OpenCloud est un avertissement",
    "admin.rules.rule.strike_scans.body": "status.php n'a pas répondu, n'a pas renvoyé de JSON, a nommé un autre produit, ou le délai a expiré. Le même hôte de nouveau est un autre avertissement ; une analyse terminée jamais.",
    "admin.rules.rule.strike_refusals.title": "Une cible refusée est un avertissement",
    "admin.rules.rule.strike_refusals.body": "Une soumission refusée pour ce qu'elle vise compte ; une faute de frappe ou un nom qui ne se résout pas ne compte pas :",
    "admin.rules.refusal.blocked": "une adresse que ce déploiement exclut",
    "admin.rules.refusal.internal": "un nom local ou interne",
    "admin.rules.refusal.not_approved": "une instance que le mode d'approbation n'a pas approuvée",
    "admin.rules.refusal.private": "une adresse privée, de bouclage ou lien-local",
    "admin.rules.refusal.unstable": "un nom dont les résolutions divergent",
    "admin.rules.refusal.wildcard_dns": "un nom DNS joker ou de rebinding",
    "admin.rules.rule.private_addresses.title": "Adresses publiques uniquement",
    "admin.rules.rule.private_addresses.body": "Chaque adresse vers laquelle un nom se résout doit être publique ; une réponse privée refuse la cible. Au-delà des plages privées, celles-ci sont aussi refusées :",
    "admin.rules.rule.internal_names.title": "Noms locaux et points de métadonnées",
    "admin.rules.rule.internal_names.body": "Refusés par nom autant que par adresse :",
    "admin.rules.rule.wildcard_dns.title": "Noms DNS joker et de rebinding",
    "admin.rules.rule.wildcard_dns.body": "Les noms sous ces services pointent là où leur écriture l'indique. L'adresse derrière peut toujours être analysée en la saisissant :",
    "admin.rules.rule.dns_consistency.title": "Un nom doit se résoudre deux fois de la même façon",
    "admin.rules.rule.dns_consistency.body": "Un nom soumis est résolu deux fois et refusé si les réponses ne partagent aucune adresse ; chaque adresse des deux est vérifiée.",
    "admin.rules.rule.redirects.title": "Chaque redirection est vérifiée",
    "admin.rules.rule.redirects.body": "Une redirection est résolue et vérifiée comme la cible soumise avant d'être suivie. L'analyse ne contacte que des adresses validées.",
    "admin.rules.rule.exclusions.title": "Exclusions",
    "admin.rules.rule.exclusions.body": "{count} entrées exclues, provenant de l'environnement et de l'onglet de synthèse.",
    "admin.rules.rule.allowed_hosts.title": "Hôtes exemptés de la protection",
    "admin.rules.rule.allowed_hosts.body": "Ces noms échappent aux règles d'adresse publique. Les exclusions s'appliquent toujours :",
    "admin.rules.rule.approval.title": "Mode d'approbation",
    "admin.rules.rule.approval.body": "Seules les instances approuvées sont analysées ; le reste est refusé avec 403. {count} entrées listées ; enregistrement DNS d'approbation : {record}.",
    "admin.rules.rule.stop_when_not_opencloud.title": "Une requête pour un hôte qui n'est pas OpenCloud",
    "admin.rules.rule.stop_when_not_opencloud.body": "Une réponse de status.php qui n'est pas OpenCloud met fin à l'analyse, sans nouvel essai en HTTPS non vérifié ni en HTTP simple.",
    "admin.rules.rule.single_address.title": "Une adresse par analyse",
    "admin.rules.rule.single_address.body": "Un nom à plusieurs adresses est analysé sur l'une d'elles, jamais sur chaque nœud d'un pool.",
    "admin.rules.rule.no_port_scan.title": "Pas de ports supplémentaires",
    "admin.rules.rule.no_port_scan.body": "Seul le port soumis est contacté ; les ports de débogage ne sont pas sondés.",
    "admin.rules.rule.load.title": "Charge par analyse",
    "admin.rules.rule.load.body": "Au plus {concurrency} requêtes simultanées, chacune avec {timeout} ; une analyse complète est arrêtée après {job}.",
    "admin.rules.rule.purge_attempts.title": "Tentatives avec l'identifiant d'effacement",
    "admin.rules.rule.purge_attempts.body": "{limit} identifiants erronés par client en {window}, puis refus jusqu'à la fin de la fenêtre. Les bons ne sont jamais comptés.",
    "admin.rules.rule.admin_refresh.title": "Boutons d'actualisation",
    "admin.rules.rule.admin_refresh.body": "Chaque actualisation des données de référence peut être lancée une fois toutes les {cooldown}.",
    "admin.docs.kicker": "Documentation d'exploitation",
    "admin.docs.source": "Depuis <code>{file}</code> dans le dépôt, en anglais.",
    "admin.band": "Espace d'exploitation - connecté en tant que {user}",
    "admin.band.signout": "Se déconnecter",
    "admin.lede": "Consultez l’état du service et les données de référence, ou lancez manuellement les actualisations quotidiennes du worker.",
    "admin.noscript": (
        "Les valeurs ci-dessus sont remplies par JavaScript. Sans lui, recharge "
        "la page pour voir les valeurs actuelles ; les deux boutons "
        "fonctionnent toujours."
    ),
    "admin.state.kicker": "Maintenant",
    "admin.state.heading": "État du service",
    "admin.state.lede": "Compteurs actuels et limites configurées. Les détails des analyses individuelles et les adresses des clients ne sont pas accessibles ici.",
    "admin.state.worker": "Worker",
    "admin.state.worker.up": "En marche",
    "admin.state.worker.down": "Ne répond pas",
    "admin.state.worker.unknown": "Impossible à déterminer",
    "admin.state.store.down": (
        "Le stockage ne répond pas - impossible de lire le battement"
    ),
    "admin.state.queue": "{depth} en file, {workers} workers",
    "admin.state.ratelimit": "Limite de requêtes",
    "admin.state.ratelimit.value": "{limit} par {window}s",
    "admin.state.cooldown.value": "{seconds}s par cible",
    "admin.state.guard": "Protection contre les abus",
    "admin.state.guard.value": "{active} réseaux bloqués",
    "admin.state.guard.week": "7 derniers jours : {blocks} blocages, {strikes} avertissements, {daily} plafonds journaliers atteints",
    "admin.state.guard.off": "Blocage anti-sondage désactivé",
    "admin.state.schedule": "Calendrier des versions",
    "admin.state.advisories": "Avis de sécurité",
    "admin.state.checked": "vérifié {when}",
    "admin.state.checked.failed": (
        "vérifié {when} - la dernière tentative n'a pas pu être récupérée"
    ),
    "admin.state.checked.rejected": (
        "vérifié {when} - la dernière tentative a été refusée par les garde-fous"
    ),
    "admin.state.refresh.off": "la mise à jour quotidienne est désactivée",
    "admin.state.ago.minutes": "il y a {minutes} min",
    "admin.state.ago.hours": "il y a {hours} h",
    "admin.state.ago.days": "il y a {days} j",
    "admin.state.never": "jamais",
    "admin.state.unknown": "inconnu",
    "admin.state.age.seconds": "Lu il y a {seconds}s",
    "admin.state.age.minutes": "Lu il y a {minutes}m",
    "admin.state.age.waiting": "En attente de la première lecture",
    "admin.state.stale": "Le service n’a pas répondu récemment. Les valeurs affichées proviennent de la dernière lecture et peuvent être périmées.",
    "admin.state.refresh": "Relire",
    "admin.state.copy": "Copier le diagnostic",
    "admin.state.copy.done": "Copié",
    "admin.state.copy.failed": "Copie impossible",
    "admin.surfaces.kicker": "Exposition",
    "admin.surfaces.heading": "Ce que propose ce déploiement",
    "admin.surfaces.lede": (
        "Les réglages avec lesquels ce processus a démarré, ceux-là mêmes que "
        "rapporte le document de diagnostic. Aucun ne change sans "
        "redémarrage, aucun n'est donc interrogé."
    ),
    "admin.surfaces.on": "Activé",
    "admin.surfaces.off": "Désactivé",
    "admin.surfaces.mcp": "Point d'accès pour agents sur /mcp",
    "admin.surfaces.mcp.guarded": (
        "Un jeton de l'émetteur configuré est exigé."
    ),
    "admin.surfaces.mcp.open": (
        "Aucun jeton n'est exigé : tout agent capable de l'atteindre peut "
        "mobiliser les workers de ce service."
    ),
    "admin.surfaces.docs": "Pages d'API navigables sur /docs",
    "admin.surfaces.docs.contract": (
        "Les désactiver masque les pages, pas le contrat : /openapi.json, "
        "/arazzo.json et /.well-known/ai.json restent publics."
    ),
    "admin.surfaces.indexed": "Trouvable par les moteurs de recherche",
    "admin.surfaces.private": "Analyses d'adresses réseau privées",
    "admin.surfaces.private.found": (
        "Autorisé sur un déploiement qui demande à être indexé : qui trouve "
        "ce service peut le pointer sur le réseau où il se trouve."
    ),
    "admin.surfaces.private.estate": (
        "Autorisé, ce qui est précisément l'objet d'un déploiement qui "
        "analyse son propre parc."
    ),
    "admin.surfaces.encrypt": "Résultats chiffrés au repos",
    "admin.surfaces.audit": "Journal d'audit",
    "admin.surfaces.audit.file": (
        "Écrit dans un fichier qui survit au conteneur."
    ),
    "admin.surfaces.audit.memory": (
        "Un anneau de {count} enregistrements en mémoire de ce processus, et "
        "rien sur disque."
    ),
    "admin.surfaces.targets": "Cibles enregistrées en clair",
    "admin.update.kicker": "Version",
    "admin.update.heading": "Mises à jour",
    "admin.update.running": "Version en cours : {version}.",
    "admin.update.available": "La version {version} est disponible.",
    "admin.update.current": "C'est la version la plus récente.",
    "admin.update.unknown": "Impossible de savoir si une version plus récente existe.",
    "admin.update.off": "La vérification des mises à jour est désactivée (COS_WEB_UPDATE_CHECK).",
    "admin.update.install": "Installer {version} maintenant",
    "admin.update.downtime": "Le bundle est vérifié par son attestation de build GitHub, puis le service web et les workers redémarrent avec celui-ci - une courte interruption, pendant laquelle toute analyse en cours est interrompue. La mise à jour reste en place jusqu'au redémarrage des conteneurs.",
    "admin.update.manual": "L'installation depuis cette page est désactivée (COS_WEB_ADMIN_UPDATE_DIR). Récupérez la nouvelle image et recréez les conteneurs.",
    "admin.update.outcome.requested": "Vérifiée et installée. Le service redémarre dans un instant - rechargez la page.",
    "admin.update.outcome.current": "Rien de plus récent à installer.",
    "admin.update.outcome.disabled": "Les mises à jour automatiques ne sont pas configurées dans ce déploiement.",
    "admin.update.outcome.failed": "La version n'a pas pu être téléchargée ou vérifiée. Rien n'a changé ; le journal indique pourquoi.",
    "admin.exclusions.kicker": "Exclusions",
    "admin.exclusions.heading": "Adresses que ce service n'analysera pas",
    "admin.exclusions.lede": (
        "Une entrée prend effet dès la requête suivante, dans chaque "
        "processus et sans redémarrage - et une analyse déjà en file "
        "d'attente est refusée plutôt qu'exécutée. Rien ici ne fait analyser "
        "quoi que ce soit : cette liste ne fait que refuser."
    ),
    "admin.exclusions.add.label": "Nom d'hôte, domaine .suffixe, adresse ou plage CIDR",
    "admin.exclusions.add.placeholder": "opencloud.example.com",
    "admin.exclusions.add.action": "Exclure",
    "admin.exclusions.add.hint": (
        "Un domaine écrit avec un point initial exclut aussi tout ce qui se "
        "trouve en dessous. Une plage est comparée à chaque adresse vers "
        "laquelle un nom d'hôte se résout."
    ),
    "admin.exclusions.remove": "Retirer",
    "admin.exclusions.empty": "Rien n'est exclu dans ce déploiement.",
    "admin.exclusions.source.configured": "Depuis l'environnement",
    "admin.exclusions.updated": "Dernière modification ici le {when}.",
    "admin.exclusions.durability": (
        "Les entrées ajoutées ici vivent dans Redis, que ce déploiement peut "
        "vider. Celles qui doivent lui survivre vont dans "
        "COS_WEB_BLOCKED_TARGETS, où cette page ne peut pas les retirer."
    ),
    "admin.exclusions.unreadable": (
        "Le stockage n'a pas répondu : les exclusions ne peuvent être ni "
        "lues ni modifiées pour l'instant. Elles restent en vigueur - une "
        "analyse qui ne peut pas les vérifier est refusée, pas exécutée."
    ),
    "admin.blocklist.error.shape": (
        "Ce n'est pas une entrée. Indiquez un nom d'hôte, un domaine "
        "commençant par un point, une adresse ou une plage CIDR."
    ),
    "admin.blocklist.error.configured": (
        "Cette entrée vient de COS_WEB_BLOCKED_TARGETS. Retirez-la là-bas "
        "puis redémarrez, pour que le déploiement et cette liste ne se "
        "contredisent pas."
    ),
    "admin.blocklist.error.full": (
        "Cette liste est pleine. Déplacez les entrées permanentes vers "
        "COS_WEB_BLOCKED_TARGETS."
    ),
    "admin.blocklist.error.long": (
        "Cette entrée est plus longue qu'un nom d'hôte ne peut l'être : ce "
        "qu'elle viserait n'atteindrait de toute façon jamais ce service."
    ),
    "admin.outcome.excluded": "Exclue. Refusée dès la requête suivante.",
    "admin.outcome.withdrawn": "Retirée. Elle peut de nouveau être analysée.",
    "admin.actions.kicker": "Données de référence",
    "admin.actions.heading": "Actualiser les données de référence",
    "admin.actions.lede": (
        "Les deux mêmes mises à jour que le worker exécute chaque jour, avec "
        "les mêmes règles : un calendrier auquel il manque une ligne de versions est "
        "refusé, une base d'avis ne peut qu'ajouter des entrées, et une récupération qui "
        "échoue ne change rien."
    ),
    "admin.actions.schedule": "Synchroniser le calendrier",
    "admin.actions.schedule.hint": "Relit la page de cycle de vie publiée.",
    "admin.actions.advisories": "Chercher des avis",
    "admin.actions.advisories.hint": "Interroge le flux d'avis sur les nouvelles entrées.",
    "admin.outcome.updated": "Mis à jour. Le nouveau document est utilisé.",
    "admin.outcome.unchanged": "Déjà à jour - rien n'a changé.",
    "admin.outcome.rejected": (
        "Refusé : les données récupérées n'ont pas passé les contrôles ; les "
        "données précédentes restent donc en service."
    ),
    "admin.outcome.failed": "Récupération impossible. Rien n'a changé.",
    "admin.outcome.disabled": "Cette mise à jour est désactivée dans la configuration de cette installation.",
    "admin.outcome.cooldown": "Vient de s'exécuter. Réessaie dans {seconds}s.",
    "admin.probe.action": "Tester les sources",
    "admin.probe.hint": (
        "Lit les deux sources et rapporte ce qu'une mise à jour en ferait. "
        "Rien n'est enregistré."
    ),
    "admin.probe.schedule": "Calendrier des versions : {answer}",
    "admin.probe.advisories": "Avis : {answer}",
    "admin.probe.usable": "lu, et une mise à jour l'accepterait",
    "admin.probe.rejected": "lu, mais les contrôles le refuseraient",
    "admin.probe.unreadable": "illisible - injoignable, ou plus dans la forme attendue",
    "admin.probe.disabled": "non vérifié - cette mise à jour est désactivée",
    "admin.search.kicker": "Index de recherche",
    "admin.search.heading": "L'index livré est-il encore à jour",
    "admin.search.lede": (
        "L'index est construit au moment de la publication et livré en lecture "
        "seule : cette vue rend compte plutôt que de reconstruire. Elle compare "
        "les pages, les langues et la version pour laquelle il a été généré - "
        "pas le corps du texte, que seul le générateur sait extraire."
    ),
    "admin.search.fresh": "À jour",
    "admin.search.stale": "Périmé",
    "admin.search.unknown": "Impossible à déterminer",
    "admin.search.detail.ok": "Chaque page et chaque langue est indexée pour cette version.",
    "admin.search.detail.release": "Généré pour {built}, version en service {running}.",
    "admin.search.detail.missing": "Non indexé : {list}.",
    "admin.search.detail.extra": (
        "Indexé mais plus servi : {list}."
    ),
    "admin.search.detail.unstamped": (
        "L'index n'indique pas pour quelle version il a été généré ; seules "
        "ses pages et ses langues ont pu être comparées."
    ),
    "admin.search.detail.changed": "{count} titres ou résumés ont changé depuis sa génération.",
    "admin.search.detail.unreadable": "L'index n'a pas pu être lu.",
    "admin.search.remedy": (
        "Une version publiée livre toujours un index généré pour elle ; ce "
        "build n'est donc pas une version telle que publiée - le plus souvent "
        "une image ou un bundle construit depuis un checkout entre deux "
        "versions. Déployez une version publiée, ou régénérez l'index dans ce "
        "checkout et reconstruisez ce que vous déployez :"
    ),
    "admin.search.remedy.commit": (
        "Rien à valider à la main : chaque pull request vers main régénère "
        "l'index et le valide dans sa branche."
    ),
    "admin.search.fix": (
        "Chaque pull request vers main et le workflow de publication "
        "régénèrent l'index et le valident. Il n'y a rien à presser ici."
    ),
    "admin.audit.kicker": "Audit",
    "admin.audit.heading": "Journal d’audit",
    "admin.audit.lede": "Demandes, refus et limites atteintes en temps réel. La connexion s’ouvre lorsque vous activez le suivi du journal.",
    "admin.audit.privacy": (
        "Une adresse de client est un HMAC tronqué sous un sel que ce processus "
        "détient, et rien ne permet d'en revenir à une adresse. Cette vue ne "
        "peut pas montrer plus que ce que le journal a décidé de noter."
    ),
    "admin.audit.replicas": (
        "Cette installation ne tient pas de fichier d'audit : ces "
        "enregistrements viennent de la mémoire du seul processus qui a "
        "répondu - avec plusieurs répliques, c'est une partie du journal et non "
        "sa totalité."
    ),
    "admin.audit.follow": "Suivre en direct",
    "admin.audit.stop": "Arrêter",
    "admin.audit.clear": "Vider",
    "admin.audit.empty": "Rien pour l'instant.",
    "admin.audit.closed": (
        "La connexion a atteint sa limite de {minutes} minutes et le service "
        "l'a fermée. Rien n'a été perdu jusque-là ; « Suivre en direct » en ouvre une "
        "autre."
    ),
    "admin.audit.disabled": (
        "Cette installation ne tient pas de journal d'audit, il n'y a donc rien "
        "à suivre. COS_WEB_AUDIT_LOG l'active."
    ),
    "admin.audit.state.off": "Pas de suivi en direct",
    "admin.audit.state.live": "En direct",
    "admin.audit.state.reconnecting": "Reconnexion",
    "admin.audit.state.unsupported": "Non pris en charge par ce navigateur",
    "admin.audit.state.closed": "Fermée par le service",
    "admin.audit.state.disabled": "Non tenu",
    "site.og_image_alt": (
        "OpenCloud Security Scan - vérifiez la sécurité d'une instance en "
        "détectant les vulnérabilités connues, le durcissement manquant et les "
        "en-têtes de sécurité faibles"
    ),
    # ------------------------------------------------------- header chrome
    "chrome.skip_to_content": "Passer au contenu",
    "chrome.brand": "Analyse de sécurité pour OpenCloud",
    "chrome.menu": "Menu",
    "chrome.nav.primary": "Principal",
    "chrome.nav.secondary": "Secondaire",
    "chrome.search.label": "Rechercher dans la documentation",
    "chrome.search.placeholder": "Rechercher",
    "chrome.theme.toggle": "Changer le thème de couleur",
    "chrome.back_to_top": "Retour en haut",
    "nav.new_scan": "Nouvelle analyse",
    "nav.how_it_works": "Fonctionnement",
    "nav.grades": "Notes",
    "nav.catalogue": "Catalogue",
    "nav.docs": "Docs",
    "nav.search": "Rechercher",
    "nav.compare": "Comparer",
    "nav.api": "API",
    "nav.privacy": "Confidentialité",
    "nav.about": "À propos",
    # --------------------------------------------------- language switcher
    "lang.region": "Langue",
    "lang.label": "Langue de la page",
    "lang.apply": "Changer de langue",
    "lang.note": (
        "L'analyse elle-même reste inchangée ; seule cette page est traduite."
    ),
    # ------------------------------------------------------------- footer
    "footer.note.title": "À propos de ce service",
    "footer.note.body": "Ce serveur analyse l’adresse que vous indiquez. Les résultats restent disponibles pendant {minutes} minutes avant d’expirer. Le service utilise <code>check-opencloud-security</code>, sans compte, sans traceurs ni outils d’analyse d’audience.",
    "footer.note.run_yourself": "Exécutez-le vous-même",
    "footer.version.title": "La version du scanner qui a produit ces résultats",
    "footer.version.label": "Backend v{version}",
    "footer.legal.scope": "<strong>Cette vérification n’est pas exhaustive et une bonne note n’est pas un certificat.</strong> Elle lit la version annoncée, les avis de sécurité correspondants, TLS, les en-têtes et les paramètres publics, y compris les comptes de démonstration documentés. Une bonne note signifie qu’aucun de ces points n’a échoué, pas que l’instance est sécurisée. Elle ne porte pas sur les fichiers privés, le système d’exploitation, les sauvegardes, les droits des comptes ou le réseau environnant. Utilisez ce rapport en complément de vos autres contrôles ; il ne constitue jamais un audit de sécurité ni un test d’intrusion.",
    "footer.legal.trademark": (
        "Il s'agit d'un projet communautaire indépendant. Il n'est pas affilié "
        "à OpenCloud GmbH et n'est ni recommandé ni pris en charge par cette "
        "société. &ldquo;OpenCloud&rdquo;, le logo OpenCloud et toutes les "
        "marques associées sont la propriété de leurs détenteurs respectifs et "
        "ne sont utilisés ici que pour indiquer quel logiciel cet outil "
        "vérifie."
    ),
    # --------------------------------------------------- the contents list
    "toc.heading": "Sur cette page",
    "toc.aria": "Sur cette page",
    "toc.group.act": "Corriger",
    "toc.group.details": "Détails",
    "toc.group.keep": "Conserver",
    # --------------------------------------------------------- cross-links
    "pagenav.kicker": "À lire aussi",
    "pagenav.aria": "En savoir plus sur ce service",
    "pagenav.how.title": "Comment fonctionne l'analyse",
    "pagenav.how.blurb": (
        "Ce qui est testé, et les quatre étapes entre le bouton et la note."
    ),
    "pagenav.grades.title": "Ce que signifient les notes",
    "pagenav.grades.blurb": (
        "Ce que signifient les notes de A+ à F et comment améliorer une "
        "évaluation."
    ),
    "pagenav.catalogue.title": "Ce que le scanner vérifie",
    "pagenav.catalogue.blurb": (
        "Chaque indicateur de durcissement, chaque en-tête et vérification "
        "TLS, et chaque vulnérabilité connue - indépendamment d'une analyse "
        "particulière."
    ),
    "pagenav.docs.title": "Documentation en ligne de commande",
    "pagenav.docs.blurb": (
        "Installez, configurez et automatisez le scanner depuis un terminal."
    ),
    "pagenav.api.title": "Analyser depuis un script ou un agent",
    "pagenav.api.blurb": (
        "L'API JSON, les limites d'utilisation raisonnable, le schéma OpenAPI "
        "et le point de terminaison MCP."
    ),
    "pagenav.privacy.title": "Ce que ce serveur conserve",
    "pagenav.privacy.blurb": (
        "En mémoire, pendant {minutes} minutes, et ce que le journal omet."
    ),
    "pagenav.about.title": "À propos d'OpenCloud",
    "pagenav.about.blurb": (
        "La plateforme analysée ici, et pourquoi ce projet en est "
        "indépendant."
    ),
    "pagenav.cta.title": "Analyser une instance",
    "pagenav.cta.blurb": (
        "Retour au formulaire. Quelques secondes suffisent, sans inscription."
    ),
    # ---------------------------------------------------------------- 404
    "notfound.title": "Page introuvable",
    "notfound.description": (
        "L'adresse n'existe pas, ou l'analyse qu'elle désignait a déjà expiré."
    ),
    "notfound.kicker": "Introuvable",
    "notfound.lede": "Cette page n’existe pas ou le résultat a expiré. Les résultats restent accessibles pendant {minutes} minutes. Lancez une nouvelle analyse pour obtenir un rapport à jour.",
    "notfound.action": "Lancer une nouvelle analyse",
    # ------------------------------------------------------- landing page
    "index.title": "Analyser une instance OpenCloud",
    "index.description": "Vérifiez les vulnérabilités connues, les protections manquantes, les en-têtes de sécurité et les mises à jour disponibles d’une instance OpenCloud. Gratuit, sans inscription.",
    "index.eyebrow": "Indépendant &middot; ressources servies depuis ce site &middot; résultats temporaires",
    "index.headline": (
        'Quel est le niveau de sécurité de votre <em class="swash">instance '
        "OpenCloud</em> ?"
    ),
    "index.lede": "Saisissez l’adresse d’une instance OpenCloud que vous êtes autorisé à tester. Le scanner examine les paramètres accessibles au public, les en-têtes HTTP et la version du logiciel, puis attribue une note de <strong>A+</strong> à <strong>F</strong>.",
    "index.form.kicker": "Demande d'analyse",
    "index.form.hint": "Quelques secondes &middot; sans inscription",
    "index.error.self_host": "Désolé pour l’attente. Ces limites garantissent à chacun l’accès au service. Vous pouvez aussi exécuter le scanner open source sur votre machine, aussi souvent que nécessaire :",
    "index.field.label": "Adresse de l'instance",
    "index.field.title": "Nom d’hôte, avec un port et un sous-dossier simples si nécessaire. Aucun paramètre d’URL, fragment ni changement de répertoire.",
    "index.field.hint": "Le nom d’hôte suffit ; sans protocole indiqué, <code>https://</code> est utilisé. Un sous-dossier simple comme <code>/opencloud</code> est accepté. Les paramètres d’URL, fragments et changements de répertoire sont refusés. Analysez uniquement des instances publiques que vous êtes autorisé à tester.",
    "index.field.invalid": "Saisissez un nom d’hôte, éventuellement avec un port et un sous-dossier simple, sans paramètres d’URL ni fragment.",
    "index.submit": "Lancer l’analyse",
    "index.submit.busy": "Démarrage de l’analyse…",
    "index.track.label": "Canal de version",
    "index.track.hint": "Sert à vérifier si la version est encore prise en charge et à recommander une mise à jour adaptée.",
    "index.format.label": "Afficher",
    "index.format.dashboard": "Un tableau de bord",
    "index.format.json": "Le JSON brut",
    "index.format.hint": "Les deux proviennent de la même analyse.",
    "index.waivers.summary": "Ignorer certains contrôles (facultatif)",
    "index.waivers.selected": "Ignorer certains contrôles ({count} sélectionné(s))",
    "index.remember.summary": (
        "Réglages de votre dernière analyse dans ce navigateur : {track} · {format} · {waivers}."
    ),
    "index.remember.waivers.none": "aucun contrôle ignoré",
    "index.remember.waivers.one": "1 contrôle ignoré",
    "index.remember.waivers.many": "{count} contrôles ignorés",
    "index.remember.apply": "Les réutiliser",
    "index.remember.forget": "Les oublier",
    "index.waivers.hint": "Un contrôle ignoré reste visible dans le rapport, mais ne réduit pas la note. Les exclusions s’appliquent uniquement aux contrôles qui ont échoué.",
    "index.waivers.search.label": "Filtrer les contrôles",
    "index.waivers.search.placeholder": "Rechercher par nom...",
    "index.waivers.search.empty": "Aucun contrôle ne correspond à votre recherche.",
    "index.assurance.aria": "Comment ce service traite vos données",
    "index.assurance.airgapped.title": "Aucune ressource externe",
    "index.assurance.airgapped.body": "Les polices, scripts et images sont servis ici, sans CDN ni outil d’analyse d’audience.",
    "index.assurance.nostore.title": "Stockage temporaire",
    "index.assurance.nostore.body": (
        "Le résultat vit en mémoire et est supprimé dès qu'il expire."
    ),
    "index.assurance.noaccount.title": "Aucune inscription requise",
    "index.assurance.noaccount.body": "Lancez une analyse sans créer de compte ni fournir d’adresse e-mail.",
    "index.assurance.ephemeral.title": "Résultats éphémères",
    "index.assurance.ephemeral.body": (
        "Le lien cesse de fonctionner {minutes} minutes après l'analyse."
    ),
    # -------------------------------------------- release tracks and waivers
    "track.auto.label": "Détecter automatiquement",
    "track.auto.description": (
        "Déduit le canal à partir de la version que l'instance annonce."
    ),
    "track.rolling.label": "Rolling",
    "track.rolling.description": "Une nouvelle version environ toutes les trois semaines.",
    "track.production.label": "Production",
    "track.production.description": (
        "Prise en charge pendant environ six mois. Le choix habituel."
    ),
    "track.lts.label": "LTS",
    "track.lts.description": "Prise en charge pendant deux ans.",
    "waivers.group.hardening": "Durcissement",
    "waivers.group.headers": "En-têtes",
    "waivers.group.checks": "Contrôles",
    # ------------------------------------------------------------ severity
    "severity.critical": "critique",
    "severity.high": "élevée",
    "severity.medium": "moyenne",
    "severity.low": "faible",
    # ------------------------------------------------------------ category
    "category.transport": "Transport & TLS",
    "category.cookies": "Cookies",
    "category.headers": "En-têtes de sécurité",
    "category.authentication": "Authentification & comptes",
    "category.sharing": "Partage & liens",
    "category.exposure": "Exposition réseau",
    "category.embedding": "Intégration",
    "category.lifecycle": "Version & cycle de vie",
    "category.proxy": "Fournisseur d'identité & proxy",
    # --------------------------------------------------------- grade scale
    "grade.5.headline": "Rien à signaler",
    "grade.5.meaning": (
        "La version est à jour pour son canal, aucun avis de sécurité ne "
        "correspond à cette version, et tous les contrôles que l'analyse a pu "
        "exécuter ont réussi."
    ),
    "grade.5.improve": (
        "Conservez cette version à jour sur votre canal et relancez l’analyse "
        "après toute modification du proxy inverse ou de la connexion."
    ),
    "grade.4.headline": "Une mise à jour est disponible",
    "grade.4.meaning": (
        "Une version corrective plus récente est disponible sur la même ligne. "
        "Aucun avis de sécurité connu ne concerne la version installée."
    ),
    "grade.4.improve": (
        "Installez la mise à jour recommandée dans votre ligne de version."
    ),
    "grade.3.headline": "Une ligne de version de retard",
    "grade.3.meaning": (
        "L’instance utilise une ligne de version plus ancienne que la dernière "
        "de son canal. Cette ligne peut encore être prise en charge."
    ),
    "grade.3.improve": (
        "Passez à la ligne actuelle de votre canal. L'analyse indique "
        "laquelle, et ne vous oriente jamais vers un canal que vous n'avez pas "
        "choisi."
    ),
    "grade.2.headline": "Des avis de sécurité correspondent à cette version",
    "grade.2.meaning": (
        "Des vulnérabilités connues concernent la version installée. Aucun des "
        "avis correspondants n’est classé comme élevé ou critique."
    ),
    "grade.2.improve": (
        "Passez à la version corrigée pour votre ligne de version. La page de "
        "résultat l'indique - un même avis peut être corrigé séparément sur "
        "plusieurs lignes."
    ),
    "grade.1.headline": "Une vulnérabilité grave concerne cette version",
    "grade.1.meaning": "Au moins une vulnérabilité connue de la version installée présente une gravité élevée ou critique.",
    "grade.1.improve": (
        "Installez la version corrigée indiquée dans le rapport et consultez "
        "les recommandations de l’avis de sécurité."
    ),
    "grade.0.headline": "Hors support",
    "grade.0.meaning": "Cette branche ne reçoit plus de correctifs de sécurité. Elle obtient un F, quels que soient les autres constats ou exclusions.",
    "grade.0.improve": (
        "Passez à une ligne de version prise en charge. Les lignes prises en "
        "charge, et pour combien de temps, figurent dans le calendrier de "
        "versions que l'analyse consulte."
    ),
    # ---------------------------------------------------------- grades page
    "grades.title": "Ce que signifient les notes",
    "grades.description": (
        "Ce que signifient les notes A+, A, C, D, E et F pour une instance "
        "OpenCloud, et quelles modifications peuvent les améliorer."
    ),
    "grades.kicker": "L'échelle",
    "grades.lede": "La note tient compte du support de la version installée, des vulnérabilités connues et des contrôles qui ont échoué. Cette page explique la note de départ, les plafonds liés aux constats et les changements qui peuvent l’améliorer.",
    "grades.scale.kicker": "Six niveaux",
    "grades.scale.heading": "L'échelle, du meilleur au pire",
    "grades.scale.intro": (
        "L'échelle <strong>0-5</strong> et ses lettres sont celles que "
        "<code>scan.nextcloud.com</code> a rendues familières, conservées "
        "délibérément pour qu'un seuil, un graphique ou une règle d'alerte "
        "existants gardent leur sens. C'est aussi pourquoi il n'y a pas de "
        "<strong>B</strong> : l'échelle le saute, et en inventer un ici ferait "
        "correspondre deux nombres à la même note."
    ),
    "grades.row.prefix": "Note {label} : ",
    "grades.row.score": "{rating} sur 5",
    "grades.row.improve": "Pour progresser :",
    "grades.caps.kicker": "Le plafond",
    "grades.caps.heading": "Comment les contrôles en échec limitent la note",
    "grades.caps.intro": (
        "La version détermine la note de départ. Les contrôles en échec imposent "
        "un plafond selon leur gravité ; c’est le plus bas de ces plafonds qui "
        "s’applique :"
    ),
    "grades.caps.at_best": "au mieux",
    "grades.caps.shared": "Les constats de même gravité imposent le même plafond. S’il reste trois constats de gravité moyenne, en corriger un seul ne suffit pas à lever ce plafond. Le plan conserve les trois étapes et indique à quel moment la note s’améliorerait.",
    "grades.caps.rules": "Deux règles sont prioritaires. <strong>La fin de support détermine toujours la note</strong> : une version qui n’est plus prise en charge reçoit <strong>F</strong>, même avec des exceptions. <strong>Une version en avance sur son canal déclaré n’est pas considérée comme obsolète</strong> ; le rapport signale cette avance.",
    "grades.improve.kicker": "Le chemin le plus court",
    "grades.improve.heading": "Corriger les problèmes relevés",
    "grades.improve.intro": "Chaque rapport fournit les éléments nécessaires pour préparer les corrections :",
    "grades.improve.plan": "<strong>Un plan de correction par priorité.</strong> Chaque étape précise le changement à effectuer et la note atteignable après cette étape et toutes les précédentes.",
    "grades.improve.release": "<strong>Une version précise à installer.</strong> Le rapport indique la version qui corrige la vulnérabilité <em>dans votre branche</em>, en respectant le canal choisi.",
    "grades.improve.explained": (
        "<strong>Les contrôles en échec sont expliqués.</strong> Vous voyez ce "
        "qui a été mesuré, pourquoi c’est important et comment corriger le "
        "problème, avec un lien vers le paramètre correspondant dans la "
        "documentation OpenCloud."
    ),
    "grades.improve.waiver": "<strong>Des exclusions pour les constats que vous acceptez.</strong> Ils restent visibles, mais ne plafonnent plus la note. Une exclusion ne s’applique qu’à un contrôle échoué et ne peut pas modifier la note d’une version en fin de vie.",
    "grades.improve.rerun": "Relancez l’analyse après vos modifications pour vérifier quels problèmes ont été corrigés.",
    "grades.limits.kicker": "Périmètre",
    "grades.limits.heading": "Ce qu'une bonne note n'est pas",
    "grades.limits.body": "Un <strong>A+</strong> signifie que les vérifications retenues pour la note n’ont révélé aucun problème. Cela ne couvre pas les fichiers privés, le système d’exploitation, les sauvegardes ou les droits des comptes. Contrôlez aussi ces éléments. La page <a href=\"/how-it-works\">Fonctionnement de l’analyse</a> précise ce qui est vérifié et les limites du rapport.",
    # -------------------------------------------------------------- catalogue
    "catalogue.title": "Ce que le scanner vérifie",
    "catalogue.description": (
        "Chaque indicateur de durcissement, en-tête de sécurité, vérification "
        "TLS et vulnérabilité connue que ce scanner peut signaler, "
        "indépendamment d'un résultat d'analyse particulier."
    ),
    "catalogue.kicker": "Référence",
    "catalogue.lede": "Consultez les vérifications possibles et les avis de sécurité utilisés pour évaluer une version. Ce catalogue décrit le périmètre de l’outil sans lancer d’analyse.",
    "catalogue.checks.kicker": "Contrôles",
    "catalogue.checks.heading": "Chaque contrôle, par catégorie",
    "catalogue.checks.lede": (
        "Regroupés par sujet plutôt que par gravité - la gravité dépend de "
        "l'instance analysée, elle n'est donc pas indiquée ici."
    ),
    "catalogue.checks.not_configurable": "non configurable",
    "catalogue.advisories.kicker": "Vulnérabilités",
    "catalogue.advisories.heading": "Vulnérabilités connues",
    "catalogue.advisories.lede": (
        "Chaque vulnérabilité de la base contre laquelle une analyse est "
        "évaluée, actualisée chaque jour depuis le flux public."
    ),
    "catalogue.advisories.empty.tag": "Aucune connue",
    "catalogue.advisories.empty.body": (
        "La base de données de vulnérabilités est actuellement vide."
    ),
    "catalogue.advisories.fixed_in": "Corrigé dans {version}",
    "catalogue.advisories.unfixed": "Aucun correctif publié pour le moment",
    # -------------------------------------------------- how the scan works
    "how.title": "Comment fonctionne l'analyse",
    "how.description": "Ce que le scanner vérifie sur une instance OpenCloud et les étapes entre la demande et le rapport.",
    "how.kicker": "La méthode",
    "how.lede": "Le scanner se connecte directement à l’adresse saisie et évalue lui-même les réponses. Il examine les informations accessibles sans compte et utilise ses données de versions et de vulnérabilités pour évaluer le logiciel installé.",
    "how.tests.heading": "Ce qui est testé",
    "how.tests.version.title": "Version et cycle de vie",
    "how.tests.version.body": "La version installée, sa période de support et les avis de sécurité qui la concernent. Une version sans support reçoit F.",
    "how.tests.transport.title": "Transport et en-têtes",
    "how.tests.transport.body": "L’accès HTTPS, le certificat et sa durée de validité restante, les versions TLS proposées et les en-têtes de sécurité : HSTS, CSP, protection contre l’intégration dans un cadre et l’interprétation incorrecte du type de contenu.",
    "how.tests.hardening.title": "Durcissement et exposition",
    "how.tests.hardening.body": "L’authentification Basic, les mots de passe et dates d’expiration des liens publics, les règles de mot de passe, les listes de répertoires, les interfaces internes accessibles et les informations de version publiées.",
    "how.pipeline.kicker": "Le déroulement",
    "how.pipeline.heading": "De la demande au résultat",
    "how.pipeline.lede": "Chaque analyse suit ces quatre étapes.",
    "how.pipeline.step1": (
        "<strong>Votre adresse est vérifiée.</strong> Les adresses privées, de "
        "bouclage et de métadonnées cloud sont refusées avant toute "
        "connexion."
    ),
    "how.pipeline.step2": "<strong>L’analyse reçoit un identifiant aléatoire.</strong> Cet identifiant donne accès au résultat. Il n’existe pas de liste publique des analyses.",
    "how.pipeline.step3": "<strong>L’analyse rejoint la file d’attente.</strong> Le nombre d’analyses simultanées est limité. Si tous les workers sont occupés, votre analyse attend et la page affiche sa position dans la file.",
    "how.pipeline.step4": "<strong>Le résultat expire.</strong> Après {minutes} minutes, il n’est plus accessible par son identifiant.",
    "how.faq.kicker": "Questions",
    "how.faq.heading": "Questions fréquentes",
    "how.faq.q1": "S'agit-il du logiciel officiel d'OpenCloud ?",
    "how.faq.a1": (
        "Non. Il s'agit d'un projet communautaire indépendant, qui n'est pas "
        "affilié à OpenCloud GmbH et que cette société ne recommande ni ne "
        'prend en charge. "OpenCloud" et son logo sont des marques '
        "appartenant à leurs détenteurs respectifs, utilisées ici uniquement "
        "pour indiquer quel logiciel cet outil contrôle."
    ),
    "how.faq.q2": "Une bonne note signifie-t-elle qu'une instance est sécurisée ?",
    "how.faq.a2": "Non. L’analyse vérifie la version annoncée, les avis de sécurité correspondants et les paramètres visibles de l’extérieur, ainsi que les identifiants de démonstration publiés. Elle n’évalue pas les fichiers privés, le système d’exploitation, les sauvegardes ou les droits des comptes. Le rapport complète votre démarche de sécurité sans remplacer un audit ou un test d’intrusion.",
    "how.faq.q3": "Combien de temps conservez-vous le résultat d'une analyse ?",
    "how.faq.a3": "Le résultat reste disponible pendant {minutes} minutes, puis expire. La page <a href=\"/privacy\">Données conservées par ce serveur</a> donne les détails.",
    "how.faq.q4": "Y a-t-il une limite de débit ?",
    "how.faq.a4": (
        "Oui, par visiteur et par cible analysée, afin qu'un visiteur trop "
        "actif n'accapare pas la file d'attente et que la même instance ne "
        "soit pas analysée coup sur coup. Les chiffres exacts de ce "
        'déploiement figurent sur la <a href="/api#api-limits">page de '
        "l'API</a>."
    ),
    "how.faq.q5": "Puis-je analyser sans limite de débit ?",
    "how.faq.a5": (
        "Oui - le scanner est open source. Exécutez-le vous-même avec "
        '<a href="/cli">une seule commande Docker</a> sur votre propre '
        "machine, sans limite et sans site web intermédiaire."
    ),
    "how.faq.q6": "Un scan m'indique-t-il si une mise à jour d'OpenCloud est en attente ?",
    "how.faq.a6": "Oui. La version annoncée est comparée aux données de publication disponibles, en tenant compte de son support et de son canal. La section <a href=\"/documentation/reference#update-check\">Vérification des mises à jour</a> explique le calcul de la recommandation.",
    # --------------------------------------------------------------- privacy
    "privacy.title": "Ce que ce serveur conserve",
    "privacy.description": (
        "Ce qui est stocké pendant l'exécution d'une analyse, pour combien de "
        "temps, et ce que le journal opérationnel enregistre ou non."
    ),
    "privacy.kicker": "Confidentialité",
    "privacy.lede": "Les résultats restent disponibles pendant {minutes} minutes, puis expirent.",
    "privacy.retention.kicker": "Rétention",
    "privacy.retention.heading": "Données de l’analyse",
    "privacy.retention.body": "L’adresse cible, les exceptions choisies et le résultat sont conservés pendant {minutes} minutes sous l’identifiant aléatoire de l’analyse. Ils expirent ensuite. Le journal courant ne contient que cet identifiant et les événements de création, de démarrage et de fin. Les limites d’utilisation reposent sur une empreinte à sens unique de l’adresse du client. L’opérateur peut aussi configurer un journal d’audit distinct.",
    "privacy.uploads.kicker": "Rapports téléversés",
    "privacy.uploads.heading": "Quand vous téléversez un rapport à comparer",
    "privacy.uploads.body": "Le fichier envoyé est lu en mémoire pour calculer la comparaison. Son contenu et son nom ne sont pas conservés. La comparaison reste accessible sous un identifiant aléatoire pendant {minutes} minutes, pour pouvoir la rouvrir ou la partager. Elle expire ensuite et ne peut pas être recalculée à partir du fichier supprimé.",
    "privacy.self_host": "Le même scanner est disponible en ligne de commande et sous forme de bibliothèque Python. Exécuté localement, il se connecte directement à l’instance depuis votre machine.",
    # ----------------------------------------------------------- legal notice
    "legal.title": "Mentions légales",
    "legal.description": (
        "Identification du fournisseur, coordonnées et clauses de "
        "responsabilité de l'exploitant de cette installation."
    ),
    "legal.kicker": "Mentions légales",
    "legal.lede": (
        "Identification du fournisseur selon le droit allemand, pour "
        "l'exploitant de cette installation."
    ),
    "legal.english_notice": (
        "Ces mentions sont le texte juridique de l'exploitant et ne sont "
        "disponibles qu'en anglais. La page qui les entoure est traduite, le "
        "texte ci-dessous ne l'est pas."
    ),
    # ----------------------------------------------------------------- about
    "about.title": "À propos d'OpenCloud et de ce scanner",
    "about.description": (
        "Ce qu'est OpenCloud, qui le développe, et pourquoi ce scanner est un "
        "projet communautaire indépendant."
    ),
    "about.kicker": "À propos",
    "about.lede": "OpenCloud permet de stocker, synchroniser et partager des fichiers. Ce scanner indépendant vérifie les paramètres de sécurité d’une instance qui sont visibles de l’extérieur.",
    "about.platform.kicker": "La plateforme",
    "about.platform.heading": "À propos d'OpenCloud",
    "about.platform.body": "<a href=\"https://opencloud.eu/\" rel=\"noopener noreferrer\">OpenCloud</a> est une plateforme open source de stockage, de synchronisation et de partage de fichiers. Les guides d’administration sont disponibles sur <a href=\"https://docs.opencloud.eu/\" rel=\"noopener noreferrer\">docs.opencloud.eu</a>.",
    "about.platform.independent": (
        "Ce scanner est un projet communautaire indépendant. Il n'est pas "
        "affilié à OpenCloud GmbH et n'est ni recommandé ni pris en charge "
        "par cette société. &ldquo;OpenCloud&rdquo;, le logo OpenCloud et "
        "toutes les marques associées sont la propriété de leurs détenteurs "
        "respectifs."
    ),
    "about.project.kicker": "Le projet",
    "about.project.heading": "À propos de ce scanner",
    "about.project.body": "Les résultats proviennent de <code>check-opencloud-security</code>, un plugin pour Nagios et Icinga avec sa propre bibliothèque d’analyse. Vous pouvez l’utiliser sur ce site ou l’exécuter sur votre machine sans limite de fréquence ni file d’attente.",
    "about.project.origin": "<strong>Massoud Ahmed</strong> a créé ce projet pour vérifier les canaux de publication, les paramètres et les installations d’OpenCloud avec un outil que les administrateurs peuvent exécuter sur leur propre machine. <a href=\"{project}\" rel=\"noopener noreferrer\">Le code source et les contributions sont sur GitHub</a>.",
    # ------------------------------------------------------------------- API
    "api.title": "Analyser depuis un script ou un agent",
    "api.description": (
        "L'API JSON derrière le formulaire : comment soumettre une analyse, "
        "l'interroger, ce que ce serveur refuse de laisser décider à "
        "l'appelant, et tout ce dont un logiciel a besoin pour le piloter - "
        "OpenAPI, les flux de travail Arazzo et le point de terminaison MCP."
    ),
    "api.kicker": "L'API",
    "api.lede": "L’API JSON permet de lancer des analyses, de suivre leur progression et de télécharger les résultats. Les scripts et agents utilisent le même service et respectent les mêmes limites que le formulaire du navigateur.",
    "api.submit.kicker": "Soumettre et interroger",
    "api.submit.heading": "Soumettre et interroger",
    "api.submit.body": (
        "Une soumission répond <code>202</code> avec l'identifiant de "
        "l'analyse ; l'interroger renvoie <code>queued</code>, "
        "<code>running</code> ou le résultat terminé, et <code>404</code> une "
        "fois qu'il a expiré. Seuls quatre champs sont lus - l'adresse, les "
        "contrôles à déroger, le canal de version et le format de sortie. "
        "Tout le reste dans le corps, la concurrence et les délais "
        "d'expiration en premier lieu, est rejeté : l'intensité avec laquelle "
        "ce serveur sonde n'est pas une décision de l'appelant."
    ),
    "api.limits.kicker": "Utilisation raisonnable",
    "api.limits.heading": "Utilisation raisonnable",
    "api.limits.enforced": "Cette installation autorise {client} demandes par adresse sur {window} minute(s), avec {cooldown}. Tout dépassement renvoie <code>429</code> et un en-tête <code>Retry-After</code>.",
    "api.limits.cooldown": "une analyse par cible toutes les {minutes} minute(s)",
    "api.limits.no_cooldown": "aucun délai de repos par cible",
    "api.limits.daily": "Au plus {count} analyses par réseau par jour.",
    "api.limits.probe": "Un réseau dont les analyses ne trouvent jamais OpenCloud est mis en pause un moment.",
    "api.limits.none": "Ce déploiement n'impose aucune limite de débit.",
    "api.limits.self_host": (
        "Si vous en rencontrez une et préférez ne pas attendre, l'ensemble "
        'tourne aussi sur votre propre machine : <a href="{project}" '
        'rel="noopener noreferrer">le projet est sur GitHub</a>.'
    ),
    "api.schema.kicker": "Le schéma",
    "api.schema.heading": "Le schéma",
    "api.schema.body": (
        "Les documents lisibles par machine sont toujours publics, sur ce "
        'déploiement comme sur tout autre : la <a href="/openapi.json">'
        "description OpenAPI 3.1</a> de chaque opération, et les "
        '<a href="/arazzo.json">flux de travail Arazzo 1.0.1</a> qui '
        "expliquent comment ces opérations s'assemblent pour soumettre une "
        "analyse, l'attendre et en récupérer le résultat."
    ),
    "api.schema.docs_on": (
        'Les deux sont consultables ici sous forme de <a href="/docs">'
        'Swagger UI</a> et de <a href="/redoc">ReDoc</a>, servis depuis ce '
        "serveur comme tout le reste - rien n'est récupéré ailleurs."
    ),
    "api.schema.docs_off": (
        "Les visionneuses interactives (Swagger UI sur <code>/docs</code>, "
        "ReDoc sur <code>/redoc</code>) sont désactivées sur ce déploiement ; "
        "un opérateur les active avec <code>COS_WEB_ENABLE_DOCS=true</code>."
    ),
    # ------------------------------------------------- API, for agents
    "api.agents.kicker": "Agents IA",
    "api.agents.heading": "Partez d'une seule adresse",
    "api.agents.intro": "Les agents peuvent découvrir les opérations de l’API et les étapes d’une analyse dans les documents publics ci-dessous, accessibles sans compte.",
    "api.agents.discovery": (
        '<strong>Découverte</strong> - <a href="/.well-known/ai.json">'
        "/.well-known/ai.json</a> nomme tout ce qui suit, avec des URL "
        "absolues. Commencez ici."
    ),
    "api.agents.openapi": (
        '<strong>OpenAPI</strong> - <a href="/openapi.json">/openapi.json</a>, '
        "chaque opération avec ses véritables codes de statut et formes de "
        "réponse."
    ),
    "api.agents.arazzo": (
        '<strong>Flux de travail Arazzo</strong> - <a href="/arazzo.json">'
        "/arazzo.json</a>, le cycle de vie d'une analyse : soumettre, "
        "interroger, détecter l'achèvement, exporter."
    ),
    "api.agents.mcp": (
        "<strong>MCP</strong> - <code>{url}</code>, un point de terminaison "
        "Model Context Protocol via HTTP en flux continu. Outils : "
        "<code>scan_instance</code>, <code>scan_instances</code>, "
        "<code>get_scan_result</code>, <code>plan_remediation</code>, "
        "<code>export_scan</code> et <code>erase_instance_data</code>. "
        "<code>scan_instance</code> effectue toute la tâche - soumission, "
        "attente et résultat - en un seul appel. Les invites (prompts) "
        "nomment les tâches elles-mêmes, comme <code>audit_instance</code>, "
        "qui audite une instance et rédige le plan de remédiation, et "
        "<code>review_transport_security</code>, qui ne s'intéresse qu'au "
        "certificat et à la négociation. Il répond au protocole plutôt qu'à "
        "un navigateur, c'est donc une adresse à configurer plutôt qu'une "
        "page à ouvrir."
    ),
    "api.agents.summary": "OpenAPI décrit les opérations disponibles ; Arazzo explique comment les enchaîner pour réaliser une analyse. Les deux documents sont générés à partir du code du service.",
    "api.agents.summary_mcp": "OpenAPI définit les opérations, Arazzo décrit les parcours et MCP les propose aux agents sous forme d’outils. Tous reposent sur la même implémentation du service.",
    "api.webmcp.kicker": "Dans le navigateur",
    "api.webmcp.heading": "Utiliser la page comme outil",
    "api.webmcp.intro": (
        "Un navigateur compatible avec le "
        '<a href="https://webmachinelearning.github.io/webmcp/" '
        'rel="noopener noreferrer">projet WebMCP</a> peut découvrir les actions '
        "de la page ouverte. Aucun autre client ne doit être configuré."
    ),
    "api.webmcp.landing": (
        "Sur la page d'accueil, <code>scan_opencloud_security</code> met une "
        "analyse en file d'attente. Son schéma contient les canaux de publication, "
        "les formats de sortie et les dérogations proposés par cette page."
    ),
    "api.webmcp.result": (
        "Sur une page de résultat, <code>get_scan_result</code> lit l'analyse "
        "actuelle et <code>export_scan_report</code> télécharge JSON, CSV, SARIF "
        "ou PDF pour l'uuid déjà affiché."
    ),
    "api.webmcp.boundary": (
        "Chaque outil du navigateur appelle la même API JSON avec "
        "<code>Accept: application/json</code>. La protection SSRF, les limites, "
        "le délai par cible, la file et l'isolation par uuid restent appliqués."
    ),
    "api.webmcp.support": (
        "WebMCP est encore un projet et les navigateurs qui ne l'implémentent pas "
        "l'ignorent. Désactiver MCP pour ce déploiement retire aussi les outils du "
        "navigateur."
    ),
    "api.clients.kicker": "Configuration",
    "api.clients.heading": "Configurer un client agent",
    "api.clients.intro": "Configurez le client avec l’URL du point d’accès et le transport HTTP streamable. Si l’opérateur exige une authentification, vous devrez également vous connecter.",
    "api.clients.body": (
        "Une configuration détaillée pour Claude Code, Claude Desktop, "
        "GitHub Copilot dans VS Code et en CLI, Cursor, Zed et Windsurf - "
        "contre ce déploiement ou l'un des vôtres - se trouve dans "
        '<a href="{project}/blob/main/docs/mcp.md" '
        'rel="noopener noreferrer">le guide MCP</a>.'
    ),
    "api.rules.kicker": "Les règles",
    "api.rules.heading": "Les mêmes règles que pour tout le monde",
    "api.rules.body": (
        "Les règles sont les mêmes pour un agent que pour n'importe qui "
        "d'autre. Une analyse est asynchrone et l'uuid est le seul moyen d'y "
        "revenir ; un <code>429</code> est une invitation à ralentir plutôt "
        "qu'un refus ; et si vous contrôlez plus qu'une poignée d'instances, "
        'merci d\'<a href="{project}" rel="noopener noreferrer">exécuter le '
        "scanner vous-même</a> - c'est le même code, sur votre machine, sans "
        "aucune limite."
    ),
    # -------------------------------- Docker one-liners, on /documentation
    "cli.lede": "Exécutez le scanner sur votre machine pour garder la maîtrise de l’analyse et éviter les limites de ce service. Les commandes ci-dessous utilisent le même scanner que ce site.",
    "cli.oneliner.kicker": "La commande unique",
    "cli.oneliner.heading": "Une commande, rien à installer",
    "cli.oneliner.body": "La commande affiche la note, le statut de support, les avis de sécurité applicables et les contrôles échoués. Son code de sortie Nagios permet de l’utiliser pour la supervision, les scripts, la CI ou les tâches cron. L’analyse s’exécute dans le conteneur et se connecte directement à votre instance.",
    "cli.json.kicker": "En JSON",
    "cli.json.heading": "L'intégralité du document de résultat",
    "cli.json.body": (
        "Chaque chiffre d'une page de résultat provient de ce document, y "
        "compris le bloc <code>addresses</code> derrière la ligne "
        "<strong>Résolu vers</strong> - les adresses IPv4 et IPv6 vers "
        "lesquelles le nom pointait pendant l'analyse."
    ),
    "cli.private.kicker": "Votre propre réseau",
    "cli.private.heading": "Les instances que ce site n'analysera pas",
    "cli.private.body": "Exécutez l’outil en ligne de commande depuis une machine qui peut joindre votre instance interne. Les adresses privées et les noms DNS internes sont acceptés. Les services publics limitent ces cibles pour empêcher l’accès à leurs propres réseaux internes.",
    "cli.nodocker.kicker": "Pas de Docker ?",
    "cli.nodocker.heading": "Sans conteneur",
    "cli.nodocker.body": "L’outil est également disponible sur PyPI. Utilisez <code>uv</code> pour l’exécuter à la demande ou <code>pipx</code> pour l’installer dans un environnement Python isolé.",
    # ------------------------------------------------ CLI documentation index
    "docs.index.title": "Documentation en ligne de commande",
    "docs.index.description": (
        "Installez, exécutez et configurez le CLI check-opencloud-security, "
        "avec les guides complets destinés aux opérateurs rassemblés en un "
        "seul endroit."
    ),
    "docs.index.kicker": "Documentation",
    "docs.index.heading": "Exécutez le scanner depuis votre terminal",
    "docs.index.lede": "Installez le scanner, lancez votre première analyse et configurez son utilisation régulière. Les guides de <code>docs/</code> expliquent la supervision, la CI, le déploiement et les contrôles à l’origine des constats.",
    "docs.index.toc.quickstart": "Démarrage rapide",
    "docs.index.toc.commands": "Commandes",
    "docs.index.toc.options": "Options utiles",
    "docs.index.toc.configuration": "Configuration",
    "docs.index.toc.monitoring": "Supervision",
    "docs.index.toc.guides": "Guides complets",
    "docs.index.quickstart.kicker": "Démarrage rapide",
    "docs.index.quickstart.heading": "Un contrôle, sans rien installer",
    "docs.index.quickstart.container": (
        "Ou utilisez le conteneur publié. Il exécute le même plugin et "
        "renvoie le même code de sortie Nagios/Icinga :"
    ),
    "docs.index.quickstart.note": (
        "Le plugin parle directement à l'instance. Il n'envoie pas l'adresse "
        "à ce site web ni à un service de verdict distant."
    ),
    "docs.index.commands.kicker": "Deux points d'entrée",
    "docs.index.commands.heading": "Le verdict et le document de résultat",
    "docs.index.commands.plugin": (
        "Le plugin de supervision : une ligne d'alerte, des données de "
        "performance et les codes de sortie standards <strong>OK</strong>, "
        "<strong>WARNING</strong>, <strong>CRITICAL</strong> et "
        "<strong>UNKNOWN</strong>."
    ),
    "docs.index.commands.scanner": (
        "La bibliothèque de scan en ligne de commande : le document de "
        "résultat JSON complet pour un script, un pipeline ou une "
        "investigation ponctuelle."
    ),
    "docs.index.options.kicker": "Les options du quotidien",
    "docs.index.options.heading": "Options utiles",
    "docs.index.option.host": (
        "Nom d'hôte, IP ou URL ; séparés par des virgules pour plusieurs "
        "instances."
    ),
    "docs.index.option.check_hardening": (
        "Inclure les mesures de durcissement manquantes et les en-têtes de "
        "sécurité."
    ),
    "docs.index.option.release_track": (
        "<code>rolling</code>, <code>production</code>, <code>lts</code> ou "
        "<code>auto</code>."
    ),
    "docs.index.option.ignore_hardening": (
        "Accepter un constat sans effacer sa preuve ; répétable et "
        "compatible avec les jokers."
    ),
    "docs.index.option.debug": (
        "Expliquer d'où part la note et ce qui l'a plombée."
    ),
    "docs.index.option.insecure": (
        "Ignorer la vérification du certificat pour une instance que vous "
        "contrôlez."
    ),
    "docs.index.option.thresholds": (
        "Choisir les seuils de notation correspondant aux états de "
        "supervision."
    ),
    "docs.index.option.format": "Afficher la sortie Nagios ou le texte Prometheus.",
    "docs.index.option.baseline": (
        "N'alerter que sur les constats nouveaux ou pires que lors de la "
        "dernière exécution."
    ),
    "docs.index.option.webhook": (
        "Notifier un autre système lorsque l'état configuré est atteint."
    ),
    "docs.index.options.manual": (
        "<code>check-opencloud-security --help</code> est le manuel "
        'installé. Le <a href="{project}#cli-usage" '
        'rel="noopener noreferrer">tableau complet des options</a> inclut '
        "chaque valeur par défaut et sa variable d'environnement "
        "<code>COS_</code>."
    ),
    "docs.index.configuration.kicker": "Un seul sens",
    "docs.index.configuration.heading": "Configuration et priorité",
    "docs.index.configuration.intro": (
        "Les paramètres peuvent provenir d'un fichier YAML ou JSON, de "
        "l'environnement ou de la ligne de commande. L'ordre est toujours :"
    ),
    "docs.index.precedence.aria": (
        "Priorité de configuration, du plus prioritaire au moins prioritaire"
    ),
    "docs.index.precedence.cli": "Option en ligne de commande",
    "docs.index.precedence.cli.note": "la réponse explicite pour cette exécution",
    "docs.index.precedence.env": "Environnement",
    "docs.index.precedence.env.note": (
        "<code>COS_*</code>, utile dans les conteneurs et les services"
    ),
    "docs.index.precedence.file": "Fichier de configuration",
    "docs.index.precedence.file.note": (
        "les valeurs par défaut durables de l'opérateur"
    ),
    "docs.index.precedence.default": "Valeur par défaut intégrée",
    "docs.index.precedence.default.note": (
        "la réponse sûre lorsque rien n'a été précisé"
    ),
    "docs.index.configuration.wizard": (
        "Laissez l'assistant rédiger le premier fichier :"
    ),
    "docs.index.configuration.note": (
        "Un fichier se terminant par <code>.json</code> est du JSON ; tout "
        "autre suffixe est du YAML. Les secrets peuvent vivre dans des "
        "fichiers séparés plutôt que sur la ligne de commande."
    ),
    "docs.index.monitoring.kicker": "Mettez-le au travail",
    "docs.index.monitoring.heading": (
        "Supervision, automatisation et plusieurs instances"
    ),
    "docs.index.monitoring.nagios": (
        "<strong>Nagios ou Icinga :</strong> utilisez directement la sortie "
        "du plugin ; le pire seuil configuré détermine le code de sortie."
    ),
    "docs.index.monitoring.fleet": (
        "<strong>Plusieurs instances :</strong> transmettez une liste "
        "d'hôtes séparés par des virgules, ou utilisez un fichier de "
        "configuration par instance dès que leurs paramètres divergent."
    ),
    "docs.index.monitoring.prometheus": (
        "<strong>Prometheus :</strong> utilisez "
        "<code>--format=prometheus</code> ponctuellement, ou exposez "
        "l'exportateur intégré avec <code>--prometheus-listen-port</code>."
    ),
    "docs.index.monitoring.ci": (
        "<strong>CI :</strong> exécutez la même commande dans un pipeline ; "
        "le code de statut fait échouer la tâche en cas de politique non "
        "respectée, sans script intermédiaire."
    ),
    "docs.index.monitoring.scheduled": (
        "<strong>Contrôles planifiés :</strong> systemd, cron, Kubernetes et "
        "le rôle Ansible utilisent tous le même flux de CLI et de "
        "configuration."
    ),
    "docs.index.guides.kicker": "Depuis le dépôt",
    "docs.index.guides.heading": "Guides complets pour les opérateurs",
    "docs.index.guides.lede": (
        "Chaque document source dispose ici de sa propre page HTML, générée "
        "à partir du Markdown du dépôt et vérifiée contre toute dérive en "
        "intégration continue."
    ),
    # --------------------------------------------------- generated guide pages
    "docs.guide.kicker": "Documentation en ligne de commande",
    "docs.guide.english_notice": "Ce guide est disponible en anglais, allemand, français et espagnol. La version anglaise est affichée pour la langue sélectionnée.",
    "docs.guide.toc.heading": "Sur cette page",
    "docs.guide.toc.aria": "Sur cette page",
    # ---------------------------------------------------------------- compare
    "compare.title": "Comparer deux analyses",
    "compare.description": (
        "Comparez deux analyses terminées de la même instance et voyez ce qui "
        "a été corrigé, ce qui est nouveau et ce qui reste ouvert."
    ),
    "compare.eyebrow": "Les correctifs ont-ils fonctionné ?",
    "compare.heading": "Comparer deux analyses",
    "compare.lede": "Indiquez les UUID de l’analyse précédente et de la nouvelle analyse. Les deux résultats doivent encore être disponibles. Si le premier a expiré, vous pouvez utiliser un rapport téléchargé dans le formulaire ci-dessous.",
    "compare.form.baseline": "Analyse antérieure",
    "compare.form.current": "Analyse postérieure",
    "compare.form.placeholder": "L'UUID dans l'adresse d'une page de résultat",
    "compare.form.submit": "Comparer",
    "compare.form.hint": (
        "L'UUID est la partie qui suit <code>/scan/</code> dans l'adresse "
        "d'une page de résultat. Il constitue à lui seul l'autorisation "
        "d'accès à ce résultat : traitez-le comme un mot de passe."
    ),
    "compare.error.unknown.baseline": (
        "L'analyse antérieure est inconnue ou a expiré. Rien ici ne permet de "
        "la retrouver : relancez une analyse de l'instance et comparez les "
        "deux résultats les plus récents."
    ),
    "compare.error.unknown.current": (
        "L'analyse postérieure est inconnue ou a expiré. Rien ici ne permet "
        "de la retrouver : relancez une analyse de l'instance et comparez les "
        "deux résultats les plus récents."
    ),
    "compare.error.unfinished.baseline": (
        "L'analyse antérieure n'est pas encore terminée. Ouvrez sa page de "
        "résultat, attendez-la, puis comparez à nouveau."
    ),
    "compare.error.unfinished.current": (
        "L'analyse postérieure n'est pas encore terminée. Ouvrez sa page de "
        "résultat, attendez-la, puis comparez à nouveau."
    ),
    "compare.error.same": (
        "Les deux champs désignent la même analyse : il n'y a rien à "
        "comparer. Relancez une analyse de l'instance et comparez le nouvel "
        "UUID avec celui-ci."
    ),
    "compare.error.different_targets": "Les deux analyses concernent des instances différentes et ne sont donc pas comparées. Comparez deux analyses de la même instance.",
    "compare.verdict.kicker": "Entre les deux analyses",
    "compare.verdict.improved": "C'est meilleur",
    "compare.verdict.unchanged": "Rien n'a changé",
    "compare.verdict.regressed": "C'est pire",
    "compare.rating.up": "La note a augmenté de {points} point(s).",
    "compare.rating.down": "La note a baissé de {points} point(s).",
    "compare.rating.same": "La note est inchangée. Des problèmes peuvent pourtant avoir été corrigés : plusieurs constats peuvent imposer le même plafond. Les listes ci-dessous détaillent les changements.",
    "compare.side.baseline": "Antérieure",
    "compare.side.current": "Postérieure",
    "compare.side.target": "Instance",
    "compare.side.version": "Version",
    "compare.side.scanned": "Analysée",
    "compare.side.unknown": "Non établi",
    "compare.side.open": "Ouvrir ce résultat",
    "compare.introduced.heading": "Nouveaux constats ({count})",
    "compare.introduced.none": (
        "Rien de nouveau depuis l'analyse antérieure."
    ),
    "compare.resolved.heading": "Constats résolus ({count})",
    "compare.resolved.none": (
        "Rien de ce qui était ouvert dans l'analyse antérieure n'a disparu."
    ),
    "compare.unchanged.heading": "Toujours ouverts ({count})",
    "compare.unchanged.none": "Rien n'est ouvert dans les deux analyses.",
    "compare.changes.heading": "Ce que la comparaison détaille",
    "compare.changes.category": "Catégorie",
    "compare.changes.change": "Changement",
    "compare.nothing_stored": "Cette comparaison est calculée à partir des deux résultats à chaque ouverture. Elle n’est pas enregistrée séparément et cesse d’être disponible si l’un des résultats expire.",
    # ----------------------------------------------------------------- search
    # ------------------------------------------ comparaison avec un fichier
    "compare.upload.kicker": "Vous avez déjà un rapport ?",
    "compare.upload.heading": "Comparer un rapport antérieur à une analyse",
    "compare.upload.lede": "Envoyez un rapport JSON ou CSV téléchargé précédemment pour le comparer à une analyse de ce service. Vous pouvez ainsi utiliser un ancien résultat même si son lien a expiré.",
    "compare.upload.field.report": "Rapport antérieur",
    "compare.upload.field.current": "Analyse postérieure",
    "compare.upload.field.hint": (
        "Le fichier <code>.json</code> ou <code>.csv</code> des téléchargements "
        "d'une page de résultat. Jusqu'à {kilobytes} Ko."
    ),
    "compare.upload.submit": "Comparer avec ce fichier",
    "compare.upload.privacy": (
        "Le fichier est lu une fois, en mémoire, pour calculer la comparaison, et "
        "n'est jamais écrit sur disque ni conservé. La comparaison elle-même est "
        "gardée {minutes} minutes pour que cette page puisse être rechargée, puis "
        "elle disparaît aussi."
    ),
    "compare.upload.source.kicker": "D'où vient le côté antérieur",
    "compare.upload.source.json": "Le rapport précédent provient d’un fichier JSON envoyé. Il n’a pas de page de résultat ici ; le fichier a été supprimé après lecture.",
    "compare.upload.source.csv": "Le rapport précédent provient d’un fichier CSV envoyé. Il n’a pas de page de résultat ici ; le fichier a été supprimé après lecture.",
    "compare.upload.source.dropped": "{count} entrée(s) avec des identifiants de constat inconnus ont été exclues de la comparaison.",
    "compare.upload.source.missing.httpsEnforced": "Le fichier ne précise pas si HTTPS était imposé. Ce point est exclu des deux rapports pour la comparaison, notamment avec les anciens exports CSV.",
    "compare.upload.source.missing.update": "Le fichier ne précise pas si une mise à jour était disponible. Ce point est exclu des deux rapports pour la comparaison, notamment avec les anciens exports CSV.",
    "compare.upload.expires": "La comparaison reste disponible pendant environ {minutes} minutes. Vous aurez ensuite besoin du fichier d’origine pour la refaire.",
    "compare.upload.error.missing": (
        "Aucun fichier n'a été téléversé. Choisissez le rapport JSON ou CSV que "
        "vous avez téléchargé auparavant."
    ),
    "compare.upload.error.no_current": "Indiquez l’UUID de l’analyse à laquelle comparer le rapport.",
    "compare.upload.error.empty": "Ce fichier est vide.",
    "compare.upload.error.too_large": "Le fichier dépasse la taille maximale de {kilobytes} Ko.",
    "compare.upload.error.unreadable": "Impossible de lire ce fichier en JSON ou CSV. Envoyez le rapport téléchargé d’origine, sans modification.",
    "compare.upload.error.not_a_report": "Le fichier ne correspond pas à un rapport de ce service. Utilisez un export JSON ou CSV téléchargé depuis une page de résultat.",
    "compare.upload.error.rate_limit": (
        "Cela fait beaucoup de rapports depuis votre réseau en peu de temps. "
        "Attendez une minute et réessayez."
    ),
    "compare.upload.error.blocked": (
        "Plusieurs adresses analysées récemment depuis votre réseau ne se sont "
        "pas révélées être OpenCloud ; ce service suspend donc temporairement "
        "les requêtes provenant de votre réseau, y compris les envois de "
        "rapports. Le scanner et sa "
        "comparaison s'exécutent aussi sans aucune limite sur votre machine."
    ),
    "compare.upload.error.expired": "Ce lien a expiré. Une comparaison reste disponible pendant {minutes} minutes ; envoyez à nouveau le fichier pour la refaire.",
    "search.title": "Recherche",
    "search.description": (
        "Recherchez dans la documentation du scanner et les recommandations "
        "publiques. Les résultats d'analyse ne sont jamais indexés."
    ),
    "search.eyebrow": "Index statique de la version",
    "search.heading": "Rechercher dans le scanner",
    "search.lede": (
        "Uniquement la documentation et les recommandations publiques. "
        "L'index est reconstruit à chaque version ; il ne lit jamais le "
        "magasin d'analyses, les pages de résultat, les UUID ou les adresses "
        "soumises."
    ),
    "search.label": "Rechercher dans la documentation",
    "search.placeholder": "TLS, Docker, dérogations...",
    "search.submit": "Rechercher",
    "search.scope.operator": "Espace d'exploitation",
    "search.status.idle": (
        "Saisissez un terme pour rechercher dans la documentation de cette "
        "version."
    ),
    "search.status.results": "{count} résultat(s) dans cette version.",
    "search.status.empty": (
        "Aucune documentation publique ne correspond à cette recherche."
    ),
    "search.status.error": "La recherche est temporairement indisponible.",
    # The search manifest: the title and summary an index entry carries, as
    # opposed to the words on the page itself.
    "search.page.index.title": "Analyser une instance OpenCloud",
    "search.page.index.summary": (
        "Lancez une analyse de sécurité publique pour une instance OpenCloud."
    ),
    "search.page.how.title": "Comment fonctionne le scanner",
    "search.page.how.summary": (
        "Ce que le scanner mesure, ce qu'il ne peut pas voir, et comment les "
        "résultats sont traités."
    ),
    "search.page.grades.title": "Ce que signifient les notes",
    "search.page.grades.summary": (
        "L'échelle de notation de A+ à F et les correctifs qui améliorent "
        "chaque note."
    ),
    "search.page.catalogue.title": "Ce que le scanner vérifie",
    "search.page.catalogue.summary": (
        "Chaque indicateur de durcissement, en-tête et vérification TLS du "
        "scanner, et chaque vulnérabilité connue."
    ),
    "search.page.documentation.title": "Documentation en ligne de commande",
    "search.page.documentation.summary": (
        "Démarrage rapide en ligne de commande, configuration, supervision "
        "et guides de déploiement."
    ),
    "search.page.api.title": "API",
    "search.page.api.summary": (
        "Soumettez des analyses, interrogez les résultats, exportez des "
        "rapports et pilotez le service depuis un agent via OpenAPI, Arazzo "
        "ou MCP."
    ),
    "search.page.privacy.title": "Confidentialité",
    "search.page.privacy.summary": (
        "Rétention des résultats, journalisation des requêtes, limites de "
        "débit et politique envers les tiers."
    ),
    "search.page.about.title": "À propos de ce projet",
    "search.page.about.summary": (
        "Pourquoi ce scanner de sécurité OpenCloud indépendant existe."
    ),
    # ------------------------------------------- what a submission is refused for
    # The API answers the English sentence these translate; a browser reads
    # the translation. The SSRF guard names the identifier, this names the
    # sentence, and neither is derived from the other.
    "error.unsupported_fields": (
        "Ce service n'accepte pas {fields}. L'analyse s'exécute uniquement "
        "avec les paramètres définis côté serveur."
    ),
    "error.rate_limit.client": (
        "C'est beaucoup d'analyses depuis votre réseau en peu de temps. "
        "Patientez une minute et réessayez."
    ),
    "error.rate_limit.probe": (
        "Plusieurs adresses analysées récemment depuis votre réseau ne se "
        "sont pas révélées être des instances OpenCloud. Ce service suspend donc "
        "vos analyses pendant un moment. Si vous vouliez vérifier votre propre "
        "instance, le scanner fonctionne aussi sur votre machine."
    ),
    "error.rate_limit.daily": (
        "C'est toutes les analyses que ce service peut faire aujourd'hui pour "
        "votre réseau. Il y aura de la place demain - ou lancez le scanner "
        "vous-même, il n'a pas de limite journalière."
    ),
    "error.target.wildcard_dns": (
        "Ce nom appartient à un service qui fait pointer des noms vers n'importe "
        "quelle adresse. Saisissez le nom d'hôte propre de l'instance ou son adresse."
    ),
    "error.target.unstable": (
        "Ce nom d'hôte répond avec des adresses différentes à chaque requête, "
        "ce service ne peut donc pas déterminer de façon fiable ce qu'il analyserait."
    ),
    "error.target.not_approved": (
        "Ce service n'analyse que les instances approuvées pour lui. Demandez à "
        "l'opérateur de l'ajouter, ou publiez l'enregistrement DNS qui l'approuve."
    ),
    "error.rate_limit.target": (
        "Cette instance a été analysée très récemment. Merci de patienter "
        "quelques minutes."
    ),
    "error.target.invalid": "Cette adresse ne peut pas être analysée.",
    "error.target.empty": "Saisissez l'adresse de l'instance OpenCloud à analyser.",
    "error.target.too_long": "Cette adresse est trop longue.",
    "error.target.characters": (
        "Cette adresse contient des caractères qu'un nom d'hôte ne peut pas "
        "avoir."
    ),
    "error.target.unparsed": "Cette adresse n'a pas pu être analysée syntaxiquement.",
    "error.target.scheme": (
        "Seules les cibles en http:// et https:// peuvent être analysées."
    ),
    "error.target.credentials": (
        "Les identifiants inclus dans l'adresse ne sont pas acceptés."
    ),
    "error.target.address_only": (
        "Saisissez uniquement l'adresse de base de l'instance. Un "
        "sous-dossier simple est accepté, mais pas les requêtes, fragments, "
        "paramètres ni traversées de chemin."
    ),
    "error.target.port": "Cette adresse comporte un port invalide.",
    "error.target.no_host": "Cette adresse ne comporte aucun nom d'hôte.",
    "error.target.hostname_shape": (
        "Ce n'est pas un nom d'hôte que ce service peut analyser."
    ),
    "error.target.unresolved": "Ce nom d'hôte ne se résout pas.",
    "error.target.hostname_long": "Ce nom d'hôte est trop long.",
    "error.target.internal": (
        "Les adresses locales et internes ne peuvent pas être analysées."
    ),
    "error.target.private": (
        "Cette adresse pointe vers un réseau privé, de bouclage ou local, "
        "que ce service n'analysera pas."
    ),
    "error.target.blocked": (
        "Il a été demandé à ce service de ne pas analyser cette adresse."
    ),
    "error.store_unavailable": (
        "Ce service ne peut pas lire sa propre configuration pour le moment et "
        "n'analysera rien tant qu'il ne sait pas quelles cibles exclure. "
        "Veuillez réessayer dans quelques minutes."
    ),
    # ----------------------------------------------------------- result page
    "result.title": "Résultats de l'analyse",
    "result.description": (
        "Le résultat d'une analyse publique, lisible uniquement avec son "
        "propre identifiant."
    ),
    "result.kicker": "Analyse de sécurité",
    "result.heading": "Résultat de l'analyse",
    "result.track.title": (
        "Le canal de version par rapport auquel cette analyse a été notée"
    ),
    "result.track.label": "Canal {track}",
    "result.another": "Analyser une autre instance",
    "result.compare": "Comparer avec une analyse antérieure",
    "result.tab.queued": "En file d'attente : {target}",
    "result.tab.queued.position": "N° {position} dans la file : {target}",
    "result.tab.running": "Analyse en cours : {target}",
    "result.tab.ready": "Rapport prêt : {target}",
    "result.tab.done": "Note {label} : {target}",
    "result.tab.failed": "Échec de l'analyse : {target}",
    "index.cooldown.opening": 'Ouverture du résultat précédent de cette instance…',
    "result.earlier.note": (
        'Voici le résultat précédent de cette instance. Elle a été analysée trop récemment pour l’être à nouveau ; le compte à rebours ci-dessous indique quand une nouvelle analyse sera possible.'
    ),
    "result.compare.offer": (
        "Vous avez déjà analysé cette instance dans cet onglet, à {time}."
    ),
    "result.compare.offer.link": "Voir ce qui a changé depuis",
    "result.progress.kicker": "En cours",
    "result.progress.queued.title": "En attente d’un worker",
    "result.progress.queued.detail": (
        "Tous les workers sont occupés. Votre analyse garde sa place dans la "
        "file et démarre dès que l’un d’eux se libère."
    ),
    "result.progress.running.title": "Analyse de l'instance en cours",
    "result.progress.running.detail": (
        "Lecture de ce que l'instance publie : version, capacités, "
        "certificat, en-têtes et les points de terminaison qu'elle expose "
        "sans connexion."
    ),
    "result.progress.step.queued": "En file d'attente",
    "result.progress.step.running": "En cours",
    "result.progress.step.done": "Résultat",
    "result.progress.estimate": "La plupart des analyses se terminent en moins d'une minute.",
    "result.progress.elapsed": "depuis {duration}",
    "result.progress.noscript": (
        "Cette page se met à jour elle-même grâce à JavaScript. Sans lui, "
        "rechargez la page dans quelques secondes pour voir le résultat."
    ),
    "result.progress.queue.position": (
        "Analyse en file d'attente. Position : #{position} sur {length}."
    ),
    "result.progress.queue.next": "Analyse en file d'attente. Vous êtes le prochain.",
    "result.progress.queue.waiting": (
        "En attente qu’un worker la prenne en charge."
    ),
    "result.progress.done.title": "Rapport prêt",
    "result.progress.done.detail": "La note est disponible. Ouverture du rapport.",
    "result.progress.failed.title": "Analyse terminée",
    "result.progress.failed.detail": (
        "L’analyse n’a pas pu être terminée. Ouverture de la page de résultat."
    ),
    "result.failed.fallback": "L'analyse n'a pas pu être menée à son terme.",
    "result.failed.body": "Le scanner n’a pas pu recueillir assez d’informations pour attribuer une note. Vérifiez l’adresse, confirmez qu’elle héberge OpenCloud et assurez-vous que l’instance est accessible depuis ce service.",
    "result.document.kicker": "Document de résultat",
    "result.document.heading": "Document de résultat",
    "result.document.lede": (
        "Le même document qu'évaluent le contrôle en ligne de commande et le "
        "plugin Nagios."
    ),
    "result.verdict.kicker": "Verdict",
    "result.verdict.heading": "Note globale",
    "result.verdict.dial": "Note {label}, {rating} sur 5",
    "result.facts.instance": "Instance",
    "result.facts.resolved": "Adresses résolues",
    "result.facts.ipv6.heading": "Accessibilité IPv6",
    "result.facts.ipv6.note": (
        "Non vérifiée - ce déploiement n'a pas de connectivité IPv6 sortante, "
        "c’est donc indiqué ici sans être pris en compte dans la note."
    ),
    "result.facts.product": "Produit",
    "result.facts.track": "Canal de version",
    "result.facts.track.unknown": "inconnu",
    "result.facts.eol_tag": "Fin de vie",
    "result.facts.schedule": "Calendrier de versions",
    "result.facts.schedule.stale": (
        "{version} est plus récente que cette copie du calendrier des "
        "versions OpenCloud, ce calendrier est donc probablement obsolète. Ce "
        "n'est pas retenu contre l'instance -"
    ),
    "result.facts.schedule.stale_generated": (
        "{version} est plus récente que cette copie du calendrier des "
        "versions OpenCloud, générée le {generated}, ce calendrier est donc "
        "probablement obsolète. Ce n'est pas retenu contre l'instance -"
    ),
    "result.facts.schedule.link": "consultez la page de cycle de vie publiée",
    "result.facts.signin": "Connexion",
    "result.facts.signin.external": "Fournisseur externe",
    "result.facts.signin.upstream_tag": "amont",
    "result.facts.signin.version_unavailable": "version non exposée",
    "result.facts.signin.advisories": "consulter les avis de sécurité",
    "result.facts.signin.builtin": "Fournisseur d'identité intégré",
    "result.facts.signin.none": "Non détecté -",
    "result.facts.signin.link": "comment la connexion OpenCloud est configurée",
    "result.facts.proxy": "Proxy inverse",
    "result.facts.proxy.detected": "Détecté",
    "result.facts.http3": "HTTP/3",
    "result.facts.http3.value": "Annoncé via UDP {ports} - vérifiez que votre pare-feu autorise délibérément ce trafic (non noté)",
    "result.facts.http3.noport": "Annoncé via UDP - vérifiez que votre pare-feu autorise délibérément ce trafic (non noté)",
    "result.facts.upgrade_path": "Chemin de mise à jour",
    "result.facts.upgrade_path.complete": "{target} corrige tous les avis connus",
    "result.facts.upgrade_path.partial": "{target} laisse encore {open} ouvert ; {safe} est la première version qui les corrige tous",
    "result.facts.upgrade_path.unfixed": "{target} laisse encore {open} ouvert ; aucune version publiée ne les corrige tous pour l’instant",
    "result.facts.office": "Bureautique",
    "result.facts.calendar": "Calendrier",
    "result.facts.calendar.detected": "Une réponse a été reçue sur le chemin CalDAV",
    "result.facts.newest": "Version la plus récente",
    "result.facts.score": "Score",
    "result.facts.score.value": "{rating} sur 5",
    "result.counter.critical": "Critique",
    "result.counter.warning": "Avertissement",
    "result.counter.info": "Info",
    "result.counter.advisories": "Avis de sécurité",
    "result.counter.passed": "Réussi",
    "result.verdict.why": "Pourquoi cette note :",
    "result.verdict.caveat": (
        "La note résume les contrôles ci-dessous. Elle ne certifie pas que "
        "l’instance est sécurisée : l’analyse ne voit que ce qu’elle expose "
        "sans connexion. "
        '<a href="#scan-limits">Ce qu\'elle ne peut pas voir</a>.'
    ),
    "result.fix": "Correctif :",
    "result.documentation": "Documentation",
    "result.explain.title": "Ce que signifie ce contrôle",
    "result.plan.kicker": "Plan de remédiation",
    "result.plan.heading": "Ce qui vous mène à {label}",
    "result.plan.then": "puis {label}",
    "result.plan.still": "toujours {label}",
    "result.plan.note": "Le plan donne la priorité aux changements qui améliorent la note. La note indiquée à chaque étape suppose que cette étape et toutes les précédentes sont terminées. Les constats de même gravité partagent un plafond : plusieurs corrections peuvent donc être nécessaires avant que la note augmente.",
    "result.plan.blocked.heading": "Ce qui limite la note et ne peut pas être corrigé",
    "result.plan.blocked.note": (
        "Ces valeurs sont codées en dur dans OpenCloud et ne peuvent pas être "
        "modifiées dans la configuration. Le plan ne peut donc pas atteindre "
        "une note supérieure."
    ),
    "result.rehearsal.kicker": "Simulation de mise à niveau",
    "result.rehearsal.heading": "Ce qu’une mise à niveau corrigerait",
    "result.rehearsal.lede": (
        "Chaque version pertinente est évaluée avant son installation. Une "
        "mise à niveau change la version, pas le proxy inverse ; les constats "
        "de cette page restent donc exactement ceux mesurés par cette analyse."
    ),
    "result.rehearsal.line": "branche {line}",
    "result.rehearsal.recommended": "recommandée",
    "result.rehearsal.eol": "fin de vie",
    "result.rehearsal.grade": "atteindrait {label}",
    "result.rehearsal.fixes": "Corrige",
    "result.rehearsal.still": "Toujours concernée par",
    "result.rehearsal.introduces": "Désormais concernée par",
    "result.rehearsal.clean": "Corrige tous les avis de sécurité qui concernent cette version.",
    "result.rehearsal.nothing": "Ne corrige aucun avis de sécurité concernant cette version.",
    "result.rehearsal.capped": (
        "La version seule atteindrait {label} ; les constats de cette page "
        "maintiennent la note à son niveau actuel."
    ),
    "result.rehearsal.note": (
        "Cette simulation utilise uniquement le calendrier des versions et la "
        "base d’avis disponibles pour cette analyse. Les versions et avis "
        "publiés depuis n’y figurent pas."
    ),
    "result.eol.alert": (
        "Cette version ne reçoit plus de correctifs de sécurité. Rien "
        "d'autre sur cette page ne peut faire remonter la note tant qu'elle "
        "n'est pas mise à niveau."
    ),
    "result.advisories.kicker": "Avis de sécurité",
    "result.advisories.heading": "Avis de sécurité connus pour cette version",
    "result.advisories.lede": "Avis publiés dont la plage concernée inclut {version}.",
    "result.advisories.fallback_id": "avis",
    "result.advisories.unrated": "non noté",
    "result.advisories.no_summary": "Aucun résumé publié.",
    "result.advisories.read": "Lire l'avis",
    "result.findings.kicker": "Constats",
    "result.findings.heading": "Contrôles en échec",
    "result.findings.lede": (
        "Chaque constat limite la note selon sa gravité. Corrigez d’abord les "
        "constats critiques, car ils ont le plus d’effet sur l’évaluation."
    ),
    "result.findings.filter.aria": "Filtrer les constats par gravité",
    "result.findings.filter.active": "Affichage des constats de gravité {severity} uniquement.",
    "result.findings.filter.clear": "Afficher tous les constats",
    "result.findings.allclear.tag": "Tout est en ordre",
    "result.findings.allclear.body": (
        "Tous les contrôles exécutés par ce scanner ont réussi sur cette "
        "instance."
    ),
    "result.hardening.kicker": "Durcissement",
    "result.hardening.heading": "Durcissement à ajouter",
    "result.hardening.lede": "Ces paramètres renforcent la protection contre les risques courants. Consultez l’explication et la correction proposée pour chacun.",
    "result.hardening.tag": "durcissement",
    "result.header.tag": "en-tête",
    # ------------------------------------------------- configuration fragment
    "result.fragment.kicker": "Extrait de configuration",
    "result.fragment.heading": "À coller dans votre configuration",
    "result.fragment.lede": (
        "Les constats ci-dessus, dans la syntaxe du fichier qui doit changer. "
        "Choisissez où votre instance est configurée."
    ),
    "result.fragment.caution": (
        "Lisez la ligne « Correction » de chaque constat avant de coller. Ce "
        "sont les valeurs que les vérifications recherchent, pas un examen de "
        "ce dont votre déploiement a besoin."
    ),
    "result.fragment.picker": "Format de configuration",
    "result.fragment.file": "À placer dans {name}.",
    "result.fragment.copy": "Copier",
    "result.fragment.copied": "Copié",
    "result.fragment.copy_failed": "Copie impossible",
    "result.fragment.nothing": "Aucun constat restant ne peut être corrigé dans ce format. Utilisez {flavours} pour la configuration concernée.",
    "result.fragment.elsewhere": (
        "Ceux-ci se corrigent ailleurs - ils relèvent de {flavours} :"
    ),
    "result.fragment.undecided": "Ces constats nécessitent un réglage adapté à votre installation. Suivez les instructions de correction de chacun pour déterminer la valeur.",
    # ------------------------------------------------------------ scan again
    "result.rescan": "Analyser à nouveau",
    "result.rescan.ready": "Cette instance peut être analysée à nouveau.",
    "result.rescan.wait": "Nouvelle analyse possible dans {countdown}.",
    "result.rescan.note": "La prochaine analyse conserve la cible, les exclusions et le canal de versions pour permettre la comparaison. Veuillez attendre la fin du délai, ou exécuter le scanner open source sans limite sur votre machine :",
    "result.rescan.self_host": "l'exécuter vous-même",
    "result.excluded.kicker": "Exclu",
    "result.fingerprint.kicker": "Configuration",
    "result.fingerprint.heading": "Cette installation a-t-elle changé ?",
    "result.fingerprint.body": (
        "Chaque groupe contient une empreinte de la configuration mesurée, "
        "sans en exposer les valeurs. Comparez les empreintes d'analyses "
        "ayant la même couverture de mesure pour détecter les changements "
        "de configuration, même si la note reste identique."
    ),
    "result.fingerprint.overall": "Tous groupes confondus : {digest}",
    "result.fingerprint.unmeasured": "Non mesuré lors de cette analyse",
    "result.fingerprint.unavailable": (
        "Ce rapport n'enregistre aucune empreinte de configuration : il ne "
        "peut donc pas dire si l'installation a changé. Ce n'est pas la même "
        "chose qu'une installation restée identique."
    ),
    "fingerprint.group.tls": "Sécurité du transport",
    "fingerprint.group.headers": "En-têtes de sécurité",
    "fingerprint.group.sharing": "Partage",
    "fingerprint.group.authentication": "Authentification",
    "fingerprint.group.proxy": "Proxy et diffusion",
    "result.coverage.kicker": "Couverture",
    "result.coverage.heading": "Ce que cette analyse n'a pas mesuré",
    "result.coverage.note": (
        "Une note décrit ce que cette analyse a établi. Ces vérifications "
        "n'ont abouti à aucune conclusion : la note ne dit donc rien à leur "
        "sujet."
    ),
    "result.coverage.summary": (
        "{measured} vérifications sur {total} ont abouti à une conclusion."
    ),
    "result.coverage.breakdown": (
        "{evaluated} vérifications évaluées, {skipped} ignorées, "
        "{indeterminate} indéterminées, {networkLimited} limitées par le réseau."
    ),
    "result.coverage.complete": (
        "Toutes les vérifications prévues par cette analyse ont abouti."
    ),
    "result.coverage.unavailable": (
        "Ce rapport a été écrit avant que les analyses n'enregistrent leur "
        "couverture ; il ne dit donc pas quelles vérifications ont eu lieu. "
        "Ce n'est pas la même chose qu'une analyse sans lacune."
    ),
    "coverage.reason.not_applicable": "Ne s'applique pas à cette instance",
    "coverage.reason.probe_disabled": (
        "La vérification était désactivée pour cette analyse"
    ),
    "coverage.reason.prerequisite_missing": (
        "L'instance n'a pas publié les données nécessaires à cette vérification"
    ),
    "coverage.reason.timeout": "Rien n'a répondu à temps",
    "coverage.reason.unreadable": "La réponse n'a pas pu être lue",
    "coverage.reason.no_route": "Ce scanner n'a aucune route vers cette adresse",
    "coverage.group.hardening": "Paramètres de durcissement",
    "coverage.group.header": "En-têtes de sécurité",
    "coverage.group.advisoryHeader": "En-têtes recommandés",
    "coverage.group.advisoryCheck": "Observations recommandées",
    "coverage.group.extraCheck": "Vérifications supplémentaires",
    "coverage.group.tls": "Sécurité du transport",
    "coverage.group.dns": "DNS",
    "coverage.group.addressParity": "Adresses",
    "coverage.group.capabilities": "Fonctionnalités",
    "coverage.group.updates": "Mises à jour",
    "coverage.group.integrations": "Intégrations",
    "result.excluded.heading": "Signalé, mais non comptabilisé",
    "result.excluded.waived.heading": "Contrôles ignorés à votre demande",
    "result.excluded.waived.note": (
        "Ces contrôles ont échoué, mais vos exclusions les retirent du calcul "
        "de la note."
    ),
    "result.excluded.unfixable.heading": "Valeurs imposées par OpenCloud",
    "result.excluded.unfixable.note": "Ces valeurs sont fixées dans le code d’OpenCloud et ne sont pas configurables. Elles sont fournies à titre informatif et n’affectent pas la note.",
    "result.scope.kicker": "Périmètre",
    "result.scope.heading": "Ce que cette analyse ne peut pas voir",
    "result.scope.body": (
        "Tout ce qui précède a été lu sans se connecter, ce qui est à la "
        "fois l'objectif et la limite. <strong>L'absence de constat n'est "
        "pas une preuve de sécurité</strong>, et la meilleure note que cette "
        "page puisse donner n'affirme pas que l'instance est sécurisée - "
        "seulement qu'aucune des vérifications effectuées ici n'a échoué. "
        "Des catégories entières échappent totalement à une analyse non "
        "authentifiée : le système d'exploitation et ses paquets, "
        "l'environnement d'exécution des conteneurs, la configuration propre "
        "du proxy inverse, les sauvegardes et leurs restaurations, le "
        "stockage derrière l'instance, la gestion des secrets et des clés, "
        "les comptes, les mots de passe et la connexion multifacteur, les "
        "permissions sur les partages existants, la chaîne "
        "d'approvisionnement logicielle, et tout ce qui ne se révèle qu'à un "
        "utilisateur connecté. C'est aussi le cas de ces deux éléments, qui "
        "semblent pourtant devoir être visibles et ne le sont pas :"
    ),
    "result.scope.audit": (
        "<strong>Journalisation d'audit.</strong> Le service d'audit "
        "d'OpenCloud ne fait que consommer le bus d'événements interne - il "
        "ne publie aucun point de terminaison et n'apparaît dans aucun "
        "document non authentifié - si bien que son fonctionnement ne peut "
        "absolument pas être établi depuis l'extérieur. Ce n'est pas "
        "contrôlé."
    ),
    "result.scope.integrations": (
        "<strong>Si une intégration bureautique ou de calendrier est "
        "configurée <em>correctement</em>.</strong> Cette page ne signale "
        "que le fait qu'un fournisseur d'application est enregistré, ou que "
        "quelque chose répond sur le chemin CalDAV. Les règles de partage, "
        "les secrets WOPI et la configuration propre du second service se "
        "trouvent tous derrière une connexion et ne sont pas contrôlés."
    ),
    "result.tls.kicker": "Transport",
    "result.tls.heading": "Sécurité du transport",
    "result.tls.lede": (
        "Ce que la couche TLS a indiqué avant qu'un seul octet HTTP ne soit "
        "échangé. Les constats ci-dessus en tiennent déjà compte ; ceci en "
        "est la mesure sous-jacente."
    ),
    "result.tls.protocol": "Protocole",
    "result.tls.bits": "({bits} bit)",
    "result.tls.deprecated": "Versions obsolètes",
    "result.tls.deprecated.accepted": "Encore acceptées : {list}",
    "result.tls.deprecated.refused": "Refusées : {list}",
    "result.tls.chain": "Chaîne",
    "result.tls.chain.trusted": "Fiable",
    "result.tls.chain.not_established": "Non établie",
    "result.tls.chain.not_trusted": "Non fiable",
    "result.tls.chain.incomplete_note": "- aucun chemin vers une racine publique",
    "result.tls.issued_to": "Délivré à",
    "result.tls.unnamed": "sans nom",
    "result.tls.issued_by": "Délivré par",
    "result.tls.unknown": "inconnu",
    "result.tls.valid_for": "Valide pour",
    "result.tls.validity": "Validité",
    "result.tls.validity.range": "{start} à {end}",
    "result.tls.validity.expired": "- expiré il y a {days} jour(s)",
    "result.tls.validity.remaining": "- {days} jour(s) restant(s)",
    "result.tls.lifetime": "Délivré pour",
    "result.tls.lifetime.days": "{days} jour(s)",
    "result.tls.ocsp": "Agrafage OCSP",
    "result.tls.ocsp.stapled": "Une réponse de révocation est fournie",
    "result.tls.ocsp.not_stapled": "Aucune réponse de révocation fournie",
    "result.tls.ocsp.undetermined": "Non déterminé",
    "result.raw.kicker": "Données brutes",
    "result.raw.heading": "Détails techniques",
    "result.raw.lede": (
        "Le document de résultat complet, exactement tel que le plugin le "
        "voit."
    ),
    "result.raw.summary": "Afficher le JSON brut",
    "result.export.kicker": "Export",
    "result.export.heading": "Exporter ce résultat",
    "result.export.lede": (
        "La même analyse, présentée de quatre façons. Chacune est générée à "
        "la demande et disparaît avec l'analyse elle-même."
    ),
    "result.export.pdf": "Rapport PDF",
    "result.export.pdf.hint": "Pour un ticket, une revue ou une impression.",
    "result.export.html": "Télécharger le rapport",
    "result.export.html.hint": (
        "Un fichier qui reste lisible après l'expiration de ce lien. Il s'ouvre "
        "hors ligne, n'effectue aucune requête réseau et ne se met pas à "
        "jour."
    ),
    "result.export.remediation.md": "Kit de correction (Markdown)",
    "result.export.remediation.md.hint": (
        "Uniquement ce qui reste ouvert : chaque constat, ce qui a été observé "
        "et les fragments nginx, Caddy, Traefik, Compose et .env qui le "
        "corrigent. Pour une pull request ou un runbook."
    ),
    "result.export.remediation.html": "Kit de correction (HTML)",
    "result.export.remediation.html.hint": (
        "Le même kit sous forme d'une page consultable hors ligne ou imprimable."
    ),
    "result.export.csv": "CSV",
    "result.export.csv.hint": "Une ligne par constat, pour un tableur.",
    "result.export.sarif": "SARIF",
    "result.export.sarif.hint": "Pour un tableau de bord d'analyse de code.",
    "result.export.json": "JSON",
    "result.export.json.hint": "Le document brut qu'évalue le plugin.",
    "result.export.passed.heading": "Ce qui est déjà en règle",
    "result.export.passed.note": (
        "Ces contrôles sont revenus propres, ils n'apparaissent donc pas dans le "
        "plan ci-dessus."
    ),
    "result.share.kicker": "Partager",
    "result.share.heading": "Partager ce rapport",
    "result.share.lede": "Copiez le lien ou un résumé, ou ouvrez un brouillon dans votre messagerie. Ce service n’envoie pas le rapport à votre place.",
    "result.share.warning": (
        "L'adresse de cette page est la seule chose qui la protège : qui la "
        "détient peut lire le rapport jusqu'à son expiration. La publier dans "
        "un canal la partage avec tout le monde, et avec tout ce qui consulte "
        "les liens pour en faire un aperçu. Copiez plutôt le résumé lorsque "
        "ce sont les constats qui comptent."
    ),
    "result.share.email": "Partager par courriel",
    "result.share.email.hint": (
        "Ouvre votre propre logiciel de messagerie avec le message prêt. Rien "
        "ne quitte votre navigateur avant l'envoi."
    ),
    "result.share.email.subject": "Rapport de sécurité OpenCloud pour {target}",
    "result.share.email.body": (
        "Voici le rapport de sécurité de notre instance OpenCloud :\n\n"
        "{url}\n\n"
        "Ce lien est ce qui donne accès au rapport : traitez-le comme un mot "
        "de passe. Il expire de lui-même, après quoi la page n'existe plus."
    ),
    "result.share.link": "Copier le lien",
    "result.share.link.hint": (
        "L'adresse de cette page. Quiconque la reçoit peut ouvrir le rapport."
    ),
    "result.share.summary": "Copier le résumé",
    "result.share.summary.hint": (
        "Les constats en texte, sans aucun lien. Le plus sûr à coller dans un "
        "canal de discussion."
    ),
    "result.share.summary.body": (
        "Rapport de sécurité OpenCloud - {domain}\n"
        "Note {label} ({rating} sur 5)\n"
        "Critiques {critical} | Avertissements {warning} | Info {info} | "
        "Alertes {advisories} | Réussis {passed}\n"
        "Mesuré avec check-opencloud-security."
    ),
    "result.share.done": "Copié",
    "result.share.failed": "Copie impossible",
    "result.share.fallback": "L'adresse de ce rapport :",
    "result.feedback.prompt": "Vous pensez que l'analyse s'est trompée ?",
    "result.feedback.link": "Signaler un faux positif ou un faux négatif",
    "result.expiry.one": (
        "Cette page expire dans environ 1 minute, après quoi le lien cesse "
        "de fonctionner et le résultat disparaît."
    ),
    "result.expiry.many": (
        "Cette page expire dans environ {minutes} minutes, après quoi le "
        "lien cesse de fonctionner et le résultat disparaît."
    ),
    "result.expiry.warning.one": "Ce rapport disparaît dans environ 1 minute.",
    "result.expiry.warning.many": (
        "Ce rapport disparaît dans environ {minutes} minutes."
    ),
    "result.expiry.warning.action": "Téléchargez une copie pour le conserver",
    "result.expiry.gone": (
        "Ce rapport a expiré. Le lien et ses téléchargements ne fonctionnent plus."
    ),
    # ----------------------------------------- transport facts beside the grade
    "tls.fact.protocol": "Version TLS",
    "tls.fact.protocol.detail": "accepte aussi {list}",
    "tls.fact.expiry": "Expiration du certificat",
    "tls.fact.expiry.expired": "expiré il y a {days} jour(s)",
    "tls.fact.expiry.remaining": "{days} jour(s) restant(s)",
    "tls.fact.chain": "Chaîne",
    "tls.fact.chain.incomplete": "Incomplète",
    "tls.fact.chain.incomplete.detail": "aucun chemin vers une racine publique",
    "tls.fact.chain.untrusted": "Non fiable",
    "tls.fact.chain.untrusted.detail": "autosigné, ou autorité inconnue",
    "tls.fact.chain.unknown": "Non établie",
    "tls.fact.chain.unknown.detail": "la négociation n'a jamais atteint le certificat",
    "tls.fact.chain.ok": "Complète et fiable",
}
