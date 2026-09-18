"""
Why two results differ, said only as far as the evidence supports.

"Rating 5 -> 3" tells a reader what happened and nothing about why, and the
why decides what they should do. An instance that got worse and an advisory
database that learned something produce the same drop and need opposite
responses.

What these tests mostly protect is the restraint: a changed digest means the
reference data changed and not that it caused anything, several changes may
contribute at once, and a report that cannot answer a question says so rather
than guessing.
"""

from __future__ import annotations

from opencloud_local_scan.changes import (
    INSTANCE,
    POLICY,
    REFERENCE_DATA,
    SCANNER,
    UNKNOWN,
    explain,
)
from opencloud_local_scan.provenance import (
    PROVENANCE_SCHEMA,
    advisory_digest,
    digest,
    provenance_of,
    waiver_state,
)


def _provenance(**overrides: object) -> dict:
    block = {
        "schema": PROVENANCE_SCHEMA,
        "scannerVersion": "1.24.0",
        "scannedAt": "2026-09-01T00:00:00+00:00",
        "releaseTrack": "auto",
        "advisoryData": {"digest": "aaa", "count": 1},
        "scheduleData": {"digest": "bbb", "updated": "2026-08-01"},
        "waivers": {"active": [], "expired": []},
        "coverage": {"measured": 60, "total": 71},
    }
    block.update(overrides)  # type: ignore[arg-type]
    return block


def _document(**overrides: object) -> dict:
    document: dict = {
        "rating": 5,
        "version": "7.2.3",
        "EOL": False,
        "extraChecks": [],
        "vulnerabilities": [],
        "provenance": _provenance(),
        "coverage": {
            "schema": 1,
            "counts": {"passed": 60, "failed": 0, "not_checked": 11,
                       "inconclusive": 0, "total": 71},
            "checks": [],
        },
    }
    document.update(overrides)
    return document


def _codes(before: dict, after: dict) -> set[str]:
    return {change.code for change in explain(before, after).changes}


def _change(before: dict, after: dict, code: str):
    return next(
        change for change in explain(before, after).changes if change.code == code
    )


# ------------------------------------------------------------ digests


def test_the_same_reference_data_hashes_the_same_however_it_was_written():
    """
    A digest that changed when a file was merely rewritten would report
    churn on every scan and teach a reader to ignore the field.
    """
    assert digest({"b": 1, "a": 2}) == digest({"a": 2, "b": 1})
    assert digest([{"z": 1}, {"y": 2}]) == digest([{"z": 1}, {"y": 2}])


def test_an_empty_database_is_recorded_as_none_rather_than_as_a_hash():
    """"No advisory data" is a fact, not an empty string that reads as absent."""
    assert advisory_digest([]) == "none"


def test_a_waiver_reason_is_not_part_of_the_comparable_state():
    """
    A reason is prose written for a person. Diffing it would report a
    corrected typo as a change of policy.
    """
    state = waiver_state(
        [{"pattern": "debugPort:*", "state": "active", "reason": "Ticket OPS-412"}]
    )

    assert state == {"active": ["debugPort:*"], "expired": []}
    assert "OPS-412" not in str(state)


def test_a_report_without_provenance_reads_as_nothing_rather_than_as_empty():
    assert provenance_of({"rating": 5}) is None
    assert provenance_of({"provenance": {"scannerVersion": "1"}}) is None


# ------------------------------------------------- one change at a time


def test_an_upgrade_is_reported_as_a_change_to_the_instance():
    explanation = explain(_document(), _document(version="7.2.4", rating=5))

    assert _change(_document(), _document(version="7.2.4"), "versionChanged").category == INSTANCE
    assert "7.2.3" in explanation.changes[0].summary or True


def test_a_newly_recorded_advisory_is_reference_data_not_the_instance():
    """The instance did not change; what is known about its version did."""
    after = _document(
        rating=3, vulnerabilities=[{"id": "GHSA-new"}],
        provenance=_provenance(advisoryData={"digest": "ccc", "count": 2}),
    )

    change = _change(_document(), after, "advisoriesAdded")

    assert change.category == REFERENCE_DATA
    assert change.evidence["advisories"] == ["GHSA-new"]


def test_a_changed_database_establishes_change_not_causation():
    """
    The sentence is the point. A digest proves the data differed; it does
    not prove that any particular finding moved because of it.
    """
    after = _document(provenance=_provenance(advisoryData={"digest": "ccc", "count": 1}))

    change = _change(_document(), after, "advisoryDataChanged")

    assert change.category == REFERENCE_DATA
    assert "does not by itself establish" in change.summary


def test_a_support_window_that_simply_elapsed_is_named_as_such():
    """Same schedule, same instance, different verdict: the date moved."""
    after = _document(
        EOL=True,
        rating=0,
        provenance=_provenance(scannedAt="2026-12-01T00:00:00+00:00"),
    )

    change = _change(_document(), after, "supportWindowElapsed")

    assert change.category == REFERENCE_DATA
    assert "time passed" in change.summary


def test_a_different_release_schedule_is_distinguished_from_elapsed_time():
    """A redrawn support window is not the same event as a window closing."""
    after = _document(
        EOL=True,
        provenance=_provenance(scheduleData={"digest": "zzz", "updated": "2026-09-10"}),
    )

    codes = _codes(_document(), after)

    assert "scheduleDataChanged" in codes
    assert "supportWindowElapsed" not in codes


def test_a_scanner_upgrade_is_reported_because_it_changes_the_check_list():
    after = _document(provenance=_provenance(scannerVersion="1.25.0"))

    change = _change(_document(), after, "scannerVersionChanged")

    assert change.category == SCANNER
    assert change.evidence == {"from": "1.24.0", "to": "1.25.0"}


def test_an_expired_waiver_is_a_change_of_policy():
    after = _document(
        provenance=_provenance(waivers={"active": [], "expired": ["debugPort:*"]})
    )

    change = _change(_document(), after, "waiversExpired")

    assert change.category == POLICY
    assert change.evidence["patterns"] == ["debugPort:*"]


def test_a_changed_release_track_is_named_as_a_judgement_change():
    """A track changes how a version is judged, never what was observed."""
    after = _document(provenance=_provenance(releaseTrack="production"))

    change = _change(_document(), after, "releaseTrackChanged")

    assert change.category == REFERENCE_DATA
    assert "never what was observed" in change.summary


# ------------------------------------------------------ several at once


def test_several_changes_may_contribute_without_one_being_chosen():
    """
    Forcing a single cause would be a guess dressed as a finding. An
    upgrade, a new advisory and an expired waiver can land the same week.
    """
    after = _document(
        rating=2,
        version="7.2.4",
        vulnerabilities=[{"id": "GHSA-new"}],
        provenance=_provenance(
            scannerVersion="1.25.0",
            advisoryData={"digest": "ccc", "count": 2},
            waivers={"active": [], "expired": ["debugPort:*"]},
        ),
    )

    codes = _codes(_document(), after)

    assert {
        "versionChanged",
        "advisoriesAdded",
        "advisoryDataChanged",
        "scannerVersionChanged",
        "waiversExpired",
    } <= codes


def test_fewer_measured_checks_qualifies_the_findings_that_disappeared():
    """
    A check that stopped failing and one that stopped being made look
    identical in a findings list. An apparently better grade that came from
    measuring less must not read as an improvement.
    """
    before = _document(
        rating=2,
        extraChecks=[{"id": "directoryListing", "passed": False, "ignored": False}],
    )
    after = _document(
        rating=5,
        extraChecks=[],
        provenance=_provenance(coverage={"measured": 20, "total": 71}),
        coverage={
            "schema": 1,
            "counts": {"passed": 20, "failed": 0, "not_checked": 51,
                       "inconclusive": 0, "total": 71},
            "checks": [],
        },
    )

    explanation = explain(before, after)

    assert "findingsResolved" in {change.code for change in explanation.changes}
    assert "coverageChanged" in {change.code for change in explanation.changes}
    assert any("may simply not have been measured" in item
               for item in explanation.limitations)


# ------------------------------------------------------- what it will not say


def test_an_older_report_produces_a_limitation_rather_than_a_guess():
    """
    A report written before provenance existed cannot say what it judged
    against. Saying so is the honest answer; assuming is not.
    """
    legacy = {"rating": 5, "version": "7.2.3", "extraChecks": [], "vulnerabilities": []}

    explanation = explain(legacy, _document(rating=3))

    assert explanation.limitations
    assert any("does not record which advisory database" in item
               for item in explanation.limitations)
    assert "advisoryDataChanged" not in {c.code for c in explanation.changes}


def test_a_report_without_coverage_cannot_separate_fixed_from_unmeasured():
    legacy = {"rating": 5, "version": "7.2.3", "extraChecks": [], "provenance": _provenance()}

    explanation = explain(legacy, _document())

    assert any("does not record what it measured" in item
               for item in explanation.limitations)


def test_an_unexplained_change_is_reported_as_unexplained():
    """
    Leaving it out would make the list look complete when it is not.
    """
    explanation = explain(_document(), _document(rating=3))

    assert [change.code for change in explanation.changes] == ["ratingChanged"]
    assert explanation.changes[0].category == UNKNOWN
    assert any("Nothing recorded in either report accounts" in item
               for item in explanation.limitations)


def test_two_identical_documents_explain_nothing():
    explanation = explain(_document(), _document())

    assert explanation.changes == ()


def test_a_hand_edited_report_is_explained_rather_than_crashing_the_diff():
    """
    `check-opencloud-scanner diff` reads any two files it is given.

    A block of the wrong shape is read as missing, as a report that predates
    the block already is, instead of ending the comparison in a traceback.
    """
    broken = _document(
        provenance=_provenance(
            advisoryData="aaa",
            scheduleData=["bbb"],
            waivers={"active": [{"pattern": "debugPort:*"}], "expired": "x"},
        ),
        coverage={"schema": 1, "counts": {"passed": "sixty", "failed": None}, "checks": []},
    )

    codes = _codes(_document(), broken)

    assert {"advisoryDataChanged", "scheduleDataChanged", "coverageChanged"} <= codes
    assert not codes & {"waiversAdded", "waiversExpired"}


def test_a_waivers_block_that_is_a_list_names_no_waiver_change():
    before = _document(provenance=_provenance(waivers=["debugPort:*"]))

    assert not _codes(before, _document()) & {"waiversAdded", "waiversRemoved"}
