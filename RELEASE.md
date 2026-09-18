## check-opencloud-security 1.25.1

### Fixed

- **A release that stopped after its tag is finished by the next run.** The
  release workflow skipped any version whose tag existed, so when v1.25.0 was
  tagged and GitHub then answered an asset upload with HTTP 500, it reached
  PyPI and Docker Hub but never got a GitHub release, and every re-run stayed
  green without doing anything. The workflow now treats a published GitHub
  release as the end of a version: a tagged version without one is rebuilt
  from its tag and released, the release stays a draft until every asset has
  been uploaded (each upload is retried), and the workflow can be started by
  hand. See ADR 0067.
- **A semicolon in a waiver's reason no longer creates a permanent waiver.**
  `temporary_waivers` is a list, and a list in the environment or a
  configuration file is split on `;`, so the reason
  `Firewall change; debugPort:9206 stays open` left a second entry behind,
  which was read as a bare pattern and became a waiver with no deadline and
  no reason. `temporary_waivers` and `--waive-until` now refuse an entry
  without an expiry and a reason instead; a permanent waiver still belongs in
  `--ignore-hardening`.
- **A malformed waiver in the configuration is UNKNOWN, not WARNING.** A
  `temporary_waivers` entry that could not be read ended the plugin in a
  traceback with exit status 1, which a monitoring system reports as WARNING.
  It now answers UNKNOWN with the reason, on every output path - several
  hosts, `--format json` and the other machine formats included, which also
  let a configuration error such as an unreadable secret escape the same way.
  `check-opencloud-scanner` reports it as a usage error.
- **`check-opencloud-scanner diff` explains a hand-edited report instead of
  crashing.** A provenance, coverage or waiver block of the wrong shape - a
  string where an object belongs, a count that is not a number - ended the
  comparison in a traceback. It is now read as missing, the same as in a
  report that predates the block.
- **The browser tests declare the web server they start.** `uvicorn` is
  imported by `tests/browser_support.py` but reached the `test` dependency
  group only as a dependency of `mcp`; it is now listed there itself.
