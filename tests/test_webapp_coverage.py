"""
The gaps in a scan, rendered beside the grade.

The web layer does not decide what was covered - the scanner recorded that
while it ran. What happens here is regrouping and translation, and two things
have to survive it: a report from before coverage existed must not be shown
as a scan with no gaps, and every reason must read as a sentence in all four
languages rather than as the token the scanner wrote.
"""

from __future__ import annotations

import pytest

from opencloud_local_scan.coverage import (
    NOT_APPLICABLE,
    PROBE_DISABLED,
    CoverageRecorder,
)
from webapp.catalog import summarise
from webapp.i18n import SUPPORTED_LOCALES, Translator

pytest.importorskip("fastapi", reason="the web extra is not installed")


def _document(**extra: object) -> dict:
    """A minimal result document, as the scanner writes one."""
    document: dict = {"rating": 4, "extraChecks": [], "hardenings": {}, "setup": {}}
    document.update(extra)
    return document


def _recorded() -> dict:
    recorder = CoverageRecorder()
    recorder.measured("Content-Security-Policy", "header", True)
    recorder.measured("directoryListing", "extraCheck", False)
    recorder.skipped(
        "tlsInspection", "tls", NOT_APPLICABLE, "The instance answered over plain HTTP."
    )
    recorder.skipped(
        "caaRecord", "dns", PROBE_DISABLED, "The extra checks are turned off."
    )
    return recorder.as_dict()


def test_a_report_from_before_coverage_is_not_a_report_without_gaps():
    """
    The distinction the whole block exists for, one layer up.

    An older stored result and an uploaded legacy report both arrive here
    with no coverage at all, and rendering that as "nothing was missed" is
    the exact misreading this is supposed to prevent.
    """
    coverage = summarise(_document())["coverage"]

    assert coverage["available"] is False
    assert coverage["gaps"] == []
    assert coverage["counts"] == {}


def test_the_counts_and_the_detail_are_the_same_list():
    """A reader who counts the entries must get the number in the summary."""
    coverage = summarise(_document(coverage=_recorded()))["coverage"]

    assert coverage["available"] is True
    assert coverage["counts"]["total"] == 4
    assert coverage["measured"] == 2
    assert len(coverage["gaps"]) == 2
    assert sum(len(group["checks"]) for group in coverage["groups"]) == len(
        coverage["gaps"]
    )


def test_only_the_unfinished_checks_are_listed_as_gaps():
    """A passed check is not a gap, and neither is a failed one."""
    coverage = summarise(_document(coverage=_recorded()))["coverage"]

    assert {entry["id"] for entry in coverage["gaps"]} == {"tlsInspection", "caaRecord"}
    assert all(entry["reason"] for entry in coverage["gaps"])
    assert all(entry["detail"] for entry in coverage["gaps"])


def test_a_gap_keeps_the_reason_the_scanner_recorded():
    """The web layer translates the reason; it never decides a different one."""
    coverage = summarise(_document(coverage=_recorded()))["coverage"]
    by_id = {entry["id"]: entry for entry in coverage["gaps"]}

    assert by_id["tlsInspection"]["reason"] == NOT_APPLICABLE
    assert by_id["caaRecord"]["reason"] == PROBE_DISABLED


@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
def test_every_reason_and_group_reads_as_a_sentence_in_every_language(locale: str):
    """
    A missing string falls back to the key, which would print
    `coverage.reason.no_route` at somebody scanning their own instance.
    """
    coverage = summarise(_document(coverage=_recorded()), Translator(locale))["coverage"]

    for entry in coverage["gaps"]:
        assert entry["reasonLabel"] != f"coverage.reason.{entry['reason']}"
        assert entry["groupLabel"] != f"coverage.group.{entry['group']}"
        assert not entry["reasonLabel"].startswith("coverage.")
        assert not entry["groupLabel"].startswith("coverage.")


def test_a_machine_reading_the_summary_gets_english():
    """Every export and the JSON API leave the translator unset (ADR 0011)."""
    english = summarise(_document(coverage=_recorded()))["coverage"]
    german = summarise(_document(coverage=_recorded()), Translator("de"))["coverage"]

    assert english["gaps"][0]["reasonLabel"] != german["gaps"][0]["reasonLabel"]
    assert english["gaps"][0]["reason"] == german["gaps"][0]["reason"]


def test_coverage_changes_no_grade():
    """The block explains a grade; the summary's verdict must not move."""
    without = summarise(_document())
    with_coverage = summarise(_document(coverage=_recorded()))

    assert without["rating"] == with_coverage["rating"]
    assert without["label"] == with_coverage["label"]
    assert without["tone"] == with_coverage["tone"]
    assert without["counts"] == with_coverage["counts"]


def test_the_result_page_shows_the_gaps_it_recorded():
    """
    A real scan of a fake instance, rendered, with the section in it.

    The fake answers over plain HTTP and publishes no identity provider, so
    there are always gaps to show - which is the point: a page that only
    renders correctly when nothing was missed is a page nobody has seen.
    """
    from tests.test_webapp_pages import _finished_page

    page = _finished_page("7.2.3")

    assert 'id="coverage"' in page
    assert Translator()("result.coverage.heading") in page
    assert Translator()("coverage.reason.not_applicable") in page
    # The block explains; it never turns into a claim about the grade.
    assert Translator()("result.coverage.unavailable") not in page
