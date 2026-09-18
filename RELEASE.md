## check-opencloud-security 1.25.2

### Added

- The Docker setup wizard moves while it works, in the four places where
  motion tells the operator something the static page could not. Section
  headings sweep into view, the step counter is a single-line gauge redrawn
  in place rather than a new bar per section, the wait for the started stack
  to answer spins and then morphs into a tick or a cross, and the summary is
  drawn as one bordered card per group. The look is borrowed from
  [ratatui](https://ratatui.rs)'s throbber, LineGauge and Block widgets; the
  wizard still depends on nothing but the standard library.

  All of it is gated on the same check that gates colour - no terminal,
  `NO_COLOR`, `FORCE_COLOR`, `TERM=dumb` or a captured run prints exactly the
  plain text it printed before, with no escape and no carriage return. A card
  narrows its label column to fit an eighty column terminal and falls back to
  the plain list in a pane too narrow for one.

### Changed

- `specs.md` states the no-JavaScript promise as clause X-20: a page read
  without a script works with plain forms and links, and a control only a
  script can make work stays hidden until the script reveals it. Clause C-8
  no longer asks for a `RELEASE.md` entry when a setting is added - the
  release workflow writes that file (ADR 0048).

### Security

- **The Docker setup wizard no longer writes credentials through a symbolic
  link.** A link left where `.env` belongs - even a dangling one, which did
  not count as an existing file and so raised no overwrite question - made
  the wizard create the link's target and write every generated secret into
  it. The wizard now refuses to write when the compose file or `.env` is a
  link, whatever `--force` says, and opens every owner-only file (`.env`,
  the nginx admin secret header, credential backups) with `O_NOFOLLOW`.
  Affected anyone who ran `setup-wizard.py` from 1.9.0 to 1.25.1 in a
  directory somebody else could write to.

### Fixed

- A report page read without JavaScript no longer shows controls that only
  a script can make work: the configuration-fragment picker and the copy
  buttons were rendered `hidden`, but their `display` rules outranked the
  attribute. New browser tests (`tests/test_webapp_browser_enhancements.py`)
  now drive the remembered form settings, the fragment picker, the share
  buttons, the rescan countdown and the expiry warning.
- The below-the-fold reveal and the site's own 404 page now have browser
  tests too (`tests/test_webapp_browser_ux.py`): blocks arrive as a reader
  scrolls, a jump to the end sweeps up every block it carried past, a page
  read without JavaScript hides nothing, and a mistyped address gets a 404
  page that runs clean under the CSP with a way home.
- The waiver search on the landing page no longer makes iOS Safari zoom the
  page when it is tapped: on a phone it is now set at 16 pixels, the size
  below which Safari zooms into a focused field. New phone tests
  (`tests/test_webapp_browser_mobile.py`) drive the menu, a scan, target
  sizes and field sizes by touch on a 390-pixel screen.
- The operator's area and the API documentation pages now have browser
  tests (`tests/test_webapp_browser_operator.py`): the admin pages run clean
  under their CSP, `admin.js` fills every tile from `/admin/state`, a
  request without the outpost's headers gets the ordinary 404, and Swagger
  UI and ReDoc render from the vendored bundles with nothing fetched from
  outside.
- The security headers are now tested on every kind of response a stranger
  can reach (`tests/test_webapp_security_headers.py`), not only the landing
  page: errors, the JSON API, every export, the badge, static files,
  redirects and the operator's area. Nothing tied to a scan's uuid may be
  stored by a cache, and the documentation pages' relaxed policy applies to
  exactly `/docs` and `/redoc`, never a neighbouring address.
- `opencloud_local_scan.scan()` raises `ScanError` for an address it cannot
  parse - an unclosed IPv6 bracket or a port outside 0-65535 - instead of
  letting urllib's `ValueError` escape. The plugin already reported these as
  UNKNOWN; a direct caller of the library now gets the exception it is
  promised. New robustness tests (`tests/test_scanner_robustness.py`) cover
  malformed, empty, binary and failing status answers, an oversized body,
  capabilities of the wrong shape, a target that never answers and a
  redirect loop.
- The Docker setup wizard checks the answers it reads back from its
  answers file the way it checks a typed answer: a value outside a
  question's choices, one its validation refuses, or one carrying a control
  character is dropped. A newline in an edited file could otherwise rewrite
  `docker-compose.yml` around it. A `.env` that is not UTF-8 now stops the
  run with a sentence instead of a traceback, and without regenerating the
  credentials a running deployment depends on. New tests
  (`tests/test_docker_wizard_hardening.py`) cover links, edited and
  unreadable files, input that ends mid-walk, refused answers and masked
  credentials.
