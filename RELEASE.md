## check-opencloud-security 1.31.1

### Changed

- **The coverage warning's alert line is now covered by mutation testing.**
  `tests/test_coverage_regression.py` drives `_apply_baseline` in process but
  was missing from the mutmut selection, so eleven mutants of the branch that
  lifts an OK to WARNING when a measured check turns inconclusive survived.
  It is now listed, and its test asserts the whole alert line: three of those
  mutants left `OK: ` inside the WARNING message without a test noticing.

### Fixed

- **The web report no longer offers "What gets you to A+" under an A+.** When
  no step in the remediation plan raises the grade, because the instance
  already has the top grade or something no setting can change holds it down,
  the plan is headed "Still worth fixing, the grade stays A+" (or whichever
  grade it holds) instead.
  This applies to the dashboard, its contents list, and the PDF and HTML
  exports, in all four languages.
- **`check-opencloud-scanner fleet` lists waiver deadlines in the order they
  end.** Deadlines were sorted by their text, so a waiver written with a
  `+02:00` offset could be listed after one that ends later in UTC.
- **The fleet summary's "Not covered" count counts each host once.** A host
  whose last scan failed long enough ago to be stale was counted twice.
- **The remediation plan no longer fails on a result document whose
  `ratingExplanation.base` is `null`.** The update step's detail is then left
  empty, instead of `remediation_plan()` raising.

### Security

- **An empty listen address no longer counts as loopback for the scan
  service.** Binding `""` listens on every interface, but the check that
  demands a token for anything but loopback let it through. The command line,
  `COS_SERVICE_LISTEN` and the configuration file all fall back to
  `127.0.0.1` when empty, so only a program calling `build_server()` or
  `serve()` with `listen=""` could reach it.
- **The container images install the dependencies `uv.lock` pins, with their
  hashes.** Both `docker/Dockerfile` and `docker/Dockerfile.web` resolved
  their dependencies from PyPI at build time, so an image could ship versions
  that CI, `pip-audit` and the SBOM never saw.
