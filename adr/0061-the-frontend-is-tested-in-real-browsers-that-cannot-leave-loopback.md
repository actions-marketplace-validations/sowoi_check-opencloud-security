# ADR 0061: The frontend is tested in real browsers that cannot leave loopback

- Status: Proposed
- Date: 2026-09-16
- Extends: ADR 0060 (the `playwright` record it requires)

## Context

The web application's tests drive the ASGI app through the Starlette test
client. That proves the server renders the right markup, but nothing in the
suite ever executed it: the nineteen scripts in `frontend/static/js/`, the
stylesheet and the Content-Security-Policy were untested outside a person's
own browser. The first browser run found three shipped defects the existing
tests could not see:

- the landing form's `pattern` is compiled by browsers with the `v` flag,
  under which `[A-Za-z0-9._~-]` is invalid, so client-side validation was
  silently off in WebKit and Chromium;
- a remediation naming `OC_PASSWORD_POLICY_MIN_UPPERCASE_CHARACTERS` has no
  break opportunity, and the findings grid's implicit `auto` column pushed
  `/catalogue` 319 pixels past a phone screen;
- `.filter-status { display: flex }` outranked `[hidden]`, so an empty
  "showing only" sentence with its "show all" link stood under every report.

Agents working on the frontend also had no way to look at the running app
beyond screenshots from a one-off script.

A browser is a large piece of third-party software that talks to the network
on its own. AGENTS.md ("Third parties") keeps the project away from Google,
Meta and Twitter/X in tooling as well as in the product, and the Chromium
builds Playwright downloads are Google's Chrome for Testing.

## Decision

**Browser tests use Playwright's Python package** (`playwright`, test
dependency group, record `security/dependencies/playwright.yml`) with our own
fixtures in `tests/browser_support.py` rather than `pytest-playwright`.
`tests/test_webapp_browser_ux.py` covers pages and progressive enhancements,
`tests/test_webapp_browser_e2e.py` the visitor's journeys. The application,
an in-process stand-in for the ARQ worker and fake OpenCloud instances run in
one background thread; expectations come from the same application's JSON
API.

**The engines are WebKit and Firefox, never Chromium.** WebKit is the default
(`PLAYWRIGHT_BROWSER`), Firefox the second engine in CI; the fixture refuses
`chromium`. Browser builds come from Microsoft's mirror via
`playwright install`.

**No browser can leave loopback.** Every browser - in the tests and in the
MCP server - is launched behind a proxy that does not exist
(`http://127.0.0.1:9`) with only `127.0.0.1`, `localhost` and `[::1]`
bypassing it. The tests additionally fail on any request, console error, page
error or `securitypolicyviolation` event.

**Missing tooling skips locally and fails in CI.** Without the package or
the browser build the modules skip, so the plugin suite still runs anywhere;
`.github/workflows/browser-tests.yml` sets `PLAYWRIGHT_TESTS_REQUIRED=1` and
runs both engines. The main test job installs the package but no browser.

**Agents get the Playwright MCP server from the same package.** `.mcp.json`
starts `uv run --group test playwright mcp` with
`.claude/playwright-mcp.json`: WebKit, isolated profile, headless, the dead
proxy, loopback origins only, output in the ignored `.playwright-mcp/`.
No Node.js installation and no npm package are involved.

## Consequences

- A frontend change is checked by what a browser does with it: CSP
  cleanliness, no request off the machine, no sideways scrolling at 390
  pixels, nothing marked `hidden` still rendered, keyboard and no-JavaScript
  paths, exports, waivers, filters and the waiting page's hand-over.
- Browser tests need a one-time `uv run playwright install webkit` (and
  `firefox` for the second engine) locally. On macOS 27 Playwright's Firefox
  155 build does not start ("Could not find profile folder"); WebKit does.
- Chromium-only behaviour is not covered. A defect that only Chrome shows
  will be found by people, not by this suite.
- The MCP server is bound to the reviewed `playwright` version; upgrading the
  package upgrades both, under the same record.

## Alternatives considered

**`@playwright/mcp` through npx.** Needs a Node.js installation and pulls a
second, pre-release `playwright-core` nobody reviewed, while the wheel
already contains the same server.

**Chromium as the default engine.** It is the most common browser, but its
builds are Google's; WebKit and Firefox exercise the same standards without
putting a Google binary into the toolchain.

**`pytest-playwright`.** Fixtures only; forty lines of our own replace it
and avoid three more packages.

**Selenium or a Node test runner.** More moving parts (drivers, a second
toolchain and lockfile) for tests that must share the Python fake instance
and worker.

**Relying on network restrictions in the browser alone** (`allowedOrigins`,
request routing). Playwright documents them as not a security boundary and
they do not cover the engine's own requests; the dead proxy does.
