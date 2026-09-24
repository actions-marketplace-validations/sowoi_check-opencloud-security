# ADR 0076: A fleet summary is read from saved reports and stores nothing

- Status: Proposed
- Date: 2026-09-24
- Extends: ADR 0012, ADR 0028, ADR 0064

## Context

Somebody responsible for twenty instances has twenty checks, each answering
"is this instance broken right now". The questions a periodic review asks are
about the fleet instead: which instances run a release that receives no
fixes, which waivers run out this month, which finding fails everywhere
because it lives in a shared template, and which instance nobody has looked
at lately. None of these is visible from one host's report, and the
monitoring system shows them as twenty unrelated service states.

The obvious ways to answer them each cost something this project has so far
refused to pay. A central store of results is a database of every instance's
weaknesses that somebody must secure, back up and expire. A command that
scans the fleet again is a second scheduler beside the monitoring one, with
its own rate limits and its own idea of which hosts exist. A verdict per
fleet - "WARNING, three unsupported releases" - is a second set of thresholds
nobody configured.

Meanwhile every answer is already on disk. Operators archive the output of
`check-opencloud-scanner scan` for CI and for `diff`, and each document
carries the version, the lifecycle, the waivers with their deadlines, the
findings with their severities and, since ADR 0064, what it did not measure.

## Decision

**`check-opencloud-scanner fleet` reads result documents and nothing else.**
Files or directories, searched for `*.json`; the newest report of each host
counts, and a failed scan counts as the newest if it is. It never scans,
never writes, and keeps nothing once it has printed. Collecting the reports
stays with whatever the operator already uses.

**It measures, it does not judge.** Ratings stay the scanner's 0-5 numbers,
as in the remediation plan (ADR 0012). There is no threshold and no exit code
that depends on the state of the fleet: it exits `0` whenever it printed a
summary.

**A report is evidence about its own day, so two facts are re-measured
against today.** The recorded version is placed again in the release schedule
the installation uses, because a line that closed after the report was
written is exactly what a review must catch; end of life is permanent, so a
report that already said so always stands. A waiver deadline is compared
with now, not with the scan time, and counts only if a check would really
alert again - the rule `next_expiry` already applies to the plugin's
`--waiver-warning`. Nothing else is recomputed: findings and severities are
what the document said.

**What nobody can change is not a common finding.** Flags OpenCloud
hardcodes and the advisory headers no OpenCloud sends fail on every instance
(ADR 0028). Ranking them first on every fleet would teach the reader to skip
the list.

**Not looking is reported as a gap.** A host named by `--expect` or
`--inventory` without a report, a failed newest scan, a report older than
`--stale-after`, a report written before the coverage block, and checks not
evaluated for any reason other than "not applicable" all appear under
missing coverage rather than being read as clean.

**The HTML page fetches nothing.** It is one file with no script, font or
image, and a Content-Security-Policy that allows its own stylesheet by hash.
Every value from a report is escaped, and control characters are stripped
from every format, because a version string and an error message were chosen
by the scanned host.

## Consequences

A fleet review needs no new service, credential or storage, and runs on any
host with the package and the reports. Its answer is only as fresh as the
newest reports, which is why staleness is a section of its own.

A host is identified by name and non-default port, so an inventory has to
spell a port the way the scan reached it.

A fleet whose reports are spread over several machines has to bring them
together first; merging remote archives is deliberately out of scope.

## Alternatives considered

- **A fleet view in the web application.** It would need a listing across
  scans, which the rule that a scan's uuid is its only capability forbids,
  and it would keep strangers' results together in one place.
- **Rescanning every host.** Duplicates the monitoring schedule and its
  per-host settings, and turns a read into load on every instance.
- **A persisted fleet database fed by the plugin.** A new store of sensitive
  results to secure and expire, for information the archived documents
  already hold.
- **A WARNING/CRITICAL exit for the fleet.** Unconfigured thresholds; the
  per-host checks already alert with the thresholds the operator chose.
