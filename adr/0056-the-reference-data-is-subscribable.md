# ADR 0056: The reference data is subscribable

- Status: Accepted
- Date: 2026-09-16

## Context

Two documents in this service refresh themselves daily and may only ever gain
knowledge: the advisory database ([ADR 0017](0017-the-advisory-database-refreshes-itself.md))
and the release schedule ([ADR 0016](0016-the-release-schedule-refreshes-itself.md)).
They are the reason a scan run today grades an instance more harshly than the
same scan a month ago, and they are public - nothing in either is about
anybody's instance.

Until now the only way to learn that a new advisory had arrived was to open
`/catalogue` and remember what had been there before. Nobody does that. The
people who most need to know - operators of the instances the database is
about - have no way to be told short of scanning again and reading the result,
which inverts the point: the database changed, not their instance.

## Decision

`/advisories.atom` and `/release-schedule.atom` publish the two documents as
Atom 1.0 feeds, built by `webapp/feeds.py` from the same functions the pages
use - `advisory_catalogue()` and the `ReleaseSchedule` a scan is rated
against - so a feed and the page describing the same advisory cannot drift
apart. No new data, no new fetch, no new state: a feed is a second rendering
of what this service already holds in Redis.

**They opt into `public, max-age=3600`.** ADR 0031 makes `no-store` the
default and reserves the cache opt-in for routes publishing metadata about
*this service*. These qualify on exactly that test: they name no instance,
carry no uuid, take no parameter and read no request state beyond the origin
they are being served from - the same class as the sitemap and the contracts.

**Advisory text is carried as `type="text"`, escaped.** Titles and
descriptions come from a public feed this project does not control, and a
reader that rendered them as HTML would be running somebody else's markup in
an application nobody here inspected. The feeds are English, like every other
machine-readable document (ADR 0020).

**Entry ids are URNs of the thing, not URLs of this service**
(`urn:check-opencloud-security:advisory:<id>`), so a reader's history survives
a deployment moving host or a visitor following a different mirror.

## Consequences

Every advisory entry carries the *database's* refresh date rather than a
publication date of its own, because the database has never recorded one per
advisory - `data/vulnerabilities.json` dates the file, not the entry. A reader
should treat the advisory feed as "what is known", not as a timeline, and a
refresh that gains one advisory restamps them all. Recording a first-seen date
per advisory would mean changing the document's shape and the acceptance
rules ADR 0017 fixed; it is worth doing if this feed becomes load-bearing, and
not worth doing speculatively.

The release schedule's entries date themselves by the line's release date,
which does not move, so that feed behaves like an ordinary one.

The feeds are two more public, unauthenticated surfaces. They are also two
more surfaces that must never learn to take a parameter: a feed filtered by
version, track or hostname would be a question about somebody's instance, and
this is the one part of the service where that has never been possible.

## Alternatives considered

**One combined feed.** Fewer routes, but an advisory and a release line are
different kinds of news with different cadences, and a subscriber who wants
security notifications does not want to be told a rolling release shipped.

**Email notifications.** An address is personal data, a subscription is state
this service would have to keep and honour, and unsubscribing becomes a
security-relevant workflow. A feed is the same information with no account, no
address and nothing stored.

**A webhook operators register.** Same objection, plus outbound requests to
addresses strangers name - which is the shape of an SSRF amplifier, and
exactly what the guard in front of scanning exists to prevent.
