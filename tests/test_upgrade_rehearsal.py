"""
The upgrade rehearsal: what each candidate release would fix, leave and rate.

It replays the scanner's own version rules for a version that is not
installed yet, so the properties worth protecting are that it agrees with
those rules, that it never forgets the findings an upgrade does not touch,
and that it only rehearses releases an operator could actually move to.
"""

from __future__ import annotations

import copy
from datetime import date

import pytest

import check_opencloud_security as plugin
from check_opencloud_security import ScanContext, ScanResult
from opencloud_local_scan.rehearsal import candidates, rehearse
from opencloud_local_scan.versions import schedule_from_document
from opencloud_local_scan.vulndb import VulnerabilityDatabase, parse_document
from tests.fake_opencloud import InstanceBehaviour
from tests.test_local_scanner import run_scan

TODAY = date(2026, 9, 19)
SCHEDULE = schedule_from_document(
    {
        "lines": [
            {"line": "7.1", "tracks": ["rolling"], "released": "2026-06-02", "latest": "7.1.2"},
            {"line": "7.2", "tracks": ["production", "rolling"],
             "released": "2026-06-25", "latest": "7.2.4"},
            {"line": "7.3", "tracks": ["rolling"], "released": "2026-07-14", "latest": "7.3.0"},
        ],
    }
)
DATABASE = VulnerabilityDatabase(
    parse_document(
        {
            "advisories": [
                {"id": "A", "severity": "high", "introduced": "7.0.0", "fixed": "7.2.2"},
                {"id": "B", "severity": "medium", "introduced": "7.0.0", "fixed": "7.3.0"},
                {"id": "C", "severity": "low", "introduced": "7.3.0"},
            ]
        }
    ),
    ["test"],
)


def _rehearse(version: str = "7.1.1", **kwargs) -> dict[str, dict]:
    kwargs.setdefault("recommended", "7.3.0")
    entries = rehearse(
        version=version, database=DATABASE, schedule=SCHEDULE, today=TODAY, **kwargs
    )
    return {entry["version"]: entry for entry in entries}


def test_every_newer_line_is_a_candidate_and_nothing_older_is():
    """The installed line's newest patch and each later line, oldest first."""
    assert candidates(SCHEDULE, "7.1.1") == ["7.1.2", "7.2.4", "7.3.0"]
    assert candidates(SCHEDULE, "7.2.4") == ["7.3.0"]
    assert candidates(SCHEDULE, "7.3.0") == []
    assert candidates(SCHEDULE, None) == []


def test_candidates_sort_release_lines_numerically():
    """10.0 follows 9.0 even though lexical sorting would put it first."""
    schedule = schedule_from_document(
        {
            "lines": [
                {"line": "7.9", "tracks": ["rolling"], "released": "2026-01-01", "latest": "7.9.4"},
                {"line": "7.10", "tracks": ["rolling"], "released": "2026-02-01", "latest": "7.10.1"},
            ],
        }
    )
    assert candidates(schedule, "7.8.1") == ["7.9.4", "7.10.1"]


def test_a_declared_track_only_rehearses_releases_on_that_track():
    """A production instance is not rehearsed onto a rolling-only line."""
    assert candidates(SCHEDULE, "7.1.1", "production") == ["7.2.4"]


def test_rehearse_passes_the_declared_track_to_candidate_selection():
    """A rehearsal never offers a release from another track."""
    clean = VulnerabilityDatabase([], [])
    entries = rehearse(
        version="7.1.1", database=clean, schedule=SCHEDULE,
        recommended="7.2.4", track="production", today=TODAY,
    )
    assert [entry["version"] for entry in entries] == ["7.2.4"]


def test_rehearse_passes_the_declared_track_to_lifecycle_status():
    """A production line is not expired by a rolling successor."""
    schedule = schedule_from_document(
        {
            "lines": [
                {"line": "7.2", "tracks": ["production", "rolling"], "released": "2026-01-01", "latest": "7.2.4"},
                {"line": "7.3", "tracks": ["rolling"], "released": "2026-06-01", "latest": "7.3.0"},
            ],
        }
    )
    clean = VulnerabilityDatabase([], [])
    production = rehearse(
        version="7.1.1", database=clean, schedule=schedule,
        recommended="7.2.4", track="production", today=date(2027, 1, 1),
    )
    rolling = rehearse(
        version="7.1.1", database=clean, schedule=schedule,
        recommended="7.2.4", track="rolling", today=date(2027, 1, 1),
    )
    assert production[0]["endOfLife"] is False
    assert rolling[0]["endOfLife"] is True


def test_each_candidate_says_what_it_fixes_leaves_and_introduces():
    """Checked against every advisory, so a later fix on another line counts."""
    rehearsed = _rehearse()

    assert rehearsed["7.2.4"]["fixes"] == ["A"]
    assert rehearsed["7.2.4"]["line"] == "7.2"
    assert rehearsed["7.2.4"]["stillAffected"] == ["B"]
    assert rehearsed["7.2.4"]["introduces"] == []
    assert rehearsed["7.3.0"]["fixes"] == ["A", "B"]
    assert rehearsed["7.3.0"]["stillAffected"] == []
    assert rehearsed["7.3.0"]["introduces"] == ["C"]
    assert rehearsed["7.3.0"]["recommended"] is True
    assert rehearsed["7.2.4"]["recommended"] is False


def test_the_version_rating_follows_the_scanners_own_rules():
    """End of life 0, a high advisory 1, any advisory 2."""
    rehearsed = _rehearse()

    # 7.1 is superseded on its only track, so it is out of support.
    assert rehearsed["7.1.2"]["endOfLife"] is True
    assert rehearsed["7.1.2"]["rating"] == 0
    assert rehearsed["7.2.4"]["versionRating"] == 2
    assert rehearsed["7.3.0"]["versionRating"] == 2


def test_a_clean_candidate_behind_the_recommendation_is_rated_like_the_scan_would():
    """A line behind is 3, a patch behind is 4, the recommended release 5."""
    clean = VulnerabilityDatabase([], [])
    by_version = {
        entry["version"]: entry["versionRating"]
        for entry in rehearse(
            version="7.2.1", database=clean, schedule=SCHEDULE, today=TODAY,
            recommended="7.3.0",
        )
    }
    assert by_version == {"7.2.4": 3, "7.3.0": 5}

    patch = rehearse(
        version="7.2.1", database=clean, schedule=SCHEDULE, today=TODAY,
        recommended="7.2.5",
    )
    assert {entry["version"]: entry["versionRating"] for entry in patch}["7.2.4"] == 4


def test_the_findings_still_cap_the_rating_after_the_upgrade():
    """An upgrade changes the version, not the proxy: a critical finding stays."""
    clean = VulnerabilityDatabase([], [])
    capped = rehearse(
        version="7.2.1", database=clean, schedule=SCHEDULE, today=TODAY,
        recommended="7.3.0", findings_ceiling=2,
    )
    newest = capped[-1]
    assert newest["versionRating"] == 5
    assert newest["rating"] == 2


def test_the_schedule_can_be_left_out_of_the_verdict():
    """With use_release_schedule off, an old line is not called end of life."""
    rehearsed = _rehearse(use_release_schedule=False)
    assert rehearsed["7.1.2"]["endOfLife"] is False
    assert rehearsed["7.1.2"]["rating"] == 1


def test_rehearse_uses_the_supplied_date_for_clock_based_eol():
    """A date-sensitive LTS line is evaluated at the scan's date, not today."""
    schedule = schedule_from_document(
        {
            "lines": [
                {"line": "7.2", "tracks": ["lts"], "released": "2026-01-01", "latest": "7.2.4"},
            ],
        }
    )
    clean = VulnerabilityDatabase([], [])
    current = rehearse(
        version="7.1.1", database=clean, schedule=schedule,
        recommended="7.2.4", today=date(2026, 9, 19),
    )
    expired = rehearse(
        version="7.1.1", database=clean, schedule=schedule,
        recommended="7.2.4", today=date(2029, 1, 2),
    )
    assert current[0]["endOfLife"] is False
    assert expired[0]["endOfLife"] is True


def test_missing_advisory_severity_does_not_become_a_high_finding():
    """An advisory without severity must not be upgraded by a fallback string."""
    database = VulnerabilityDatabase(
        parse_document(
            {"advisories": [{"id": "unknown-severity", "introduced": "7.0.0", "fixed": "7.3.0"}]}
        ),
        ["test"],
    )
    entries = rehearse(
        version="7.1.1", database=database, schedule=SCHEDULE,
        recommended="7.3.0", today=TODAY,
    )
    by_version = {entry["version"]: entry for entry in entries}
    assert by_version["7.2.4"]["versionRating"] == 2
    assert by_version["7.3.0"]["versionRating"] == 5


# ------------------------------------------------------------- the plugin


RESULT = {
    "rating": 2,
    "version": "7.1.1",
    "vulnerabilities": [],
    "upgradeRehearsal": [
        {"version": "7.2.4", "line": "7.2", "recommended": False, "fixes": ["A", "B", "D"],
         "stillAffected": ["E"], "introduces": [], "endOfLife": False,
         "versionRating": 2, "rating": 2},
        {"version": "7.3.0", "line": "7.3", "recommended": True, "fixes": ["A"],
         "stillAffected": [], "introduces": ["C"], "endOfLife": False,
         "versionRating": 3, "rating": 3},
    ],
}


def _details(document: dict, capsys) -> list[str]:
    with pytest.raises(SystemExit):
        plugin.check_vulnerabilities(
            ScanContext(host="opencloud.example.com"),
            ScanResult(response=document, uuid="local-x"),
            duration_seconds=1.0,
        )
    text = capsys.readouterr().out.rpartition(" | ")[0]
    return text.split("\n")[1:]


def test_the_plugin_grades_each_rehearsed_release_with_its_own_rate_map(capsys):
    """The scanner's numbers become the plugin's letters, in one sentence."""
    details = _details(copy.deepcopy(RESULT), capsys)
    line = next(item for item in details if item.startswith("Upgrade rehearsal:"))

    assert "7.2.4 fixes 3 findings, leaves 1, reaches rating D" in line
    assert "7.3.0 fixes 1 finding, leaves 0, adds 1, reaches rating C" in line


def test_no_rehearsal_line_when_there_is_nothing_to_move_to(capsys):
    """An instance on the newest release gets no empty sentence."""
    document = copy.deepcopy(RESULT)
    document["upgradeRehearsal"] = []
    assert not any("rehearsal" in item for item in _details(document, capsys))


def test_the_payload_carries_the_rehearsal_in_snake_case_with_the_grade():
    """The plugin's own output is snake_case, and the letter is RATE_MAP's."""
    entries = plugin._upgrade_rehearsal_payload(copy.deepcopy(RESULT))

    assert entries[0]["still_affected"] == ["E"]
    assert entries[0]["rating_label"] == "D"
    assert entries[1]["rating_label"] == "C"
    assert "stillAffected" not in entries[0]
    assert plugin._upgrade_rehearsal_payload({}) == []


# -------------------------------------------------------------- a real scan


def test_a_real_scan_carries_a_rehearsal_that_agrees_with_its_own_rating():
    """The fake instance runs 7.2.3; its newest candidate is never rated above 5."""
    result = run_scan(InstanceBehaviour())
    rehearsal = result["upgradeRehearsal"]

    assert isinstance(rehearsal, list)
    assert all(entry["version"] != "7.2.3" for entry in rehearsal)
    for entry in rehearsal:
        assert 0 <= entry["rating"] <= entry["versionRating"] <= 5
