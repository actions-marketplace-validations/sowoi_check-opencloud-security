# ADR 0051: A client that keeps scanning hosts that are not OpenCloud is blocked

- Status: Accepted
- Date: 2026-09-14

## Context

The public service takes an address from a stranger and connects to it. The
SSRF guard keeps it off private networks, the client limit keeps one visitor
from filling the queue and the target cooldown keeps one instance from being
hammered - but none of them notices somebody feeding it a list of public
addresses to learn which of them answer, and with what. Every such scan is
cheap for the prober, costs somebody else a set of requests from this
service's address, and ends with a failed scan that says what was found
instead of OpenCloud. That is a host scanner with extra steps.

What distinguishes the misuse is not the address, which cannot be judged
before connecting, but the outcome: somebody checking their own instance gets
a result, somebody sweeping gets failure after failure.

## Decision

A client address whose scans find no OpenCloud `COS_WEB_PROBE_LIMIT` times
(default 5) within `COS_WEB_PROBE_WINDOW` (300 seconds) is refused for
`COS_WEB_PROBE_BLOCK` (3600 seconds).

- **The outcome decides, and the worker counts.** A strike is a scan that ends
  in the scanner's own `ScanError` - `status.php` unreachable, not JSON, no
  version, another product - or in the job timeout. A completed scan never
  counts, whatever its grade, and neither does a target the SSRF guard or an
  exclusion refused: that is this deployment's policy, not a stranger's probe.
- **The same host counts every time.** Asking one address repeatedly whether
  it has started answering is probing as much as a list is.
- **The fingerprint travels with the scan, the address never does.** The API
  derives the same truncated HMAC the client limit uses and stores it under
  `scan:{uuid}:prober`, apart from the metadata the uuid holder reads back.
  The worker reads and deletes it when the scan starts. The pepper may be per
  process, so the worker could not derive it itself.
- **The API only reads the block**, before the client limit, so refusals
  during a block do not also spend the allowance the visitor returns to.
- **It is a rate limit, with the rate limit's manner**: 429, `Retry-After`, the
  self-host pointer, `rate_limit_probe` in the audit trail.
- **The workflow layer does not sleep through it.** A `Retry-After` longer than
  `SUBMIT_MAX_WAIT_SECONDS` (300) goes back to the caller as not retryable,
  so an agent tells its user rather than appearing to hang for an hour.

## Consequences

Sweeping addresses through the service now costs an hour per five misses per
client address. An operator whose own instance is down, or who mistypes it
five times, meets the block too; the message says why and offers the local
scanner, and `COS_WEB_PROBE_LIMIT=0` switches it off for a deployment that
scans only its own hosts.

A client with many addresses still gets many allowances, as with every other
per-address limit here. A deployment with several web processes must share
`COS_WEB_RATE_LIMIT_SALT`, as it already must for the client limit.

For the time a scan waits in the queue, the store holds a fingerprint next to
a target. It is the fingerprint the rate-limit keys already hold, it is never
returned, it is removed by an erasure request, and it is gone once the scan
starts.

## Alternatives considered

**Counting distinct hosts only** was rejected at review: it leaves one address
free to be polled indefinitely once the cooldown lifts.

**Judging the address before scanning** - reverse DNS, a name pattern, a
pre-flight request - was rejected: the first two guess, and the third is the
same connection with the verdict moved earlier.

**Recording the strike from the API when a result is read** was rejected: a
prober never has to read a result.
