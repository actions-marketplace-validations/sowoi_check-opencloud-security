"""
check_vulnerabilities end to end, in-process: the wiring between its parts.

Each part - the rating, the baseline, perfdata, the webhook payload - has its
own tests. These run the whole function and check that it hands each part
the right values and prints what an operator reads, which is what a
mutation run found untested (/mutation-test).
"""

from __future__ import annotations

import copy

import pytest

import check_opencloud_security as plugin
from check_opencloud_security import NagiosExitCode, ScanContext, ScanResult
from opencloud_local_scan.baseline import Snapshot, load_baseline

HOST = "cloud.example.com"

RESULT = {
    "domain": HOST,
    "product": "OpenCloud",
    "version": "7.2.0",
    "scannedAt": {"date": "2026-05-01 10:00:00.000000"},
    "rating": 5,
    "EOL": False,
    "vulnerabilities": [],
    "hardenings": {"basicAuthDisabled": True, "cspWithoutUnsafeInline": True},
    "setup": {"https": {"used": True, "enforced": True}, "headers": {}},
    "updates": {"available": False, "version": "7.2.0", "source": "pinned"},
}


def result(**changes):
    document = copy.deepcopy(RESULT)
    document.update(changes)
    return document


def run(document, capsys, **kwargs):
    """Run the check; return exit code, alert line, detail lines and perfdata."""
    context = ScanContext(host=HOST, **kwargs)
    with pytest.raises(SystemExit) as excinfo:
        plugin.check_vulnerabilities(
            context, ScanResult(response=document, uuid="local-x"), duration_seconds=1.25
        )
    text, _, perfdata = capsys.readouterr().out.rstrip("\n").rpartition(" | ")
    first, *details = text.split("\n")
    code = excinfo.value.code
    assert isinstance(code, int), code
    return NagiosExitCode(code), first, details, perfdata


def metrics(perfdata):
    return dict(part.split("=", 1) for part in perfdata.split())


# --- the alert line ---
def test_vulnerabilities_with_a_good_rating_warn_and_are_listed(capsys):
    """A known CVE on an A+ instance is a WARNING naming the CVEs, never OK."""
    vulns = [{"id": "CVE-2026-0001"}, {"id": "CVE-2026-0002"}]
    code, first, details, perfdata = run(result(vulnerabilities=vulns), capsys)

    assert code is NagiosExitCode.WARNING
    assert first == "WARNING: Found 2 vulnerabilities (rating A+)."
    assert "Known vulnerabilities: CVE-2026-0001, CVE-2026-0002" in details
    assert metrics(perfdata)["vulnerabilities"] == "2;;;0;"


def test_missing_hardening_warns_with_the_exact_alert_line(capsys):
    """The first line is what a monitoring system shows; it must say what is wrong."""
    document = result(hardenings={"basicAuthDisabled": False, "cspWithoutUnsafeInline": True})
    code, first, details, _ = run(document, capsys, check_hardening=True)

    assert code is NagiosExitCode.WARNING
    assert first == "WARNING: 1 hardening measure(s) missing, but no known vulnerabilities."
    assert (
        "Missing hardening: basicAuthDisabled "
        "(run with --debug for what each means and how to fix it)"
    ) in details


def test_complete_hardening_says_so(capsys):
    """Silence would be indistinguishable from a check that never ran."""
    _, first, details, _ = run(result(), capsys, check_hardening=True)

    assert first == "OK: Server is up to date. No known vulnerabilities."
    assert "Hardening: all checked measures in place" in details


def test_waived_measures_are_listed_and_do_not_warn(capsys):
    """An accepted measure stays visible but stops alerting."""
    document = result(
        hardenings={"basicAuthDisabled": False, "cspWithoutUnsafeInline": False},
        ignored=["basicAuthDisabled", "cspWithoutUnsafeInline"],
    )
    code, _, details, _ = run(document, capsys, check_hardening=True)

    assert code is NagiosExitCode.OK
    assert "Ignored by configuration (2): basicAuthDisabled, cspWithoutUnsafeInline" in details


def test_update_warning_names_the_version(capsys):
    """--update-warning must say which release to install."""
    updates = {"available": True, "version": "7.2.0", "availableVersion": "7.3.0", "source": "pinned"}
    code, first, _, perfdata = run(result(updates=updates), capsys, update_warning=True)

    assert code is NagiosExitCode.WARNING
    assert first == "WARNING: Update available (7.3.0), but no known vulnerabilities."
    assert metrics(perfdata)["update_available"] == "1;;;0;1"


def test_update_warning_without_a_version_says_unknown(capsys):
    """An unnamed update still warns, without printing None."""
    updates = {"available": True, "version": "7.2.0", "source": "pinned"}
    _, first, _, _ = run(result(updates=updates), capsys, update_warning=True)

    assert first == "WARNING: Update available (unknown version), but no known vulnerabilities."


def test_the_header_line_names_product_version_domain_rating_and_date(capsys):
    """The first detail line is how an operator tells runs and hosts apart."""
    _, _, details, _ = run(result(), capsys)

    assert details[0] == (
        f"OpenCloud 7.2.0 on {HOST}, rating: A+, last scanned: 2026-05-01 10:00:00.000000"
    )


# --- extra checks ---
def _extra(count):
    return [{"id": f"check{i}", "passed": False, "severity": "low"} for i in range(count)]


def test_five_failed_extra_checks_are_all_listed(capsys):
    """Up to five failures fit on the line in full."""
    _, _, details, perfdata = run(result(extraChecks=_extra(5)), capsys)

    assert "Additional checks failed (5): check0, check1, check2, check3, check4" in details
    assert metrics(perfdata)["extra_checks_failed"] == "5;;;0;"


def test_more_than_five_failed_extra_checks_are_truncated(capsys):
    """A long list is cut, and says how much was cut."""
    _, _, details, _ = run(result(extraChecks=_extra(7)), capsys)

    assert "Additional checks failed (7): check0, check1, check2, check3, check4 (+2 more)" in details


def test_passing_extra_checks_say_so(capsys):
    """All passed is reported, not left blank."""
    _, _, details, _ = run(result(extraChecks=[{"id": "a", "passed": True}]), capsys)

    assert "Additional checks: all passed" in details


# --- perfdata ---
def test_perfdata_carries_every_measured_value(capsys):
    """Everything the check measured must be graphable."""
    document = result(
        hardenings={"basicAuthDisabled": False, "cspWithoutUnsafeInline": True},
        extraChecks=_extra(2),
    )
    _, _, _, perfdata = run(document, capsys, check_hardening=True, warning_rating=4)
    values = metrics(perfdata)

    assert values["rating"] == "5;@0:4;@0:1;0;5"
    assert values["vulnerabilities"] == "0;;;0;"
    assert values["time"] == "1.250s;;;0;"
    assert values["hardenings_missing"] == "1;;;0;"
    assert values["extra_checks_failed"] == "2;;;0;"


def test_perfdata_leaves_out_what_was_not_measured(capsys):
    """Hardening off and no extra checks: those metrics are absent, not zero."""
    document = result(hardenings={"basicAuthDisabled": False})
    del document["updates"]
    _, _, _, perfdata = run(document, capsys)
    values = metrics(perfdata)

    assert "hardenings_missing" not in values
    assert "extra_checks_failed" not in values
    assert "update_available" not in values


# --- the self-update note ---
def test_the_self_update_note_is_printed(capsys, monkeypatch):
    """A newer plugin is mentioned without changing the state."""
    monkeypatch.setattr(plugin, "self_update_note", lambda version: "Plugin update: 9.9.9")
    code, _, details, _ = run(result(), capsys, self_update_check=True)

    assert "Plugin update: 9.9.9" in details
    assert code is NagiosExitCode.OK


def test_no_self_update_note_when_there_is_none(capsys, monkeypatch):
    """No release, no note."""
    monkeypatch.setattr(plugin, "self_update_note", lambda version: None)
    _, _, details, _ = run(result(), capsys, self_update_check=True)

    assert not any(line.startswith("Plugin update") for line in details)


# --- the baseline ---
def _recorded(path) -> Snapshot:
    store = load_baseline(str(path))
    comparison = store.compare(HOST, Snapshot(rating=5, eol=False))
    assert comparison.previous is not None
    return comparison.previous


def test_the_baseline_records_what_the_alert_line_reports(capsys, tmp_path):
    """Missing and waived hardening, vulnerabilities: the baseline sees the same list."""
    path = tmp_path / "baseline.json"
    document = result(
        rating=3,
        vulnerabilities=[{"id": "CVE-2026-0001"}],
        hardenings={"basicAuthDisabled": False, "cspWithoutUnsafeInline": False},
        ignored=["cspWithoutUnsafeInline"],
    )
    _, _, details, _ = run(document, capsys, check_hardening=True, baseline_path=str(path))
    snapshot = _recorded(path)

    assert snapshot.rating == 3
    assert "hardening:basicAuthDisabled" in snapshot.findings
    assert "hardening:cspWithoutUnsafeInline" not in snapshot.findings
    assert any("CVE-2026-0001" in finding for finding in snapshot.findings)
    assert any(line.startswith("Baseline: ") for line in details)


def test_without_hardening_checks_the_baseline_records_no_hardening(capsys, tmp_path):
    """A measure the operator did not ask about must not become a 'new' finding later."""
    path = tmp_path / "baseline.json"
    document = result(hardenings={"basicAuthDisabled": False})
    run(document, capsys, baseline_path=str(path))

    assert not any(f.startswith("hardening:") for f in _recorded(path).findings)


def test_warn_on_new_suppresses_through_the_whole_check(capsys, tmp_path):
    """The second identical run stops paging, end to end."""
    path = str(tmp_path / "baseline.json")
    document = result(vulnerabilities=[{"id": "CVE-2026-0001"}])
    run(document, capsys, baseline_path=path, warn_on_new=True)
    code, first, _, _ = run(document, capsys, baseline_path=path, warn_on_new=True)

    assert code is NagiosExitCode.OK
    assert first == "OK: nothing new since the last run (WARNING state unchanged)."


# --- the payload behind --format and the webhook ---
def test_the_result_payload_matches_the_printed_result(capsys, tmp_path):
    """--format json and the webhook must say what the text output says."""
    document = result(vulnerabilities=[{"id": "CVE-2026-0001"}])
    code, first, _, _ = run(document, capsys, check_hardening=True, baseline_path=str(tmp_path / "b.json"))
    stored = plugin._RESULT_PAYLOAD.get()

    assert stored is not None
    assert stored["scan"] is document
    assert stored["hardening_checked"] is True
    assert stored["webhook_fires"] is False
    payload = stored["payload"]
    assert payload["message"] == first
    assert payload["vulnerability_count"] == 1
    assert payload["baseline_diff"]["summary"].startswith("Baseline: ")
    assert code is NagiosExitCode.WARNING


def test_a_failed_webhook_delivery_is_reported(capsys, monkeypatch):
    """A lost notification must at least show up in the check output."""
    monkeypatch.setattr(plugin, "_send_or_defer_webhook", lambda context, payload, code: (False, True))
    _, _, details, _ = run(result(rating=0), capsys)

    assert "Webhook delivery failed (see debug log)" in details


# --- a sparse result document, as a caller outside the scanner may hand in ---
def test_a_result_without_details_is_unknown_and_says_so(capsys):
    """Missing fields read 'Unknown' in the header, and no rating is never OK."""
    code, first, details, perfdata = run({}, capsys)

    assert code is NagiosExitCode.UNKNOWN
    assert first == "UNKNOWN: Scan result unclear. Please verify manually."
    assert details[0] == "Unknown Unknown on Unknown, rating: Unknown, last scanned: Unknown"
    assert metrics(perfdata)["rating"].startswith("U;")
    assert metrics(perfdata)["vulnerabilities"] == "0;;;0;"


def test_several_missing_measures_are_listed_comma_separated(capsys):
    """Each missing measure is named, readably separated."""
    document = result(hardenings={"basicAuthDisabled": False, "cspWithoutUnsafeInline": False})
    _, first, details, _ = run(document, capsys, check_hardening=True)

    assert first == "WARNING: 2 hardening measure(s) missing, but no known vulnerabilities."
    assert any(
        line.startswith("Missing hardening: basicAuthDisabled, cspWithoutUnsafeInline ")
        for line in details
    )


def test_six_failed_extra_checks_show_one_more(capsys):
    """The cut starts at the sixth failure, not later."""
    _, _, details, _ = run(result(extraChecks=_extra(6)), capsys)

    assert "Additional checks failed (6): check0, check1, check2, check3, check4 (+1 more)" in details


# --- login throttling and the upgrade path metric ---
def test_throttled_sign_ins_are_reported_with_their_evidence(capsys):
    """A 429 on the failed sign-ins is named, and marked as not rated."""
    throttling = {"tested": True, "throttled": True, "evidence": "HTTP 429", "attempts": 3}
    code, _, details, _ = run(result(loginThrottling=throttling), capsys)

    assert code is NagiosExitCode.OK
    assert "Failed sign-ins throttled (HTTP 429) (not rated)." in details
    assert not any("were not throttled" in line for line in details)


def test_unthrottled_sign_ins_say_how_many_and_what_to_do(capsys):
    """An open login path is reported with the attempt count and the proxy advice."""
    throttling = {"tested": True, "throttled": False, "evidence": "", "attempts": 10}
    code, _, details, _ = run(result(loginThrottling=throttling), capsys)

    assert code is NagiosExitCode.OK
    assert (
        "10 failed sign-ins in a row were not throttled - consider rate limiting "
        "at the proxy (not rated)."
    ) in details
    assert not any("Failed sign-ins throttled" in line for line in details)


@pytest.mark.parametrize("throttling", [{"tested": False}, None, "yes"])
def test_an_untested_or_absent_throttling_record_adds_no_line(throttling, capsys):
    """Nothing was measured, so nothing is said - and no 'None' line appears."""
    _, _, details, _ = run(result(loginThrottling=throttling), capsys)

    assert not any("sign-ins" in line for line in details)
    assert "None" not in details


@pytest.mark.parametrize(
    ("still_affected", "expected"), [([], "1"), (["GHSA-bbbb"], "0")]
)
def test_the_upgrade_path_metric_reaches_the_perfdata(still_affected, expected, capsys):
    """upgrade_path_complete is 1 when the target clears everything, 0 when it does not."""
    path = {"target": "7.3.0", "fixes": ["GHSA-aaaa"], "stillAffected": still_affected,
            "safeVersion": "7.3.0"}
    _, _, _, perfdata = run(result(upgradePath=path), capsys)

    assert metrics(perfdata)["upgrade_path_complete"] == f"{expected};;;0;1"


def test_there_is_no_upgrade_path_metric_without_a_path(capsys):
    """Without advisories there is nothing to complete, so no metric at all."""
    _, _, _, perfdata = run(result(), capsys)

    assert "upgrade_path_complete" not in metrics(perfdata)


# --- the coverage line ---
COVERAGE = {
    "schema": 1,
    "counts": {"passed": 2, "failed": 0, "not_checked": 2, "inconclusive": 1, "total": 5},
    "checks": [
        {"id": "basicAuthDisabled", "group": "hardening", "state": "passed"},
        {"id": "cspWithoutUnsafeInline", "group": "hardening", "state": "passed"},
        {"id": "tlsVersion", "group": "tls", "state": "not_checked", "reason": "probe_disabled"},
        {"id": "dnssec", "group": "dns", "state": "not_checked", "reason": "timeout"},
        {"id": "identityProvider", "group": "integrations", "state": "inconclusive",
         "reason": "prerequisite_missing"},
    ],
}


def test_the_coverage_line_tells_a_gap_apart_from_a_pass(capsys):
    """An operator has to see what could not be measured, not infer it."""
    _, _, details, _ = run(result(coverage=COVERAGE), capsys)

    assert (
        "Coverage: 2 checks evaluated, 1 skipped, 1 indeterminate, 1 network-limited"
        in details
    )


def test_a_scan_without_coverage_prints_no_coverage_line(capsys):
    """Saying nothing is right when the document does not say."""
    _, _, details, _ = run(result(), capsys)

    assert [line for line in details if line.startswith("Coverage:")] == []


def test_the_payload_carries_the_coverage_counts(capsys):
    """A receiver reads the same numbers the operator does, snake_case."""
    run(result(coverage=COVERAGE), capsys)
    recorded = plugin._RESULT_PAYLOAD.get()
    assert recorded is not None
    payload = recorded["payload"]

    assert payload["coverage"] == {
        "evaluated": 2,
        "skipped": 1,
        "indeterminate": 1,
        "network_limited": 1,
        "total": 5,
        "summary": "2 checks evaluated, 1 skipped, 1 indeterminate, 1 network-limited",
    }


def test_the_payload_says_nothing_rather_than_none_missed(capsys):
    run(result(), capsys)

    recorded = plugin._RESULT_PAYLOAD.get()
    assert recorded is not None
    assert recorded["payload"]["coverage"] is None


# --- the configuration fingerprint ---
def _fingerprinted(**groups):
    """A result document carrying a fingerprint with the given group digests."""
    return result(
        configuration={
            "schema": 1,
            "digest": "deadbeef" + "0" * 56,
            "groups": {
                group: {"digest": digest, "scope": "scope" + group, "facts": 3}
                for group, digest in groups.items()
            },
        }
    )


FULL = {
    "tls": "a" * 64,
    "headers": "b" * 64,
    "sharing": "c" * 64,
    "authentication": "d" * 64,
    "proxy": "e" * 64,
}


def test_the_fingerprint_line_is_short_enough_to_read(capsys):
    """An operator compares two runs by eye; 64 characters defeats that."""
    _, _, details, _ = run(_fingerprinted(**FULL), capsys)

    assert "Configuration fingerprint: deadbeef" in details


def test_the_fingerprint_line_names_what_it_could_not_measure(capsys):
    """Four groups out of five is not a fingerprint of the deployment."""
    partial = dict(FULL)
    partial["tls"] = "none"
    _, _, details, _ = run(_fingerprinted(**partial), capsys)

    assert "Configuration fingerprint: deadbeef (tls not measured)" in details


def test_a_scan_without_a_fingerprint_prints_no_line(capsys):
    """A report that cannot say must not look like one with nothing to say."""
    _, _, details, _ = run(result(), capsys)

    assert [line for line in details if line.startswith("Configuration")] == []


def test_the_payload_carries_the_digests_and_nothing_else(capsys):
    """A receiver compares digests; it is never handed the configuration."""
    run(_fingerprinted(**FULL), capsys)
    recorded = plugin._RESULT_PAYLOAD.get()
    assert recorded is not None
    configuration = recorded["payload"]["configuration"]

    assert configuration["digest"].startswith("deadbeef")
    assert set(configuration["groups"]) == set(FULL)
    assert configuration["groups"]["tls"] == "scopetls:" + "a" * 64


def test_the_payload_says_nothing_when_the_scan_recorded_no_fingerprint(capsys):
    run(result(), capsys)
    recorded = plugin._RESULT_PAYLOAD.get()
    assert recorded is not None

    assert recorded["payload"]["configuration"] is None
