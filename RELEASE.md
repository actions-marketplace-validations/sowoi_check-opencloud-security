## check-opencloud-security 1.23.3

### Added

- **An operator can search the operator area.** While the sign-in lasts,
  `/search` also answers from the area's own pages - the overview, the
  configuration and rules tabs and the two operator documents - and marks
  those results as the operator area's. The index behind them is built into
  the package rather than `frontend/static`, is served only by an authorised
  route under `/admin`, and is sent `no-store` so that signing out ends
  access to it immediately. Everybody else gets the public index alone and no
  indication that another one exists.

### Fixed

- **The operator documents no longer carry broken images.** The repository's
  Markdown points at files beside it, which resolve to nothing once a page is
  served from `/admin/docs/`. The architecture diagram is now served from this
  origin, as `img-src 'self'` requires; the two interface screenshots are
  megabytes each and show the page the reader is already on, so they become
  links to the repository rather than weight in the bundle.
- **The two generated operator documents now look like the rest of the area.**
  `Architecture` and `Operations` never loaded `admin.css`, so the tab strip
  above them rendered as bare links and neither page carried the signed-in
  band or the ruled heading the other tabs have.

### Changed

- **The operator index is chosen from a table rather than named by a request.**
  The file each language's operator search index lives in is now a fixed entry
  in one table in `webapp/search.py`, which both the build script and the
  request path read. The language a request asks for could already only be one
  of the four this frontend has - a cookie or `Accept-Language` is reduced to a
  supported code or to nothing before anything else sees it - so no traversal
  was reachable, but the name was still assembled from that value, which is a
  shape static analysis rightly objects to and one refactor away from being
  true. A cookie the visitor wrote by hand now selects an entry or misses the
  table and gets English.

- **The agent guide is now part of the API page.** `/ai` was a tab of its own
  next to `/api`, which asked a reader wiring up software to guess whether a
  curl call and an MCP endpoint were documented in the same place. Discovery,
  WebMCP, client configuration and the rules for agents are now sections of
  `/api`, which keeps its name. `/ai` redirects there permanently, and the
  discovery document's `documentation` key follows it.

- **Reference data re-read and the generated documentation rebuilt.** The
  OpenCloud release schedule is unchanged (production 7.2.4, rolling 8.0.0)
  and the advisory database brought no new entries, so this release carries
  the same ratings as the last one. The bundled documentation pages and the
  four search indexes are regenerated against the new version.
