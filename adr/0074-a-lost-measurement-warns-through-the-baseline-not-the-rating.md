# ADR 0074: A lost measurement warns through the baseline, not the rating

- Status: Accepted
- Date: 2026-09-24
- Extends: ADR 0064

## Context

ADR 0064 made a scan record what it did not measure, and decided that
coverage explains a grade and never changes one - not the rating, not the
alert line, not the exit code.

That keeps a single scan honest. It leaves a gap across scans: a check that
was measured every day for a month and times out today leaves the grade where
it was, and the alert state where it was. The grade is still correct for the
evidence, but the evidence is thinner than yesterday's and nobody is told. A
monitoring check whose job is to notice change is silent about the one change
that makes its own answer less trustworthy.

Only a comparison can see this. A single document says "inconclusive"; it
takes the previous run to say "and it was not before".

## Decision

**The baseline records, per host, which coverage checks reached a
conclusion, and a run warns when one of them is `inconclusive` now.**
`Snapshot.measured` and `Snapshot.inconclusive` hold it;
`Comparison.coverage_lost` names each lost check with the scanner's reason.

**It is kept apart from the rating.** The rating, the severities, the
findings and every perfdata value stay exactly what the evidence gave. The
plugin raises an `OK` to `WARNING` with its own message and never touches a
run that is already `WARNING` or `CRITICAL` beyond adding a line. ADR 0064's
rule still holds for the coverage block and for a single scan; this is a
statement about the difference between two scans, made where differences are
already made.

**Only `inconclusive` counts.** `not_checked` is the scanner deciding not to
look - a probe the operator disabled, or a check that no longer applies to
the deployment - and reporting that as a regression would report the
operator's own configuration back to them.

**A lost check stays measurable until it is measured again.** The recorded
snapshot carries it forward, so the warning lasts as long as the gap rather
than for one check interval, after which the gap would otherwise have become
the baseline.

**`--warn-on-new` does not suppress it**, for the same reason it does not
suppress a new finding: it is new.

The two-document comparison (`changes.explain`) reports the same loss as a
`coverageRegressed` scanner change, so the CLI, the web comparison and the
plugin cannot disagree about it.

## Consequences

The baseline file gains two additive keys per host. A file written before
them loads with `measured` unset, which is a snapshot that cannot say, and the
first run after an upgrade reports no loss. `FORMAT_VERSION` is unchanged.

A deployment whose DNS or network is flaky will see `WARNING` states it did
not see before. That is the point - the grade in those runs rested on less
evidence - but it is a behaviour change for anyone already using
`--baseline`.

Rejected: lowering the rating for lost coverage, which would make the grade
describe the scan rather than the instance; and a separate opt-in flag, which
would leave the gap closed only for people who already knew it was there.
