# ADR 0071: OpenCloud's repository advisories are a second advisory source

- Status: Proposed
- Date: 2026-09-19
- Extends: ADR 0017

## Context

[ADR 0017](0017-the-advisory-database-refreshes-itself.md) made the advisory
database refresh itself from OSV, which aggregates GitHub's global advisory
database and the Go vulnerability database. That relies on OpenCloud's
advisories reaching GitHub's global database.

They don't always. OpenCloud published GHSA-gf4p-7p27-26w7 (CVE-2026-57500,
"Access to internal metadata", fixed in 4.0.8 and 7.2.0) on 2026-07-03 as a
repository advisory only. GitHub's global database answers 404 for it and OSV
answers "not found", so the daily refresh never saw it. Every release of this
project shipped without it, and an instance on 4.0.7 or 7.1.x was rated free
of known advisories: the silent pass ADR 0017 exists to prevent.

The repository advisories are published at
`api.github.com/repos/opencloud-eu/opencloud/security-advisories`. The endpoint
needs no token, and this project already calls api.github.com for releases and
attestations. But the data in it is written by hand:

- `vulnerable_version_range` can be prose (`stable releases 4.0.x`,
  `rolling releases <= 5.0.1`).
- An advisory fixed on two release lines is written as `< 4.0.8, < 7.2.0`.
  The existing GitHub parser in `vulndb._parse_range` reads that as one range
  where the last bound wins, which would flag the fixed 4.0.8.

## Decision

**The repository advisories are read as a second source, after OSV.**
`advisory_source.fetch_advisory_document` takes an optional `repository_url`.
With it, `fetch_repository_records` reads the repository advisories and
`parse_repository_advisory` converts them. The daily
`scripts/update_vulnerability_db.py` passes `REPOSITORY_ADVISORIES_URL` by
default (`--repository-url ''` skips it). The web application reads it on
every refresh unless `COS_WEB_ADVISORY_REPOSITORY_URL=off`; the variable may
also point at a mirror.

**OSV stays primary.** A repository advisory whose GHSA or CVE id OSV already
answered with, as an id or an alias, is skipped. OSV's structured ranges are
never merged with the hand-written ones.

**Ranges are read strictly.** `repository_ranges` accepts only a
comma-separated list of operator/version pairs:

- Several upper bounds alone are one range per release line. `< 4.0.8,
  < 7.2.0` becomes "1.0.0 up to 4.0.8" and "4.1.0 up to 7.2.0". Each later
  range starts at the release line after the previous fix. A missing lower
  bound becomes 1.0.0, OpenCloud's first release, so a version older than
  anything OpenCloud shipped stays outside every advisory.
- Anything with prose in it yields nothing. An advisory with no readable
  range is dropped, as ADR 0017 already requires for unbounded records.
- Withdrawn, unpublished and non-OpenCloud entries are dropped.

**A failure in the second source never fails a refresh.** If the repository
feed cannot be read (rate limit, outage), a warning is logged and OSV's answer
is kept. ADR 0017's rule that a refresh only ever gains knowledge is unchanged.

**The missed advisory is also in the bundled database**, written by hand with
the ranges this parser derives, so it reaches installations that never refresh.

## Consequences

- An advisory OpenCloud publishes only on its repository reaches the database
  within a day, and the web service picks it up at its next refresh.
- The plugin's own `refresh-data` path is unchanged. By default it installs
  the signed database this project's workflow builds, which now includes
  repository advisories. A custom unsigned feed URL still reads OSV only.
- Unauthenticated GitHub API calls are limited to 60 an hour per address; one
  call a day is well within that. A deployment behind an egress allowlist
  needs api.github.com, which it already needs for release checks.
- A repository advisory written only in prose is still missed. That stays a
  gap to catch by hand: the parser won't guess.

## Alternatives considered

- **Replace OSV with the repository feed.** Rejected: OSV also carries the Go
  database's entries and structured ranges, and GitHub's global database is
  reviewed. The repository feed covers only what OpenCloud writes itself.
- **Reuse `vulndb._from_github` for the repository feed.** Rejected: it
  reads two upper bounds as one range (a false positive on 4.0.8) and takes
  the `<= 5.0.1` out of `rolling releases <= 5.0.1`, which as one unbounded
  range would flag every 4.0.x release from 4.0.3 on.
- **Add missed advisories by hand only.** Rejected as the only fix, because
  it depends on somebody noticing, as happened this time. The bundled entry is
  kept alongside the automatic source.
- **Ask OpenCloud to request GitHub review of its advisories.** Worth doing,
  but outside this project's control and no guarantee for the next one.
