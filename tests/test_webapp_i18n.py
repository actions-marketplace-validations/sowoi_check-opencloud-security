"""The frontend speaks the visitor's language without changing API contracts."""

from __future__ import annotations

import re
from string import Formatter

import pytest
from jinja2 import Environment

from tests.webapp_support import (  # noqa: F401 - the fixtures are autouse
    _isolated_backend,
    _offline_resolver,
    client,
)
from webapp.i18n import (
    LANGUAGE_COOKIE,
    Translator,
    negotiate_locale,
    parse_accept_language,
    safe_next_path,
)
from webapp.locales import CATALOGUES

FRONTEND_PATHS = (
    "/",
    "/how-it-works",
    "/grades",
    "/catalogue",
    "/documentation",
    "/search",
    "/compare",
    "/api",
    "/privacy",
    "/about",
)


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("de-DE,de;q=0.9,en;q=0.8", "de"),
        ("es-MX;q=0.7,fr;q=0.9", "fr"),
        ("fr-CA,en;q=0.5", "fr"),
        ("nl-NL,*;q=0.5", "en"),
        ("de;q=0,en;q=0.5", "en"),
        ("not a language", "en"),
    ],
)
def test_browser_language_negotiation_honours_regions_and_quality(
    header: str, expected: str
):
    """A browser's weighted language list must select the best supported locale."""
    assert negotiate_locale(header) == expected


def test_a_quality_that_is_not_a_number_is_not_a_preference():
    """
    ``q=nan`` parses as a float and then compares false against everything.

    Left in, it decides the order of the weighted list by whichever
    comparisons Python happened to make, so the language a visitor is served
    stops following the header they sent. A weight that is not a weight is
    dropped like an unparsable one, while a client that overshoots the range
    is still understood.
    """
    assert parse_accept_language("de;q=nan") == ()
    assert negotiate_locale("de;q=nan,fr;q=0.5") == "fr"
    # The negative half: a real weight in the same header still counts, and an
    # out-of-range one is clamped rather than discarded.
    assert parse_accept_language("de;q=nan,fr;q=0.5") == (("fr", 0.5),)
    assert parse_accept_language("de;q=1.5") == (("de", 1.0),)
    assert negotiate_locale("de;q=1.5,fr;q=0.9") == "de"


def test_a_chosen_language_persists_and_overrides_the_browser():
    """A deliberate switch must win over later browser-language negotiation."""
    test_client = client()

    response = test_client.post(
        "/language",
        data={"locale": "de", "next": "/grades"},
        headers={"accept-language": "fr"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/grades"
    assert f"{LANGUAGE_COOKIE}=de" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=lax" in response.headers["set-cookie"]
    page = test_client.get("/grades", headers={"accept-language": "fr"})
    assert '<html lang="de">' in page.text
    assert Translator("de")("grades.title") in page.text


@pytest.mark.parametrize(
    "destination",
    [
        "https://attacker.example/",
        "//attacker.example/",
        "/../admin",
        r"/\attacker",
        "/%2f%2fattacker.example",
    ],
)
def test_the_language_switch_cannot_redirect_off_site(destination: str):
    """The switcher's return field must never become an open redirect."""
    response = client().post(
        "/language",
        data={"locale": "fr", "next": destination},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_safe_language_return_paths_keep_local_pages_and_drop_queries():
    """Switching on a result page should retain its path without copying a query."""
    assert safe_next_path("/scans/1234?source=elsewhere#result") == "/scans/1234"


def test_every_catalog_has_the_same_keys_placeholders_and_markup():
    """A translated page must not lose a sentence, value, link, or emphasis."""
    english = CATALOGUES["en"]

    for locale in ("de", "es", "fr"):
        translated = CATALOGUES[locale]
        assert translated.keys() == english.keys()
        for key, source in english.items():
            assert _fields(translated[key]) == _fields(source), (locale, key)
            assert _tags(translated[key]) == _tags(source), (locale, key)


@pytest.mark.parametrize("locale", ["en", "de", "es", "fr"])
def test_every_handwritten_page_renders_in_each_language(locale: str):
    """One incomplete catalog key must not break an otherwise reachable page."""
    test_client = client()
    test_client.cookies.set(LANGUAGE_COOKIE, locale)

    for path in FRONTEND_PATHS:
        page = test_client.get(path)
        assert page.status_code == 200
        assert f'<html lang="{locale}">' in page.text
        assert 'action="/language"' in page.text


def test_machine_readable_contracts_remain_english():
    """Language negotiation must never mutate schemas consumed by software."""
    test_client = client(enable_docs=True)
    english = test_client.get("/openapi.json").json()
    german = test_client.get(
        "/openapi.json", headers={"accept-language": "de-DE"}
    ).json()

    assert german == english


def test_html_translation_placeholders_cannot_inject_tags_or_attributes():
    """Untrusted placeholder text must stay escaped inside trusted catalogue HTML."""
    payload = '"><img src=x onerror="alert(1)">'
    translated = Translator("en").html("docs.index.options.manual", project=payload)
    rendered = Environment(autoescape=True).from_string("{{ value }}").render(
        value=translated
    )

    assert "<img" not in rendered
    assert 'onerror="' not in rendered
    assert "&lt;img" in rendered
    assert "&#34;alert(1)&#34;" in rendered


def test_html_translation_keeps_trusted_catalogue_markup_renderable():
    """Allow-listed inline elements authored in a catalogue must remain HTML."""
    translated = Translator("en").html(
        "docs.index.options.manual", project="https://opencloud.example.com/docs"
    )
    rendered = Environment(autoescape=True).from_string("{{ value }}").render(
        value=translated
    )

    assert '<a href="https://opencloud.example.com/docs#cli-usage"' in rendered
    assert "</a>" in rendered
    assert "&lt;a " not in rendered


def _fields(value: str) -> tuple[str, ...]:
    return tuple(
        field_name
        for _, field_name, _, _ in Formatter().parse(value)
        if field_name is not None
    )


def _tags(value: str) -> tuple[str, ...]:
    return tuple(re.findall(r"</?[^>]+>", value))


# ----------------------------------------------------------- German register

#: German is written in the informal "du" (see AGENTS.md, "Frontend prose").
#: These keys predate that guideline and still address the reader as "Sie".
#: The set may only shrink: rewrite a string to "du" and remove its key here.
#: Never add a key - a new or reworded German string uses "du".
FORMAL_GERMAN_KEYS = frozenset(
    {
        "about.project.body",
        "about.project.origin",
        "admin.lede",
        "admin.search.remedy",
        "api.clients.intro",
        "api.lede",
        "api.rules.body",
        "catalogue.lede",
        "cli.lede",
        "cli.nodocker.body",
        "cli.oneliner.body",
        "cli.private.body",
        "compare.error.same",
        "compare.error.unfinished.baseline",
        "compare.error.unfinished.current",
        "compare.error.unknown.baseline",
        "compare.error.unknown.current",
        "compare.form.hint",
        "compare.lede",
        "compare.upload.error.expired",
        "compare.upload.error.missing",
        "compare.upload.error.no_current",
        "compare.upload.error.rate_limit",
        "compare.upload.error.unreadable",
        "compare.upload.expires",
        "compare.upload.lede",
        "docs.index.lede",
        "docs.index.quickstart.container",
        "error.rate_limit.client",
        "error.rate_limit.daily",
        "error.rate_limit.probe",
        "error.rate_limit.target",
        "error.target.address_only",
        "error.target.empty",
        "error.target.wildcard_dns",
        "footer.legal.scope",
        "grade.0.improve",
        "grade.1.improve",
        "grade.2.improve",
        "grade.3.improve",
        "grade.4.improve",
        "grade.5.improve",
        "grades.improve.intro",
        "grades.improve.release",
        "grades.improve.rerun",
        "grades.lede",
        "grades.limits.body",
        "how.faq.a2",
        "how.faq.a5",
        "how.pipeline.step3",
        "index.assurance.aria",
        "index.assurance.noaccount.body",
        "index.description",
        "index.error.self_host",
        "index.field.hint",
        "index.headline",
        "index.lede",
        "index.remember.summary",
        "index.waivers.search.empty",
        "notfound.lede",
        "privacy.self_host",
        "privacy.uploads.body",
        "privacy.uploads.heading",
        "result.excluded.waived.heading",
        "result.export.lede",
        "result.failed.body",
        "result.feedback.prompt",
        "result.fragment.caution",
        "result.fragment.heading",
        "result.fragment.lede",
        "result.fragment.nothing",
        "result.fragment.undecided",
        "result.hardening.lede",
        "result.progress.noscript",
        "result.rescan.note",
        "result.share.email.hint",
        "result.share.lede",
        "result.share.warning",
        "search.status.idle",
    }
)

#: "Sie", "Ihnen" and "Ihr..." capitalised in the middle of a sentence can only
#: be the formal address. At the start of a sentence they may just as well mean
#: "she" or "they", so those are left alone - the guideline still applies there,
#: the test cannot tell.
_FORMAL_GERMAN = re.compile(r"\b(?:Sie|Ihnen|Ihr(?:e[mnrs]?)?)\b")


def _formal_address(value: str) -> list[str]:
    text = re.sub(r"<[^>]+>", "", value)
    found = []
    for match in _FORMAL_GERMAN.finditer(text):
        before = text[: match.start()].rstrip()
        if before and before[-1] not in ".!?:-\u2013":
            found.append(match.group(0))
    return found


@pytest.mark.parametrize(
    ("text", "formal"),
    [
        ("Prüfe die Adresse und starte den Scan erneut.", False),
        ("Prüfen Sie die Adresse.", True),
        ("Das sind viele Berichte aus Ihrem Netz.", True),
        ("Von Ihnen ausgenommene Befunde", True),
        ("Wie sicher ist <em>Ihre</em> Instanz?", True),
        # Third person at a sentence start: "they", not the reader.
        ("Die Werte sind fest. Sie dienen zur Information.", False),
        ("<strong>Der Scan erhält eine Kennung.</strong> Sie ermöglicht den Zugriff.", False),
        ("OpenCloud prüft sie und ihre Werte.", False),
    ],
)
def test_the_formal_address_detector_tells_the_reader_from_a_third_person(
    text: str, formal: bool
):
    """A detector that flags "they" would push translators into worse German."""
    assert bool(_formal_address(text)) is formal


def test_new_german_strings_address_the_reader_informally():
    """
    The guideline for new German text is "du", and the catalogue must not drift back.

    Most existing strings are formal, so copying a neighbour is the easy
    mistake; this names the key that did it.
    """
    formal = {
        key: _formal_address(value)
        for key, value in CATALOGUES["de"].items()
        if key not in FORMAL_GERMAN_KEYS and _formal_address(value)
    }

    assert formal == {}


def test_the_formal_german_list_only_names_strings_that_are_still_formal():
    """A key rewritten to "du" leaves the list, so the list keeps shrinking."""
    assert FORMAL_GERMAN_KEYS <= CATALOGUES["de"].keys()
    assert sorted(
        key for key in FORMAL_GERMAN_KEYS if not _formal_address(CATALOGUES["de"][key])
    ) == []
