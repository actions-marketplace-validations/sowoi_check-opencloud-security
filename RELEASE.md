## check-opencloud-security 1.24.1

### Added

- **The frontend is tested in a real browser.** `tests/test_webapp_browser_ux.py`
  and `tests/test_webapp_browser_e2e.py` drive the web application in WebKit
  (and Firefox in CI, `.github/workflows/browser-tests.yml`) through
  Playwright: every public page runs clean under its Content-Security-Policy,
  fits a phone screen and hides what is marked hidden; navigation, theme,
  language, form validation, waiver search, site search and back-to-top
  behave; and a visitor's journeys work from the form to the report - the
  waiting page's hand-over, severity filters, all four exports, waivers,
  keyboard only, without JavaScript and in German. No browser can reach
  anything but loopback, and Chromium is never used because its builds are
  Google's. New test dependency `playwright` has an approved review in
  `security/dependencies/playwright.yml`; see
  [ADR 0061](adr/0061-the-frontend-is-tested-in-real-browsers-that-cannot-leave-loopback.md).
- **Agents can drive the running app through the Playwright MCP server.**
  `.mcp.json` starts the server bundled with the same `playwright` package,
  configured in `.claude/playwright-mcp.json` for WebKit, an isolated
  headless profile and loopback only - no Node.js installation needed.

### Fixed

- **The scan form validates the address in the browser again.** Browsers
  compile the field's `pattern` with the `v` flag, under which the unescaped
  `-` in `[A-Za-z0-9._~-]` is an error, so WebKit and Chromium silently
  skipped client-side validation and sent malformed addresses to the server.
- **The catalogue and reports no longer scroll sideways on phones.** A
  remediation naming a long environment variable had no break opportunity,
  and the findings list grew to fit it - 319 pixels past a 390-pixel screen on
  `/catalogue`.
- **The findings filter note is hidden until a filter is chosen.** A
  `display: flex` rule outranked the `hidden` attribute, so every report showed
  an empty "showing only" line with a "show all" link.

### Changed

- **A new Python dependency needs an approved review first.** Every package in
  `pyproject.toml` and every `uvx` tool in a workflow needs a record in
  `security/dependencies/` that says why it is needed, which tests exercise
  it, what a security review found, and which maintainer approved it.
  `scripts/check_dependencies.py`, run by a new `dependency-policy` job in the
  supply-chain workflow, fails without one. The 33 dependencies already in use
  are listed in `security/dependencies/grandfathered.txt`, which may only
  shrink. The dependency-review action now fails a pull request that
  introduces a known-vulnerable package instead of only commenting, and the
  supply-chain workflow grants its attestation permissions to the one job that
  attests. See
  [ADR 0060](adr/0060-a-new-dependency-is-justified-tested-and-reviewed-first.md).
- **Routine dependency updates get a seven-day stabilization window.**
  Dependabot still raises security updates immediately, while monthly version
  updates wait long enough for a compromised or broken release to be noticed.
  The composite action also invokes its private scanner environment directly
  instead of adding that directory to the rest of the job's executable path.

- **Comparing two scans of different instances is refused.** The `/compare`
  page, the report upload and the MCP tool `compare_scans` used to compare a
  scan of one host with a scan of another and only show a warning. They now
  answer 422 and compare nothing, matching the default of
  `check-opencloud-scanner diff`. A report that names no instance is refused
  the same way. `sameTarget` stays in the answer and is always `true`. See
  [ADR 0059](adr/0059-a-comparison-refuses-two-different-instances.md), which
  supersedes this part of ADR 0029.
### Documentation

- **New German text addresses the reader as "du".** New and reworded strings
  in the German web interface and guides use the informal form instead of
  "Sie". Existing formal strings are listed in `tests/test_webapp_i18n.py`,
  which fails on any other formal string; the list only shrinks as strings
  are converted. The "Die beiden Scans betreffen unterschiedliche Instanzen"
  message already uses the new form.
- **The release skills build a release skeleton and never write a changelog
  entry.** `/patch-release`, `/minor-release` and `/major-release` now make
  exactly the version bump in `pyproject.toml`, a new `uv.lock` and the
  refreshed generated files (release schedule, advisory database, frontend
  documentation, search indexes), and leave `CHANGELOG.md` and `RELEASE.md`
  alone: the release notes are the `[Unreleased]` entries the merged pull
  requests wrote. A new OpenCloud release or advisory found by the refresh is
  reported to the user instead of written down. The version guard now runs
  after the commit, because it reads the committed version, with
  `--labels skip-changelog` so that only its version check applies.
- **`/open-release-pr` checks the changelog before it opens anything.** It
  stops when the `[Unreleased]` section is empty, when the release branch
  changes `RELEASE.md`, or when it changes a released section of
  `CHANGELOG.md`. Entries the release branch adds under `[Unreleased]` are
  allowed and become part of the pull request body, which uses the
  `[Unreleased]` entries verbatim; the skill never edits either file.
- **Claude Code hooks enforce the project's hard rules.** `.claude/settings.json`
  refuses publishing or syncing advisories, merging pull requests, creating
  tags and releases, force-pushing, pushing to `main`, `git reset --hard`,
  aborting a merge and `ruff format`; refuses hand edits to `RELEASE.md`, the
  generated documentation, search indexes, bundled data, the README
  release-schedule block and the embedded wizard blueprints; asks before a
  version change or a literal `__version__`; and refuses inline styles and
  scripts in templates. When the session ends, it runs the fast generator
  `--check` guards for changed sources.
- **A privacy guard keeps real instances, scan output and personal data out
  of commits.** `.claude/hooks/privacy_guard.py` checks staged changes and
  commit messages before `git commit`, the commits a `git push` would send,
  pull request bodies, and, when the session ends, everything staged or not
  yet pushed. It refuses hostnames that look like an instance or scan target,
  public IP addresses, personal e-mail addresses, credentials and scanner or
  plugin output in any format, and asks about any other new hostname. Values
  already on `main` and public references in
  `.claude/hooks/privacy_allowlist.txt` pass.
- **The hooks refuse when they cannot run, and have tests.** A guard that is
  missing, crashes or cannot read its input now refuses the command or edit
  instead of letting it through; the generator checks at the end of a
  session run in the project's environment and report a missing dependency
  as skipped rather than as a stale file; the privacy guard only starts for
  `git` and `gh` commands. `tests/test_claude_hooks.py` covers all of it.
- **The hooks close the gaps a review found.** The Bash guard now applies the
  Edit guard's rules to shell writes (redirects, `tee`, `sed -i`, `cp`, `mv`,
  `rm`), sees commands inside `$(...)`, backticks, `bash -c`, `eval`, braces,
  background jobs and `xargs`, ignores quoted text, heredoc bodies and
  comments, lets `ruff format --check`/`--diff` and redirected `git tag`
  listings through, and reads `git push -o` values correctly. Pushes using
  `--repo` are checked against both the main-branch guard and the privacy
  guard. The privacy
  guard matches values already on `main` as whole tokens only, reads diffs
  without mistaking an added `++ ` line for a file header, checks merge
  commits, checks the branch a push actually sends, reads `git commit -F`
  message files and `gh` `-F`/`--body-file=` bodies (issues too), only widens
  a commit check to the working tree for a real `git add`, `-a`/`-i`/`-o` or
  pathspec, and asks when it cannot read the commits of a push. The session-end
  generator checks treat only a traceback ending in an import error as a
  missing dependency.
- **`/preflight` runs in a read-only `preflight-runner` agent**, so its output
  stays out of the conversation and nothing is changed while it checks.
- **`/patch-release`, `/minor-release` and `/major-release` are now one
  `/release <patch|minor|major>` skill.**
- **German guide pages no longer repeat their title inside the article.** The
  frontend generator removes the source and translated Markdown title before
  rendering the page header; German sources keep their headings and key
  external references in German, and the Spanish agent-client guidance uses
  the formal form of address consistently.
- **French guide sources are now available in the frontend.** Every public
  guide has a matching `docs/fr/` source, generated French template and search
  index entry. Spanish guide pages continue to use the explicit English
  fallback until their own source set is reviewed. See
  [ADR 0062](adr/0062-public-guides-have-french-sources.md).
