"""
The English source strings.

This catalogue is the original: every other language is a translation of what
is written here, and a key that does not exist here does not exist at all.
The identifiers read ``page.element`` so that a template says what it wants
rather than what it says, and so that a sentence can be rewritten without
touching markup in four places.

A value may contain the inline markup that belongs to the sentence -
emphasis, a code span, a link - and templates render those with ``t.html``.
Anything interpolated into one is escaped on the way in.

What is deliberately *not* here: identifiers, versions, certificate subjects,
error text from a scanned host and every other piece of measured evidence.
The scanner reports those, this layer only labels them.
"""

from __future__ import annotations

MESSAGES: dict[str, str] = {
    # ---------------------------------------------------------------- site
    # ------------------------------------------------- the operator's area
    # Served only where COS_WEB_ADMIN_ENABLED asked for it, behind an
    # authentik sign-in, and never indexed. Kept in the catalogue like every
    # other page so the area is translated rather than the one English
    # corner of a localized service.
    "admin.title": "Operator area",
    "admin.description": "Service state, reference data and the audit trail.",
    "admin.kicker": "Operations",
    "admin.tabs.aria": "Operator area",
    "admin.tabs.overview": "Overview",
    "admin.tabs.configuration": "Configuration",
    "admin.tabs.rules": "Rules",
    "admin.config.title": "Configuration",
    "admin.config.lede": "Every COS_WEB_* variable this service reads, and the value it is running with.",
    "admin.config.scope": "These are this web process’s effective settings at startup. OpenCloud and the scan worker have their own configuration. Credentials are shown only as set or not set.",
    "admin.config.source.environment": "Set",
    "admin.config.source.default": "Default",
    "admin.config.secret.set": "Set (value hidden)",
    "admin.config.unset": "Not set",
    "admin.config.default": "Documented default:",
    "admin.config.unknown.kicker": "Check the spelling",
    "admin.config.unknown.heading": "Variables this service does not read",
    "admin.config.unknown.lede": "These variables start with COS_WEB_ but do not match a known setting. Check their spelling: a typo leaves the default value in use. Their values are not shown.",
    "admin.config.group.storage": "Storage and workers",
    "admin.config.group.scanning": "How a scan runs",
    "admin.config.group.targets": "What may be scanned",
    "admin.config.group.limits": "Rate limits and abuse guards",
    "admin.config.group.approval": "Target approval",
    "admin.config.group.network": "Public address, proxy and indexing",
    "admin.config.group.reference": "Release and advisory data",
    "admin.config.group.interfaces": "API documentation and agent endpoint",
    "admin.config.group.mcp_auth": "Sign-in on the agent endpoint",
    "admin.config.group.admin": "Operator area",
    "admin.config.group.audit": "Audit trail",
    "admin.config.group.protection": "Erasure, signatures and encryption",
    "admin.config.group.frontend": "Frontend",
    "admin.rules.title": "Rules in force",
    "admin.rules.lede": "How grades are calculated and which request limits this deployment uses.",
    "admin.rules.scope": "This overview shows the settings loaded when this process started and the rules defined in the code. Target addresses and visitor details are not shown.",
    "admin.rules.on": "Enforced",
    "admin.rules.off": "Off",
    "admin.rules.variables": "Set by",
    "admin.rules.rating.kicker": "Grades",
    "admin.rules.rating.heading": "How an instance is rated",
    "admin.rules.rating.lede": "The rating is the scanner's own; this service only shows it. These are the rules it applies to every scan here.",
    "admin.rules.rating.scale": "The scale",
    "admin.rules.rating.caps": "What a failed check can do to the grade",
    "admin.rules.rating.version.title": "The version sets the starting grade",
    "admin.rules.rating.version.body": "The starting grade depends on the release line's support status and known vulnerabilities affecting the version. Failed checks can lower that grade.",
    "admin.rules.rating.overrides.title": "End of life and the release track",
    "admin.rules.rating.shared.title": "One ceiling per severity",
    "admin.rules.rating.extra.title": "Extra checks count towards the grade",
    "admin.rules.rating.extra.body": "Transport security, headers and other extra checks limit the grade in the same way as hardening checks.",
    "admin.rules.rating.waivers.title": "Waivers a visitor may choose",
    "admin.rules.rating.waivers.body": "{count} hardening checks may be waived in the form. A waived check stops capping the grade and stays in the report, marked; end of life cannot be waived.",
    "admin.rules.rating.track.title": "Release track",
    "admin.rules.rating.track.body": "Without a choice in the form, the track is {track}. The track changes how a version is rated, never how hard the instance is probed.",
    "admin.rules.rating.reference.title": "Reference data rated against",
    "admin.rules.rating.reference.body": "{advisories} advisories in the database; release schedule dated {schedule}.",
    "admin.rules.rating.more": "The <a href=\"/grades\">grades page</a> explains each grade to visitors in the same terms.",
    "admin.rules.group.submissions": "Submission limits",
    "admin.rules.group.submissions.lede": "How often a client may ask, and how the service behaves under load.",
    "admin.rules.group.probe": "Probe block",
    "admin.rules.group.probe.lede": "Limits on repeated requests to targets that cannot be scanned.",
    "admin.rules.group.targets": "What may be scanned",
    "admin.rules.group.targets.lede": "Checked before anything connects, and again for every redirect.",
    "admin.rules.group.scanner": "How hard a host is probed",
    "admin.rules.group.scanner.lede": "The flags every scan from this deployment is built with. No request can change them.",
    "admin.rules.group.operator": "Credentials and operator actions",
    "admin.rules.group.operator.lede": "Limits on requests that require credentials and actions in the operator area.",
    "admin.rules.rule.client_limit.title": "Per-client limit",
    "admin.rules.rule.client_limit.body": "At most {limit} submissions per client every {window}. An IPv4 address is one client; an IPv6 client is its /{ipv6}.",
    "admin.rules.rule.daily_cap.title": "Daily cap",
    "admin.rules.rule.daily_cap.body": "At most {limit} submissions per client every {window}, on top of the per-client limit.",
    "admin.rules.rule.target_cooldown.title": "Per-target cooldown",
    "admin.rules.rule.target_cooldown.body": "The same instance may be scanned once every {cooldown}, whoever asks.",
    "admin.rules.rule.batch.title": "Batch size",
    "admin.rules.rule.batch.body": "A batch carries at most {limit} targets, and each one counts against every limit.",
    "admin.rules.rule.queue.title": "Queueing under load",
    "admin.rules.rule.queue.body": "{workers} scans run at once; further submissions wait in order and are never refused for load.",
    "admin.rules.rule.agent_wait.title": "Automatic retry limit",
    "admin.rules.rule.agent_wait.body": "MCP and the workflows wait out a Retry-After of up to {wait} themselves, at most {attempts} attempts; a longer one is handed back to the caller.",
    "admin.rules.rule.probe_block.title": "Block after repeated strikes",
    "admin.rules.rule.probe_block.body": "{limit} strikes within {window} block the client's network for {block}.",
    "admin.rules.rule.probe_escalation.title": "Repeated blocks grow",
    "admin.rules.rule.probe_escalation.body": "A network blocked again within {repeat} of its last block waits {factor} times longer each time: {steps}.",
    "admin.rules.rule.probe_network.title": "The block covers a network",
    "admin.rules.rule.probe_network.body": "A block applies to the client's IPv4 /{ipv4} and IPv6 /{ipv6}, so the next address along cannot step around it.",
    "admin.rules.rule.strike_scans.title": "A scan that finds no OpenCloud is a strike",
    "admin.rules.rule.strike_scans.body": "status.php did not answer, was not JSON, named another product, or the scan ran out of time. The same host again is another strike; a finished scan never is.",
    "admin.rules.rule.strike_refusals.title": "A refused target is a strike",
    "admin.rules.rule.strike_refusals.body": "A submission refused for what it points at counts; a typo or a name that does not resolve does not:",
    "admin.rules.refusal.blocked": "an address this deployment excludes",
    "admin.rules.refusal.internal": "a local or internal name",
    "admin.rules.refusal.not_approved": "an instance approval mode has not approved",
    "admin.rules.refusal.private": "a private, loopback or link-local address",
    "admin.rules.refusal.unstable": "a name whose lookups disagree",
    "admin.rules.refusal.wildcard_dns": "a wildcard or rebinding DNS name",
    "admin.rules.rule.private_addresses.title": "Public addresses only",
    "admin.rules.rule.private_addresses.body": "Every address a name resolves to must be public unicast; one private answer refuses the target. Beyond the private ranges, these are refused too:",
    "admin.rules.rule.internal_names.title": "Local names and metadata endpoints",
    "admin.rules.rule.internal_names.body": "Refused by name as well as by address:",
    "admin.rules.rule.wildcard_dns.title": "Wildcard and rebinding DNS names",
    "admin.rules.rule.wildcard_dns.body": "Names under these services point anywhere their spelling says. The address behind one can still be scanned by typing it:",
    "admin.rules.rule.dns_consistency.title": "A name must resolve the same way twice",
    "admin.rules.rule.dns_consistency.body": "A submitted name is looked up twice and refused when the answers share no address; every address from both is checked.",
    "admin.rules.rule.redirects.title": "Every redirect is checked",
    "admin.rules.rule.redirects.body": "A redirect is resolved and checked like the submitted target before it is followed, and the scan dials only addresses that passed.",
    "admin.rules.rule.exclusions.title": "Exclusions",
    "admin.rules.rule.exclusions.body": "{count} entries excluded, from the environment and the overview tab together.",
    "admin.rules.rule.allowed_hosts.title": "Hosts exempt from the guard",
    "admin.rules.rule.allowed_hosts.body": "These names skip the public-address rules. Exclusions still apply:",
    "admin.rules.rule.approval.title": "Approval mode",
    "admin.rules.rule.approval.body": "Only approved instances are scanned; anything else is refused with 403. {count} listed entries; DNS approval record: {record}.",
    "admin.rules.rule.stop_when_not_opencloud.title": "One request for a host that is not OpenCloud",
    "admin.rules.rule.stop_when_not_opencloud.body": "An answer from status.php that is not OpenCloud ends the scan, without a retry over unverified HTTPS or plain HTTP.",
    "admin.rules.rule.single_address.title": "One address per scan",
    "admin.rules.rule.single_address.body": "A name resolving to several addresses is scanned on one of them, never on every node of a pool.",
    "admin.rules.rule.no_port_scan.title": "No extra ports",
    "admin.rules.rule.no_port_scan.body": "Only the port submitted is contacted; the debug ports are not probed.",
    "admin.rules.rule.load.title": "Load per scan",
    "admin.rules.rule.load.body": "At most {concurrency} requests in flight, each allowed {timeout}; a whole scan is stopped after {job}.",
    "admin.rules.rule.purge_attempts.title": "Erasure credential attempts",
    "admin.rules.rule.purge_attempts.body": "{limit} wrong credentials per client within {window}, then refused until the window ends. Right ones are never counted.",
    "admin.rules.rule.admin_refresh.title": "Refresh buttons",
    "admin.rules.rule.admin_refresh.body": "Each reference-data refresh may be pressed once every {cooldown}.",
    "admin.docs.kicker": "Operator documentation",
    "admin.docs.source": "Shown from <code>{file}</code> in the repository, in English.",
    "admin.band": "Operator area - signed in as {user}",
    # Shown only where COS_WEB_ADMIN_SIGN_OUT_URL named where the provider in
    # front ends its session. This service has none of its own to end.
    "admin.band.signout": "Sign out",
    "admin.lede": "Check the service state, review the reference data and run the worker’s daily refreshes manually.",
    "admin.noscript": (
        "The readings above are filled in by JavaScript. Without it, reload the "
        "page to see the current ones; both refresh buttons still work."
    ),
    "admin.state.kicker": "Now",
    "admin.state.heading": "Service state",
    "admin.state.lede": "Current counts and configured limits. Individual scan details and client addresses are not available here.",
    "admin.state.worker": "Worker",
    "admin.state.worker.up": "Running",
    "admin.state.worker.down": "Not answering",
    # The third answer, and the one worth having: the worker's heartbeat is a
    # key in the store, so a store that is gone is not evidence about the
    # worker either way. Saying "not answering" there sends somebody to
    # restart the wrong container.
    "admin.state.worker.unknown": "Cannot tell",
    "admin.state.store.down": "The store is not answering - the heartbeat cannot be read",
    "admin.state.queue": "{depth} queued, {workers} workers",
    "admin.state.ratelimit": "Rate limit",
    "admin.state.ratelimit.value": "{limit} per {window}s",
    "admin.state.cooldown.value": "{seconds}s per target",
    "admin.state.guard": "Abuse guard",
    "admin.state.guard.value": "{active} networks blocked",
    "admin.state.guard.week": "last 7 days: {blocks} blocks, {strikes} strikes, {daily} daily caps reached",
    "admin.state.guard.off": "Probe block off",
    "admin.state.schedule": "Release schedule",
    "admin.state.advisories": "Advisories",
    "admin.state.checked": "checked {when}",
    # The two that say why a stamp has stopped moving. Both refreshes leave
    # the data exactly as it was when they do not succeed, so the checked
    # stamp cannot tell these apart - and the difference between a source
    # nobody can reach and a document this deployment is right to refuse is
    # the whole of what an operator does next.
    "admin.state.checked.failed": "checked {when} - the last attempt could not be fetched",
    "admin.state.checked.rejected": (
        "checked {when} - the last attempt was refused by the guards"
    ),
    "admin.state.refresh.off": "the daily refresh is off",
    # Relative, because the question is never "what date does this say" but
    # "how long has this been sitting there". The exact stamp is on the
    # element, for whoever does want the date.
    "admin.state.ago.minutes": "{minutes}m ago",
    "admin.state.ago.hours": "{hours}h ago",
    "admin.state.ago.days": "{days}d ago",
    "admin.state.never": "never",
    "admin.state.unknown": "unknown",
    "admin.state.age.seconds": "Read {seconds}s ago",
    "admin.state.age.minutes": "Read {minutes}m ago",
    "admin.state.age.waiting": "Waiting for the first reading",
    "admin.state.stale": "The service has not responded recently. These are the last available readings and may be out of date.",
    "admin.state.refresh": "Read again",
    "admin.state.copy": "Copy diagnostics",
    "admin.state.copy.done": "Copied",
    "admin.state.copy.failed": "Could not copy",
    # What this deployment offers the world. Every one of these is a setting
    # read at startup, so the card is the server's and never repolled - and
    # the two sentences that carry the accent describe a *combination*, since
    # neither setting is a mistake on its own.
    "admin.surfaces.kicker": "Exposure",
    "admin.surfaces.heading": "What this deployment offers",
    "admin.surfaces.lede": (
        "The settings this process was started with, and the same ones the "
        "diagnostics document reports. None of them changes without a "
        "restart, so none of them is polled."
    ),
    "admin.surfaces.on": "On",
    "admin.surfaces.off": "Off",
    "admin.surfaces.mcp": "Agent endpoint at /mcp",
    "admin.surfaces.mcp.guarded": "A token from the configured issuer is required.",
    "admin.surfaces.mcp.open": (
        "No token is required: any agent that can reach it can spend this "
        "service's workers."
    ),
    "admin.surfaces.docs": "Browsable API pages at /docs",
    "admin.surfaces.docs.contract": (
        "Off hides the pages, not the contract: /openapi.json, /arazzo.json "
        "and /.well-known/ai.json stay public."
    ),
    "admin.surfaces.indexed": "Findable by search engines",
    "admin.surfaces.private": "Scans of private network addresses",
    "admin.surfaces.private.found": (
        "Allowed on a deployment that asks to be indexed: a stranger who "
        "finds this service can point it at the network it stands in."
    ),
    "admin.surfaces.private.estate": (
        "Allowed, which is what a deployment scanning its own estate is for."
    ),
    "admin.surfaces.encrypt": "Results encrypted at rest",
    "admin.surfaces.audit": "Audit trail",
    "admin.surfaces.audit.file": "Written to a file that outlives the container.",
    "admin.surfaces.audit.memory": (
        "A ring of {count} records in this process's memory, and nothing on "
        "disk."
    ),
    "admin.surfaces.targets": "Targets recorded in the clear",
    "admin.exclusions.kicker": "Exclusions",
    "admin.exclusions.heading": "Addresses this service will not scan",
    "admin.exclusions.lede": (
        "An entry takes effect from the next request, in every process, "
        "without a restart - and a scan already waiting in the queue is "
        "refused rather than run. Nothing here can make this service scan "
        "something: the list only ever refuses."
    ),
    "admin.exclusions.add.label": "Hostname, .suffix domain, address or CIDR range",
    "admin.exclusions.add.placeholder": "opencloud.example.com",
    "admin.exclusions.add.action": "Exclude",
    "admin.exclusions.add.hint": (
        "A domain written with a leading dot excludes everything under it "
        "as well. A range is matched against every address a hostname "
        "resolves to."
    ),
    "admin.exclusions.remove": "Withdraw",
    "admin.exclusions.empty": "Nothing is excluded in this deployment.",
    "admin.exclusions.source.configured": "From the environment",
    "admin.exclusions.updated": "Last changed here {when}.",
    "admin.exclusions.durability": (
        "Entries added here live in Redis, which this deployment is free to "
        "flush. Put the ones that must outlive it in COS_WEB_BLOCKED_TARGETS, "
        "where they cannot be withdrawn from this page."
    ),
    "admin.exclusions.unreadable": (
        "The store did not answer, so the exclusions cannot be read or "
        "changed right now. They are still in force: a scan that cannot "
        "check them is refused, not run."
    ),
    "admin.blocklist.error.shape": (
        "That is not an entry. Give a hostname, a domain starting with a dot, "
        "an address or a CIDR range."
    ),
    "admin.blocklist.error.configured": (
        "That entry comes from COS_WEB_BLOCKED_TARGETS. Remove it there and "
        "restart, so the deployment and this list cannot disagree."
    ),
    "admin.blocklist.error.full": (
        "This list is full. Move the standing entries into "
        "COS_WEB_BLOCKED_TARGETS."
    ),
    "admin.blocklist.error.long": (
        "That entry is longer than a hostname can be, so nothing it could be "
        "meant to match would ever reach this service."
    ),
    "admin.outcome.excluded": "Excluded. It is refused from the next request.",
    "admin.outcome.withdrawn": "Withdrawn. It can be scanned again.",
    "admin.actions.kicker": "Reference data",
    "admin.actions.heading": "Update reference data",
    "admin.actions.lede": (
        "The same two refreshes the worker runs daily, with the same rules: a "
        "schedule that lost a release line is refused, an advisory database "
        "only ever gains entries, and a failed fetch changes nothing."
    ),
    "admin.actions.schedule": "Sync release schedule",
    "admin.actions.schedule.hint": "Re-reads the published lifecycle page.",
    "admin.actions.advisories": "Check for advisories",
    "admin.actions.advisories.hint": "Asks the advisory feed for new entries.",
    "admin.outcome.updated": "Updated. The new document is in use.",
    "admin.outcome.unchanged": "Already current - nothing changed.",
    "admin.outcome.rejected": (
        "Refused: what was fetched did not pass the guards, so the previous "
        "data is still in use."
    ),
    "admin.outcome.failed": "Could not be fetched. Nothing changed.",
    "admin.outcome.disabled": "That refresh is switched off in this deployment's settings.",
    "admin.outcome.cooldown": "Just ran. Try again in {seconds}s.",
    "admin.probe.action": "Test the sources",
    "admin.probe.hint": (
        "Reads both sources and reports what a refresh would make of them. "
        "Nothing is stored."
    ),
    "admin.probe.schedule": "Release schedule: {answer}",
    "admin.probe.advisories": "Advisories: {answer}",
    "admin.probe.usable": "read, and a refresh would accept it",
    "admin.probe.rejected": "read, but the guards would refuse it",
    "admin.probe.unreadable": "could not be read - unreachable, or no longer in the expected shape",
    "admin.probe.disabled": "not checked - this refresh is switched off",
    "admin.search.kicker": "Search index",
    "admin.search.heading": "Is the shipped index still current",
    "admin.search.lede": (
        "The search index is generated during the build and cannot be changed "
        "here. This view checks whether its pages, languages and release "
        "version match the running service. It does not compare full page text."
    ),
    "admin.search.fresh": "Current",
    "admin.search.stale": "Out of date",
    # The third verdict, for an index that does not say which release it was
    # built for. The pages and the languages were compared; the copy could
    # not be, because only the stamp says what the copy was extracted from.
    "admin.search.unknown": "Cannot tell",
    "admin.search.detail.ok": "Every page and language is indexed for this release.",
    "admin.search.detail.unstamped": (
        "The index does not say which release it was built for, so only its "
        "pages and languages could be compared."
    ),
    "admin.search.detail.release": "Built for {built}, running {running}.",
    "admin.search.detail.missing": "Not indexed: {list}.",
    # A page the index holds and this build does not serve: a search result
    # leading to a page that is not there.
    "admin.search.detail.extra": "Indexed but no longer served: {list}.",
    "admin.search.detail.changed": "{count} page titles or summaries have changed since it was built.",
    "admin.search.detail.unreadable": "The index could not be read.",
    "admin.search.remedy": (
        "A published release always ships an index built for it, so this "
        "build is not a release as published - usually an image or bundle "
        "built from a checkout between releases. Deploy a published release, "
        "or regenerate the index in that checkout and rebuild what you deploy:"
    ),
    "admin.search.remedy.commit": (
        "Nothing needs committing by hand: every pull request to main "
        "rebuilds the index and commits it to its branch."
    ),
    "admin.search.fix": (
        "Every pull request to main and the release workflow regenerate the "
        "index and commit it. You cannot rebuild the index from this page."
    ),
    "admin.audit.kicker": "Audit",
    "admin.audit.heading": "Audit log",
    "admin.audit.lede": (
        "Scan requests, rejections and triggered limits, arriving as they "
        "happen. Following starts a connection; nothing is streamed until you "
        "ask for it."
    ),
    "admin.audit.privacy": (
        "Client addresses appear only as truncated HMAC fingerprints, using "
        "a salt held by this process. This view shows existing audit log "
        "entries and cannot resolve fingerprints to client addresses."
    ),
    "admin.audit.replicas": (
        "This deployment keeps no audit file, so these records come from the "
        "memory of the one process that answered - behind more than one "
        "replica, that is a part of the trail rather than all of it."
    ),
    "admin.audit.follow": "Follow",
    "admin.audit.stop": "Stop",
    "admin.audit.clear": "Clear",
    "admin.audit.empty": "Nothing yet.",
    "admin.audit.closed": (
        "The connection reached its {minutes}-minute limit and was closed by "
        "the service. Nothing was missed before that; press Follow to start "
        "another."
    ),
    "admin.audit.disabled": (
        "This deployment does not keep an audit trail, so there is nothing to "
        "follow. COS_WEB_AUDIT_LOG switches it on."
    ),
    "admin.audit.state.off": "Not following",
    "admin.audit.state.live": "Live",
    "admin.audit.state.reconnecting": "Reconnecting",
    "admin.audit.state.unsupported": "Not supported by this browser",
    "admin.audit.state.closed": "Closed by the service",
    "admin.audit.state.disabled": "Not kept",
    "site.og_image_alt": (
        "OpenCloud Security Scan - check an instance for known vulnerabilities, "
        "missing hardening and weak security headers"
    ),
    # ------------------------------------------------------- header chrome
    "chrome.skip_to_content": "Skip to content",
    "chrome.brand": "Security scan for OpenCloud",
    "chrome.menu": "Menu",
    "chrome.nav.primary": "Primary",
    "chrome.nav.secondary": "Secondary",
    "chrome.search.label": "Search documentation",
    "chrome.search.placeholder": "Search",
    "chrome.theme.toggle": "Toggle colour theme",
    "chrome.back_to_top": "Back to top",
    "nav.new_scan": "New scan",
    "nav.how_it_works": "How it works",
    "nav.grades": "Grades",
    "nav.catalogue": "Catalogue",
    "nav.docs": "Docs",
    "nav.search": "Search",
    "nav.compare": "Compare",
    "nav.api": "API",
    "nav.privacy": "Privacy",
    "nav.about": "About",
    # --------------------------------------------------- language switcher
    "lang.region": "Language",
    "lang.label": "Page language",
    "lang.apply": "Change language",
    "lang.note": "The scan itself is unchanged; only this page is translated.",
    # ------------------------------------------------------------- footer
    "footer.note.title": "About this service",
    "footer.note.body": "Scans run from this server against the address you enter. Results are available for {minutes} minutes before expiring. Powered by <code>check-opencloud-security</code>, with no account required and no trackers or analytics.",
    "footer.note.run_yourself": "Run it yourself",
    "footer.version.title": "The scanner version that produced these results",
    "footer.version.label": "Backend v{version}",
    "footer.legal.scope": "<strong>This check is not exhaustive, and a good grade is not a certificate.</strong> It reads the reported version, matching advisories, TLS, headers and publicly visible settings, including the documented demo accounts. A good grade means none of those went wrong - not that the instance is secure. It does not assess private files, the operating system, backups, account permissions or the surrounding network. Use the report alongside your other security checks; it is never a security audit or a penetration test.",
    "footer.legal.trademark": (
        "This is an independent community project. It is not affiliated with "
        "OpenCloud GmbH and is neither recommended nor supported by the "
        "company. &ldquo;OpenCloud&rdquo;, the OpenCloud logo and all "
        "associated trademarks are the property of their respective owners and "
        "are used here solely to indicate which software this tool checks."
    ),
    # --------------------------------------------------- the contents list
    "toc.heading": "On this page",
    "toc.aria": "On this page",
    "toc.group.act": "Fix",
    "toc.group.details": "Details",
    "toc.group.keep": "Keep",
    # --------------------------------------------------------- cross-links
    "pagenav.kicker": "Read on",
    "pagenav.aria": "More about this service",
    "pagenav.how.title": "How the scan works",
    "pagenav.how.blurb": (
        "What gets tested, and the four steps between the button and the grade."
    ),
    "pagenav.grades.title": "What the grades mean",
    "pagenav.grades.blurb": (
        "Every step from A+ to F, what holds a grade down and how to move it up."
    ),
    "pagenav.catalogue.title": "What the scanner checks",
    "pagenav.catalogue.blurb": (
        "Every hardening flag, header and TLS check, and every known advisory - "
        "independent of any one scan."
    ),
    "pagenav.docs.title": "CLI documentation",
    "pagenav.docs.blurb": "Install, configure and automate the scanner from a terminal.",
    "pagenav.api.title": "Scanning from a script or an agent",
    "pagenav.api.blurb": (
        "The JSON API, the fair use limits, the OpenAPI schema and the MCP endpoint."
    ),
    "pagenav.privacy.title": "What this server keeps",
    "pagenav.privacy.blurb": (
        "In memory, for {minutes} minutes, and what the log leaves out."
    ),
    "pagenav.about.title": "About OpenCloud",
    "pagenav.about.blurb": (
        "The platform this checks, and why this project is independent of it."
    ),
    "pagenav.cta.title": "Scan an instance",
    "pagenav.cta.blurb": "Back to the form. Takes a few seconds, no sign-up.",
    # ---------------------------------------------------------------- 404
    "notfound.title": "Nothing here",
    "notfound.description": (
        "The address does not exist, or the scan it pointed at has already "
        "expired."
    ),
    "notfound.kicker": "Not found",
    "notfound.lede": "This page does not exist, or the scan result has expired. Results are available for {minutes} minutes. Start a new scan to get a current report.",
    "notfound.action": "Run a new scan",
    # ------------------------------------------------------- landing page
    "index.title": "OpenCloud Security Scanner",
    "index.description": "Check an OpenCloud instance for known vulnerabilities, missing hardening, weak security headers and available updates. Free to use, with no account required.",
    "index.eyebrow": "Independent &middot; self-hosted assets &middot; temporary results",
    "index.headline": 'OpenCloud <em class="swash">Security Scanner</em>',
    "index.lede": "Enter an OpenCloud address you have permission to test. The scanner checks the instance’s publicly accessible settings, headers and software version, then gives it a grade from <strong>A+</strong> to <strong>F</strong>.",
    "index.form.kicker": "Scan request",
    "index.form.hint": "A few seconds &middot; no sign-up",
    "index.error.self_host": "Sorry for the wait. These limits help keep the service available to everyone. You can also run the open-source scanner on your own machine, as often as you need:",
    "index.field.label": "Address of the instance",
    "index.field.title": (
        "The instance base address: a hostname, optional port, and optional "
        "plain subfolder. No query, fragment, parameters, escapes or traversal."
    ),
    "index.field.hint": (
        "Just the hostname is enough - <code>https://</code> is assumed. A "
        "subfolder such as <code>/opencloud</code> is supported; queries, "
        "fragments, parameters and path traversal are refused. Public addresses "
        "only, and only instances you run or have permission to test."
    ),
    "index.field.invalid": (
        "Not a valid address: a hostname, optional port and a plain subfolder - "
        "no query, fragment or parameters."
    ),
    "index.submit": "Start scan",
    "index.submit.busy": "Starting scan…",
    "index.track.label": "Release track",
    "index.track.hint": "Used to assess release support and recommend a suitable update.",
    "index.format.label": "Show me",
    "index.format.dashboard": "A dashboard",
    "index.format.json": "The raw JSON",
    "index.format.hint": "Both come from the same scan.",
    "index.waivers.summary": "Ignore specific checks (optional)",
    "index.waivers.selected": "Ignore specific checks ({count} selected)",
    "index.remember.summary": (
        "Settings from your last scan in this browser: {track} · {format} · {waivers}."
    ),
    "index.remember.waivers.none": "no waived checks",
    "index.remember.waivers.one": "1 waived check",
    "index.remember.waivers.many": "{count} waived checks",
    "index.remember.apply": "Use them again",
    "index.remember.forget": "Forget them",
    "index.waivers.hint": "A waived finding remains visible in the report but does not lower the grade. Waivers apply only to checks that failed.",
    "index.waivers.search.label": "Filter checks",
    "index.waivers.search.placeholder": "Search by name...",
    "index.waivers.search.empty": "No checks match your search.",
    "index.assurance.aria": "How this service handles your data",
    "index.assurance.airgapped.title": "No external page assets",
    "index.assurance.airgapped.body": "Fonts, scripts and images are served here. The page uses no CDN or analytics.",
    "index.assurance.nostore.title": "Temporary storage",
    "index.assurance.nostore.body": (
        "The result lives in memory and is dropped the moment it expires."
    ),
    "index.assurance.noaccount.title": "No registration needed",
    "index.assurance.noaccount.body": "Start a scan without creating an account or providing an email address.",
    "index.assurance.ephemeral.title": "Ephemeral results",
    "index.assurance.ephemeral.body": (
        "The link stops working {minutes} minutes after the scan."
    ),
    # -------------------------------------------- release tracks and waivers
    "track.auto.label": "Detect automatically",
    "track.auto.description": (
        "Work the track out from the release the instance reports."
    ),
    "track.rolling.label": "Rolling",
    "track.rolling.description": "A new release roughly every three weeks.",
    "track.production.label": "Production",
    "track.production.description": (
        "Supported for about six months. The usual choice."
    ),
    "track.lts.label": "LTS",
    "track.lts.description": "Supported for two years.",
    "waivers.group.hardening": "Hardening",
    "waivers.group.headers": "Headers",
    "waivers.group.checks": "Checks",
    # ------------------------------------------------------------ severity
    "severity.critical": "critical",
    "severity.high": "high",
    "severity.medium": "medium",
    "severity.low": "low",
    # ------------------------------------------------------------ category
    "category.transport": "Transport & TLS",
    "category.cookies": "Cookies",
    "category.headers": "Security headers",
    "category.authentication": "Authentication & accounts",
    "category.sharing": "Sharing & links",
    "category.exposure": "Network exposure",
    "category.embedding": "Embedding",
    "category.lifecycle": "Version & lifecycle",
    "category.proxy": "Identity provider & proxy",
    # --------------------------------------------------------- grade scale
    "grade.5.headline": "Nothing found",
    "grade.5.meaning": (
        "The release is current for its track, no advisory matches the version, "
        "and every check the scan could run passed."
    ),
    "grade.5.improve": (
        "Keep the instance up to date on your release track. Run another scan "
        "after changes to the reverse proxy or sign-in configuration."
    ),
    "grade.4.headline": "An update is waiting",
    "grade.4.meaning": (
        "A newer patch release is available on the same release line. No known "
        "advisories match the installed version."
    ),
    "grade.4.improve": (
        "Install the recommended update within your release line."
    ),
    "grade.3.headline": "A release line behind",
    "grade.3.meaning": (
        "The instance uses an older release line than the latest on its track. "
        "That older line may still be supported."
    ),
    "grade.3.improve": (
        "Move up to the current line for your track. The scan names which one "
        "that is, and never points at a track you did not choose."
    ),
    "grade.2.headline": "Advisories match this version",
    "grade.2.meaning": (
        "Known vulnerabilities affect the installed version. None of the "
        "matching advisories is rated high or critical."
    ),
    "grade.2.improve": (
        "Upgrade to the fixed version for your release line. The result page "
        "names it - one advisory can be patched separately on several lines."
    ),
    "grade.1.headline": "A critical or high advisory matches",
    "grade.1.meaning": "At least one known vulnerability affecting the installed version is rated high or critical.",
    "grade.1.improve": (
        "Install the fixed version listed in the report and review the "
        "advisory's instructions."
    ),
    "grade.0.headline": "Out of support",
    "grade.0.meaning": "This release line no longer receives security fixes. It receives an F regardless of other findings or waivers.",
    "grade.0.improve": (
        "Move to a supported release line. Which lines are supported, and for how "
        "long, is on the release schedule the scan reads."
    ),
    # ---------------------------------------------------------- grades page
    "grades.title": "What the grades mean",
    "grades.description": (
        "What the grades A+, A, C, D, E and F mean for an OpenCloud instance "
        "and which changes can improve its rating."
    ),
    "grades.kicker": "The scale",
    "grades.lede": "The grade combines the installed release’s support status and known vulnerabilities with the checks that failed. This page explains the starting grade, the limits imposed by findings and the changes that can improve it.",
    "grades.scale.kicker": "Six steps",
    "grades.scale.heading": "The scale, best first",
    "grades.scale.intro": (
        "The <strong>0-5</strong> scale and its letters are the ones "
        "<code>scan.nextcloud.com</code> made familiar, kept deliberately so that "
        "an existing threshold, graph or alert rule keeps its meaning. That is "
        "also why there is no <strong>B</strong>: the scale skips it, and "
        "inventing one here would make two numbers mean the same grade."
    ),
    "grades.row.prefix": "Grade {label}: ",
    "grades.row.score": "{rating} out of 5",
    "grades.row.improve": "To move up:",
    "grades.caps.kicker": "The ceiling",
    "grades.caps.heading": "How failed checks limit the grade",
    "grades.caps.intro": (
        "The version determines the starting grade. Failed checks impose "
        "limits based on their severity. The lowest of these limits applies:"
    ),
    "grades.caps.at_best": "at best",
    "grades.caps.shared": "Findings with the same severity impose the same grade limit. If three medium findings remain, fixing only one does not remove that limit. The remediation plan keeps all three steps and shows when the grade would improve.",
    "grades.caps.rules": "Two rules take precedence. <strong>End of life always determines the grade</strong>: an unsupported release receives <strong>F</strong>, even with waivers. <strong>A release ahead of its declared track is not treated as outdated</strong>; the report identifies it as ahead of that track.",
    "grades.improve.kicker": "The shortest route",
    "grades.improve.heading": "From findings to fixes",
    "grades.improve.intro": "Each result includes the information you need to plan the work:",
    "grades.improve.plan": "<strong>A prioritised remediation plan.</strong> Each step explains what to change and shows the grade you could reach after completing that step and all preceding ones.",
    "grades.improve.release": "<strong>A specific release recommendation.</strong> The report identifies a version that fixes the advisory <em>on your release line</em>, while respecting your chosen track.",
    "grades.improve.explained": (
        "<strong>Explanations for failed checks.</strong> What was checked, why "
        "it matters and how to fix it, with a link to the relevant setting "
        "in the OpenCloud documentation."
    ),
    "grades.improve.waiver": "<strong>Exceptions for findings you accept.</strong> Waived findings remain visible but no longer limit the grade. A waiver applies only to a failed check and cannot change an end-of-life rating.",
    "grades.improve.rerun": "Run another scan after making changes to check which findings have been resolved.",
    "grades.limits.kicker": "Scope",
    "grades.limits.heading": "What a good grade is not",
    "grades.limits.body": "An <strong>A+</strong> means the checks used for the grade found no issue. It does not cover private files, the operating system, backups or account permissions. Use the report alongside those checks. See <a href=\"/how-it-works\">how the scan works</a> for its scope and limits.",
    # -------------------------------------------------------------- catalogue
    "catalogue.title": "What the scanner checks",
    "catalogue.description": (
        "Every hardening flag, security header, TLS check and known advisory "
        "this scanner can report, independent of any single scan result."
    ),
    "catalogue.kicker": "Reference",
    "catalogue.lede": "Browse the checks a scan can report and the advisory data used to assess a release. This catalogue describes the scanner’s coverage without scanning an instance.",
    "catalogue.checks.kicker": "Checks",
    "catalogue.checks.heading": "Every check, by category",
    "catalogue.checks.lede": (
        "Grouped by what they are about rather than how badly they can fail - "
        "severity depends on the instance being scanned, so it is not shown here."
    ),
    "catalogue.checks.not_configurable": "not configurable",
    "catalogue.advisories.kicker": "Advisories",
    "catalogue.advisories.heading": "Known advisories",
    "catalogue.advisories.lede": (
        "Every advisory in the database a scan is rated against, refreshed "
        "daily from the public feed."
    ),
    "catalogue.advisories.empty.tag": "None known",
    "catalogue.advisories.empty.body": "The advisory database is currently empty.",
    "catalogue.advisories.fixed_in": "Fixed in {version}",
    "catalogue.advisories.unfixed": "No fix published yet",
    # -------------------------------------------------- how the scan works
    "how.title": "How the scan works",
    "how.description": (
        "What this scanner tests on an OpenCloud instance, and what happens "
        "between pressing the button and reading the grade."
    ),
    "how.kicker": "The method",
    "how.lede": "The scanner connects directly to the address you enter and evaluates the responses itself. It checks information available without an account and uses its release and advisory data to assess the installed version.",
    "how.tests.heading": "What gets tested",
    "how.tests.version.title": "Version and lifecycle",
    "how.tests.version.body": (
        "Which release is running, whether it still receives security fixes, and "
        "whether any published advisory matches it. A release past its end of "
        "life is an F, whatever else is right."
    ),
    "how.tests.transport.title": "Transport and headers",
    "how.tests.transport.body": (
        "HTTPS reachability, the certificate and its remaining life, the TLS "
        "versions on offer, and the security headers a browser is actually sent - "
        "HSTS, CSP, frame and content-type protection."
    ),
    "how.tests.hardening.title": "Hardening and exposure",
    "how.tests.hardening.body": (
        "Basic authentication, public link password and expiry policy, password "
        "rules, directory listing, exposed endpoints and anything announcing the "
        "version to the world."
    ),
    "how.pipeline.kicker": "The pipeline",
    "how.pipeline.heading": "What happens when you press the button",
    "how.pipeline.lede": "Each scan goes through these four stages.",
    "how.pipeline.step1": (
        "<strong>Your address is checked.</strong> Private, loopback and cloud "
        "metadata addresses are refused before anything connects."
    ),
    "how.pipeline.step2": "<strong>The scan receives a random identifier.</strong> This identifier grants access to the result. There is no public list of scans.",
    "how.pipeline.step3": "<strong>The scan joins the queue.</strong> A fixed number of scans can run at once. When all workers are busy, your scan waits and the page shows its position in the queue.",
    "how.pipeline.step4": "<strong>The result expires.</strong> After {minutes} minutes, it can no longer be retrieved using its identifier.",
    "how.faq.kicker": "Questions",
    "how.faq.heading": "Frequently asked",
    "how.faq.q1": "Is this official OpenCloud software?",
    "how.faq.a1": (
        "No. This is an independent community project, not affiliated with "
        "OpenCloud GmbH and neither recommended nor supported by that company. "
        '"OpenCloud" and its logo are trademarks of their respective owners, '
        "used here solely to name the software this tool checks."
    ),
    "how.faq.q2": "Does a good grade mean an instance is secure?",
    "how.faq.a2": "No. The scan checks the reported version, matching advisories and settings visible from outside, with a limited test of the published demo credentials. It does not assess private files, the operating system, backups or account permissions. The report supports your security work; it does not replace an audit or penetration test.",
    "how.faq.q3": "How long do you keep a scan's result?",
    "how.faq.a3": (
        "In memory only, for {minutes} minutes, and then it is gone. No "
        "accounts, no analytics, no trackers - see "
        '<a href="/privacy">what this server keeps</a> for the rest.'
    ),
    "how.faq.q4": "Is there a rate limit?",
    "how.faq.a4": (
        "Yes, per visitor and per scanned target, so one busy visitor cannot "
        "crowd out another and the same instance is not scanned back to back. "
        'The exact numbers for this deployment are on the '
        '<a href="/api#api-limits">API page</a>.'
    ),
    "how.faq.q5": "Can I scan without a rate limit?",
    "how.faq.a5": (
        "Yes - the scanner is open source. Run it yourself with "
        '<a href="/cli">one Docker command</a> on your own machine, with no '
        "limit and no third party in the middle."
    ),
    "how.faq.q6": "Does a scan tell me about a pending OpenCloud update?",
    "how.faq.a6": "Yes. The reported version is assessed against the available release data, including its support status and release track. See <a href=\"/documentation/reference#update-check\">the update check</a> for how the recommendation is calculated.",
    # --------------------------------------------------------------- privacy
    "privacy.title": "What this server keeps",
    "privacy.description": (
        "What is stored while a scan runs, for how long, and what the operational "
        "log does and does not record."
    ),
    "privacy.kicker": "Privacy",
    "privacy.lede": "Scan results remain available for {minutes} minutes before expiring.",
    "privacy.retention.kicker": "Retention",
    "privacy.retention.heading": "Stored scan data",
    "privacy.retention.body": "The target address, chosen waivers and result are stored under the scan’s random identifier for {minutes} minutes, then expire. The ordinary operational log records only that identifier and the creation, start and completion events. Usage limits use a one-way fingerprint of the client address. An operator can also configure a separate audit log.",
    "privacy.uploads.kicker": "Uploaded reports",
    "privacy.uploads.heading": "When you upload a report to compare",
    "privacy.uploads.body": "The uploaded file is read in memory to calculate the comparison. Its contents and filename are not retained. The comparison is available under a random identifier for {minutes} minutes so you can reload or share it. It then expires and cannot be reconstructed from the discarded upload.",
    "privacy.self_host": "The same scanner is available as a command-line program and Python library. When run locally, it connects directly from your machine to the instance.",
    # ----------------------------------------------------------- legal notice
    "legal.title": "Legal Notice",
    "legal.description": (
        "Provider identification, contact details and disclaimers for the "
        "operator of this deployment."
    ),
    "legal.kicker": "Imprint",
    "legal.lede": (
        "Provider identification under German law, for the operator of this "
        "deployment."
    ),
    "legal.english_notice": (
        "This notice is the operator's own legal text and is available in "
        "English only. The page around it is translated; the text below is not."
    ),
    # ----------------------------------------------------------------- about
    "about.title": "About OpenCloud and this scanner",
    "about.description": (
        "What OpenCloud is, who makes it, and why this scanner is an independent "
        "community project."
    ),
    "about.kicker": "About",
    "about.lede": "OpenCloud provides file storage, synchronisation and sharing. This independent scanner checks the security settings an instance exposes to visitors.",
    "about.platform.kicker": "The platform",
    "about.platform.heading": "About OpenCloud",
    "about.platform.body": "<a href=\"https://opencloud.eu/\" rel=\"noopener noreferrer\">OpenCloud</a> is an open-source platform for storing, synchronizing and sharing files. Its administration guides are available at <a href=\"https://docs.opencloud.eu/\" rel=\"noopener noreferrer\">docs.opencloud.eu</a>.",
    "about.platform.independent": (
        "This scanner is an independent community project. It is not affiliated "
        "with OpenCloud GmbH and is neither recommended nor supported by the "
        "company. &ldquo;OpenCloud&rdquo;, the OpenCloud logo and all associated "
        "trademarks are the property of their respective owners."
    ),
    "about.project.kicker": "The project",
    "about.project.heading": "About this scanner",
    "about.project.body": (
        "Results come from <code>check-opencloud-security</code>, a Nagios and "
        "Icinga plugin with a built-in scanner library. You can use it through "
        "this website or run it on your own machine without a rate limit or queue."
    ),
    "about.project.origin": "<strong>Massoud Ahmed</strong> created this project to check OpenCloud’s release tracks, settings and deployment model with a scanner operators can run on their own machines. <a href=\"{project}\" rel=\"noopener noreferrer\">Source code and contributions are on GitHub</a>.",
    # ------------------------------------------------------------------- API
    "api.title": "Scanning from a script or an agent",
    "api.description": (
        "How to submit scans and retrieve results through the JSON API, "
        "including usage limits, OpenAPI, Arazzo workflows and the MCP endpoint."
    ),
    "api.kicker": "The API",
    "api.lede": "Use the JSON API to submit scans, check their progress and download results. Scripts and agents use the same scanning service and limits as the browser form.",
    "api.submit.kicker": "Submit & poll",
    "api.submit.heading": "Submit and poll",
    "api.submit.body": (
        "Submitting a scan returns <code>202</code> and its identifier. Polling "
        "returns <code>queued</code>, <code>running</code> or the completed "
        "result. Expired scans return <code>404</code>. You can supply four "
        "fields: the address, checks to waive, release track and output format. "
        "Other fields are rejected. The operator sets concurrency and timeouts."
    ),
    "api.limits.kicker": "Fair use",
    "api.limits.heading": "Fair use",
    "api.limits.enforced": "This deployment allows {client} submissions per {window} minute(s) from one address, with {cooldown}. Exceeding either limit returns <code>429</code> and a <code>Retry-After</code> header.",
    "api.limits.cooldown": "one scan per target every {minutes} minute(s)",
    "api.limits.no_cooldown": "no per-target cooldown",
    "api.limits.daily": "At most {count} scans per network per day.",
    "api.limits.probe": "A network whose scans keep finding no OpenCloud is paused for a while.",
    "api.limits.none": "This deployment sets no rate limit.",
    "api.limits.self_host": (
        "You can also run the scanner on your own machine without these limits: "
        '<a href="{project}" rel="noopener noreferrer">get the source on GitHub</a>.'
    ),
    "api.schema.kicker": "The schema",
    "api.schema.heading": "The schema",
    "api.schema.body": (
        "The machine-readable documents are always public, on this deployment and "
        'on every other: the <a href="/openapi.json">OpenAPI 3.1 description</a> '
        'of every operation, and the <a href="/arazzo.json">Arazzo 1.0.1 '
        "workflows</a> that say how those operations combine into submitting a "
        "scan, waiting for completion and retrieving the result."
    ),
    "api.schema.docs_on": (
        'Both are browsable here as <a href="/docs">Swagger UI</a> and '
        '<a href="/redoc">ReDoc</a>, served from this server like everything else '
        "- nothing is fetched from anywhere."
    ),
    "api.schema.docs_off": (
        "The interactive viewers (Swagger UI at <code>/docs</code>, ReDoc at "
        "<code>/redoc</code>) are switched off on this deployment; an operator "
        "turns them on with <code>COS_WEB_ENABLE_DOCS=true</code>."
    ),
    # ------------------------------------------------- API, for agents
    "api.agents.kicker": "AI agents",
    "api.agents.heading": "Start from one address",
    "api.agents.intro": "Agents can discover the API operations and scanning workflows through the public documents below. These descriptions are available without an account.",
    "api.agents.discovery": (
        "<strong>Discovery</strong> - "
        '<a href="/.well-known/ai.json">/.well-known/ai.json</a> names all of the '
        "below, with absolute URLs. Start here."
    ),
    "api.agents.openapi": (
        '<strong>OpenAPI</strong> - <a href="/openapi.json">/openapi.json</a>, '
        "every operation with its real status codes and response shapes."
    ),
    "api.agents.arazzo": (
        '<strong>Arazzo workflows</strong> - <a href="/arazzo.json">/arazzo.json'
        "</a>, the lifecycle of a scan: submit, poll, detect completion, export."
    ),
    "api.agents.mcp": (
        "<strong>MCP</strong> - <code>{url}</code>, a Model Context Protocol "
        "endpoint over streamable HTTP. Tools: <code>scan_instance</code>, "
        "<code>scan_instances</code>, <code>get_scan_result</code>, "
        "<code>plan_remediation</code>, <code>export_scan</code> and "
        "<code>erase_instance_data</code>. <code>scan_instance</code> does the "
        "whole task - submission, waiting and result - in one call. Prompts name "
        "the jobs themselves, such as <code>audit_instance</code>, which audits an "
        "instance and writes the remediation plan, and "
        "<code>review_transport_security</code>, which looks only at the "
        "certificate and the handshake. It answers the protocol rather than a "
        "browser, so it is an address to configure rather than a page to open."
    ),
    "api.agents.summary": "OpenAPI defines the available operations; Arazzo describes how to combine them into a scan workflow. Both documents are generated from the service code.",
    "api.agents.summary_mcp": "OpenAPI defines the operations, Arazzo describes the workflows, and MCP exposes those workflows as tools for agents. They use the same service implementation.",
    "api.webmcp.kicker": "In the browser",
    "api.webmcp.heading": "Use the page as a tool",
    "api.webmcp.intro": (
        "A browser that supports the "
        '<a href="https://webmachinelearning.github.io/webmcp/" '
        'rel="noopener noreferrer">WebMCP draft</a> can discover actions from the '
        "page already open. There is no separate client to configure."
    ),
    "api.webmcp.landing": (
        "On the landing page, <code>scan_opencloud_security</code> queues a scan. "
        "Its schema contains the release tracks, output formats and waiver "
        "identifiers offered by that page."
    ),
    "api.webmcp.result": (
        "On a result page, <code>get_scan_result</code> reads the current scan and "
        "<code>export_scan_report</code> downloads JSON, CSV, SARIF or PDF for the "
        "uuid already being viewed."
    ),
    "api.webmcp.boundary": (
        "Every browser tool calls the same JSON API with "
        "<code>Accept: application/json</code>. It keeps the SSRF guard, rate "
        "limits, target cooldown, queue and uuid isolation in place."
    ),
    "api.webmcp.support": (
        "WebMCP is still a draft and is ignored by browsers that do not implement "
        "it. Turning MCP off for this deployment removes the browser tools too."
    ),
    "api.clients.kicker": "Configuration",
    "api.clients.heading": "Configure an agent client",
    "api.clients.intro": "Configure your client with the endpoint URL and the streamable HTTP transport. If the operator requires authentication, you will also need to sign in.",
    "api.clients.body": (
        "Worked configuration for Claude Code, Claude Desktop, GitHub Copilot in "
        "VS Code and the CLI, Cursor, Zed and Windsurf - against this deployment or "
        'one of your own - is in <a href="{project}/blob/main/docs/mcp.md" '
        'rel="noopener noreferrer">the MCP guide</a>.'
    ),
    "api.rules.kicker": "The rules",
    "api.rules.heading": "The same rules as everybody else",
    "api.rules.body": (
        "The rules are the same for an agent as for anybody else. A scan is "
        "asynchronous and the uuid is the only way back to it; a <code>429</code> "
        "is an invitation to slow down rather than a refusal; and if you are "
        "checking more than a handful of instances, please "
        '<a href="{project}" rel="noopener noreferrer">run the scanner yourself</a> '
        "- it is the same code, on your machine, with no limits."
    ),
    # -------------------------------- Docker one-liners, on /documentation
    "cli.lede": "Run the scanner on your own machine to keep the scan under your control and avoid this service’s rate limits. The commands below use the same scanner as this website.",
    "cli.oneliner.kicker": "The one-liner",
    "cli.oneliner.heading": "One command, nothing installed",
    "cli.oneliner.body": "The command prints the grade, release support status, matching advisories and failed checks. Its Nagios exit code lets you use it in monitoring, scripts, CI or cron jobs. The scan runs in the container and connects directly to your instance.",
    "cli.json.kicker": "As JSON",
    "cli.json.heading": "The whole result document",
    "cli.json.body": (
        "Every number on a result page comes out of this document, including the "
        "<code>addresses</code> block behind the <strong>Resolved to</strong> line "
        "- the IPv4 and IPv6 the name pointed at while the scan ran."
    ),
    "cli.private.kicker": "Your own network",
    "cli.private.heading": "The instances this site will not scan",
    "cli.private.body": "Run the command-line scanner from a machine that can reach your internal instance. It supports private addresses and internal DNS names. Public scanning services restrict these targets to prevent requests into their own internal networks.",
    "cli.nodocker.kicker": "No Docker?",
    "cli.nodocker.heading": "Without a container",
    "cli.nodocker.body": "The scanner is also available from PyPI. Use <code>uv</code> to run it on demand or <code>pipx</code> to install it in an isolated Python environment.",
    # ------------------------------------------------ CLI documentation index
    "docs.index.title": "CLI documentation",
    "docs.index.description": (
        "Install, run and configure the check-opencloud-security CLI, with the "
        "complete operator guides collected in one place."
    ),
    "docs.index.kicker": "Documentation",
    "docs.index.heading": "Run the scanner from your terminal",
    "docs.index.lede": "Install the scanner, run your first check and configure it for regular use. The <code>docs/</code> guides cover monitoring, CI, deployment and the checks behind each finding.",
    "docs.index.toc.quickstart": "Quick start",
    "docs.index.toc.commands": "Commands",
    "docs.index.toc.options": "Useful options",
    "docs.index.toc.configuration": "Configuration",
    "docs.index.toc.monitoring": "Monitoring",
    "docs.index.toc.guides": "Full guides",
    "docs.index.quickstart.kicker": "Quick start",
    "docs.index.quickstart.heading": "One check, without installing anything",
    "docs.index.quickstart.container": (
        "Or use the published container. It runs the same plugin and returns the "
        "same Nagios/Icinga exit code:"
    ),
    "docs.index.quickstart.note": (
        "The plugin talks directly to the instance. It does not send the address "
        "to this website or to a remote verdict service."
    ),
    "docs.index.commands.kicker": "Two entry points",
    "docs.index.commands.heading": "The verdict and the result document",
    "docs.index.commands.plugin": (
        "The monitoring plugin: one alert line, performance data and the standard "
        "exit codes <strong>OK</strong>, <strong>WARNING</strong>, "
        "<strong>CRITICAL</strong> and <strong>UNKNOWN</strong>."
    ),
    "docs.index.commands.scanner": (
        "The scanner library as a CLI: the complete JSON result document for a "
        "script, a pipeline or an ad-hoc investigation."
    ),
    "docs.index.options.kicker": "The everyday flags",
    "docs.index.options.heading": "Useful options",
    "docs.index.option.host": (
        "Hostname, IP or URL; comma-separated for several instances."
    ),
    "docs.index.option.check_hardening": (
        "Include missing hardening measures and security headers."
    ),
    "docs.index.option.release_track": (
        "<code>rolling</code>, <code>production</code>, <code>lts</code> or "
        "<code>auto</code>."
    ),
    "docs.index.option.ignore_hardening": (
        "Accept one finding without erasing its evidence; repeatable and wildcard "
        "capable."
    ),
    "docs.index.option.debug": (
        "Explain where the rating started and what held it down."
    ),
    "docs.index.option.insecure": (
        "Skip certificate verification for an instance you control."
    ),
    "docs.index.option.thresholds": (
        "Choose the rating thresholds that map to monitoring states."
    ),
    "docs.index.option.format": "Print Nagios output or Prometheus text.",
    "docs.index.option.baseline": (
        "Alert only on findings that are new or worse than the last run."
    ),
    "docs.index.option.webhook": (
        "Notify another system when the configured state is reached."
    ),
    "docs.index.options.manual": (
        "<code>check-opencloud-security --help</code> is the installed manual. The "
        '<a href="{project}#cli-usage" rel="noopener noreferrer">complete option '
        "table</a> includes every default and its <code>COS_</code> environment "
        "variable."
    ),
    "docs.index.configuration.kicker": "One direction",
    "docs.index.configuration.heading": "Configuration and precedence",
    "docs.index.configuration.intro": (
        "Settings may come from a YAML or JSON file, the environment or the "
        "command line. The order is always:"
    ),
    "docs.index.precedence.aria": "Configuration precedence, highest first",
    "docs.index.precedence.cli": "CLI flag",
    "docs.index.precedence.cli.note": "the explicit answer for this run",
    "docs.index.precedence.env": "Environment",
    "docs.index.precedence.env.note": (
        "<code>COS_*</code>, useful in containers and services"
    ),
    "docs.index.precedence.file": "Configuration file",
    "docs.index.precedence.file.note": "the durable operator defaults",
    "docs.index.precedence.default": "Built-in default",
    "docs.index.precedence.default.note": (
        "the safe answer when nothing was specified"
    ),
    "docs.index.configuration.wizard": "Let the wizard write the first file:",
    "docs.index.configuration.note": (
        "A file ending in <code>.json</code> is JSON; every other suffix is YAML. "
        "Secrets may live in separate files rather than on the command line."
    ),
    "docs.index.monitoring.kicker": "Put it to work",
    "docs.index.monitoring.heading": (
        "Monitoring, automation and several instances"
    ),
    "docs.index.monitoring.nagios": (
        "<strong>Nagios or Icinga:</strong> use the plugin output directly; the "
        "worst configured threshold determines the exit code."
    ),
    "docs.index.monitoring.fleet": (
        "<strong>Several instances:</strong> pass a comma-separated host list, or "
        "use one configuration file per instance once their settings diverge."
    ),
    "docs.index.monitoring.prometheus": (
        "<strong>Prometheus:</strong> use <code>--format=prometheus</code> once, "
        "or expose the built-in exporter with "
        "<code>--prometheus-listen-port</code>."
    ),
    "docs.index.monitoring.ci": (
        "<strong>CI:</strong> run the same command in a pipeline; the status code "
        "makes a failed policy fail the job without a wrapper."
    ),
    "docs.index.monitoring.scheduled": (
        "<strong>Scheduled checks:</strong> systemd, cron, Kubernetes and the "
        "Ansible role all use the same CLI and configuration flow."
    ),
    "docs.index.guides.kicker": "From the repository",
    "docs.index.guides.heading": "Full operator guides",
    "docs.index.guides.lede": (
        "Every source document has its own HTML page here, generated from the "
        "repository Markdown and checked for drift in CI."
    ),
    # --------------------------------------------------- generated guide pages
    "docs.guide.kicker": "CLI documentation",
    "docs.guide.english_notice": "This guide is available in English, German, French and Spanish. The English version is shown for your selected language.",
    "docs.guide.toc.heading": "On this page",
    "docs.guide.toc.aria": "On this page",
    # ---------------------------------------------------------------- compare
    # The page that answers "did the fixes work" for a reader, the way
    # --baseline answers it for an operator's monitoring. Every number it
    # shows was worked out before the page was rendered; these are labels.
    "compare.title": "Compare two scans",
    "compare.description": (
        "Compare two finished scans of the same instance and see what was "
        "fixed, what is new and what is still open."
    ),
    "compare.eyebrow": "Did the fixes work?",
    "compare.heading": "Compare two scans",
    "compare.lede": "Enter the UUIDs of an earlier and a later scan. Both results must still be available. If the earlier result has expired, use a downloaded report in the form below.",
    "compare.form.baseline": "Earlier scan",
    "compare.form.current": "Later scan",
    "compare.form.placeholder": "The uuid from a result page address",
    "compare.form.submit": "Compare",
    "compare.form.hint": (
        "A uuid is the part after <code>/scan/</code> in the address of a "
        "result page. It is the whole of the authorisation for that result, "
        "so treat it like a password."
    ),
    "compare.error.unknown.baseline": (
        "The earlier scan is unknown or has expired. Nothing here can look it "
        "up: scan the instance again and compare the two newest results."
    ),
    "compare.error.unknown.current": (
        "The later scan is unknown or has expired. Nothing here can look it "
        "up: scan the instance again and compare the two newest results."
    ),
    "compare.error.unfinished.baseline": (
        "The earlier scan has not finished yet. Open its result page, wait "
        "for it, and compare again."
    ),
    "compare.error.unfinished.current": (
        "The later scan has not finished yet. Open its result page, wait for "
        "it, and compare again."
    ),
    "compare.error.same": (
        "Both fields name the same scan, so there is nothing to compare. Scan "
        "the instance again and compare the new uuid with this one."
    ),
    "compare.error.different_targets": "The two scans describe different instances, so they are not compared. Compare two scans of the same instance.",
    "compare.verdict.kicker": "Between the two scans",
    "compare.verdict.improved": "It got better",
    "compare.verdict.unchanged": "Nothing changed",
    "compare.verdict.regressed": "It got worse",
    "compare.rating.up": "The grade rose by {points} point(s).",
    "compare.rating.down": "The grade fell by {points} point(s).",
    # Said plainly, because a grade that did not move is the case people
    # misread as a failed remediation: findings of one severity share a single
    # cap, so several fixes can land before the letter changes.
    "compare.rating.same": "The grade is unchanged, but findings may still have been resolved. Several findings can impose the same grade limit. The lists below show the individual changes.",
    "compare.side.baseline": "Earlier",
    "compare.side.current": "Later",
    "compare.side.target": "Instance",
    "compare.side.version": "Version",
    "compare.side.scanned": "Scanned",
    "compare.side.unknown": "Not established",
    "compare.side.open": "Open this result",
    "compare.introduced.heading": "New findings ({count})",
    "compare.introduced.none": "Nothing is new since the earlier scan.",
    "compare.resolved.heading": "Resolved findings ({count})",
    "compare.resolved.none": "Nothing that was open in the earlier scan is gone.",
    "compare.unchanged.heading": "Still open ({count})",
    "compare.unchanged.none": "Nothing is open in both scans.",
    "compare.changes.heading": "What the comparison itemises",
    "compare.changes.category": "Category",
    "compare.changes.change": "Change",
    "compare.nothing_stored": (
        "This comparison was worked out from the two results and stored "
        "nowhere. Reload the page and it is worked out again; let either "
        "result expire and it can no longer be asked for at all."
    ),
    # ------------------------------------------------- comparing against a file
    # The second way onto the page above: the earlier side arrives as a report
    # somebody downloaded, because they kept it or because the scan it came
    # from expired. Only where it came from changes; the arithmetic does not.
    "compare.upload.kicker": "Have a report already?",
    "compare.upload.heading": "Compare an earlier report with a scan",
    "compare.upload.lede": (
        "Upload a report you downloaded earlier - JSON or CSV - and compare it "
        "with a scan from this service. Useful when the earlier scan has long "
        "since expired but you kept the file."
    ),
    "compare.upload.field.report": "Earlier report",
    "compare.upload.field.current": "Later scan",
    "compare.upload.field.hint": (
        "The <code>.json</code> or <code>.csv</code> file from the downloads on "
        "a result page. Up to {kilobytes} KB."
    ),
    "compare.upload.submit": "Compare with this file",
    "compare.upload.privacy": (
        "The file is read once, in memory, to work out the comparison, and is "
        "never written to disk or kept. The comparison itself is held for "
        "{minutes} minutes so that this page can be reloaded, and then it is "
        "gone too."
    ),
    "compare.upload.source.kicker": "Where the earlier side came from",
    "compare.upload.source.json": (
        "The earlier side was read from a JSON report you uploaded. It has no "
        "result page here - the file was read and discarded."
    ),
    "compare.upload.source.csv": (
        "The earlier side was read from a CSV report you uploaded. It has no "
        "result page here - the file was read and discarded."
    ),
    "compare.upload.source.dropped": (
        "{count} line(s) in the file were not named the way this scanner names "
        "its findings and were left out of the comparison."
    ),
    "compare.upload.source.missing.httpsEnforced": (
        "The uploaded file does not record whether HTTPS was enforced, so that "
        "measure was left out of both sides rather than guessed at. A CSV "
        "downloaded before this was added is one such file."
    ),
    "compare.upload.source.missing.update": (
        "The uploaded file does not record whether an update was pending, so "
        "pending updates were left out of both sides rather than guessed at. A "
        "CSV downloaded before this was added is one such file."
    ),
    "compare.upload.expires": (
        "This comparison disappears in about {minutes} minutes, and the link to "
        "it stops working. Nothing here can rebuild it: the file it was drawn "
        "from is gone."
    ),
    "compare.upload.error.missing": (
        "No file was uploaded. Choose the JSON or CSV report you downloaded "
        "earlier."
    ),
    "compare.upload.error.no_current": "Enter the UUID of the scan you want to compare with this report.",
    "compare.upload.error.empty": "That file is empty.",
    "compare.upload.error.too_large": "The file exceeds the {kilobytes} KB size limit.",
    "compare.upload.error.unreadable": (
        "That file could not be read as JSON or as CSV. Upload the file exactly "
        "as it was downloaded, without opening and re-saving it."
    ),
    "compare.upload.error.not_a_report": (
        "That file does not look like a scan report from this service. The "
        "downloads on a result page are what this expects."
    ),
    "compare.upload.error.rate_limit": (
        "That is a lot of reports from your network in a short time. Give it a "
        "minute and try again."
    ),
    "compare.upload.error.blocked": (
        "Several of the addresses scanned from your network recently did not "
        "turn out to be OpenCloud, so this service is taking a break from your "
        "network for a while - uploads included. The scanner and its "
        "comparison run on your own machine with no limits at all."
    ),
    "compare.upload.error.expired": (
        "This comparison has expired. Comparisons drawn from an uploaded file "
        "are kept for {minutes} minutes only, and the file itself was never "
        "kept at all - upload it again to ask the same question."
    ),
    # ----------------------------------------------------------------- search
    "search.title": "Search",
    "search.description": (
        "Search the scanner documentation and public guidance. Scan results are "
        "never indexed."
    ),
    "search.eyebrow": "Static release index",
    "search.heading": "Search the scanner",
    "search.lede": (
        "Documentation and public guidance only. The index is rebuilt for "
        "releases; it never reads the scan store, result pages, UUIDs, or "
        "submitted addresses."
    ),
    "search.label": "Search documentation",
    "search.placeholder": "TLS, Docker, waivers...",
    "search.submit": "Search",
    "search.scope.operator": "Operator area",
    "search.status.idle": "Enter a term to search this release's documentation.",
    "search.status.results": "{count} result(s) in this release.",
    "search.status.empty": "No public documentation matched that search.",
    "search.status.error": "Search is temporarily unavailable.",
    # The search manifest: the title and summary an index entry carries, as
    # opposed to the words on the page itself.
    "search.page.index.title": "Scan an OpenCloud instance",
    "search.page.index.summary": (
        "Run a public security scan against an OpenCloud instance."
    ),
    "search.page.how.title": "How the scanner works",
    "search.page.how.summary": (
        "What the scanner measures, what it cannot see, and how results are "
        "handled."
    ),
    "search.page.grades.title": "What the grades mean",
    "search.page.grades.summary": (
        "The A+ to F rating scale and the fixes that improve each grade."
    ),
    "search.page.catalogue.title": "What the scanner checks",
    "search.page.catalogue.summary": (
        "Every hardening flag, header and TLS check the scanner runs, and "
        "every known advisory."
    ),
    "search.page.documentation.title": "CLI documentation",
    "search.page.documentation.summary": (
        "Command-line quick start, configuration, monitoring, and deployment "
        "guides."
    ),
    "search.page.api.title": "API",
    "search.page.api.summary": (
        "Submit scans, poll results, export reports, and drive the service from "
        "an agent over OpenAPI, Arazzo or MCP."
    ),
    "search.page.privacy.title": "Privacy",
    "search.page.privacy.summary": (
        "Result retention, request logging, rate limits, and third-party policy."
    ),
    "search.page.about.title": "About this project",
    "search.page.about.summary": (
        "Why this independent OpenCloud security scanner exists."
    ),
    # ------------------------------------------- what a submission is refused for
    # The API answers the English sentence these translate; a browser reads
    # the translation. The SSRF guard names the identifier, this names the
    # sentence, and neither is derived from the other.
    "error.unsupported_fields": (
        "This service does not accept {fields}. The scan runs with server-side "
        "settings only."
    ),
    "error.rate_limit.client": (
        "That is a lot of scans from your network in a short time. Give it a "
        "minute and try again."
    ),
    "error.rate_limit.probe": (
        "Several of the addresses scanned from your network recently did not "
        "turn out to be OpenCloud, so this service is taking a break from your "
        "scans for a while. If you meant to check your own instance, the "
        "scanner runs on your machine too."
    ),
    "error.rate_limit.daily": (
        "That is all the scans this service can run for your network today. It "
        "will make room again tomorrow - or run the scanner yourself, which has "
        "no daily limit."
    ),
    "error.target.wildcard_dns": (
        "That name belongs to a service that points names at any address. Enter "
        "the instance's own hostname, or its address."
    ),
    "error.target.unstable": (
        "That hostname answers with different addresses each time it is looked "
        "up, so this service cannot tell what it would scan."
    ),
    "error.target.not_approved": (
        "This service only scans instances that have been approved for it. Ask "
        "the operator to add it, or publish the DNS record that approves it."
    ),
    "error.rate_limit.target": (
        "That instance was scanned very recently. Please give it a few minutes."
    ),
    "error.target.invalid": "That address cannot be scanned.",
    "error.target.empty": "Enter the address of the OpenCloud instance to scan.",
    "error.target.too_long": "That address is too long.",
    "error.target.characters": (
        "That address contains characters a hostname cannot have."
    ),
    "error.target.unparsed": "That address could not be parsed.",
    "error.target.scheme": "Only http:// and https:// targets can be scanned.",
    "error.target.credentials": "Credentials in the address are not accepted.",
    "error.target.address_only": (
        "Enter the instance base address only. A plain subfolder is accepted, "
        "but queries, fragments, parameters and path traversal are not."
    ),
    "error.target.port": "That address has an invalid port.",
    "error.target.no_host": "That address has no hostname.",
    "error.target.hostname_shape": (
        "That is not a hostname this service can scan."
    ),
    "error.target.unresolved": "That hostname does not resolve.",
    "error.target.hostname_long": "That hostname is too long.",
    "error.target.internal": "Local and internal addresses cannot be scanned.",
    "error.target.private": (
        "That address points into a private, loopback or link-local network, "
        "which this service will not scan."
    ),
    "error.target.blocked": (
        "This service has been asked not to scan that address."
    ),
    # Not about the address at all: this deployment could not read its own
    # exclusions and refuses to scan without them. Said plainly, because the
    # visitor has nothing to fix and the only useful next step is the one the
    # self-host pointer beside it offers.
    "error.store_unavailable": (
        "This service cannot reach its own configuration right now, and will "
        "not scan without knowing what it has been asked to leave alone. "
        "Please try again in a few minutes."
    ),
    # ----------------------------------------------------------- result page
    "result.title": "Scan results",
    "result.description": (
        "The result of one public scan, readable only with its own identifier."
    ),
    "result.kicker": "Security scan",
    "result.heading": "Scan result",
    "result.track.title": "The release track this scan was rated against",
    "result.track.label": "{track} track",
    "result.another": "Scan another instance",
    "result.compare": "Compare with an earlier scan",
    "result.tab.queued": "Queued: {target}",
    "result.tab.queued.position": "#{position} in line: {target}",
    "result.tab.running": "Scanning: {target}",
    "result.tab.ready": "Report ready: {target}",
    "result.tab.done": "Grade {label}: {target}",
    "result.tab.failed": "Scan failed: {target}",
    "result.compare.offer": "You scanned this instance earlier in this tab, at {time}.",
    "result.compare.offer.link": "See what changed since then",
    "result.progress.kicker": "In progress",
    "result.progress.queued.title": "Waiting for a scanner worker",
    "result.progress.queued.detail": (
        "Every worker is busy right now. Your scan keeps its place in line and "
        "starts as soon as one is free."
    ),
    "result.progress.running.title": "Scanning the instance",
    "result.progress.running.detail": (
        "Reading what the instance publishes: version, capabilities, certificate, "
        "headers and the endpoints it exposes without a login."
    ),
    "result.progress.step.queued": "Queued",
    "result.progress.step.running": "Running",
    "result.progress.step.done": "Result",
    "result.progress.estimate": "Most scans finish in under a minute.",
    "result.progress.elapsed": "{duration} elapsed",
    "result.progress.noscript": (
        "This page updates itself with JavaScript. Without it, reload the page in "
        "a few seconds to see the result."
    ),
    "result.progress.queue.position": (
        "Scan queued. Position in line: #{position} of {length}."
    ),
    "result.progress.queue.next": "Scan queued. You are next in line.",
    "result.progress.queue.waiting": "Waiting for a scanner worker to pick this up.",
    "result.progress.done.title": "Report ready",
    "result.progress.done.detail": "The grade is in. Opening the report.",
    "result.progress.failed.title": "Scan finished",
    "result.progress.failed.detail": (
        "The scan could not be completed. Opening the result page."
    ),
    "result.failed.fallback": "The scan could not be completed.",
    "result.failed.body": "The scanner could not obtain enough information to assign a grade. Check the address, confirm that it runs OpenCloud and make sure it is reachable from this service.",
    "result.document.kicker": "Result document",
    "result.document.heading": "Result document",
    "result.document.lede": (
        "The same document the command line check and the Nagios plugin evaluate."
    ),
    "result.verdict.kicker": "Verdict",
    "result.verdict.heading": "Overall rating",
    "result.verdict.dial": "Rating {label}, {rating} out of 5",
    "result.facts.instance": "Instance",
    "result.facts.resolved": "Resolved to",
    "result.facts.ipv6.heading": "IPv6 reachability",
    "result.facts.ipv6.note": (
        "Not checked - this deployment has no outbound IPv6 connectivity, so "
        "it is noted here rather than counted against the instance."
    ),
    "result.facts.product": "Product",
    "result.facts.track": "Release track",
    "result.facts.track.unknown": "unknown",
    "result.facts.eol_tag": "End of life",
    "result.facts.schedule": "Release schedule",
    "result.facts.schedule.stale": (
        "{version} is newer than this copy of the OpenCloud release schedule, so "
        "the schedule is probably out of date. It is not counted against the "
        "instance -"
    ),
    "result.facts.schedule.stale_generated": (
        "{version} is newer than this copy of the OpenCloud release schedule, "
        "generated {generated}, so the schedule is probably out of date. It is not "
        "counted against the instance -"
    ),
    "result.facts.schedule.link": "check the published lifecycle page",
    "result.facts.signin": "Sign-in",
    "result.facts.signin.external": "External provider",
    "result.facts.signin.upstream_tag": "upstream",
    "result.facts.signin.version_unavailable": "version not exposed",
    "result.facts.signin.advisories": "check security advisories",
    "result.facts.signin.builtin": "Built-in identity provider",
    "result.facts.signin.none": "Not detected -",
    "result.facts.signin.link": "how OpenCloud sign-in is set up",
    "result.facts.proxy": "Reverse proxy",
    "result.facts.proxy.detected": "Detected",
    "result.facts.http3": "HTTP/3",
    "result.facts.http3.value": "Advertised on UDP {ports} - make sure your firewall covers it on purpose (not rated)",
    "result.facts.http3.noport": "Advertised over UDP - make sure your firewall covers it on purpose (not rated)",
    "result.facts.upgrade_path": "Upgrade path",
    "result.facts.upgrade_path.complete": "{target} fixes every known advisory",
    "result.facts.upgrade_path.partial": "{target} still leaves {open} open; {safe} is the first release that clears them all",
    "result.facts.upgrade_path.unfixed": "{target} still leaves {open} open; no published release fixes all of them yet",
    "result.facts.office": "Office",
    "result.facts.calendar": "Calendar",
    "result.facts.calendar.detected": "Response received at the CalDAV path",
    "result.facts.newest": "Newest release",
    "result.facts.score": "Score",
    "result.facts.score.value": "{rating} out of 5",
    "result.counter.critical": "Critical",
    "result.counter.warning": "Warning",
    "result.counter.info": "Info",
    "result.counter.advisories": "Advisories",
    "result.counter.passed": "Passed",
    "result.verdict.why": "Why this grade:",
    "result.verdict.caveat": (
        "The grade reflects the checks below. It does not certify that the "
        "instance is secure: the scan sees only what it exposes to an "
        'anonymous visitor. <a href="#scan-limits">What it cannot see</a>.'
    ),
    "result.fix": "Fix:",
    "result.documentation": "Documentation",
    "result.explain.title": "What this check means",
    "result.plan.kicker": "Remediation plan",
    "result.plan.heading": "What gets you to {label}",
    "result.plan.then": "then {label}",
    "result.plan.still": "still {label}",
    "result.plan.note": "The plan prioritises changes that improve the grade. The grade beside each step assumes that you have completed it and all preceding steps. Findings of equal severity share a rating limit, so several fixes may be needed before the grade improves.",
    "result.plan.blocked.heading": "Holding the grade down, and not fixable",
    "result.plan.blocked.note": (
        "These values are hardcoded in OpenCloud and cannot be changed through "
        "configuration. They prevent the plan from reaching a higher grade."
    ),
    "result.eol.alert": (
        "This release no longer receives security fixes. Nothing else on this page "
        "can lift the grade until it is upgraded."
    ),
    "result.advisories.kicker": "Advisories",
    "result.advisories.heading": "Known advisories for this version",
    "result.advisories.lede": (
        "Published advisories whose affected range includes {version}."
    ),
    "result.advisories.fallback_id": "advisory",
    "result.advisories.unrated": "unrated",
    "result.advisories.no_summary": "No summary published.",
    "result.advisories.read": "Read the advisory",
    "result.findings.kicker": "Findings",
    "result.findings.heading": "Checks that failed",
    "result.findings.lede": (
        "Each finding limits the grade according to its severity. Fix critical "
        "findings first, as they have the greatest effect on the rating."
    ),
    "result.findings.filter.aria": "Filter findings by severity",
    "result.findings.filter.active": "Showing {severity} findings only.",
    "result.findings.filter.clear": "Show all findings",
    "result.findings.allclear.tag": "All clear",
    "result.findings.allclear.body": (
        "Every check this scanner runs passed on this instance."
    ),
    "result.hardening.kicker": "Hardening",
    "result.hardening.heading": "Hardening worth adding",
    "result.hardening.lede": "These settings add protection against common risks. Review the explanation and suggested fix for each one.",
    "result.hardening.tag": "hardening",
    "result.header.tag": "header",
    # ------------------------------------------------- configuration fragment
    "result.fragment.kicker": "Configuration snippet",
    "result.fragment.heading": "Paste this into your configuration",
    "result.fragment.lede": (
        "The findings above, in the syntax of the file that has to change. "
        "Pick where your instance is configured."
    ),
    "result.fragment.caution": (
        "Read each finding's Fix line before you paste. These are the values "
        "the checks look for, not a review of what your deployment needs."
    ),
    "result.fragment.picker": "Configuration format",
    "result.fragment.file": "Goes in {name}.",
    "result.fragment.copy": "Copy",
    "result.fragment.copied": "Copied",
    "result.fragment.copy_failed": "Could not copy",
    "result.fragment.nothing": "No remaining finding can be addressed in this format. Use {flavours} for the relevant configuration.",
    "result.fragment.elsewhere": (
        "These are fixed somewhere else - they belong in {flavours}:"
    ),
    "result.fragment.undecided": "These findings need a setting chosen for your deployment. Follow each finding’s fix instructions to determine the value.",
    # ------------------------------------------------------------ scan again
    "result.rescan": "Scan again",
    "result.rescan.ready": "Ready to scan this instance again.",
    "result.rescan.wait": "Ready to scan again in {countdown}.",
    "result.rescan.note": "The next scan uses the same target, waivers and release track so you can compare the results. Please wait for the cooldown, or run the open-source scanner on your own machine without limits:",
    "result.rescan.self_host": "run it yourself",
    "result.excluded.kicker": "Excluded",
    "result.coverage.kicker": "Coverage",
    "result.coverage.heading": "What this scan did not measure",
    "result.coverage.note": (
        "A grade describes the evidence this scan collected. These checks "
        "reached no conclusion, so the grade says nothing about them."
    ),
    "result.coverage.summary": "{measured} of {total} checks reached a conclusion.",
    "result.coverage.complete": (
        "Every check this scan considered reached a conclusion."
    ),
    "result.coverage.unavailable": (
        "This report was written before scans recorded their coverage, so it "
        "does not say which checks ran. That is not the same as a scan with "
        "no gaps."
    ),
    "coverage.reason.not_applicable": "Does not apply to this instance",
    "coverage.reason.probe_disabled": "The probe was turned off for this scan",
    "coverage.reason.prerequisite_missing": (
        "The instance did not publish what this reads"
    ),
    "coverage.reason.timeout": "Nothing answered in time",
    "coverage.reason.unreadable": "The answer could not be read",
    "coverage.reason.no_route": "This scanner has no route to that address",
    "coverage.group.hardening": "Hardening settings",
    "coverage.group.header": "Security headers",
    "coverage.group.advisoryHeader": "Advisory headers",
    "coverage.group.advisoryCheck": "Advisory observations",
    "coverage.group.extraCheck": "Extra checks",
    "coverage.group.tls": "Transport security",
    "coverage.group.dns": "DNS",
    "coverage.group.addressParity": "Addresses",
    "coverage.group.capabilities": "Capabilities",
    "coverage.group.updates": "Updates",
    "coverage.group.integrations": "Integrations",
    "result.excluded.heading": "Reported, but not counted",
    "result.excluded.waived.heading": "You asked to ignore these",
    "result.excluded.waived.note": (
        "These checks failed, but your waivers exclude them from the grade."
    ),
    "result.excluded.unfixable.heading": "Hardcoded in OpenCloud",
    "result.excluded.unfixable.note": "These flags are hardcoded in OpenCloud and cannot be configured by an operator. They are included for reference and do not affect the grade.",
    "result.scope.kicker": "Scope",
    "result.scope.heading": "What this scan cannot see",
    "result.scope.body": (
        "The scan checks publicly accessible information. <strong>No findings "
        "does not mean the instance is secure</strong>, even with the highest "
        "grade. It does not inspect the operating system and its packages, "
        "container runtime, reverse proxy configuration, backups and recovery, "
        "storage, secrets and key management, accounts, passwords, multi-factor "
        "sign-in, existing share permissions or the software supply chain. "
        "Data available only after sign-in is also outside its scope. "
        "Two further limits are worth checking separately:"
    ),
    "result.scope.audit": (
        "<strong>Audit logging.</strong> OpenCloud's audit service only consumes "
        "the internal event bus - it publishes no endpoint and appears in no "
        "unauthenticated document - so whether it runs cannot be established from "
        "outside at all. It is not checked."
    ),
    "result.scope.integrations": (
        "<strong>Whether an office or calendar integration is set up "
        "<em>correctly</em>.</strong> This page reports only that an app provider "
        "is registered, or that something answers the CalDAV path. Sharing rules, "
        "WOPI secrets and the second service's own configuration all live behind a "
        "login and are not checked."
    ),
    "result.tls.kicker": "Transport",
    "result.tls.heading": "Transport security",
    "result.tls.lede": (
        "What the TLS layer said before a single byte of HTTP was exchanged. The "
        "findings above already judge these; this is the measurement behind them."
    ),
    "result.tls.protocol": "Protocol",
    "result.tls.bits": "({bits} bit)",
    "result.tls.deprecated": "Deprecated versions",
    "result.tls.deprecated.accepted": "Still accepted: {list}",
    "result.tls.deprecated.refused": "Refused: {list}",
    "result.tls.chain": "Chain",
    "result.tls.chain.trusted": "Trusted",
    "result.tls.chain.not_established": "Not established",
    "result.tls.chain.not_trusted": "Not trusted",
    "result.tls.chain.incomplete_note": "- no path to a public root",
    "result.tls.issued_to": "Issued to",
    "result.tls.unnamed": "unnamed",
    "result.tls.issued_by": "Issued by",
    "result.tls.unknown": "unknown",
    "result.tls.valid_for": "Valid for",
    "result.tls.validity": "Validity",
    "result.tls.validity.range": "{start} to {end}",
    "result.tls.validity.expired": "- expired {days} day(s) ago",
    "result.tls.validity.remaining": "- {days} day(s) left",
    "result.tls.lifetime": "Issued for",
    "result.tls.lifetime.days": "{days} day(s)",
    "result.tls.ocsp": "OCSP stapling",
    "result.tls.ocsp.stapled": "A revocation answer is stapled",
    "result.tls.ocsp.not_stapled": "Not stapled",
    "result.tls.ocsp.undetermined": "Not determined",
    "result.raw.kicker": "Raw data",
    "result.raw.heading": "Technical details",
    "result.raw.lede": "The full result document, exactly as the plugin sees it.",
    "result.raw.summary": "Show the raw JSON",
    "result.export.kicker": "Export",
    "result.export.heading": "Take this result with you",
    "result.export.lede": (
        "The same scan, rendered four ways. Each one is generated when you ask for "
        "it and disappears with the scan itself."
    ),
    "result.export.pdf": "PDF report",
    "result.export.pdf.hint": "For a ticket, a review or a printout.",
    "result.export.html": "Download the report",
    "result.export.html.hint": (
        "One file that still reads after this link expires. Opens offline, "
        "makes no network request, and does not update."
    ),
    "result.export.csv": "CSV",
    "result.export.csv.hint": "One row per finding, for a spreadsheet.",
    "result.export.sarif": "SARIF",
    "result.export.sarif.hint": "For a code-scanning dashboard.",
    "result.export.json": "JSON",
    "result.export.json.hint": "The raw document the plugin evaluates.",
    "result.export.passed.heading": "What already passed",
    "result.export.passed.note": (
        "These checks came back clean, so they are not in the plan above."
    ),
    "result.share.kicker": "Share",
    "result.share.heading": "Share this report",
    "result.share.lede": "Copy the link or a text summary, or open a draft in your email client. This service does not send the report for you.",
    "result.share.warning": (
        "The address of this page is the only thing protecting it: anyone who "
        "has it can read the report until it expires. Posting it in a channel "
        "shares it with everyone in that channel, and with whatever fetches "
        "links there to build a preview. Copy the summary instead where the "
        "findings are the point."
    ),
    "result.share.email": "Share by email",
    "result.share.email.hint": (
        "Opens your own mail client with the message ready. Nothing leaves "
        "your browser until you send it."
    ),
    "result.share.email.subject": "OpenCloud security report for {target}",
    "result.share.email.body": (
        "Here is the security report for our OpenCloud instance:\n\n"
        "{url}\n\n"
        "This link is what grants access to the report, so treat it as a "
        "password. It expires on its own, after which the page is gone."
    ),
    "result.share.link": "Copy link",
    "result.share.link.hint": (
        "The address of this page. Anyone you give it to can open the report."
    ),
    "result.share.summary": "Copy summary",
    "result.share.summary.hint": (
        "The findings as text, with no link in it. The safer thing to paste "
        "into a chat channel."
    ),
    "result.share.summary.body": (
        "OpenCloud security report - {domain}\n"
        "Grade {label} ({rating} out of 5)\n"
        "Critical {critical} | Warning {warning} | Info {info} | "
        "Advisories {advisories} | Passed {passed}\n"
        "Measured by check-opencloud-security."
    ),
    "result.share.done": "Copied",
    "result.share.failed": "Could not copy",
    "result.share.fallback": "The address of this report:",
    "result.feedback.prompt": "Think the scan got something wrong?",
    "result.feedback.link": "Report a false positive or false negative",
    "result.expiry.one": (
        "This page expires in about 1 minute, after which the link stops working "
        "and the result is gone."
    ),
    "result.expiry.many": (
        "This page expires in about {minutes} minutes, after which the link stops "
        "working and the result is gone."
    ),
    "result.expiry.warning.one": "This report disappears in about 1 minute.",
    "result.expiry.warning.many": "This report disappears in about {minutes} minutes.",
    "result.expiry.warning.action": "Download a copy to keep it",
    "result.expiry.gone": (
        "This report has expired. The link and its downloads no longer work."
    ),
    # ----------------------------------------- transport facts beside the grade
    "tls.fact.protocol": "TLS version",
    "tls.fact.protocol.detail": "also accepts {list}",
    "tls.fact.expiry": "Certificate expires",
    "tls.fact.expiry.expired": "expired {days} day(s) ago",
    "tls.fact.expiry.remaining": "{days} day(s) left",
    "tls.fact.chain": "Chain",
    "tls.fact.chain.incomplete": "Incomplete",
    "tls.fact.chain.incomplete.detail": "no path to a public root",
    "tls.fact.chain.untrusted": "Not trusted",
    "tls.fact.chain.untrusted.detail": "self-signed, or an unknown authority",
    "tls.fact.chain.unknown": "Not established",
    "tls.fact.chain.unknown.detail": "the handshake never reached the certificate",
    "tls.fact.chain.ok": "Complete and trusted",
}
