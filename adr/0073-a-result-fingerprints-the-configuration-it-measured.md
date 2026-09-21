# ADR 0073: A result fingerprints the configuration it measured

- Status: Proposed
- Date: 2026-09-21
- Extends: ADR 0013, ADR 0057, ADR 0064, ADR 0066

## Context

A grade answers "is this instance in good shape". It does not answer "is this
still the instance you looked at last week".

Plenty of deployment changes move no grade at all. A content security policy
is rewritten without gaining or losing `unsafe-inline`. A reverse proxy is
replaced with a different product that sets the same headers. Public links
stop requiring a password on Monday and require one again on Thursday. The
certificate moves to a different issuer. An identity provider is swapped for
another one that is configured just as well. Each of those is something an
operator would want to know about - a change nobody remembers making is how an
incident starts - and each of them leaves a result document that reads exactly
like the one before it.

A scan could record the configuration itself and let a reader diff it. It must
not. The result document is published: it is rendered on a public web page,
attached to tickets, posted to webhooks and uploaded to the comparison
endpoint by strangers. A content security policy names the origins a
deployment trusts, an OpenID discovery document can name a tenant, a
capabilities document carries a deployment's own vocabulary, and a server
banner names an internal build. None of that is ours to publish.

## Decision

**A result records a `configuration` block: grouped digests of how the
deployment is configured, and nothing it is configured to.** Five groups -
`tls`, `headers`, `sharing`, `authentication`, `proxy` - plus one digest over
the five. Each group carries a digest, a scope (below), and how many facts
went into it.

**Digests only, never the configuration.** Every fact is hashed into its group
and discarded. A reader learns *that* sharing changed, never *what* it is set
to. This is what makes the block safe on a public page, in a webhook and in an
uploaded report alike.

**Groups are the questions an operator asks.** "Did TLS change?" is useful;
"did fact 37 change?" is not. Five group digests turn a hash into a sentence.

**Only what the deployment decides.** The transport group hashes the issuer,
the key, the signature algorithm and the negotiated protocols, and leaves the
serial number, the validity dates and the certificate fingerprint alone,
because a renewal is routine and a fingerprint that moved every ninety days is
one an operator learns to ignore. The proxy group hashes the vendor, not the
server banner, which carries a build number that moves with every patch.

**A scan's own settings are never a fact.** Each group carries a second
digest, its **scope**: which facts it was able to look at, without their
values. Two groups are compared only when their scopes match, so a run that
stopped inspecting TLS reports "not comparable" rather than drift, and a group
with nothing to hash at all is `none`. Without this, the first run with a
probe turned off would report a redeployment.

**It never changes a grade.** Nothing in the block reaches the rating, the
severities, the alert line or the exit code, and drift never makes a
`--baseline` run regress. The checks decide what is wrong; this only says what
moved. An exit code that changed because a header was reworded would make the
fingerprint the noisiest thing in the plugin.

**A report that has no fingerprint says so.** `fingerprint.fingerprint_of`
returns `None` for a missing or malformed block, every reader asks through it,
and a comparison reports a limitation. "This report cannot say" and "this
deployment did not change" are different answers, as they are for coverage
(ADR 0064) and provenance (ADR 0066).

**An uploaded report's block comes through the same allow-list.** ADR 0057
holds: `webapp/imports.py` rebuilds `configuration` group by group, keeping
only our own group names and only values shaped like one of our digests. An
upload cannot introduce a group, and it cannot smuggle a configuration value
in where a digest belongs.

## Consequences

The result document gains one additive key, `configuration`, with its own
schema number; nothing existing changed meaning. The webhook payload and
`--format json` gain a `configuration` object of digests, `null` for a scan
that recorded none.

A baseline snapshot gains the group digests, so `--baseline` can report "no
new findings, but the configuration changed (headers)". A baseline file
written before this exists loads as before and reports no drift, which is the
honest answer for a file that cannot say.

`changes.explain` gains a `configurationChanged` change in the `instance`
category, and a limitation for groups the two scans looked at differently.
`check-opencloud-scanner diff` and the web comparison both get it, because
both call the same function.

The digests are not portable between scanner versions by construction: adding
a fact to a group changes that group's scope, and a comparison across such a
change reports "not comparable" rather than inventing drift. That is the
intended behaviour, and it is why the scope exists.

Accepted ADRs are historical records: do not rewrite their decision. When a
decision changes, add a new ADR and mark the older record as superseded.
