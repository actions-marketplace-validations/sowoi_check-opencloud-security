"""
The fixed public-page manifest used to build the browser search index.

The English title and summary are the source, and each page also names the
catalogue identifiers for the same two strings, so a release can build an
index a German reader recognises without this manifest growing a copy of
every translation. What may *not* appear here is a page reached with a scan
uuid: the list is the structural reason a result cannot enter search, so it
is written out by hand rather than discovered.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from .documentation import DOCUMENTATION_PAGES, OPERATOR_DOCUMENTATION_PAGES
from .i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES


@dataclass(frozen=True)
class SearchPage:
    """One public page whose authored text may enter the static index."""

    path: str
    title: str
    summary: str
    template: str
    #: The catalogue identifier for the title, when there is one.
    title_key: str = ""
    #: The catalogue identifier for the summary, when there is one.
    summary_key: str = ""


SEARCH_PAGES: tuple[SearchPage, ...] = (
    SearchPage(
        "/",
        "Scan an OpenCloud instance",
        "Run a public security scan against an OpenCloud instance.",
        "index.html",
        "search.page.index.title",
        "search.page.index.summary",
    ),
    SearchPage(
        "/how-it-works",
        "How the scanner works",
        "What the scanner measures, what it cannot see, and how results are handled.",
        "how-it-works.html",
        "search.page.how.title",
        "search.page.how.summary",
    ),
    SearchPage(
        "/grades",
        "What the grades mean",
        "The A+ to F rating scale and the fixes that improve each grade.",
        "grades.html",
        "search.page.grades.title",
        "search.page.grades.summary",
    ),
    SearchPage(
        "/catalogue",
        "What the scanner checks",
        "Every hardening flag, header and TLS check the scanner runs, and every known advisory.",
        "catalogue.html",
        "search.page.catalogue.title",
        "search.page.catalogue.summary",
    ),
    SearchPage(
        "/documentation",
        "CLI documentation",
        "Command-line quick start, configuration, monitoring, and deployment guides.",
        "documentation.html",
        "search.page.documentation.title",
        "search.page.documentation.summary",
    ),
    *(
        SearchPage(
            f"/documentation/{document.slug}",
            document.title,
            document.description,
            f"docs/{document.slug}.html",
            f"docs.{document.slug}.title",
            f"docs.{document.slug}.description",
        )
        for document in DOCUMENTATION_PAGES
    ),
    SearchPage(
        "/api",
        "API",
        "Submit scans, poll results, export reports, and drive the service from an agent over OpenAPI, Arazzo or MCP.",
        "api.html",
        "search.page.api.title",
        "search.page.api.summary",
    ),
    SearchPage(
        "/privacy",
        "Privacy",
        "Result retention, request logging, rate limits, and third-party policy.",
        "privacy.html",
        "search.page.privacy.title",
        "search.page.privacy.summary",
    ),
    SearchPage(
        "/about",
        "About this project",
        "Why this independent OpenCloud security scanner exists.",
        "about.html",
        "search.page.about.title",
        "search.page.about.summary",
    ),
)


#: The operator area's own pages, indexed separately from everything above.
#:
#: These are *not* public pages, so they are never written into
#: ``frontend/static``: the built index for them lands in ``webapp/data``,
#: which nothing mounts, and it is served only by the authorised route in the
#: area itself. An operator searching should find the configuration tab and
#: the operations notes; a stranger doing the same must not learn that either
#: exists. That separation is the whole reason this is a second manifest
#: rather than a flag on the entries above - a page in ``SEARCH_PAGES`` is
#: public by construction, and nothing can put an operator page there by
#: accident.
ADMIN_SEARCH_PAGES: tuple[SearchPage, ...] = (
    SearchPage(
        "/admin",
        "Operator area",
        "What this deployment is doing, what it knows, and the refreshes the worker runs.",
        "admin.html",
        "admin.title",
        "admin.lede",
    ),
    SearchPage(
        "/admin/configuration",
        "Configuration",
        "Every COS_WEB_* variable this service reads, and the value it is running with.",
        "admin-configuration.html",
        "admin.config.title",
        "admin.config.lede",
    ),
    SearchPage(
        "/admin/rules",
        "Rules in force",
        "How a grade is decided, and every rule this deployment enforces against a request.",
        "admin-rules.html",
        "admin.rules.title",
        "admin.rules.lede",
    ),
    *(
        # English only and no catalogue keys, exactly as the tab strip renders
        # them: these two are the repository's own documents.
        SearchPage(
            f"/admin/docs/{document.slug}",
            document.title,
            document.description,
            f"admin-docs/{document.slug}.html",
        )
        for document in OPERATOR_DOCUMENTATION_PAGES
    ),
)


#: Where the built operator indexes live, inside the package and outside
#: anything the application mounts.
ADMIN_INDEX_DIR = Path(__file__).resolve().parent / "data"

#: The one file each language's operator index is written to and read from.
#: A request *selects* an entry from this table and can never contribute a
#: character to a file name, which is what keeps a hand-written language
#: cookie a missing key rather than a path this process would go and read.
ADMIN_INDEX_FILES: dict[str, str] = {
    locale: (
        "admin-search-index.json"
        if locale == DEFAULT_LOCALE
        else f"admin-search-index.{locale}.json"
    )
    for locale in SUPPORTED_LOCALES
}


@lru_cache(maxsize=len(SUPPORTED_LOCALES))
def admin_search_document(locale: str) -> dict[str, Any] | None:
    """The operator index for one language, or ``None`` when it was not built.

    Cached because the file is written at release time and cannot change while
    the process runs. ``None`` rather than an exception: a deployment whose
    bundle predates this index should still answer search with the public
    pages instead of failing the request.
    """
    name = ADMIN_INDEX_FILES.get(locale) or ADMIN_INDEX_FILES[DEFAULT_LOCALE]
    try:
        return json.loads((ADMIN_INDEX_DIR / name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
