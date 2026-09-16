# ADR 0057: An uploaded report is evidence, not a scan

- Status: Accepted
- Date: 2026-09-16

## Context

`/compare` answers "did the fixes work" for a reader holding two uuids
([ADR 0006](0006-a-result-is-rendered-four-ways.md) gave them the files, and
the page gave them the arithmetic). It has one shape of failure that no amount
of care in this service can fix: a result lives an hour by default, and the
interesting comparison is usually against something older than that. The scan
somebody wants as their baseline has almost always expired, and this service
keeps no history to look it up in - deliberately, because a history of who
scanned what is exactly what it exists not to keep.

What the reader does still have is the file. Every result page offers four
downloads, and people keep them: attached to a ticket, in a folder, in the
change record for the work they are now trying to verify.

Letting them upload one back changes something structural, though. Every
document this application has compared until now came out of its own scanner
minutes earlier; the untrusted part was always a *string inside* a document
this service built - a product name, a certificate subject - and
`workflows.REMOTE_FIELDS` names them. An uploaded file is the first untrusted
**structure**: its keys, its types, its nesting and its size are all chosen by
whoever produced the file, which may not be this service at all.

It also breaks an invariant the rest of the service leans on. Every page here
can be recomputed from what it was rendered from, because the uuids still name
things in Redis. A comparison against an uploaded file cannot be: the file is
gone the moment it has been read.

## Decision

**The file crosses exactly one boundary, and is rebuilt on the far side of
it.** `webapp/imports.py` parses an upload into a throwaway and then assembles
a *new* result document from an allow-list - the handful of keys
`baseline.snapshot_of` reads, each type-checked, length-capped and
shape-checked. Nothing else survives the crossing. A key nobody named in
`_rebuild` cannot reach the comparison, the template or Redis, whatever the
file contains, which makes "what does a hostile file do" a question about one
module rather than about every surface downstream. Identifiers that are not
spelled the way this scanner spells its own are dropped and counted, never
repaired: a half-repaired identifier compares unequal to the real one and
reads as a finding that appeared out of nowhere.

**The arithmetic does not change.** The comparison is still
`workflows.compare_documents`, which is still the plugin's own `--baseline`
comparison. An uploaded baseline and a stored one cannot produce two different
verdicts about the same pair, for the same reason the page and the
`compare_scans` tool cannot.

**A fact a format never recorded is removed from both sides, not guessed at.**
The CSV export is a flat table of findings; two measurements live outside it -
whether an update was pending, and whether HTTPS was enforced. Both are now
written as rows, but a file downloaded before that was true is silent about
them, and silence is not the answer "no". `imports.restrict_to` neutralises
each unrecorded fact on *both* documents before they are compared, and the
page names what it left out. Removing an input is not judging one: the
arithmetic still decides what the remaining evidence means.

**What survives the request is the comparison, for five minutes.** The upload
is read once into memory and never written anywhere. The comparison drawn from
it is held under a fresh uuid4 in its own `compare:{token}:*` namespace so that
a reload and a shared link keep working. `comparisons.clamp_ttl` enforces the
ceiling, so `COS_WEB_COMPARISON_TTL` can shorten the window and cannot widen
it. The token is a capability exactly as a scan uuid is: unknown, malformed
and expired are one 404, nothing lists them, and encryption at rest applies
where a deployment asked for it.

**And it is inside the erasure, not excused from it by its own TTL.**
`DELETE /api/purge` walks the comparison namespace as well as the scan one and
deletes every cached comparison naming that instance on either side, counting
the keys into the same receipt. Five minutes is a short exemption but it is
still an exemption, and "it goes away soon" is precisely the argument
[ADR 0007](0007-erasure-on-request.md) refuses for the result the comparison
is drawn from.

**It is a browser feature and stays one.** `POST /compare` is
`include_in_schema=False`, and there is no MCP tool and no REST endpoint for
uploading a report. `compare_scans` already answers this question for an agent
from two uuids, which is the shape an agent is in a position to supply;
handing agents a file parser buys nothing and widens the one untrusted
structure in the application to a second caller.

## Consequences

**The five minutes are short on purpose and will read as too short to
somebody.** It is the window in which a reader reloads and sends a colleague
the link, not a place to keep a report. The page says so rather than leaving
it to be discovered when the link stops working, and the remedy - upload the
file again - costs nothing, because the reader still has the file and this
service never did.

**A CSV baseline is a slightly smaller comparison than a JSON one**, and one
downloaded before this decision is smaller still. This is stated on the page
rather than smoothed over. JSON is the lossless round trip; the CSV is a
spreadsheet that happens to be readable back.

**The upload has its own rate-limit bucket**, sharing the client limit's
numbers but not its counter: parsing a file costs this service work and costs
nobody else's instance anything, so it has no business spending a visitor's
scan allowance.

**`reports.csv_report` gained two rows.** Anything parsing that file by
position rather than by label will need adjusting - the rows are written with
their labels for exactly that reason.
