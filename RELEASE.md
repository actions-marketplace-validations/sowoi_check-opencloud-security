## check-opencloud-security 1.29.2

### Fixed

- **`/llms.txt` and `/llms-full.txt` described an older version of the
  service.** They are the map an agent reads before deciding what this
  service can do, and four of their facts had fallen behind the code:
  `/mcp` was described as six tools and six prompts where it registers seven
  of each, `compare_scans` was missing from the tool list in the long form,
  the export formats omitted `html`, and the endpoint summary never mentioned
  `GET /api/scans/{uuid}/badge.svg`. An agent that trusts the map would have
  concluded the badge and the HTML export do not exist. All four now match
  what `webapp/mcp_server.py`, `wf.EXPORT_FORMATS` and `webapp/openapi.py`
  actually serve.

- **A page's `<lastmod>` in `sitemap.xml` now moves only when the page really
  changed.** The date came from the modification time of the template that
  renders the page, and a checkout, a container build and an unpacked release
  tarball all write every template at once - so every public page claimed to
  have changed on release day, and a crawler told that everything changed
  learns nothing from the file. Each public page's date is now recorded next
  to a digest of its template in `webapp/data/page-revisions.json`, and
  `scripts/update_page_revisions.py` moves a date only when that digest does.
  A page the record has never seen, or one edited since it was written, still
  falls back to the modification time rather than publishing a date that is
  no longer true. CI checks the record with `--check`, as it does for the
  generated documentation.

- **The German, Spanish and French pages no longer drop names the English
  text uses to say what this is.** The translated "About" paragraph called the
  plugin a generic monitoring plugin, so a reader of those pages never learned
  it plugs into Nagios and Icinga, and it also lost the English sentence's
  point that running it yourself has no rate limit or queue. The German and
  French descriptions of the method page said "what the scanner checks"
  without naming an OpenCloud instance, and the Spanish search summary for the
  API page dropped OpenAPI, Arazzo and MCP - the three things somebody
  searching for that page is searching for. All four strings now carry the
  names again; the search index is rebuilt with them.
