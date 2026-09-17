# ADR 0065: A waiver may carry a reason and a deadline

- Status: Accepted
- Date: 2026-09-17

## Context

`--ignore-hardening` suppresses the alert for a failing check. It is the right
tool for a finding that is real but not actionable here - a CSP that cannot be
tightened without breaking the web UI, an HSTS header the reverse proxy owns.

It has two gaps, and they compound. It records no reason, so the next person
to read the configuration cannot tell a deliberate architectural decision from
something switched off during an incident. And it never ends. A waiver added
for "two weeks, until the firewall change" is still there a year later, the
check is still failing, the alert is still suppressed, and the change shipped
months ago. Nobody removes it because nothing reminds anybody it is there.

The failure mode is the worst kind: silent, and it looks exactly like success.

## Decision

**A waiver may be written as `pattern|expires|reason`.** The pattern matches
as it always has - case-insensitive, shell-style wildcards, so `debugPort:*`
still covers a generated family. `--waive-until` takes these records,
repeatably, and `COS_SCANNER_TEMPORARY_WAIVERS` / `scanner.temporary_waivers`
configure the same thing.

**A bare pattern is still a permanent waiver.** `--ignore-hardening`,
`SCANNER_IGNORE_HARDENINGS` and every existing configuration keep working and
keep meaning exactly what they meant. Internally both forms become the same
record type, one of them with no deadline.

**An incomplete temporary record is refused, never made permanent.** The
expiry must parse as ISO 8601 *and* carry a timezone; the reason may not be
empty. A record missing either raises rather than degrading, because failing
open is how a typo becomes a suppression that outlives everybody who knew
about it. A naive timestamp is refused rather than assumed to be UTC or local:
the two readings are hours apart and the difference decides whether an alert
fires.

**Expiry is decided once, against one clock, in UTC.** The scan reads the
clock at the start and every record is resolved against that moment. The
boundary is `now >= expires_at`: at the stroke of the expiry the waiver is
over, because somebody who writes `2026-12-31T00:00:00Z` means the waiver
covers the year rather than the first instant after it. A scan that re-read
the clock could waive a check at the top and alert on it at the bottom.

**Any active record suppresses; every applicable record is reported.**
Waivers are permissions, and one permission is a permission - so a broader
active record covers a check whose own specific waiver has expired. That is
the right behaviour and the wrong thing to leave unsaid, so the result
document lists every record that applies to a check, expired ones included,
and `WaiverDecision.only_covered_by_a_wildcard` names the case. A permanent
`*` sitting in a configuration file cannot silently absorb the expiry of
everything underneath it.

**A waiver still never touches the evidence.** Only failing checks can be
waived; a waiver for something that passes is a blind spot waiting for the day
it fails, and is not applied. Findings are flagged, never removed. End of life
is still an F under an active wildcard. None of this changes with a deadline
attached.

**This release is configured from the CLI and configuration files only.** The
public web service takes waivers as a request field, and those are
session-scoped choices a stranger makes about one scan - a deadline means
nothing there. Offering temporary waivers as a request field, or an editor in
the operator area, is a separate decision with its own storage and
authorisation questions.

## Consequences

The result document gains `waivers`: every configured record with its reason,
expiry, state and what it matched. `ignored` stays a flat list of identifiers,
so existing readers are unaffected. A record that matched nothing appears too -
that is usually a pattern whose finding no longer exists, which is how a
waiver outlives its reason.

`_apply_waivers` takes the scan's clock and returns the report alongside the
identifiers. It is private, and its callers in the scanner and the tests moved
with it.

Reasons are operator-supplied text and are treated as untrusted wherever they
are rendered. In the web application that is Jinja's autoescaping, which
already covers every other scan-derived string on the page.

An operator who wants the old behaviour does nothing: the old flag is
unchanged. An operator who adopts the new one gets an alert back on the day
they said they would, which is the entire point.
