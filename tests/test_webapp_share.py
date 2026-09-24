"""
Sharing a report without handing it to anybody on the way.

The address of a report page is the credential for it (ADR 0007), so the
tests here are mostly negative: no third party is contacted, no share-intent
URL is offered, and the text held out for pasting into a chat channel carries
the findings *without* the link. The positive half is small by comparison -
there is a ``mailto:`` and there are two clipboard buttons.
"""

from __future__ import annotations

import asyncio
import re
from html import unescape
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient

from tests.fake_opencloud import FakeOpenCloud, InstanceBehaviour
from tests.webapp_support import (  # noqa: F401 - the fixtures are autouse
    _isolated_backend,
    _offline_resolver,
    settings,
)
from webapp.app import create_app
from webapp.i18n import LANGUAGE_COOKIE, Translator
from webapp.locales import CATALOGUES
from webapp.reports import EXPORT_FORMATS
from webapp.tasks import run_scan

IDENTIFIER = "b6f2c0c5-1c4b-4f4e-9a3b-0d3f8b7c1a20"
ORIGIN = "https://scan.example.org"

# Anything that would fetch the page to build a preview of it, or that would
# carry the address off this origin as a side effect of a click.
THIRD_PARTY_SHARE = (
    "slack.com",
    "teams.microsoft.com",
    "office.com",
    "twitter.com",
    "x.com",
    "facebook.com",
    "linkedin.com",
    "wa.me",
    "telegram.me",
    "share?",
    "sharer",
    "intent/tweet",
)


@pytest.fixture(params=tuple(CATALOGUES))
def report_page(request) -> str:
    """One real scan of the fake instance, rendered as the page a reader sees."""
    configured = settings(
        allow_private_targets=True,
        verify_tls=False,
        scan_timeout=5,
        public_base_url=ORIGIN,
    )
    app = create_app(configured)
    with TestClient(app) as test_client:
        test_client.cookies.set(LANGUAGE_COOKIE, request.param)
        store = app.state.store
        with FakeOpenCloud(InstanceBehaviour(basic_auth=True)) as instance:
            asyncio.run(
                store.create(
                    IDENTIFIER,
                    target=f"http://{instance.host}",
                    ignore_hardenings=(),
                    output_format="dashboard",
                )
            )
            asyncio.run(run_scan({"web_settings": configured, "store": store}, IDENTIFIER))
        response = test_client.get(f"/scan/{IDENTIFIER}")
        assert response.status_code == 200
        assert f'<html lang="{request.param}">' in response.text
        return response.text


def _share_section(page: str) -> str:
    """Just the sharing card, so an assertion cannot pass on the rest of the page."""
    heading = page.index('id="share"')
    start = page.rfind("<section", 0, heading)
    end = page.index("</section>", heading) + len("</section>")
    return page[start:end]


def _translator(page: str) -> Translator:
    """Use the page language rather than assuming that the render was English."""
    match = re.search(r'<html lang="([a-z]+)"', page)
    assert match is not None
    return Translator(match.group(1))


def test_sharing_offers_no_third_party_and_names_none(report_page: str):
    """A service that unfurls a link would be fetching somebody's report to preview it."""
    section = _share_section(report_page)

    for host in THIRD_PARTY_SHARE:
        assert host not in section.lower(), f"{host} is offered a report address"


def test_the_email_link_is_a_mailto_and_reaches_no_server(report_page: str):
    """`mailto:` is handed to the reader's own client; nothing is posted anywhere."""
    hrefs = re.findall(r'href="(mailto:[^"]*)"', report_page)

    assert len(hrefs) == 1
    body = hrefs[0]
    # The report address travels in the body the reader chooses to send.
    assert "scan.example.org" in body.replace("%3A", ":").replace("%2F", "/")
    assert "http" not in body.split("body=")[0]
    query = parse_qs(urlsplit(unescape(body)).query)
    translator = _translator(report_page)
    assert query["body"] == [
        translator("result.share.email.body", url=f"{ORIGIN}/scan/{IDENTIFIER}")
    ]
    assert query["subject"][0].startswith(
        translator("result.share.email.subject").split("{target}")[0]
    )


def test_the_summary_for_a_chat_channel_carries_no_link(report_page: str):
    """Pasting findings into a channel must not hand everyone in it a capability."""
    summary = re.search(
        r"<div hidden data-share-summary-text>(.*?)</div>", report_page, re.DOTALL
    )
    assert summary is not None
    text = summary.group(1)

    expected_heading = _translator(report_page)("result.share.summary.body").split(
        "{domain}", 1
    )[0]
    assert expected_heading in unescape(text)
    # The negative, which is the whole reason this exists separately.
    assert IDENTIFIER not in text
    assert "http://" not in text and "https://" not in text
    assert "/scan/" not in text


def test_the_copy_buttons_are_hidden_until_a_script_can_use_them(report_page: str):
    """A button that cannot reach a clipboard is worse than the address in plain text."""
    section = _share_section(report_page)
    buttons = re.findall(r"<button[^>]*data-share-copy[^>]*>", section)

    assert len(buttons) == 2
    for button in buttons:
        assert "hidden" in button
    # And the reader who never runs the script still gets the address.
    assert "data-share-fallback" in report_page


def test_the_reader_is_told_the_address_is_the_credential(report_page: str):
    """Someone about to paste a link into a channel needs to know what it grants."""
    section = _share_section(report_page)

    warning = re.search(r'<p class="hint share-warning">(.*?)</p>', section, re.DOTALL)
    assert warning is not None
    text = unescape(warning.group(1))
    translator = _translator(report_page)
    assert translator("result.share.warning") in text
    # Keep the access, expiry and preview warnings even if catalogue text changes.
    concepts = {
        "en": ("anyone", "expires", "preview"),
        "de": ("wer", "ablauf", "linkvorschau"),
        "es": ("cualquier persona", "caduque", "vista previa"),
        "fr": ("toute personne", "expiration", "aperçu"),
    }
    assert all(concept in text.lower() for concept in concepts[translator.locale])


def test_every_language_offers_the_supported_downloads(report_page: str):
    """A translated result must keep every full-report and remediation download."""
    formats = re.findall(
        rf'href="/api/scans/{IDENTIFIER}/export/([a-z-]+)"', report_page
    )
    assert set(formats) == set(EXPORT_FORMATS)
    assert len(formats) == len(EXPORT_FORMATS)
    assert _translator(report_page)("result.export.lede") in unescape(report_page)


def test_sharing_adds_no_inline_script_or_handler(report_page: str):
    """The CSP has no `unsafe-inline`, so a handler in the markup would not run."""
    section = _share_section(report_page)

    assert "onclick" not in section.lower()
    assert "<script" not in section.lower()
    assert "javascript:" not in section.lower()
