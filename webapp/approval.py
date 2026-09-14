"""
Which targets a deployment in approval mode may scan.

Off by default: the public service scans any public OpenCloud. A deployment
that should scan only instances somebody vouched for sets
``COS_WEB_REQUIRE_APPROVAL=true``, and a target is then approved when either

- it is named in ``COS_WEB_APPROVED_TARGETS`` - hostnames, ``.suffix`` domains,
  addresses and CIDR ranges, the same shapes the exclusions take; or
- with ``COS_WEB_APPROVAL_DNS`` (on by default), its own DNS says so: a TXT
  record at ``_check-opencloud-security.<hostname>`` reading
  ``check-opencloud-security=<this service's hostname>``.

The record names *this* service, so publishing it approves one deployment and
not every copy of this project. It needs no secret: whoever can write a TXT
record under a name controls the name, which is exactly the claim approval
asks for.

The lookup goes to the resolver this machine already uses and nowhere else,
through the same wire format the scanner's CAA and DNSSEC checks speak (ADR
0024). A lookup that fails is a refusal, never an approval.
"""

from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit

from opencloud_local_scan.dns import (
    ask,
    read_header,
    read_records,
    skip_questions,
    system_nameservers,
)

from .settings import WebSettings
from .ssrf import Target, _parse_entry, denylist

TYPE_TXT = 16
APPROVAL_LABEL = "_check-opencloud-security"
APPROVAL_KEY = "check-opencloud-security"
LOOKUP_TIMEOUT_SECONDS = 3.0

NOT_APPROVED = (
    "This service only scans instances that have been approved for it. "
    "Ask the operator to add it, or publish the DNS record that approves it."
)


def approval_value(settings: WebSettings) -> str | None:
    """What the TXT record must say, or ``None`` without a public address."""
    host = urlsplit(settings.public_base_url or "").hostname
    return f"{APPROVAL_KEY}={host.lower()}" if host else None


def ensure_approval_ready(settings: WebSettings) -> None:
    """
    Refuse to start an approval mode that could approve nothing, or a typo.

    Required with an empty list and the DNS proof off would refuse every
    submission while looking configured; an entry that does not parse would
    silently approve nothing it names.
    """
    unparsed = [
        entry for entry in settings.approved_targets
        if entry.strip() and _parse_entry(entry) is None
    ]
    if unparsed:
        raise ValueError(
            "COS_WEB_APPROVED_TARGETS contains entries that are neither a "
            f"hostname, a .suffix, an address nor a CIDR range: {', '.join(unparsed)}."
        )
    if not settings.require_approval:
        return
    if not settings.approved_targets and not settings.approval_dns:
        raise ValueError(
            "COS_WEB_REQUIRE_APPROVAL is on with no COS_WEB_APPROVED_TARGETS and "
            "COS_WEB_APPROVAL_DNS off, so no target could ever be scanned."
        )
    if settings.approval_dns and approval_value(settings) is None:
        raise ValueError(
            "COS_WEB_APPROVAL_DNS needs COS_WEB_PUBLIC_BASE_URL: the record "
            "approves this service by its hostname."
        )


def listed(target: Target, entries: tuple[str, ...]) -> bool:
    """Whether the operator's list names the target, by name or by address."""
    if not entries:
        return False
    approved = denylist(tuple(entries))
    if approved.blocks_hostname(target.hostname):
        return True
    addresses = [ipaddress.ip_address(address) for address in target.addresses]
    return bool(addresses) and all(approved.blocks_address(address) for address in addresses)


def _txt_strings(rdata: bytes) -> str:
    """One TXT record's character-strings, joined as RFC 7208 reads them."""
    parts = []
    offset = 0
    while offset < len(rdata):
        length = rdata[offset]
        parts.append(rdata[offset + 1 : offset + 1 + length])
        offset += 1 + length
    return b"".join(parts).decode("utf-8", "replace")


def txt_records(name: str, timeout: float = LOOKUP_TIMEOUT_SECONDS) -> list[str]:
    """Every TXT record at ``name``, from the system resolver, or an empty list."""
    for nameserver in system_nameservers():
        try:
            data = ask(name, TYPE_TXT, nameserver, timeout)
            header = read_header(data)
            records, _ = read_records(data, skip_questions(data, header), header.ancount)
        except (OSError, ValueError):
            continue
        return [_txt_strings(record.rdata) for record in records if record.rtype == TYPE_TXT]
    return []


def dns_approved(target: Target, settings: WebSettings) -> bool:
    """Whether the target's own zone approves this service."""
    expected = approval_value(settings)
    if expected is None or target.hostname.startswith("["):
        return False
    try:
        ipaddress.ip_address(target.hostname)
    except ValueError:
        pass
    else:
        return False
    records = txt_records(f"{APPROVAL_LABEL}.{target.hostname}")
    return any(record.strip().lower() == expected for record in records)


def approved(target: Target, settings: WebSettings) -> bool:
    """Whether a deployment's approval rules let it scan this target."""
    if not settings.require_approval:
        return True
    if listed(target, settings.approved_targets):
        return True
    return settings.approval_dns and dns_approved(target, settings)
