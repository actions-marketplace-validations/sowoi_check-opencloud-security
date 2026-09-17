"""The browser documentation generated from the Markdown operator guides."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

from tests.webapp_support import (  # noqa: F401 - the fixtures are autouse
    _isolated_backend,
    _offline_resolver,
    client,
)
from webapp.documentation import DOCUMENTATION_PAGES, GUIDE_LANGUAGES
from webapp.locales import CATALOGUES

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_generator():
    """Load the standalone build script without making scripts/ a package."""
    path = REPO_ROOT / "scripts" / "build_frontend_documentation.py"
    spec = importlib.util.spec_from_file_location("build_frontend_documentation", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_frontend_documentation"] = module
    spec.loader.exec_module(module)
    return module


generator = _load_generator()


def test_the_generated_documentation_is_current():
    """
    The checked-in HTML must be the page the source Markdown generates.

    Serving generated files keeps Markdown out of the runtime, but only this
    check turns regeneration from a convention into a pipeline.
    """
    assert generator.stale_pages() == []


def test_every_document_has_its_own_local_html_page():
    """The Docs tab must not send somebody to a GitHub Markdown renderer."""
    test_client = client()
    index = test_client.get("/documentation")

    assert index.status_code == 200
    assert "/blob/main/" not in index.text
    for document in DOCUMENTATION_PAGES:
        path = f"/documentation/{document.slug}"
        assert f'href="{path}"' in index.text
        response = test_client.get(path)
        assert response.status_code == 200
        assert f"<h1>{document.title}</h1>" in response.text
        assert generator.GENERATED_MARKER not in response.text
        assert "style=" not in response.text
        assert "<script>" not in response.text
        resources_body = re.sub(
            r'<link rel="(?:canonical|service-desc|arazzo|ai-discovery)"[^>]*>',
            "",
            response.text,
        )
        resources = re.findall(
            r'<(?:script|link|img)[^>]*?(?:src|href)="([^"]+)"',
            resources_body,
        )
        assert resources
        assert all(resource.startswith("/static/") for resource in resources)


def test_an_unknown_document_is_the_same_404_as_any_unknown_page():
    """The generated catalogue must not become a file-serving catch-all."""
    response = client().get(
        "/documentation/not-a-document", headers={"Accept": "text/html"}
    )

    assert response.status_code == 404
    assert "Nothing here" in response.text


@pytest.mark.parametrize("locale,body_language", [("en", "en"), ("de", "de"), ("fr", "fr"), ("es", "es")])
def test_every_guide_serves_the_selected_translation_or_an_explicit_fallback(
    locale: str, body_language: str,
):
    """Every interface language with guide sources serves its own body, and no notice."""
    test_client = client()
    for document in DOCUMENTATION_PAGES:
        response = test_client.get(
            f"/documentation/{document.slug}", headers={"Accept-Language": locale}
        )
        assert response.status_code == 200
        body = re.search(r'<article class="docs-article.*?</article>', response.text, re.DOTALL)
        assert body is not None
        assert f'lang="{body_language}"' in body[0]
        assert "<h1" not in body[0]
        template = generator.render_page(document.slug, body_language)
        expected = re.search(r'<article class="docs-article.*?</article>', template, re.DOTALL)
        assert expected is not None
        # Jinja escapes examples during generation; render before comparing.
        assert "@@CODE:" not in body[0] and "@@TABLE@@" not in body[0]
        first_heading = re.search(r'<h2[^>]*>.*?</h2>', expected[0], re.DOTALL)
        if first_heading:
            assert first_heading[0] in body[0]
        notice = CATALOGUES[locale]["docs.guide.english_notice"]
        assert notice not in response.text
        # The notice is kept for a future locale without sources.
        assert f"locale not in {('en', *GUIDE_LANGUAGES)!r}" in template


def test_translated_guides_keep_the_english_section_anchors():
    """Cross-guide links must reach the same section after a language switch."""
    for document in DOCUMENTATION_PAGES:
        anchors = []
        for language in ("en", *GUIDE_LANGUAGES):
            template = generator.render_page(document.slug, language)
            anchors.append(re.findall(r'<h[2-6] id="([^"]+)"', template))
        assert all(found == anchors[0] for found in anchors), document.slug


def test_a_saved_language_choice_selects_the_german_guide_body():
    """The guide route must honour the same cookie precedence as the interface."""
    test_client = client()
    test_client.post(
        "/language", data={"locale": "de", "next": "/documentation/configuration"}
    )
    response = test_client.get(
        "/documentation/configuration", headers={"Accept-Language": "fr"}
    )
    assert 'data-reveal lang="de"' in response.text
    assert 'data-reveal lang="en"' not in response.text
