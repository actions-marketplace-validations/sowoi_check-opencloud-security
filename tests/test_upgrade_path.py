"""The upgrade path and the Alt-Svc detail line: what the plugin adds to a scan."""

from __future__ import annotations

import pytest

import check_opencloud_security as plugin
from check_opencloud_security import NagiosExitCode, ScanContext, ScanResult
from opencloud_local_scan.vulndb import Advisory, VulnerabilityDatabase


def database(*advisories):
    return VulnerabilityDatabase(advisories=list(advisories), sources=[])


FIXED_IN_724 = Advisory(id="GHSA-aaaa", introduced="7.0.0", fixed="7.2.4")
FIXED_IN_730 = Advisory(id="GHSA-bbbb", introduced="7.0.0", fixed="7.3.0")
UNFIXED = Advisory(id="GHSA-cccc", introduced="7.0.0", fixed=None)
BACKPORTED = Advisory(
    id="GHSA-dddd", ranges=(("7.0.0", "7.2.3"), ("7.3.0", "7.3.2"))
)


def test_a_target_past_every_fix_clears_all_advisories():
    """Moving to 7.3.0 leaves nothing of what 7.2.1 carries."""
    path = database(FIXED_IN_724, FIXED_IN_730).upgrade_path("7.2.1", "7.3.0")

    assert path == {
        "target": "7.3.0",
        "fixes": ["GHSA-aaaa", "GHSA-bbbb"],
        "stillAffected": [],
        "safeVersion": "7.3.0",
    }


def test_a_target_short_of_a_fix_names_the_release_that_clears_it():
    """7.2.4 fixes one advisory; the other needs 7.3.0."""
    path = database(FIXED_IN_724, FIXED_IN_730).upgrade_path("7.2.1", "7.2.4")

    assert path["fixes"] == ["GHSA-aaaa"]
    assert path["stillAffected"] == ["GHSA-bbbb"]
    assert path["safeVersion"] == "7.3.0"


def test_an_advisory_without_a_fix_has_no_safe_version():
    """No release can be named when one advisory is unfixed everywhere."""
    path = database(FIXED_IN_724, UNFIXED).upgrade_path("7.2.1", "7.3.0")

    assert path["stillAffected"] == ["GHSA-cccc"]
    assert path["safeVersion"] is None


def test_every_range_of_an_advisory_is_checked_against_the_target():
    """A target inside a later range is still affected, and its own fix counts."""
    path = database(BACKPORTED).upgrade_path("7.2.1", "7.3.1")

    assert path["stillAffected"] == ["GHSA-dddd"]
    assert path["safeVersion"] == "7.3.2"


def test_there_is_no_path_without_an_advisory_or_a_newer_target():
    """Nothing to clear, no target, or a target that is not newer: no path."""
    assert database(FIXED_IN_724).upgrade_path("7.2.5", "7.3.0") is None
    assert database(FIXED_IN_724).upgrade_path("7.2.1", None) is None
    assert database(FIXED_IN_724).upgrade_path("7.2.1", "7.2.1") is None
    assert database(FIXED_IN_724).upgrade_path("7.2.1", "7.3.0") is not None


def test_the_plugin_says_the_target_fixes_everything():
    """A complete path is one reassuring line."""
    line = plugin._upgrade_path_line(
        {"upgradePath": {"target": "7.3.0", "fixes": ["A", "B"], "stillAffected": [],
                         "safeVersion": "7.3.0"}}
    )

    assert line == "Upgrade path: 7.3.0 fixes all 2 known vulnerabilities."


def test_the_plugin_names_what_the_target_leaves_open():
    """A partial path names the leftovers and the release that clears them."""
    line = plugin._upgrade_path_line(
        {"upgradePath": {"target": "7.2.4", "fixes": ["A"], "stillAffected": ["B"],
                         "safeVersion": "7.3.0"}}
    )

    assert line == (
        "Upgrade path: 7.2.4 fixes A but is still affected by B; "
        "7.3.0 is the first release that clears them all."
    )


def test_the_plugin_says_when_no_release_fixes_everything():
    """Without a safe version the line says so instead of naming one."""
    line = plugin._upgrade_path_line(
        {"upgradePath": {"target": "7.3.0", "fixes": [], "stillAffected": ["C"],
                         "safeVersion": None}}
    )

    assert line == (
        "Upgrade path: 7.3.0 is still affected by C; "
        "no published release fixes all of them yet."
    )


def test_the_plugin_prints_nothing_without_a_path():
    """An older result, or one with nothing to clear, adds no line."""
    assert plugin._upgrade_path_line({}) == ""
    assert plugin._upgrade_path_line({"upgradePath": None}) == ""


def test_the_plugin_mentions_an_advertised_http3_listener(capsys):
    """An h3 Alt-Svc entry becomes a detail line; without one there is none."""
    def details(document):
        with pytest.raises(SystemExit) as excinfo:
            plugin.check_vulnerabilities(
                ScanContext(host="opencloud.example.com"),
                ScanResult(response=document, uuid="local-x"),
                duration_seconds=1.0,
            )
        return NagiosExitCode(excinfo.value.code), capsys.readouterr().out

    base = {"version": "7.2.0", "rating": 5, "EOL": False, "vulnerabilities": [],
            "hardenings": {}, "setup": {"https": {"used": True, "enforced": True}}}
    quic = dict(base, alternativeServices={
        "advertised": True, "http3": True,
        "entries": [{"protocol": "h3", "host": "", "port": 443, "udp": True}],
    })

    code, out = details(quic)
    assert code is NagiosExitCode.OK
    assert "Advertises HTTP/3 via Alt-Svc on UDP 443" in out
    assert "Alt-Svc" not in details(base)[1]
