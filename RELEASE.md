## check-opencloud-security 1.29.1

### Changed

- **The `--policy` deployment gate is now covered by tests mutation testing
  can run.** Its behaviour was only ever exercised through the real CLI, which
  runs the plugin as a subprocess, so mutation testing could delete the scan
  document, the rating or the vulnerability list that `_apply_policy` is
  handed - and drop the policy verdict from the webhook payload - without a
  single test noticing. A violation that should fail a pipeline could have
  stopped failing it silently. `tests/test_policy_gate.py` now drives the same
  gate in process and is listed in the mutmut selection; the five surviving
  mutants it was written for are killed.

- **A result list that no longer lines up with the checks that produced it is
  now an error rather than a shorter report.** Every place the scanner and the
  plugin pair a list of checks with the results `_run_all` returned for them -
  the exposed paths, the protected endpoints, the debug endpoints and ports,
  the demo accounts, and the per-host rows of the `checkmk` and `summary`
  output formats - zipped the two without asserting they were the same length.
  The lengths match by construction today, so nothing changes for any scan that
  runs; what changes is the failure mode if a later edit breaks that pairing.
  Silently dropping the tail would have meant a report that omits checks
  without saying so, which reads as an instance that passed them. The one
  pairing deliberately left lenient is the lifecycle page parser, where the two
  lists come from somebody else's HTML and a tab without a panel must be
  dropped rather than raise.

### Fixed

- The browser test for the severity filter no longer drops its own press in
  WebKit on CI. Pressing a counter hides most of the list and reveals the
  status line above it, so the page it leaves behind is a different height
  from the one that was pressed; the test read the new count back with a
  single sample and pressed *clear* straight away, on a control that was
  still settling. WebKit dropped that press rather than delivering it, the
  filter stayed on, and the run failed counting a list nobody had asked for.
  Each press is now waited out for the count it asked for before the next one
  is aimed, which still fails - loudly - if a press is ever genuinely lost.
