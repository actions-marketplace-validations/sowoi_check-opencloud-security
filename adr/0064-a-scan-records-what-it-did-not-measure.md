# ADR 0064: A scan records what it did not measure

- Status: Accepted
- Date: 2026-09-17
- Extends: ADR 0013

## Context

A result document reports what the scanner observed. When it could not
observe something, it leaves the measurement out - ADR 0013 requires exactly
that, because writing a value nobody measured is worse than writing nothing.

The consequence is that a check that passed and a check that never ran look
identical to a reader: both are an absence. `hardenings` has no
`userEnumerationRestricted` key when the instance published no
user-enumeration setting, and none when the capabilities document could not
be read at all. `tls` is `null` for an instance on plain HTTP and `null` for
a scan with the extra checks turned off. The grade is computed from evidence
either way, and it is correct either way, but it is read as a statement about
the whole check list - and the check list was shorter than the reader thinks.

Nothing in the document said so, and nothing could work it out afterwards:
inferring "not measured" from an absent key is the same guess in the other
direction.

## Decision

**A scan records a coverage entry for every check it considered, at the point
where it decided.** `opencloud_local_scan/coverage.py` defines the contract
and `scan()` records into it beside each decision - not afterwards from the
finished document, because absence is the thing being explained and reading
it back would answer the question with itself.

**Four states, and a reason whenever there is no measurement.** `passed` and
`failed` are measurements and carry no reason. `not_checked` is a check the
scanner chose not to run and `inconclusive` is one that ran without reaching
a conclusion; both carry a machine-readable reason from a closed set -
`not_applicable`, `probe_disabled`, `prerequisite_missing`, `timeout`,
`unreadable`, `no_route` - and a sentence of detail. `CoverageEntry` refuses
to be built any other way, so a reason cannot ride along with a pass.

**The reason is what separates a gap from a property of the deployment.** An
instance on plain HTTP has no certificate to inspect: that is
`not_applicable`, not a hole in the scan. An operator who turned the extra
checks off gets `probe_disabled`, which is their own configuration reported
back to them. A capabilities document the instance never published is
`prerequisite_missing`.

**The total is what this scan considered, not a constant.** The checks are
dynamic - which paths are probed, which debug ports are dialled, which
addresses are compared all depend on the instance and the settings - so there
is no fixed denominator to divide by, and inventing one would be a fiction.
The document publishes the count of entries this scan recorded.

**Coverage explains a grade and never changes one.** Nothing in the block
reaches the rating, the severities, the alert line, the exit code or the
webhook payload. Identical evidence grades identically whether or not the
block is present. A waived failure stays a `failed` measurement with its
acceptance recorded separately in `extraChecks[].ignored`: a waiver is a
decision about alerting, and letting it improve the coverage figure would
make the one number that describes the evidence describe the policy instead.

**A report without the block is a report that does not say.** Readers ask
`coverage.coverage_of()`, which answers `None` for a document written before
this existed or carrying something that is not a coverage block. The
interface renders that as "this report does not record its coverage", never
as a scan with no gaps.

## Consequences

The result document gains one additive key, `coverage`, with its own `schema`
number. Every existing reader is unaffected: no key changed meaning, none was
removed, and the grade arithmetic is untouched.

`_check_headers` still reports `false` for a page it never read, because the
rating has always counted it that way and ADR 0064 must not move a grade.
Coverage is where that difference is now stated: those headers are recorded
`inconclusive` with reason `unreadable` while the rating continues to treat
them exactly as before. Changing the rating itself would need its own record.

`HARDENING_PREREQUISITES` sits beside `derive_hardenings` and has to grow with
it. A hardening added to one and not the other is a check the block cannot
explain, and `tests/test_coverage.py` fails on precisely that.

The web application regroups the block in `webapp/catalog.py` and renders the
gaps beside the grade in all four languages. It translates the reason token;
it never decides a different one.
