"""
Rate limits, all kept in Redis and all expiring on their own.

The client limit protects the service from one visitor; the target limit
protects an OpenCloud instance from the service. They are separate on purpose:
a busy but well-behaved client should not be able to make one instance the
target of a scan every second, and a popular instance should not lock out
everybody who wants to scan something else.

The probe guard is the third, and the only one decided after the fact: a
client whose submissions keep turning out not to be OpenCloud at all is using
the service to find out what answers where, which is not what it is for. The
worker counts those hosts and imposes the block; the API only reads it.

Client addresses are never stored in the clear. The key holds a truncated
HMAC of the address under a pepper, which is enough to count and useless
afterwards - the counter expires, and nothing on disk maps it back.

That pepper is per-process by default, which is right for a single process and
wrong the moment there are two. Each one derives a different key for the same
address, so a client silently gets one allowance per process and the limit
becomes a suggestion - with nothing in the log to say so. A deployment that
runs more than one web process therefore sets ``COS_WEB_RATE_LIMIT_SALT`` to
the same value everywhere, which is what makes them count together.
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import os
import time
from dataclasses import dataclass

from .redis_backend import RedisBackend
from .settings import DAILY_WINDOW_SECONDS, WebSettings

# The fallback, regenerated on every restart. There is no reason for it to
# survive: a counter with a one-minute window has nothing to remember across a
# restart, and a key that never changes is a key that can be brute-forced
# offline. It is only ever right for a deployment running one web process.
_PROCESS_PEPPER = os.urandom(32)


def _pepper(salt: str | None) -> bytes:
    """The keying material for the fingerprints, configured or per-process."""
    return salt.encode("utf-8") if salt else _PROCESS_PEPPER


def _fingerprint(value: str, salt: str | None = None) -> str:
    digest = hmac.new(_pepper(salt), value.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest[:32]


def client_key(client: str, salt: str | None = None) -> str:
    """Rate-limit key for one client address."""
    return f"cos:web:rl:client:{_fingerprint(client, salt)}"


def target_key(host: str, salt: str | None = None) -> str:
    """Cooldown key for one scan target."""
    return f"cos:web:rl:target:{_fingerprint(host.lower(), salt)}"


def upload_key(client: str, salt: str | None = None) -> str:
    """Rate-limit key for report uploads from one client address."""
    return f"cos:web:rl:upload:{_fingerprint(client, salt)}"


def credential_key(client: str, salt: str | None = None) -> str:
    """Failed-authorisation key for one client address."""
    return f"cos:web:rl:auth:{_fingerprint(client, salt)}"


def network_of(client: str, ipv4_prefix: int, ipv6_prefix: int) -> str:
    """
    The network a client address is counted as, in CIDR notation.

    One IPv6 subscriber is handed a whole /64 and can rotate through it for
    free, so counting single IPv6 addresses gives a client as many allowances
    as it cares to have. Anything that is not an address - a test client, a
    socket with no peer - is counted as itself.
    """
    try:
        address = ipaddress.ip_address(client.strip("[]"))
    except ValueError:
        return client
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped is not None:
        address = address.ipv4_mapped
    prefix = ipv4_prefix if address.version == 4 else ipv6_prefix
    maximum = 32 if address.version == 4 else 128
    prefix = max(1, min(maximum, prefix))
    if prefix == maximum:
        # A single address keeps the spelling every key was derived from
        # before networks were counted, so a deploy does not reset counters.
        return str(address)
    return str(ipaddress.ip_network(f"{address}/{prefix}", strict=False))


def prober_fingerprint(client: str, salt: str | None = None) -> str:
    """The fingerprint a submission hands to the worker for the probe guard.

    ``client`` is already the network (:func:`network_of`). The worker learns
    whether a host was OpenCloud and the API knows who asked; neither can
    derive the other's key while the pepper is per process, so the
    fingerprint itself travels with the scan instead.
    """
    return _fingerprint(client, salt)


def probe_count_key(prober: str) -> str:
    """How many suspicious outcomes one client network had, in the window."""
    return f"cos:web:rl:probe:{prober}"


def probe_block_key(prober: str) -> str:
    """The block a client network earned by probing."""
    return f"cos:web:rl:blocked:{prober}"


def probe_repeat_key(prober: str) -> str:
    """How many blocks one client network has earned recently, for escalation."""
    return f"cos:web:rl:blocks:{prober}"


def daily_key(client: str, salt: str | None = None) -> str:
    """Submissions from one client in the current day-long window."""
    return f"cos:web:rl:daily:{_fingerprint(client, salt)}"


BLOCK_KEY_PATTERN = "cos:web:rl:blocked:*"

#: How much longer each repeated block lasts than the one before it, up to
#: the configured ceiling: an hour, then six, then a day.
BLOCK_ESCALATION_FACTOR = 6

#: Day-stamped counters for the operator area, kept for a week and a day so
#: "the last seven days" is always whole.
STATS_RETENTION_SECONDS = 8 * 86400
STAT_BLOCKS = "blocks"
STAT_STRIKES = "strikes"
STAT_DAILY = "daily"


def stats_key(name: str, day: str) -> str:
    """One day's count of one guard event. A number and a date, nothing else."""
    return f"cos:web:stats:{name}:{day}"


def _today(offset_days: int = 0) -> str:
    return time.strftime("%Y%m%d", time.gmtime(time.time() - offset_days * 86400))


async def count_event(backend: RedisBackend, name: str) -> None:
    """Add one to today's count of a guard event."""
    key = stats_key(name, _today())
    if await backend.incr(key) == 1:
        await backend.expire(key, STATS_RETENTION_SECONDS)


async def event_counts(backend: RedisBackend, name: str) -> tuple[int, int]:
    """Today's count and the last seven days' total of one guard event."""
    days = []
    for offset in range(7):
        raw = await backend.get(stats_key(name, _today(offset)))
        try:
            days.append(int(raw) if raw is not None else 0)
        except ValueError:  # pragma: no cover - only a hand-edited key gets here
            days.append(0)
    return days[0], sum(days)


def probe_policy(settings: WebSettings) -> ProbePolicy:
    """The probe guard as both processes read it from the environment."""
    return ProbePolicy(
        limit=settings.probe_limit,
        window=settings.probe_window,
        block=settings.probe_block,
        block_max=settings.probe_block_max,
        repeat_window=settings.probe_repeat_window,
    )


def limiter_for(backend: RedisBackend, settings: WebSettings) -> RateLimiter:
    """Every client and target limit, configured from the settings."""
    return RateLimiter(
        backend=backend,
        client_limit=settings.ip_rate_limit,
        client_window=settings.ip_rate_window,
        target_cooldown=settings.target_cooldown,
        # Unset is a random pepper per process, which counts correctly only
        # while there is one. A deployment behind several web processes sets
        # the same value in each, or every client gets one allowance apiece.
        salt=settings.rate_limit_salt,
        probe=probe_policy(settings),
        ipv4_prefix=settings.probe_ipv4_prefix,
        ipv6_prefix=settings.client_ipv6_prefix,
        daily_limit=settings.daily_scan_limit,
        daily_window=DAILY_WINDOW_SECONDS,
    )


@dataclass(frozen=True)
class ProbePolicy:
    """How many suspicious outcomes earn a block, and how long blocks last.

    Built from the settings in both processes: the API refuses and counts
    refused targets, the worker counts hosts that were not OpenCloud.
    """

    limit: int
    window: int
    block: int
    block_max: int
    repeat_window: int

    @property
    def enabled(self) -> bool:
        return self.limit > 0

    def duration(self, repeat: int) -> int:
        """How long the ``repeat``-th block inside the repeat window lasts."""
        steps = max(0, repeat - 1)
        return max(1, min(self.block * BLOCK_ESCALATION_FACTOR**steps, max(self.block, self.block_max)))


# An erasure request is rare and its credential belongs to the operator, so
# there is no legitimate caller who needs a sixth attempt inside five minutes.
# Only *failures* are counted: an operator working through a list of erasure
# requests presents the right token every time and never meets this.
CREDENTIAL_ATTEMPT_LIMIT = 5
CREDENTIAL_ATTEMPT_WINDOW_SECONDS = 300


@dataclass(frozen=True)
class LimitDecision:
    """Whether a request may proceed, and when to try again if not."""

    allowed: bool
    retry_after: int = 0
    scope: str = ""


@dataclass
class RateLimiter:
    """Fixed-window client limit plus a per-target cooldown."""

    backend: RedisBackend
    client_limit: int
    client_window: int
    target_cooldown: int
    salt: str | None = None
    """Shared across every web process, or ``None`` for the per-process one.
    Two processes with different peppers do not share a counter, so this is
    what makes the client limit hold for a deployment that runs more than
    one."""
    probe: ProbePolicy | None = None
    """The probe guard, or ``None`` with it off. The API reads the block and
    counts refused targets; the worker, which learns whether a host was
    OpenCloud, counts the rest (:func:`record_strike`)."""
    ipv4_prefix: int = 32
    """How much of an IPv4 address the probe guard counts as one client."""
    ipv6_prefix: int = 64
    """How much of an IPv6 address every client limit counts as one client."""
    daily_limit: int = 0
    """Submissions per client per day; ``0`` switches the cap off."""
    daily_window: int = 86400

    def client_identity(self, client: str) -> str:
        """Who the client and daily limits count: the address, or its IPv6 /64."""
        return network_of(client, 32, self.ipv6_prefix)

    def network(self, client: str) -> str:
        """Who the probe guard counts: the configured IPv4 and IPv6 networks."""
        return network_of(client, self.ipv4_prefix, self.ipv6_prefix)

    async def check_client(self, client: str) -> LimitDecision:
        """Count one request from this client and decide whether it may run."""
        if self.client_limit <= 0:
            return LimitDecision(True)
        key = client_key(self.client_identity(client), self.salt)
        count = await self.backend.incr(key)
        if count == 1:
            await self.backend.expire(key, self.client_window)
        if count > self.client_limit:
            return LimitDecision(False, await self._window_left(key, self.client_window), "client")
        return LimitDecision(True)

    async def check_upload(self, client: str) -> LimitDecision:
        """
        Count one uploaded report from this client.

        A bucket of its own, with the same allowance as the scan limit. Two
        reasons it is not simply the same counter: uploading a report costs
        this service a parse and costs somebody else's instance nothing, so it
        has no business spending a visitor's scan allowance - and a parser fed
        from outside is worth being able to see the rate of on its own.
        """
        if self.client_limit <= 0:
            return LimitDecision(True)
        key = upload_key(self.client_identity(client), self.salt)
        count = await self.backend.incr(key)
        if count == 1:
            await self.backend.expire(key, self.client_window)
        if count > self.client_limit:
            return LimitDecision(
                False, await self._window_left(key, self.client_window), "upload"
            )
        return LimitDecision(True)

    async def _window_left(self, key: str, window: int) -> int:
        """How long a counter's window still has to run, repairing a lost one.

        ``INCR`` and ``EXPIRE`` are two round trips, and a counter created by
        the first without reaching the second has no window at all: it can
        never fall back below the limit, so the client it belongs to would be
        refused for ever with nothing in the log to say why. A counter already
        over the limit is the only place that can be observed, so it is also
        where it is put right - the client waits one window rather than for
        somebody to notice and delete a key.
        """
        remaining = await self.backend.ttl(key)
        if remaining > 0:
            return max(1, remaining)
        await self.backend.expire(key, window)
        return max(1, window)

    async def check_target(self, host: str) -> LimitDecision:
        """
        Claim the cooldown slot for one target.

        ``SET NX`` is what makes this safe under concurrency: the first
        request to arrive creates the key, everyone else sees it already
        there, and no read-then-write window exists for two simultaneous
        requests to slip through.
        """
        if self.target_cooldown <= 0:
            return LimitDecision(True)
        key = target_key(host, self.salt)
        claimed = await self.backend.set(key, "1", ex=self.target_cooldown, nx=True)
        if claimed:
            return LimitDecision(True)
        retry_after = await self.backend.ttl(key)
        return LimitDecision(
            False, max(1, retry_after if retry_after > 0 else self.target_cooldown), "target"
        )

    async def peek_client(self, client: str) -> LimitDecision:
        """
        Whether this client could submit now, without spending anything.

        The mirror of :meth:`check_client` with the ``INCR`` left out. It
        exists so that a page can tell a reader how long they have to wait
        instead of letting them find out by being refused - and reading it
        must not itself be the request that uses up the allowance.
        """
        if self.client_limit <= 0:
            return LimitDecision(True)
        key = client_key(self.client_identity(client), self.salt)
        raw = await self.backend.get(key)
        try:
            count = int(raw) if raw is not None else 0
        except ValueError:  # pragma: no cover - only a hand-edited key gets here
            count = 0
        if count < self.client_limit:
            return LimitDecision(True)
        retry_after = await self.backend.ttl(key)
        return LimitDecision(
            False, max(1, retry_after if retry_after > 0 else self.client_window), "client"
        )

    async def peek_target(self, host: str) -> LimitDecision:
        """
        How long this target's cooldown still has to run, claiming nothing.

        :meth:`check_target` answers the same question by taking the slot,
        which is right for a submission and wrong for a page that only wants
        to show a countdown: asking would start a new cooldown and the answer
        would always be "the full one".
        """
        if self.target_cooldown <= 0:
            return LimitDecision(True)
        retry_after = await self.backend.ttl(target_key(host, self.salt))
        if retry_after <= 0:
            return LimitDecision(True)
        return LimitDecision(False, retry_after, "target")

    async def check_credential(self, client: str) -> LimitDecision:
        """
        Whether this client may present an operator credential again.

        Counts nothing itself - only :meth:`record_failed_credential` does, and
        only on a wrong answer. A caller holding the right token is never
        slowed down, and a caller guessing gets five tries per window however
        fast it sends them.
        """
        key = credential_key(client, self.salt)
        raw = await self.backend.get(key)
        try:
            count = int(raw) if raw is not None else 0
        except ValueError:  # pragma: no cover - only a hand-edited key gets here
            count = 0
        if count < CREDENTIAL_ATTEMPT_LIMIT:
            return LimitDecision(True)
        return LimitDecision(
            False,
            await self._window_left(key, CREDENTIAL_ATTEMPT_WINDOW_SECONDS),
            "credential",
        )

    async def record_failed_credential(self, client: str) -> None:
        """Count one wrong credential from this client, for the window."""
        key = credential_key(client, self.salt)
        count = await self.backend.incr(key)
        if count == 1:
            await self.backend.expire(key, CREDENTIAL_ATTEMPT_WINDOW_SECONDS)

    async def check_daily(self, client: str) -> LimitDecision:
        """
        Count one submission against this client's day, and decide.

        The per-minute limit stops a burst; this stops the patient version of
        the same thing, which stays just under it all night.
        """
        if self.daily_limit <= 0:
            return LimitDecision(True)
        key = daily_key(self.client_identity(client), self.salt)
        count = await self.backend.incr(key)
        if count == 1:
            await self.backend.expire(key, self.daily_window)
        if count > self.daily_limit:
            if count == self.daily_limit + 1:
                await count_event(self.backend, STAT_DAILY)
            return LimitDecision(False, await self._window_left(key, self.daily_window), "daily")
        return LimitDecision(True)

    async def peek_daily(self, client: str) -> LimitDecision:
        """The mirror of :meth:`check_daily` that spends nothing."""
        if self.daily_limit <= 0:
            return LimitDecision(True)
        key = daily_key(self.client_identity(client), self.salt)
        raw = await self.backend.get(key)
        try:
            count = int(raw) if raw is not None else 0
        except ValueError:  # pragma: no cover - only a hand-edited key gets here
            count = 0
        if count < self.daily_limit:
            return LimitDecision(True)
        retry_after = await self.backend.ttl(key)
        return LimitDecision(
            False, max(1, retry_after if retry_after > 0 else self.daily_window), "daily"
        )

    async def check_probe_block(self, client: str) -> LimitDecision:
        """
        Whether this client's network is serving a block for probing, spending nothing.

        Asked before the client limit, so a blocked client's refusals do not
        also run down an allowance it will want back when the block ends.
        """
        prober = self.prober_for(client)
        if prober is None:
            return LimitDecision(True)
        remaining = await self.backend.ttl(probe_block_key(prober))
        if remaining <= 0:
            return LimitDecision(True)
        return LimitDecision(False, remaining, "probe")

    def prober_for(self, client: str) -> str | None:
        """The fingerprint to store with a scan, or ``None`` with the guard off."""
        if self.probe is None or not self.probe.enabled:
            return None
        return prober_fingerprint(self.network(client), self.salt)

    async def record_refused_target(self, client: str) -> ProbeOutcome:
        """Count a submission the guard refused as a strike against its network."""
        prober = self.prober_for(client)
        if prober is None or self.probe is None:
            return ProbeOutcome(0, False)
        return await record_strike(self.backend, prober, self.probe)

    async def release_target(self, host: str) -> None:
        """Give the slot back when the request is rejected for another reason."""
        if self.target_cooldown > 0:
            await self.backend.delete(target_key(host, self.salt))

    async def forget_target(self, host: str) -> int:
        """
        Erase the cooldown derived from a host, and say whether one existed.

        The key holds a fingerprint and a counter, never the hostname, but it
        is still state derived from a target - so an erasure request removes it
        too, and the receipt counts it.
        """
        return await self.backend.delete(target_key(host, self.salt))


@dataclass(frozen=True)
class ProbeOutcome:
    """What one suspicious outcome did to the client network that caused it."""

    strikes: int
    blocked: bool
    """Whether this outcome is the one that started a block."""
    duration: int = 0
    """How long that block lasts, when it started one."""


async def record_strike(backend: RedisBackend, prober: str, policy: ProbePolicy) -> ProbeOutcome:
    """
    Count one suspicious outcome, and block the network at the limit.

    A strike is a scan whose host turned out not to be OpenCloud, or a target
    the guard refused outright. Every one counts, the same host again as much
    as a new one: a list of addresses that answer with something else - or
    nothing - is the shape of using this service to find out what runs where,
    and so is asking one address over and over whether it answers yet.

    The block is claimed with ``SET NX`` before its length is decided, so two
    workers reaching the limit together start one block and escalate once.
    Each block inside the repeat window lasts :data:`BLOCK_ESCALATION_FACTOR`
    times the one before, up to the ceiling; strikes that land while a block
    already runs change nothing.
    """
    if not policy.enabled or not prober:
        return ProbeOutcome(0, False)
    await count_event(backend, STAT_STRIKES)
    key = probe_count_key(prober)
    strikes = await backend.incr(key)
    if strikes == 1 or await backend.ttl(key) <= 0:
        await backend.expire(key, policy.window)
    if strikes < policy.limit:
        return ProbeOutcome(strikes, False)
    block_key = probe_block_key(prober)
    if not await backend.set(block_key, "1", ex=policy.block, nx=True):
        return ProbeOutcome(strikes, False)
    repeat_key = probe_repeat_key(prober)
    repeat = await backend.incr(repeat_key)
    duration = policy.duration(repeat)
    await backend.expire(block_key, duration)
    # Remembered from the end of this block, not its start: a network that
    # comes straight back to probing after a day-long block has not waited a
    # day of good behaviour.
    await backend.expire(repeat_key, duration + policy.repeat_window)
    await backend.delete(key)
    await count_event(backend, STAT_BLOCKS)
    return ProbeOutcome(strikes, True, duration)


async def active_blocks(backend: RedisBackend) -> int:
    """How many client networks are blocked right now. A count, never a key."""
    return len(await backend.keys_matching(BLOCK_KEY_PATTERN))
