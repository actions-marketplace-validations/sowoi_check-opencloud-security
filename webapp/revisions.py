"""
When a public page last really changed, rather than when it was deployed.

``sitemap.xml`` carries a ``<lastmod>`` per page, and the honest source for
it used to look like the template's modification time. It is not one: a
checkout, a container build and an unpacked release tarball all write every
template at once, so every page claimed to have changed on release day even
when its text had not moved in months. A crawler that is told everything
changed learns nothing, and eventually stops believing the file.

So the date is recorded next to a digest of the template it belongs to, in
`data/page-revisions.json`, and `scripts/update_page_revisions.py` moves a
date only when that digest does. The record travels with the release, which
is what makes it survive the checkout that destroyed the modification time.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from functools import lru_cache
from pathlib import Path

#: Where the checked-in record lives. Inside the package, because it ships
#: with the web bundle and is read at runtime like any other data file.
REVISIONS_FILE = Path(__file__).resolve().parent / "data" / "page-revisions.json"


def digest_of(template: Path) -> str:
    """The digest a record is keyed by: the template's bytes, nothing else."""
    return hashlib.sha256(template.read_bytes()).hexdigest()


def load(path: Path | None = None) -> dict[str, dict[str, str]]:
    """The recorded revisions, or an empty record when there is no file."""
    source = REVISIONS_FILE if path is None else path
    try:
        document = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    pages = document.get("pages")
    return pages if isinstance(pages, dict) else {}


@lru_cache(maxsize=1)
def _records() -> dict[str, dict[str, str]]:
    """The record, read once per process - it changes only on release."""
    return load()


def recorded_date(template: Path, name: str) -> date | None:
    """
    The recorded date for this template, when the record still describes it.

    ``None`` for a template the record has never seen or one that has been
    edited since - a stale date is worse than a fallback, because it says
    the page did not change when it did.
    """
    entry = _records().get(name)
    if not entry:
        return None
    try:
        if entry.get("digest") != digest_of(template):
            return None
        return date.fromisoformat(str(entry.get("lastmod")))
    except (OSError, ValueError):
        return None
