## check-opencloud-security 1.25.0

### Added

- **The comparison journeys are covered in a real browser.** The Playwright
  suite now downloads a scan report and uploads it as the baseline for a later
  scan, follows the same-tab comparison offer through to its result, and
  verifies that the capability-bearing scan history does not cross into
  another tab.
- **Translation quality checks.** `scripts/check_translations.py` compares the
  four frontend catalogues and the translated guides against their English
  source and separates what a machine can decide from what it cannot.
  Structural differences - a missing or unknown key, changed `{placeholders}`,
  a string `str.format` would refuse, changed or disallowed inline markup, a
  translated `href`, a relative guide link that resolves to no file - are
  errors and fail CI. Prose heuristics - the form of address a language uses,
  a string left in English, a dropped product name, a glossary term rendered
  two ways - are warnings that name a key for a reviewer, and `--strict` fails
  on those too. Decisions about a warning are recorded in the script's
  `ACCEPTED` table rather than by removing the check.
- **[`TRANSLATING.md`](TRANSLATING.md), the style guide behind those checks.**
  It records the register each language uses - German informal "du", French
  polite "vous", Spanish polite "usted" - the agreed terminology, what happens
  to example hostnames and placeholders, and the review workflow.

- **A scan now records what it did not measure.** The result document gains an
  additive `coverage` block: every check the scan considered, in one of four
  states - `passed`, `failed`, `not_checked` or `inconclusive` - and, whenever
  there is no measurement, a machine-readable reason from a closed set
  (`not_applicable`, `probe_disabled`, `prerequisite_missing`, `timeout`,
  `unreadable`, `no_route`) with a sentence of detail. A passed check and a
  check that never ran no longer look identical. The reason is what separates
  a property of the deployment - no certificate to inspect on a plain-HTTP
  instance - from a probe somebody turned off. The total is what that scan
  considered rather than a fixed denominator, because the checks are dynamic.
  Coverage explains a grade and never changes one: nothing in the block reaches
  the rating, the severities, the alert line, the exit code or the webhook
  payload, and a waived failure stays a failed measurement with its acceptance
  recorded separately. A report written before this existed has no block, which
  every reader treats as "does not say" rather than "nothing was missed". The
  result page shows the gaps beside the grade in all four languages. See
  [ADR 0064](adr/0064-a-scan-records-what-it-did-not-measure.md).

- **A waiver can now carry a reason and a deadline.** `--waive-until
  'debugPort:9205|2026-12-31T00:00:00Z|Firewall change, OPS-412'` accepts a
  failing check until a stated moment, after which it alerts again with no
  configuration change - the fix for a waiver added "for two weeks" that is
  still suppressing an alert a year later. The expiry must carry a timezone and
  the reason may not be empty; a record missing either is refused rather than
  quietly becoming permanent, because failing open is how a typo outlives
  everybody who knew about it. The boundary is `now >= expires_at`, decided
  once per scan against one UTC clock. A bare pattern in `--ignore-hardening`
  is still a permanent waiver and is unchanged. Any active record suppresses,
  and the result document's new `waivers` block lists every record that applies
  to a check - active, expired, and the ones that matched nothing - so a
  permanent wildcard cannot silently absorb an expiry underneath it. Waivers
  still only apply to failing checks, still never remove evidence, and end of
  life is still an F. Configurable as `COS_SCANNER_TEMPORARY_WAIVERS` and
  `scanner.temporary_waivers`. See
  [ADR 0065](adr/0065-a-waiver-may-carry-a-reason-and-a-deadline.md).
- **A comparison now explains why a result changed, not only that it did.**
  Every scan records a `provenance` block built from the data it was actually
  given while it ran: the scanner version, the scan time, the release track,
  the waivers in force, how much was measured, and a stable digest of the exact
  advisory database and release schedule it judged against - a digest rather
  than a copy or a file path, and one that is independent of serialisation
  order. `check-opencloud-scanner diff` and the web comparison then share one
  explanation model that groups contributing changes as `instance`,
  `referenceData`, `scanner`, `policy` or `unknown`, so an upgrade, a newly
  recorded advisory, a support window that simply elapsed, a scanner upgrade
  and an expired waiver are told apart instead of all reading as a regression.
  It claims only what the evidence supports: a changed digest establishes that
  the reference data differed and explicitly not that it caused any particular
  grade to move, several changes may contribute without one being elected the
  cause, and a difference nothing accounts for is reported as unexplained
  rather than dropped. An older report that records neither block still
  compares; what cannot be established is reported as a limitation instead of
  guessed. Uploaded reports pass both blocks through the same bounded
  allow-list (ADR 0057). No new scan history is stored. See
  [ADR 0066](adr/0066-a-result-records-the-conditions-it-was-produced-under.md).
- **A scan can be downloaded as one standalone HTML report.** A result link
  is a capability with a time limit, which is right for a page a stranger can
  reach and wrong for the evidence somebody needs at the end of the quarter.
  `GET /api/scans/{uuid}/export/html` is the same report without the service
  under it: the styling travels inside the document, and there is no script, no
  image, no font service and no stylesheet to fetch, so opening the file makes
  no network request at all - the documentation links are the only addresses in
  it and are followed only if the reader chooses to. It carries the findings,
  the ignored ones with their waiver reasons, the remediation plan, the
  coverage gaps and the reference data the scan was judged against, marking
  what an older report does not record rather than leaving it blank. It says
  plainly that it is a copy that outlives the link, does not update, and is not
  erased when the scan is. There is nothing to operate in it: no form, no
  rescan control, no polling, no erasure token. Every string in it comes from
  the scanned instance or from an operator's waiver, so all of it is escaped
  and a `javascript:` reference renders as text rather than as a link. The
  download sits beside the existing exports on the result page in all four
  languages; the report itself is English, as every export is.

### Security

- **An uploaded report that carries more findings than a report can is now
  refused rather than read in part.** `webapp/imports.py` capped every block
  of a report to its first 500 entries and read the rest of the file as if
  they had never been written. That is the one kind of hole the page cannot
  name: everything past the cut reads as resolved on the earlier side and as
  introduced on the later one, in a comparison that otherwise looks complete.
  A block longer than the cap is now the same 422 as any other file that is
  not a report this service wrote - the answer the CSV row limit already gave
  a file that was too long. What is still read in part is still counted: an
  entry that is not the shape its block is written in, and a waiver that is
  not an identifier this scanner writes, now reach the count the page shows
  beside the comparison instead of disappearing. The grade is read through the
  same length cap as every other string in the file, so a quarter of a
  megabyte of digits is not handed to `int` on the strength of an interpreter
  default an operator can turn off. See
  [ADR 0057](adr/0057-an-uploaded-report-is-evidence-not-a-scan.md).
- **A network serving a probe block can no longer upload a report either.**
  The block ADR 0051 imposes on a client whose recent scans kept turning out
  not to be OpenCloud was asked about on the submission path only, so the same
  network could still hand `POST /compare` a file to parse - the one parser
  here fed from outside, and work this service does whether or not a scan
  follows. It is now asked before the upload's own bucket, as the submission
  path asks it before the client limit, so a blocked client's refusals do not
  run down an allowance it will want back when the block ends. The answer is
  the 429 with `Retry-After` the block gives everywhere else, in its own
  sentence in all four languages.
- **The report upload now reaches the audit trail.** It is the only structure
  this service parses that it did not write, and it was the one refusal an
  operator with `COS_WEB_AUDIT_LOG` on could not see: a spent upload limit and
  a file the parser would not read are now `rate_limited` with the scope
  `rate_limit_upload` and `submission_rejected` with the reason
  `report_rejected`. The record carries the key of this service's own refusal
  and no part of the file, because an audit trail is as attractive a place for
  a hostile upload to be quoted as an error page is.

### Fixed

- **Two sentences about a refused upload printed their own placeholder.** The
  page that says a file is too large, and the one that says a comparison has
  expired, are catalogue strings with a number in them, and both were rendered
  without it - so a reader was told their file exceeded the "{kilobytes} KB"
  limit. Every sentence on that path is now given the size limit and the
  window a comparison lives for, from the settings that enforce them.

- **101 dead links in the French guides.** A guide under `docs/<language>/`
  sits one directory deeper than its English source, so every path out of
  `docs/` needed `../../` and had `../`. The generated French pages carried
  the same mistake into the public documentation, where links to ADRs and
  repository files pointed at GitHub addresses that did not exist. The
  English guide index also linked to a German index that was never written;
  it now points at the three translated guide directories.
