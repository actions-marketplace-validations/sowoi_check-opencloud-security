## check-opencloud-security 1.31.2

### Security

- **The erasure credential throttle counts an IPv6 client by its /64.** Failed
  guesses at the `DELETE /api/purge` token were counted per single address,
  while every other limit counts an IPv6 client by the /64 it is handed - so
  rotating the interface identifier bought five fresh guesses each time. The
  32-character minimum on the token kept guessing impractical regardless.
- **The scan service refuses a guessable token on a wide bind.** Serving
  anywhere but loopback required a token but accepted any non-empty one -
  `--token a`, or the placeholder `secrets/scanner_token.example` ships with -
  and nothing counts failed attempts, so a short token let anybody who reached
  the port make it scan whatever they named. Such a bind now needs a token of
  at least 32 characters that is not that placeholder, or it refuses to start.
  `openssl rand -hex 32`, which every guide already uses, is unaffected.

### Fixed

- **A check only one of two scans made is no longer called new or resolved.**
  Comparisons read a finding missing from the earlier scan as passing, so a
  check added by a newer scanner - or by turning the extra checks on - was
  reported as a regression of the instance, and a check the later scan no
  longer made as fixed. The baseline, `check-opencloud-scanner diff`, the web
  comparison and `compare_scans` now list these as newly measured or no
  longer measured, based on each scan's coverage block, and the explanation
  files them as scanner changes. A newly measured failure still alerts, and
  `--warn-on-new` still does not suppress it. A report or baseline that does
  not list its checks is compared as before. See ADR 0079.
- Aligned the report expiry footer, warning and live countdown to round remaining
  minutes up consistently in every language.
- **A comparison page rounds its expiry up too.** It rounded the minutes
  left down, so it announced one minute fewer than the result page would.

### Documentation

- Added German, Spanish and French operator architecture and operations documentation, including
  localized document navigation and operator search. Section anchors and commands
  remain aligned with English; ADRs and release-note bodies remain English.

- Clarified grouped remediation, upgrade estimates, report expiry and operator
  messages in English, German, Spanish and French. A simulated upgrade whose
  grade is limited by findings no longer implies that the grade cannot improve.
  Count labels also read correctly for a single finding.
- Expanded all-language tests for remediation groups, upgrade estimates,
  escaped version strings, singular and plural expiry warnings, and the
  translated decision-record interface around English source documents.
- **Decision records are never translated.** ADR 0077 records that every
  record in `adr/` exists in English only, and once: the operator area shows
  it untranslated in every locale, and translation work leaves `adr/` alone.
- **Changelogs and release notes are never translated.** ADR 0078 records
  that `CHANGELOG.md`, `RELEASE.md` and the GitHub release body exist in
  English only, and that the operator area's Releases tab shows them
  untranslated in every locale.
