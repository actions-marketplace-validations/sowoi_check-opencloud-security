# ADR 0069: Login throttling is observed only when the operator asks

- Status: Proposed
- Date: 2026-09-19

## Context

An OpenCloud instance on the internet takes password guesses on every
endpoint that accepts Basic authentication. Whether anything slows those
guesses down - a proxy rate limit on the login path, fail2ban, the identity
provider itself - cannot be read from any header or document. The only way
to see it from outside is to fail a few sign-ins and watch the answers.

The scan already sends credentials in exactly one place: the demo-account
check tries the five published demo passwords against the built-in identity
provider, and only there. Sending further sign-ins is a new kind of probe.
A few failed logins are a normal event for any login page, but they are
still requests a stranger could buy against somebody else's instance through
the public web service, and they could end up in that instance's audit log.

## Decision

**The scanner can record `loginThrottling`, and only when the operator opts
in.** `scanner.check_login_throttling` (`COS_SCANNER_CHECK_LOGIN_THROTTLING`,
`--login-throttling` on the plugin and on `scan`) is off by default.

- **Six sequential failed sign-ins** go to the account endpoint the demo
  check already uses, as a random account name that cannot exist
  (`cos-throttle-probe-<random>`) with a random password. No real account can
  be locked out, and nothing resembling a guess at a password is sent.
- **Only the built-in identity provider is asked**, for the reason the demo
  check gives: an external provider belongs to somebody else.
- **It runs after every other probe.** A throttled instance answers 429 to
  what follows, and a throttled demo login must never read as a rejected one.
- **It stops at the first sign of throttling** - an HTTP 429 or a
  `Retry-After` header - and records that evidence.
- **It is an observation and is never graded.** Not being throttled is worth
  knowing, but many deployments throttle at a layer the probe cannot see
  (per IP address over a longer window, at a WAF that only reacts to more
  traffic), so a negative is weak evidence - the same reasoning as
  `reverseProxy`.
- **The web service pins it off** in `webapp/runner.py`, and a request cannot
  ask for it: a submission chooses what to scan, never whether logins are
  sent at it.

## Consequences

- Operators get a signal about brute-force protection that the scan could not
  give before, at the cost of six extra requests when they ask for it.
- The result document gains `loginThrottling`: `null` when not asked,
  otherwise `tested`, `attempts`, `throttled`, `evidence` and `statuses`.
- The instance's logs show six failed sign-ins for a name that says what it
  is. That is the point of the name.

## Alternatives considered

- **Grading it.** Rejected: a well-protected instance can look unthrottled
  from one short burst, and a grade would push operators to tune for the probe
  rather than for attackers.
- **Using the demo accounts' names.** Rejected: a lockout policy on a real
  account would then lock that account.
- **Offering it in the web service.** Rejected for the reason above; the
  plugin runs against instances its operator is responsible for.
