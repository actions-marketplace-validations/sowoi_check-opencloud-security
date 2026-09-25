#!/usr/bin/env python3
"""
Build the static frontend search index from its public-page manifest.

One file per language, and the language files are overlays: the English index
carries every page and its text, and ``search-index.<locale>.json`` carries
the translated title, summary and translated body text. German, French and
Spanish guides have their own bodies; a guide entry in any other language
would inherit the English body.

The templates say ``t('some.key')`` rather than the sentence, so the strings
are read out of the catalogues here. Nothing else changes: the manifest is
still the structural reason a scan result cannot enter search.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "frontend" / "static"
OUTPUT = STATIC / "search-index.json"
#: Where the operator area's index lands. Inside the Python package and
#: not under `frontend/static`, because `/static` is mounted and this file
#: is for authorised readers only - it is served by the guarded route in
#: the area, never as an asset.
ADMIN_OUTPUT_DIR = ROOT / "webapp" / "data"

sys.path.insert(0, str(ROOT))
from opencloud_local_scan import __version__
from webapp.documentation import GUIDE_LANGUAGES, TRANSLATED_OPERATOR_SLUGS
from webapp.i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES, Translator
from webapp.search import ADMIN_INDEX_FILES, ADMIN_SEARCH_PAGES, SEARCH_PAGES

_JINJA = re.compile(r"{[#%].*?[#%]}|{{.*?}}", re.DOTALL)
_SPACE = re.compile(r"\s+")
# A catalogue lookup in a template, with the identifier written as a literal.
# A key built from a loop variable is left out rather than guessed at.
_LOOKUP = re.compile(r"{{-?\s*t(?:\.html|\.raw)?\(\s*'([^']+)'.*?\)\s*-?}}", re.DOTALL)
_PLACEHOLDER = re.compile(r"{[a-z_]+}")


def _localised_source(template: str, translate: Translator) -> str:
    """The template with every literal catalogue lookup already resolved."""
    if translate.locale in GUIDE_LANGUAGES and template.startswith("docs/"):
        template = template.replace("docs/", f"docs/{translate.locale}/", 1)
    if (
        translate.locale in GUIDE_LANGUAGES
        and template.startswith("admin-docs/")
        and Path(template).stem in TRANSLATED_OPERATOR_SLUGS
    ):
        template = template.replace("admin-docs/", f"admin-docs/{translate.locale}/", 1)
    source = (ROOT / "frontend" / "templates" / template).read_text(encoding="utf-8")

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if not translate.has(key):
            return " "
        return " " + _PLACEHOLDER.sub("", translate.raw(key)) + " "

    return _LOOKUP.sub(replace, source)


class _Text(HTMLParser):
    """Collect visible authored text without executing a template."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "svg"}:
            self.hidden += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "svg"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


def _body(template: str, translate: Translator) -> str:
    parser = _Text()
    parser.feed(_JINJA.sub(" ", _localised_source(template, translate)))
    return _SPACE.sub(" ", html.unescape(" ".join(parser.parts))).strip()[:20_000]


def _translated(key: str, fallback: str, translate: Translator) -> str:
    return translate(key) if key and translate.has(key) else fallback


def _generated(template: str) -> bool:
    """Whether the page's text is generated from the repository Markdown."""
    return template.startswith(("docs/", "admin-docs/"))


def render(locale: str = DEFAULT_LOCALE) -> str:
    """Return the deterministic release index for one language."""
    translate = Translator(locale)
    pages = []
    for page in SEARCH_PAGES:
        entry = {
            "path": page.path,
            "title": _translated(page.title_key, page.title, translate),
            "summary": _translated(page.summary_key, page.summary, translate),
        }
        # An overlay leaves out the English guide bodies it would only repeat.
        if locale == DEFAULT_LOCALE or locale in GUIDE_LANGUAGES or not _generated(page.template):
            entry["body"] = _body(page.template, translate)
        pages.append(entry)
    # The release this index was generated for. The body text is extracted
    # from the templates by this script, which is deliberately not part of
    # the deployed bundle, so a running service cannot re-derive it to check.
    # What it can do is compare this stamp against the version it is itself
    # running: an index built for an earlier release is one whose page text
    # was written before the copy currently on screen.
    document: dict[str, object] = {
        "version": 1,
        "builtFor": __version__,
        "pages": pages,
    }
    if locale != DEFAULT_LOCALE:
        document = {
            "version": 1,
            "builtFor": __version__,
            "locale": locale,
            "pages": pages,
        }
    return json.dumps(document, ensure_ascii=True, indent=2) + "\n"


def render_admin(locale: str = DEFAULT_LOCALE) -> str:
    """The operator area's index for one language, complete rather than an overlay.

    Complete because it is read by one authorised request on a page that has
    already fetched the public index: a second round trip for an overlay would
    buy nothing. Each index already contains the selected document translations.
    """
    translate = Translator(locale)
    pages = [
        {
            "path": page.path,
            "title": _translated(page.title_key, page.title, translate),
            "summary": _translated(page.summary_key, page.summary, translate),
            "body": _body(page.template, translate),
        }
        for page in ADMIN_SEARCH_PAGES
    ]
    document: dict[str, object] = {
        "version": 1,
        "builtFor": __version__,
        "scope": "admin",
        "pages": pages,
    }
    if locale != DEFAULT_LOCALE:
        document["locale"] = locale
    return json.dumps(document, ensure_ascii=True, indent=2) + "\n"


def admin_output_for(locale: str) -> Path:
    """Where one language's operator index is written.

    The names come from the application's own table rather than a second copy
    of the rule, so what is built is what the operator area will look for.
    """
    return ADMIN_OUTPUT_DIR / ADMIN_INDEX_FILES[locale]


def output_for(locale: str) -> Path:
    """Where one language's index is written."""
    if locale == DEFAULT_LOCALE:
        return OUTPUT
    return STATIC / f"search-index.{locale}.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="fail when the checked-in index differs"
    )
    arguments = parser.parse_args(argv)
    failed = False
    ADMIN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    targets = [
        (output_for(locale), render(locale)) for locale in SUPPORTED_LOCALES
    ] + [
        (admin_output_for(locale), render_admin(locale))
        for locale in SUPPORTED_LOCALES
    ]
    for target, expected in targets:
        if arguments.check:
            if not target.is_file() or target.read_text(encoding="utf-8") != expected:
                print(
                    f"The search index {target.name} is not the current "
                    "release index.",
                    file=sys.stderr,
                )
                failed = True
            continue
        target.write_text(expected, encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
