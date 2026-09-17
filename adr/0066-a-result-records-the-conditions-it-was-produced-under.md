# ADR 0066: A result records the conditions it was produced under

- Status: Accepted
- Date: 2026-09-17
- Extends: ADR 0057, ADR 0059, ADR 0064

## Context

Two scans of the same instance can disagree without the instance having
changed. The advisory database learned a CVE. The release schedule moved a
line to end of life. A day passed and a support window closed. The scanner was
upgraded and started making a check it did not make before. A waiver expired.

A comparison could not tell any of that from a real regression, because a
result document records what was *observed* and not what was *known* at the
time. "Rating 5 -> 3" was the whole answer, and an operator had to work out
the rest from memory. The two cases need opposite responses - fix the
instance, or read the new advisory - so guessing between them is expensive.

## Decision

**A result records a `provenance` block, built from the data the scan was
given, while it ran.** The scanner's version, the moment of the scan, the
release track asked for, the waivers in force, how much was measured, and a
stable digest of the exact advisory database and release schedule it judged
against.

**A digest, not a copy and not a path.** The question is "was this the same
reference data?", which 64 characters answer. Embedding the database would put
megabytes of other people's advisories in every report; recording a file path
would publish where the server keeps its files. The digest is canonical JSON
over each record's identifying fields, so the same data hashes the same
however it was serialised, merged or ordered - a digest that changed when a
file was merely rewritten would report churn on every scan.

**Captured from the scan's own scope, never looked up afterwards.** A worker
that refreshes its advisory database between finishing a scan and rendering
the report would otherwise describe the scan with data the scan never saw.

**Publication time and scan time are separate fields.** A schedule generated
in June and read in September has one of each, and a comparison that confused
them would call a stale file fresh.

**One explanation model, shared.** `opencloud_local_scan/changes.py` turns two
documents into contributing changes grouped as `instance`, `referenceData`,
`scanner`, `policy` or `unknown`. `check-opencloud-scanner diff` and
`webapp/workflows.py:compare_documents` both call it, so an operator's own
monitoring and the public service cannot explain the same two documents
differently.

**It claims only what the evidence establishes.** A changed digest means the
reference data differed - not that it caused any particular grade to move, and
the sentence says so. Several changes may contribute; none is elected "the
cause". A difference nothing accounts for is reported in the `unknown`
category rather than omitted, because a list that quietly drops what it cannot
explain looks complete when it is not.

**Missing context is a stated limitation.** A report written before this block
existed cannot say what it was judged against, and one without coverage cannot
distinguish a check that stopped failing from one that stopped being made. The
comparison says which question it cannot answer instead of assuming.

**Waiver reasons are not comparable state.** The block records waiver patterns
and their states, never the reason text: a reason is prose written for a
person, and diffing it would report a corrected typo as a change of policy.

**An uploaded report's blocks come through the same allow-list.** ADR 0057
holds: `webapp/imports.py` rebuilds `provenance` and `coverage` key by key,
retyping each field and dropping a digest that is not one of ours. The
per-check coverage detail is not rebuilt at all, because nothing in a
comparison reads an individual entry and an allow-list that copies arbitrary
objects is not one.

## Consequences

The result document gains one additive key, `provenance`, with its own schema
number. Nothing existing changed meaning. The comparison payload gains
`explanation`; `changes`, `introduced`, `resolved` and `verdict` are untouched,
so an existing client keeps working.

No new persistent history is created. The explanation is computed from the two
documents in hand, at the moment they are compared, and stored nowhere.

ADR 0059 still refuses a comparison of two different instances, and this does
not weaken it: provenance explains why the same instance's results differ.

`advisorySources` continues to carry the file paths the database was read
from. That predates this record and is unchanged by it; whether a public
deployment should publish those paths is a separate question from this one.
