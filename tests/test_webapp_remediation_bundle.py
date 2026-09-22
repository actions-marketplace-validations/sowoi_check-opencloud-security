"""
The bundle: only the open work, with the configuration that closes it.

The other exports are the whole scan. This one is deliberately a subset, and
a subset is the easy thing to get wrong in both directions - leaving out a
finding somebody then never fixes, or quietly including a waived one that an
operator already decided to accept. Both are checked here against a real scan
of ``tests/fake_opencloud.py`` rather than a hardcoded list, so a check added
to the scanner is covered without anybody remembering to update this file.

The fragments matter as much as the prose: the file's whole promise is that
what it prints can be pasted, so a flavour that claims to cover a finding has
to actually carry that finding's assignment.
"""

from __future__ import annotations

import pytest

from opencloud_local_scan import __version__, describe_hardening
from tests.test_webapp_exports import (  # noqa: F401 - finished_scan is a fixture
    IDENTIFIER,
    finished_scan,
)
from tests.webapp_support import (  # noqa: F401 - the fixtures are autouse
    MEMORY_URL,
    _isolated_backend,
    _offline_resolver,
    backend,
    client,
    settings,
)
from webapp.catalog import open_findings, summarise
from webapp.remediation_bundle import remediation_html, remediation_markdown
from webapp.reports import EXPORT_FORMATS, FILE_SUFFIXES, MEDIA_TYPES
from webapp.workflows import EXPORT_FORMATS as workflow_formats

pytest.importorskip("fastapi", reason="the web extra is not installed")

HOSTILE = '"><script>alert(1)</script>[click](javascript:alert(1))'


def _document(**overrides: object) -> dict:
    """A small result with one of each kind of open finding."""
    document: dict = {
        "rating": 2,
        "domain": "opencloud.example.com",
        "product": "OpenCloud",
        "version": "7.2.3",
        "releaseType": "production",
        "EOL": False,
        "scannedAt": {"date": "2026-09-17 12:00:00.000000"},
        "hardenings": {"basicAuthDisabled": False},
        "setup": {"headers": {"Strict-Transport-Security": False}},
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


# --- what belongs in it, and what does not


def test_every_open_finding_is_in_both_bundles(
    finished_scan,  # noqa: F811 - the fixture imported above
):
    """A fix left out of the bundle is a fix nobody does."""
    summary = summarise(finished_scan)
    names = open_findings(summary)
    assert names, "the fake instance must leave something open to test this"

    markdown = remediation_markdown(finished_scan)
    html = remediation_html(finished_scan)
    for name in names:
        assert name in markdown, f"{name} is missing from the Markdown bundle"
        assert name in html, f"{name} is missing from the HTML bundle"


def test_the_bundle_leaves_out_what_was_waived_or_cannot_be_acted_on():
    """
    A waived finding was accepted on purpose and an unfixable one is hardcoded.

    Printing either under "the work to do" would send somebody to change a
    setting they already decided about, or one that does not exist.
    """
    document = _document(
        hardenings={"basicAuthDisabled": False},
        extraChecks=[
            {
                "id": "directoryListing",
                "severity": "high",
                "passed": False,
                "ignored": True,
                "detail": "accepted by the operator",
            }
        ],
    )
    summary = summarise(document)
    assert summary["waived"], "the fixture must waive something to test this"

    markdown = remediation_markdown(document)
    assert "directoryListing" not in markdown
    assert "basicAuthDisabled" in markdown


def test_the_bundle_carries_no_grade_advisory_or_passed_check(
    finished_scan,  # noqa: F811 - the fixture imported above
):
    """
    The bundle is the complement of the report, not a second copy of it.

    If the grade and the passed checks drift back in, the one file that was
    only about the outstanding work stops being that.
    """
    summary = summarise(finished_scan)
    assert summary["passedChecks"], "the fake instance must pass something"

    markdown = remediation_markdown(finished_scan)
    for passed in summary["passedChecks"]:
        assert passed not in markdown, f"{passed} already passes and is not work"
    assert "out of 5" not in markdown
    assert str(summary["label"]) not in markdown.split("---")[0].splitlines()[0]


def test_a_finding_carries_its_evidence_and_its_fix(
    finished_scan,  # noqa: F811 - the fixture imported above
):
    """A finding without what was observed is an assertion, not a report."""
    summary = summarise(finished_scan)
    issue = next(item for item in summary["issues"] if item.get("detail"))

    markdown = remediation_markdown(finished_scan)
    assert str(issue["detail"])[:60] in markdown
    assert describe_hardening(str(issue["id"])).remediation[:60] in markdown


# --- the fragments


def test_each_fragment_covers_what_it_says_it_covers():
    """A snippet that omits a finding it lists is a file pasted in vain."""
    markdown = remediation_markdown(_document())

    # The env flavours carry the OpenCloud setting, the header flavours the
    # header - and each names the other as belonging elsewhere.
    assert "PROXY_ENABLE_BASIC_AUTH" in markdown
    assert 'add_header Strict-Transport-Security' in markdown
    assert "Those belong in: nginx, Caddy, Traefik." in markdown
    assert "Those belong in: Docker Compose, .env." in markdown


def test_every_flavour_is_rendered_not_only_the_default():
    """
    A file handed to somebody else has no picker.

    The person who opens it may run Caddy when the scan was read by the one
    running Compose, so every flavour that has something to say is written.
    """
    markdown = remediation_markdown(_document())
    for filename in (
        "docker-compose.yml",
        ".env",
        "nginx.conf",
        "Caddyfile",
        "traefik-dynamic.yml",
    ):
        assert filename in markdown


def test_a_flavour_with_nothing_to_write_is_left_out():
    """An empty code block promises a fix and delivers none."""
    only_headers = _document(
        hardenings={}, setup={"headers": {"Strict-Transport-Security": False}}
    )
    markdown = remediation_markdown(only_headers)
    assert "nginx.conf" in markdown
    assert "docker-compose.yml" not in markdown


def test_a_finding_with_no_mechanical_fix_is_named_rather_than_guessed_at():
    """
    A fragment that must be edited before it is pasted looks finished and is not.

    ``directoryListing`` is fixed by pointing a web server somewhere else -
    a decision about the deployment - so the catalogue gives it no assignment
    and the bundle has to say so rather than invent a placeholder.
    """
    markdown = remediation_markdown(_document())
    section = markdown.split("## No mechanical fix")[1]
    assert "directoryListing" in section


def test_an_instance_with_nothing_open_says_so():
    """Silence would read as a bundle that failed to render."""
    clean = _document(hardenings={}, setup={"headers": {}}, extraChecks=[])
    assert "Nothing to do" in remediation_markdown(clean)
    assert "Nothing to do" in remediation_html(clean)


# --- what the scanned instance is allowed to put in the file


def test_a_hostile_detail_is_not_markup_in_either_bundle():
    """
    The evidence is a string the *scanned* instance chose.

    In the HTML bundle it must not be a script, and in the Markdown one it
    must not become a link - the file is opened by somebody who did not run
    the scan and has no reason to distrust it.
    """
    document = _document(
        product=HOSTILE,
        extraChecks=[
            {
                "id": "directoryListing",
                "severity": "high",
                "passed": False,
                "ignored": False,
                "detail": HOSTILE,
            }
        ],
    )

    html = remediation_html(document)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html

    markdown = remediation_markdown(document)
    assert "<script>" not in markdown
    assert "[click](javascript:" not in markdown
    assert "\\[click\\]" in markdown


def test_the_html_bundle_fetches_nothing_when_it_is_opened():
    """
    A saved file that phones home turns "I opened my notes" into a signal.

    Same rule as the HTML report: the documentation links are the only
    addresses, and they are followed only if the reader clicks one.
    """
    html = remediation_html(_document())
    assert "<link" not in html
    assert "<script" not in html
    assert "<img" not in html
    assert "fonts.googleapis" not in html
    assert "@import" not in html


# --- how it is asked for


def test_both_bundles_are_offered_as_exports_with_their_own_filenames():
    """A download named like the report next to it is the wrong file to open."""
    for fmt in ("remediation-md", "remediation-html"):
        assert fmt in EXPORT_FORMATS
        assert fmt in MEDIA_TYPES
        assert fmt in FILE_SUFFIXES
    assert FILE_SUFFIXES["remediation-md"] == "remediation.md"
    assert MEDIA_TYPES["remediation-md"].startswith("text/markdown")


def test_the_workflow_layer_offers_exactly_the_formats_the_service_renders():
    """
    An agent that cannot ask for a format a browser can download is a
    second-class client, which is the one thing ADR 0011 rules out.

    ``workflows.py`` repeats the list rather than importing it - it is the
    client side of the API and imports nothing that renders - so the only
    thing keeping the two honest is this assertion.
    """
    assert set(workflow_formats) == set(EXPORT_FORMATS)


def test_the_export_endpoint_serves_both_bundles(
    finished_scan,  # noqa: F811 - the fixture imported above
):
    """The route is what an operator actually reaches; the renderer is not."""
    test_client = client()

    response = test_client.get(f"/api/scans/{IDENTIFIER}/export/remediation-md")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert IDENTIFIER in response.headers["content-disposition"]
    assert "remediation.md" in response.headers["content-disposition"]
    assert "OpenCloud remediation bundle" in response.text
    assert __version__ in response.text

    response = test_client.get(f"/api/scans/{IDENTIFIER}/export/remediation-html")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.text.startswith("<!DOCTYPE html>")
