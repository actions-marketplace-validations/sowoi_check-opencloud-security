# ADR 0072: Remediation verification re-measures named findings without a full scan

- Status: Accepted
- Date: 2026-09-19

## Context

An operator who changes one reverse-proxy setting - adds
`Strict-Transport-Security`, stops serving `/.env` - wants to know whether
that fixed the finding. The only answer so far was a full scan: every probe,
the update check, the advisory database, TLS and DNS lookups. That is slow,
noisy in the instance's logs, and answers a much larger question than the
one asked.

## Decision

**A new library function measures, the plugin judges.**
`opencloud_local_scan.verification.verify(host, finding_ids, settings)` maps
each finding id to the probe group that produces it (`probe_group`), runs
each needed group once, and returns a document with one entry per id:
`verifiable`, `passed`, the `checks` that answered it and a `reason`. It
never rates, applies waivers or picks an exit code - the layer boundary of
the scanner stays as it is.

**The probes are the scanner's own.** `verify` calls the same private
functions `scan()` uses (`_check_headers`, `_exposed_path_findings`,
`_cors_finding`, ...) with the same arguments, and reaches the instance
through `_open_instance`. A check verified here cannot disagree with the next
full scan; a test compares the two.

**Ids are the ones the full output already reports.** Headers, hardening
flags, advisory checks and extra-check ids work as they are; a family root
(`exposed`, `authentication`, `debugEndpoint`, `debugPort`,
`versionDisclosure`) covers every member.

**What needs the whole picture is not verifiable.** `eol`,
`vulnerability:*`, `httpsAvailable`, `addressParity` and `tlsAddressParity`
depend on the version, the release schedule, the connection fallback or
every resolved address. They - and any id the build does not know - are
reported as not verifiable, never guessed.

**The plugin flag `--verify-remediation`** (repeatable, comma-separated)
judges the document: `OK` when every id passes, `CRITICAL` when a still
failing check is high or critical severity, `WARNING` for any other failure,
`UNKNOWN` when an id could not be verified. `--format json` prints the
document. It produces no rating and never touches a baseline or a webhook.

## Consequences

- A fix can be confirmed in seconds, with a handful of requests.
- `verification.py` imports private scanner functions; renaming one of them
  now has a second caller to update. The mapping tables (`_CHECK_GROUPS`,
  `_FAMILIES`) must gain an entry when a new extra check is added, or the new
  id reports as not verifiable - safe, but worth adding to
  `/add-hardening-check`.
- The flag is excluded from the Icinga CheckCommands: it is a one-off check
  after a change, not a recurring service.
- The web application does not offer it; a request still chooses what to
  scan, never how much.

## Alternatives considered

- **A full scan filtered to the requested ids.** Correct by construction but
  exactly as slow as the scan it was meant to replace.
- **A `checks=` setting on `scan()` that skips groups.** Would thread a
  subset through a 500-line function whose coverage, rating and remediation
  plan all assume a complete measurement, and would produce result documents
  that look complete but are not.
- **Applying waivers and a rating to the subset.** A partial measurement is
  not a state of the instance; rating it would invite comparing it with full
  scans.
