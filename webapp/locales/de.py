"""The German translation of :mod:`webapp.locales.en`."""

from __future__ import annotations

MESSAGES: dict[str, str] = {
    # ---------------------------------------------------------------- site
    # ------------------------------------------------ der Betriebsbereich
    "admin.title": "Betriebsbereich",
    "admin.description": "Dienstzustand, Referenzdaten und das Audit-Log.",
    "admin.kicker": "Betrieb",
    "admin.tabs.aria": "Betreiberbereich",
    "admin.tabs.overview": "Überblick",
    "admin.tabs.configuration": "Konfiguration",
    "admin.tabs.rules": "Regeln",
    "admin.tabs.decisions": "Entscheidungen",
    "admin.config.title": "Konfiguration",
    "admin.config.lede": "Alle COS_WEB_*-Variablen, die dieser Dienst liest, und ihre aktuell wirksamen Werte.",
    "admin.config.scope": "Hier stehen die beim Start wirksamen Einstellungen dieses Webprozesses. OpenCloud und der Scan-Worker haben eine eigene Konfiguration. Bei Zugangsdaten wird nur angezeigt, ob sie gesetzt sind.",
    "admin.config.source.environment": "Gesetzt",
    "admin.config.source.default": "Standard",
    "admin.config.secret.set": "Gesetzt (Wert verborgen)",
    "admin.config.unset": "Nicht gesetzt",
    "admin.config.default": "Dokumentierter Standard:",
    "admin.config.unknown.kicker": "Schreibweise prüfen",
    "admin.config.unknown.heading": "Variablen, die dieser Dienst nicht liest",
    "admin.config.unknown.lede": "Diese Variablen beginnen mit COS_WEB_, gehören aber zu keiner bekannten Einstellung. Prüfe die Schreibweise: Bei einem Tippfehler gilt weiterhin der Standardwert. Die Werte dieser Variablen werden nicht angezeigt.",
    "admin.config.group.storage": "Speicher und Worker",
    "admin.config.group.scanning": "Ablauf eines Scans",
    "admin.config.group.targets": "Was gescannt werden darf",
    "admin.config.group.limits": "Ratenbegrenzung und Missbrauchsschutz",
    "admin.config.group.approval": "Freigabe von Zielen",
    "admin.config.group.network": "Öffentliche Adresse, Proxy und Indexierung",
    "admin.config.group.reference": "Release- und Advisory-Daten",
    "admin.config.group.interfaces": "API-Dokumentation und Agent-Endpunkt",
    "admin.config.group.mcp_auth": "Anmeldung am Agent-Endpunkt",
    "admin.config.group.admin": "Betreiberbereich",
    "admin.config.group.audit": "Audit-Log",
    "admin.config.group.protection": "Löschung, Signaturen und Verschlüsselung",
    "admin.config.group.frontend": "Frontend",
    "admin.rules.title": "Geltende Regeln",
    "admin.rules.lede": "Wie eine Note entsteht und welche Regeln diese Bereitstellung für Anfragen durchsetzt – einschließlich der aktuell wirksamen Werte.",
    "admin.rules.scope": "Diese Übersicht zeigt die beim Prozessstart geladene Konfiguration und die im Code festgelegten Regeln. Zieladressen und Besucherdaten werden nicht angezeigt.",
    "admin.rules.on": "Aktiv",
    "admin.rules.off": "Aus",
    "admin.rules.variables": "Gesetzt über",
    "admin.rules.rating.kicker": "Noten",
    "admin.rules.rating.heading": "Wie eine Instanz bewertet wird",
    "admin.rules.rating.lede": 'Der Scanner berechnet die Note nach diesen Regeln. Der Webdienst zeigt das Ergebnis an.',
    "admin.rules.rating.scale": "Die Skala",
    "admin.rules.rating.caps": "Wie fehlgeschlagene Prüfungen die Note begrenzen",
    "admin.rules.rating.version.title": "Die Version bestimmt die Ausgangsnote",
    "admin.rules.rating.version.body": "Die Ausgangsnote richtet sich nach dem Supportstatus der Release-Linie und den bekannten Schwachstellen der Version. Fehlgeschlagene Prüfungen können die Note verschlechtern.",
    "admin.rules.rating.overrides.title": "Supportende und Release-Track",
    "admin.rules.rating.shared.title": "Notengrenzen nach Schweregrad",
    "admin.rules.rating.extra.title": "Zusatzprüfungen zählen zur Note",
    "admin.rules.rating.extra.body": "Transportsicherheit, Header und die übrigen Zusatzprüfungen begrenzen die Note wie Härtungsprüfungen, statt nur im Bericht zu erscheinen.",
    "admin.rules.rating.waivers.title": "Ausnahmen, die Besucher wählen können",
    "admin.rules.rating.waivers.body": "Im Formular kannst du {count} Härtungsprüfungen ausnehmen. Ausgenommene Prüfungen bleiben im Bericht gekennzeichnet, begrenzen aber die Note nicht. Das Supportende beeinflusst die Note immer.",
    "admin.rules.rating.track.title": "Release-Track",
    "admin.rules.rating.track.body": "Ohne Auswahl im Formular gilt der Track {track}. Der Track ändert, wie eine Version bewertet wird, nie wie intensiv die Instanz geprüft wird.",
    "admin.rules.rating.reference.title": "Referenzdaten für die Bewertung",
    "admin.rules.rating.reference.body": "{advisories} Sicherheitsmeldungen in der Datenbank; Release-Zeitplan vom {schedule}.",
    "admin.rules.rating.more": "Die <a href=\"/grades\">Notenseite</a> erklärt Besuchern jede Note mit denselben Begriffen.",
    "admin.rules.group.submissions": "Limits für Einreichungen",
    "admin.rules.group.submissions.lede": "Wie oft ein Client einen Scan anfordern kann und wie der Dienst mit hoher Last umgeht.",
    "admin.rules.group.probe": "Scan-Sperre",
    "admin.rules.group.probe.lede": "Grenzen für wiederholte Anfragen an Ziele, die sich nicht scannen lassen.",
    "admin.rules.group.targets": "Was gescannt werden darf",
    "admin.rules.group.targets.lede": "Ziele werden vor dem Verbindungsaufbau und vor jeder Weiterleitung geprüft.",
    "admin.rules.group.scanner": "Wie intensiv ein Host geprüft wird",
    "admin.rules.group.scanner.lede": "Die Einstellungen, mit denen jeder Scan dieser Bereitstellung ausgeführt wird. Anfragen können sie nicht ändern.",
    "admin.rules.group.operator": "Zugangsdaten und Betreiberaktionen",
    "admin.rules.group.operator.lede": "Grenzen für Anfragen mit Zugangsdaten und für Aktionen im Betreiberbereich.",
    "admin.rules.rule.client_limit.title": "Limit pro Client",
    "admin.rules.rule.client_limit.body": 'Höchstens {limit} Einreichungen pro Client innerhalb von {window}. Jede IPv4-Adresse zählt als ein Client. Bei IPv6 zählt jedes /{ipv6}-Netz als ein Client.',
    "admin.rules.rule.daily_cap.title": "Tageslimit",
    "admin.rules.rule.daily_cap.body": "Höchstens {limit} Einreichungen pro Client alle {window}, zusätzlich zum Limit pro Client.",
    "admin.rules.rule.target_cooldown.title": "Abkühlzeit pro Ziel",
    "admin.rules.rule.target_cooldown.body": "Dieselbe Instanz darf einmal alle {cooldown} gescannt werden, egal wer fragt.",
    "admin.rules.rule.batch.title": "Stapelgröße",
    "admin.rules.rule.batch.body": 'Ein Stapel enthält höchstens {limit} Ziele. Jedes Ziel wird bei allen Limits einzeln gezählt.',
    "admin.rules.rule.queue.title": "Scan-Warteschlange bei hoher Last",
    "admin.rules.rule.queue.body": "Bis zu {workers} Scans laufen gleichzeitig. Weitere Anfragen warten in der Reihenfolge ihres Eingangs. Hohe Last führt nicht zur Ablehnung.",
    "admin.rules.rule.agent_wait.title": "Grenze automatischer Wiederholungen",
    "admin.rules.rule.agent_wait.body": 'MCP und die Workflows wiederholen die Anfrage nach einer Retry-After-Wartezeit von bis zu {wait} automatisch, höchstens {attempts} Mal. Längere Wartezeiten werden an den Aufrufer zurückgegeben.',
    "admin.rules.rule.probe_block.title": "Sperre nach wiederholten Verstößen",
    "admin.rules.rule.probe_block.body": "{limit} Verstöße innerhalb von {window} sperren das Netz des Clients für {block}.",
    "admin.rules.rule.probe_escalation.title": "Wiederholte Sperren werden länger",
    "admin.rules.rule.probe_escalation.body": "Ein Netz, das innerhalb von {repeat} nach seiner letzten Sperre erneut gesperrt wird, wartet jedes Mal {factor}-mal länger: {steps}.",
    "admin.rules.rule.probe_network.title": "Die Sperre gilt für ein Netz",
    "admin.rules.rule.probe_network.body": "Eine Sperre gilt für das IPv4-/{ipv4}- oder IPv6-/{ipv6}-Netz des Clients. Ein Adresswechsel innerhalb dieses Netzes umgeht die Sperre nicht.",
    "admin.rules.rule.strike_scans.title": "Ein Scan ohne OpenCloud ist ein Verstoß",
    "admin.rules.rule.strike_scans.body": 'Ein Verstoß wird gezählt, wenn status.php nicht antwortet, ungültiges JSON liefert, ein anderes Produkt nennt oder das Zeitlimit des Scans abläuft. Eine erneute Anfrage für denselben Host zählt als weiterer Verstoß. Ein abgeschlossener Scan zählt nicht.',
    "admin.rules.rule.strike_refusals.title": "Ein abgelehntes Ziel ist ein Verstoß",
    "admin.rules.rule.strike_refusals.body": "Eine Einreichung, die wegen ihres Ziels abgelehnt wird, zählt; ein Tippfehler oder ein nicht auflösbarer Name nicht:",
    "admin.rules.refusal.blocked": "eine Adresse, die dieses Deployment ausschließt",
    "admin.rules.refusal.internal": "ein lokaler oder interner Name",
    "admin.rules.refusal.not_approved": "eine Instanz, die der Freigabemodus nicht freigegeben hat",
    "admin.rules.refusal.private": "eine private, Loopback- oder Link-Local-Adresse",
    "admin.rules.refusal.unstable": "ein Name, dessen Abfragen sich widersprechen",
    "admin.rules.refusal.wildcard_dns": "ein Wildcard- oder Rebinding-DNS-Name",
    "admin.rules.rule.private_addresses.title": "Nur öffentliche Adressen",
    "admin.rules.rule.private_addresses.body": 'Jede aufgelöste Adresse muss eine öffentliche Unicast-Adresse sein. Schon eine einzige private Adresse führt zur Ablehnung. Auch diese Adressen werden abgelehnt:',
    "admin.rules.rule.internal_names.title": "Lokale Namen und Metadaten-Endpunkte",
    "admin.rules.rule.internal_names.body": "Nach Name wie nach Adresse abgelehnt:",
    "admin.rules.rule.wildcard_dns.title": "Wildcard- und Rebinding-DNS-Namen",
    "admin.rules.rule.wildcard_dns.body": "Diese Dienste kodieren eine IP-Adresse im Hostnamen. Um diese Adresse zu scannen, gib die IP-Adresse direkt ein:",
    "admin.rules.rule.dns_consistency.title": "Ein Name muss zweimal gleich auflösen",
    "admin.rules.rule.dns_consistency.body": "Ein eingereichter Name wird zweimal abgefragt und abgelehnt, wenn die Antworten keine Adresse teilen; jede Adresse aus beiden wird geprüft.",
    "admin.rules.rule.redirects.title": "Jede Weiterleitung wird geprüft",
    "admin.rules.rule.redirects.body": "Eine Weiterleitung wird wie das eingereichte Ziel aufgelöst und geprüft, bevor ihr gefolgt wird. Der Scan stellt nur Verbindungen zu Adressen her, die die Prüfung bestanden haben.",
    "admin.rules.rule.exclusions.title": "Ausschlüsse",
    "admin.rules.rule.exclusions.body": "{count} ausgeschlossene Einträge aus der Umgebung und dem Tab „Übersicht“.",
    "admin.rules.rule.allowed_hosts.title": "Vom Schutz ausgenommene Hosts",
    "admin.rules.rule.allowed_hosts.body": "Diese Namen umgehen die Regeln für öffentliche Adressen. Ausschlüsse gelten weiterhin:",
    "admin.rules.rule.approval.title": "Freigabemodus",
    "admin.rules.rule.approval.body": "Nur freigegebene Instanzen werden gescannt; alles andere wird mit 403 abgelehnt. {count} gelistete Einträge; DNS-Freigabeeintrag: {record}.",
    "admin.rules.rule.stop_when_not_opencloud.title": "Eine Anfrage für einen Host ohne OpenCloud",
    "admin.rules.rule.stop_when_not_opencloud.body": "Eine Antwort von status.php, die nicht OpenCloud ist, beendet den Scan, ohne erneuten Versuch über unverifiziertes HTTPS oder einfaches HTTP.",
    "admin.rules.rule.single_address.title": "Eine Adresse pro Scan",
    "admin.rules.rule.single_address.body": "Ein Name mit mehreren Adressen wird auf einer davon gescannt, nie auf jedem Knoten eines Pools.",
    "admin.rules.rule.no_port_scan.title": "Keine zusätzlichen Ports",
    "admin.rules.rule.no_port_scan.body": "Nur der eingereichte Port wird kontaktiert; die Debug-Ports werden nicht geprüft.",
    "admin.rules.rule.load.title": "Last pro Scan",
    "admin.rules.rule.load.body": "Höchstens {concurrency} gleichzeitige Anfragen mit jeweils {timeout} Zeit; ein gesamter Scan wird nach {job} abgebrochen.",
    "admin.rules.rule.purge_attempts.title": "Versuche mit dem Löschzugang",
    "admin.rules.rule.purge_attempts.body": 'Nach {limit} Versuchen mit falschen Zugangsdaten pro Client innerhalb von {window} werden weitere Versuche bis zum Ende dieses Zeitraums abgelehnt. Richtige Zugangsdaten werden nicht mitgezählt.',
    "admin.rules.rule.admin_refresh.title": "Aktualisierungsknöpfe",
    "admin.rules.rule.admin_refresh.body": "Jede Aktualisierung der Referenzdaten kann einmal alle {cooldown} ausgelöst werden.",
    "admin.docs.kicker": "Betreiberdokumentation",
    "admin.docs.source": "Aus <code>{file}</code> im Repository, auf Englisch.",
    "admin.decisions.title": "Architekturentscheidungen",
    "admin.decisions.lede": "Jeder Architekturentscheidungseintrag dieses Repositorys mit seinem Status, auf Englisch wie geschrieben.",
    "admin.decisions.search.label": "Entscheidungseinträge filtern",
    "admin.decisions.search.placeholder": "Nummer, Titel oder Status",
    "admin.decisions.search.empty": "Kein Eintrag passt. Die Seitensuche durchsucht auch den Text jedes Eintrags.",
    "admin.decisions.back": "Alle Entscheidungen",
    "admin.band": "Betriebsbereich - angemeldet als {user}",
    "admin.band.signout": "Abmelden",
    "admin.lede": "Prüfe den Dienstzustand und die Referenzdaten oder starte die täglichen Aktualisierungen des Workers manuell.",
    "admin.noscript": "JavaScript aktualisiert die Werte oben. Ohne JavaScript musst du die Seite neu laden, um aktuelle Werte zu sehen. Beide Aktualisierungsschaltflächen funktionieren weiterhin.",
    "admin.state.kicker": "Jetzt",
    "admin.state.heading": "Dienstzustand",
    "admin.state.lede": "Aktuelle Zählerstände und konfigurierte Begrenzungen. Einzelne Scanergebnisse und Client-Adressen sind hier nicht abrufbar.",
    "admin.state.worker": "Worker",
    "admin.state.worker.up": "Läuft",
    "admin.state.worker.down": "Antwortet nicht",
    "admin.state.worker.unknown": "Nicht feststellbar",
    "admin.state.store.down": (
        "Der Speicher antwortet nicht - das Lebenszeichen ist nicht lesbar"
    ),
    "admin.state.queue": "{depth} in der Warteschlange, {workers} Worker",
    "admin.state.ratelimit": "Ratenbegrenzung",
    "admin.state.ratelimit.value": "{limit} pro {window}s",
    "admin.state.cooldown.value": "{seconds}s pro Ziel",
    "admin.state.guard": "Missbrauchsschutz",
    "admin.state.guard.value": "{active} Netze gesperrt",
    "admin.state.guard.week": "letzte 7 Tage: {blocks} Sperren, {strikes} Verstöße, {daily}-mal Tageslimit erreicht",
    "admin.state.guard.off": "Scan-Sperre aus",
    "admin.state.schedule": "Release-Zeitplan",
    "admin.state.advisories": "Sicherheitsmeldungen",
    "admin.state.checked": "geprüft {when}",
    "admin.state.checked.failed": "geprüft {when} - der letzte Datenabruf ist fehlgeschlagen",
    "admin.state.checked.rejected": "geprüft {when} - die abgerufenen Daten haben die Validierung nicht bestanden",
    "admin.state.refresh.off": "die tägliche Aktualisierung ist aus",
    "admin.state.ago.minutes": "vor {minutes} Min.",
    "admin.state.ago.hours": "vor {hours} Std.",
    "admin.state.ago.days": "vor {days} Tagen",
    "admin.state.never": "nie",
    "admin.state.unknown": "unbekannt",
    "admin.state.age.seconds": "Vor {seconds}s gelesen",
    "admin.state.age.minutes": "Vor {minutes}m gelesen",
    "admin.state.age.waiting": "Warten auf den ersten Messwert",
    "admin.state.stale": "Der Dienst hat seit einiger Zeit nicht geantwortet. Die angezeigten Werte stammen von der letzten Abfrage und sind möglicherweise veraltet.",
    "admin.state.refresh": "Erneut lesen",
    "admin.state.copy": "Diagnose kopieren",
    "admin.state.copy.done": "Kopiert",
    "admin.state.copy.failed": "Kopieren nicht möglich",
    "admin.surfaces.kicker": "Angriffsfläche",
    "admin.surfaces.heading": "Was diese Installation anbietet",
    "admin.surfaces.lede": (
        'Diese beim Start geladenen Einstellungen stehen auch im Diagnosedokument. Änderungen erfordern einen Neustart. Deshalb fragt diese Seite keine Aktualisierungen ab.'
    ),
    "admin.surfaces.on": "An",
    "admin.surfaces.off": "Aus",
    "admin.surfaces.mcp": "Agenten-Endpunkt unter /mcp",
    "admin.surfaces.mcp.guarded": (
        "Ein Token des konfigurierten Ausstellers ist erforderlich."
    ),
    "admin.surfaces.mcp.open": "Kein Token erforderlich. Jeder Agent, der diesen Endpunkt erreicht, kann Scans starten.",
    "admin.surfaces.docs": 'API-Dokumentation im Browser unter /docs',
    "admin.surfaces.docs.contract": (
        'Bei ausgeschalteter Anzeige bleiben die Schnittstellenbeschreibungen /openapi.json, /arazzo.json und /.well-known/ai.json öffentlich.'
    ),
    "admin.surfaces.indexed": "Über Suchmaschinen auffindbar",
    "admin.surfaces.private": "Scans privater Netzwerkadressen",
    "admin.surfaces.private.found": (
        'Private Ziele sind erlaubt, und die Suchmaschinenindexierung ist aktiviert. Wer diesen Dienst findet, kann Ziele in dessen internem Netzwerk einreichen.'
    ),
    "admin.surfaces.private.estate": "Erlaubt, damit dieser Dienst Instanzen im eigenen internen Netz prüfen kann.",
    "admin.surfaces.encrypt": "Ergebnisse verschlüsselt gespeichert",
    "admin.surfaces.audit": "Audit-Log",
    "admin.surfaces.audit.file": (
        "Wird in eine Datei geschrieben, die den Container überdauert."
    ),
    "admin.surfaces.audit.memory": (
        "Ein Ring aus {count} Einträgen im Speicher dieses Prozesses, nichts "
        "auf der Platte."
    ),
    "admin.surfaces.targets": "Ziele im Klartext protokolliert",
    "admin.update.kicker": "Release",
    "admin.update.heading": "Aktualisierungen",
    "admin.update.running": "Läuft mit {version}.",
    "admin.update.available": "Release {version} ist verfügbar.",
    "admin.update.current": "Das ist das neueste Release.",
    "admin.update.unknown": "Ob es ein neueres Release gibt, ließ sich nicht herausfinden.",
    "admin.update.off": "Die Update-Prüfung ist ausgeschaltet (COS_WEB_UPDATE_CHECK).",
    "admin.update.install": "{version} jetzt installieren",
    "admin.update.downtime": 'Der Dienst prüft das Bundle anhand seiner GitHub-Build-Attestierung und startet anschließend Webdienst und Worker neu. Dabei ist der Dienst kurz nicht verfügbar; laufende Scans werden abgebrochen. Das Update bleibt bis zum nächsten Neustart der Container aktiv.',
    "admin.update.manual": 'Die Installation über diese Seite ist ausgeschaltet (COS_WEB_ADMIN_UPDATE_DIR). Lade das neue Image herunter und erstelle die Container neu.',
    "admin.update.outcome.requested": "Geprüft und installiert. Der Dienst startet gleich neu - lade die Seite neu.",
    "admin.update.outcome.current": "Es gibt nichts Neueres zu installieren.",
    "admin.update.outcome.disabled": "Automatische Updates sind in dieser Installation nicht eingerichtet.",
    "admin.update.outcome.failed": "Das Release ließ sich nicht laden oder prüfen. Nichts wurde geändert; das Log nennt den Grund.",
    "admin.exclusions.kicker": "Ausschlüsse",
    "admin.exclusions.heading": "Adressen, die dieser Dienst nicht scannt",
    "admin.exclusions.lede": (
        'Änderungen gelten ohne Neustart ab der nächsten Anfrage in jedem Prozess. Bereits eingereihte Scans ausgeschlossener Ziele werden ebenfalls abgelehnt. Diese Liste kann Scans ausschließlich sperren.'
    ),
    "admin.exclusions.add.label": "Hostname, .Suffix-Domain, Adresse oder CIDR-Bereich",
    "admin.exclusions.add.placeholder": "opencloud.example.com",
    "admin.exclusions.add.action": "Ausschließen",
    "admin.exclusions.add.hint": (
        "Eine Domain mit führendem Punkt schließt auch alles darunter aus. "
        "Ein Bereich wird gegen jede Adresse geprüft, zu der ein Hostname "
        "auflöst."
    ),
    "admin.exclusions.remove": "Zurücknehmen",
    "admin.exclusions.empty": "In dieser Installation ist nichts ausgeschlossen.",
    "admin.exclusions.source.configured": "Aus der Umgebung",
    "admin.exclusions.updated": "Zuletzt hier geändert am {when}.",
    "admin.exclusions.durability": (
        'Hier hinzugefügte Einträge werden in Redis gespeichert und gehen verloren, wenn Redis geleert wird. Verwende COS_WEB_BLOCKED_TARGETS für dauerhafte Ausschlüsse. Diese Einträge lassen sich auf dieser Seite nicht entfernen.'
    ),
    "admin.exclusions.unreadable": (
        "Der Speicher hat nicht geantwortet, die Ausschlüsse lassen sich "
        "gerade weder lesen noch ändern. Sie gelten weiterhin: ein Scan, der "
        "sie nicht prüfen kann, wird abgelehnt und nicht ausgeführt."
    ),
    "admin.blocklist.error.shape": (
        "Das ist kein Eintrag. Bitte einen Hostnamen, eine Domain mit "
        "führendem Punkt, eine Adresse oder einen CIDR-Bereich angeben."
    ),
    "admin.blocklist.error.configured": (
        "Dieser Eintrag stammt aus COS_WEB_BLOCKED_TARGETS. Dort entfernen "
        "und den Dienst neu starten, damit Bereitstellung und Liste nicht auseinanderlaufen."
    ),
    "admin.blocklist.error.full": (
        "Diese Liste ist voll. Dauerhafte Einträge gehören in "
        "COS_WEB_BLOCKED_TARGETS."
    ),
    "admin.blocklist.error.long": (
        'Der Eintrag überschreitet die maximale Länge eines Hostnamens. Gib höchstens 253 Zeichen ein.'
    ),
    "admin.outcome.excluded": "Ausgeschlossen. Ab der nächsten Anfrage abgelehnt.",
    "admin.outcome.withdrawn": "Zurückgenommen. Kann wieder gescannt werden.",
    "admin.actions.kicker": "Referenzdaten",
    "admin.actions.heading": "Referenzdaten aktualisieren",
    "admin.actions.lede": (
        'Diese Aktionen starten die täglichen Aktualisierungen des Workers manuell. Der Zeitplan muss alle bekannten Release-Linien behalten. Aktualisierungen der Sicherheitsmeldungen dürfen nur Einträge ergänzen. Schlägt der Abruf fehl, bleiben die vorhandenen Daten unverändert.'
    ),
    "admin.actions.schedule": "Release-Zeitplan abgleichen",
    "admin.actions.schedule.hint": "Liest die veröffentlichte Lifecycle-Seite neu.",
    "admin.actions.advisories": "Nach Advisories suchen",
    "admin.actions.advisories.hint": "Fragt den Advisory-Feed nach neuen Einträgen.",
    "admin.outcome.updated": "Aktualisiert. Das neue Dokument ist in Gebrauch.",
    "admin.outcome.unchanged": "Bereits aktuell - nichts geändert.",
    "admin.outcome.rejected": (
        "Abgelehnt: Die abgerufenen Daten haben die Prüfungen nicht bestanden; die "
        "bisherigen Daten bleiben in Gebrauch."
    ),
    "admin.outcome.failed": "Konnte nicht abgerufen werden. Nichts geändert.",
    "admin.outcome.disabled": "Diese Aktualisierung ist in den Einstellungen dieser Installation abgeschaltet.",
    "admin.outcome.cooldown": "Eine Aktualisierung lief gerade. Versuche es in {seconds}s erneut.",
    "admin.probe.action": "Quellen testen",
    "admin.probe.hint": "Ruft beide Quellen ab und prüft, ob die Daten für eine Aktualisierung geeignet sind. Die abgerufenen Daten werden nicht gespeichert.",
    "admin.probe.schedule": "Release-Zeitplan: {answer}",
    "admin.probe.advisories": "Sicherheitsmeldungen: {answer}",
    "admin.probe.usable": 'gelesen; die Daten würden bei einer Aktualisierung übernommen',
    "admin.probe.rejected": 'gelesen; die Daten würden bei der Prüfung abgelehnt',
    "admin.probe.unreadable": "nicht lesbar - nicht erreichbar oder nicht mehr in der erwarteten Form",
    "admin.probe.disabled": "nicht geprüft - diese Aktualisierung ist abgeschaltet",
    "admin.search.kicker": "Suchindex",
    "admin.search.heading": "Status des Suchindexes",
    "admin.search.lede": "Der Suchindex wird beim Build erzeugt. Diese Ansicht vergleicht seine Seiten, Sprachen und Release-Version mit dem laufenden Dienst. Sie vergleicht keine vollständigen Seitentexte und ändert den Index nicht.",
    "admin.search.fresh": "Aktuell",
    "admin.search.stale": "Veraltet",
    "admin.search.unknown": "Nicht feststellbar",
    "admin.search.detail.ok": "Jede Seite und jede Sprache ist für dieses Release indiziert.",
    "admin.search.detail.release": "Erzeugt für {built}, in Betrieb ist {running}.",
    "admin.search.detail.missing": "Nicht indiziert: {list}.",
    "admin.search.detail.extra": (
        "Indiziert, aber nicht mehr ausgeliefert: {list}."
    ),
    "admin.search.detail.unstamped": (
        "Der Index nennt kein Release, für das er gebaut wurde; nur seine "
        "Seiten und Sprachen ließen sich vergleichen."
    ),
    "admin.search.detail.changed": "{count} Seitentitel oder Kurzbeschreibungen haben sich seither geändert.",
    "admin.search.detail.unreadable": "Der Index konnte nicht gelesen werden.",
    "admin.search.remedy": (
        'Veröffentlichte Releases enthalten einen passenden Suchindex. Erzeuge bei einem eigenen Build den Index im Quellcode-Checkout neu und erstelle daraus die Bereitstellung erneut. Du kannst auch ein veröffentlichtes Release installieren:'
    ),
    "admin.search.remedy.commit": (
        "Von Hand muss nichts eingecheckt werden: Jeder Pull Request auf main "
        "erzeugt den Index neu und checkt ihn in seinen Branch ein."
    ),
    "admin.search.fix": "Die Pull-Request- und Release-Workflows erzeugen den Index neu und committen ihn. Auf dieser Seite kannst du ihn nicht neu erstellen.",
    "admin.audit.kicker": "Audit-Log",
    "admin.audit.heading": "Audit-Log",
    "admin.audit.lede": (
        'Verfolge Scan-Anfragen, Ablehnungen und ausgelöste Limits in Echtzeit. Wähle „Live verfolgen“, um die Verbindung zu öffnen und Einträge zu empfangen.'
    ),
    "admin.audit.privacy": "Client-Adressen erscheinen als gekürzte HMAC-Fingerabdrücke. Das dafür verwendete Salt bleibt in diesem Prozess. Diese Ansicht zeigt vorhandene Protokolleinträge und kann daraus keine Client-Adressen ermitteln.",
    "admin.audit.replicas": "Es ist keine Audit-Datei konfiguriert. Diese Einträge stammen aus dem Speicher dieses Prozesses. Bei mehreren Replikaten zeigt die Ansicht nur einen Teil des Audit-Logs.",
    "admin.audit.follow": "Live verfolgen",
    "admin.audit.stop": "Anhalten",
    "admin.audit.clear": "Leeren",
    "admin.audit.empty": "Noch keine Einträge.",
    "admin.audit.closed": (
        'Der Dienst hat die Verbindung nach {minutes} Minuten geschlossen. Wähle „Live verfolgen“, um sie erneut zu öffnen.'
    ),
    "admin.audit.disabled": (
        "Diese Installation führt kein Audit-Log, es gibt also nichts live zu "
        "verfolgen. COS_WEB_AUDIT_LOG schaltet es ein."
    ),
    "admin.audit.state.off": "Nicht aktiv",
    "admin.audit.state.live": "Live",
    "admin.audit.state.reconnecting": "Verbindet neu",
    "admin.audit.state.unsupported": "Von diesem Browser nicht unterstützt",
    "admin.audit.state.closed": "Vom Dienst geschlossen",
    "admin.audit.state.disabled": "Nicht geführt",
    "site.og_image_alt": (
        "OpenCloud Security Scan - eine Instanz auf bekannte Schwachstellen, "
        "fehlende Härtung und schwache Sicherheits-Header prüfen"
    ),
    # ------------------------------------------------------- header chrome
    "chrome.skip_to_content": "Zum Inhalt springen",
    "chrome.brand": "Sicherheitsscan für OpenCloud",
    "chrome.menu": "Menü",
    "chrome.nav.primary": "Primär",
    "chrome.nav.secondary": "Sekundär",
    "chrome.search.label": "Dokumentation durchsuchen",
    "chrome.search.placeholder": "Suchen",
    "chrome.theme.toggle": "Farbschema wechseln",
    "chrome.back_to_top": "Nach oben",
    "nav.new_scan": "Neuer Scan",
    "nav.how_it_works": "So funktioniert es",
    "nav.grades": "Noten",
    "nav.catalogue": "Katalog",
    "nav.docs": "Doku",
    "nav.search": "Suche",
    "nav.compare": "Vergleichen",
    "nav.api": "API",
    "nav.privacy": "Datenschutz",
    "nav.about": "Über",
    # --------------------------------------------------- language switcher
    "lang.region": "Sprache",
    "lang.label": "Seitensprache",
    "lang.apply": "Sprache ändern",
    "lang.note": "Der Scan selbst bleibt unverändert; nur diese Seite wird übersetzt.",
    # ------------------------------------------------------------- footer
    "footer.note.title": "Über diesen Dienst",
    "footer.note.body": "Der Scan läuft von diesem Server aus gegen die eingegebene Adresse. Ergebnisse sind {minutes} Minuten verfügbar und laufen danach ab. Grundlage ist <code>check-opencloud-security</code>; ein Konto ist nicht nötig. Es gibt weder Tracking noch Analysewerkzeuge.",
    "footer.note.run_yourself": "Selbst ausführen",
    "footer.version.title": "Die Scanner-Version, die dieses Ergebnis erzeugt hat",
    "footer.version.label": "Backend v{version}",
    "footer.legal.scope": "<strong>Diese Prüfung ist nicht erschöpfend, und eine gute Note ist kein Zertifikat.</strong> Sie liest die gemeldete Version, passende Sicherheitsmeldungen, TLS, Header und öffentlich sichtbare Einstellungen einschließlich der dokumentierten Demo-Konten. Eine gute Note bedeutet, dass nichts davon fehlgeschlagen ist - nicht, dass die Instanz sicher ist. Private Dateien, Betriebssystem, Backups, Kontoberechtigungen und das umgebende Netzwerk werden nicht untersucht. Nutze den Bericht ergänzend zu deinen übrigen Prüfungen; er ist niemals ein Sicherheitsaudit oder ein Penetrationstest.",
    "footer.legal.trademark": (
        "Dies ist ein unabhängiges Community-Projekt. Es steht in keiner "
        "Verbindung zur OpenCloud GmbH und wird von diesem Unternehmen weder "
        "empfohlen noch unterstützt. &ldquo;OpenCloud&rdquo;, das OpenCloud-Logo "
        "und alle zugehörigen Marken sind Eigentum ihrer jeweiligen Inhaber und "
        "werden hier ausschließlich verwendet, um zu kennzeichnen, welche "
        "Software dieses Werkzeug prüft."
    ),
    # --------------------------------------------------- the contents list
    "toc.heading": "Auf dieser Seite",
    "toc.aria": "Auf dieser Seite",
    "toc.group.act": "Beheben",
    "toc.group.details": "Details",
    "toc.group.keep": "Mitnehmen",
    # --------------------------------------------------------- cross-links
    "pagenav.kicker": "Weiterlesen",
    "pagenav.aria": "Mehr über diesen Dienst",
    "pagenav.how.title": "Wie der Scan funktioniert",
    "pagenav.how.blurb": "Die Prüfungen und die vier Phasen eines Scans.",
    "pagenav.grades.title": "Was die Noten bedeuten",
    "pagenav.grades.blurb": "Was die Noten von A+ bis F bedeuten und wie du eine Bewertung verbessern kannst.",
    "pagenav.catalogue.title": "Was der Scanner prüft",
    "pagenav.catalogue.blurb": (
        "Härtungsmaßnahmen, Header- und TLS-Prüfungen sowie bekannte "
        "Sicherheitslücken – unabhängig von einem einzelnen Scan."
    ),
    "pagenav.docs.title": "CLI-Dokumentation",
    "pagenav.docs.blurb": (
        "Den Scanner von einem Terminal aus installieren, konfigurieren und "
        "automatisieren."
    ),
    "pagenav.api.title": "Scannen per Skript oder Agent",
    "pagenav.api.blurb": (
        "Die JSON-API, die Fair-Use-Grenzen, das OpenAPI-Schema und der "
        "MCP-Endpunkt."
    ),
    "pagenav.privacy.title": "Was dieser Server speichert",
    "pagenav.privacy.blurb": "Welche Daten für {minutes} Minuten im Speicher bleiben und welche Daten protokolliert werden.",
    "pagenav.about.title": "Über OpenCloud",
    "pagenav.about.blurb": (
        "Die Plattform, die hier geprüft wird, und warum dieses Projekt "
        "unabhängig davon ist."
    ),
    "pagenav.cta.title": "Eine Instanz scannen",
    "pagenav.cta.blurb": (
        "Zurück zum Formular. Dauert ein paar Sekunden, keine Anmeldung nötig."
    ),
    # ---------------------------------------------------------------- 404
    "notfound.title": "Seite nicht gefunden",
    "notfound.description": (
        "Die Adresse existiert nicht, oder der Scan, auf den sie zeigte, ist "
        "bereits abgelaufen."
    ),
    "notfound.kicker": "Nicht gefunden",
    "notfound.lede": "Diese Seite existiert nicht oder das Scanergebnis ist abgelaufen. Ergebnisse sind {minutes} Minuten lang abrufbar. Starte einen neuen Scan, um einen aktuellen Bericht zu erhalten.",
    "notfound.action": "Neuen Scan starten",
    # ------------------------------------------------------- landing page
    "index.title": "Eine OpenCloud-Instanz scannen",
    "index.description": "Prüfe eine OpenCloud-Instanz auf bekannte Schwachstellen, fehlende Schutzmaßnahmen, unsichere HTTP-Header und verfügbare Updates. Kostenlos und ohne Anmeldung.",
    "index.eyebrow": "Unabhängig &middot; lokal bereitgestellte Inhalte &middot; befristete Ergebnisse",
    "index.headline": "Wie sicher ist deine <em class=\"swash\">OpenCloud-Instanz</em>?",
    "index.lede": "Gib die Adresse einer OpenCloud-Instanz ein, die du prüfen darfst. Der Scanner untersucht öffentlich zugängliche Einstellungen, HTTP-Header und die Softwareversion. Daraus ergibt sich eine Bewertung von <strong>A+</strong> bis <strong>F</strong>.",
    "index.form.kicker": "Scan-Anfrage",
    "index.form.hint": "Ein paar Sekunden &middot; keine Anmeldung",
    "index.error.self_host": "Entschuldige die Wartezeit. Die Begrenzung hält den Dienst für alle verfügbar. Du kannst den quelloffenen Scanner auch auf deinem eigenen Rechner ausführen, so oft du möchtest:",
    "index.field.label": "Adresse der Instanz",
    "index.field.title": (
        "Die Basisadresse der Instanz: ein Hostname, optionaler Port und "
        "optionaler einfacher Unterordner. Keine Query, kein Fragment, keine "
        "Parameter, keine Escapes und keine Traversierung."
    ),
    "index.field.hint": "Der Hostname genügt; ohne Schema wird <code>https://</code> verwendet. Ein einfacher Unterordner wie <code>/opencloud</code> ist möglich. Querys, Fragmente, Parameter und Pfadwechsel sind nicht erlaubt. Prüfe nur öffentliche Instanzen, für die du eine Berechtigung hast.",
    "index.field.invalid": (
        "Keine gültige Adresse: ein Hostname, optionaler Port und ein einfacher "
        "Unterordner - keine Query, kein Fragment und keine Parameter."
    ),
    "index.submit": "Scan starten",
    "index.submit.busy": "Scan wird gestartet …",
    "index.track.label": "Release-Kanal",
    "index.track.hint": "Bestimmt, ob die Version noch unterstützt wird und welches Update empfohlen wird.",
    "index.format.label": "Anzeigen als",
    "index.format.dashboard": "Ergebnisübersicht",
    "index.format.json": "JSON-Daten",
    "index.format.hint": "Beide stammen aus demselben Scan.",
    "index.waivers.summary": "Bestimmte Prüfungen ignorieren (optional)",
    "index.waivers.selected": "Bestimmte Prüfungen ignorieren ({count} ausgewählt)",
    "index.remember.summary": "Einstellungen deines letzten Scans in diesem Browser: {track} · {format} · {waivers}.",
    "index.remember.waivers.none": 'keine ausgenommenen Prüfungen',
    "index.remember.waivers.one": '1 ausgenommene Prüfung',
    "index.remember.waivers.many": '{count} ausgenommene Prüfungen',
    "index.remember.apply": "Wieder verwenden",
    "index.remember.forget": "Vergessen",
    "index.waivers.hint": "Ausgenommene Befunde bleiben im Bericht sichtbar, senken aber die Bewertung nicht. Ausnahmen gelten nur für fehlgeschlagene Prüfungen.",
    "index.waivers.search.label": "Prüfungen filtern",
    "index.waivers.search.placeholder": "Nach Name suchen...",
    "index.waivers.search.empty": "Keine Prüfung passt zu deiner Suche.",
    "index.assurance.aria": "Wie dieser Dienst mit deinen Daten umgeht",
    "index.assurance.airgapped.title": "Keine externen Seiteninhalte",
    "index.assurance.airgapped.body": "Schriften, Skripte und Bilder stammen von diesem Server. Die Seite verwendet weder CDN noch Analysewerkzeuge.",
    "index.assurance.nostore.title": "Befristete Speicherung",
    "index.assurance.nostore.body": (
        "Das Ergebnis liegt im Speicher und wird in dem Moment verworfen, in dem "
        "es abläuft."
    ),
    "index.assurance.noaccount.title": "Keine Registrierung nötig",
    "index.assurance.noaccount.body": "Starte einen Scan ohne Benutzerkonto und ohne Angabe einer E-Mail-Adresse.",
    "index.assurance.ephemeral.title": "Ergebnislink mit Ablaufzeit",
    "index.assurance.ephemeral.body": (
        "Der Link funktioniert {minutes} Minuten nach dem Scan nicht mehr."
    ),
    # -------------------------------------------- release tracks and waivers
    "track.auto.label": "Automatisch erkennen",
    "track.auto.description": (
        "Den Track aus dem gemeldeten Release der Instanz ableiten."
    ),
    "track.rolling.label": "Rolling",
    "track.rolling.description": "Ungefähr alle drei Wochen ein neues Release.",
    "track.production.label": "Production",
    "track.production.description": (
        "Etwa sechs Monate unterstützt. Die übliche Wahl."
    ),
    "track.lts.label": "LTS",
    "track.lts.description": "Zwei Jahre unterstützt.",
    "waivers.group.hardening": "Härtung",
    "waivers.group.headers": "Header",
    "waivers.group.checks": "Prüfungen",
    # ------------------------------------------------------------ severity
    "severity.critical": "kritisch",
    "severity.high": "hoch",
    "severity.medium": "mittel",
    "severity.low": "niedrig",
    # ------------------------------------------------------------ category
    "category.transport": "Transport & TLS",
    "category.cookies": "Cookies",
    "category.headers": "Sicherheits-Header",
    "category.authentication": "Authentifizierung & Konten",
    "category.sharing": "Freigaben & Links",
    "category.exposure": "Netzwerk-Exposition",
    "category.embedding": "Einbettung",
    "category.lifecycle": "Version & Lebenszyklus",
    "category.proxy": "Identity-Provider & Proxy",
    # --------------------------------------------------------- grade scale
    "grade.5.headline": "Nichts gefunden",
    "grade.5.meaning": (
        "Das Release ist auf seinem Kanal aktuell. Die Datenbank enthält keine "
        "passende Sicherheitsmeldung, und alle durchgeführten Prüfungen wurden "
        "bestanden."
    ),
    "grade.5.improve": "Halte die Instanz auf deinem Release-Kanal aktuell. Wiederhole den Scan nach Änderungen am Reverse Proxy oder an der Anmeldung.",
    "grade.4.headline": "Ein Update wartet",
    "grade.4.meaning": (
        "Für diese Release-Linie gibt es ein neueres Patch-Release. Für die "
        "installierte Version sind keine passenden Sicherheitsmeldungen bekannt."
    ),
    "grade.4.improve": "Installiere das empfohlene Update innerhalb deiner Release-Linie.",
    "grade.3.headline": "Eine Release-Linie zurück",
    "grade.3.meaning": (
        "Die Instanz verwendet eine ältere Release-Linie als die aktuellste "
        "ihres Kanals. Diese ältere Linie wird möglicherweise noch unterstützt."
    ),
    "grade.3.improve": "Aktualisiere auf die empfohlene Release-Linie deines Kanals. Der Bericht nennt das passende Ziel.",
    "grade.2.headline": "Bekannte Schwachstellen in dieser Version",
    "grade.2.meaning": (
        "Für die installierte Version sind Schwachstellen bekannt. Keine davon "
        "hat den Schweregrad hoch oder kritisch."
    ),
    "grade.2.improve": "Installiere die Korrekturversion für deine Release-Linie. Der Bericht berücksichtigt, dass eine Sicherheitsmeldung mehrere getrennt korrigierte Linien betreffen kann.",
    "grade.1.headline": "Schwachstelle mit hohem oder kritischem Schweregrad",
    "grade.1.meaning": "Mindestens eine bekannte Schwachstelle der installierten Version hat den Schweregrad hoch oder kritisch.",
    "grade.1.improve": "Installiere die im Bericht genannte Korrekturversion und prüfe die Hinweise der Sicherheitsmeldung.",
    "grade.0.headline": "Nicht mehr unterstützt",
    "grade.0.meaning": "Diese Versionslinie erhält keine Sicherheitsupdates mehr. Sie erhält die Note F, unabhängig von anderen Befunden oder Ausnahmen.",
    "grade.0.improve": "Wechsle auf eine unterstützte Release-Linie. Der Release-Zeitplan nennt die verfügbaren Kanäle und deren Supportende.",
    # ---------------------------------------------------------- grades page
    "grades.title": "Was die Noten bedeuten",
    "grades.description": (
        "A+, A, C, D, E und F: Was jede Note über eine OpenCloud-Instanz aussagt, "
        "was sie nach unten drückt, und der kürzeste Weg zur nächsthöheren."
    ),
    "grades.kicker": "Die Skala",
    "grades.lede": "Die Bewertung berücksichtigt den Supportstatus der installierten Version, bekannte Schwachstellen und fehlgeschlagene Prüfungen. Hier erfährst du, wie die Ausgangsnote entsteht, welche Befunde sie begrenzen und welche Änderungen sie verbessern.",
    "grades.scale.kicker": "Sechs Stufen",
    "grades.scale.heading": "Die Skala, beste Note zuerst",
    "grades.scale.intro": (
        "Die <strong>0-5</strong>-Skala und ihre Buchstaben sind die, die "
        "<code>scan.nextcloud.com</code> bekannt gemacht hat, bewusst "
        "beibehalten, damit ein bestehender Schwellenwert, ein Graph oder eine "
        "Alarmregel ihre Bedeutung behalten. Das ist auch, warum es kein "
        "<strong>B</strong> gibt: Die Skala überspringt es, und eines hier zu "
        "erfinden würde zwei Zahlen dieselbe Note bedeuten lassen."
    ),
    "grades.row.prefix": "Note {label}: ",
    "grades.row.score": "{rating} von 5",
    "grades.row.improve": "So verbesserst du die Note:",
    "grades.caps.kicker": "Die Obergrenze",
    "grades.caps.heading": "Wie fehlgeschlagene Prüfungen die Note begrenzen",
    "grades.caps.intro": (
        "Die Version bestimmt die Ausgangsnote. Fehlgeschlagene Prüfungen "
        "begrenzen sie abhängig vom Schweregrad. Es gilt die niedrigste "
        "dieser Obergrenzen:"
    ),
    "grades.caps.at_best": "bestenfalls",
    "grades.caps.shared": "Befunde desselben Schweregrads setzen dieselbe Obergrenze. Bei drei mittleren Befunden reicht es daher nicht, nur einen zu beheben. Der Maßnahmenplan zeigt alle drei Schritte und den Punkt, an dem sich die Note verbessert.",
    "grades.caps.rules": "Zwei Regeln haben Vorrang. <strong>Das Supportende bestimmt immer die Note</strong>: Ein nicht mehr unterstütztes Release erhält auch mit Ausnahmen ein <strong>F</strong>. <strong>Ein Release, das neuer ist als der Stand seines angegebenen Kanals, gilt nicht als veraltet</strong>; der Bericht weist darauf hin, dass es diesem Kanal voraus ist.",
    "grades.improve.kicker": "Der kürzeste Weg",
    "grades.improve.heading": "Befunde beheben",
    "grades.improve.intro": "Jeder Bericht enthält die Informationen, die du für die nächsten Schritte brauchst:",
    "grades.improve.plan": "<strong>Ein Maßnahmenplan nach Priorität.</strong> Jeder Schritt beschreibt die nötige Änderung und die erreichbare Note, wenn dieser und alle vorherigen Schritte erledigt sind.",
    "grades.improve.release": "<strong>Eine konkrete Update-Empfehlung.</strong> Der Bericht nennt die Version, die die Schwachstelle <em>in deiner Versionslinie</em> behebt, und berücksichtigt den gewählten Release-Kanal.",
    "grades.improve.explained": (
        "<strong>Erklärungen zu fehlgeschlagenen Prüfungen.</strong> Du erfährst, "
        "was geprüft wurde, warum es relevant ist und wie du den Befund behebst. "
        "Ein Link führt zur passenden Einstellung in der OpenCloud-Dokumentation."
    ),
    "grades.improve.waiver": "<strong>Ausnahmen für bewusst akzeptierte Befunde.</strong> Diese bleiben sichtbar, begrenzen aber die Note nicht mehr. Eine Ausnahme gilt nur für eine fehlgeschlagene Prüfung und ändert nichts an der Bewertung einer nicht mehr unterstützten Version.",
    "grades.improve.rerun": "Prüfe nach den Änderungen mit einem weiteren Scan, welche Befunde behoben sind.",
    "grades.limits.kicker": "Prüfumfang",
    "grades.limits.heading": "Was eine gute Note nicht ist",
    "grades.limits.body": "Ein <strong>A+</strong> bedeutet, dass die für die Note ausgewerteten Prüfungen keinen Fehler ergeben haben. Private Dateien, Betriebssystem, Backups und Kontoberechtigungen sind davon nicht erfasst. Prüfe diese Bereiche gesondert. Unter <a href=\"/how-it-works\">So funktioniert der Scan</a> findest du Umfang und Grenzen.",
    # -------------------------------------------------------------- catalogue
    "catalogue.title": "Was der Scanner prüft",
    "catalogue.description": (
        "Härtungsmaßnahmen, Sicherheits-Header, TLS-Prüfungen und "
        "bekannte Sicherheitslücken, unabhängig von einem einzelnen "
        "Scan-Ergebnis."
    ),
    "catalogue.kicker": "Referenz",
    "catalogue.lede": "Hier findest du die möglichen Prüfungen und die Sicherheitsmeldungen, mit denen der Scanner eine Version abgleicht. Der Katalog beschreibt den Prüfumfang, ohne eine Instanz zu scannen.",
    "catalogue.checks.kicker": "Checks",
    "catalogue.checks.heading": "Jeder Check, nach Kategorie",
    "catalogue.checks.lede": (
        "Gruppiert nach Thema statt nach Schweregrad - der Schweregrad hängt "
        "von der gescannten Instanz ab und wird hier deshalb nicht angezeigt."
    ),
    "catalogue.checks.not_configurable": "nicht konfigurierbar",
    "catalogue.advisories.kicker": "Sicherheitslücken",
    "catalogue.advisories.heading": "Bekannte Sicherheitslücken",
    "catalogue.advisories.lede": (
        "Jede Sicherheitslücke in der Datenbank, gegen die ein Scan bewertet "
        "wird, täglich aus dem öffentlichen Feed aktualisiert."
    ),
    "catalogue.advisories.empty.tag": "Keine bekannt",
    "catalogue.advisories.empty.body": (
        "Die Datenbank der Sicherheitslücken ist derzeit leer."
    ),
    "catalogue.advisories.fixed_in": "Behoben in {version}",
    "catalogue.advisories.unfixed": "Noch keine Korrektur veröffentlicht",
    # -------------------------------------------------- how the scan works
    "how.title": "Wie der Scan funktioniert",
    "how.description": "Was der Scanner auf einer OpenCloud-Instanz prüft und wie aus der Anfrage ein Bericht entsteht.",
    "how.kicker": "Prüfumfang und Ablauf",
    "how.lede": "Der Scanner verbindet sich direkt mit der eingegebenen Adresse und wertet die Antworten selbst aus. Er prüft Informationen, die ohne Benutzerkonto zugänglich sind, und bewertet die installierte Version anhand seiner Release- und Schwachstellendaten.",
    "how.tests.heading": "Was geprüft wird",
    "how.tests.version.title": "Version und Lebenszyklus",
    "how.tests.version.body": "Installierte Version, Supportstatus und passende Sicherheitsmeldungen. Ein nicht mehr unterstütztes Release erhält F.",
    "how.tests.transport.title": "Transport und Header",
    "how.tests.transport.body": (
        "HTTPS-Erreichbarkeit, das Zertifikat und seine verbleibende Laufzeit, "
        "die angebotenen TLS-Versionen und die Sicherheits-Header, die einem "
        "Browser tatsächlich gesendet werden - HSTS, CSP, Frame- und "
        "Content-Type-Schutz."
    ),
    "how.tests.hardening.title": "Schutzmaßnahmen und öffentliche Zugänge",
    "how.tests.hardening.body": "Basic Auth, Passwort- und Ablaufregeln für öffentliche Links, Passwortrichtlinien, Verzeichnisauflistungen, erreichbare interne Endpunkte und veröffentlichte Versionsangaben.",
    "how.pipeline.kicker": "Ablauf",
    "how.pipeline.heading": "Von der Anfrage zum Ergebnis",
    "how.pipeline.lede": "Jeder Scan durchläuft diese vier Schritte.",
    "how.pipeline.step1": "<strong>Die Zieladresse wird geprüft.</strong> Private, lokale und Cloud-Metadaten-Adressen werden vor dem Verbindungsaufbau abgewiesen.",
    "how.pipeline.step2": "<strong>Der Scan erhält eine zufällige Kennung.</strong> Sie ermöglicht den Zugriff auf das Ergebnis. Eine Liste aller Scans gibt es nicht.",
    "how.pipeline.step3": "<strong>Der Scan kommt in die Warteschlange.</strong> Es können nur begrenzt viele Scans gleichzeitig laufen. Sind alle Worker beschäftigt, wartet dein Scan. Die Seite zeigt seine Position in der Warteschlange an.",
    "how.pipeline.step4": "<strong>Das Ergebnis läuft ab.</strong> Nach {minutes} Minuten ist es über seine Kennung nicht mehr abrufbar.",
    "how.faq.kicker": "Fragen",
    "how.faq.heading": "Häufig gestellte Fragen",
    "how.faq.q1": "Ist das die offizielle OpenCloud-Software?",
    "how.faq.a1": (
        "Nein. Dies ist ein unabhängiges Community-Projekt, das in keiner "
        "Verbindung zur OpenCloud GmbH steht und von diesem Unternehmen weder "
        'empfohlen noch unterstützt wird. "OpenCloud" und das zugehörige Logo '
        "sind Marken ihrer jeweiligen Inhaber und werden hier ausschließlich "
        "verwendet, um die geprüfte Software zu benennen."
    ),
    "how.faq.q2": "Bedeutet eine gute Note, dass eine Instanz sicher ist?",
    "how.faq.a2": "Nein. Der Scan prüft die gemeldete Version, passende Sicherheitsmeldungen und von außen sichtbare Einstellungen sowie die veröffentlichten Demo-Zugangsdaten. Private Dateien, Betriebssystem, Backups und Kontoberechtigungen werden nicht untersucht. Der Bericht unterstützt deine Sicherheitsprüfung, ersetzt aber weder Audit noch Penetrationstest.",
    "how.faq.q3": "Wie lange bleibt ein Scan-Ergebnis gespeichert?",
    "how.faq.a3": "Das Ergebnis ist {minutes} Minuten verfügbar und läuft danach ab. Weitere Angaben stehen unter <a href=\"/privacy\">Was dieser Server speichert</a>.",
    "how.faq.q4": "Wie oft kann ich scannen?",
    "how.faq.a4": (
        "Es gelten Limits pro Besucher und Ziel, damit die Warteschlange für "
        "alle verfügbar bleibt und dieselbe Instanz nicht zu oft gescannt wird. "
        "Die genauen Werte für diese Installation stehen "
        '<a href="/api#api-limits">auf der API-Seite</a>.'
    ),
    "how.faq.q5": "Kann ich ohne Ratenlimit scannen?",
    "how.faq.a5": "Ja. Du kannst den quelloffenen Scanner mit <a href=\"/cli\">einem Docker-Befehl</a> auf deinem eigenen Rechner ausführen. Die Limits dieses Webdienstes gelten dort nicht.",
    "how.faq.q6": "Sagt mir ein Scan, ob ein OpenCloud-Update ansteht?",
    "how.faq.a6": "Ja. Die gemeldete Version wird mit den verfügbaren Release-Daten abgeglichen, einschließlich Supportstatus und Release-Kanal. Unter <a href=\"/documentation/reference#update-check\">Update-Prüfung</a> ist beschrieben, wie die Empfehlung entsteht.",
    # --------------------------------------------------------------- privacy
    "privacy.title": "Was dieser Server speichert",
    "privacy.description": (
        "Was während eines Scans gespeichert wird, für wie lange, und was das "
        "Betriebslog aufzeichnet und was nicht."
    ),
    "privacy.kicker": "Datenschutz",
    "privacy.lede": "Scan-Ergebnisse bleiben {minutes} Minuten verfügbar und laufen danach ab.",
    "privacy.retention.kicker": "Speicherdauer",
    "privacy.retention.heading": "Gespeicherte Scandaten",
    "privacy.retention.body": "Zieladresse, gewählte Ausnahmen und Ergebnis werden unter der zufälligen Scan-Kennung für {minutes} Minuten gespeichert. Danach laufen sie ab. Das normale Betriebslog nennt nur diese Kennung und die Ereignisse Erstellung, Start und Abschluss. Client-Adressen werden für die Nutzungsgrenzen nur als Einweg-Fingerabdruck verarbeitet. Ein Betreiber kann zusätzlich ein separates Audit-Log konfigurieren.",
    "privacy.uploads.kicker": "Hochgeladene Berichte",
    "privacy.uploads.heading": "Wenn du einen Bericht zum Vergleich hochlädst",
    "privacy.uploads.body": "Die hochgeladene Datei wird im Arbeitsspeicher für den Vergleich gelesen. Inhalt und Dateiname werden nicht aufbewahrt. Der Vergleich ist über eine zufällige Kennung {minutes} Minuten abrufbar, damit du ihn erneut öffnen oder teilen kannst. Danach läuft er ab und lässt sich ohne die verworfene Datei nicht erneut berechnen.",
    "privacy.self_host": "Für den eigenen Betrieb stehen derselbe Scanner als Kommandozeilenprogramm und die Python-Bibliothek bereit. Der Scan verbindet sich direkt von deinem Rechner mit der Instanz.",
    # ----------------------------------------------------------- legal notice
    "legal.title": "Impressum",
    "legal.description": (
        "Anbieterkennzeichnung, Kontaktdaten und Haftungshinweise des "
        "Betreibers dieser Installation."
    ),
    "legal.kicker": "Impressum",
    "legal.lede": (
        "Anbieterkennzeichnung nach deutschem Recht für den Betreiber dieser "
        "Installation."
    ),
    "legal.english_notice": (
        "Dieses Impressum ist der eigene Rechtstext des Betreibers und liegt "
        "nur auf Englisch vor. Die Seite darum herum ist übersetzt, der Text "
        "darunter nicht."
    ),
    # ----------------------------------------------------------------- about
    "about.title": "Über OpenCloud und diesen Scanner",
    "about.description": (
        "Was OpenCloud ist, wer es entwickelt, und warum dieser Scanner ein "
        "unabhängiges Community-Projekt ist."
    ),
    "about.kicker": "Über",
    "about.lede": "OpenCloud dient zum Speichern, Synchronisieren und Teilen von Dateien. Dieser unabhängige Scanner prüft die Sicherheitseinstellungen, die eine Instanz nach außen erkennen lässt.",
    "about.platform.kicker": "Die Plattform",
    "about.platform.heading": "Über OpenCloud",
    "about.platform.body": "<a href=\"https://opencloud.eu/\" rel=\"noopener noreferrer\">OpenCloud</a> ist eine Open-Source-Plattform zum Speichern, Synchronisieren und Teilen von Dateien. Die Anleitungen zur Administration stehen unter <a href=\"https://docs.opencloud.eu/\" rel=\"noopener noreferrer\">docs.opencloud.eu</a>.",
    "about.platform.independent": (
        "Dieser Scanner ist ein unabhängiges Community-Projekt. Er steht in "
        "keiner Verbindung zur OpenCloud GmbH und wird von diesem Unternehmen "
        "weder empfohlen noch unterstützt. &ldquo;OpenCloud&rdquo;, das "
        "OpenCloud-Logo und alle zugehörigen Marken sind Eigentum ihrer "
        "jeweiligen Inhaber."
    ),
    "about.project.kicker": "Das Projekt",
    "about.project.heading": "Über diesen Scanner",
    "about.project.body": "Die Ergebnisse stammen aus <code>check-opencloud-security</code>, einem Plugin für Nagios und Icinga mit eigener Scanner-Bibliothek. Du kannst es über diese Website oder lokal auf deinem Rechner ohne Ratenbegrenzung und Warteschlange verwenden.",
    "about.project.origin": "<strong>Massoud Ahmed</strong> hat das Projekt entwickelt, um OpenClouds Release-Kanäle, Einstellungen und typische Installationen mit einem lokal ausführbaren Scanner zu prüfen. <a href=\"{project}\" rel=\"noopener noreferrer\">Quellcode und Beiträge findest du auf GitHub</a>.",
    # ------------------------------------------------------------------- API
    "api.title": "Scannen per Skript oder Agent",
    "api.description": (
        "So startest du Scans über die JSON-API und fragst Ergebnisse ab. "
        "Mit Angaben zu Limits, OpenAPI, Arazzo-Workflows und dem MCP-Endpunkt."
    ),
    "api.kicker": "Die API",
    "api.lede": "Über die JSON-API kannst du Scans starten, ihren Fortschritt abfragen und Ergebnisse herunterladen. Für Skripte und Agenten gelten dieselben Prüfungen und Begrenzungen wie für das Formular im Browser.",
    "api.submit.kicker": "Einreichen & abfragen",
    "api.submit.heading": "Einreichen und abfragen",
    "api.submit.body": (
        "Nach dem Start erhältst du <code>202</code> und die Scan-Kennung. "
        "Bei der Statusabfrage bekommst du <code>queued</code>, <code>running</code> "
        "oder das fertige Ergebnis. Abgelaufene Scans liefern <code>404</code>. "
        "Du kannst vier Angaben übergeben: Adresse, ausgenommene Prüfungen, "
        "Release-Kanal und Ausgabeformat. Andere Felder werden abgelehnt. "
        "Parallelität und Zeitlimits legt der Betreiber fest."
    ),
    "api.limits.kicker": "Fair Use",
    "api.limits.heading": "Fair Use",
    "api.limits.enforced": "Diese Installation erlaubt {client} Anfragen je Adresse innerhalb von {window} Minute(n), mit {cooldown}. Bei Überschreitung antwortet sie mit <code>429</code> und einem <code>Retry-After</code>-Header.",
    "api.limits.cooldown": "einer Wartezeit von {minutes} Minute(n) zwischen Scans desselben Ziels",
    "api.limits.no_cooldown": "keiner Wartezeit zwischen Scans desselben Ziels",
    "api.limits.daily": "Höchstens {count} Scans pro Netz am Tag.",
    "api.limits.probe": 'Scans aus einem Netz, dessen Anfragen wiederholt keine OpenCloud-Instanz erreichen, werden vorübergehend gesperrt.',
    "api.limits.none": "Dieses Deployment setzt kein Ratenlimit.",
    "api.limits.self_host": "Du kannst den Scanner auch lokal ausführen und damit unabhängig von diesen Limits nutzen: <a href=\"{project}\" rel=\"noopener noreferrer\">Quellcode auf GitHub</a>.",
    "api.schema.kicker": "Das Schema",
    "api.schema.heading": "Das Schema",
    "api.schema.body": (
        "Die maschinenlesbaren Dokumente sind immer öffentlich, auf diesem "
        'Deployment wie auf jedem anderen: die <a href="/openapi.json">'
        "OpenAPI-3.1-Beschreibung</a> jeder Operation, und die "
        '<a href="/arazzo.json">Arazzo-1.0.1-Workflows</a>, die sagen, wie sich '
        "diese Operationen zum Einreichen eines Scans, Warten darauf und "
        "Abholen des Ergebnisses zusammenfügen."
    ),
    "api.schema.docs_on": "Öffne die API-Dokumentation mit <a href=\"/docs\">Swagger UI</a> oder <a href=\"/redoc\">ReDoc</a>. Beide Ansichten laden ihre Ressourcen von diesem Server, ohne Anfragen an Dritte.",
    "api.schema.docs_off": (
        "Die interaktiven Anzeigen (Swagger UI unter <code>/docs</code>, ReDoc "
        "unter <code>/redoc</code>) sind bei diesem Deployment abgeschaltet; ein "
        "Betreiber schaltet sie mit <code>COS_WEB_ENABLE_DOCS=true</code> ein."
    ),
    # ------------------------------------------------- API, for agents
    "api.agents.kicker": "KI-Agenten",
    "api.agents.heading": "Von einer Adresse aus starten",
    "api.agents.intro": "Agenten finden die API-Funktionen und Scanabläufe in den folgenden öffentlichen Beschreibungen. Dafür ist kein Benutzerkonto nötig.",
    "api.agents.discovery": (
        "<strong>Discovery</strong> - "
        '<a href="/.well-known/ai.json">/.well-known/ai.json</a> nennt alles '
        "Folgende, mit absoluten URLs. Hier starten."
    ),
    "api.agents.openapi": (
        '<strong>OpenAPI</strong> - <a href="/openapi.json">/openapi.json</a>, '
        "jede Operation mit ihren echten Statuscodes und Antwortformen."
    ),
    "api.agents.arazzo": (
        '<strong>Arazzo-Workflows</strong> - <a href="/arazzo.json">'
        "/arazzo.json</a>, der Lebenszyklus eines Scans: einreichen, abfragen, "
        "Abschluss erkennen, exportieren."
    ),
    "api.agents.mcp": (
        "<strong>MCP</strong> - <code>{url}</code>, ein Model-Context-Protocol-"
        "Endpunkt über streambares HTTP. Werkzeuge: <code>scan_instance</code>, "
        "<code>scan_instances</code>, <code>get_scan_result</code>, "
        "<code>plan_remediation</code>, <code>export_scan</code> und "
        "<code>erase_instance_data</code>. <code>scan_instance</code> erledigt "
        "die ganze Aufgabe - Einreichung, Warten und Ergebnis - in einem Aufruf. "
        "Prompts benennen die Aufgaben selbst, etwa "
        "<code>audit_instance</code>, das eine Instanz prüft und den "
        "Sanierungsplan schreibt, und <code>review_transport_security</code>, "
        "das nur das Zertifikat und den Handshake betrachtet. Trage die "
        "MCP-Adresse in deinem Agenten ein. Sie ist keine Webseite, die du "
        "im Browser öffnen kannst."
    ),
    "api.agents.summary": "OpenAPI beschreibt die verfügbaren Operationen, Arazzo deren Ablauf vom Auftrag bis zum Ergebnis. Beide Dokumente werden aus dem Dienstcode erzeugt.",
    "api.agents.summary_mcp": "OpenAPI beschreibt die Operationen, Arazzo die Abläufe und MCP stellt diese Abläufe als Werkzeuge für Agenten bereit. Alle verwenden dieselbe Implementierung des Dienstes.",
    "api.webmcp.kicker": "Im Browser",
    "api.webmcp.heading": "Die Seite als Werkzeug verwenden",
    "api.webmcp.intro": (
        "Ein Browser mit Unterstützung für den "
        '<a href="https://webmachinelearning.github.io/webmcp/" '
        'rel="noopener noreferrer">WebMCP-Entwurf</a> kann Aktionen direkt auf '
        "der geöffneten Seite entdecken. Ein separater Client ist nicht nötig."
    ),
    "api.webmcp.landing": (
        "Auf der Startseite stellt <code>scan_opencloud_security</code> einen Scan "
        "in die Warteschlange. Das Schema enthält die Release-Tracks, "
        "Ausgabeformate und Ausnahmen, die diese Seite anbietet."
    ),
    "api.webmcp.result": (
        "Auf einer Ergebnisseite liest <code>get_scan_result</code> den aktuellen "
        "Scan. <code>export_scan_report</code> lädt JSON, CSV, SARIF oder PDF für "
        "die bereits angezeigte UUID herunter."
    ),
    "api.webmcp.boundary": (
        "Jedes Browser-Werkzeug verwendet dieselbe JSON-API mit "
        "<code>Accept: application/json</code>. SSRF-Schutz, Limits, Ziel-Wartezeit, "
        "Warteschlange und UUID-Isolierung bleiben wirksam."
    ),
    "api.webmcp.support": (
        "WebMCP ist noch ein Entwurf und wird von Browsern ohne Unterstützung "
        "ignoriert. Wird MCP für diese Bereitstellung abgeschaltet, verschwinden "
        "auch die Browser-Werkzeuge."
    ),
    "api.clients.kicker": "Konfiguration",
    "api.clients.heading": "Agent-Client einrichten",
    "api.clients.intro": "Trage im Client die Endpunkt-URL und den Transporttyp Streamable HTTP ein. Falls der Betreiber eine Authentifizierung verlangt, musst du dich außerdem anmelden.",
    "api.clients.body": "Die <a href=\"{project}/blob/main/docs/mcp.md\" rel=\"noopener noreferrer\">MCP-Anleitung</a> enthält Konfigurationen für Claude Code, Claude Desktop, GitHub Copilot, Cursor, Zed und Windsurf, sowohl für diesen Dienst als auch für eigene Installationen.",
    "api.rules.kicker": "Die Regeln",
    "api.rules.heading": "Dieselben Regeln wie für alle anderen",
    "api.rules.body": "Agenten verwenden dieselben Abläufe und Limits. Scans laufen asynchron; ihre UUID ermöglicht den späteren Zugriff. Bei <code>429</code> wartest du die angegebene Frist ab. Für regelmäßige Prüfungen vieler Instanzen kannst du <a href=\"{project}\" rel=\"noopener noreferrer\">den Scanner lokal betreiben</a>.",
    # -------------------------------- Docker one-liners, on /documentation
    "cli.lede": "Führe den Scanner auf deinem eigenen Rechner aus, um den Scan selbst zu kontrollieren und die Begrenzungen dieses Dienstes zu umgehen. Die folgenden Befehle verwenden denselben Scanner wie diese Website.",
    "cli.oneliner.kicker": "Die Einzeiler",
    "cli.oneliner.heading": "Ein Befehl, nichts installiert",
    "cli.oneliner.body": "Der Befehl gibt die Note, den Supportstatus, zutreffende Sicherheitshinweise und fehlgeschlagene Prüfungen aus. Mit dem Nagios-Exitcode lässt er sich in Monitoring, Skripte, CI oder Cronjobs einbinden. Der Scan läuft im Container und verbindet sich direkt mit deiner Instanz.",
    "cli.json.kicker": "Als JSON",
    "cli.json.heading": "Das gesamte Ergebnisdokument",
    "cli.json.body": (
        "Jede Zahl auf einer Ergebnisseite stammt aus diesem Dokument, "
        "einschließlich des <code>addresses</code>-Blocks hinter der Zeile "
        "<strong>Aufgelöst zu</strong> - die IPv4- und IPv6-Adressen, auf die "
        "der Name während des Scans zeigte."
    ),
    "cli.private.kicker": "Internes Netzwerk",
    "cli.private.heading": "Die Instanzen, die diese Website nicht scannt",
    "cli.private.body": "Führe den Kommandozeilen-Scanner auf einem Rechner aus, der deine interne Instanz erreicht. Private Adressen und interne DNS-Namen werden unterstützt. Öffentliche Scandienste beschränken solche Ziele, um Zugriffe in ihre eigenen internen Netze zu verhindern.",
    "cli.nodocker.kicker": "Kein Docker?",
    "cli.nodocker.heading": "Ohne Container",
    "cli.nodocker.body": "Der Scanner ist auch auf PyPI verfügbar. Mit <code>uv</code> führst du ihn bei Bedarf aus; mit <code>pipx</code> installierst du ihn in einer eigenen Python-Umgebung.",
    # ------------------------------------------------ CLI documentation index
    "docs.index.title": "CLI-Dokumentation",
    "docs.index.description": (
        "Die check-opencloud-security-CLI installieren, ausführen und "
        "konfigurieren, mit den vollständigen Betreiberanleitungen an einem Ort "
        "gesammelt."
    ),
    "docs.index.kicker": "Dokumentation",
    "docs.index.heading": "Den Scanner im Terminal verwenden",
    "docs.index.lede": "Installiere den Scanner, führe die erste Prüfung aus und richte regelmäßige Scans ein. Die Anleitungen aus <code>docs/</code> erklären Monitoring, CI, Bereitstellung und die Prüfungen hinter den Befunden.",
    "docs.index.toc.quickstart": "Schnellstart",
    "docs.index.toc.commands": "Befehle",
    "docs.index.toc.options": "Nützliche Optionen",
    "docs.index.toc.configuration": "Konfiguration",
    "docs.index.toc.monitoring": "Monitoring",
    "docs.index.toc.guides": "Vollständige Anleitungen",
    "docs.index.quickstart.kicker": "Schnellstart",
    "docs.index.quickstart.heading": (
        "Eine Prüfung, ohne irgendetwas zu installieren"
    ),
    "docs.index.quickstart.container": "Alternativ verwendest du das veröffentlichte Container-Image. Es führt dasselbe Plugin aus und liefert denselben Nagios-/Icinga-Exitcode:",
    "docs.index.quickstart.note": (
        "Das Plugin spricht direkt mit der Instanz. Es sendet die Adresse weder "
        "an diese Website noch an einen externen Bewertungsdienst."
    ),
    "docs.index.commands.kicker": "Zwei Einstiegspunkte",
    "docs.index.commands.heading": "Das Urteil und das Ergebnisdokument",
    "docs.index.commands.plugin": (
        "Das Monitoring-Plugin: eine Alarmzeile, Performance-Daten und die "
        "Standard-Exit-Codes <strong>OK</strong>, <strong>WARNING</strong>, "
        "<strong>CRITICAL</strong> und <strong>UNKNOWN</strong>."
    ),
    "docs.index.commands.scanner": (
        "Die Scanner-Bibliothek als CLI: das vollständige JSON-Ergebnisdokument "
        "für ein Skript, eine Pipeline oder eine Ad-hoc-Untersuchung."
    ),
    "docs.index.options.kicker": "Häufig verwendete Optionen",
    "docs.index.options.heading": "Nützliche Optionen",
    "docs.index.option.host": (
        "Hostname, IP oder URL; durch Komma getrennt für mehrere Instanzen."
    ),
    "docs.index.option.check_hardening": (
        "Fehlende Härtungsmaßnahmen und Sicherheits-Header einbeziehen."
    ),
    "docs.index.option.release_track": (
        "<code>rolling</code>, <code>production</code>, <code>lts</code> oder "
        "<code>auto</code>."
    ),
    "docs.index.option.ignore_hardening": (
        "Einen Befund akzeptieren, ohne seinen Nachweis zu löschen; "
        "wiederholbar und mit Wildcard-Unterstützung."
    ),
    "docs.index.option.debug": (
        "Ausgangsnote und Auswirkungen der einzelnen Befunde erklären."
    ),
    "docs.index.option.insecure": "Überspringe die Zertifikatsprüfung für eine Instanz, die du selbst verwaltest.",
    "docs.index.option.thresholds": (
        "Die Bewertungsschwellen wählen, die auf Monitoring-Zustände abbilden."
    ),
    "docs.index.option.format": "Ergebnisse im Nagios- oder Prometheus-Format ausgeben.",
    "docs.index.option.baseline": (
        "Nur bei Befunden alarmieren, die neu sind oder sich gegenüber dem "
        "letzten Lauf verschlechtert haben."
    ),
    "docs.index.option.webhook": (
        "Ein anderes System benachrichtigen, wenn der konfigurierte Zustand "
        "erreicht ist."
    ),
    "docs.index.options.manual": (
        "<code>check-opencloud-security --help</code> ist das installierte "
        'Handbuch. Die <a href="{project}#cli-usage" rel="noopener noreferrer">'
        "vollständige Optionstabelle</a> enthält jeden Standardwert und seine "
        "<code>COS_</code>-Umgebungsvariable."
    ),
    "docs.index.configuration.kicker": "Einstellungen",
    "docs.index.configuration.heading": "Konfiguration und Rangfolge",
    "docs.index.configuration.intro": (
        "Einstellungen können aus einer YAML- oder JSON-Datei, der Umgebung "
        "oder der Kommandozeile stammen. Die Reihenfolge ist immer:"
    ),
    "docs.index.precedence.aria": "Konfigurationsrangfolge, höchste zuerst",
    "docs.index.precedence.cli": "CLI-Flag",
    "docs.index.precedence.cli.note": "deine Angabe für diesen Aufruf",
    "docs.index.precedence.env": "Umgebung",
    "docs.index.precedence.env.note": (
        "<code>COS_*</code>, nützlich in Containern und Diensten"
    ),
    "docs.index.precedence.file": "Konfigurationsdatei",
    "docs.index.precedence.file.note": "die dauerhaften Standardwerte des Betreibers",
    "docs.index.precedence.default": "Eingebauter Standardwert",
    "docs.index.precedence.default.note": (
        "gilt, wenn du keinen Wert angibst"
    ),
    "docs.index.configuration.wizard": (
        "Den Assistenten die erste Datei schreiben lassen:"
    ),
    "docs.index.configuration.note": (
        "Eine Datei, die auf <code>.json</code> endet, ist JSON; jede andere "
        "Endung ist YAML. Geheimnisse können in separaten Dateien statt auf der "
        "Kommandozeile liegen."
    ),
    "docs.index.monitoring.kicker": "Regelmäßige Prüfungen",
    "docs.index.monitoring.heading": (
        "Monitoring, Automatisierung und mehrere Instanzen"
    ),
    "docs.index.monitoring.nagios": "<strong>Nagios oder Icinga:</strong> Verwende die Plugin-Ausgabe direkt. Der schwerwiegendste Status, den die konfigurierten Schwellenwerte auslösen, bestimmt den Exit-Code.",
    "docs.index.monitoring.fleet": "<strong>Mehrere Instanzen:</strong> Übergib eine kommagetrennte Liste von Hosts. Verwende für jede Instanz, die andere Einstellungen benötigt, eine eigene Konfigurationsdatei.",
    "docs.index.monitoring.prometheus": "<strong>Prometheus:</strong> Verwende <code>--format=prometheus</code> für einen einmaligen Export oder stelle Metriken mit dem eingebauten Exporter über <code>--prometheus-listen-port</code> bereit.",
    "docs.index.monitoring.ci": (
        "<strong>CI:</strong> denselben Befehl in einer Pipeline ausführen. "
        "Der Exitcode lässt den Job fehlschlagen, wenn die eingestellten "
        "Schwellenwerte überschritten werden. Ein Wrapper ist nicht nötig."
    ),
    "docs.index.monitoring.scheduled": (
        "<strong>Geplante Prüfungen:</strong> systemd, cron, Kubernetes und die "
        "Ansible-Rolle nutzen alle denselben CLI- und Konfigurationsablauf."
    ),
    "docs.index.guides.kicker": "Aus dem Repository",
    "docs.index.guides.heading": "Vollständige Betreiberanleitungen",
    "docs.index.guides.lede": (
        "Jedes Quelldokument hat hier seine eigene HTML-Seite, erzeugt aus dem "
        "Markdown des Repositorys und in der CI auf Abweichungen geprüft."
    ),
    # --------------------------------------------------- generated guide pages
    "docs.guide.kicker": "CLI-Dokumentation",
    "docs.guide.english_notice": "Diese Anleitung gibt es auf Deutsch, Englisch, Französisch und Spanisch. Für deine gewählte Sprache wird die englische Fassung angezeigt.",
    "docs.guide.toc.heading": "Auf dieser Seite",
    "docs.guide.toc.aria": "Auf dieser Seite",
    # ---------------------------------------------------------------- compare
    "compare.title": "Zwei Scans vergleichen",
    "compare.description": (
        "Zwei abgeschlossene Scans derselben Instanz vergleichen und sehen, "
        "was behoben wurde, was neu ist und was weiterhin offen ist."
    ),
    "compare.eyebrow": "Haben die Korrekturen gewirkt?",
    "compare.heading": "Zwei Scans vergleichen",
    "compare.lede": "Gib die UUIDs eines früheren und eines späteren Scans ein. Beide Ergebnisse müssen noch verfügbar sein. Ist der frühere Scan abgelaufen, verwende unten einen heruntergeladenen Bericht.",
    "compare.form.baseline": "Früherer Scan",
    "compare.form.current": "Späterer Scan",
    "compare.form.placeholder": "Die UUID aus der Adresse einer Ergebnisseite",
    "compare.form.submit": "Vergleichen",
    "compare.form.hint": (
        "Die UUID ist der Teil nach <code>/scan/</code> in der Adresse "
        "einer Ergebnisseite. Sie ist die gesamte Berechtigung für dieses "
        "Ergebnis - behandle sie wie ein Passwort."
    ),
    "compare.error.unknown.baseline": (
        "Der frühere Scan ist unbekannt oder abgelaufen. Hier lässt er sich "
        "nicht nachschlagen: Scanne die Instanz erneut und vergleiche die "
        "beiden neuesten Ergebnisse."
    ),
    "compare.error.unknown.current": (
        "Der spätere Scan ist unbekannt oder abgelaufen. Hier lässt er sich "
        "nicht nachschlagen: Scanne die Instanz erneut und vergleiche die "
        "beiden neuesten Ergebnisse."
    ),
    "compare.error.unfinished.baseline": (
        "Der frühere Scan ist noch nicht abgeschlossen. Öffne seine "
        "Ergebnisseite, warte ihn ab und vergleiche erneut."
    ),
    "compare.error.unfinished.current": (
        "Der spätere Scan ist noch nicht abgeschlossen. Öffne seine "
        "Ergebnisseite, warte ihn ab und vergleiche erneut."
    ),
    "compare.error.same": (
        "Beide Felder nennen denselben Scan, es gibt also nichts zu "
        "vergleichen. Scanne die Instanz erneut und vergleiche die neue "
        "UUID mit dieser."
    ),
    "compare.error.different_targets": "Die beiden Scans betreffen unterschiedliche Instanzen und werden deshalb nicht verglichen. Vergleiche zwei Scans derselben Instanz.",
    "compare.verdict.kicker": "Zwischen den beiden Scans",
    "compare.verdict.improved": "Scan-Ergebnis verbessert",
    "compare.verdict.unchanged": "Nichts hat sich geändert",
    "compare.verdict.regressed": "Scan-Ergebnis verschlechtert",
    "compare.rating.up": "Die Note ist um {points} Punkt(e) gestiegen.",
    "compare.rating.down": "Die Note ist um {points} Punkt(e) gefallen.",
    "compare.rating.same": "Die Note ist gleich geblieben. Trotzdem können Befunde behoben worden sein: Mehrere Befunde können dieselbe Bewertungsgrenze setzen. Die Listen unten zeigen die einzelnen Änderungen.",
    "compare.side.baseline": "Früher",
    "compare.side.current": "Später",
    "compare.side.target": "Instanz",
    "compare.side.version": "Version",
    "compare.side.scanned": "Gescannt",
    "compare.side.unknown": "Nicht ermittelt",
    "compare.side.open": "Dieses Ergebnis öffnen",
    "compare.introduced.heading": "Neue Funde ({count})",
    "compare.introduced.none": "Seit dem früheren Scan ist nichts neu.",
    "compare.resolved.heading": "Behobene Funde ({count})",
    "compare.resolved.none": "Keine Befunde aus dem früheren Scan wurden behoben.",
    "compare.unchanged.heading": "Weiterhin offen ({count})",
    "compare.unchanged.none": "In beiden Scans ist nichts offen.",
    "compare.changes.heading": "Was der Vergleich einzeln aufführt",
    "compare.changes.category": "Kategorie",
    "compare.changes.change": "Änderung",
    "compare.nothing_stored": "Dieser Vergleich wird bei jedem Aufruf der Seite aus den beiden Ergebnissen berechnet. Er wird nicht separat gespeichert und ist nicht mehr verfügbar, sobald eines der Ergebnisse abläuft.",
    # ----------------------------------------------------------------- search
    # ------------------------------------------- Vergleich mit einer Datei
    "compare.upload.kicker": "Schon einen Bericht zur Hand?",
    "compare.upload.heading": "Einen früheren Bericht mit einem Scan vergleichen",
    "compare.upload.lede": (
        "Lade einen früher heruntergeladenen Bericht hoch - JSON oder CSV - "
        "und vergleiche ihn mit einem Scan dieses Dienstes. Nützlich, wenn "
        "der frühere Scan längst abgelaufen ist, die Datei aber noch da "
        "ist."
    ),
    "compare.upload.field.report": "Früherer Bericht",
    "compare.upload.field.current": "Späterer Scan",
    "compare.upload.field.hint": (
        "Die Datei <code>.json</code> oder <code>.csv</code> aus den Downloads "
        "einer Ergebnisseite. Bis zu {kilobytes} KB."
    ),
    "compare.upload.submit": "Mit dieser Datei vergleichen",
    "compare.upload.privacy": (
        "Die Datei wird einmal im Arbeitsspeicher gelesen, um den Vergleich zu "
        "berechnen, und weder auf die Festplatte geschrieben noch aufbewahrt. "
        "Der Vergleich selbst wird {minutes} Minuten vorgehalten, damit diese "
        "Seite neu geladen werden kann, und ist danach ebenfalls weg."
    ),
    "compare.upload.source.kicker": "Quelle des früheren Berichts",
    "compare.upload.source.json": (
        'Das frühere Ergebnis stammt aus einem hochgeladenen JSON-Bericht. Es hat hier keine eigene Ergebnisseite; die Datei wurde gelesen und verworfen.'
    ),
    "compare.upload.source.csv": (
        'Das frühere Ergebnis stammt aus einem hochgeladenen CSV-Bericht. Es hat hier keine eigene Ergebnisseite; die Datei wurde gelesen und verworfen.'
    ),
    "compare.upload.source.dropped": "Einträge mit unbekannten Befundkennungen, die vom Vergleich ausgeschlossen wurden: {count}.",
    "compare.upload.source.missing.httpsEnforced": (
        "Die hochgeladene Datei hält nicht fest, ob HTTPS erzwungen wurde. Diese "
        "Maßnahme blieb deshalb auf beiden Seiten außen vor, statt geraten zu "
        "werden. Eine CSV-Datei von vor dieser Neuerung ist so eine Datei."
    ),
    "compare.upload.source.missing.update": (
        "Die hochgeladene Datei hält nicht fest, ob ein Update ausstand. "
        "Ausstehende Updates blieben deshalb auf beiden Seiten außen vor, statt "
        "geraten zu werden. Eine CSV-Datei von vor dieser Neuerung ist so eine "
        "Datei."
    ),
    "compare.upload.expires": "Dieser Vergleich ist noch etwa {minutes} Minuten abrufbar. Danach brauchst du die ursprüngliche Datei für einen neuen Vergleich.",
    "compare.upload.error.missing": (
        "Es wurde kein Bericht hochgeladen. Wähle einen JSON- oder CSV-Bericht, den du von einer Ergebnisseite heruntergeladen hast."
    ),
    "compare.upload.error.no_current": "Gib die UUID des Scans an, mit dem du den hochgeladenen Bericht vergleichen möchtest.",
    "compare.upload.error.empty": "Die hochgeladene Datei ist leer. Wähle einen heruntergeladenen JSON- oder CSV-Bericht.",
    "compare.upload.error.too_large": "Die Datei überschreitet die erlaubte Größe von {kilobytes} KB.",
    "compare.upload.error.unreadable": (
        "Diese Datei ließ sich weder als JSON noch als CSV lesen. Lade die "
        "Datei genau so hoch, wie sie heruntergeladen wurde, ohne sie zu "
        "öffnen und neu zu speichern."
    ),
    "compare.upload.error.not_a_report": (
        "Diese Datei wurde nicht als Scanbericht erkannt. Verwende einen JSON- oder CSV-Download von einer Ergebnisseite."
    ),
    "compare.upload.error.rate_limit": (
        "Das sind viele Berichte aus deinem Netz in kurzer Zeit. Warte eine "
        "Minute und versuche es erneut."
    ),
    "compare.upload.error.blocked": (
        "Mehrere zuletzt aus deinem Netz angefragte Ziele waren keine "
        "erreichbaren OpenCloud-Instanzen. Dieser Dienst legt deshalb eine "
        "Pause ein - auch für Uploads. Der Scanner und sein Vergleich laufen "
        "ohne jede Begrenzung auch auf deinem eigenen Rechner."
    ),
    "compare.upload.error.expired": (
        "Dieser Vergleich ist abgelaufen. Vergleiche aus einer "
        "hochgeladenen Datei werden nur {minutes} Minuten vorgehalten, und "
        "die Datei selbst wurde nie aufbewahrt - lade sie erneut hoch, um "
        "dieselbe Frage zu stellen."
    ),
    "search.title": "Suche",
    "search.description": (
        "Die Scanner-Dokumentation und öffentliche Anleitungen durchsuchen. "
        "Scan-Ergebnisse werden nie indexiert."
    ),
    "search.eyebrow": "Statischer Release-Index",
    "search.heading": "Den Scanner durchsuchen",
    "search.lede": (
        "Nur Dokumentation und öffentliche Anleitungen. Der Index wird für "
        "Releases neu aufgebaut; er liest nie den Scan-Speicher, "
        "Ergebnisseiten, UUIDs oder übermittelte Adressen."
    ),
    "search.label": "Dokumentation durchsuchen",
    "search.placeholder": 'TLS, Docker, Ausnahmen...',
    "search.submit": "Suchen",
    "search.scope.operator": "Betriebsbereich",
    "search.status.idle": "Gib einen Suchbegriff ein.",
    "search.status.results": "{count} Ergebnis(se) in diesem Release.",
    "search.status.empty": "Keine öffentliche Dokumentation passte zu dieser Suche.",
    "search.status.error": "Die Suche ist vorübergehend nicht verfügbar.",
    # The search manifest: the title and summary an index entry carries, as
    # opposed to the words on the page itself.
    "search.page.index.title": "Eine OpenCloud-Instanz scannen",
    "search.page.index.summary": (
        "Einen öffentlichen Sicherheitsscan für eine OpenCloud-Instanz "
        "ausführen."
    ),
    "search.page.how.title": "Wie der Scanner funktioniert",
    "search.page.how.summary": (
        "Was der Scanner misst, was er nicht sehen kann, und wie mit "
        "Ergebnissen umgegangen wird."
    ),
    "search.page.grades.title": "Was die Noten bedeuten",
    "search.page.grades.summary": (
        "Die Bewertungsskala von A+ bis F und die Fixes, die jede Note "
        "verbessern."
    ),
    "search.page.catalogue.title": "Was der Scanner prüft",
    "search.page.catalogue.summary": (
        "Jedes Härtungsmerkmal, jeden Header- und TLS-Check des Scanners, und "
        "jede bekannte Sicherheitslücke."
    ),
    "search.page.documentation.title": "CLI-Dokumentation",
    "search.page.documentation.summary": (
        "Kommandozeilen-Schnellstart, Konfiguration, Monitoring und "
        "Deployment-Anleitungen."
    ),
    "search.page.api.title": "API",
    "search.page.api.summary": (
        "Scans einreichen, Ergebnisse abfragen, Berichte exportieren und den "
        "Dienst per OpenAPI, Arazzo oder MCP aus einem Agenten heraus steuern."
    ),
    "search.page.privacy.title": "Datenschutz",
    "search.page.privacy.summary": (
        "Aufbewahrung von Ergebnissen, Anfrageprotokollierung, Ratenlimits und "
        "Drittanbieter-Richtlinie."
    ),
    "search.page.about.title": "Über dieses Projekt",
    "search.page.about.summary": (
        "Warum dieser unabhängige OpenCloud-Sicherheitsscanner existiert."
    ),
    # ------------------------------------------- what a submission is refused for
    # The API answers the English sentence these translate; a browser reads
    # the translation. The SSRF guard names the identifier, this names the
    # sentence, and neither is derived from the other.
    "error.unsupported_fields": (
        "Dieser Dienst akzeptiert {fields} nicht. Der Scan läuft ausschließlich "
        "mit serverseitigen Einstellungen."
    ),
    "error.rate_limit.client": "Aus deinem Netzwerk wurden in kurzer Zeit viele Scans angefragt. Bitte warte eine Minute und versuche es erneut.",
    "error.rate_limit.probe": "Mehrere zuletzt angefragte Ziele waren keine erreichbaren OpenCloud-Instanzen. Weitere Scans aus deinem Netzwerk sind vorübergehend gesperrt. Für deine eigene Instanz kannst du den Scanner auch lokal ausführen.",
    "error.rate_limit.daily": "Leider ist das heutige Scan-Limit für dein Netzwerk erreicht. Versuche es morgen erneut oder führe den Scanner auf deinem Rechner ohne dieses Tageslimit aus.",
    "error.target.wildcard_dns": "Dieser Name gehört zu einem Wildcard-DNS-Dienst. Gib den eigenen Hostnamen oder die IP-Adresse der Instanz ein.",
    "error.target.unstable": (
        "Dieser Hostname liefert bei jeder Abfrage andere Adressen, daher kann "
        "dieser Dienst nicht verlässlich bestimmen, was er scannen würde."
    ),
    "error.target.not_approved": (
        "Dieser Dienst scannt nur freigegebene Instanzen. Bitte den Betreiber um die Freigabe dieser Instanz oder veröffentliche den dafür erforderlichen DNS-Eintrag."
    ),
    "error.rate_limit.target": "Diese Instanz wurde kürzlich gescannt. Bitte warte einige Minuten.",
    "error.target.invalid": "Diese Adresse kann nicht gescannt werden.",
    "error.target.empty": "Gib die Adresse der OpenCloud-Instanz ein.",
    "error.target.too_long": "Diese Adresse ist zu lang.",
    "error.target.characters": (
        "Diese Adresse enthält Zeichen, die ein Hostname nicht haben kann."
    ),
    "error.target.unparsed": "Diese Adresse konnte nicht gelesen werden. Prüfe sie und gib die Basis-URL der Instanz ein.",
    "error.target.scheme": (
        "Nur http://- und https://-Ziele können gescannt werden."
    ),
    "error.target.credentials": (
        "Zugangsdaten in der Adresse werden nicht akzeptiert."
    ),
    "error.target.address_only": "Gib nur die Basisadresse der Instanz ein, bei Bedarf mit einfachem Unterordner. Querys, Fragmente, Parameter und Pfadwechsel sind nicht erlaubt.",
    "error.target.port": "Diese Adresse hat einen ungültigen Port.",
    "error.target.no_host": "Diese Adresse hat keinen Hostnamen.",
    "error.target.hostname_shape": (
        "Das ist kein Hostname, den dieser Dienst scannen kann."
    ),
    "error.target.unresolved": "Für diesen Hostnamen wurde keine IP-Adresse gefunden. Prüfe die Schreibweise und die DNS-Konfiguration.",
    "error.target.hostname_long": "Dieser Hostname ist zu lang.",
    "error.target.internal": (
        "Lokale und interne Adressen können nicht gescannt werden."
    ),
    "error.target.private": (
        "Diese Adresse zeigt in ein privates, lokales oder link-lokales "
        "Netzwerk, das dieser Dienst nicht scannt."
    ),
    "error.target.blocked": (
        "Der Betreiber hat diese Adresse von Scans ausgeschlossen."
    ),
    "error.store_unavailable": (
        "Der Dienst kann seine Liste ausgeschlossener Ziele nicht lesen und deshalb keinen Scan sicher starten. Bitte versuche es in einigen Minuten erneut."
    ),
    # ----------------------------------------------------------- result page
    "result.title": "Scan-Ergebnisse",
    "result.description": (
        "Das Ergebnis eines öffentlichen Scans, lesbar nur mit seiner eigenen "
        "Kennung."
    ),
    "result.kicker": "Sicherheitsprüfung",
    "result.heading": "Scan-Ergebnis",
    "result.track.title": (
        "Der Release-Track, gegen den dieser Scan bewertet wurde"
    ),
    "result.track.label": "{track}-Track",
    "result.another": "Eine weitere Instanz scannen",
    "result.compare": "Mit einem früheren Scan vergleichen",
    "result.tab.queued": "In der Warteschlange: {target}",
    "result.tab.queued.position": "Platz {position}: {target}",
    "result.tab.running": "Wird gescannt: {target}",
    "result.tab.ready": "Bericht fertig: {target}",
    "result.tab.done": "Note {label}: {target}",
    "result.tab.failed": "Scan fehlgeschlagen: {target}",
    "index.cooldown.opening": 'Dein vorheriges Ergebnis für diese Instanz wird geöffnet …',
    "result.earlier.note": (
        'Das ist dein vorheriges Ergebnis für diese Instanz. Die Instanz wurde gerade erst gescannt und kann noch nicht erneut gescannt werden; der Countdown unten zeigt, wann ein neuer Scan möglich ist.'
    ),
    "result.compare.offer": "In diesem Tab wurde diese Instanz bereits um {time} gescannt.",
    "result.compare.offer.link": "Sehen, was sich seitdem geändert hat",
    "result.progress.kicker": "In Bearbeitung",
    "result.progress.queued.title": "Wartet auf den Start des Scans",
    "result.progress.queued.detail": "Alle Scan-Prozesse sind beschäftigt. Dein Scan behält seinen Platz in der Warteschlange und startet, sobald ein Prozess frei wird.",
    "result.progress.running.title": "Die Instanz wird gescannt",
    "result.progress.running.detail": "Der Scanner prüft Version, Funktionen, Zertifikat, Header und Endpunkte, die die Instanz ohne Anmeldung bereitstellt.",
    "result.progress.step.queued": "In Warteschlange",
    "result.progress.step.running": "Läuft",
    "result.progress.step.done": "Ergebnis",
    "result.progress.estimate": "Die meisten Scans sind in unter einer Minute fertig.",
    "result.progress.elapsed": "Vergangene Zeit: {duration}",
    "result.progress.noscript": "JavaScript aktualisiert diese Seite automatisch. Falls JavaScript nicht verfügbar ist, lade die Seite nach einigen Sekunden neu, um das Ergebnis zu sehen.",
    "result.progress.queue.position": (
        "Scan in Warteschlange. Position in der Reihe: #{position} von "
        "{length}."
    ),
    "result.progress.queue.next": "Dein Scan ist als Nächstes in der Warteschlange an der Reihe.",
    "result.progress.queue.waiting": (
        "Wartet auf einen freien Scan-Prozess."
    ),
    "result.progress.done.title": "Bericht fertig",
    "result.progress.done.detail": "Der Scan ist abgeschlossen. Der Bericht wird geöffnet.",
    "result.progress.failed.title": "Scan beendet",
    "result.progress.failed.detail": (
        "Der Scan konnte nicht abgeschlossen werden. Die Ergebnisseite mit den Fehlerdetails wird geöffnet."
    ),
    "result.failed.fallback": "Der Scan konnte nicht abgeschlossen werden.",
    "result.failed.body": "Der Scanner konnte nicht genügend Informationen für eine Bewertung abrufen. Prüfe die Adresse und stelle sicher, dass dort OpenCloud läuft und die Instanz von diesem Dienst aus erreichbar ist.",
    "result.document.kicker": "Ergebnisdokument",
    "result.document.heading": "Ergebnisdokument",
    "result.document.lede": (
        "Dasselbe Dokument, das das Kommandozeilen-Tool und das Nagios-Plugin "
        "auswerten."
    ),
    "result.verdict.kicker": "Urteil",
    "result.verdict.heading": "Gesamtbewertung",
    "result.verdict.dial": "Note {label}, {rating} von 5",
    "result.facts.instance": "Instanz",
    "result.facts.resolved": "Aufgelöste Adressen",
    "result.facts.ipv6.heading": "IPv6-Erreichbarkeit",
    "result.facts.ipv6.note": (
        "Nicht geprüft - dieses Deployment hat keine ausgehende IPv6-"
        "Verbindung, daher wird dies nur vermerkt und nicht gegen die "
        "Instanz gewertet."
    ),
    "result.facts.product": "Produkt",
    "result.facts.track": "Release-Track",
    "result.facts.track.unknown": "unbekannt",
    "result.facts.eol_tag": "End of Life",
    "result.facts.schedule": "Release-Zeitplan",
    "result.facts.schedule.stale": (
        "{version} ist neuer als diese Kopie des OpenCloud-Release-Zeitplans, "
        "der Zeitplan ist also wahrscheinlich veraltet. Es wird der Instanz "
        "nicht angelastet -"
    ),
    "result.facts.schedule.stale_generated": (
        "{version} ist neuer als diese Kopie des OpenCloud-Release-Zeitplans, "
        "erzeugt am {generated}, der Zeitplan ist also wahrscheinlich veraltet. "
        "Es wird der Instanz nicht angelastet -"
    ),
    "result.facts.schedule.link": "öffne den veröffentlichten Release-Lebenszyklus",
    "result.facts.signin": "Anmeldung",
    "result.facts.signin.external": "Externer Anbieter",
    "result.facts.signin.upstream_tag": "vorgelagert",
    "result.facts.signin.version_unavailable": "Version nicht offengelegt",
    "result.facts.signin.advisories": "Sicherheitshinweise prüfen",
    "result.facts.signin.builtin": "Eingebauter Identity-Provider",
    "result.facts.signin.none": "Nicht erkannt -",
    "result.facts.signin.link": "wie die OpenCloud-Anmeldung eingerichtet wird",
    "result.facts.proxy": "Reverse Proxy",
    "result.facts.proxy.detected": "Erkannt",
    "result.facts.http3": "HTTP/3",
    "result.facts.http3.value": "Über UDP {ports} angekündigt - prüfe, ob deine Firewall diesen Verkehr bewusst zulässt (nicht bewertet)",
    "result.facts.http3.noport": "Über UDP angekündigt - prüfe, ob deine Firewall diesen Verkehr bewusst zulässt (nicht bewertet)",
    "result.facts.upgrade_path": "Update-Pfad",
    "result.facts.upgrade_path.complete": '{target} behebt alle bekannten Schwachstellen',
    "result.facts.upgrade_path.partial": '{target} lässt {open} Schwachstellen offen; {safe} ist die erste Version, die alle behebt',
    "result.facts.upgrade_path.unfixed": '{target} lässt {open} Schwachstellen offen; noch keine veröffentlichte Version behebt sie alle',
    "result.facts.office": "Office",
    "result.facts.calendar": "Kalender",
    "result.facts.calendar.detected": "Ein Dienst antwortet am CalDAV-Pfad",
    "result.facts.newest": "Neuestes Release",
    "result.facts.score": "Punktzahl",
    "result.facts.score.value": "{rating} von 5",
    "result.counter.critical": "Kritisch",
    "result.counter.warning": "Warnung",
    "result.counter.info": "Info",
    "result.counter.advisories": "Advisories",
    "result.counter.passed": "Bestanden",
    "result.verdict.why": "Warum diese Note:",
    "result.verdict.caveat": (
        "Die Note fasst die unten stehenden Prüfungen zusammen. Sie bestätigt "
        "nicht, dass die Instanz sicher ist: Der Scan sieht nur, was sie "
        "ohne Anmeldung zugänglich macht. "
        '<a href="#scan-limits">Was er nicht sehen kann</a>.'
    ),
    "result.fix": "Behebung:",
    "result.documentation": "Dokumentation",
    "result.explain.title": "Was diese Prüfung bedeutet",
    "result.plan.kicker": "Maßnahmenplan",
    "result.plan.heading": "Schritte zur Note {label}",
    "result.plan.heading.held": "Noch zu beheben, die Note bleibt {label}",
    "result.plan.then": "dann {label}",
    "result.plan.still": "immer noch {label}",
    "result.plan.note": "Der Plan priorisiert Änderungen, die die Bewertung verbessern. Die Note neben einem Schritt setzt voraus, dass dieser und alle vorherigen Schritte erledigt sind. Befunde gleicher Schwere begrenzen die Note gemeinsam. Deshalb können mehrere Korrekturen nötig sein, bevor sie steigt.",
    "result.plan.blocked.heading": (
        "Begrenzt die Note und lässt sich nicht konfigurieren"
    ),
    "result.plan.blocked.note": (
        "Diese Werte sind im OpenCloud-Code festgelegt. Du kannst sie nicht "
        "über die Konfiguration ändern. Deshalb kann der Maßnahmenplan "
        "keine bessere Note erreichen."
    ),
    "result.groups.kicker": "Nach Konfiguration gruppiert",
    "result.groups.heading": "Was du wo ändern musst",
    "result.groups.lede": "Dieselben offenen Befunde, gruppiert nach dem System, das du zur Behebung bearbeitest – auch Befunde, die die Note nicht beeinflussen. Oft behebt eine Änderung mehrere Befunde.",
    "result.groups.target.reverseProxy": "Reverse Proxy",
    "result.groups.target.identityProvider": "Identitätsanbieter",
    "result.groups.target.opencloud": "OpenCloud",
    "result.groups.target.dnsZone": "DNS-Zone",
    "result.groups.count": "{count} offene Befunde, {label} mit allen Änderungen hier",
    "result.groups.resolves": "Behebt {count} Befunde auf einmal",
    "result.groups.alone": "nur diese Änderung: {label}",
    "result.rehearsal.kicker": "Upgrade-Simulation",
    "result.rehearsal.heading": "Was ein Upgrade beheben würde",
    "result.rehearsal.lede": (
        "Jede sinnvolle Zielversion wird bewertet, bevor sie jemand installiert. "
        "Ein Upgrade ändert die Version, nicht den Reverse Proxy. Die Befunde "
        "auf dieser Seite bleiben daher unverändert."
    ),
    "result.rehearsal.line": "Versionslinie {line}",
    "result.rehearsal.recommended": "empfohlen",
    "result.rehearsal.eol": "Ende des Supports",
    "result.rehearsal.grade": "erreicht {label}",
    "result.rehearsal.fixes": "Behebt",
    "result.rehearsal.still": "Weiterhin betroffen:",
    "result.rehearsal.introduces": "Neu betroffen:",
    "result.rehearsal.clean": 'Behebt alle bekannten Schwachstellen dieser Version.',
    "result.rehearsal.nothing": 'Behebt keine der bekannten Schwachstellen dieser Version.',
    "result.rehearsal.capped": (
        "Die Version allein würde {label} erreichen; die Befunde auf dieser "
        "Seite halten die Bewertung auf ihrem aktuellen Stand."
    ),
    "result.rehearsal.note": (
        'Diese Simulation nutzt nur den Release-Zeitplan und die Schwachstellendatenbank, die diesem Scan vorlagen. Später veröffentlichte Versionen oder Sicherheitsmeldungen sind nicht enthalten.'
    ),
    "result.eol.alert": (
        "Dieses Release erhält keine Sicherheitsfixes mehr. Nichts anderes auf "
        "dieser Seite kann die Note anheben, bis es aktualisiert wird."
    ),
    "result.advisories.kicker": "Advisories",
    "result.advisories.heading": "Bekannte Advisories für diese Version",
    "result.advisories.lede": (
        "Veröffentlichte Advisories, deren betroffener Bereich {version} "
        "einschließt."
    ),
    "result.advisories.fallback_id": "Advisory",
    "result.advisories.unrated": "unbewertet",
    "result.advisories.no_summary": "Keine Zusammenfassung veröffentlicht.",
    "result.advisories.read": "Die Advisory lesen",
    "result.findings.kicker": "Befunde",
    "result.findings.heading": "Fehlgeschlagene Prüfungen",
    "result.findings.lede": (
        "Jeder Befund begrenzt die Note abhängig von seinem Schweregrad. "
        "Behebe zuerst die kritischen Befunde, da sie die Bewertung am "
        "stärksten verschlechtern."
    ),
    "result.findings.filter.aria": "Befunde nach Schweregrad filtern",
    "result.findings.filter.active": "Zeigt nur Befunde mit Schweregrad {severity}.",
    "result.findings.filter.clear": "Alle Befunde anzeigen",
    "result.findings.allclear.tag": "Alles klar",
    "result.findings.allclear.body": (
        "Jede Prüfung, die dieser Scanner durchführt, wurde auf dieser Instanz "
        "bestanden."
    ),
    "result.hardening.kicker": "Härtung",
    "result.hardening.heading": "Fehlende Härtungsmaßnahmen",
    "result.hardening.lede": "Diese Einstellungen bieten zusätzlichen Schutz vor typischen Risiken. Prüfe zu jedem Befund die Erklärung und den vorgeschlagenen Lösungsweg.",
    "result.hardening.tag": "Härtung",
    "result.header.tag": "Header",
    # ------------------------------------------------- configuration fragment
    "result.fragment.kicker": "Konfigurationsvorlage",
    "result.fragment.heading": "In die Konfiguration einfügen",
    "result.fragment.lede": (
        "Die Befunde von oben, in der Syntax der Datei, die geändert werden "
        "muss. Wähle, wo deine Instanz konfiguriert wird."
    ),
    "result.fragment.caution": (
        "Lies vor dem Einfügen die Zeile „Behebung“ jedes Befundes. Dies "
        "sind die Werte, nach denen die Prüfungen suchen, keine Bewertung "
        "dessen, was deine Installation braucht."
    ),
    "result.fragment.picker": "Konfigurationsformat",
    "result.fragment.file": "Gehört in {name}.",
    "result.fragment.copy": "Kopieren",
    "result.fragment.copied": "Kopiert",
    "result.fragment.copy_failed": "Kopieren fehlgeschlagen",
    "result.fragment.nothing": "Kein offener Befund lässt sich in diesem Format beheben. Die passenden Einstellungen findest du unter {flavours}.",
    "result.fragment.elsewhere": (
        "Diese werden woanders behoben - sie gehören nach {flavours}:"
    ),
    "result.fragment.undecided": "Bei diesen Befunden hängt der passende Wert von deiner Installation ab. Folge den Hinweisen zur Behebung des jeweiligen Befunds.",
    # ------------------------------------------------------------ scan again
    "result.rescan": "Erneut scannen",
    "result.rescan.ready": "Diese Instanz kann erneut gescannt werden.",
    "result.rescan.wait": "Erneut scannen möglich in {countdown}.",
    "result.rescan.note": "Der nächste Scan verwendet dasselbe Ziel, dieselben Ausnahmen und denselben Release-Kanal, damit die Ergebnisse vergleichbar bleiben. Warte bitte die Pause ab oder nutze den quelloffenen Scanner ohne Begrenzung auf deinem Rechner:",
    "result.rescan.self_host": "selbst betreiben",
    "result.excluded.kicker": "Ausgeschlossen",
    "result.fingerprint.kicker": "Konfiguration",
    "result.fingerprint.heading": "Hat sich diese Installation geändert?",
    "result.fingerprint.body": (
        "Jede Gruppe enthält einen Hash der gemessenen Konfiguration, ohne "
        "deren Werte offenzulegen. Vergleiche Hashes aus Scans mit gleichem "
        "Messumfang, um Konfigurationsänderungen zu erkennen, auch wenn die "
        "Note gleich bleibt."
    ),
    "result.fingerprint.overall": "Über alle Gruppen: {digest}",
    "result.fingerprint.unmeasured": "In diesem Scan nicht gemessen",
    "result.fingerprint.unavailable": "Dieser Bericht enthält keinen Konfigurationsfingerabdruck. Ob sich die Installation geändert hat, lässt sich damit nicht feststellen.",
    "fingerprint.group.tls": "Transportsicherheit",
    "fingerprint.group.headers": "Sicherheits-Header",
    "fingerprint.group.sharing": "Freigaben",
    "fingerprint.group.authentication": "Anmeldung",
    "fingerprint.group.proxy": "Proxy und Auslieferung",
    "result.coverage.kicker": "Abdeckung",
    "result.coverage.heading": "Was dieser Scan nicht gemessen hat",
    "result.coverage.note": (
        "Eine Note beschreibt, was dieser Scan festgestellt hat. Diese "
        "Prüfungen kamen zu keinem Ergebnis; über sie sagt die Note also "
        "nichts aus."
    ),
    "result.coverage.summary": (
        "{measured} von {total} Prüfungen kamen zu einem Ergebnis."
    ),
    "result.coverage.breakdown": (
        "{evaluated} Prüfungen ausgewertet, {skipped} übersprungen, "
        "{indeterminate} unentschieden, {networkLimited} netzwerkbedingt offen."
    ),
    "result.coverage.complete": (
        "Jede Prüfung, die dieser Scan vorgesehen hat, kam zu einem Ergebnis."
    ),
    "result.coverage.unavailable": "Dieser ältere Bericht enthält keine Angaben zu den ausgeführten Prüfungen. Der Prüfumfang ist unbekannt.",
    "coverage.reason.not_applicable": "Trifft auf diese Instanz nicht zu",
    "coverage.reason.probe_disabled": "Die Prüfung war für diesen Scan abgeschaltet",
    "coverage.reason.prerequisite_missing": "Die Instanz hat die für diese Prüfung benötigten Informationen nicht bereitgestellt",
    "coverage.reason.timeout": "Nichts hat rechtzeitig geantwortet",
    "coverage.reason.unreadable": "Die Antwort war nicht lesbar",
    "coverage.reason.no_route": "Dieser Scanner hat keine Route zu dieser Adresse",
    "coverage.group.hardening": "Härtungseinstellungen",
    "coverage.group.header": "Sicherheits-Header",
    "coverage.group.advisoryHeader": "Empfohlene Header",
    "coverage.group.advisoryCheck": "Empfohlene Beobachtungen",
    "coverage.group.extraCheck": "Zusatzprüfungen",
    "coverage.group.tls": "Transportsicherheit",
    "coverage.group.dns": "DNS",
    "coverage.group.addressParity": "Adressen",
    "coverage.group.capabilities": "Funktionen",
    "coverage.group.updates": "Updates",
    "coverage.group.integrations": "Integrationen",
    "result.excluded.heading": "Gemeldet, aber nicht gezählt",
    "result.excluded.waived.heading": "Von dir ausgenommene Befunde",
    "result.excluded.waived.note": (
        "Diese Prüfungen sind fehlgeschlagen, beeinflussen die Note wegen "
        "deiner Ausnahmen aber nicht."
    ),
    "result.excluded.unfixable.heading": "Von OpenCloud fest vorgegeben",
    "result.excluded.unfixable.note": "Diese Werte sind im OpenCloud-Code festgelegt und können nicht konfiguriert werden. Sie dienen zur Information und beeinflussen die Bewertung nicht.",
    "result.scope.kicker": "Umfang",
    "result.scope.heading": "Was dieser Scan nicht sehen kann",
    "result.scope.body": "Der Scan prüft öffentlich zugängliche Informationen. <strong>Keine Befunde bedeuten nicht, dass die Instanz sicher ist</strong>, auch bei der besten Note. Nicht geprüft werden Betriebssystem und Pakete, Container-Laufzeit, Reverse-Proxy-Konfiguration, Backups und Wiederherstellung, Speicher, Geheimnisse und Schlüsselverwaltung, Konten, Passwörter, Multi-Faktor-Anmeldung, bestehende Freigabeberechtigungen und die Software-Lieferkette. Auch Daten, die erst nach der Anmeldung zugänglich sind, liegen außerhalb des Prüfumfangs. Prüfe diese beiden Bereiche gesondert:",
    "result.scope.audit": (
        '<strong>Audit-Logging.</strong> Der Audit-Dienst von OpenCloud nutzt nur den internen Event-Bus. Er veröffentlicht keinen Endpunkt und wird in keinem ohne Anmeldung zugänglichen Dokument genannt. Von außen lässt sich deshalb nicht feststellen, ob er läuft. Der Scanner prüft ihn nicht.'
    ),
    "result.scope.integrations": (
        "<strong>Ob eine Office- oder Kalender-Integration <em>korrekt</em> "
        "eingerichtet ist.</strong> Diese Seite meldet nur, dass ein "
        "App-Provider registriert ist, oder dass etwas auf den CalDAV-Pfad "
        "antwortet. Freigaberegeln, WOPI-Geheimnisse und die eigene "
        "Konfiguration des zweiten Dienstes liegen alle hinter einer Anmeldung "
        "und werden nicht geprüft."
    ),
    "result.tls.kicker": "Transport",
    "result.tls.heading": "Transportsicherheit",
    "result.tls.lede": "Protokoll- und Zertifikatsdetails aus dem TLS-Handshake. Die Befunde oben erklären, wie sich diese Messwerte auf die Note auswirken.",
    "result.tls.protocol": "Protokoll",
    "result.tls.bits": "({bits} Bit)",
    "result.tls.deprecated": "Veraltete Versionen",
    "result.tls.deprecated.accepted": "Noch akzeptiert: {list}",
    "result.tls.deprecated.refused": "Abgelehnt: {list}",
    "result.tls.chain": "Kette",
    "result.tls.chain.trusted": "Vertrauenswürdig",
    "result.tls.chain.not_established": "Nicht hergestellt",
    "result.tls.chain.not_trusted": "Nicht vertrauenswürdig",
    "result.tls.chain.incomplete_note": '- kein Pfad zu einem öffentlich vertrauenswürdigen Wurzelzertifikat',
    "result.tls.issued_to": "Ausgestellt für",
    "result.tls.unnamed": "unbenannt",
    "result.tls.issued_by": "Ausgestellt von",
    "result.tls.unknown": "unbekannt",
    "result.tls.valid_for": "Gültig für",
    "result.tls.validity": "Gültigkeit",
    "result.tls.validity.range": "{start} bis {end}",
    "result.tls.validity.expired": "- vor {days} Tag(en) abgelaufen",
    "result.tls.validity.remaining": "- noch {days} Tag(e)",
    "result.tls.lifetime": "Ausgestellt für",
    "result.tls.lifetime.days": "{days} Tag(e)",
    "result.tls.ocsp": "OCSP-Stapling",
    "result.tls.ocsp.stapled": "Eine Widerrufsantwort wird mitgeliefert",
    "result.tls.ocsp.not_stapled": "Nicht mitgeliefert",
    "result.tls.ocsp.undetermined": "Nicht ermittelt",
    "result.raw.kicker": "Rohdaten",
    "result.raw.heading": "Technische Details",
    "result.raw.lede": (
        "Das vollständige Ergebnisdokument, genau so, wie das Plugin es sieht."
    ),
    "result.raw.summary": "Das rohe JSON anzeigen",
    "result.export.kicker": "Export",
    "result.export.heading": "Dieses Ergebnis herunterladen",
    "result.export.lede": "Wähle einen vollständigen Bericht oder ein Behebungspaket. Die Download-Links funktionieren bis zum Ablauf des Scans; gespeicherte Dateien bleiben auf deinem Gerät verfügbar.",
    "result.export.pdf": "PDF-Bericht",
    "result.export.pdf.hint": "Für ein Ticket, eine Überprüfung oder einen Ausdruck.",
    "result.export.html": "Bericht herunterladen",
    "result.export.html.hint": (
        "Ein eigenständiger Bericht, den du nach Ablauf dieses Links offline öffnen kannst. Er stellt keine Netzwerkanfragen und aktualisiert sich nicht."
    ),
    "result.export.remediation.md": "Behebungspaket (Markdown)",
    "result.export.remediation.md.hint": (
        "Nur das, was noch offen ist: jeder Befund, was beobachtet wurde, und "
        "die nginx-, Caddy-, Traefik-, Compose- und .env-Fragmente, die ihn "
        "beheben. Für einen Pull Request oder ein Runbook."
    ),
    "result.export.remediation.html": "Behebungspaket (HTML)",
    "result.export.remediation.html.hint": (
        "Dasselbe Paket als eine Seite, die du offline öffnen oder drucken kannst."
    ),
    "result.export.csv": "CSV",
    "result.export.csv.hint": "Eine Zeile pro Befund, für eine Tabellenkalkulation.",
    "result.export.sarif": "SARIF",
    "result.export.sarif.hint": "Für ein Code-Scanning-Dashboard.",
    "result.export.json": "JSON",
    "result.export.json.hint": "Das rohe Dokument, das das Plugin auswertet.",
    "result.export.passed.heading": "Bestandene Prüfungen",
    "result.export.passed.note": (
        "Diese Prüfungen wurden bestanden und erfordern keine Maßnahme im Behebungsplan oben."
    ),
    "result.share.kicker": "Teilen",
    "result.share.heading": "Diesen Bericht teilen",
    "result.share.lede": "Kopiere den Link oder eine Zusammenfassung, oder öffne einen Entwurf in deinem E-Mail-Programm. Der Dienst versendet den Bericht nicht selbst.",
    "result.share.warning": "Wer diesen Link hat, kann den Bericht bis zum Ablauf lesen. Wenn du ihn in einem Kanal teilst, erhalten auch dessen Mitglieder und Linkvorschau-Dienste Zugriff. Teile stattdessen die Textzusammenfassung, wenn du keinen Zugriff auf den vollständigen Bericht gewähren möchtest.",
    "result.share.email": "Per E-Mail teilen",
    "result.share.email.hint": "Öffnet eine vorbereitete Nachricht in deinem E-Mail-Programm. Du entscheidest, ob du sie sendest.",
    "result.share.email.subject": "OpenCloud-Sicherheitsbericht für {target}",
    "result.share.email.body": (
        "Hier ist der Sicherheitsbericht für unsere OpenCloud-Instanz:\n\n{url}\n\nWer diesen Link hat, kann den Bericht lesen. Behandle ihn wie ein Passwort. Nach Ablauf des Berichts funktioniert der Link nicht mehr."
    ),
    "result.share.link": "Link kopieren",
    "result.share.link.hint": (
        "Die Adresse dieser Seite. Wer sie bekommt, kann den Bericht öffnen."
    ),
    "result.share.summary": "Zusammenfassung kopieren",
    "result.share.summary.hint": (
        "Befunde als Text ohne Berichtslink. Das Teilen der Zusammenfassung gewährt keinen Zugriff auf den vollständigen Bericht."
    ),
    "result.share.summary.body": (
        "OpenCloud-Sicherheitsbericht - {domain}\n"
        "Note {label} ({rating} von 5)\n"
        "Kritisch {critical} | Warnung {warning} | Info {info} | "
        "Hinweise {advisories} | Bestanden {passed}\n"
        "Gemessen mit check-opencloud-security."
    ),
    "result.share.done": "Kopiert",
    "result.share.failed": "Kopieren nicht möglich",
    "result.share.fallback": "Die Adresse dieses Berichts:",
    "result.feedback.prompt": "Wurde ein Befund deiner Ansicht nach falsch bewertet?",
    "result.feedback.link": "Falsch positives oder falsch negatives Ergebnis melden",
    "result.expiry.one": (
        "Diese Seite läuft in etwa 1 Minute ab, danach funktioniert der Link "
        "nicht mehr und das Ergebnis ist weg."
    ),
    "result.expiry.many": (
        "Diese Seite läuft in etwa {minutes} Minuten ab, danach funktioniert "
        "der Link nicht mehr und das Ergebnis ist weg."
    ),
    "result.expiry.warning.one": "Dieser Bericht verschwindet in etwa 1 Minute.",
    "result.expiry.warning.many": (
        "Dieser Bericht verschwindet in etwa {minutes} Minuten."
    ),
    "result.expiry.warning.action": "Lade eine Kopie herunter, um ihn zu behalten",
    "result.expiry.gone": (
        "Dieser Bericht ist abgelaufen. Der Link und seine Downloads funktionieren nicht mehr."
    ),
    # ----------------------------------------- transport facts beside the grade
    "tls.fact.protocol": "TLS-Version",
    "tls.fact.protocol.detail": "akzeptiert auch {list}",
    "tls.fact.expiry": "Zertifikat läuft ab",
    "tls.fact.expiry.expired": "vor {days} Tag(en) abgelaufen",
    "tls.fact.expiry.remaining": "noch {days} Tag(e)",
    "tls.fact.chain": "Kette",
    "tls.fact.chain.incomplete": "Unvollständig",
    "tls.fact.chain.incomplete.detail": 'kein Pfad zu einem öffentlich vertrauenswürdigen Wurzelzertifikat',
    "tls.fact.chain.untrusted": "Nicht vertrauenswürdig",
    "tls.fact.chain.untrusted.detail": (
        "selbstsigniert, oder eine unbekannte Zertifizierungsstelle"
    ),
    "tls.fact.chain.unknown": "Nicht hergestellt",
    "tls.fact.chain.unknown.detail": (
        "der Handshake hat das Zertifikat nie erreicht"
    ),
    "tls.fact.chain.ok": "Vollständig und vertrauenswürdig",
}
