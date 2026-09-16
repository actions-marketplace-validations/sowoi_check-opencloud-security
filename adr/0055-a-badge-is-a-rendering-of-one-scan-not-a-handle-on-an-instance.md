# ADR 0055: A badge is a rendering of one scan, not a handle on an instance

- Status: Accepted
- Date: 2026-09-16

## Context

A grade is the one thing about a scan that fits in a picture, and a picture
travels where a link does not: a ticket, a chat message, a status page, a wiki
column. The web application already renders a finished scan four ways
(ADR 0006), all of them files somebody downloads. An image is different in one
respect that matters here - it is fetched by browsers nobody asked, from pages
this service did not write.

Two things about badges are conventional and both are wrong for this service.
The first is to fetch them from a badge service, which would hand that service
the result URL in a `Referer` on every view, and the uuid in that URL is the
entire authorisation for the full result. The second is to address a badge by
the *thing* it describes - `/badge/opencloud.example.com.svg` - which is how
every badge in a README works, and which here would be a permanent, guessable
handle on somebody else's instance: the listing endpoint this service does not
have, arriving as an image.

## Decision

**The badge is addressed by uuid and behaves like every other reading of one.**
`GET /api/scans/{uuid}/badge.svg` answers 404 for unknown, invalid and expired
alike, 409 while the scan has not finished, and carries the scan's TTL by
carrying the scan. There is no badge for a hostname, no badge for a target
and no way to ask for one without already holding the uuid.

**It is rendered here, in `webapp/badge.py`**, as a self-contained SVG with no
script, no external font, no stylesheet and no URL that anything fetches - the
same bargain `reports.py` makes for the PDF, for the same reason the frontend
loads nothing from a CDN.

**It carries nothing the scanned instance chose.** Not the hostname, not the
product string, not the version - three fixed words and a letter. A rendering
assembled entirely from our own text needs no argument about what somebody
else's server put in a header, and it means the image cannot quote an instance
to a reader who never scanned it.

**It keeps `no-store`.** Every route that opts into a public cache publishes
metadata about *this service* ([ADR 0031](0031-a-response-is-uncacheable-until-a-route-opts-in.md));
a badge is a statement about somebody's instance, which is the case that rule
exists for.

The grade and its colour come from `catalog.rating_label` and
`catalog.rating_tone`, so the badge, the dial on the result page and the letter
in an export cannot disagree - the judging stays the plugin's
(`RATE_MAP`), as everywhere else in `webapp/`.

## Consequences

**A badge lasts as long as its scan: one hour by default.** This is the whole
of the cost, and it is deliberate rather than an oversight to fix later. The
obvious feature request - a badge in a README - is *not* served by this
endpoint, and the documentation says so plainly instead of letting somebody
discover it when the image breaks. Serving it properly would mean a permanent
handle on an instance, which is the thing this decision refuses.

Where a README badge is genuinely wanted, the answer is the same one the rate
limit already gives: the whole check is open source and runs on the operator's
own machine. A badge rendered by the plugin, into a file the operator commits
or publishes, depends on nobody's uptime, nobody's TTL, and publishes no uuid.
That is a plugin-side format and is not built here; ADR 0026 already records
why such a renderer would be the plugin's own rather than an import of
`webapp/`.

Publishing a badge URL publishes the uuid with it. That is true of the result
URL too, and is the visitor's decision to make, but an image invites pasting
in a way a link does not - so both the API description and the operator
documentation say it outright.

## Alternatives considered

**`/badge/{hostname}.svg`, the conventional shape.** A permanent handle on an
instance nobody has to have scanned, enumerable by anybody with a wordlist,
and a listing endpoint in everything but name. It also cannot answer without
either serving a stale verdict or scanning on demand for whoever loaded the
image, which would make every page carrying one a way to make this service
scan.

**Shields.io, or any badge service.** One request per view to a third party
carrying the result URL as a referrer. The prohibition in `AGENTS.md` names
Google, Meta and Twitter/X specifically, but the reasoning - a visitor hands
us the address of a system they are responsible for - rules this out on its
own merits.

**A `?style=` or `?label=` parameter.** A request may choose what to scan,
never how hard; here it would also mean a caller choosing text that this
service then renders into an image served from its own origin. Three fixed
words cost nothing and answer no questions.

**Opting into a short public cache.** Tempting for an image, and exactly what
ADR 0031 set the default against: a shared cache holding a statement about
somebody's instance, keyed by a URL whose uuid is the authorisation.
