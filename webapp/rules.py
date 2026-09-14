"""
Every rating rule and every abuse rule this deployment enforces, as it runs.

The operator area's rules tab reads this. The configuration tab answers "what
is each variable set to"; this answers the question an operator actually has
when a visitor writes in: *what will this service do to that request, and why
did that instance get that grade?*

**Nothing here is a second copy of a rule.** Every number is read from the
:class:`~webapp.settings.WebSettings` this process runs with or from the
constant the enforcing code itself uses - the severity ceilings from the
scanner, the refused names from :mod:`webapp.ssrf`, the escalation from
:class:`~webapp.ratelimit.ProbePolicy`, the scan's own flags from
:func:`webapp.runner.scanner_settings_for`. A page that described a limit the
code no longer had would be worse than no page, because it is the one an
operator would believe.

**It names nothing anybody submitted.** Counts and configured lists only, as
on the rest of the area (ADR 0035): the operator's own exclusions and approved
instances are shown because the operator wrote them, never a target, a uuid,
a fingerprint or a client.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .approval import APPROVAL_LABEL, approval_value
from .catalog import DEFAULT_RELEASE_TRACK, allowed_waivers, severity_caps
from .ratelimit import (
    BLOCK_ESCALATION_FACTOR,
    CREDENTIAL_ATTEMPT_LIMIT,
    CREDENTIAL_ATTEMPT_WINDOW_SECONDS,
    probe_policy,
)
from .runner import scanner_settings_for
from .settings import DAILY_WINDOW_SECONDS, WebSettings
from .ssrf import (
    BLOCKED_ADDRESSES,
    BLOCKED_HOSTNAMES,
    BLOCKED_NETWORKS,
    BLOCKED_SUFFIXES,
    SUSPICIOUS_REJECTIONS,
    WILDCARD_DNS_SUFFIXES,
    Target,
)
from .workflows import SUBMIT_MAX_ATTEMPTS, SUBMIT_MAX_WAIT_SECONDS

#: The groups, in the order the tab shows them.
GROUPS = ("submissions", "probe", "targets", "scanner", "operator")

#: The escalation is shown up to this many steps; past the ceiling every
#: further block is the same length, so there is nothing more to say.
MAX_ESCALATION_STEPS = 6

#: A target that is never contacted, only used to ask the runner which flags
#: a scan from this deployment is built with.
_SAMPLE_TARGET = Target(
    hostname="opencloud.example.com", port=443, scheme="https", path="", addresses=()
)


def duration(seconds: int) -> str:
    """A length of time in the units every catalogue shares: s, min, h, d."""
    if seconds <= 0:
        return "0 s"
    if seconds % 86400 == 0 and seconds > 2 * 86400:
        return f"{seconds // 86400} d"
    if seconds % 3600 == 0:
        return f"{seconds // 3600} h"
    if seconds > 3600:
        minutes = (seconds % 3600) // 60
        return f"{seconds // 3600} h {minutes} min" if minutes else f"{seconds // 3600} h"
    if seconds % 60 == 0:
        return f"{seconds // 60} min"
    if seconds > 60:
        return f"{seconds // 60} min {seconds % 60} s"
    return f"{seconds} s"


@dataclass(frozen=True)
class Rule:
    """One enforced rule: whether it is on, and the values its sentence names."""

    key: str
    """``admin.rules.rule.<key>.title`` and ``.body`` in the catalogues."""
    on: bool
    params: Mapping[str, str] = field(default_factory=dict)
    items: tuple[str, ...] = ()
    """Literal values shown as code: names, suffixes, addresses."""
    labels: tuple[str, ...] = ()
    """Catalogue keys shown as a list of sentences."""
    variables: tuple[str, ...] = ()
    """The ``COS_WEB_`` variables that govern it, without the prefix."""


def _submission_rules(settings: WebSettings) -> tuple[Rule, ...]:
    return (
        Rule(
            "client_limit",
            settings.ip_rate_limit > 0,
            {
                "limit": str(settings.ip_rate_limit),
                "window": duration(settings.ip_rate_window),
                "ipv6": str(settings.client_ipv6_prefix),
            },
            variables=("IP_RATE_LIMIT", "IP_RATE_WINDOW", "CLIENT_IPV6_PREFIX"),
        ),
        Rule(
            "daily_cap",
            settings.daily_scan_limit > 0,
            {
                "limit": str(settings.daily_scan_limit),
                "window": duration(DAILY_WINDOW_SECONDS),
            },
            variables=("DAILY_SCAN_LIMIT",),
        ),
        Rule(
            "target_cooldown",
            settings.target_cooldown > 0,
            {"cooldown": duration(settings.target_cooldown)},
            variables=("TARGET_COOLDOWN",),
        ),
        Rule(
            "batch",
            True,
            {"limit": str(settings.max_batch_targets)},
            variables=("MAX_BATCH_TARGETS",),
        ),
        Rule(
            "queue",
            True,
            {"workers": str(settings.max_workers)},
            variables=("MAX_WORKERS",),
        ),
        Rule(
            "agent_wait",
            True,
            {"wait": duration(SUBMIT_MAX_WAIT_SECONDS), "attempts": str(SUBMIT_MAX_ATTEMPTS)},
        ),
    )


def escalation(settings: WebSettings) -> tuple[str, ...]:
    """The length of each successive block, until the ceiling stops it growing."""
    policy = probe_policy(settings)
    steps: list[str] = []
    previous = -1
    for repeat in range(1, MAX_ESCALATION_STEPS + 1):
        length = policy.duration(repeat)
        if length == previous:
            break
        steps.append(duration(length))
        previous = length
        if settings.probe_repeat_window <= 0:
            break
    return tuple(steps)


def _probe_rules(settings: WebSettings) -> tuple[Rule, ...]:
    enabled = settings.probe_limit > 0
    return (
        Rule(
            "probe_block",
            enabled,
            {
                "limit": str(settings.probe_limit),
                "window": duration(settings.probe_window),
                "block": duration(settings.probe_block),
            },
            variables=("PROBE_LIMIT", "PROBE_WINDOW", "PROBE_BLOCK"),
        ),
        Rule(
            "probe_escalation",
            enabled and settings.probe_repeat_window > 0,
            {
                "steps": " → ".join(escalation(settings)),
                "factor": str(BLOCK_ESCALATION_FACTOR),
                "repeat": duration(settings.probe_repeat_window),
            },
            variables=("PROBE_BLOCK_MAX", "PROBE_REPEAT_WINDOW"),
        ),
        Rule(
            "probe_network",
            enabled,
            {"ipv4": str(settings.probe_ipv4_prefix), "ipv6": str(settings.client_ipv6_prefix)},
            variables=("PROBE_IPV4_PREFIX", "CLIENT_IPV6_PREFIX"),
        ),
        Rule("strike_scans", enabled),
        Rule(
            "strike_refusals",
            enabled,
            labels=tuple(
                f"admin.rules.refusal.{key.rsplit('.', 1)[1]}"
                for key in sorted(SUSPICIOUS_REJECTIONS)
            ),
        ),
    )


def _target_rules(settings: WebSettings, exclusions: int | None) -> tuple[Rule, ...]:
    guarded = not settings.allow_private_targets
    approval = approval_value(settings)
    return (
        Rule(
            "private_addresses",
            guarded,
            items=tuple(str(network) for network in BLOCKED_NETWORKS),
            variables=("ALLOW_PRIVATE_TARGETS",),
        ),
        Rule(
            "internal_names",
            guarded,
            items=tuple(sorted(BLOCKED_HOSTNAMES)) + BLOCKED_SUFFIXES
            + tuple(str(address) for address in sorted(BLOCKED_ADDRESSES, key=str)),
        ),
        Rule("wildcard_dns", guarded, items=WILDCARD_DNS_SUFFIXES),
        Rule(
            "dns_consistency",
            guarded and settings.dns_consistency_check,
            variables=("DNS_CONSISTENCY_CHECK",),
        ),
        Rule("redirects", True),
        Rule(
            "exclusions",
            bool(exclusions),
            {"count": "?" if exclusions is None else str(exclusions)},
            variables=("BLOCKED_TARGETS",),
        ),
        Rule(
            "allowed_hosts",
            bool(settings.extra_hosts_allowed),
            items=settings.extra_hosts_allowed,
            variables=("ALLOWED_HOSTS",),
        ),
        Rule(
            "approval",
            settings.require_approval,
            {
                "count": str(len(settings.approved_targets)),
                "record": (
                    f'{APPROVAL_LABEL}.<host> TXT "{approval}"'
                    if settings.require_approval and settings.approval_dns and approval
                    else "-"
                ),
            },
            items=settings.approved_targets,
            variables=("REQUIRE_APPROVAL", "APPROVED_TARGETS", "APPROVAL_DNS"),
        ),
    )


def _scanner_rules(settings: WebSettings) -> tuple[Rule, ...]:
    scan = scanner_settings_for(_SAMPLE_TARGET, (), settings)
    return (
        Rule("stop_when_not_opencloud", scan.stop_when_not_opencloud),
        Rule("single_address", not scan.check_all_addresses),
        Rule("no_port_scan", not scan.check_debug_ports, variables=("CHECK_DEBUG_PORTS",)),
        Rule(
            "load",
            True,
            {
                "concurrency": str(scan.workers),
                "timeout": duration(scan.timeout),
                "job": duration(settings.job_timeout),
            },
            variables=("SCAN_CONCURRENCY", "SCAN_TIMEOUT", "JOB_TIMEOUT"),
        ),
    )


def _operator_rules(settings: WebSettings) -> tuple[Rule, ...]:
    return (
        Rule(
            "purge_attempts",
            bool(settings.purge_token),
            {
                "limit": str(CREDENTIAL_ATTEMPT_LIMIT),
                "window": duration(CREDENTIAL_ATTEMPT_WINDOW_SECONDS),
            },
            variables=("PURGE_TOKEN",),
        ),
        Rule(
            "admin_refresh",
            settings.admin_refresh_cooldown > 0,
            {"cooldown": duration(settings.admin_refresh_cooldown)},
            variables=("ADMIN_REFRESH_COOLDOWN",),
        ),
    )


def enforcement_groups(
    settings: WebSettings, exclusions: int | None
) -> tuple[tuple[str, tuple[Rule, ...]], ...]:
    """Every abuse and target rule, grouped in display order.

    ``exclusions`` is how many entries the effective exclusion list holds, or
    ``None`` when the store did not answer - shown as unknown rather than as
    none, which would read as "nothing is excluded".
    """
    built = {
        "submissions": _submission_rules(settings),
        "probe": _probe_rules(settings),
        "targets": _target_rules(settings, exclusions),
        "scanner": _scanner_rules(settings),
        "operator": _operator_rules(settings),
    }
    return tuple((group, built[group]) for group in GROUPS)


@dataclass(frozen=True)
class RatingRules:
    """How a grade is decided on this deployment."""

    caps: tuple[tuple[str, int, str], ...]
    extra_checks_rated: bool
    waivers: int
    default_track: str


def rating_rules(settings: WebSettings) -> RatingRules:
    """The ceilings the scanner applies and the flags this deployment scans with."""
    scan = scanner_settings_for(_SAMPLE_TARGET, (), settings)
    return RatingRules(
        caps=severity_caps(),
        extra_checks_rated=scan.extra_checks and scan.extra_checks_affect_rating,
        waivers=len(allowed_waivers()),
        default_track=DEFAULT_RELEASE_TRACK,
    )
