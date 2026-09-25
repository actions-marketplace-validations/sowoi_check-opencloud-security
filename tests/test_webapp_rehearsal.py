"""
The upgrade rehearsal, rendered beside the grade.

The scanner decided all of it - which releases are worth moving to, what each
one fixes and leaves, and the rating each would reach. The web layer may only
regroup that, so the properties worth protecting are that no number is
recomputed here, that a result from before the rehearsal existed renders as a
page without the panel rather than as an instance with nothing to upgrade to,
and that a version string the scanned host chose reaches the page as text.
"""

from __future__ import annotations

import asyncio
from html import unescape

import pytest
from fastapi.testclient import TestClient

from tests.webapp_support import (  # noqa: F401 - the fixtures are autouse
    _isolated_backend,
    _offline_resolver,
    settings,
)
from webapp.app import create_app
from webapp.catalog import _upgrade_rehearsal, summarise
from webapp.i18n import LANGUAGE_COOKIE, Translator

pytest.importorskip("fastapi", reason="the web extra is not installed")

IDENTIFIER = "1a2b3c4d-5e6f-4a8b-9c0d-1e2f3a4b5c6d"

REHEARSAL = [
    {
        "version": "7.2.4",
        "line": "7.2",
        "recommended": True,
        "fixes": ["CVE-2026-0001"],
        "stillAffected": ["CVE-2026-0002"],
        "introduces": [],
        "endOfLife": False,
        "versionRating": 2,
        "rating": 2,
    },
    {
        "version": "7.3.0",
        "line": "7.3",
        "recommended": False,
        "fixes": ["CVE-2026-0001", "CVE-2026-0002"],
        "stillAffected": [],
        "introduces": [],
        "endOfLife": False,
        "versionRating": 5,
        "rating": 3,
    },
]


def _document(**overrides: object) -> dict:
    """A result document the way the scanner writes one."""
    document: dict = {
        "rating": 3,
        "domain": "opencloud.example.com",
        "product": "OpenCloud",
        "version": "7.2.3",
        "releaseType": "production",
        "EOL": False,
        "scannedAt": {"date": "2026-09-19 12:00:00.000000"},
        "hardenings": {},
        "setup": {},
        "extraChecks": [],
        "vulnerabilities": [],
        "upgradeRehearsal": REHEARSAL,
    }
    document.update(overrides)
    return document


def _page(document: dict, locale: str = "en") -> str:
    """Render the result page for a stored document, without scanning."""
    app = create_app(settings())
    with TestClient(app) as test_client:
        test_client.cookies.set(LANGUAGE_COOKIE, locale)
        store = app.state.store
        asyncio.run(
            store.create(
                IDENTIFIER,
                target="http://opencloud.example.com",
                ignore_hardenings=(),
                output_format="dashboard",
            )
        )
        asyncio.run(store.mark_running(IDENTIFIER))
        asyncio.run(store.mark_completed(IDENTIFIER, document))
        return test_client.get(f"/scan/{IDENTIFIER}").text


# ------------------------------------------------------------- the summary


def test_every_candidate_keeps_the_rating_the_scanner_gave_it():
    """
    The layer rule, in one assertion.

    A grade recomputed here could disagree with the scan that runs after the
    upgrade, which is the whole reason the rehearsal lives in the scanner.
    """
    entries = _upgrade_rehearsal(_document())

    assert [entry["rating"] for entry in entries] == [2, 3]
    assert [entry["versionRating"] for entry in entries] == [2, 5]
    assert [entry["label"] for entry in entries] == ["D", "C"]
    assert [entry["versionLabel"] for entry in entries] == ["D", "A+"]


def test_a_candidate_the_findings_hold_back_is_marked_as_such():
    """
    "Upgrading is not worth it" and "upgrading is not enough" differ.

    7.3.0 would be an A+ on its version alone; this instance's own findings
    cap it at C, and a reader who cannot see that reads the rehearsal as an
    argument against upgrading.
    """
    entries = _upgrade_rehearsal(_document())

    assert entries[0]["cappedByFindings"] is False
    assert entries[1]["cappedByFindings"] is True


def test_a_result_from_before_the_rehearsal_existed_has_no_panel():
    """An older stored result must not render as "nothing to upgrade to"."""
    assert _upgrade_rehearsal({}) == []
    assert _upgrade_rehearsal({"upgradeRehearsal": None}) == []
    assert summarise(_document(upgradeRehearsal=[]))["upgradeRehearsal"] == []


def test_an_entry_without_a_version_is_dropped():
    """There is nothing to offer an operator without the release's name."""
    entries = _upgrade_rehearsal(
        {"upgradeRehearsal": [{"line": "7.3"}, "not a mapping", {"version": "7.3.0"}]}
    )

    assert [entry["version"] for entry in entries] == ["7.3.0"]


def test_the_summary_carries_the_rehearsal_for_the_page():
    """The dashboard reads the summary, not the document."""
    summary = summarise(_document())

    assert [entry["version"] for entry in summary["upgradeRehearsal"]] == [
        "7.2.4",
        "7.3.0",
    ]


# ---------------------------------------------------------------- the page


@pytest.mark.parametrize("locale", ["en", "de", "es", "fr"])
def test_the_result_page_shows_what_each_candidate_would_do(locale):
    """The panel is the point: a reader sees the trade before installing anything."""
    page = _page(_document(), locale)

    assert 'id="rehearsal"' in page
    assert "7.2.4" in page
    assert "7.3.0" in page
    assert "CVE-2026-0002" in page
    assert f'<html lang="{locale}">' in page
    assert Translator(locale)("result.rehearsal.grade", label="C") in unescape(page)


@pytest.mark.parametrize("locale", ["en", "de", "es", "fr"])
def test_a_capped_upgrade_can_still_improve_the_current_grade(locale):
    """A cap below the version-only grade does not mean the upgrade has no benefit."""
    document = _document(rating=1, upgradeRehearsal=[REHEARSAL[1]])
    page = unescape(_page(document, locale))
    translator = Translator(locale)
    assert translator("result.rehearsal.grade", label="C") in page
    assert translator("result.rehearsal.capped", label="A+") in page
    assert translator("result.rehearsal.grade", label="E") not in page
    assert summarise(document)["label"] == "E"


@pytest.mark.parametrize("locale", ["en", "de", "es", "fr"])
def test_a_result_without_a_rehearsal_renders_the_page_without_the_panel(locale):
    """The negative case: no panel, no contents entry, and no error."""
    page = _page(_document(upgradeRehearsal=[]), locale)

    assert 'id="rehearsal"' not in page
    assert 'href="#rehearsal"' not in page


@pytest.mark.parametrize("locale", ["en", "de", "es", "fr"])
def test_a_version_string_the_host_chose_is_text_on_the_page(locale):
    """Every string in a rehearsal entry came from somebody else's server."""
    hostile = dict(REHEARSAL[0], version='7.2.4"><script>alert(1)</script>')
    page = _page(_document(upgradeRehearsal=[hostile]), locale)

    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page
