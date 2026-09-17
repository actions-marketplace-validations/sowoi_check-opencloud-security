"""
What the scan looked at, and what it could not look at.

A grade is a statement about evidence, and evidence has edges. A check that
passed and a check that never ran both leave the same shape in a result
document - an absent finding - and a reader who cannot tell them apart will
read the second as the first. That is the one misreading this module exists
to prevent.

The rules it follows:

* **A state is recorded where the decision is made.** The scanner knows it
  skipped the TLS inspection because the instance answered on plain HTTP; a
  later reader of the document can only guess from an absent key. Guessing
  from absence is exactly what :doc:`ADR 0013 <adr>` forbids, so nothing here
  infers a state - every entry is written by the code that decided it.
* **A missing measurement is never a pass and never a failure.** It is
  ``not_checked`` when the scanner chose not to look, and ``inconclusive``
  when it looked and could not tell. Both carry a machine-readable reason.
* **Coverage explains a grade; it never changes one.** Nothing here feeds
  the rating, the severities, the alert line or the exit code. A scan with
  half its checks skipped gets the same grade for the same evidence - it
  just says so.
* **The set of checks is what this scan considered, not a constant.** The
  scanner's checks are dynamic: the exposed paths it probes, the debug ports
  it dials and the addresses it compares all depend on the instance and the
  settings. A fixed denominator would be a fiction, so the total is the
  number of entries recorded during the scan and the document says as much.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

#: The document version, so a reader can tell this block's shape from a later
#: one. Additive changes keep the number; a change to what a state means does
#: not.
COVERAGE_SCHEMA = 1

#: The check ran and the instance satisfied it.
PASSED = "passed"
#: The check ran and the instance did not satisfy it.
FAILED = "failed"
#: The scanner did not run the check. The reason says why.
NOT_CHECKED = "not_checked"
#: The scanner ran the check and could not reach a conclusion.
INCONCLUSIVE = "inconclusive"

STATES: frozenset[str] = frozenset({PASSED, FAILED, NOT_CHECKED, INCONCLUSIVE})

#: The check cannot apply to this instance as it is deployed. A plain-HTTP
#: instance has no certificate to inspect; a name with one address has no
#: second address to disagree with itself.
NOT_APPLICABLE = "not_applicable"
#: A setting turned the probe off. The operator decided this, and a scan that
#: reports it as a gap is reporting their own configuration back to them.
PROBE_DISABLED = "probe_disabled"
#: The check needs something the instance did not publish - a capabilities
#: document, an authentication challenge, a discovery document, a header it
#: would have rated.
PREREQUISITE_MISSING = "prerequisite_missing"
#: The instance did not answer in time.
TIMEOUT = "timeout"
#: Something answered and could not be understood.
UNREADABLE = "unreadable"
#: There is no route to that address family from where the scan ran.
NO_ROUTE = "no_route"

REASONS: frozenset[str] = frozenset(
    {
        NOT_APPLICABLE,
        PROBE_DISABLED,
        PREREQUISITE_MISSING,
        TIMEOUT,
        UNREADABLE,
        NO_ROUTE,
    }
)

#: The families a check belongs to, which is how the interface groups them.
GROUPS: tuple[str, ...] = (
    "hardening",
    "header",
    "advisoryHeader",
    "advisoryCheck",
    "extraCheck",
    "tls",
    "dns",
    "addressParity",
    "capabilities",
    "updates",
    "integrations",
)


@dataclass(frozen=True)
class CoverageEntry:
    """One check this scan considered, and what became of it."""

    id: str
    group: str
    state: str
    reason: str = ""
    detail: str = ""

    def __post_init__(self) -> None:
        if self.state not in STATES:
            raise ValueError(f"{self.state!r} is not a coverage state")
        if self.reason and self.reason not in REASONS:
            raise ValueError(f"{self.reason!r} is not a coverage reason")
        # A reason explains an absence. Attaching one to a measurement that
        # ran invites a reader to treat "passed, because disabled" as a
        # sentence, which is how a gap becomes a pass.
        if self.state in {PASSED, FAILED} and self.reason:
            raise ValueError("a measured check has no reason")
        if self.state in {NOT_CHECKED, INCONCLUSIVE} and not self.reason:
            raise ValueError("an unmeasured check needs a reason")

    def as_dict(self) -> dict[str, Any]:
        """Render the entry for the result document, camelCase as usual."""
        entry: dict[str, Any] = {"id": self.id, "group": self.group, "state": self.state}
        if self.reason:
            entry["reason"] = self.reason
        if self.detail:
            entry["detail"] = self.detail
        return entry


@dataclass
class CoverageRecorder:
    """
    Collects coverage as the scan makes its decisions.

    One recorder per scan. Every method takes the identifier the result
    document already uses for that check, so a coverage entry and the finding
    it explains are joined by the same string.
    """

    entries: dict[str, CoverageEntry] = field(default_factory=dict)

    def measured(self, check: str, group: str, passed: bool) -> None:
        """Record a check that ran and reached a conclusion."""
        self._add(CoverageEntry(check, group, PASSED if passed else FAILED))

    def skipped(self, check: str, group: str, reason: str, detail: str = "") -> None:
        """Record a check the scanner decided not to run."""
        self._add(CoverageEntry(check, group, NOT_CHECKED, reason, detail))

    def inconclusive(self, check: str, group: str, reason: str, detail: str = "") -> None:
        """Record a check that ran and could not decide."""
        self._add(CoverageEntry(check, group, INCONCLUSIVE, reason, detail))

    def _add(self, entry: CoverageEntry) -> None:
        # First write wins. A check is decided once, at the point that
        # decided it; a later, coarser caller must not overwrite the specific
        # reason an earlier one already recorded.
        self.entries.setdefault(entry.id, entry)

    def counts(self) -> dict[str, int]:
        """How many checks are in each state, and how many there are."""
        counts = {state: 0 for state in (PASSED, FAILED, NOT_CHECKED, INCONCLUSIVE)}
        for entry in self.entries.values():
            counts[entry.state] += 1
        counts["total"] = len(self.entries)
        return counts

    def as_dict(self) -> dict[str, Any]:
        """The ``coverage`` block of the result document."""
        return {
            "schema": COVERAGE_SCHEMA,
            "counts": self.counts(),
            "checks": [
                entry.as_dict()
                for entry in sorted(
                    self.entries.values(), key=lambda item: (item.group, item.id)
                )
            ],
        }


def coverage_of(result: Mapping[str, Any]) -> dict[str, Any] | None:
    """
    The coverage block of a result document, or nothing when it has none.

    A report written before this block existed is not a report with no gaps;
    it is a report that does not say. Every reader has to tell those apart,
    so they all ask here rather than reaching for the key.
    """
    coverage = result.get("coverage")
    if not isinstance(coverage, Mapping):
        return None
    if not isinstance(coverage.get("checks"), list):
        return None
    return dict(coverage)


def gaps(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Every check in a result document that did not reach a conclusion."""
    coverage = coverage_of(result)
    if coverage is None:
        return []
    return [
        dict(entry)
        for entry in coverage["checks"]
        if isinstance(entry, Mapping)
        and entry.get("state") in {NOT_CHECKED, INCONCLUSIVE}
    ]
