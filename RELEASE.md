## check-opencloud-security 1.25.3

### Added

- The `/check-changelog-docs` skill checks that every new `Added` or
  `Changed` entry under `[Unreleased]` is documented where AGENTS.md requires
  it - the README option table, the example YAML, the `docs/` guides in all
  four languages, `docs/webapp.md`, the guide index and the generated
  `/documentation` pages - and reports each gap as a concrete action. A new
  Claude Code hook stops the first `git commit` that adds such entries and
  asks for the check; retrying the same commit goes through.

- Manual mutation testing for contributors: the `/mutation-test` skill runs
  mutmut through the read-only `mutation-tester` agent on chosen plugin or
  scanner functions and sorts every surviving mutant into a real test gap,
  unreachable code or noise. mutmut 3.8.0 is a new dependency in its own
  `mutation` group - never installed by CI or a plain `uv sync`, never run in
  CI - reviewed and approved in `security/dependencies/mutmut.yml`.

- The browser tests now also run in Chromium, the engine behind Chrome,
  Edge and most Android browsers, as a third job in the browser-tests
  workflow ([ADR 0068](adr/0068-chromium-is-a-third-browser-test-engine-behind-the-dead-proxy.md),
  superseding ADR 0061's WebKit-and-Firefox-only rule). Chromium is
  Playwright's build, which is Google's, and runs behind the same dead proxy
  and request watch as the other engines; WebKit stays the default. The
  workflow now runs every `tests/test_webapp_browser_*.py` file, including
  the enhancements, phone and operator tests it had been leaving out.
  Chromium's first run showed ReDoc asking for Redocly's logo from its CDN;
  the `/redoc` page's policy already blocks it, and a test now keeps it that
  way.

### Fixed

- The end-of-life alert no longer shows a double space ("The 2.x  release
  line") when the scan result names a release line but no release type.
- `--baseline` and `--warn-on-new` are now tested in-process: suppressing an
  unchanged problem, keeping new findings, worse ratings and OK runs as they
  are, leaving waived measures out of the baseline, and a baseline that
  cannot be written. The rating messages (end of life, thresholds, OK and
  UNKNOWN) are pinned exactly. A mutation-testing trial run found both gaps.
- `check_vulnerabilities` is now tested as a whole, in-process: a scan with
  known vulnerabilities and a good rating, the exact hardening and update
  alert lines, what the baseline records with and without
  `--check-hardening`, perfdata, the self-update note, extra-check
  truncation and the payload behind `--format` and the webhook. A
  `/mutation-test` run of the rating, baseline and check functions now
  leaves only 3 equivalent mutants alive (was 108).
- The browser tests for the below-the-fold reveal no longer time out in
  Firefox on CI. They ran the longest page with the blurred fade switched
  on, which starved headless Firefox until even the next page load timed
  out; they now use reduced motion like every other browser test, which
  still exercises the same hiding and revealing, and the motion itself
  stays covered on the landing page.

### Documentation

- `docker/docker-compose.yml` now shows every web setting it had left out:
  the operator's area (`COS_WEB_ADMIN_*`), `COS_WEB_AUDIT_LOG_ROTATION` and
  `COS_WEB_RATE_LIMIT_SALT` as commented examples, and why
  `COS_WEB_FRONTEND_DIR` stays unset. The example configuration shows
  `scanner.proxy` and `releases.proxy`, which override the top-level `proxy`.

### Security

- **Scan targets and redirect hops in deprecated IPv6 site-local space are refused.**
  The web service's SSRF guard let the deprecated site-local range (RFC 3879) through because no
  `ipaddress` private flag covers it, so a name resolving there - or a redirect
  to it - could reach a network that still routes site-local addresses.

- **Webhooks to deprecated IPv6 site-local addresses are refused.** The
  plugin's webhook guard had the same site-local gap as the web service.
