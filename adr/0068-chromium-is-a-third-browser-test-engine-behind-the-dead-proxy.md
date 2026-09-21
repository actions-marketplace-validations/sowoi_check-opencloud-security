# ADR 0068: Chromium is a third browser test engine, behind the dead proxy

- Status: Proposed
- Date: 2026-09-18
- Supersedes: ADR 0061 (its "never Chromium" engine choice only)

## Context

ADR 0061 put the frontend under real browsers and chose WebKit and Firefox,
refusing Chromium because Playwright's Chromium builds are Google's (Chrome
for Testing). It named the cost itself: "Chromium-only behaviour is not
covered. A defect that only Chrome shows will be found by people, not by
this suite."

Chrome, Edge, Brave, Opera and most Android browsers render with Blink, so
the engine the suite leaves out is the one most visitors use. The first
browser run already showed engines disagreeing: the landing form's
`pattern` was invalid under the `v` flag in WebKit *and Chromium*. Two
engines out of three is a real gap, not a formality.

AGENTS.md ("Third parties") forbids anything in the project that *talks to*
Google. A browser that runs behind the dead proxy of ADR 0061 talks to
nobody: every request that is not to loopback goes to a port where nothing
listens. What remained of the objection is provenance - a Google-built
binary in the test toolchain - and the maintainer has decided that the
coverage is worth that.

## Decision

**Playwright's Chromium is a third engine for the browser tests.**
`tests/browser_support.py` accepts `PLAYWRIGHT_BROWSER=chromium` alongside
`webkit` and `firefox`, and `.github/workflows/browser-tests.yml` runs all
three in its matrix. The build is installed with `playwright install
chromium` from Microsoft's Playwright mirror, as the other two are.

**It gets exactly the confinement the others have.** Chromium is launched
behind the same dead proxy (`http://127.0.0.1:9`, loopback bypassed only),
and the same watch fails a test on any request that leaves loopback, any
console or page error and any CSP violation. Chromium's own background
traffic - component updates, safe browsing, metrics - has nowhere to go.

**WebKit stays the default, and nothing else changes.** A plain `uv run
pytest` still drives WebKit; Chromium runs where it is asked for. The
Playwright MCP server of ADR 0061 stays on WebKit. The product rule is
untouched: no page, deployment or workflow of this project may contact
Google, and this decision gives no precedent for one that does.

**The rest of ADR 0061 stands** - Playwright's Python package, our own
fixtures, the dead proxy, skip-locally-fail-in-CI, and the MCP server.

## Consequences

- Blink is covered: a layout, script or CSP defect that only Chrome-family
  browsers show now fails CI instead of reaching visitors.
- A Google-built binary is part of the CI toolchain and of any developer
  machine that installs it. It is fetched from Microsoft's mirror and never
  reaches the network while it runs, but it is there, and AGENTS.md and
  CLAUDE.md say so rather than claiming "never Chromium".
- The browser-tests workflow runs a third job; its time and runner cost grow
  by about half.
- Chromium joins WebKit as an engine that starts on macOS 27, where
  Playwright's Firefox build does not (ADR 0061), so Blink behaviour can be
  checked locally too.

## Alternatives considered

**Keep ADR 0061 as it was.** No Google-built binary anywhere, but the
engine most visitors use stays untested; the maintainer judged the gap the
larger risk.

**A Chromium built by a Linux distribution** (Debian's package in a CI
container, launched through `executable_path`). No Google-built binary, but
another container image and install path to maintain, a build that lags
upstream Blink, and no way to run it on a developer's Mac.

**Manual checks in a Chrome-family browser before a release.** Cheap, but
exactly the "found by people, not by this suite" ADR 0061 already accepted,
and nobody's memory is a regression test.
