## check-opencloud-security 1.27.2

### Added

- **Property-based tests for the parsers that read outside text.**
  `tests/test_properties.py` uses Hypothesis, a new test-only dependency
  (reviewed in `security/dependencies/hypothesis.yml`), to generate inputs
  for version parsing and comparison, advisory ranges, the
  Strict-Transport-Security and Content-Security-Policy readers, the web
  application's SSRF guard (private literals, IPv4-mapped and 6to4
  addresses, arbitrary input) and the `;`-joined configuration lists.
- **The output documents' key names are pinned.**
  `tests/test_output_shape.py` fails when a top-level key of the scan result
  or of the plugin's `--format json` / webhook payload is renamed, added or
  dropped, or when a key breaks the camelCase (result) / snake_case (plugin)
  convention, so a breaking rename cannot land unnoticed.
- **The advisory database also reads OpenCloud's repository advisories.**
  OpenCloud publishes some advisories only on its GitHub repository, where
  OSV never sees them. The daily refresh (`scripts/update_vulnerability_db.py`,
  new `--repository-url`) and the web application's refresh (new
  `COS_WEB_ADVISORY_REPOSITORY_URL`, `off` to skip) now add those
  advisories. Their version ranges are read strictly: an advisory fixed on two
  release lines becomes one range per line, and prose ranges are never
  guessed at. OSV stays the primary source, and if the repository feed can't
  be read, OSV's answer is kept.
  [ADR 0071](adr/0071-repository-advisories-are-a-second-advisory-source.md).

### Changed

- **Polished recent German, Spanish and French web translations.** Fixed mixed
  forms of address and several literal or awkward phrases in the operator
  update messages, scan facts and coverage explanations.

### Security

- **GHSA-gf4p-7p27-26w7 (CVE-2026-57500, "Access to internal metadata") is
  now reported.** OpenCloud published it only as a repository advisory, which
  never reaches OSV, the one feed the advisory database was refreshed from - so
  every release before 4.0.8, and 5.0.0 up to 7.2.0, was rated as free of
  known advisories. The bundled database now carries it, affecting releases
  from 1.0.0 up to 4.0.8 and from 4.1.0 up to (but not including) 7.2.0.
