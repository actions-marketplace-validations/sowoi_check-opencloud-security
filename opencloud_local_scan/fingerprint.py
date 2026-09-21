"""
What the deployment is configured like, as digests rather than as settings.

A grade answers "is this instance in good shape". It does not answer "is this
still the same instance you looked at last week". A proxy was replaced, the
content security policy was rewritten, public links stopped requiring a
password and started requiring one again, the certificate moved to a
different issuer - none of that has to move a grade, and an operator who only
watches the grade will not see any of it.

This records a **configuration fingerprint**: five group digests - transport,
headers, sharing, authentication and proxy - and one digest over those five.
Two scans with the same group digest were looking at the same configuration
for that group; two that differ were not. That is the entire claim.

The rules that make it safe to publish and worth comparing:

* **Digests only, never the configuration.** A header value can carry
  internal host names, a discovery document can carry a tenant id, a
  capabilities document can carry a deployment's own vocabulary. Nothing here
  keeps any of it: every fact is hashed into its group and discarded, and the
  block that reaches the result document is five hex strings, a count of the
  facts behind each, and nothing else. A reader learns *that* sharing changed,
  never *what* it is set to.
* **A group is a question an operator asks.** "Did TLS change?" is a useful
  question; "did fact 37 change?" is not. Grouping is what turns a digest
  into a sentence, which is why there are five of them rather than one.
* **What the scan settings decide is never a fact.** A probe that was turned
  off this time must not look like a deployment that changed. Each group
  therefore carries a second digest, its **scope**: which facts it was able
  to look at, without their values. Two groups are compared only when their
  scopes match, so a scan that stopped inspecting TLS reports "not
  comparable", never drift. A group with nothing at all to hash is ``none``.
* **Only what the deployment decides.** A certificate's expiry date moves on
  every renewal and says nothing about how the instance is configured, so the
  transport group hashes the issuer, the key and the protocols and leaves the
  serial number, the validity dates and the fingerprint alone. A fingerprint
  that changed every ninety days would be one an operator learns to ignore.
* **It never changes a grade.** Nothing here reaches the rating, the
  severities, the alert line or the exit code. Drift is a fact to report, not
  a finding to alert on - the checks decide what is wrong, this only says
  what moved.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

#: The block's own version, so a reader can tell this shape from a later one.
FINGERPRINT_SCHEMA = 1

#: What a group with nothing to hash records. A scan that could not look at
#: TLS and a deployment with no TLS at all both land here, which is why a
#: comparison treats it as "not measured" rather than as a value.
NOT_MEASURED = "none"

#: Transport security: whether HTTPS is used and enforced, the protocols and
#: ciphers that were negotiated, and who issued the certificate.
TLS = "tls"
#: The security headers the instance sends, by name and by value.
HEADERS = "headers"
#: What the instance allows to be shared, and under what conditions.
SHARING = "sharing"
#: How someone signs in: the challenge, the provider and its parameters.
AUTHENTICATION = "authentication"
#: What sits in front of the instance and how it advertises itself.
PROXY = "proxy"

GROUPS: tuple[str, ...] = (TLS, HEADERS, SHARING, AUTHENTICATION, PROXY)

#: The headers whose *values* the header group hashes. The set is fixed here
#: rather than taken from the response, so that a deployment adding an
#: unrelated header - a cache tag, a request id - does not read as a change
#: in its security configuration.
FINGERPRINTED_HEADERS: tuple[str, ...] = (
    "Content-Security-Policy",
    "Cross-Origin-Embedder-Policy",
    "Cross-Origin-Opener-Policy",
    "Cross-Origin-Resource-Policy",
    "Permissions-Policy",
    "Referrer-Policy",
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "X-Permitted-Cross-Domain-Policies",
    "X-Robots-Tag",
    "X-XSS-Protection",
)

#: The hardening flags that belong to each group. A hardening is a decision
#: the operator made about the deployment, which is exactly what a
#: configuration fingerprint is for.
_HARDENING_GROUPS: dict[str, str] = {
    "hstsLongMaxAge": TLS,
    "hstsPreload": TLS,
    "cspWithoutUnsafeInline": HEADERS,
    "publicLinkPasswordEnforced": SHARING,
    "publicLinkExpirationEnforced": SHARING,
    "userEnumerationRestricted": SHARING,
    "basicAuthDisabled": AUTHENTICATION,
    "passwordPolicyEnforced": AUTHENTICATION,
    "passwordPolicyComplexity": AUTHENTICATION,
    "oidcPkceSupported": AUTHENTICATION,
    "oidcImplicitFlowDisabled": AUTHENTICATION,
    "oidcSigningAlgorithmStrong": AUTHENTICATION,
    "oidcEndpointsUseHttps": AUTHENTICATION,
}


def _normalise(value: Any) -> str:
    """
    One fact, as a string that says the same thing every time.

    Case and runs of whitespace are removed because a header rewritten with
    different spacing is the same policy, and a fingerprint that disagreed
    would report a change that nobody made.
    """
    if isinstance(value, bool) or value is None:
        return {True: "true", False: "false", None: "null"}[value]
    return " ".join(str(value).split()).lower()


def _digest(facts: Sequence[tuple[str, str]]) -> str:
    """A digest over a group's facts, or ``none`` when it has none."""
    if not facts:
        return NOT_MEASURED
    canonical = json.dumps(sorted(facts), separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _scope(facts: Sequence[tuple[str, str]]) -> str:
    """
    A digest over which facts a group looked at, ignoring what they said.

    This is what makes a comparison honest about probes: two scans that
    looked at different things are not two scans that saw a difference.
    """
    if not facts:
        return NOT_MEASURED
    canonical = json.dumps(sorted(key for key, _ in facts), separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class _Facts:
    """The facts collected for each group while a fingerprint is built."""

    def __init__(self) -> None:
        self.groups: dict[str, list[tuple[str, str]]] = {group: [] for group in GROUPS}

    def add(self, group: str, key: str, value: Any) -> None:
        """
        Record one fact, unless there is nothing to record.

        ``None`` is dropped rather than hashed: it is what a probe that did
        not run leaves behind, and hashing it would make "not measured" a
        value that differs from every measured one.
        """
        if value is None:
            return
        self.groups[group].append((key, _normalise(value)))


def _dig(source: Any, *path: str) -> Any:
    """Walk nested mappings, returning ``None`` at the first thing that is not one."""
    current = source
    for key in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _transport_facts(facts: _Facts, result: Mapping[str, Any]) -> None:
    """HTTPS, the negotiated connection, and who issued the certificate."""
    https = _dig(result, "setup", "https")
    if isinstance(https, Mapping):
        facts.add(TLS, "https.used", https.get("used"))
        facts.add(TLS, "https.enforced", https.get("enforced"))

    for key, inspection in _tls_endpoints(result):
        if not isinstance(inspection, Mapping) or not inspection.get("reachable"):
            continue
        facts.add(TLS, f"{key}.protocol", inspection.get("protocol"))
        facts.add(TLS, f"{key}.cipher", inspection.get("cipher"))
        facts.add(TLS, f"{key}.chainLength", inspection.get("chainLength"))
        facts.add(
            TLS,
            f"{key}.deprecatedAccepted",
            ",".join(sorted(str(item) for item in inspection.get("deprecatedProtocolsAccepted") or [])),
        )
        certificate = inspection.get("certificate")
        if isinstance(certificate, Mapping):
            # The issuer, the key and the signature - what a deployment
            # chose. Not the serial, the dates or the alternative names,
            # which a routine renewal rewrites without anyone deciding
            # anything.
            facts.add(TLS, f"{key}.issuer", certificate.get("issuer"))
            facts.add(TLS, f"{key}.keyType", certificate.get("keyType"))
            facts.add(TLS, f"{key}.keyBits", certificate.get("keyBits"))
            facts.add(TLS, f"{key}.signature", certificate.get("signatureAlgorithm"))
            facts.add(TLS, f"{key}.selfSigned", certificate.get("selfSigned"))


def _tls_endpoints(result: Mapping[str, Any]) -> list[tuple[str, Any]]:
    """Every inspected endpoint, named so that two scans line them up."""
    endpoints: list[tuple[str, Any]] = [("tls", result.get("tls"))]
    by_address = result.get("tlsByAddress")
    if isinstance(by_address, Mapping):
        endpoints.extend(
            (f"tls.{family}", inspection) for family, inspection in sorted(by_address.items())
        )
    return endpoints


def _header_facts(facts: _Facts, headers: Mapping[str, str] | None) -> None:
    """
    The security headers, by value where there is one.

    The values are hashed, never kept: a content security policy names the
    origins a deployment trusts, which is its business and not a report's.
    """
    if headers is None:
        return
    for name in FINGERPRINTED_HEADERS:
        value = headers.get(name)
        facts.add(HEADERS, name, value if value is not None else "absent")


def _sharing_facts(facts: _Facts, capabilities: Mapping[str, Any] | None) -> None:
    """What the instance publishes about sharing, as one digestible fact."""
    sharing = _dig(capabilities, "capabilities", "files_sharing")
    if isinstance(sharing, Mapping):
        # The whole published sharing subtree, canonically. Naming individual
        # keys here would silently stop noticing a setting that a later
        # OpenCloud release adds.
        facts.add(
            SHARING,
            "filesSharing",
            json.dumps(sharing, sort_keys=True, separators=(",", ":"), default=str),
        )


def _authentication_facts(
    facts: _Facts, result: Mapping[str, Any], capabilities: Mapping[str, Any] | None
) -> None:
    """Who issues the identity, how it is challenged, and what it demands."""
    provider = result.get("identityProvider")
    if isinstance(provider, Mapping) and provider.get("detected"):
        facts.add(AUTHENTICATION, "idp.external", provider.get("external"))
        facts.add(AUTHENTICATION, "idp.issuer", provider.get("issuer"))
        facts.add(AUTHENTICATION, "idp.vendor", provider.get("vendor"))

    password = _dig(capabilities, "capabilities", "core", "password_policy")
    if isinstance(password, Mapping):
        facts.add(
            AUTHENTICATION,
            "passwordPolicy",
            json.dumps(password, sort_keys=True, separators=(",", ":"), default=str),
        )


def _proxy_facts(facts: _Facts, result: Mapping[str, Any]) -> None:
    """What answers in front of the instance, and what it offers."""
    proxy = result.get("reverseProxy")
    if isinstance(proxy, Mapping):
        facts.add(PROXY, "detected", proxy.get("detected"))
        # The vendor, not the evidence: the evidence quotes a server banner,
        # which carries a build number that moves with every patch release.
        facts.add(PROXY, "vendor", proxy.get("vendor"))

    services = result.get("alternativeServices")
    if isinstance(services, Mapping):
        facts.add(PROXY, "altSvc.advertised", services.get("advertised"))
        facts.add(PROXY, "altSvc.http3", services.get("http3"))
        entries = services.get("entries")
        if isinstance(entries, Sequence) and not isinstance(entries, str):
            facts.add(
                PROXY,
                "altSvc.protocols",
                ",".join(sorted(str(entry) for entry in entries)),
            )


def _hardening_facts(facts: _Facts, result: Mapping[str, Any]) -> None:
    """The hardening decisions, filed under the group each one belongs to."""
    hardenings = result.get("hardenings")
    if not isinstance(hardenings, Mapping):
        return
    for name, value in sorted(hardenings.items()):
        group = _HARDENING_GROUPS.get(str(name))
        if group is not None:
            facts.add(group, f"hardening.{name}", value)


def build(
    result: Mapping[str, Any],
    *,
    headers: Mapping[str, str] | None = None,
    capabilities: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    The ``configuration`` block for a result document.

    ``result`` is the document as the scan has assembled it; ``headers`` and
    ``capabilities`` are the two things the scan saw that the document keeps
    only the verdicts of. Both are optional, and a fingerprint built without
    them records the groups they feed as not measured rather than as empty.
    """
    facts = _Facts()
    _transport_facts(facts, result)
    _header_facts(facts, headers)
    _sharing_facts(facts, capabilities)
    _authentication_facts(facts, result, capabilities)
    _proxy_facts(facts, result)
    _hardening_facts(facts, result)

    groups = {
        group: {
            "digest": _digest(facts.groups[group]),
            # Which facts this group could look at, so that a later
            # comparison can tell "configured differently" from "looked at
            # differently".
            "scope": _scope(facts.groups[group]),
            "facts": len(facts.groups[group]),
        }
        for group in GROUPS
    }
    return {
        "schema": FINGERPRINT_SCHEMA,
        # One value to watch when the five are more than a reader wants.
        # Built from the group digests, so it moves when any of them does.
        "digest": _digest([(group, str(groups[group]["digest"])) for group in GROUPS]),
        "groups": groups,
    }


def fingerprint_of(result: Mapping[str, Any]) -> dict[str, Any] | None:
    """
    The configuration block of a result document, or nothing when it has none.

    A report written before this block existed is not a report of a
    deployment that never changes; it is a report that cannot say. Every
    reader asks here rather than reaching for the key, so that the two stay
    different answers.
    """
    block = result.get("configuration")
    if not isinstance(block, Mapping) or "schema" not in block:
        return None
    if not isinstance(block.get("groups"), Mapping):
        return None
    return dict(block)


def digests(result: Mapping[str, Any]) -> dict[str, str]:
    """
    Each group as one opaque string, ``<scope>:<digest>``.

    One string per group is what a baseline file, a webhook receiver and a
    comparison all want to store and compare, and keeping the scope inside it
    means none of them can compare two groups that looked at different
    things. Empty for a report that carries no fingerprint.
    """
    block = fingerprint_of(result)
    if block is None:
        return {}
    groups = block["groups"]
    found: dict[str, str] = {}
    for group in GROUPS:
        entry = groups.get(group)
        if not isinstance(entry, Mapping) or not isinstance(entry.get("digest"), str):
            continue
        scope = entry.get("scope")
        found[group] = f"{scope if isinstance(scope, str) else NOT_MEASURED}:{entry['digest']}"
    return found


def _parts(value: str) -> tuple[str, str]:
    """A stored ``<scope>:<digest>`` string, split. Anything else is unmeasured."""
    scope, _, digest = value.partition(":")
    if not digest:
        return NOT_MEASURED, NOT_MEASURED
    return scope, digest


def drift(before: Mapping[str, str], after: Mapping[str, str]) -> tuple[str, ...]:
    """
    The groups whose configuration is not the one it was, in group order.

    A group is only compared when both scans measured it and both looked at
    the same facts. Silence and a narrower scan are not changes, and
    reporting them as ones would make every scan with a probe turned off look
    like a redeployment.
    """
    drifted = []
    for group in GROUPS:
        before_scope, before_digest = _parts(before.get(group, ""))
        after_scope, after_digest = _parts(after.get(group, ""))
        if NOT_MEASURED in {before_digest, after_digest}:
            continue
        if before_scope != after_scope:
            continue
        if before_digest != after_digest:
            drifted.append(group)
    return tuple(drifted)


def incomparable(before: Mapping[str, str], after: Mapping[str, str]) -> tuple[str, ...]:
    """
    The groups the two scans looked at differently, so cannot be compared.

    Reported rather than ignored: a reader who is told nothing drifted needs
    to know which groups that statement was not about.
    """
    return tuple(
        group
        for group in GROUPS
        if NOT_MEASURED not in {_parts(before.get(group, ""))[1], _parts(after.get(group, ""))[1]}
        and _parts(before.get(group, ""))[0] != _parts(after.get(group, ""))[0]
    )


def unmeasured(digests_now: Mapping[str, str]) -> tuple[str, ...]:
    """The groups this scan had nothing to fingerprint, in group order."""
    return tuple(
        group
        for group in GROUPS
        if _parts(digests_now.get(group, ""))[1] == NOT_MEASURED
    )
