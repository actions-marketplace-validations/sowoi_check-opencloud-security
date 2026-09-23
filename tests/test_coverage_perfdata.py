"""
coverage_inconclusive and coverage_not_checked: the coverage block, graphable.

The long output and the webhook always said how many checks the scan could
not decide or did not run. The graph did not, so "three checks became
unreadable this morning" was invisible there. These are the two gaps as
numbers - and nothing else: they carry no thresholds and never move the
grade or the state.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

import check_opencloud_security as plugin
from check_opencloud_security import NagiosExitCode, ScanContext, ScanResult
from opencloud_local_scan.coverage import state_counts
from opencloud_local_scan.metrics import collect

HOST = "opencloud.example.com"

RESULT: dict[str, Any] = {
    "domain": HOST,
    "product": "OpenCloud",
    "version": "7.2.0",
    "scannedAt": {"date": "2026-05-01 10:00:00.000000"},
    "rating": 5,
    "EOL": False,
    "vulnerabilities": [],
    "hardenings": {},
    "setup": {"https": {"used": True, "enforced": True}, "headers": {}},
    "coverage": {
        "schema": 1,
        "counts": {"passed": 0, "failed": 0, "not_checked": 0, "inconclusive": 0, "total": 0},
        "checks": [
            {"id": "a", "group": "tls", "state": "passed"},
            {"id": "b", "group": "tls", "state": "failed"},
            {"id": "c", "group": "dns", "state": "not_checked", "reason": "probe_disabled"},
            {"id": "d", "group": "dns", "state": "inconclusive", "reason": "unreadable"},
            {"id": "e", "group": "dns", "state": "inconclusive", "reason": "timeout"},
            {"id": "f", "group": "dns", "state": "inconclusive", "reason": "no_route"},
        ],
    },
}


def run(document, capsys):
    with pytest.raises(SystemExit) as excinfo:
        plugin.check_vulnerabilities(
            ScanContext(host=HOST, update_check=False),
            ScanResult(response=document, uuid="local-x"),
            duration_seconds=1.0,
        )
    output = capsys.readouterr().out
    code = excinfo.value.code
    assert isinstance(code, int), code
    return NagiosExitCode(code), output


def perfdata(output: str) -> dict[str, str]:
    return dict(item.split("=", 1) for item in output.split("|", 1)[1].split())


def test_the_counts_come_from_the_checks_not_the_counts_block():
    """A stale counts block cannot disagree with the entries it claims to count."""
    assert state_counts(RESULT) == {
        "passed": 1, "failed": 1, "not_checked": 1, "inconclusive": 3,
    }


def test_a_result_without_coverage_has_no_counts():
    """A report that does not say is not a report with no gaps."""
    document = copy.deepcopy(RESULT)
    del document["coverage"]

    assert state_counts(document) is None


def test_the_gaps_are_perfdata_without_thresholds(capsys):
    """Both gaps reach the graph, each by state whatever its reason."""
    _, output = run(copy.deepcopy(RESULT), capsys)
    values = perfdata(output)

    assert values["coverage_inconclusive"] == "3;;;0;"
    assert values["coverage_not_checked"] == "1;;;0;"


def test_the_gaps_leave_the_state_alone(capsys):
    """Coverage explains a grade; it never changes one."""
    complete = copy.deepcopy(RESULT)
    complete["coverage"]["checks"] = complete["coverage"]["checks"][:2]

    gappy_code, gappy = run(copy.deepcopy(RESULT), capsys)
    complete_code, whole = run(complete, capsys)

    assert gappy_code is complete_code is NagiosExitCode.OK
    assert gappy.split("\n", 1)[0] == whole.split("\n", 1)[0]
    assert perfdata(whole)["coverage_inconclusive"] == "0;;;0;"


def test_a_result_without_coverage_has_no_coverage_perfdata(capsys):
    """An absent block is absent from the graph, not a confident zero."""
    document = copy.deepcopy(RESULT)
    del document["coverage"]

    _, output = run(document, capsys)

    assert "coverage_inconclusive" not in perfdata(output)
    assert "coverage_not_checked" not in perfdata(output)


def test_the_gaps_reach_checkmk_and_prometheus():
    """Every monitoring tool learns the same two numbers."""
    metrics = plugin._checkmk_metrics(
        {"payload": {}, "scan": RESULT, "hardening_checked": False}
    ).split("|")
    families = {
        family.name: family.samples[0].value
        for family in collect(HOST, RESULT, duration_seconds=1.0, success=True)
    }

    assert "coverage_inconclusive=3" in metrics
    assert "coverage_not_checked=1" in metrics
    assert families["opencloud_security_coverage_inconclusive_total"] == 3
    assert families["opencloud_security_coverage_not_checked_total"] == 1
