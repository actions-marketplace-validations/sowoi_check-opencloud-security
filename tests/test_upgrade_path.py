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
        code = excinfo.value.code
        assert isinstance(code, int), code
        return NagiosExitCode(code), capsys.readouterr().out

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


# --- edge cases ------------------------------------------------------------------
@pytest.mark.parametrize("version", [None, "", "garbage"])
def test_an_unknown_installed_version_has_no_path(version):
    """Without a version to compare, there is nothing to say and nothing to raise."""
    assert database(FIXED_IN_724).upgrade_path(version, "7.3.0") is None


@pytest.mark.parametrize("target", ["", "garbage", "7.1.0"])
def test_an_unusable_or_older_target_has_no_path(target):
    """A target that is empty, unreadable or a downgrade is not an upgrade path."""
    assert database(FIXED_IN_724).upgrade_path("7.2.1", target) is None


def test_an_empty_database_has_no_path():
    """No advisories, nothing to clear."""
    assert database().upgrade_path("7.2.1", "7.3.0") is None


def test_the_safe_version_is_the_highest_fix_across_the_leftovers():
    """Two advisories left open: the later fix is the first release that clears both."""
    later = Advisory(id="GHSA-eeee", introduced="7.0.0", fixed="7.3.5")
    path = database(FIXED_IN_730, later).upgrade_path("7.2.1", "7.2.9")

    assert path["stillAffected"] == ["GHSA-bbbb", "GHSA-eeee"]
    assert path["safeVersion"] == "7.3.5"


def test_the_ids_are_sorted_whatever_order_the_database_holds_them_in():
    """A stable order keeps the detail line from reshuffling between runs."""
    path = database(FIXED_IN_730, FIXED_IN_724).upgrade_path("7.2.1", "7.3.0")

    assert path["fixes"] == ["GHSA-aaaa", "GHSA-bbbb"]


@pytest.mark.parametrize(
    "document",
    [
        {"upgradePath": "7.3.0"},
        {"upgradePath": []},
        {"upgradePath": {}},
        {"upgradePath": {"target": ""}},
        {"upgradePath": {"target": None, "fixes": ["A"]}},
    ],
)
def test_a_malformed_path_adds_no_line(document):
    """A result document from another version must not crash the plugin."""
    assert plugin._upgrade_path_line(document) == ""


def test_a_path_with_missing_lists_still_reads_as_a_sentence():
    """Absent or null fixes and leftovers count as empty rather than raising."""
    assert plugin._upgrade_path_line({"upgradePath": {"target": "7.3.0"}}) == (
        "Upgrade path: 7.3.0 fixes all 0 known vulnerabilities."
    )
    assert plugin._upgrade_path_line(
        {"upgradePath": {"target": "7.3.0", "fixes": None, "stillAffected": ["B"]}}
    ) == "Upgrade path: 7.3.0 is still affected by B; no published release fixes all of them yet."


def _details(document, capsys):
    with pytest.raises(SystemExit) as excinfo:
        plugin.check_vulnerabilities(
            ScanContext(host="opencloud.example.com"),
            ScanResult(response=document, uuid="local-x"),
            duration_seconds=1.0,
        )
    code = excinfo.value.code
    assert isinstance(code, int), code
    return NagiosExitCode(code), capsys.readouterr().out


_BASE = {"version": "7.2.0", "rating": 5, "EOL": False, "vulnerabilities": [],
         "hardenings": {}, "setup": {"https": {"used": True, "enforced": True}}}


def test_http3_ports_are_listed_once_and_in_order(capsys):
    """h3 and a draft h3-29 on the same port name that port once."""
    document = dict(_BASE, alternativeServices={"http3": True, "entries": [
        {"protocol": "h3", "port": 8443, "udp": True},
        {"protocol": "h3-29", "port": 443, "udp": True},
        {"protocol": "h3", "port": 443, "udp": True},
        {"protocol": "h2", "port": 9443, "udp": False},
    ]})

    code, out = _details(document, capsys)

    assert code is NagiosExitCode.OK
    assert "Advertises HTTP/3 via Alt-Svc on UDP 443, 8443 -" in out


def test_http3_without_a_readable_port_names_no_port(capsys):
    """The line still warns; it just cannot say which UDP port."""
    document = dict(_BASE, alternativeServices={"http3": True, "entries": [
        {"protocol": "h3", "port": None, "udp": True}, "garbage", None,
    ]})

    _, out = _details(document, capsys)

    assert "Advertises HTTP/3 via Alt-Svc - make sure the firewall covers it" in out


@pytest.mark.parametrize(
    "services",
    [None, "h3", [], {"http3": False, "entries": [{"port": 443, "udp": True}]}, {"entries": None}],
)
def test_no_http3_or_a_malformed_record_adds_no_line(services, capsys):
    """Only an explicit http3 flag produces the line, and nothing here raises."""
    code, out = _details(dict(_BASE, alternativeServices=services), capsys)

    assert code is NagiosExitCode.OK
    assert "Alt-Svc" not in out


def test_the_upgrade_path_reaches_the_plugin_output(capsys):
    """With a known vulnerability, the operator reads which release fixes it."""
    document = dict(
        _BASE,
        vulnerabilities=[{"id": "GHSA-aaaa"}, {"id": "GHSA-bbbb"}],
        upgradePath={"target": "7.2.4", "fixes": ["GHSA-aaaa"],
                     "stillAffected": ["GHSA-bbbb"], "safeVersion": "7.3.0"},
    )

    _, out = _details(document, capsys)
    lines = out.split(" | ")[0].split("\n")

    assert (
        "Upgrade path: 7.2.4 fixes GHSA-aaaa but is still affected by GHSA-bbbb; "
        "7.3.0 is the first release that clears them all."
    ) in lines
    assert "None" not in lines

    _, clean = _details(dict(_BASE), capsys)
    assert "Upgrade path:" not in clean
