## check-opencloud-security 1.28.1

### Added

- **`--profile` judges a scan by a named threshold set.** `strict`, `ops` and
  `lenient` each decide the five settings a team otherwise writes out by hand
  - `--warning`, `--critical`, `--check-hardening`, `--update-warning` and
  `--eol-warning` - so a monitoring definition can adopt a stance without
  twelve flags. A profile decides **how the same measurements are judged,
  never how hard the instance is probed**: there is no profile that scans
  more or less. It is also the weakest source of a value, so an explicit
  flag, an environment variable or a configuration key still wins, and the
  `--debug` explanation names the profile a rating was judged by. Leaving it
  unset keeps every default exactly as it was. See
  [Threshold profiles](README.md#threshold-profiles).

- **The web application renders the upgrade rehearsal.** The result page
  gains a *What upgrading would buy you* panel: one row per candidate
  release, with the advisories it clears, the ones it leaves, any it newly
  brings in, whether it is already end of life, and the grade it would reach.
  Where the version alone would rate better than the row shows, the panel
  says so - the difference is this instance's own findings, which an upgrade
  does not touch. Every number comes from the scanner's `upgradeRehearsal`;
  the web layer only picks the letter and the tone, as it does for every
  other grade on the page. A result stored before the rehearsal existed
  renders without the panel rather than as an instance with nothing to
  upgrade to.

- **A golden corpus of frozen verdicts.** `tests/golden/` records the whole
  judgement a handful of known instances earn - rating, grade, failed checks,
  missing measures, the caps that produced the rating and the exit code under
  the plugin's defaults and under every profile - and `tests/test_golden_corpus.py`
  replays them. It is the assertion no single test makes: that a severity
  raised or a measure added to the catalogue cannot silently re-grade every
  instance that looks like one of these. The reference data is pinned in
  `tests/golden_corpus.py`, so a published release or advisory does not move
  the corpus; `python scripts/update_golden_corpus.py` rewrites it when the
  new verdict is the intended one.

### Changed

- **The Icinga check commands offer `--profile`.** The three CheckCommand
  definitions - `contrib/icinga2/check_opencloud_security.conf` and the
  `opencloud_check_native` / `opencloud_check_docker` role templates - carry
  the new option as `$opencloud_profile$`, next to `--warning` and
  `--critical`. Without it an Icinga user could not reach a profile at all,
  which is what `tests/test_monitoring_parity.py` is there to notice.

- **The upgrade rehearsal's reporting is pinned by tests.** Mutation testing
  found the two plugin helpers behind it under-covered: an end-of-life
  candidate, a malformed entry, a rating outside the 0-5 range and seven of
  the webhook payload's ten keys were asserted by nothing. The gaps are
  closed, and `tests/test_verify_remediation.py` and
  `tests/test_threshold_profiles.py` are now part of the mutmut test
  selection, which reported "no tests" for `verification.py` before.

### Security

- **The web application sends `Strict-Transport-Security` over HTTPS.** The
  generated reverse-proxy configuration deliberately adds no security headers
  - "the application sends its own, and an `add_header` here would be one
  more place they can disagree" - and HSTS was the one the application did
  not send, so no deployment built by `docker/setup-wizard.py` had it. A
  service whose subject is HTTPS enforcement now asks of itself what
  `hstsLongMaxAge` and `hstsIncludeSubdomains` ask of the instances it
  scans: `max-age=63072000; includeSubDomains`. Not `preload`, which is an
  effectively irreversible submission to a list browsers ship and belongs to
  whoever owns the domain. Sent only over TLS, because RFC 6797 forbids a
  browser to record it from a cleartext hop - and the scheme is read from
  `X-Forwarded-Proto` only where `COS_WEB_TRUST_FORWARDED_FOR` says a proxy
  writes it, which is the same trust decision `client_address` makes.

- **A tampered erasure receipt verifies as false rather than raising.**
  `webapp.purge.verify` compared the expected digest with the receipt's
  signature as `str`, and `hmac.compare_digest` raises `TypeError` on a
  string outside ASCII - so a receipt edited to carry one answered an auditor
  with a traceback instead of the `False` the function is read for. Both
  sides are encoded now, exactly as the purge endpoint has always compared
  its token. The endpoint itself was never affected.
