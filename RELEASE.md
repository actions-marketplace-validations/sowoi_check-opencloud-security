## check-opencloud-security 1.29.0

### Added

- **A scan fingerprints the configuration it measured, so drift is visible
  without the grade moving.** A rewritten content security policy, a replaced
  reverse proxy, public links that stopped requiring a password, a certificate
  at a different issuer - none of that has to change a grade, and an operator
  watching only the grade saw none of it. The result document now carries a
  `configuration` block: grouped digests for transport, headers, sharing,
  authentication and proxy, plus one over all five. **Digests only, never the
  configuration** - a policy, an issuer and a server banner go in and a hash
  comes out, so the block is safe on a public page, in a webhook and in an
  uploaded report. The plugin prints `Configuration fingerprint: 9e3c4428`,
  `--baseline` reports `No new findings, but the configuration changed
  (headers)`, `check-opencloud-scanner diff` adds a `configurationChanged`
  change, and the web application shows the groups under *Has this deployment
  changed?*. Routine churn is deliberately excluded: a renewed certificate and
  a proxy's new build number are not drift, and a group the two scans looked
  at differently is reported as not comparable rather than as a change.
  Nothing in it touches a rating, an exit code or an alert line. See
  [ADR 0073](adr/0073-a-result-fingerprints-the-configuration-it-measured.md).
- **`--policy` fails a deployment on explicit requirements, not on a grade.**
  `-w`/`-c` and `--profile` judge an instance by its rating, which is the
  wrong shape for a CI gate: a team that requires HTTPS enforcement and no
  demo accounts cannot express that as a number. A policy file states it
  directly - `minimum_rating`, `required_hardenings` and `forbidden` (a
  missing measure, a failed check or a vulnerability id) - and anything it
  asks for that an instance does not meet ends the run CRITICAL. A policy
  only ever makes a verdict worse, a waiver does not excuse a requirement,
  and an unknown key or measure is a usage error rather than a rule that
  quietly requires nothing. `--format json` and the webhook payload carry the
  verdict under `policy`. See [CI policy mode](README.md#ci-policy-mode) and
  [`config/policy.example.yml`](config/policy.example.yml).
- **`--format summary` reads a whole fleet in one table.** Checking a dozen
  instances printed a dozen result blocks written for a monitoring system,
  which is a lot to read when the question is just "which of these needs me
  today". The new format prints one aligned row per host instead - host,
  grade, version, end-of-life state, how many advisories apply, and how much
  moved since `--baseline` - followed by the same tally the Nagios output
  starts with. Rows keep the order the hosts were given and the exit code is
  unchanged, so it works from a cron job that mails its output. The `NEW`
  column distinguishes "no baseline given" (`-`) from "no new findings" (`0`),
  and a host whose scan failed shows its Nagios status where the grade would
  be. See [Reading a fleet in one table](README.md#reading-a-fleet-in-one-table).
- **The output says how much it could actually measure.** A check that
  passed and one that never ran left the same trace in the plugin's output -
  nothing - so the plugin now prints a `Coverage:` line such as `84 checks
  evaluated, 6 skipped, 2 indeterminate, 1 network-limited`, and the webhook
  payload and `--format json` carry the same counts under `coverage`. The web
  application's *What this scan did not measure* section shows the same four
  numbers. `network_limited` is split out of the skipped and indeterminate
  counts because a timeout or a missing route - DNSSEC, an external identity
  provider, an optional endpoint - is the gap another vantage point might
  close. Nothing in it changes a grade, an exit code or an alert line.
