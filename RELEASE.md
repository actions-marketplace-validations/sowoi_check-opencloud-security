## check-opencloud-security 1.23.0

### Added

- **The operator area has a Rules tab.** `/admin/rules` documents how a grade
  is decided - the scale, the scanner's severity ceilings, the end-of-life and
  track overrides, whether extra checks count, the waivers a visitor may
  choose, and the advisory database and release schedule rated against - and
  every rule enforced against a request: the per-client, daily and per-target
  limits, the probe block with its strikes, network scope and escalation, the
  SSRF guard's refused ranges, names and wildcard DNS services, approval mode,
  the flags every scan runs with, and the credential and refresh limits. Each
  rule is marked enforced or off and names its `COS_WEB_*` variables. Nothing
  is restated: every number and list is read from the running settings and
  the constants of the code that enforces it, and the page names no target,
  uuid or client.
- **The operator area has a Configuration tab.** `/admin/configuration`
  lists every `COS_WEB_*` variable the web service reads, grouped, with the
  value in effect after parsing, whether the environment set it or the default
  applies, and the documented default and description from `docs/webapp.md`.
  Credentials - tokens, signing keys, salts, the admin proxy secret and the
  password in `COS_WEB_REDIS_URL` - are shown only as set or not set; for
  `COS_WEB_ENCRYPTION_KEY_<n>` only the versions present are named. `COS_WEB_*`
  names the service does not recognise are listed without their values, so a
  misspelt variable is noticed instead of silently leaving the default in
  force. `scripts/build_frontend_documentation.py` now also generates
  `webapp/environment_reference.py` from the documentation table, and
  `COS_WEB_IPV6_ENABLED` and `COS_WEB_WEBHOOK_SECRET` are documented there for
  the first time.
- **The web service blocks a client that keeps scanning hosts that are not
  OpenCloud.** Five scans from one client address that find no OpenCloud -
  nothing answering on `status.php`, something that is not JSON, another
  product, or no answer in time - within five minutes block that address for
  an hour; the same host scanned again counts again. A blocked submission
  answers 429 with a `Retry-After` of the rest of the block, the usual pointer
  to running the scanner locally, and `rate_limit_probe` in the audit trail.
  Only the worker learns the outcome, so a submission hands it the client's
  rate-limit fingerprint, never the address, under `scan:{uuid}:prober`, and
  the worker deletes it as soon as it starts the scan. Tuned with
  `COS_WEB_PROBE_LIMIT`, `COS_WEB_PROBE_WINDOW` and `COS_WEB_PROBE_BLOCK`,
  which the web service and the worker both read; `COS_WEB_PROBE_LIMIT=0`
  turns it off. MCP and the workflows now wait out a `Retry-After` of at most
  five minutes by themselves and hand a longer one back to the caller instead
  of sleeping through it. See ADR 0051.
- **The probe block counts networks, grows when it is earned again, and counts
  refused targets.** An IPv6 client is one /64 for every limit
  (`COS_WEB_CLIENT_IPV6_PREFIX`), so rotating through a subscriber's own
  addresses no longer resets anything, and the probe block covers an IPv4 /24
  (`COS_WEB_PROBE_IPV4_PREFIX`) so the next address along cannot step around
  it; the per-minute limit still counts single IPv4 addresses. A block earned
  again within `COS_WEB_PROBE_REPEAT_WINDOW` of the last one lasts six times
  longer - an hour, six hours, a day - up to `COS_WEB_PROBE_BLOCK_MAX`. A
  submission the guard refuses for what it points at - a private or internal
  address, an exclusion, a misleading DNS name, an unapproved instance - is a
  strike too; a typo or an unresolvable name is not. See ADR 0052.
- **A daily cap per client.** `COS_WEB_DAILY_SCAN_LIMIT` (default 50) refuses
  the patient version of a burst with 429, `rate_limit_daily` in the audit
  trail and the usual self-host pointer.
- **Wildcard and rebinding DNS names are refused, and a name must resolve the
  same way twice.** Names under `nip.io`, `sslip.io`, `xip.io`, `traefik.me`,
  `localtest.me`, `lvh.me`, `vcap.me`, `lacolhost.com`, `localhost.direct`,
  `local.gd`, `rbndr.us` and `1u.ms` are refused by name wherever the SSRF
  guard applies. A submitted name is looked up twice and refused when the
  answers share no address, with every address from both held to the guard
  (`COS_WEB_DNS_CONSISTENCY_CHECK`).
- **Approval mode.** `COS_WEB_REQUIRE_APPROVAL=true` scans only instances in
  `COS_WEB_APPROVED_TARGETS` or, with `COS_WEB_APPROVAL_DNS`, instances whose
  zone publishes `_check-opencloud-security.<host> TXT
  "check-opencloud-security=<this service's hostname>"`; anything else is a
  403 and `target_not_approved` in the audit trail. A mode that could approve
  nothing, or a list entry that does not parse, refuses startup.
- **The operator's area has an Abuse guard tile**: networks blocked now, and
  blocks, strikes and daily caps reached over seven days, as counts only.
- **The Docker setup wizard asks for every abuse limit** in a new *Abuse
  protection* section and writes them to both containers.
- **`ScannerSettings.stop_when_not_opencloud` and `NotOpenCloud`.** A
  `status.php` answer that is not OpenCloud now raises `NotOpenCloud`, a
  subclass of `ScanError`. With the setting on, the scan stops there rather
  than asking again without certificate verification and over plain HTTP;
  the web service turns it on, and the plugin's default is unchanged.

### Security

- **The scan service refuses a request not addressed to loopback when it has
  no token.** `check-opencloud-scanner serve` on its default `127.0.0.1` bind
  with no token answered any `Host`, so a web page open in a browser on the
  same machine could point a hostname of its own at `127.0.0.1` (DNS
  rebinding), read every answer as same-origin, and use `/api/scan` - which
  has no target guard - to scan and report back what the operator's network
  holds. Without a token a request must now name `localhost`, a `127.0.0.0/8`
  address or `::1`, or it is answered 403; a service with a token is
  unaffected, since a page cannot know it.
- **`POST /api/scans/batch` refuses a cross-site submission like the single
  one does.** It was the one public POST without the `Sec-Fetch-Site`/`Origin`
  check, and it parses its body as JSON whatever the `Content-Type` says, so a
  foreign page's `text/plain` form - which needs no preflight - could queue a
  batch of scans from a borrowed browser, spending that visitor's allowance
  and, with the probe guard, earning their address a block.
- **The operator area accepts a write only from its own origin.** Its three
  POSTs took the public pages' check, which lets `same-site` through, and a
  sign-in cookie is sent on a same-site request - so a page on any sibling
  subdomain, the identity provider's or an OpenCloud instance's among them,
  could add or withdraw exclusions and press the refreshes with the
  operator's session. `/admin` now requires `Sec-Fetch-Site: same-origin`
  (or `none`), or an `Origin` of this service where that header is absent.
- **A non-ASCII `X-COS-Admin-Proxy` header is refused with 404 instead of
  crashing with 500.** The secret was compared as `str`, which raises on
  characters outside ASCII; the 500 differed from the 404 an area that is off
  answers, and told a prober from outside that `/admin` was switched on. It is
  now compared as bytes, as the erasure token already was.
