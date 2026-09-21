"""
The checks that keep four catalogues and three sets of guides honest.

``scripts/check_translations.py`` draws one line: a structural difference
from the English source is a defect a machine can prove, and everything
about prose is a warning a human has to judge. These tests hold that line
from both sides - the structural rules really do fire on broken input, and
the things that only look broken (a literal brace, a hostname, a guide title
the manifest deliberately leaves in English) really do not.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_checker():
    """Load the standalone check script without making scripts/ a package."""
    path = REPO_ROOT / "scripts" / "check_translations.py"
    spec = importlib.util.spec_from_file_location("check_translations", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_translations"] = module
    spec.loader.exec_module(module)
    return module


checker = _load_checker()


# These are marketing and assistant-cliché words, not a general vocabulary
# ban. A technical sentence may be enthusiastic without sounding generated;
# these phrases are the recurring signal that it is not saying anything
# concrete. Keep the list small and add a term only when it has appeared in a
# proposed translation or user-facing sentence.
AI_SLOP = re.compile(
    r"\b(?:"
    r"seamless|robust|leverage|empower|unlock|delve|harness|streamline|"
    r"cutting-edge|game-changer|world-class|best-in-class|furthermore|"
    r"moreover|rest assured|at a glance|it is important to note|"
    r"nahtlos\w*|bahnbrechend\w*|darüber hinaus|im heutigen|"
    r"sin fisuras|puntero|de vanguardia|cabe destacar|en el mundo actual|"
    r"descubre|sans effort|révolutionnaire|à la pointe|il est important de|"
    r"dans le monde actuel|découvrez"
    r")\b",
    re.IGNORECASE,
)

# These phrases are especially easy to miss because they are valid English,
# but they are a defect when copied into a translated guide. They came from
# the profile option added to the four installation guides and stay here as
# a regression check for future generated documentation.
UNTRANSLATED_GUIDE_SLOP = re.compile(
    r"\b(?:Named threshold set|judging the result)\b",
    re.IGNORECASE,
)


def _ai_slop_hits(value: str) -> list[str]:
    """Return cliché wording found in one visible catalogue string."""
    return [match.group(0) for match in AI_SLOP.finditer(value)]


# ------------------------------------------------- the tree as it stands


def test_the_catalogues_have_no_structural_differences():
    """
    A missing key, a lost placeholder or a moved link breaks a page.

    This is the check that fails the build, so it is the one that has to be
    true of the repository as it is, not only of fixtures.
    """
    assert checker.structural_findings() == []


def test_catalogues_do_not_use_ai_slop_wording():
    """Localized copy should describe the product, not sound auto-generated."""
    findings = [
        (locale, key, hit)
        for locale, messages in checker.OWN_MESSAGES.items()
        for key, value in messages.items()
        for hit in _ai_slop_hits(value)
    ]

    assert findings == []


def test_handwritten_guides_and_templates_do_not_use_ai_slop_wording():
    """First-party prose should stay concrete outside the catalogues too."""
    roots = (REPO_ROOT / "docs", REPO_ROOT / "frontend" / "templates")
    findings = []
    for root in roots:
        for path in sorted(root.rglob("*")):
            if path.suffix not in {".md", ".html"}:
                continue
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                for hit in _ai_slop_hits(line):
                    findings.append((path.relative_to(REPO_ROOT).as_posix(), line_number, hit))

    assert findings == []


@pytest.mark.parametrize(
    "value",
    [
        "A seamless and robust experience.",
        "Eine nahtlose und bahnbrechende Lösung.",
        "Una solución de vanguardia; cabe destacar su alcance.",
        "Une solution robuste et à la pointe.",
    ],
)
def test_ai_slop_detector_catches_typical_cliches(value: str):
    """The guard must fail closed when a known cliché is introduced."""
    assert _ai_slop_hits(value)


def test_translated_guides_do_not_keep_known_english_placeholders():
    """Translated guides must not ship the English source sentence unchanged."""
    findings = []
    for locale in checker.GUIDE_LANGUAGES:
        for path in sorted((REPO_ROOT / "docs" / locale).glob("*.md")):
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                for match in UNTRANSLATED_GUIDE_SLOP.finditer(line):
                    findings.append((locale, path.name, line_number, match.group(0)))

    assert findings == []


def test_no_guide_links_to_a_file_that_is_not_there():
    """
    A translated guide sits one directory deeper than its English source.

    Copying the English link depth leaves every path out of ``docs/`` one
    ``../`` short, which is how the French guides arrived with a hundred
    links to nowhere.
    """
    dead = [
        finding
        for finding in checker.guide_findings()
        if finding.severity == "error"
    ]

    assert dead == []


def test_every_style_warning_names_a_place_a_reviewer_can_open():
    """A warning without a location is a warning nobody acts on."""
    for finding in checker.style_findings() + checker.guide_findings():
        assert finding.rule
        assert finding.action
        assert ":" in finding.location
        rendered = finding.render()
        assert finding.location in rendered
        assert finding.rule in rendered
        assert finding.action in rendered


# ------------------------------------------------------- structural rules


def _compare(source: str, translated: str):
    """Every structural finding for one English string and one translation."""
    return checker._compare("de", "webapp/locales/de.py", "some.key", source, translated)


def _rules(source: str, translated: str) -> set[str]:
    return {finding.rule for finding in _compare(source, translated)}


def test_a_lost_placeholder_is_an_error():
    """``{minutes} minutes`` translated without the number says nothing."""
    assert _rules("Kept for {minutes} minutes.", "Wird aufbewahrt.") == {"placeholder"}


def test_an_invented_placeholder_is_an_error():
    """``str.format`` is given the English names and raises on any other."""
    assert _rules("Kept for {minutes}.", "Wird {dauer} aufbewahrt.") == {"placeholder"}


def test_reordering_placeholders_is_not_an_error():
    """Word order is the first thing a translation changes, and may."""
    assert _compare("{a} before {b}", "{b} nach {a}") == []


def test_a_literal_brace_is_not_a_placeholder():
    """A catalogue showing a JSON example writes ``{{`` and stays valid."""
    assert _compare('Send {{"url": "..."}}', 'Sende {{"url": "..."}}') == []


def test_an_unbalanced_brace_is_reported_as_a_format_error():
    """A stray brace raises at render time, on the page, for a visitor."""
    findings = _compare("Kept for {minutes}.", "Wird {minutes aufbewahrt.")

    assert [finding.rule for finding in findings] == ["format-syntax"]
    assert "{{" in findings[0].action


def test_dropped_emphasis_is_an_error():
    """The sentence survives; the part it was making does not."""
    assert _rules("A <strong>failed</strong> check", "Eine fehlgeschlagene Prüfung") == {
        "markup"
    }


def test_markup_a_catalogue_may_not_carry_is_an_error():
    """``Translator.html`` renders these, so the set of elements is a contract."""
    findings = _compare("Plain text", "<script>alert(1)</script>")

    assert "markup" in {finding.rule for finding in findings}
    assert any("script" in finding.detail for finding in findings)


def test_allowed_inline_markup_is_not_an_error():
    """The elements the catalogues already use must stay usable."""
    assert _compare("<code>a</code> and <em>b</em>", "<code>a</code> und <em>b</em>") == []


def test_a_translated_link_target_is_an_error():
    """Translate the words, never the address."""
    findings = _compare(
        '<a href="/grades">Grades</a>', '<a href="/noten">Noten</a>'
    )

    assert "link-target" in {finding.rule for finding in findings}


def test_the_same_link_with_translated_text_is_not_an_error():
    assert _compare('<a href="/grades">Grades</a>', '<a href="/grades">Noten</a>') == []


def test_a_missing_key_and_an_unknown_key_are_both_errors(monkeypatch: pytest.MonkeyPatch):
    """A key only English has is untranslated; one only German has is unread."""
    monkeypatch.setattr(
        checker,
        "OWN_MESSAGES",
        {"en": {"a": "A", "b": "B"}, "de": {"a": "A", "c": "C"}},
    )
    monkeypatch.setattr(checker, "TRANSLATIONS", ("de",))

    rules = {(finding.rule, finding.location) for finding in checker.structural_findings()}

    assert ("missing-key", "webapp/locales/de.py:b") in rules
    assert ("extra-key", "webapp/locales/de.py:c") in rules


# ------------------------------------------------------------ style rules


@pytest.mark.parametrize(
    ("value", "prose"),
    [
        ("opencloud.example.com", False),
        ("{track} · {format}", False),
        ("https://opencloud.example.com/docs", False),
        ("Check an instance for known vulnerabilities.", True),
        ("Grades", False),
    ],
)
def test_only_a_sentence_is_expected_to_be_translated(value: str, prose: bool):
    """
    A hostname, a placeholder row and a single word are the same everywhere.

    Reporting them as untranslated is how a style check becomes noise that
    teaches a reviewer to skip it.
    """
    assert checker._is_prose(value) is prose


def test_a_guide_title_the_manifest_leaves_in_english_is_not_reported():
    """
    ``webapp/locales/__init__.py`` fills untranslated guide titles from the
    manifest on purpose, so every guide is reachable before it is translated.
    Reading the merged catalogue would report all of them as untranslated.
    """
    reported = {
        finding.location.split(":", 1)[1] for finding in checker.style_findings()
    }

    assert not any(key.startswith("docs.") and key.endswith(".title") for key in reported)


@pytest.mark.parametrize(
    ("locale", "text", "wrong_register"),
    [
        ("de", "Prüfe die Adresse und starte den Scan erneut.", False),
        ("de", "Prüfen Sie die Adresse.", True),
        ("de", "Das sind viele Berichte aus Ihrem Netz.", True),
        # Third person at a sentence start is "they", not the reader.
        ("de", "Die Werte sind fest. Sie dienen zur Information.", False),
        ("fr", "Saisissez l'adresse de base.", False),
        ("fr", "Saisis ton adresse de base.", True),
        ("es", "Introduzca la dirección base.", False),
        ("es", "Introduce tu dirección base.", True),
    ],
)
def test_each_language_is_checked_against_its_own_form_of_address(
    locale: str, text: str, wrong_register: bool
):
    """German is informal, French and Spanish are polite - see TRANSLATING.md."""
    _, _, pattern, exempt_start = checker.REGISTER[locale]

    hits = checker._register_hits(text, pattern, exempt_start)

    assert bool(hits) is wrong_register


def test_a_dropped_product_name_is_a_warning_not_an_error(
    monkeypatch: pytest.MonkeyPatch,
):
    """Losing "OpenCloud" costs the reader the word they could have searched."""
    monkeypatch.setattr(
        checker,
        "OWN_MESSAGES",
        {
            "en": {"a": "What this tests on an OpenCloud instance."},
            "de": {"a": "Was hier geprüft wird."},
        },
    )
    monkeypatch.setattr(checker, "TRANSLATIONS", ("de",))

    findings = checker.style_findings()

    assert "protected-term" in {finding.rule for finding in findings}
    assert {finding.severity for finding in findings} == {"warning"}


def test_a_term_rendered_two_ways_is_a_warning(monkeypatch: pytest.MonkeyPatch):
    """The glossary is what keeps one concept one word in each language."""
    monkeypatch.setattr(
        checker,
        "OWN_MESSAGES",
        {
            "en": {"a": "Missing hardening lowers the grade."},
            "de": {"a": "Fehlende Schutzmaßnahmen senken die Note."},
        },
    )
    monkeypatch.setattr(checker, "TRANSLATIONS", ("de",))

    glossary = [
        finding for finding in checker.style_findings() if finding.rule == "glossary"
    ]

    assert len(glossary) == 1
    assert "Härtung" in glossary[0].detail


def test_a_placeholder_name_is_not_a_glossary_term(monkeypatch: pytest.MonkeyPatch):
    """``{waivers}`` is a variable the translation keeps, not a word to render."""
    monkeypatch.setattr(
        checker,
        "OWN_MESSAGES",
        {
            "en": {"a": "Settings: {track} · {waivers}."},
            "de": {"a": "Einstellungen: {track} · {waivers}."},
        },
    )
    monkeypatch.setattr(checker, "TRANSLATIONS", ("de",))

    assert [
        finding for finding in checker.style_findings() if finding.rule == "glossary"
    ] == []


# ---------------------------------------------------------------- reports


def test_an_accepted_finding_is_kept_out_of_the_open_list(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    A decision that has been made is recorded, not switched off.

    ``--show-accepted`` still lists it, so the reason stays readable.
    """
    monkeypatch.setattr(
        checker,
        "OWN_MESSAGES",
        {
            "en": {"a": "Check an OpenCloud instance now."},
            "de": {"a": "Check an OpenCloud instance now."},
        },
    )
    monkeypatch.setattr(checker, "TRANSLATIONS", ("de",))
    monkeypatch.setattr(checker, "GUIDE_LANGUAGES", ())

    before, _ = checker.all_findings()
    assert "untranslated" in {finding.rule for finding in before}

    monkeypatch.setitem(checker.ACCEPTED, ("untranslated", "de", "a"), "A fixture.")
    open_findings, accepted = checker.all_findings()

    assert "untranslated" not in {finding.rule for finding in open_findings}
    assert [finding.rule for finding in accepted] == ["untranslated"]


def test_only_a_structural_error_fails_the_build(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    """Warnings are for a reviewer; a build that fails on them gets ignored."""
    monkeypatch.setattr(
        checker,
        "OWN_MESSAGES",
        {
            "en": {"a": "Check an OpenCloud instance now."},
            "de": {"a": "Check an OpenCloud instance now."},
        },
    )
    monkeypatch.setattr(checker, "TRANSLATIONS", ("de",))
    monkeypatch.setattr(checker, "GUIDE_LANGUAGES", ())

    assert checker.main([]) == 0
    assert checker.main(["--strict"]) == 1
    assert "style warning" in capsys.readouterr().out
