## check-opencloud-security 1.28.0

### Added

- **Upgrade rehearsal: what each candidate release would fix, leave and
  rate.** The scan result gains `upgradeRehearsal`, which simulates every
  release worth moving to (the newest patch of the installed line and the
  newest release of each later line, only on the declared track) against the
  advisory database and the release schedule. The plugin prints it as one
  detail line, for example "Upgrade rehearsal: 7.2.4 fixes 3 findings,
  leaves 1, reaches rating C", and the webhook payload carries it as
  `upgrade_rehearsal`. The rating replays the scanner's own version rules and
  keeps the instance's failed checks as caps, because an upgrade does not
  change the proxy. See
  [Rehearse every upgrade](docs/release-lifecycle.md#rehearse-every-upgrade).

- **A scan the target cooldown refuses now opens your earlier result.** When
  an instance was scanned too recently and this browser tab has already shown
  a finished scan of it, the web application opens that result instead of
  only refusing, says it is the earlier result, and counts down to when a new
  scan is possible. The earlier result comes from the tab's own scan history
  (the one the comparison offer keeps in `sessionStorage`); the server never
  hands one visitor a scan somebody else started, as
  [ADR 0002](adr/0002-no-scan-result-caching.md) requires. Without such a
  scan the refusal is unchanged.

- **`--verify-remediation` re-checks one finding without a full scan.**
  After changing a single reverse-proxy setting, pass the finding ids the
  full output reported (repeatable or comma-separated, a family root such as
  `exposed` covers every member) and only the probes that measure them run.
  The plugin answers `OK` when every one now passes, `WARNING`/`CRITICAL`
  while one still fails, and `UNKNOWN` for an id only a full scan can settle
  (`eol`, a vulnerability, address parity). No rating, baseline or webhook.
  The measurement is `opencloud_local_scan.verification.verify`, which reuses
  the scanner's own probes so its answer matches the next full scan. See
  ADR 0072.

### Documentation

- **Translated release-lifecycle guides now include the upgrade-rehearsal
  section.** Their section anchors stay aligned with the English guide.

### Fixed

- **Pytest no longer collects mutmut's generated working copy.** This avoids
  an `ImportPathMismatchError` between the real and mutated test suites.
