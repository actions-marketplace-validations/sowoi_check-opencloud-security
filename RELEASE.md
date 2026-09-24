## check-opencloud-security 1.30.2

### Changed

- **Tests now cover code that no test reached before.** The advisory refresh
  script `scripts/update_vulnerability_db.py` has tests. They prove that it
  writes new advisories and that `--check` writes nothing. If the feed is
  down, the script keeps the file. `scripts/verify_export.py` has tests too. They
  prove that it refuses edited bytes, the wrong key and a missing key. The scan
  child process in `webapp/scan_process.py` has tests for a rejected target, a
  failed scan and a crash. A rejected target stays a rejection in the worker,
  and a crash sends no exception text. The approval mode in
  `webapp/approval.py` has tests that prove DNS never approves an address
  target, and that a failed TXT lookup is a refusal.
  `tests/test_verify_remediation.py` now makes sure that every extra check and
  hardening flag of a full scan verifies to the same answer, not only three of
  them.

### Documentation

- Clarified operator status, comparison results, monitoring instructions and
  TLS explanations in English, German, Spanish and French. Corrected Spanish
  forms of address and translated two overlooked deployment settings rows.
- Expanded translation tests to cover copied English table descriptions,
  duplicate catalogue keys, repeated placeholders, and formatting and HTML
  escaping across every language, including messages on conditional pages.

### Fixed

- `--waiver-warning` and `waiver_days_left` no longer count a waiver that
  only covers a flag OpenCloud hardcodes, such as
  `publicLinkExpirationEnforced`. That flag never alerts, so the end of its
  waiver changes nothing. Before this fix, such a waiver raised a WARNING.
- The plugin output now says "1 day left" instead of "1 days left" in the
  end-of-life warning, the lifecycle line and the waiver warning. If one
  waiver covers several checks, the waiver warning now says that they
  "alert again".
- If two waivers end at the same moment, the waiver warning now names both.
  Before this fix, it named only one waiver but listed the checks of both.
