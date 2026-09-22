## check-opencloud-security 1.30.0

### Documentation

- Listed `tests/test_monitoring_export.py` in the test index, so the
  scheduler-export tests can be found by purpose.

- Clarified German operator messages about wildcard DNS and temporary
  application updates, and replaced the literal TLS introduction with a
  description of the measured values. Added three wording regression cases.

- Clarified configuration-drift explanations in the English, German, Spanish
  and French baseline guides. Older baselines lack fingerprints, so an absent
  drift report does not establish that the configuration is unchanged.
  Added regression cases for vague and anthropomorphic wording in all four
  languages. Fixed four French guide links to the documentation index found
  by the translation tests.
- Reworded literal German and Spanish translations in the baseline and scanner CLI
  guides, including severity comparisons and missing measurements. Added
  regression cases for the awkward phrases found during review.

### Added

- **The setup wizard exports the scheduled check, not just the configuration.**
  `check-opencloud-scanner configure` now offers to write the monitoring
  configuration next to the file it saved, and `--export-monitoring`
  (`icinga`, `systemd`, `both`, `none`) answers that question up front for a
  provisioning script. It produces an Icinga 2 `Service` object, and a systemd
  `oneshot` service, `daily` timer and `COS_` environment file, each carrying
  the thresholds, the release track and every other answer just given - so the
  check that runs every day is the one that was configured rather than an
  example adjusted from memory. Two rules shape the output: **nothing is
  installed** (the files are written for review and the install commands are
  printed, never run), and **no credential is written into them** - a webhook
  URL or release token stays in the owner-only configuration file, which both
  artefacts point at with `vars.opencloud_config` and `COS_CONFIG_FILE`, and
  the settings withheld are named rather than silently dropped. The generated
  unit carries the same hardening directives as the one in `contrib/systemd/`,
  asserted by a test so it cannot quietly become a weaker copy.

- **`check-opencloud-scanner diff` compares two results finding by finding.**
  A new `--format side-by-side` states both scans as two columns, one finding
  per row, so a reader does not have to rebuild each side from a list of
  changes; `--all-findings` adds the findings that did not move. Every
  comparison now reports per-finding severity movement - a `~` line and a
  `Failing by severity:` tally - which the baseline's comparison of two sets
  of names cannot express: a check that stayed open and moved from `high` to
  `critical` never enters or leaves that set, and caps the rating a grade
  lower. `--category` narrows the comparison to one area, taking a value
  either from the finding categories (`exposure`, `headers`, `transport`,
  `advisory`, ...) or from the change categories (`instance`,
  `referenceData`, `scanner`, `policy`, `unknown`); an unknown value is
  refused rather than silently showing nothing. `--format json` carries the
  same as `findings` and `severityTotals`. A side that was never measured is
  reported as such and never as a pass, and a waived finding is still counted.

- **A finished scan downloads as a remediation bundle: only the work that is
  left, with the configuration that closes it.** The result page and
  `GET /api/scans/{uuid}/export/{format}` gained `remediation-md` and
  `remediation-html`. A bundle carries **only** the open, actionable findings
  - waived entries and the flags OpenCloud hardcodes are left out - each with
  what the scanner observed, what it means and what to change, followed by the
  nginx, Caddy, Traefik, Docker Compose and `.env` fragments that satisfy
  them, rendered from the hardening catalogue's own `env_fix` and
  `header_fix` entries. Every flavour is written out rather than one, each
  naming which findings it covers and which belong in the other kind of file,
  and a finding whose right value is a decision about the deployment is listed
  as having no mechanical fix rather than given a placeholder to edit. The
  grade, the passed checks and the advisory list stay in the full report:
  repeating them here would bury the one thing the file is for.

- **SARIF output now carries what a code-scanning dashboard needs to act on a
  finding.** `--format sarif` previously named a rule and a level and left the
  rest to a reader's own research. Each rule now carries the hardening
  catalogue's remediation sentence, the official documentation link
  (`helpUri`), the catalogue entry that explains a per-path finding
  (`catalogueId` - `exposed` for `exposed:/opencloud.yaml`), the setting
  behind it, and the `security-severity`, `problem.severity` and `tags`
  properties GitHub code scanning sorts and filters alerts on. Each result
  carries the severity, category, remediation and reference beside the host,
  and a `partialFingerprints` entry stable across runs, so a finding that has
  been open for a month stays one alert with a history rather than a new one
  every night. An advisory additionally names `fixedIn` and the release
  window it covers (`affectedRanges`, e.g. `>= 1.0.0, < 4.0.8`), and the run
  reports the rating, version and end-of-life state per scanned host. The web
  application's own SARIF export gained the same properties and fingerprints,
  keeping the two renderers in convention-sync as ADR 0026 requires.

- **A scan result's `vulnerabilities` entries name the release range they
  apply to.** `affectedRanges` (and `introduced`) join `fixedIn`, so a reader
  can tell whether an older release was ever affected rather than only which
  release ends the window.

### Fixed

- **The French scanner CLI guide no longer ships the newly added comparison
  sections in English.** Its `diff` explanation, severity view, side-by-side
  output and category filtering are now translated, and regression tests catch
  those copied-English phrases in future guide updates.

- **The German operator area no longer leaves avoidable English labels in
  place.** Advisory status is shown as Sicherheitsmeldungen, update controls
  as Aktualisierungen, and the audit section consistently names its log.
