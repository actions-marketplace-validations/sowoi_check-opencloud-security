# ADR 0052: The probe guard counts networks, and a deployment may scan approved instances only

- Status: Accepted
- Date: 2026-09-14
- Extends: ADR 0051

## Context

ADR 0051 blocks a client address whose scans keep finding no OpenCloud. Left
there, it had gaps that cost a prober nothing to walk through: an IPv6
subscriber owns a /64 and can use a new address per scan; the next IPv4
address in a hosting customer's range is a fresh client; a block that ends is
forgotten; walking private ranges through the form was refused but never
counted; a patient client stays under the per-minute limit indefinitely; a
wildcard DNS name reaches whatever address it spells; and a host that
answered "not OpenCloud" over HTTPS was still asked twice more. Some
deployments also want no public scanner at all.

## Decision

- **Clients are networks where an address is not a client.** Every limit
  counts an IPv6 client as its /64. The probe guard also counts an IPv4 /24;
  the per-minute and daily limits keep counting single IPv4 addresses, because
  strangers sharing a /24 should not share capacity. Both prefixes are
  settings. A full-length prefix keeps the plain address, so existing keys
  are unchanged.
- **Blocks escalate.** The block is claimed with `SET NX` at the first
  block's length, then the repeat counter decides the real length - six times
  the previous, up to `COS_WEB_PROBE_BLOCK_MAX` - so concurrent strikes start
  one block and escalate once. The counter lives until the repeat window after
  the block *ends*. Strikes during a block change nothing.
- **Refused targets are strikes** when the refusal is about what the target
  points at (`SUSPICIOUS_REJECTIONS` in `webapp/ssrf.py`); typos, unresolvable
  names and malformed input are not.
- **A daily cap** per client, counted like the per-minute limit.
- **Misleading names are refused by the guard.** A fixed list of wildcard and
  rebinding DNS services, wherever the SSRF guard applies unless private
  targets are allowed; and a submission's name resolved twice, refused when the
  answers share nothing, with both answers checked. The worker and the
  redirect guard keep their single, pinned lookup.
- **The scanner can stop at a foreign answer.** `NotOpenCloud` separates "it
  answered, and not as OpenCloud" from silence, and
  `ScannerSettings.stop_when_not_opencloud` ends the scan at the first such
  answer. The web service sets it; the plugin's behaviour is unchanged. This
  is a measurement option in the scanner, not a probe issued by `webapp/`.
- **Approval mode** (`COS_WEB_REQUIRE_APPROVAL`) scans listed instances, or
  instances whose zone publishes a TXT record naming this service's hostname.
  The record approves one deployment, needs no secret, and is read from the
  system resolver only (ADR 0024). A failed lookup refuses. It is checked at
  submission and runs off the event loop.
- **The operator's area counts the guard**: active blocks by counting block
  keys, and day-stamped counters for blocks, strikes and daily caps. No key,
  fingerprint or address is returned.
- **Every number is an environment variable** and a question in the Docker
  setup wizard, written to the container that reads it.

## Consequences

A prober needs many networks, not many addresses, and pays more each time it
returns. An office behind one /24 in which somebody probes shares that block;
`COS_WEB_PROBE_IPV4_PREFIX=32` narrows it. A rotating DNS pool whose lookups
return disjoint sets is refused until `COS_WEB_DNS_CONSISTENCY_CHECK=false`. A
legitimate instance under a wildcard DNS service must be submitted by address.
Approval mode turns the service into an opt-in scanner; approval revoked while
a scan is queued does not stop that scan.

## Alternatives considered

**A /24 for the per-minute limit** was rejected: capacity limits punish
bystanders, abuse limits punish the network that earned them.

**A pre-flight `status.php` request from `webapp/`** was rejected as a second
implementation of the scanner's first step in the wrong layer; the scanner
already asks `status.php` first and only needed to stop retrying.

**A per-deployment secret in the approval record** was rejected: it would have
to be handed to every instance owner, and the hostname already binds the
record to one deployment.
