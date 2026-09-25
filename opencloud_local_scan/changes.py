"""
Why two results differ, said only as far as the evidence supports.

A comparison that reports "rating 5 -> 3" has told the reader what happened
and nothing about why, and the why is the whole question. Did the instance
get worse, or did the advisory database learn something it did not know last
week? Both produce the same drop and need opposite responses.

This turns two result documents into a list of contributing changes, grouped
by what kind of thing changed. The discipline that makes it worth reading is
refusing to overstate:

* **Several changes may contribute.** An upgrade, a new advisory and an
  expired waiver can land in the same week, and forcing one of them to be
  "the cause" would be a guess dressed as a finding.
* **A digest that changed establishes that reference data changed.** It does
  not establish that the reference data caused any particular grade to move.
  The wording says exactly that much.
* **Missing context is stated, never filled in.** A report written before
  provenance existed cannot say whether the scanner was upgraded between the
  two runs, so the comparison reports a limitation instead of assuming.
* **An unexplained difference is its own category.** Leaving a change out
  because nothing here accounts for it would make the list look complete
  when it is not.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .coverage import FAILED, INCONCLUSIVE, PASSED, considered, coverage_of
from .fingerprint import digests as fingerprint_digests
from .fingerprint import drift as configuration_drift
from .fingerprint import incomparable as configuration_incomparable
from .provenance import provenance_of

#: The instance itself changed: a different version, a check that started or
#: stopped failing.
INSTANCE = "instance"
#: What the scanner judged against changed: advisories, the release schedule,
#: or a support window that simply elapsed.
REFERENCE_DATA = "referenceData"
#: The scanner changed: a different version, or a different amount of it ran.
SCANNER = "scanner"
#: The operator's policy changed: a waiver expired, was added or removed.
POLICY = "policy"
#: Something moved and nothing recorded here accounts for it.
UNKNOWN = "unknown"

CATEGORIES: tuple[str, ...] = (INSTANCE, REFERENCE_DATA, SCANNER, POLICY, UNKNOWN)


@dataclass(frozen=True)
class Change:
    """One thing that differs between two results, and how sure we are."""

    category: str
    #: A stable token for software, so a client can branch on the kind of
    #: change without parsing the sentence.
    code: str
    #: One sentence for a person, phrased to claim only what is established.
    summary: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Render the change for JSON output."""
        return {
            "category": self.category,
            "code": self.code,
            "summary": self.summary,
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class Explanation:
    """Everything that contributed, and everything that could not be read."""

    changes: tuple[Change, ...] = ()
    #: What this comparison could not establish, in plain words. A missing
    #: block is a limitation, not an absence of change.
    limitations: tuple[str, ...] = ()

    @property
    def rating_moved(self) -> bool:
        return any(change.code == "ratingChanged" for change in self.changes)

    def by_category(self, category: str) -> tuple[Change, ...]:
        return tuple(change for change in self.changes if change.category == category)

    def as_dict(self) -> dict[str, Any]:
        return {
            "changes": [change.as_dict() for change in self.changes],
            "limitations": list(self.limitations),
        }


def _rating(document: Mapping[str, Any]) -> int | None:
    try:
        return int(document["rating"])
    except (KeyError, TypeError, ValueError):
        return None


def _block(value: Any) -> Mapping[str, Any]:
    """A nested block, or an empty one when a report carries something else."""
    return value if isinstance(value, Mapping) else {}


def _count(value: Any) -> int:
    """A count from a report, or 0 when it is not one."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _patterns(value: Any) -> set[str]:
    """Waiver patterns from a report, skipping anything that is not a string."""
    if isinstance(value, str) or not isinstance(value, Sequence):
        return set()
    return {entry for entry in value if isinstance(entry, str)}


def _findings(document: Mapping[str, Any]) -> set[str]:
    """The identifiers of every check that is currently failing and counted."""
    checks = document.get("extraChecks")
    if not isinstance(checks, Sequence):
        return set()
    return {
        str(entry.get("id"))
        for entry in checks
        if isinstance(entry, Mapping)
        and entry.get("passed") is False
        and not entry.get("ignored")
    }


def _advisories(document: Mapping[str, Any]) -> set[str]:
    listed = document.get("vulnerabilities")
    if not isinstance(listed, Sequence):
        return set()
    return {
        str(entry.get("id") or entry.get("identifier"))
        for entry in listed
        if isinstance(entry, Mapping)
    }


def explain(
    previous: Mapping[str, Any], current: Mapping[str, Any]
) -> Explanation:
    """
    Every change that contributed to the difference between two results.

    Both arguments are result documents. Either may predate provenance or
    coverage, in which case what cannot be established is reported as a
    limitation rather than guessed at.
    """
    changes: list[Change] = []
    limitations: list[str] = []

    before_rating, after_rating = _rating(previous), _rating(current)
    if before_rating is not None and after_rating is not None and before_rating != after_rating:
        changes.append(
            Change(
                UNKNOWN,
                "ratingChanged",
                f"The grade moved from {before_rating} to {after_rating}. "
                "The changes below are what differed between the two scans.",
                {"from": before_rating, "to": after_rating},
            )
        )

    before_configuration = fingerprint_digests(previous)
    after_configuration = fingerprint_digests(current)
    if not before_configuration or not after_configuration:
        limitations.append(
            "At least one report does not record a configuration fingerprint, "
            "so a deployment that was reconfigured without moving a grade "
            "cannot be told from one that was left alone."
        )
    else:
        narrowed = configuration_incomparable(before_configuration, after_configuration)
        if narrowed:
            limitations.append(
                "The two scans looked at different things in the "
                f"{', '.join(narrowed)} configuration, so those group(s) are "
                "not compared here - a difference in them would not show up "
                "as a change."
            )

    changes.extend(_instance_changes(previous, current))
    changes.extend(_reference_changes(previous, current, limitations))
    changes.extend(_scanner_changes(previous, current, limitations))
    changes.extend(_policy_changes(previous, current, limitations))

    # A check that stopped failing and a check that stopped being made look
    # identical in the findings list. When both moved in the same direction,
    # say so rather than letting the reader read the first as the second.
    codes = {change.code for change in changes}
    if "findingsResolved" in codes and "coverageChanged" in codes:
        coverage_change = next(
            change for change in changes if change.code == "coverageChanged"
        )
        if int(coverage_change.evidence.get("to", 0)) < int(
            coverage_change.evidence.get("from", 0)
        ):
            limitations.append(
                "The second scan reached a conclusion on fewer checks than the "
                "first, so some of the checks that stopped failing may simply "
                "not have been measured."
            )

    # The rating line is a heading for the rest, so it is only "unknown" when
    # nothing else was found to put under it.
    if len(changes) == 1 and changes[0].code == "ratingChanged":
        limitations.append(
            "Nothing recorded in either report accounts for the change in "
            "grade. Comparing the two documents directly is the next step."
        )

    return Explanation(tuple(changes), tuple(dict.fromkeys(limitations)))


def _instance_changes(
    previous: Mapping[str, Any], current: Mapping[str, Any]
) -> list[Change]:
    """What the instance itself did differently."""
    changes: list[Change] = []

    before, after = str(previous.get("version") or ""), str(current.get("version") or "")
    if before and after and before != after:
        changes.append(
            Change(
                INSTANCE,
                "versionChanged",
                f"The instance moved from {before} to {after}.",
                {"from": before, "to": after},
            )
        )

    drifted = configuration_drift(
        fingerprint_digests(previous), fingerprint_digests(current)
    )
    if drifted:
        changes.append(
            Change(
                INSTANCE,
                "configurationChanged",
                f"The {', '.join(drifted)} configuration is not the one the "
                "earlier scan saw. That establishes the deployment changed; "
                "what it was changed to is not recorded, by design.",
                {"groups": list(drifted)},
            )
        )

    # A check only one side considered did not start or stop failing on the
    # instance; the scanner started or stopped making it, which
    # `_scanner_changes` reports. Taken out only where both sides list their
    # checks, so a report that cannot say is read as it always was.
    only_after, only_before = _one_sided_checks(previous, current)
    appeared = _findings(current) - _findings(previous) - only_after
    resolved = _findings(previous) - _findings(current) - only_before
    if appeared:
        changes.append(
            Change(
                INSTANCE,
                "findingsAppeared",
                f"{len(appeared)} check(s) started failing.",
                {"checks": sorted(appeared)},
            )
        )
    if resolved:
        changes.append(
            Change(
                INSTANCE,
                "findingsResolved",
                f"{len(resolved)} check(s) stopped failing.",
                {"checks": sorted(resolved)},
            )
        )
    return changes


def _reference_changes(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
    limitations: list[str],
) -> list[Change]:
    """What the scanner judged against, and whether it was the same."""
    changes: list[Change] = []

    new_advisories = _advisories(current) - _advisories(previous)
    if new_advisories:
        changes.append(
            Change(
                REFERENCE_DATA,
                "advisoriesAdded",
                f"{len(new_advisories)} advisory record(s) apply to this "
                "version now and did not before.",
                {"advisories": sorted(new_advisories)},
            )
        )

    before, after = provenance_of(previous), provenance_of(current)
    if before is None or after is None:
        limitations.append(
            "At least one report does not record which advisory database and "
            "release schedule it was judged against, so a change in reference "
            "data cannot be told from a change in the instance."
        )
        return changes

    before_advisory = _block(before.get("advisoryData")).get("digest")
    after_advisory = _block(after.get("advisoryData")).get("digest")
    if before_advisory != after_advisory:
        changes.append(
            Change(
                REFERENCE_DATA,
                "advisoryDataChanged",
                "The advisory database was not the same in both scans. That "
                "establishes the reference data changed; it does not by "
                "itself establish that any particular finding changed "
                "because of it.",
                {"from": before_advisory, "to": after_advisory},
            )
        )

    before_schedule = _block(before.get("scheduleData")).get("digest")
    after_schedule = _block(after.get("scheduleData")).get("digest")
    if before_schedule != after_schedule:
        changes.append(
            Change(
                REFERENCE_DATA,
                "scheduleDataChanged",
                "The release schedule was not the same in both scans, so a "
                "support window may be drawn differently.",
                {
                    "from": before_schedule,
                    "to": after_schedule,
                    "publishedBefore": _block(before.get("scheduleData")).get("updated"),
                    "publishedAfter": _block(after.get("scheduleData")).get("updated"),
                },
            )
        )
    elif previous.get("EOL") is False and current.get("EOL") is True:
        # Same schedule, same instance, different verdict: the only thing
        # left that can have moved is the date.
        changes.append(
            Change(
                REFERENCE_DATA,
                "supportWindowElapsed",
                "The release reached end of life between the two scans "
                "against the same release schedule - time passed rather than "
                "anything changing.",
                {
                    "scannedBefore": before.get("scannedAt"),
                    "scannedAfter": after.get("scannedAt"),
                },
            )
        )

    if before.get("releaseTrack") != after.get("releaseTrack"):
        changes.append(
            Change(
                REFERENCE_DATA,
                "releaseTrackChanged",
                f"The scans asked for different release tracks: "
                f"{before.get('releaseTrack')} then {after.get('releaseTrack')}. "
                "A track changes how a version is judged, never what was "
                "observed.",
                {"from": before.get("releaseTrack"), "to": after.get("releaseTrack")},
            )
        )
    return changes


def _scanner_changes(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
    limitations: list[str],
) -> list[Change]:
    """Whether the thing doing the measuring was the same, and did as much."""
    changes: list[Change] = []
    before, after = provenance_of(previous), provenance_of(current)
    if (
        before is not None
        and after is not None
        and before.get("scannerVersion") != after.get("scannerVersion")
    ):
        changes.append(
                Change(
                SCANNER,
                "scannerVersionChanged",
                f"The scanner moved from {before.get('scannerVersion')} to "
                f"{after.get('scannerVersion')}, so the two scans may not "
                "have made the same set of checks.",
                {
                    "from": before.get("scannerVersion"),
                    "to": after.get("scannerVersion"),
                },
            )
        )

    before_coverage, after_coverage = coverage_of(previous), coverage_of(current)
    if before_coverage is None or after_coverage is None:
        limitations.append(
            "At least one report does not record what it measured, so a "
            "check that stopped failing cannot be told from one that stopped "
            "being checked."
        )
        return changes

    only_after, only_before = _one_sided_checks(previous, current)
    if only_after:
        failing = sorted(only_after & _findings(current))
        changes.append(
            Change(
                SCANNER,
                "checksNewlyMeasured",
                f"The second scan made {len(only_after)} check(s) the first "
                f"did not, {len(failing)} of them failing. A check that was "
                "not made before was not passing before, so these say "
                "nothing about the instance having changed.",
                {"checks": sorted(only_after), "failing": failing},
            )
        )
    if only_before:
        failing = sorted(only_before & _findings(previous))
        changes.append(
            Change(
                SCANNER,
                "checksNoLongerMeasured",
                f"The first scan made {len(only_before)} check(s) the second "
                f"did not, {len(failing)} of them failing then. Nothing says "
                "those failures were fixed - the second scan did not look.",
                {"checks": sorted(only_before), "failing": failing},
            )
        )
    if considered(previous) is None or considered(current) is None:
        limitations.append(
            "At least one report does not list the individual checks it made, "
            "so a check that started or stopped failing cannot be told from "
            "one that only one of the two scans made."
        )

    before_counts = _block(before_coverage.get("counts"))
    after_counts = _block(after_coverage.get("counts"))
    before_measured = _count(before_counts.get("passed")) + _count(before_counts.get("failed"))
    after_measured = _count(after_counts.get("passed")) + _count(after_counts.get("failed"))
    if before_measured != after_measured:
        changes.append(
            Change(
                SCANNER,
                "coverageChanged",
                f"The scans reached a conclusion on a different number of "
                f"checks: {before_measured} then {after_measured}. A grade "
                "computed from less evidence is not a better or worse grade, "
                "but it is a different statement.",
                {"from": before_measured, "to": after_measured},
            )
        )

    # Counts can stand still while one check goes dark and another comes into
    # view, so the loss is named check by check, whatever the totals did.
    lost = _coverage_lost(before_coverage, after_coverage)
    if lost:
        changes.append(
            Change(
                SCANNER,
                "coverageRegressed",
                f"{len(lost)} check(s) the first scan reached a conclusion on "
                "were inconclusive in the second. That says the scan saw "
                "less, not that the instance got better or worse, and it "
                "does not change the grade.",
                {"checks": dict(sorted(lost.items()))},
            )
        )
    return changes


def _one_sided_checks(
    previous: Mapping[str, Any], current: Mapping[str, Any]
) -> tuple[set[str], set[str]]:
    """
    The checks only the later scan considered, and those only the earlier did.

    Both empty unless both documents list their checks: a side that does not
    say cannot be shown to have lacked anything.
    """
    before, after = considered(previous), considered(current)
    if before is None or after is None:
        return set(), set()
    return set(after) - set(before), set(before) - set(after)


def _coverage_lost(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> dict[str, str]:
    """Checks measured in ``before`` and inconclusive in ``after``, with the reason."""
    measured = {
        str(entry.get("id"))
        for entry in before.get("checks") or ()
        if isinstance(entry, Mapping) and entry.get("state") in {PASSED, FAILED}
    }
    return {
        str(entry.get("id")): str(entry.get("reason") or "unknown")
        for entry in after.get("checks") or ()
        if isinstance(entry, Mapping)
        and entry.get("state") == INCONCLUSIVE
        and str(entry.get("id")) in measured
    }


def _policy_changes(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
    limitations: list[str],
) -> list[Change]:
    """What the operator decided to accept, and whether it still holds."""
    changes: list[Change] = []
    before, after = provenance_of(previous), provenance_of(current)
    if before is None or after is None:
        return changes

    before_waivers = _block(before.get("waivers"))
    after_waivers = _block(after.get("waivers"))
    before_active = _patterns(before_waivers.get("active"))
    after_active = _patterns(after_waivers.get("active"))
    newly_expired = _patterns(after_waivers.get("expired")) - _patterns(
        before_waivers.get("expired")
    )

    if newly_expired:
        changes.append(
            Change(
                POLICY,
                "waiversExpired",
                f"{len(newly_expired)} waiver(s) expired between the two "
                "scans, so checks they were suppressing can alert again.",
                {"patterns": sorted(newly_expired)},
            )
        )
    added = after_active - before_active
    removed = before_active - after_active - newly_expired
    if added:
        changes.append(
            Change(
                POLICY,
                "waiversAdded",
                f"{len(added)} waiver(s) are in force that were not before.",
                {"patterns": sorted(added)},
            )
        )
    if removed:
        changes.append(
            Change(
                POLICY,
                "waiversRemoved",
                f"{len(removed)} waiver(s) are no longer in force.",
                {"patterns": sorted(removed)},
            )
        )
    return changes
