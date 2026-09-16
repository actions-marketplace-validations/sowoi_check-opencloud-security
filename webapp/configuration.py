"""
Every ``COS_WEB_*`` variable, and how this process has it set.

The operator area's configuration tab reads this. It answers the question an
operator otherwise answers by opening the compose file, the ``.env`` beside
it and whatever the orchestrator injected, and hoping those three agree with
what the container actually started with: *what is this service running
with?*

Three rules shape it.

**The value shown is the one in effect.** It is read off the
:class:`~webapp.settings.WebSettings` this process was built with, after the
parsing, clamping and fallbacks :meth:`WebSettings.from_env` applies - so a
``COS_WEB_SCAN_TIMEOUT=abc`` shows the default it fell back to rather than
the typo, next to a note that the variable *was* set. The environment is
consulted only to say where a value came from.

**A credential is never rendered.** A token, a key, a salt or the password in
the Redis URL is reported as set or not set and nothing more. The area is
signed in, but a page is also a screenshot, a browser cache and a screen
share, and none of those should be able to leak what the proxy secret or the
erasure token is.

**The list cannot drift from the code.** :data:`VARIABLES` is written out
rather than discovered, because each entry also needs a group and a verdict
on whether it is secret - and ``tests/test_webapp_admin_configuration.py``
records every name ``from_env`` actually reads and fails when the two
disagree. The description and documented default come from the table in
``docs/webapp.md``, extracted at build time into
:mod:`webapp.environment_reference`.

This is the web service's own environment. OpenCloud's configuration is not
visible to this process and is not shown; neither is the worker's, which
reads the same variables in its own container and should be given the same
values.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from .environment_reference import REFERENCE
from .settings import ENV_PREFIX, WebSettings

#: Variables whose names follow a pattern rather than being fixed.
ENCRYPTION_KEY_PREFIX = f"{ENV_PREFIX}ENCRYPTION_KEY_"

#: Read by the application module rather than by the settings, because the
#: templates have to be found before any settings exist.
FRONTEND_DIR = "FRONTEND_DIR"


@dataclass(frozen=True)
class Variable:
    """One configurable variable: where it lands, and how it may be shown."""

    name: str
    """Without the ``COS_WEB_`` prefix."""
    group: str
    field: str | None = None
    """The :class:`WebSettings` attribute it becomes; ``None`` if it has none."""
    secret: bool = False
    """Reported as set or not set, never by value."""

    @property
    def env_name(self) -> str:
        return f"{ENV_PREFIX}{self.name}"


# The groups, in the order the tab shows them.
GROUPS = (
    "storage",
    "scanning",
    "targets",
    "limits",
    "approval",
    "network",
    "reference",
    "interfaces",
    "mcp_auth",
    "admin",
    "audit",
    "protection",
    "frontend",
)

VARIABLES: tuple[Variable, ...] = (
    # Where state lives and how much work runs at once.
    Variable("REDIS_URL", "storage", "redis_url"),
    Variable("RESULT_TTL", "storage", "result_ttl"),
    Variable("COMPARISON_TTL", "storage", "comparison_ttl"),
    Variable("MAX_WORKERS", "storage", "max_workers"),
    Variable("JOB_TIMEOUT", "storage", "job_timeout"),
    # How one scan behaves against the instance.
    Variable("SCAN_CONCURRENCY", "scanning", "scan_concurrency"),
    Variable("SCAN_TIMEOUT", "scanning", "scan_timeout"),
    Variable("VERIFY_TLS", "scanning", "verify_tls"),
    Variable("CHECK_DEBUG_PORTS", "scanning", "check_debug_ports"),
    Variable("IPV6_ENABLED", "scanning", "ipv6_enabled"),
    # What may be scanned at all.
    Variable("ALLOW_PRIVATE_TARGETS", "targets", "allow_private_targets"),
    Variable("ALLOWED_HOSTS", "targets", "extra_hosts_allowed"),
    Variable("BLOCKED_TARGETS", "targets", "blocked_targets"),
    Variable("DNS_CONSISTENCY_CHECK", "targets", "dns_consistency_check"),
    # How often, and what earns a block.
    Variable("IP_RATE_LIMIT", "limits", "ip_rate_limit"),
    Variable("IP_RATE_WINDOW", "limits", "ip_rate_window"),
    Variable("TARGET_COOLDOWN", "limits", "target_cooldown"),
    Variable("DAILY_SCAN_LIMIT", "limits", "daily_scan_limit"),
    Variable("MAX_BATCH_TARGETS", "limits", "max_batch_targets"),
    Variable("PROBE_LIMIT", "limits", "probe_limit"),
    Variable("PROBE_WINDOW", "limits", "probe_window"),
    Variable("PROBE_BLOCK", "limits", "probe_block"),
    Variable("PROBE_BLOCK_MAX", "limits", "probe_block_max"),
    Variable("PROBE_REPEAT_WINDOW", "limits", "probe_repeat_window"),
    Variable("PROBE_IPV4_PREFIX", "limits", "probe_ipv4_prefix"),
    Variable("CLIENT_IPV6_PREFIX", "limits", "client_ipv6_prefix"),
    Variable("RATE_LIMIT_SALT", "limits", "rate_limit_salt", secret=True),
    # Whether a target has to be approved first.
    Variable("REQUIRE_APPROVAL", "approval", "require_approval"),
    Variable("APPROVED_TARGETS", "approval", "approved_targets"),
    Variable("APPROVAL_DNS", "approval", "approval_dns"),
    # Where the service is reached, and through what.
    Variable("PUBLIC_BASE_URL", "network", "public_base_url"),
    Variable("TRUST_FORWARDED_FOR", "network", "trust_forwarded_for"),
    Variable("TRUSTED_PROXY_HOPS", "network", "trusted_proxy_hops"),
    Variable("INDEX_META_TAG", "network", "index_meta_tags"),
    Variable("ALLOW_INDEXING", "network", "allow_indexing"),
    # What the ratings are measured against.
    Variable("RELEASES_MODE", "reference", "releases_mode"),
    Variable("RELEASES_TOKEN", "reference", "releases_token", secret=True),
    Variable("SCHEDULE_REFRESH", "reference", "schedule_refresh"),
    Variable("SCHEDULE_REFRESH_URL", "reference", "schedule_refresh_url"),
    Variable("SCHEDULE_REFRESH_HOUR", "reference", "schedule_refresh_hour"),
    Variable("ADVISORY_REFRESH", "reference", "advisory_refresh"),
    Variable("ADVISORY_REFRESH_URL", "reference", "advisory_refresh_url"),
    # The optional ways in besides the form.
    Variable("ENABLE_DOCS", "interfaces", "enable_docs"),
    Variable("ENABLE_MCP", "interfaces", "enable_mcp"),
    Variable("MCP_ALLOWED_HOSTS", "interfaces", "mcp_allowed_hosts"),
    Variable("MCP_MAX_CONCURRENT_WAITS", "interfaces", "mcp_max_concurrent_waits"),
    Variable("WEBHOOK_SECRET", "interfaces", "webhook_secret", secret=True),
    # Who may use /mcp.
    Variable("MCP_AUTH_ENABLED", "mcp_auth", "mcp_auth_enabled"),
    Variable("MCP_AUTH_ISSUER", "mcp_auth", "mcp_auth_issuer"),
    Variable("MCP_AUTH_AUDIENCE", "mcp_auth", "mcp_auth_audience"),
    Variable("MCP_AUTH_JWKS_URL", "mcp_auth", "mcp_auth_jwks_url"),
    Variable("MCP_AUTH_RESOURCE_URL", "mcp_auth", "mcp_auth_resource_url"),
    Variable("MCP_AUTH_SCOPES", "mcp_auth", "mcp_auth_scopes"),
    # This area.
    Variable("ADMIN_ENABLED", "admin", "admin_enabled"),
    Variable("ADMIN_PROXY_SECRET", "admin", "admin_proxy_secret", secret=True),
    Variable("ADMIN_USERS", "admin", "admin_users"),
    Variable("ADMIN_SIGN_OUT_URL", "admin", "admin_sign_out_url"),
    Variable("ADMIN_AUDIT_BUFFER", "admin", "admin_audit_buffer"),
    Variable("ADMIN_REFRESH_COOLDOWN", "admin", "admin_refresh_cooldown"),
    # The trail.
    Variable("AUDIT_LOG", "audit", "audit_log"),
    Variable("AUDIT_LOG_TARGETS", "audit", "audit_log_targets"),
    Variable("AUDIT_SALT", "audit", "audit_salt", secret=True),
    Variable("AUDIT_LOG_FILE", "audit", "audit_log_file"),
    Variable("AUDIT_LOG_MAX_BYTES", "audit", "audit_log_max_bytes"),
    Variable("AUDIT_LOG_BACKUPS", "audit", "audit_log_backups"),
    Variable("AUDIT_LOG_ROTATION", "audit", "audit_log_rotation"),
    # Erasure, signatures and encryption at rest.
    Variable("PURGE_TOKEN", "protection", "purge_token", secret=True),
    Variable("PURGE_SIGNING_KEY", "protection", "purge_signing_key", secret=True),
    Variable("EXPORT_SIGNING_KEY", "protection", "export_signing_key", secret=True),
    Variable("ENCRYPT_RESULTS", "protection", "encrypt_results"),
    Variable("ENCRYPTION_KEY_<n>", "protection", "encryption_keys", secret=True),
    # Where the pages come from.
    Variable(FRONTEND_DIR, "frontend"),
)

VARIABLES_BY_NAME = {variable.name: variable for variable in VARIABLES}


def _redact_url(value: str) -> str:
    """A URL with any password replaced, so the rest of it can still be read."""
    parts = urlsplit(value)
    if not parts.password:
        return value
    user = parts.username or ""
    host = parts.hostname or ""
    if ":" in host:
        host = f"[{host}]"
    port = f":{parts.port}" if parts.port else ""
    netloc = f"{user}:******@{host}{port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def _display(value: Any) -> str | None:
    """How an effective value reads on the page; ``None`` for no value at all."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (tuple, list)):
        items = [
            f"{item.name}={item.content}" if hasattr(item, "content") else str(item)
            for item in value
        ]
        return "; ".join(items) if items else None
    text = str(value)
    return text if text else None


def _is_set(env_name: str, environ: Mapping[str, str]) -> bool:
    """Whether the environment gives this a value, the way ``from_env`` reads it."""
    return bool((environ.get(env_name) or "").strip())


@dataclass(frozen=True)
class Row:
    """One variable as the tab shows it."""

    name: str
    group: str
    source: str
    """``environment`` or ``default``."""
    value: str | None
    """What is in effect; ``None`` when nothing is. Never a secret's value."""
    secret: bool
    documented_default: str | None
    description: str | None


def _is_encryption_key(name: str) -> bool:
    """``COS_WEB_ENCRYPTION_KEY_<n>`` with a numeric ``n``, as the settings read it."""
    return name.startswith(ENCRYPTION_KEY_PREFIX) and name[len(ENCRYPTION_KEY_PREFIX):].isdigit()


def _encryption_key_names(environ: Mapping[str, str]) -> list[str]:
    return sorted(
        (name for name in environ if _is_encryption_key(name) and _is_set(name, environ)),
        key=lambda name: int(name[len(ENCRYPTION_KEY_PREFIX):]),
    )


def rows(
    settings: WebSettings, environ: Mapping[str, str] | None = None
) -> list[Row]:
    """Every variable, in group order, with what this process runs with."""
    environ = os.environ if environ is None else environ
    result: list[Row] = []
    for variable in VARIABLES:
        reference = REFERENCE.get(variable.name, {})
        hidden = variable.secret
        if variable.name == "ENCRYPTION_KEY_<n>":
            # The row carries version names only, never key material, so it
            # is shown rather than reduced to "set".
            hidden = False
            names = _encryption_key_names(environ)
            source = "environment" if names else "default"
            # Which versions exist is not a secret, and it is what a rotation
            # needs checking; the keys themselves are.
            value = ", ".join(name[len(ENV_PREFIX):] for name in names) or None
        elif variable.name == FRONTEND_DIR:
            source = "environment" if _is_set(variable.env_name, environ) else "default"
            value = (environ.get(variable.env_name) or "").strip() or None
        else:
            source = "environment" if _is_set(variable.env_name, environ) else "default"
            effective = getattr(settings, variable.field or "")
            if variable.secret:
                value = "set" if effective else None
            elif variable.name == "REDIS_URL":
                value = _redact_url(str(effective))
            else:
                value = _display(effective)
        result.append(
            Row(
                name=variable.name,
                group=variable.group,
                source=source,
                value=value,
                secret=hidden,
                documented_default=reference.get("default"),
                description=reference.get("description"),
            )
        )
    order = {group: index for index, group in enumerate(GROUPS)}
    return sorted(result, key=lambda row: order[row.group])


def grouped_rows(
    settings: WebSettings, environ: Mapping[str, str] | None = None
) -> list[tuple[str, list[Row]]]:
    """The rows, gathered under their groups in display order."""
    every = rows(settings, environ)
    return [
        (group, [row for row in every if row.group == group])
        for group in GROUPS
        if any(row.group == group for row in every)
    ]


def unrecognised(environ: Mapping[str, str] | None = None) -> list[str]:
    """
    ``COS_WEB_*`` names in the environment that nothing here reads.

    Almost always a typo - ``COS_WEB_IP_RATELIMIT`` - and a typo in this
    prefix is silent: the service starts, and runs on the default the operator
    believes they changed. Names only; a value somebody meant for a variable
    that does not exist may still be a credential.
    """
    environ = os.environ if environ is None else environ
    known = {variable.env_name for variable in VARIABLES}
    return sorted(
        name
        for name in environ
        if name.startswith(ENV_PREFIX)
        and name not in known
        and not _is_encryption_key(name)
    )
