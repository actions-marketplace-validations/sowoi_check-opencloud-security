"""
What the scan looked at, and what it could not look at.

A passed check and a check that never ran leave the same shape in a result
document - nothing - and a reader who cannot tell them apart reads the second
as the first. These tests hold the three properties that stop that: every
check the scanner considered has exactly one state, an unmeasured one always
says why, and none of it touches the grade.
"""

from __future__ import annotations

import pytest

from opencloud_local_scan.coverage import (
    FAILED,
    INCONCLUSIVE,
    NO_ROUTE,
    NOT_APPLICABLE,
    NOT_CHECKED,
    PASSED,
    PREREQUISITE_MISSING,
    PROBE_DISABLED,
    REASONS,
    STATES,
    TIMEOUT,
    UNREADABLE,
    CoverageEntry,
    CoverageRecorder,
    coverage_of,
    gaps,
    summary,
    summary_line,
)
from opencloud_local_scan.scanner import (
    HARDENING_PREREQUISITES,
    ScannerSettings,
    scan,
)
from tests.fake_opencloud import FakeOpenCloud, InstanceBehaviour


def _scan(**settings: object) -> dict:
    """One scan of a default fake instance, with the given settings."""
    with FakeOpenCloud() as fake:
        return scan(fake.host, ScannerSettings(verify_tls=False, **settings))  # type: ignore[arg-type]


def _entries(result: dict) -> dict[str, dict]:
    return {entry["id"]: entry for entry in result["coverage"]["checks"]}


# ------------------------------------------------------- the contract


def test_a_measured_check_carries_no_reason():
    """
    "Passed, because the probe was disabled" is not a sentence.

    Letting a reason ride along with a measurement is how a gap gets read as
    a pass, so the entry refuses to be built that way.
    """
    with pytest.raises(ValueError):
        CoverageEntry("a", "header", PASSED, PROBE_DISABLED)


def test_an_unmeasured_check_must_say_why():
    """A gap without a reason is the absence this block exists to replace."""
    with pytest.raises(ValueError):
        CoverageEntry("a", "header", NOT_CHECKED)


@pytest.mark.parametrize("state", sorted(STATES))
def test_every_state_is_one_of_four(state: str):
    """The four states are the contract; anything else is a typo."""
    entry = CoverageEntry("a", "header", state, "" if state in {PASSED, FAILED} else NOT_APPLICABLE)

    assert entry.state in STATES


def test_an_unknown_state_or_reason_is_refused():
    with pytest.raises(ValueError):
        CoverageEntry("a", "header", "probably")
    with pytest.raises(ValueError):
        CoverageEntry("a", "header", NOT_CHECKED, "because")


def test_the_first_decision_wins():
    """
    A specific reason recorded where the decision was made outranks a
    later, coarser one: "the name has one address" says more than "the
    extra checks are off", and the code that knew it ran first.
    """
    recorder = CoverageRecorder()
    recorder.skipped("tlsByAddress", "addressParity", NOT_APPLICABLE, "One address.")
    recorder.skipped("tlsByAddress", "addressParity", PROBE_DISABLED, "Off.")

    assert recorder.entries["tlsByAddress"].reason == NOT_APPLICABLE


def test_the_total_is_what_this_scan_considered():
    """
    The scanner's checks are dynamic - which paths it probes and which
    addresses it compares depend on the instance - so a fixed denominator
    would be a fiction.
    """
    recorder = CoverageRecorder()
    recorder.measured("a", "header", True)
    recorder.measured("b", "header", False)
    recorder.skipped("c", "tls", NOT_APPLICABLE, "Plain HTTP.")

    assert recorder.counts() == {
        PASSED: 1,
        FAILED: 1,
        NOT_CHECKED: 1,
        INCONCLUSIVE: 0,
        "total": 3,
    }


# --------------------------------------------------- a report that has none


def test_a_report_without_coverage_says_so_rather_than_claiming_none():
    """An older report is one that does not say, not one with no gaps."""
    assert coverage_of({"rating": 5}) is None
    assert gaps({"rating": 5}) == []


def test_a_coverage_block_that_is_not_one_is_not_read():
    """An uploaded report is evidence, and evidence can be malformed."""
    assert coverage_of({"coverage": "all of it"}) is None
    assert coverage_of({"coverage": {"counts": {}}}) is None


# ------------------------------------------------------------- real scans


def test_every_check_has_exactly_one_state_and_the_counts_agree():
    """The summary and the detail are the same list counted two ways."""
    result = _scan(extra_checks=True)
    coverage = result["coverage"]
    identifiers = [entry["id"] for entry in coverage["checks"]]

    assert len(identifiers) == len(set(identifiers))
    assert coverage["counts"]["total"] == len(identifiers)
    assert sum(
        coverage["counts"][state]
        for state in (PASSED, FAILED, NOT_CHECKED, INCONCLUSIVE)
    ) == len(identifiers)
    for entry in coverage["checks"]:
        assert entry["state"] in STATES
        if entry["state"] in {NOT_CHECKED, INCONCLUSIVE}:
            assert entry["reason"] in REASONS
            assert entry["detail"]


def test_every_hardening_the_scanner_can_derive_is_accounted_for():
    """
    A hardening absent from the block is one the reader cannot explain.

    This is what keeps `HARDENING_PREREQUISITES` beside `derive_hardenings`:
    adding a measure there without a prerequisite here fails right now.
    """
    entries = _entries(_scan(extra_checks=True))

    assert set(HARDENING_PREREQUISITES) <= set(entries)
    for name in HARDENING_PREREQUISITES:
        assert entries[name]["group"] == "hardening"


def test_turning_the_extra_checks_off_is_a_disabled_probe_not_a_gap():
    """The operator decided this, and the report says whose decision it was."""
    entries = _entries(_scan(extra_checks=False))

    for check in ("tlsInspection", "caaRecord", "dnssec", "office", "calendar"):
        assert entries[check]["state"] == NOT_CHECKED
        assert entries[check]["reason"] == PROBE_DISABLED


def test_plain_http_makes_the_certificate_checks_inapplicable_not_missing():
    """
    There is no handshake to inspect, so nothing was missed.

    The fake listens on plain HTTP, which is the deployment property this
    distinguishes from a probe that was switched off.
    """
    entries = _entries(_scan(extra_checks=True))

    for check in ("tlsInspection", "caaRecord", "dnssec"):
        assert entries[check]["state"] == NOT_CHECKED
        assert entries[check]["reason"] == NOT_APPLICABLE


def test_a_scanner_without_an_ipv6_route_says_so_rather_than_failing_a_check():
    """
    A timeout that belongs to the machine running the scan is not a fault
    of the instance - the same rule `ScannerSettings.ipv6_enabled` follows.
    """
    entries = _entries(_scan(extra_checks=True, ipv6_enabled=False))

    assert entries["ipv6Reachability"]["state"] == NOT_CHECKED
    assert entries["ipv6Reachability"]["reason"] == "no_route"


def test_a_name_with_one_address_cannot_disagree_with_itself():
    """Address parity needs two addresses; one is not a gap in the scan."""
    entries = _entries(_scan(extra_checks=True, check_all_addresses=True))

    assert entries["addressObservations"]["state"] == NOT_CHECKED
    assert entries["addressObservations"]["reason"] in {NOT_APPLICABLE, PROBE_DISABLED}


def test_a_capability_the_instance_never_published_is_a_missing_prerequisite():
    """
    `derive_hardenings` leaves a measure out when there is nothing to rate,
    which is right and is indistinguishable from a pass. This is where the
    difference is written down.
    """
    entries = _entries(_scan(extra_checks=True))

    assert entries["userEnumerationRestricted"]["state"] == NOT_CHECKED
    assert entries["userEnumerationRestricted"]["reason"] == PREREQUISITE_MISSING
    assert "did not publish" in entries["userEnumerationRestricted"]["detail"]


def test_an_instance_without_a_capabilities_document_says_which_checks_that_cost():
    """The prerequisite is named once and explains a whole family of gaps."""
    behaviour = InstanceBehaviour(capabilities=None)
    with FakeOpenCloud(behaviour) as fake:
        result = scan(fake.host, ScannerSettings(verify_tls=False, extra_checks=True))

    entries = _entries(result)

    assert result["capabilitiesAvailable"] is False
    assert entries["capabilities"]["state"] == NOT_CHECKED
    assert entries["capabilities"]["reason"] == PREREQUISITE_MISSING
    assert entries["passwordPolicyEnforced"]["state"] == NOT_CHECKED


# ------------------------------------------------ coverage explains, never rates


def test_a_waived_failure_is_still_a_failed_measurement():
    """
    A waiver is a decision about alerting, not about evidence.

    Letting it improve the coverage figure would make the one number that
    describes the evidence describe the policy instead.
    """
    with FakeOpenCloud() as fake:
        waived = scan(
            fake.host,
            ScannerSettings(
                verify_tls=False, extra_checks=True, ignore_hardenings=("directoryListing",)
            ),
        )

    entry = _entries(waived).get("directoryListing")

    assert entry is not None
    assert entry["state"] in {PASSED, FAILED}
    assert "reason" not in entry


def test_coverage_does_not_move_the_grade():
    """
    Identical evidence grades identically, however much of it there is.

    The block is additive: removing it from both documents leaves two that
    are equal, which is the whole promise made to existing readers.
    """
    with FakeOpenCloud() as fake:
        first = scan(fake.host, ScannerSettings(verify_tls=False, extra_checks=True))
        second = scan(fake.host, ScannerSettings(verify_tls=False, extra_checks=True))

    assert first["rating"] == second["rating"]
    assert first["ratingExplanation"] == second["ratingExplanation"]
    assert first["coverage"]["counts"] == second["coverage"]["counts"]
    # Nothing in the rating's own arithmetic reads the block.
    assert "coverage" not in str(first["ratingExplanation"])


def test_the_gaps_helper_lists_exactly_what_did_not_conclude():
    result = _scan(extra_checks=False)

    listed = gaps(result)

    assert listed
    assert {entry["state"] for entry in listed} == {NOT_CHECKED}
    assert all(entry["reason"] for entry in listed)


def _document(*entries: tuple[str, str, str, str]) -> dict:
    """A minimal result document carrying the given coverage entries."""
    recorder = CoverageRecorder()
    for check, group, state, reason in entries:
        if state == PASSED:
            recorder.measured(check, group, True)
        elif state == FAILED:
            recorder.measured(check, group, False)
        elif state == NOT_CHECKED:
            recorder.skipped(check, group, reason)
        else:
            recorder.inconclusive(check, group, reason)
    return {"coverage": recorder.as_dict()}


def test_the_summary_puts_every_check_in_exactly_one_bucket():
    document = _document(
        ("a", "hardening", PASSED, ""),
        ("b", "hardening", FAILED, ""),
        ("c", "tls", NOT_CHECKED, PROBE_DISABLED),
        ("d", "dns", INCONCLUSIVE, UNREADABLE),
        ("e", "dns", NOT_CHECKED, TIMEOUT),
        ("f", "addressParity", INCONCLUSIVE, NO_ROUTE),
    )

    totals = summary(document)

    assert totals == {
        "evaluated": 2,
        "skipped": 1,
        "indeterminate": 1,
        # Both the skipped and the inconclusive network reasons land here,
        # and neither is counted twice.
        "networkLimited": 2,
        "total": 6,
    }
    assert totals["total"] == document["coverage"]["counts"]["total"]


def test_the_summary_line_names_the_gaps_and_leaves_out_the_zeroes():
    document = _document(
        ("a", "hardening", PASSED, ""),
        ("b", "tls", NOT_CHECKED, NOT_APPLICABLE),
        ("c", "dns", INCONCLUSIVE, UNREADABLE),
        ("d", "dns", NOT_CHECKED, NO_ROUTE),
    )

    assert summary_line(document) == (
        "1 checks evaluated, 1 skipped, 1 indeterminate, 1 network-limited"
    )

    complete = _document(("a", "hardening", PASSED, ""))

    assert summary_line(complete) == "1 checks evaluated"


def test_a_summary_of_a_report_without_coverage_claims_nothing():
    """
    A document that predates the block is not a document with no gaps.

    ``None`` and ``""`` are what the readers key on, so neither can be
    confused with a scan that measured everything.
    """
    assert summary({}) is None
    assert summary_line({}) == ""
    assert summary({"coverage": {"counts": {"total": 3}}}) is None


def test_a_real_scan_summarises_its_own_coverage():
    result = _scan(extra_checks=False)

    totals = summary(result)
    assert totals is not None
    assert totals["evaluated"] > 0
    assert totals["skipped"] > 0
    assert totals["total"] == len(result["coverage"]["checks"])
    assert summary_line(result).startswith(f"{totals['evaluated']} checks evaluated")
