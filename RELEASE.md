## check-opencloud-security 1.30.1

### Added

- `--waiver-warning DAYS` (`COS_WAIVER_WARNING`, YAML `waiver_warning`)
  sets a warning window for `--waive-until` waivers. If a waiver that hides
  a failing check ends within `DAYS` days, an otherwise OK result becomes
  WARNING. Before this, a waiver gave no lead time. The check was silent
  until the deadline and alerted on the next run after it. The long output
  also names the next waiver to end. The default `0` turns the warning off.
- The `waiver_days_left` performance value counts the days until that
  waiver ends. With `--waiver-warning` it carries the window as its warning
  range. Checkmk reports it under the same name, and Prometheus and OTLP as
  `opencloud_security_waiver_days_remaining`. The webhook payload adds
  `waiver_days_left`, `waiver_warning_days` and `waiver_warning`, and
  `contrib/prometheus/alerts.yml` adds an `OpenCloudWaiverExpiring` rule.
- The `coverage_inconclusive` and `coverage_not_checked` performance values
  put the coverage block on a graph. A graph now shows the day that checks
  become unreadable. Checkmk uses the same names, and Prometheus and OTLP use
  `opencloud_security_coverage_inconclusive_total` and
  `opencloud_security_coverage_not_checked_total`. The grade does not change.

### Documentation

- Replaced vague and literal wording in the interface, scanner guides and
  README. Aligned English, German, Spanish and French explanations and
  corrected inconsistent forms of address.
- Completed the remaining French guide translations while preserving commands,
  technical values and section links.
- Expanded wording checks to current repository documentation and Python
  product strings, including phrases split across lines. Added regression
  cases and a translation review checklist. Corrected inconsistent exemption
  terminology and Spanish plural recognition in the glossary check. Recorded
  reviewed plain-language alternatives so they no longer produce warnings.
