"""
Accepting a failed check, for a while, for a stated reason.

A waiver is an operator saying "I know, and not today". The existing form of
that is a pattern in ``--ignore-hardening``: it suppresses the alert, it says
nothing about why, and it lasts until somebody remembers to take it out.
Nobody remembers. A year later the check is still failing, the alert is still
suppressed, and the reason is in a ticket nobody can find.

This adds the two things that fix that - a reason and a deadline - without
taking anything away:

* **A pattern on its own is still a permanent waiver.** Every existing
  configuration keeps working and keeps meaning what it meant.
* **A temporary waiver is refused unless it is complete.** It needs a
  non-empty reason and a timezone-qualified expiry. A record that cannot be
  parsed is an error, never a permanent waiver by accident - failing open is
  how a typo becomes a blind spot that outlives everybody who knew about it.
* **Expiry is decided once, at the start of the scan, in UTC.** The boundary
  is ``now >= expires_at``: at the stroke of the expiry the waiver is over.
  Nothing re-reads the clock while the scan runs, so a long scan cannot have
  a check waived at the top and not at the bottom.
* **Every applicable record is reported, not just the one that matched.**
  Otherwise a permanent ``*`` sitting quietly in a configuration file would
  mask the expiry of every temporary waiver underneath it, and the report
  would say the suppression was still deliberate when it was not.

None of it touches severity, grading or the rating. A waiver decides whether
an alert is raised; the evidence stays exactly as measured.
"""

from __future__ import annotations

import fnmatch
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .hardening import is_actionable

#: What separates the three fields of a temporary waiver. A check identifier
#: is a name, a path or a port - `exposed:/config/opencloud.yaml`,
#: `debugPort:9205` - and a pattern is an fnmatch glob over those, so none of
#: them can contain a pipe. A comma or a semicolon could not be used here:
#: both already separate entries in a flag and in an environment variable.
FIELD_SEPARATOR = "|"


class WaiverError(ValueError):
    """A waiver record that cannot be understood, and so is not accepted."""


@dataclass(frozen=True)
class Waiver:
    """One accepted failure: what, why, and until when."""

    pattern: str
    #: When this stops suppressing anything. ``None`` is the old, permanent
    #: form, which has no deadline because nobody wrote one.
    expires_at: datetime | None = None
    reason: str = ""

    def matches(self, name: str) -> bool:
        """
        Whether this record covers a check identifier.

        Case-insensitive, with shell-style wildcards, so a generated family -
        ``exposed:/some/path``, ``debugPort:9205`` - is waived by one
        ``debugPort:*`` rather than one entry per port. This is the rule the
        scanner has always used and it is unchanged.
        """
        candidate, pattern = name.casefold(), self.pattern.casefold()
        return bool(pattern) and (
            candidate == pattern or fnmatch.fnmatch(candidate, pattern)
        )

    def active_at(self, now: datetime) -> bool:
        """Whether this record still suppresses an alert at ``now``."""
        if self.expires_at is None:
            return True
        return now < self.expires_at

    @property
    def temporary(self) -> bool:
        """Whether an expiry was written down for this record."""
        return self.expires_at is not None

    def as_dict(self, now: datetime) -> dict[str, Any]:
        """Render the record for the result document, camelCase as usual."""
        return {
            "pattern": self.pattern,
            "reason": self.reason,
            "expiresAt": self.expires_at.isoformat() if self.expires_at else None,
            "state": "active" if self.active_at(now) else "expired",
        }


def parse_waiver(text: str, *, require_deadline: bool = False) -> Waiver:
    """
    Read one configured waiver.

    ``pattern`` on its own is the permanent form this project has always
    accepted. ``pattern|expires|reason`` is the temporary one, and every part
    of it is required: an expiry without a reason documents nothing, and a
    reason without an expiry is the permanent form wearing a note.

    ``require_deadline`` refuses the permanent form. The inputs that exist to
    carry a deadline - ``--waive-until`` and ``temporary_waivers`` - pass it:
    there a bare pattern is never what was meant. It is usually the tail of a
    reason that a ``;`` split off into an entry of its own, and reading that
    as a permanent waiver would suppress whatever the fragment happens to
    match, forever.

    Raises :class:`WaiverError` rather than degrading to a permanent waiver.
    A malformed record is a mistake, and the safe reading of a mistake is
    "this does not suppress anything", not "this suppresses everything
    forever".
    """
    raw = text.strip()
    if not raw:
        raise WaiverError("A waiver needs a check identifier or pattern.")

    parts = [part.strip() for part in raw.split(FIELD_SEPARATOR)]
    if len(parts) == 1 and require_deadline:
        raise WaiverError(
            f"{raw!r} has no expiry and no reason. A temporary waiver is "
            f"written pattern{FIELD_SEPARATOR}expires{FIELD_SEPARATOR}reason, "
            "and a ';' separates two waivers, so it cannot appear in a "
            "reason. A permanent waiver belongs in --ignore-hardening."
        )
    if len(parts) == 1:
        return Waiver(parts[0])
    if len(parts) != 3:
        raise WaiverError(
            f"A temporary waiver is written pattern{FIELD_SEPARATOR}expires"
            f"{FIELD_SEPARATOR}reason; {raw!r} has {len(parts)} field(s)."
        )

    pattern, expires, reason = parts
    if not pattern:
        raise WaiverError(f"{raw!r} waives nothing: the pattern is empty.")
    if not reason:
        raise WaiverError(
            f"{raw!r} has no reason. A temporary waiver records why the "
            "failure is acceptable, so that whoever finds it later can tell."
        )
    return Waiver(pattern, _parse_expiry(expires, raw), reason)


def _parse_expiry(value: str, raw: str) -> datetime:
    """
    Read an expiry, which must say what timezone it is in.

    A naive timestamp is refused rather than assumed to be UTC or local: the
    two readings are hours apart, the difference decides whether an alert is
    suppressed, and the scanner has no way to know which one was meant.
    """
    text = value.strip()
    if not text:
        raise WaiverError(f"{raw!r} has no expiry.")
    # `datetime.fromisoformat` learned to read a trailing Z in 3.11, and this
    # project supports 3.10.
    normalised = f"{text[:-1]}+00:00" if text.endswith(("Z", "z")) else text
    try:
        parsed = datetime.fromisoformat(normalised)
    except ValueError as error:
        raise WaiverError(
            f"{raw!r} has an expiry that is not an ISO 8601 timestamp: {error}."
        ) from error
    if parsed.tzinfo is None:
        raise WaiverError(
            f"{raw!r} has an expiry with no timezone. Write it as "
            "2026-12-31T00:00:00Z or with an offset, so that it means the "
            "same moment wherever the scan runs."
        )
    return parsed.astimezone(timezone.utc)


def parse_waivers(
    values: Iterable[str], *, require_deadline: bool = False
) -> tuple[Waiver, ...]:
    """Read every configured waiver, keeping the order they were given in."""
    return tuple(
        parse_waiver(value, require_deadline=require_deadline)
        for value in values
        if value.strip()
    )


@dataclass(frozen=True)
class WaiverDecision:
    """What the configured waivers say about one failing check."""

    check: str
    #: Every record whose pattern covers this check, expired ones included.
    #: A permanent wildcard must not be able to hide that a specific
    #: temporary waiver underneath it has run out.
    applicable: tuple[Waiver, ...]
    waived: bool
    #: The moment the decision was made against, carried so that the
    #: breakdown below cannot answer against a different clock.
    at: datetime

    @property
    def expired(self) -> tuple[Waiver, ...]:
        """The applicable records that have run out."""
        return tuple(
            record
            for record in self.applicable
            if record.temporary and not record.active_at(self.at)
        )

    @property
    def only_covered_by_a_wildcard(self) -> bool:
        """
        Whether this check is suppressed only because something broader is.

        A specific temporary waiver has expired and a wider record is still
        carrying the suppression. The alert is still correctly suppressed -
        the wider record says so - but nobody re-decided it, and that is
        worth saying out loud rather than letting the expiry pass silently.
        """
        return bool(self.waived and self.expired)


def resolve(
    waivers: Sequence[Waiver], check: str, now: datetime
) -> WaiverDecision:
    """
    Decide one check against every configured record.

    Any active record is enough to suppress the alert - waivers are
    permissions, and one permission is a permission. Every applicable record
    is carried along whether it is active or not, so the report can say that
    a suppression is still deliberate, or that it is only still happening
    because something broader is covering for an expiry.
    """
    applicable = tuple(record for record in waivers if record.matches(check))
    waived = any(record.active_at(now) for record in applicable)
    return WaiverDecision(check, applicable, waived, now)


def scan_clock() -> datetime:
    """
    The one moment a scan decides every expiry against.

    Read once, at the start, in UTC. A scan that re-read the clock could
    waive a check in its first second and alert on it in its last.
    """
    return datetime.now(timezone.utc)


def report(
    waivers: Sequence[Waiver], decisions: Iterable[WaiverDecision], now: datetime
) -> list[dict[str, Any]]:
    """
    The waiver block of the result document.

    Every configured record appears, with what it matched. A record that
    matched nothing is worth seeing too: it is usually a pattern that no
    longer corresponds to any check, which is how a waiver outlives the
    finding it was written for.
    """
    matched: dict[int, list[str]] = {index: [] for index in range(len(waivers))}
    for decision in decisions:
        for index, record in enumerate(waivers):
            if record in decision.applicable:
                matched[index].append(decision.check)
    return [
        {**record.as_dict(now), "matched": sorted(set(matched[index]))}
        for index, record in enumerate(waivers)
    ]


@dataclass(frozen=True)
class UpcomingExpiry:
    """The next moment a waiver stops suppressing a failing check."""

    at: datetime
    #: The failing checks that lose their last active waiver at ``at``.
    checks: tuple[str, ...]
    #: The record whose deadline that is, so the alert can name it.
    pattern: str
    reason: str


def next_expiry(block: Any) -> UpcomingExpiry | None:
    """
    When the result document's waivers next let a failing check alert again.

    Read from the ``waivers`` block the scan wrote, so it answers against the
    same decisions the scan made. A check is only uncovered once *every*
    active record matching it has run out: a temporary waiver beneath a
    permanent wildcard ends without anything changing, and two overlapping
    temporary waivers end at the later of the two. Records that matched
    nothing are ignored for the same reason - their deadline passes
    unnoticed - and so are flags OpenCloud hardcodes, which never alert
    whether waived or not.

    ``None`` when no failing check is suppressed by a temporary waiver alone.
    """
    if not isinstance(block, list):
        return None
    # check -> the deadlines of the active records covering it; None is a
    # permanent record, which covers the check for good.
    covering: dict[str, list[tuple[datetime | None, dict[str, Any]]]] = {}
    for record in block:
        if not isinstance(record, dict) or record.get("state") != "active":
            continue
        expires = record.get("expiresAt")
        deadline: datetime | None = None
        if expires is not None:
            try:
                deadline = _parse_expiry(str(expires), str(expires))
            except WaiverError:
                continue
        for check in record.get("matched") or ():
            if is_actionable(str(check)):
                covering.setdefault(str(check), []).append((deadline, record))

    ends: dict[str, tuple[datetime, dict[str, Any]]] = {}
    for check, records in covering.items():
        if any(deadline is None for deadline, _ in records):
            continue
        ends[check] = max(
            ((deadline, record) for deadline, record in records if deadline is not None),
            key=lambda item: item[0],
        )
    if not ends:
        return None
    at, record = min(ends.values(), key=lambda item: item[0])
    return UpcomingExpiry(
        at=at,
        checks=tuple(sorted(check for check, (end, _) in ends.items() if end == at)),
        pattern=str(record.get("pattern") or ""),
        reason=str(record.get("reason") or ""),
    )


def scanned_at(result: Mapping[str, Any]) -> datetime | None:
    """The moment the scan decided its waivers, read back from the document."""
    scanned = result.get("scannedAt")
    date = scanned.get("date") if isinstance(scanned, Mapping) else None
    if not isinstance(date, str):
        return None
    try:
        return datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def days_left(result: Mapping[str, Any], now: datetime | None = None) -> int | None:
    """
    Whole days until the next waiver expiry lets a failing check alert again.

    Counted from the scan's own moment, so the number agrees with the
    ``active`` state beside it, and truncated as the certificate's
    ``daysRemaining`` is: ``0`` means it ends within the next 24 hours.
    ``None`` when nothing is suppressed by a temporary waiver alone.
    """
    upcoming = next_expiry(result.get("waivers"))
    if upcoming is None:
        return None
    moment = now or scanned_at(result) or scan_clock()
    return max((upcoming.at - moment).days, 0)
