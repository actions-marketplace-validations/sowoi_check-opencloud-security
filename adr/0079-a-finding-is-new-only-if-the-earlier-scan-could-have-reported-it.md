# ADR 0079: A finding is new only if the earlier scan could have reported it

- Status: Accepted
- Date: 2026-09-24
- Extends: ADR 0029, ADR 0074

## Context

ADR 0029 made every comparison - the plugin's `--baseline`,
`check-opencloud-scanner diff`, the web page and the `compare_scans` tool -
one arithmetic: a finding is a name in a set, and what is in the later set and
not the earlier one is new.

That arithmetic reads an absent finding as a passing one. For most of a
scan's life that is true, but not across a scanner upgrade. A scanner that did
not yet know `basicAuthDisabled` writes nothing about it; the next scanner
measures it, finds it failing, and the comparison reports "new since last
run" and a verdict of `regressed` about an instance that did not change. The
explanation then filed it under `instance` as a check that "started failing".
The same happens the other way round: a check the later scan did not make
reads as resolved, and the verdict as `improved`. Turning the extra checks on
between two runs has the same effect.

ADR 0064 already gives the scan a record of what it considered - the
`coverage` block, written where each decision is made. Presence of a key in
`hardenings` or `extraChecks` is not a substitute: an uploaded CSV report
(ADR 0057) carries only the failing rows, so reading "not listed" as "not
checked" there would turn a real regression into a softer word.

## Decision

**A finding counts as introduced or resolved only if both scans could have
reported it.** `snapshot_of` records, in `Snapshot.considered`, every
hardening, header and extra-check finding the scan's coverage block lists, in
any state. `Baseline.compare` moves a finding that is failing now, that the
earlier scan did not consider and that this one did, from `new_findings` to
`Comparison.newly_measured`; and a finding failing before, that this scan did
not consider and the earlier one did, from `resolved_findings` to
`Comparison.no_longer_measured`.

**It needs both sides to say.** A document without a check list - no
coverage block, an uploaded report whose entries are not carried over, or a
baseline file written before this field - has `considered = None`, and the
comparison is exactly what it was before. So is any finding neither side lists
as a check, such as an advisory or `httpsEnforced`. The rule can only move a
finding that the record positively shows was not checked.

**A newly measured failure still alerts.** `Comparison.regressed` includes
it, so `--warn-on-new` does not file it under "nothing new": it is not the
instance's doing, but nobody has been told about it yet, and suppressing it
once would suppress it for good. The difference is in what it is called -
`Newly measured (n): ... - the last run did not check these` rather than
`New since last run` - and in where it is listed. The web verdict stays
`regressed` for the same reason; `resolved` no longer contains a check that
was simply not made, so a verdict of `improved` no longer rests on one.

**The explanation says the scanner moved.** `changes.explain` reports
`checksNewlyMeasured` and `checksNoLongerMeasured` in the `scanner` category
and leaves those checks out of `findingsAppeared` and `findingsResolved`, and
states a limitation when either report does not list its checks.

**The web comparison carries `newlyMeasured` and `noLongerMeasured`**, and
the page shows each in a card of its own only when it is not empty.

## Consequences

The baseline file gains one additive key per host. `FORMAT_VERSION` is
unchanged; the first run after an upgrade compares as before, because the
stored snapshot cannot say what it considered.

The alert state of every existing setup is unchanged: what moved is the
wording and the list a finding appears in, never whether a run alerts.

An uploaded report cannot benefit from this until the import rebuilds the
coverage entries it currently drops. That is deliberately left for a change
of its own, because it widens what an untrusted file may carry into the
comparison.

## Alternatives considered

- **Inferring "not checked" from a missing key.** Wrong for every report that
  lists only failures, and wrong in the direction that hides a regression.
- **Not counting a newly measured failure as a regression at all.** It would
  make `--warn-on-new` swallow a failure the operator has never been shown.
- **A new web verdict value.** Existing clients branch on the three values
  ADR 0029 named; the new lists say the same thing without breaking them.
