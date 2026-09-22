"""
Two result documents, finding by finding, with the severities kept.

:mod:`opencloud_local_scan.baseline` answers "did anything get worse", which
is the question monitoring asks, and to answer it a finding is a name in a
set: ``check:cspWithoutUnsafeInline`` either is failing or is not. That is
deliberately less than a reader wants after the fact. A check that was
failing at ``medium`` and is failing at ``critical`` never enters or leaves
that set, so the baseline is silent about it - correctly, because nothing
regressed by its definition - and an operator reading the comparison would
never learn that the same finding now caps the rating two grades lower.

So this module keeps what the set throws away: the severity on each side, and
the category the finding belongs to. It computes, it does not judge - no
wording, no exit code, no opinion about whether the movement matters. The
caller renders.

Three rules keep it honest:

* **Absent is not passing.** A check that was not measured on one side gets
  ``None`` for that side, and its status says ``appeared`` or ``disappeared``
  rather than ``introduced`` or ``resolved``. ADR 0064 made a scan record
  what it did not measure precisely so this distinction can be made.
* **A waived finding is still a finding.** It is reported with ``waived``
  set, exactly as the scan document reports it, because a waiver is the
  operator's decision to not be alerted and not a claim the finding is gone.
* **The severity is whatever the document said.** An unrecognised or missing
  one becomes ``unknown`` and sorts last; it is never guessed from the
  catalogue, because the catalogue is today's opinion and the document is
  what was true when it was written.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .hardening import CATEGORIES as HARDENING_CATEGORIES
from .hardening import describe

#: Severities in the order they are worth reading, worst first. ``unknown``
#: is last and is what anything unrecognised becomes.
SEVERITIES: tuple[str, ...] = ("critical", "high", "medium", "low", "unknown")

#: The category advisories are filed under. Advisories have no entry in the
#: hardening catalogue - they are not a setting anybody can change - so they
#: would otherwise have no category to filter on at all.
ADVISORY_CATEGORY = "advisory"

#: Every value ``--category`` accepts for a finding.
CATEGORIES: tuple[str, ...] = (*HARDENING_CATEGORIES, ADVISORY_CATEGORY)

#: The finding is failing on the later side and was not failing before.
INTRODUCED = "introduced"
#: The finding was failing before and is not failing now.
RESOLVED = "resolved"
#: Failing on both sides. The severity may still have moved.
OPEN = "open"
#: Passing on both sides. Carried so a caller can show a full side-by-side.
PASSING = "passing"
#: Measured now, not measured before - which is not the same as introduced.
APPEARED = "appeared"
#: Measured before, not measured now - which is not the same as resolved.
DISAPPEARED = "disappeared"

_RANK: dict[str, int] = {name: index for index, name in enumerate(SEVERITIES)}


def normalise_severity(value: Any) -> str:
    """One document's severity, held to :data:`SEVERITIES`."""
    text = str(value or "").strip().lower()
    return text if text in _RANK else "unknown"


def severity_rank(severity: str) -> int:
    """Sort key for a severity: 0 is the worst, ``unknown`` is last."""
    return _RANK.get(severity, len(SEVERITIES))


@dataclass(frozen=True)
class Side:
    """One finding as one of the two documents recorded it."""

    severity: str
    passed: bool
    waived: bool

    @property
    def failing(self) -> bool:
        """Whether this side counts as a failure, waiver included."""
        return not self.passed

    def label(self) -> str:
        """A short rendering for a column: ``ok``, ``FAIL high``, ``waived``."""
        if self.passed:
            return "ok"
        if self.waived:
            return f"waived {self.severity}"
        return f"FAIL {self.severity}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "passed": self.passed,
            "waived": self.waived,
        }


@dataclass(frozen=True)
class Delta:
    """One finding on both sides, and how it moved."""

    id: str
    category: str
    #: ``None`` where the document did not measure this finding at all.
    before: Side | None
    after: Side | None
    status: str

    @property
    def severity_change(self) -> tuple[str, str] | None:
        """``(before, after)`` where the severity moved, else ``None``."""
        if self.before is None or self.after is None:
            return None
        if self.before.severity == self.after.severity:
            return None
        return (self.before.severity, self.after.severity)

    @property
    def severity_worsened(self) -> bool:
        """Whether the severity moved to a worse one on the later side."""
        moved = self.severity_change
        if moved is None:
            return False
        return severity_rank(moved[1]) < severity_rank(moved[0])

    @property
    def waiver_change(self) -> tuple[bool, bool] | None:
        """``(before, after)`` where the waiver was added or lifted."""
        if self.before is None or self.after is None:
            return None
        if self.before.waived == self.after.waived:
            return None
        return (self.before.waived, self.after.waived)

    @property
    def changed(self) -> bool:
        """
        Whether anything about this finding moved at all.

        A waiver counts. Nothing on the instance moved when one is added, and
        that is exactly why it belongs in the comparison: the alert going
        quiet is a decision somebody made, and a comparison that showed only
        the instance would present it as the problem having gone away.
        """
        if self.status == PASSING:
            return False
        if self.status != OPEN:
            return True
        return self.severity_change is not None or self.waiver_change is not None

    def as_dict(self) -> dict[str, Any]:
        moved = self.severity_change
        return {
            "id": self.id,
            "category": self.category,
            "status": self.status,
            "before": self.before.as_dict() if self.before else None,
            "after": self.after.as_dict() if self.after else None,
            "waiverChange": (
                {"from": self.waiver_change[0], "to": self.waiver_change[1]}
                if self.waiver_change
                else None
            ),
            "severityChange": (
                {"from": moved[0], "to": moved[1], "worsened": self.severity_worsened}
                if moved
                else None
            ),
        }


def _category_of(identifier: str) -> str:
    """
    Which area a finding belongs to, from the catalogue where it has an entry.

    Header names and exposed paths have no catalogue entry until one is built
    for them on demand, which :func:`~opencloud_local_scan.hardening.describe`
    does. It answers for anything, and the entry it invents for an identifier
    this build does not know carries no category - which is right, because a
    finding filed somewhere plausible would be filtered out by a
    ``--category`` that should have shown it.
    """
    return describe(identifier).category


def _checks(document: Mapping[str, Any]) -> dict[str, Side]:
    """Every extra check a document recorded, by identifier."""
    entries = document.get("extraChecks")
    if not isinstance(entries, Sequence) or isinstance(entries, str):
        return {}
    sides: dict[str, Side] = {}
    for entry in entries:
        if not isinstance(entry, Mapping) or not entry.get("id"):
            continue
        sides[str(entry["id"])] = Side(
            severity=normalise_severity(entry.get("severity")),
            passed=bool(entry.get("passed")),
            waived=bool(entry.get("ignored")),
        )
    return sides


def _advisories(document: Mapping[str, Any]) -> dict[str, Side]:
    """
    Every advisory a document matched, by identifier.

    An advisory is only ever listed when it applies, so a listed one is a
    failing side and the absence of one is absence, not a pass. That is why
    an advisory that stops matching comes out as ``disappeared`` rather than
    ``resolved``: the upgrade that removed it is reported by the instance
    changes, and claiming the advisory itself was "resolved" would suggest
    somebody fixed the vulnerability.
    """
    entries = document.get("vulnerabilities")
    if not isinstance(entries, Sequence) or isinstance(entries, str):
        return {}
    sides: dict[str, Side] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        identifier = entry.get("id") or entry.get("identifier")
        if not identifier:
            continue
        sides[str(identifier)] = Side(
            severity=normalise_severity(entry.get("severity")),
            passed=False,
            waived=False,
        )
    return sides


def _status(before: Side | None, after: Side | None) -> str:
    if before is None:
        return APPEARED
    if after is None:
        return DISAPPEARED
    if before.failing and after.failing:
        return OPEN
    if after.failing:
        return INTRODUCED
    if before.failing:
        return RESOLVED
    return PASSING


def _deltas(
    before: Mapping[str, Side], after: Mapping[str, Side], category: str | None
) -> Iterator[Delta]:
    for identifier in sorted(set(before) | set(after)):
        left, right = before.get(identifier), after.get(identifier)
        yield Delta(
            id=identifier,
            category=category if category is not None else _category_of(identifier),
            before=left,
            after=right,
            status=_status(left, right),
        )


def compare(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
    *,
    categories: Sequence[str] = (),
    changed_only: bool = True,
) -> tuple[Delta, ...]:
    """
    Every finding in either document, with the severity on each side.

    ``categories`` keeps only findings filed under one of the named areas;
    an empty sequence keeps all of them. ``changed_only`` drops the findings
    that are passing on both sides and the ones that are open on both sides
    at the same severity - the ones a reader asking "what changed" did not
    ask about. Pass ``False`` for a full side-by-side of everything measured.

    The order is worst first: introduced findings, then severity increases,
    then everything else, each by severity and then by identifier, so the
    first line of the output is the one worth reading first.
    """
    wanted = {str(name).strip().lower() for name in categories if str(name).strip()}
    deltas = [
        *_deltas(_checks(previous), _checks(current), None),
        *_deltas(_advisories(previous), _advisories(current), ADVISORY_CATEGORY),
    ]
    if wanted:
        deltas = [delta for delta in deltas if delta.category.lower() in wanted]
    if changed_only:
        deltas = [delta for delta in deltas if delta.changed]
    return tuple(sorted(deltas, key=_ordering))


def _ordering(delta: Delta) -> tuple[int, int, str]:
    """Worst first: what is new, then what got worse, then the rest."""
    if delta.status in (INTRODUCED, APPEARED):
        rank = 0
    elif delta.severity_worsened:
        rank = 1
    elif delta.status == OPEN:
        rank = 2
    elif delta.status in (RESOLVED, DISAPPEARED):
        rank = 3
    else:
        rank = 4
    side = delta.after or delta.before
    return (rank, severity_rank(side.severity if side else "unknown"), delta.id)


def severity_totals(deltas: Sequence[Delta]) -> dict[str, tuple[int, int]]:
    """
    How many findings were failing at each severity, before and after.

    Only the severities that appear on one of the sides are returned, so a
    caller never has to decide whether a row of zeroes is worth printing.
    Waived findings are counted, because the operator asked not to be
    alerted about them and not for them to stop existing.
    """
    totals: dict[str, list[int]] = {}
    for delta in deltas:
        for index, side in enumerate((delta.before, delta.after)):
            if side is None or not side.failing:
                continue
            totals.setdefault(side.severity, [0, 0])[index] += 1
    return {
        severity: (counts[0], counts[1])
        for severity, counts in sorted(
            totals.items(), key=lambda item: severity_rank(item[0])
        )
    }
