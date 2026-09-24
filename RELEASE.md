## check-opencloud-security 1.31.0

### Documentation

- Polished scan progress, errors, downloads and sharing text in English,
  German, Spanish and French. Corrected informal Spanish instructions and
  clarified that saved downloads remain available after a scan expires.
- Updated all four web-service guides to describe every export format,
  including offline HTML reports and remediation bundles. Expanded tests for
  translated error pages, email drafts, link-free summaries and download links.
- Translation checks now catch additional Spanish forms of informal address
  and report broken guide links at their original line numbers, ignoring
  links shown only in code examples. Added regression tests for both cases.

### Added

- **Coverage regression alerts.** With `--baseline`, a check that an earlier
  run reached a conclusion on and that is `inconclusive` now raises an `OK` to
  `WARNING`, even when the grade has not moved. The rating, its perfdata and
  the findings are untouched: the scan saw less, the instance did not change.
  The warning lasts until the check is measured again, `--warn-on-new` does
  not suppress it, the webhook's `baseline_diff` carries the lost checks as
  `coverage_regressed`, and the two-document comparison reports a
  `coverageRegressed` scanner change. See ADR 0074 and
  [Reporting only what changed](docs/baseline.md#coverage-regressions).
- **Grouped remediation plans.** `remediationPlan.groups` places every open
  finding in the system its fix is made in - the reverse proxy, the identity
  provider, OpenCloud or the DNS zone - and merges the findings one edit
  resolves into a single change: every missing header is one header block,
  every exposed path one proxy rule, and the update closes every matching
  advisory. Each change carries the rating it alone would give, replayed
  through the rating function, and `groupSummary` names the changes that
  resolve several findings at once. Shown by `--debug`, on the web dashboard
  ("What to change where"), in the remediation bundle, and returned by the
  `plan_remediation` MCP tool. See ADR 0075 and
  [What would raise the rating](README.md#grouped-by-where-the-change-is-made).
- **Architecture decisions in the operator area.** A new Decisions tab at
  `/admin/decisions` lists every architecture decision record with its
  status, and a filter narrows the list by number, title or status. Each
  record opens as its own page in English, and links between records, or from
  the Architecture tab, stay inside the area. The area's search now indexes
  every record's full text. Like the rest of the area, the records are never
  public: a stranger gets a 404, and they are absent from the public search,
  the sitemap and `/documentation`.
- **`check-opencloud-scanner review-waivers`.** It reads the configured
  waivers (`ignore_hardenings` and `temporary_waivers`, or the
  `--ignore-hardening` and `--waive-until` values given to it) and lists five
  kinds that need attention. *Expired* waivers no longer suppress anything.
  *Expiring soon* ones run out within the `waiver_warning` window. *Unused*
  ones match no failing check in a `--result` document, or with no document,
  no identifier the scanner knows. *Overlapping* ones are already covered by
  another waiver, such as a deadline hidden under a permanent `*`.
  *Permanent* ones have no reason and no deadline. Each item has a suggested
  cleanup, for a permanent waiver a `--waive-until` record to copy. The
  command never changes the configuration. It exits `1` when it lists
  anything, unless given `--exit-zero`, and `--format json` suits scripts. See
  [the scanner command](docs/scanner-cli.md#review-waivers---waivers-that-need-attention).
- **`check-opencloud-scanner fleet`.** It turns saved `scan` result
  documents into one summary of a fleet. Give it files, or directories that
  it searches for `*.json`, and it keeps the newest report of each host. It
  lists end-of-life releases and releases whose support ends soon. The
  recorded version is placed in today's release schedule again, so a line
  that closed after the report was written is listed too. It lists waivers
  that let a failing check alert again within `--window` days (default
  `30`), measured against today. It counts the failing findings that most
  hosts share, and leaves out the ones no operator can change. Under missing
  coverage it lists stale reports (`--stale-after`, default `7` days), failed
  scans, checks the scans could not evaluate, and hosts named by `--expect`
  or `--inventory` that have no report. The output is text, Markdown, JSON,
  or one self-contained HTML page that fetches nothing. It never scans,
  stores nothing and applies no threshold, so it exits `0` whenever it
  printed a summary. See
  [the scanner command](docs/scanner-cli.md#fleet---a-dashboard-from-saved-results).

### Fixed

- **The `.deb` install smoke test survives a mirror caught mid-sync.** When
  the Ubuntu or Debian mirror lists a dependency it no longer serves (a
  404), `packaging/tests/install-smoke.sh` refreshes the package index and
  tries the install once more before the release dry run fails.
