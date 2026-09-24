"""
The remediation plan, regrouped by where each change is made.

The plan in :mod:`opencloud_local_scan.remediation` answers "what first". An
operator sitting down to fix things asks a second question: "I have the
reverse proxy configuration open - what do I change while I am here?" Eleven
findings are rarely eleven edits. Four missing headers are one header block,
three certificate complaints are one new certificate, and one update closes
every advisory that matches the installed release.

This module answers that question without judging anything new:

* **Every finding is placed where its fix is made** - the reverse proxy, the
  identity provider, OpenCloud's own configuration, or the DNS zone. The
  table below is explicit rather than inferred from the wording of a fix,
  and a test fails when a catalogued check has no place in it.
* **A change groups the findings one edit resolves.** Members of a family
  (``exposed:/a``, ``exposed:/b``) share their family's change; related
  checks share one named in :data:`SHARED_CHANGES`. Anything else is a
  change of its own.
* **Every rating is replayed, never guessed.** The planner hands in the same
  arithmetic it plans with, so "this change alone gives 4/5" is the rating
  function run with those findings removed - the same promise the ordered
  steps make.
* **Blocked and waived findings are not changes.** A flag OpenCloud
  hardcodes cannot be fixed by editing anything, and a waived one is a
  decision already made; both stay where the plan lists them.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .hardening import catalogue_id, describe, header_names

#: The reverse proxy, or whatever terminates TLS in front of OpenCloud.
REVERSE_PROXY = "reverseProxy"
#: The OpenID Connect provider users sign in through.
IDENTITY_PROVIDER = "identityProvider"
#: OpenCloud's own configuration: environment, compose file, release.
OPENCLOUD = "opencloud"
#: The domain's DNS zone.
DNS_ZONE = "dnsZone"

#: The order the groups are listed in, and the heading each one gets.
TARGETS: dict[str, str] = {
    REVERSE_PROXY: "Reverse proxy",
    IDENTITY_PROVIDER: "Identity provider",
    OPENCLOUD: "OpenCloud",
    DNS_ZONE: "DNS zone",
}

#: Where each catalogued check is fixed, keyed by catalogue id. A family root
#: covers every member (``exposed`` covers ``exposed:/config/opencloud.yaml``),
#: and every security response header is fixed at the reverse proxy.
CHECK_TARGETS: dict[str, str] = {
    # OpenCloud's own settings.
    "basicAuthDisabled": OPENCLOUD,
    "cspWithoutUnsafeInline": OPENCLOUD,
    "publicLinkPasswordEnforced": OPENCLOUD,
    "publicLinkExpirationEnforced": OPENCLOUD,
    "userEnumerationRestricted": OPENCLOUD,
    "passwordPolicyEnforced": OPENCLOUD,
    "passwordPolicyComplexity": OPENCLOUD,
    "corsOriginRestricted": OPENCLOUD,
    "demoUsersDisabled": OPENCLOUD,
    "versionDetection": OPENCLOUD,
    "addressParity": OPENCLOUD,
    "companionEditorHttps": OPENCLOUD,
    "debugPort": OPENCLOUD,
    "backendPortClosed": OPENCLOUD,
    "webEmbedMessageOriginRestricted": OPENCLOUD,
    "webEmbedDelegatedAuthenticationRestricted": OPENCLOUD,
    "versionCurrent": OPENCLOUD,
    "advisory": OPENCLOUD,
    # Whatever sits in front of it and terminates TLS.
    "hstsLongMaxAge": REVERSE_PROXY,
    "hstsPreload": REVERSE_PROXY,
    "hstsPreloadEligible": REVERSE_PROXY,
    "httpsEnforced": REVERSE_PROXY,
    "httpsAvailable": REVERSE_PROXY,
    "reverseProxyDetected": REVERSE_PROXY,
    "tlsHandshake": REVERSE_PROXY,
    "tlsTrusted": REVERSE_PROXY,
    "tlsProtocol": REVERSE_PROXY,
    "tlsCertificate": REVERSE_PROXY,
    "tlsDeprecatedProtocol": REVERSE_PROXY,
    "tlsHostname": REVERSE_PROXY,
    "tlsChain": REVERSE_PROXY,
    "tlsCertificateLifetime": REVERSE_PROXY,
    "tlsCipherSuite": REVERSE_PROXY,
    "tlsCertificatePolicy": REVERSE_PROXY,
    "tlsOcspStapling": REVERSE_PROXY,
    "tlsCertificateTransparency": REVERSE_PROXY,
    "tlsEarlyData": REVERSE_PROXY,
    "tlsAddressParity": REVERSE_PROXY,
    "companionAdminConsole": REVERSE_PROXY,
    "cookieSecure": REVERSE_PROXY,
    "cookieHttpOnly": REVERSE_PROXY,
    "cookieSameSite": REVERSE_PROXY,
    "cookiePrefix": REVERSE_PROXY,
    "traceMethodDisabled": REVERSE_PROXY,
    "forwardedHostIgnored": REVERSE_PROXY,
    "directoryListing": REVERSE_PROXY,
    "webfingerVersionDisclosure": REVERSE_PROXY,
    "securityTxtPublished": REVERSE_PROXY,
    "exposed": REVERSE_PROXY,
    "authentication": REVERSE_PROXY,
    "debugEndpoint": REVERSE_PROXY,
    "versionDisclosure": REVERSE_PROXY,
    # The OpenID Connect provider.
    "identityProviderDetected": IDENTITY_PROVIDER,
    "oidcPkceSupported": IDENTITY_PROVIDER,
    "oidcImplicitFlowDisabled": IDENTITY_PROVIDER,
    "oidcSigningAlgorithmStrong": IDENTITY_PROVIDER,
    "oidcEndpointsUseHttps": IDENTITY_PROVIDER,
    # The domain's zone.
    "tlsCaaRecord": DNS_ZONE,
    "tlsDnssec": DNS_ZONE,
}


@dataclass(frozen=True)
class SharedChange:
    """One edit that resolves several related findings at once."""

    id: str
    target: str
    title: str
    action: str
    members: frozenset[str]


_HEADERS = frozenset(header_names())

#: Changes that resolve more than one catalogued check. Keyed by catalogue id
#: through :func:`_shared_change_of`; a check belongs to at most one.
SHARED_CHANGES: tuple[SharedChange, ...] = (
    SharedChange(
        "securityHeaders",
        REVERSE_PROXY,
        "Send the missing security headers",
        "Add every missing header to the one block of response headers the "
        "reverse proxy sends for this site, then scan again.",
        _HEADERS | {"hstsLongMaxAge", "hstsPreload"},
    ),
    SharedChange(
        "certificate",
        REVERSE_PROXY,
        "Replace the certificate",
        "Serve a certificate from a publicly trusted authority that names "
        "this host, with its full chain, from an ACME client that renews it "
        "automatically.",
        frozenset(
            {
                "tlsTrusted",
                "tlsHostname",
                "tlsChain",
                "tlsCertificate",
                "tlsCertificateLifetime",
                "tlsCertificatePolicy",
                "tlsCertificateTransparency",
            }
        ),
    ),
    SharedChange(
        "tlsSettings",
        REVERSE_PROXY,
        "Modernise the TLS settings",
        "Restrict the TLS terminator to TLS 1.2 and 1.3 with forward-secret "
        "AEAD ciphers, enable OCSP stapling and leave early data off.",
        frozenset(
            {
                "tlsHandshake",
                "tlsProtocol",
                "tlsDeprecatedProtocol",
                "tlsCipherSuite",
                "tlsOcspStapling",
                "tlsEarlyData",
            }
        ),
    ),
    SharedChange(
        "https",
        REVERSE_PROXY,
        "Serve HTTPS and redirect plain HTTP to it",
        "Terminate TLS for this name and answer every plain-HTTP request with "
        "a permanent redirect to the HTTPS address.",
        frozenset({"httpsAvailable", "httpsEnforced"}),
    ),
    SharedChange(
        "cookies",
        REVERSE_PROXY,
        "Harden the cookie attributes",
        "Issue every cookie with Secure, HttpOnly and SameSite, and a "
        "__Host- prefix for the session cookie - at the proxy, or at the "
        "service that sets it.",
        frozenset({"cookieSecure", "cookieHttpOnly", "cookieSameSite", "cookiePrefix"}),
    ),
    SharedChange(
        "staticFiles",
        REVERSE_PROXY,
        "Stop serving the deployment directory",
        "Proxy every request to OpenCloud's own address instead of serving "
        "files from disk, and switch directory indexing off.",
        frozenset({"exposed", "directoryListing"}),
    ),
    SharedChange(
        "versionBanner",
        REVERSE_PROXY,
        "Stop announcing versions",
        "Strip or flatten version-bearing response headers and fields at the "
        "proxy (Nginx 'server_tokens off', Apache 'ServerTokens Prod').",
        frozenset({"versionDisclosure", "webfingerVersionDisclosure"}),
    ),
    SharedChange(
        "passwordPolicy",
        OPENCLOUD,
        "Enforce a password policy",
        "Set the OC_PASSWORD_POLICY_* variables together: a minimum length "
        "and the character classes a password must contain.",
        frozenset({"passwordPolicyEnforced", "passwordPolicyComplexity"}),
    ),
    SharedChange(
        "embedOrigins",
        OPENCLOUD,
        "Restrict the embed origins",
        "Set WEB_OPTION_EMBED_MESSAGES_ORIGIN and "
        "WEB_OPTION_EMBED_DELEGATE_AUTHENTICATION_ORIGIN to the exact trusted "
        "parent origin, or switch the embed integration off.",
        frozenset(
            {
                "webEmbedMessageOriginRestricted",
                "webEmbedDelegatedAuthenticationRestricted",
            }
        ),
    ),
    SharedChange(
        "upgrade",
        OPENCLOUD,
        "Update OpenCloud",
        "",
        frozenset({"versionCurrent", "advisory"}),
    ),
)

_SHARED_BY_MEMBER: dict[str, SharedChange] = {
    member: change for change in SHARED_CHANGES for member in change.members
}


def _root(finding: str) -> str:
    """The catalogue id a finding is explained under - its family, for a member."""
    if finding.startswith("advisory:"):
        return "advisory"
    return catalogue_id(finding) or finding


def target_of(finding: str) -> str:
    """
    Where the fix for a finding is made.

    A header nobody catalogued is still a header, and headers are set at the
    reverse proxy. Anything else this build cannot place is filed under
    OpenCloud, because that is where an operator starts looking - and a test
    makes sure no catalogued check ever relies on that.
    """
    root = _root(finding)
    if root in CHECK_TARGETS:
        return CHECK_TARGETS[root]
    if root in _HEADERS:
        return REVERSE_PROXY
    return OPENCLOUD


#: A finding the groups place: its id, and the plan step it is (0 when it is
#: not a step).
Finding = tuple[str, int]

#: Replays the rating with the given findings resolved. The second argument
#: says whether the update is among them.
RatingReplay = Callable[[frozenset[str], bool], int]


def _open_findings(
    result: Mapping[str, Any],
    steps: list[dict[str, Any]],
    blocked: list[dict[str, Any]],
) -> list[Finding]:
    """
    Every open finding somebody can act on, in plan order first.

    The plan lists only what holds the rating down. A missing header caps
    nothing but is still a line in the reverse proxy's configuration, and
    leaving it out would split one edit across two lists.
    """
    ignored = {str(name) for name in result.get("ignored") or () if isinstance(name, str)}
    seen = {str(step.get("id")) for step in blocked}
    found: list[Finding] = []

    def add(name: str, order: int = 0) -> None:
        if name in seen or name in ignored:
            return
        if order == 0 and not describe(name).actionable:
            return
        seen.add(name)
        found.append((name, order))

    for step in steps:
        add(str(step.get("id")), int(step.get("order") or 0))
    for entry in result.get("extraChecks") or ():
        if isinstance(entry, Mapping) and entry.get("passed") is False and not entry.get("ignored"):
            add(str(entry.get("id")))
    hardenings = result.get("hardenings")
    if isinstance(hardenings, Mapping):
        for name, enabled in hardenings.items():
            if enabled is False:
                add(str(name))
    setup = result.get("setup")
    if isinstance(setup, Mapping):
        https = setup.get("https")
        if isinstance(https, Mapping) and https.get("enforced") is False:
            add("httpsEnforced")
        headers = setup.get("headers")
        if isinstance(headers, Mapping):
            for name, present in headers.items():
                if present is False:
                    add(str(name))
    # An advisory is closed by the update, and only by it; there is no
    # update to group it under when the plan found none to recommend.
    if any(name == "versionCurrent" for name, _ in found):
        for entry in result.get("vulnerabilities") or ():
            if isinstance(entry, Mapping):
                identifier = entry.get("id") or entry.get("identifier")
                if identifier:
                    add(f"advisory:{identifier}")
    return found


def _change_of(finding: str, upgrade_action: str) -> tuple[str, str, str]:
    """The id, title and action of the edit that resolves a finding."""
    root = _root(finding)
    shared = _SHARED_BY_MEMBER.get(root)
    if shared is not None:
        return shared.id, shared.title, shared.action or upgrade_action
    note = describe(root)
    return root, note.title, note.remediation


def groups(
    result: Mapping[str, Any],
    steps: list[dict[str, Any]],
    blocked: list[dict[str, Any]],
    replay: RatingReplay,
) -> list[dict[str, Any]]:
    """
    The ``groups`` block of a remediation plan.

    One entry per place a change is made, in :data:`TARGETS` order and only
    where something is open. Each lists its ``changes``, the ones resolving
    the most findings first; each change names the ``findings`` it resolves,
    the plan ``steps`` among them and ``ratingAfter`` - the rating with that
    change alone made. ``ratingAfter`` on the group is the rating with every
    change in it made.
    """
    upgrade_action = next(
        (str(step.get("action") or "") for step in steps if step.get("id") == "versionCurrent"),
        "",
    )
    changes: dict[str, dict[str, Any]] = {}
    targets: dict[str, str] = {}
    for name, order in _open_findings(result, steps, blocked):
        change_id, title, action = _change_of(name, upgrade_action)
        targets.setdefault(change_id, target_of(name))
        change = changes.setdefault(
            change_id,
            {"id": change_id, "title": title, "action": action, "findings": [], "steps": []},
        )
        change["findings"].append(name)
        if order:
            change["steps"].append(order)

    def rating_after(findings: list[str]) -> int:
        resolved = frozenset(findings)
        return replay(resolved, "versionCurrent" in resolved)

    rendered: list[dict[str, Any]] = []
    for target, title in TARGETS.items():
        members = [change for key, change in changes.items() if targets[key] == target]
        if not members:
            continue
        for change in members:
            change["steps"].sort()
            change["resolvesSeveral"] = len(change["findings"]) > 1
            change["ratingAfter"] = rating_after(change["findings"])
        members.sort(
            key=lambda change: (
                -len(change["findings"]),
                min(change["steps"], default=10_000),
                change["id"],
            )
        )
        findings = [name for change in members for name in change["findings"]]
        rendered.append(
            {
                "target": target,
                "title": title,
                "findings": len(findings),
                "ratingAfter": rating_after(findings),
                "changes": members,
            }
        )
    return rendered


def summary(grouped: list[dict[str, Any]]) -> str:
    """One sentence naming the edits that close more than one finding."""
    combined = [
        change
        for group in grouped
        for change in group["changes"]
        if change["resolvesSeveral"]
    ]
    if not combined:
        return ""
    combined.sort(key=lambda change: -len(change["findings"]))
    listed = ", ".join(
        f"{change['title'].lower()} ({len(change['findings'])})"
        for change in combined[:3]
    )
    noun = "change resolves" if len(combined) == 1 else "changes resolve"
    return f"{len(combined)} {noun} several findings at once: {listed}."


__all__ = [
    "CHECK_TARGETS",
    "DNS_ZONE",
    "IDENTITY_PROVIDER",
    "OPENCLOUD",
    "REVERSE_PROXY",
    "SHARED_CHANGES",
    "TARGETS",
    "groups",
    "summary",
    "target_of",
]
