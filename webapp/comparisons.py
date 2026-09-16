"""
The five minutes a comparison against an uploaded report is allowed to live.

Every other page in this service can be rebuilt from what it was rendered
from: two uuids still name two results in Redis, so ``/compare`` recomputes
rather than remembers. A comparison against an *uploaded* report cannot,
because the upload is gone the moment it has been read - deliberately, since
keeping somebody's file is precisely what this service promises not to do.

That leaves one thing to hold: the comparison itself, which is a few hundred
bytes this service wrote, containing no part of the upload that did not come
through :mod:`webapp.imports`. It is held so that the answer survives a reload
and a shared link back to it, and it is held for five minutes, which is about
as long as somebody reads one.

The token follows the rule the rest of the service follows: it is a uuid4, it
is the whole of the authorisation for what it names, unknown and expired are
the same 404, and nothing lists them. The difference from a scan uuid is the
clock - a scan lasts an hour by default, a comparison five minutes at the
outside - because a scan is a measurement somebody may want to come back to
and this is the arithmetic on top of one.
"""

from __future__ import annotations

import json
import uuid as uuid_module
from dataclasses import dataclass
from typing import Any

from .encryption import EncryptionConfig, decrypt_value, encrypt_value
from .redis_backend import RedisBackend
from .store import target_hostname

#: The cap, and the default. Five minutes is the promise the page makes, so it
#: is written here once and clamped rather than trusted to a configuration
#: value: an operator may shorten the window, never lengthen it.
MAX_COMPARISON_TTL_SECONDS = 300

#: Below this a comparison would expire while it was still being read.
MIN_COMPARISON_TTL_SECONDS = 30


def comparison_key(token: str) -> str:
    """Redis key holding one cached comparison."""
    return f"compare:{token}:document"


def is_comparison_token(candidate: str) -> bool:
    """Whether a path segment is a token this service issued.

    The same canonical-uuid4 test scan identifiers get, for the same reason:
    a lookup for anything else is a probe, and refusing it here keeps
    caller-controlled text out of a Redis key name altogether.
    """
    try:
        parsed = uuid_module.UUID(candidate)
    except (ValueError, AttributeError, TypeError):
        return False
    return parsed.version == 4 and str(parsed) == candidate


def new_token() -> str:
    """A fresh capability for one comparison."""
    return str(uuid_module.uuid4())


def clamp_ttl(seconds: int) -> int:
    """The configured lifetime, held to the five minutes the page promises."""
    return max(MIN_COMPARISON_TTL_SECONDS, min(int(seconds), MAX_COMPARISON_TTL_SECONDS))


@dataclass
class ComparisonStore:
    """Reads and writes the ``compare:{token}:*`` namespace, and nothing else."""

    backend: RedisBackend
    ttl: int = MAX_COMPARISON_TTL_SECONDS
    encryption_config: EncryptionConfig | None = None

    def __post_init__(self) -> None:
        self.ttl = clamp_ttl(self.ttl)

    async def save(self, token: str, document: dict[str, Any]) -> None:
        """Hold one comparison for its window. Encrypted where scans are."""
        if not is_comparison_token(token):  # pragma: no cover - we issue these
            raise ValueError("A comparison token must be a canonical uuid4.")
        payload = json.dumps(document, separators=(",", ":"), default=str)
        if self.encryption_config:
            payload = encrypt_value(payload, self.encryption_config)
        await self.backend.set(comparison_key(token), payload, ex=self.ttl)

    async def get(self, token: str) -> dict[str, Any] | None:
        """
        One cached comparison, or ``None`` for unknown, expired and malformed.

        The caller turns all three into the same 404. Distinguishing them
        would answer whether a token was ever real, which is the one thing a
        capability must not tell somebody who does not hold it.
        """
        if not is_comparison_token(token):
            return None
        raw = await self.backend.get(comparison_key(token))
        if raw is None:
            return None
        if self.encryption_config:
            decrypted = decrypt_value(raw, self.encryption_config)
            if decrypted is None:
                return None
            raw = decrypted
        try:
            document = json.loads(raw)
        except ValueError:  # pragma: no cover - we wrote it
            return None
        return document if isinstance(document, dict) else None

    async def purge_target(self, hostname: str) -> tuple[int, int]:
        """
        Delete every cached comparison that names one instance, then look again.

        An erasure request names an instance, and a comparison names two. It
        would expire within five minutes on its own, but "it goes away soon"
        is exactly the argument
        [ADR 0007](../adr/0007-erasure-on-request.md) refuses for a scan
        result, and this is a scan result's arithmetic - so it is erased on
        request like one.

        Walking the keyspace is the same cost `ScanStore.purge_target` pays
        and for the same reason: nothing here maps an instance back to what
        mentions it, and keeping such a map would be keeping the record this
        service exists not to keep. The second walk is what makes the number
        in the receipt honest, because by then the evidence is gone.

        Returns what was deleted, and what still matched afterwards.
        """
        wanted = hostname.lower()
        tokens = await self._tokens_for(wanted)
        deleted = 0
        for token in tokens:
            deleted += await self.backend.delete(comparison_key(token))
        return deleted, len(await self._tokens_for(wanted))

    async def _tokens_for(self, hostname: str) -> list[str]:
        """Every cached comparison with this hostname on either side."""
        found: list[str] = []
        for key in await self.backend.keys_matching("compare:*:document"):
            parts = key.split(":")
            if len(parts) != 3 or not is_comparison_token(parts[1]):
                continue
            document = await self.get(parts[1])
            if document is None:
                continue
            sides = (document.get("baseline") or {}, document.get("current") or {})
            if any(
                target_hostname(side.get("target")) == hostname
                for side in sides
                if isinstance(side, dict)
            ):
                found.append(parts[1])
        return found

    async def expires_in(self, token: str) -> int:
        """Seconds left on one comparison, for the line that says so."""
        if not is_comparison_token(token):
            return 0
        remaining = await self.backend.ttl(comparison_key(token))
        return max(0, remaining) if remaining >= 0 else self.ttl
