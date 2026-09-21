# Sécurité des cookies

Le scanner inspecte les en-têtes `Set-Cookie` dans les réponses publiques pour quatre cookies
protections. Il lit les attributs définis par OpenCloud ou son proxy inversé et ne
conserver les valeurs des cookies.

If the response sets no cookies, these checks are omitted. An unperformed check is not
reported as a pass.

<!-- TOC -->
* [Cookie attributes: what this scanner checks, and why](#cookie-attributes-what-this-scanner-checks-and-why)
  * [1. Does the cookie require HTTPS: `cookieSecure`](#1-does-the-cookie-require-https-cookiesecure)
  * [2. Can page scripts read the cookie: `cookieHttpOnly`](#2-can-page-scripts-read-the-cookie-cookiehttponly)
  * [3. Is the cookie sent on cross-site requests: `cookieSameSite`](#3-is-the-cookie-sent-on-cross-site-requests-cookiesamesite)
  * [4. Does the cookie name carry a prefix: `cookiePrefix`](#4-does-the-cookie-name-carry-a-prefix-cookieprefix)
  * [Severity and rating impact](#severity-and-rating-impact)
<!-- TOC -->


## 1. Does the cookie require HTTPS: `cookieSecure`

A cookie without `Secure` will be sent over a plain HTTP connection if the
browser ever makes one to the same host - a stray `http://` link, a mixed
redirect, or a captive portal are all it takes. Once that happens, the cookie
crosses the network in clear text and can be replayed by anyone who saw it.

**Fix:** set `Secure` on every cookie the reverse proxy or application issues.
If the instance terminates TLS in a reverse proxy, this is usually the
proxy's own session or CSRF cookie rather than one OpenCloud itself sets - see
[Reverse proxies](reverse-proxy.md) for the header set this check reads.

## 2. Can page scripts read the cookie: `cookieHttpOnly`

Without `HttpOnly`, scripts running on the page can read a cookie through
`document.cookie`. For session cookies this increases the impact of an injected script.
Some CSRF-token designs deliberately require JavaScript access, so assess the cookie’s
purpose before changing the attribute.

**Fix:** use `HttpOnly` for cookies that scripts do not need to read, especially session
cookies. Confirm the application’s requirements before applying the attribute to every
cookie.

## 3. Is the cookie sent on cross-site requests: `cookieSameSite`

`SameSite` controls when the browser includes a cookie in cross-site requests. Many
current browsers apply a Lax-like default when it is omitted, but an explicit value
makes the intended behavior clear. The check reports the missing attribute rather than
proving that a CSRF attack is possible.

**Fix:** set `SameSite=Lax` or `SameSite=Strict` unless a documented
cross-site flow genuinely needs `SameSite=None` (which additionally requires
`Secure`). `Lax` is right for most session cookies: it still allows a
top-level navigation such as clicking a shared link to arrive signed in.

## 4. Does the cookie name carry a prefix: `cookiePrefix`

Cookie-name prefixes add rules for setting a cookie. Supporting browsers require
`__Secure-` cookies to be set securely with `Secure`. `__Host-` additionally requires
`Path=/` and forbids `Domain`, binding the cookie to the host that set it. This helps
prevent a sibling subdomain from setting a competing parent-domain cookie. It does not
isolate cookies by port.

The check reports two different failures, because they have one fix:

- **A cookie that claims a prefix it does not honour** - `__Host-` with a
  `Domain` attribute, with a `Path` other than `/`, or without `Secure`. Supporting
  browsers reject such a cookie, so this is not a theoretical
  weakness: the session it carries silently does not work. The detail names
  which rule was broken.
- **No observed cookie carrying a prefix at all**, which is the ordinary
  state of an instance nobody has changed.

**Fix:** rename the session cookie to `__Host-<name>` and set it with
`Secure`, `Path=/` and no `Domain` attribute - or `__Secure-<name>` when it
genuinely has to be shared across subdomains. Where the cookie comes from a
reverse proxy or an identity provider rather than from OpenCloud, rename it
there.

## Severity and rating impact

All four are `extraChecks`, reported whenever a cookie is observed -
`cookieSecure` at `high`, `cookieHttpOnly` at `medium`, `cookieSameSite` and
`cookiePrefix` at `low` - and each caps the rating on its own the same way any
other failed extra check does (`high` -> `C`, `medium` -> `A`, `low` -> `A+`; see the
extra-checks table in [the main README](scanner-checks.md#what-the-scanner-checks)).
Set `scanner.extra_checks_rating: false` to report them without touching the
rating, or `--no-extra-checks` to skip them outright.
