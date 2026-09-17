"""
The scan as one file that still reads after the link has expired.

A result link is a capability with a time limit (ADR 0007), which is right
for a page a stranger can reach and wrong for the evidence somebody needs at
the end of the quarter. The downloaded report is the same report without the
service under it.

Two things have to be true of it and are easy to lose. It must make no
network request when it is opened - a stylesheet link or a font service would
turn "open my saved report" into "tell somebody I opened my saved report",
offline or not. And every string in it comes either from the scanned instance
or from an operator's waiver, so none of it may be markup.
"""

from __future__ import annotations

import re

import pytest

from tests.test_webapp_exports import (  # noqa: F401 - finished_scan is a fixture
    IDENTIFIER,
    client,
    finished_scan,
)
from webapp.reports import EXPORT_FORMATS, FILE_SUFFIXES, MEDIA_TYPES, html_report

pytest.importorskip("fastapi", reason="the web extra is not installed")

HOSTILE = '"><script>alert(1)</script>'


def _document(**overrides: object) -> dict:
    document: dict = {
        "rating": 3,
        "domain": "opencloud.example.com",
        "product": "OpenCloud",
        "version": "7.2.3",
        "releaseType": "production",
        "EOL": False,
        "scannedAt": {"date": "2026-09-17 12:00:00.000000"},
        "hardenings": {},
        "setup": {},
        "vulnerabilities": [],
        "extraChecks": [
            {
                "id": "directoryListing",
                "severity": "high",
                "passed": False,
                "ignored": False,
                "detail": "A directory index is served",
            }
        ],
    }
    document.update(overrides)
    return document


def _report(**overrides: object) -> str:
    return html_report(_document(**overrides), identifier="b6f2c0c5-1c4b")


# ------------------------------------------------- it is one self-contained file


def test_the_format_is_registered_with_a_media_type_and_a_suffix():
    assert "html" in EXPORT_FORMATS
    assert MEDIA_TYPES["html"].startswith("text/html")
    assert FILE_SUFFIXES["html"] == "html"


def test_opening_the_report_makes_no_request_to_anybody():
    """
    The property the whole format exists for.

    Anything with `src`, and any `href` that is not a link the reader chooses
    to follow, would be fetched the moment the file is opened.
    """
    report = _report()

    assert "<script" not in report.lower()
    assert " src=" not in report
    assert "<link" not in report.lower()
    assert "@import" not in report
    assert "url(" not in report
    # The only addresses are documentation links, which a reader follows
    # deliberately - never a resource the page pulls in by itself.
    for href in re.findall(r'href="([^"]*)"', report):
        assert href.startswith("https://"), href


def test_the_presentation_travels_with_the_document():
    """A stylesheet left behind is a blank page for whoever opens it next year."""
    report = _report()

    assert "<style>" in report
    assert "font-family: system-ui" in report
    assert "@media print" in report
    assert 'name="viewport"' in report


def test_there_is_nothing_to_operate_in_a_saved_file():
    """No form to submit, no scan to start, nothing to poll, no token to leak."""
    report = _report()

    for absent in ("<form", "<input", "<button", "rescan", "erasure", "Bearer"):
        assert absent.lower() not in report.lower()


def test_the_report_says_it_is_a_copy_that_outlives_the_service():
    """
    Somebody who has the file needs to know two things about it: it keeps
    working when the link stops, and deleting the scan does not delete it.
    """
    report = _report()

    assert "after the result link" in report
    assert "will not update" in report
    assert "no network request" in report


# ------------------------------------------------------------ untrusted text


@pytest.mark.parametrize(
    "field",
    ["domain", "product", "version", "releaseType"],
)
def test_a_hostile_value_from_the_scanned_instance_cannot_inject_markup(field: str):
    """
    Half of a report is a string the scanned host chose. A target that
    poisons the report of anybody who scans it is the case to beat.
    """
    report = _report(**{field: HOSTILE})

    assert "<script>alert(1)</script>" not in report
    assert "&lt;script&gt;" in report


def test_a_hostile_finding_detail_cannot_inject_markup():
    report = _report(
        extraChecks=[
            {
                "id": "directoryListing",
                "severity": "high",
                "passed": False,
                "ignored": False,
                "detail": HOSTILE,
            }
        ]
    )

    assert "<script>alert(1)</script>" not in report
    assert "&lt;script&gt;" in report


def test_a_hostile_waiver_reason_cannot_inject_markup():
    """A reason is text an operator typed, which makes it text and not markup."""
    report = _report(
        waivers=[
            {
                "pattern": "debugPort:*",
                "reason": HOSTILE,
                "expiresAt": "2026-12-31T00:00:00+00:00",
                "state": "active",
            }
        ]
    )

    assert "<script>alert(1)</script>" not in report
    assert "&lt;script&gt;" in report


def test_a_javascript_link_is_rendered_as_text_rather_than_as_a_link():
    """
    A file opened from somebody's own disk is the one place a `javascript:`
    href would run with nothing between it and the reader.
    """
    report = _report(
        extraChecks=[
            {
                "id": "directoryListing",
                "severity": "high",
                "passed": False,
                "ignored": False,
                "detail": "x",
                "reference": "javascript:alert(1)",
            }
        ]
    )

    assert "javascript:alert(1)" not in report or 'href="javascript:' not in report
    assert 'href="javascript:' not in report


def test_text_in_any_language_survives_the_round_trip():
    """The content can be in any language even though the report is English."""
    report = _report(product="OpenCloud Größe 日本語 Ñ")

    assert 'charset="utf-8"' in report or "charset=utf-8" in report
    assert "Größe" in report
    assert "日本語" in report


# --------------------------------------------- it agrees with the dashboard


def test_the_grade_and_the_findings_are_the_ones_the_dashboard_shows():
    """
    Nothing is decided here. A report that disagreed with the page it came
    from would be worse than no report.
    """
    from webapp.catalog import summarise

    document = _document()
    summary = summarise(document)
    report = html_report(document)

    assert str(summary["rating"]) in report
    assert summary["label"] in report
    assert "directoryListing" in report


def test_a_report_without_coverage_says_so_rather_than_claiming_none():
    report = _report()

    assert "does not record its coverage" in report


def test_the_coverage_gaps_are_listed_when_the_scan_recorded_them():
    report = _report(
        coverage={
            "schema": 1,
            "counts": {"passed": 5, "failed": 1, "not_checked": 2,
                       "inconclusive": 0, "total": 8},
            "checks": [
                {"id": "tlsInspection", "group": "tls", "state": "not_checked",
                 "reason": "not_applicable",
                 "detail": "The instance answered over plain HTTP."},
            ],
        }
    )

    assert "6 of 8 checks reached a conclusion" in report
    assert "tlsInspection" in report
    assert "plain HTTP" in report


def test_a_report_without_provenance_marks_the_metadata_unavailable():
    report = _report()

    assert "predates the record of its own" in report


def test_the_reference_data_it_was_judged_against_is_named():
    report = _report(
        provenance={
            "schema": 1,
            "scannerVersion": "1.25.0",
            "scannedAt": "2026-09-17T12:00:00+00:00",
            "releaseTrack": "production",
            "advisoryData": {"digest": "a" * 64, "count": 3},
            "scheduleData": {"digest": "b" * 64, "updated": "2026-09-15"},
            "waivers": {"active": [], "expired": []},
        }
    )

    assert "1.25.0" in report
    assert "3 record(s)" in report
    assert "generated 2026-09-15" in report


# ------------------------------------------------------------- the route


def test_the_route_serves_it_as_a_download_with_the_right_headers(
    finished_scan,  # noqa: F811 - the fixture imported above
):
    """The capability, the attachment header and the media type, end to end."""
    response = client().get(f"/api/scans/{IDENTIFIER}/export/html")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "attachment" in response.headers["content-disposition"]
    assert f"scan-{IDENTIFIER}.html" in response.headers["content-disposition"]
    assert response.text.startswith("<!DOCTYPE html>")


def test_an_unknown_capability_gets_the_same_404_as_any_other_format():
    unknown = client().get(
        "/api/scans/00000000-0000-4000-8000-000000000000/export/html"
    )

    assert unknown.status_code == 404
