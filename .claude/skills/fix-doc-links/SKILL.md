---
name: fix-doc-links
description: Find and repair broken OpenCloud documentation links in check-opencloud-security - run check_documentation_links.py, locate each dead URL's new address on the official OpenCloud sites, update every occurrence including the hardening catalogue, and regenerate the documentation. Use when the link check fails or when asked to fix documentation links.
---

# Fix documentation links

`scripts/check_documentation_links.py` checks only OpenCloud's own hosts,
across every text file **and** the imported hardening catalogue (a URL split
across string literals is invisible to grep).

## 1. Find broken links

```bash
python scripts/check_documentation_links.py --warn-only
```

Run it in the background if it takes long. Collect each broken URL, its status
or error, and where it is referenced. A temporary redirect is not broken. A
single transport error may be transient - re-run once before treating it as
dead.

## 2. Find the new address

For each dead link, in this order:

1. The same path on the current documentation site - OpenCloud often moves
   pages between `docs/admin/...` and `docs/dev/...`, or renames a service
   directory.
2. The OpenCloud documentation site's search, or the documentation source
   repository on GitHub (git history of the moved file).
3. For a source-code link (e.g. `services/frontend/pkg/revaconfig/config.go`),
   the same file on the default branch; prefer a link pinned to a tag or
   commit if the surrounding references are pinned.

Use WebFetch to confirm the replacement page **exists and still says what the
reference is cited for** - a page that answers 200 but describes something else
is not a fix. `docs.opencloud.eu` is a single-page app: confirm the content,
not just the status.

If no replacement can be found, do not guess. Report it and ask whether to
remove the link or point to the nearest parent page.

## 3. Update every occurrence

```bash
grep -rn --exclude-dir=.git --exclude-dir=__pycache__ '<old url or distinctive path fragment>' .
```

- Prefer changing a shared constant (`DOCS_*` in
  `opencloud_local_scan/hardening.py`) over individual strings.
- Search for a fragment too, because long URLs may be split across literals.
- Skip generated files (`frontend/templates/docs/`, `frontend/static/search-index*.json`)
  - they are regenerated below.
- Never edit an accepted ADR's decision text; a link fix inside an ADR is
  acceptable only as a link fix.

## 4. Regenerate and verify

```bash
python scripts/build_frontend_documentation.py
python scripts/build_search_index.py
python scripts/check_documentation_links.py        # must now pass for the fixed links
uv run pytest tests/test_hardening.py tests/test_webapp_catalogue_links.py -q
```

Add a `### Documentation` entry under `## [Unreleased]` in `CHANGELOG.md`
listing which references moved. Report old → new for each link, and any link
left unresolved.
