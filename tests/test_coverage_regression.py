"""Tests for coverage regression alerts: a measured check that became inconclusive."""

from __future__ import annotations

import json

import check_opencloud_security as check
from opencloud_local_scan.baseline import load_baseline, snapshot_of
from opencloud_local_scan.changes import explain

HOST = "opencloud.example.com"


def _document(rating: int = 5, **states: str) -> dict:
    """A result document whose coverage block holds the given check states."""
    checks = []
    for name, state in states.items():
        entry = {"id": name, "group": "dns", "state": state}
        if state in {"inconclusive", "not_checked"}:
            entry["reason"] = "timeout" if state == "inconclusive" else "probe_disabled"
        checks.append(entry)
    return {"rating": rating, "coverage": {"schema": 1, "counts": {}, "checks": checks}}


def _apply(tmp_path, response, exit_code=check.NagiosExitCode.OK, *, warn_on_new=False):
    """Run the plugin's baseline step against a baseline file in tmp_path."""
    context = check.ScanContext(
        host=HOST,
        baseline_path=str(tmp_path / "baseline.json"),
        warn_on_new=warn_on_new,
    )
    return check._apply_baseline(
        context,
        response,
        hardenings=[],
        waived=[],
        message=f"{exit_code.name}: original",
        exit_code=exit_code,
    )


def test_a_measured_check_that_becomes_inconclusive_warns_without_moving_the_rating(tmp_path):
    """The grade stood still while the evidence behind it shrank; that has to be said."""
    _apply(tmp_path, _document(caaRecord="passed", dnssec="passed"))
    message, code, lines, comparison = _apply(
        tmp_path, _document(caaRecord="inconclusive", dnssec="passed")
    )

    assert comparison.coverage_lost == {"caaRecord": "timeout"}
    assert comparison.current.rating == comparison.previous.rating == 5
    assert code is check.NagiosExitCode.WARNING
    # The original OK message is carried without its own "OK: ", so the alert
    # line never reads as both a WARNING and an OK.
    assert message == (
        "WARNING: 1 previously measured check(s) are now inconclusive; "
        "the rating is unchanged (original)"
    )
    assert any(line.startswith("Coverage regressed (1)") for line in lines)
    assert comparison.as_dict()["coverage_regressed"] == {"caaRecord": "timeout"}


def test_an_unchanged_coverage_does_not_warn(tmp_path):
    """Without a lost measurement the run stays OK, or the alert means nothing."""
    _apply(tmp_path, _document(caaRecord="passed"))
    message, code, _, comparison = _apply(tmp_path, _document(caaRecord="passed"))

    assert comparison.coverage_lost == {}
    assert (message, code) == ("OK: original", check.NagiosExitCode.OK)


def test_a_check_that_was_never_measured_is_not_a_regression(tmp_path):
    """Inconclusive both times is a standing gap, not a new one."""
    _apply(tmp_path, _document(caaRecord="inconclusive"))
    _, code, _, comparison = _apply(tmp_path, _document(caaRecord="inconclusive"))

    assert comparison.coverage_lost == {}
    assert code is check.NagiosExitCode.OK


def test_a_check_the_operator_turned_off_is_not_a_regression(tmp_path):
    """Only 'ran and could not tell' counts; a disabled probe is the operator's choice."""
    _apply(tmp_path, _document(caaRecord="passed"))
    _, code, _, comparison = _apply(tmp_path, _document(caaRecord="not_checked"))

    assert comparison.coverage_lost == {}
    assert code is check.NagiosExitCode.OK


def test_a_lost_check_keeps_warning_until_it_is_measured_again(tmp_path):
    """One missed interval must not make the gap the new normal."""
    _apply(tmp_path, _document(caaRecord="passed"))
    _apply(tmp_path, _document(caaRecord="inconclusive"))
    _, still, _, _ = _apply(tmp_path, _document(caaRecord="inconclusive"))
    _apply(tmp_path, _document(caaRecord="passed"))
    _, recovered, _, comparison = _apply(tmp_path, _document(caaRecord="inconclusive"))

    assert still is check.NagiosExitCode.WARNING
    assert recovered is check.NagiosExitCode.WARNING
    assert comparison.coverage_lost == {"caaRecord": "timeout"}


def test_a_worse_state_keeps_its_own_message(tmp_path):
    """The coverage warning only lifts an OK; a CRITICAL stays the CRITICAL it was."""
    _apply(tmp_path, _document(caaRecord="passed"), check.NagiosExitCode.CRITICAL)
    message, code, lines, _ = _apply(
        tmp_path, _document(caaRecord="inconclusive"), check.NagiosExitCode.CRITICAL
    )

    assert (message, code) == ("CRITICAL: original", check.NagiosExitCode.CRITICAL)
    assert any(line.startswith("Coverage regressed") for line in lines)


def test_warn_on_new_does_not_suppress_a_coverage_regression(tmp_path):
    """A known problem goes quiet, but a scan that suddenly sees less is news."""
    _apply(tmp_path, _document(caaRecord="passed"), check.NagiosExitCode.WARNING)
    _, code, _, comparison = _apply(
        tmp_path,
        _document(caaRecord="inconclusive"),
        check.NagiosExitCode.WARNING,
        warn_on_new=True,
    )

    assert comparison.regressed
    assert code is check.NagiosExitCode.WARNING


def test_a_baseline_without_coverage_cannot_report_a_loss(tmp_path):
    """A snapshot written before this field existed cannot say what was measurable."""
    path = tmp_path / "baseline.json"
    path.write_text(
        json.dumps(
            {"version": 1, "hosts": {HOST: {"rating": 5, "eol": False, "findings": []}}}
        ),
        encoding="utf-8",
    )
    stored = load_baseline(path)
    snapshot = stored.snapshot(HOST)

    assert snapshot is not None
    assert snapshot.measured is None
    comparison = stored.compare(HOST, snapshot_of(_document(caaRecord="inconclusive")))
    assert comparison.coverage_lost == {}


def test_the_comparison_of_two_documents_names_the_lost_check():
    """The CLI and web comparison must say it too, as a scanner change, not an instance one."""
    reasons = explain(
        _document(caaRecord="passed", dnssec="passed"),
        _document(caaRecord="inconclusive", dnssec="passed"),
    )
    regressed = [c for c in reasons.changes if c.code == "coverageRegressed"]

    assert len(regressed) == 1
    assert regressed[0].category == "scanner"
    assert regressed[0].evidence == {"checks": {"caaRecord": "timeout"}}
    assert not any(
        c.code == "coverageRegressed"
        for c in explain(_document(caaRecord="passed"), _document(caaRecord="passed")).changes
    )
