## check-opencloud-security 1.22.2

### Added

- **The bundled Authentik requires a second factor at every sign-in.**
  `authentik/blueprints/opencloud-mfa.yaml` sets Authentik's own
  `default-authentication-mfa-validation` stage to enrol an account that has
  no authenticator - TOTP or WebAuthn - before the sign-in completes, instead
  of skipping it, and is re-applied so the requirement stays on. It is mounted
  by `docker-compose.authentik.yml` and copied by the Docker setup wizard.
  Agents using `client_credentials` run no flow and are unaffected.
- **The Docker setup wizard configures Authentik without its admin interface.**
  It asks who signs in, by username (the operator guest list is always
  included), and prints one enrollment link. Each person named chooses a
  password and enrols a second factor there; an operator joins
  `opencloud-scanner-operators` on the way. The link is an invitation keyed by
  a generated `AUTHENTIK_ENROLLMENT_TOKEN` in `.env` - the wizard prints the
  link with a placeholder and a command that fills the token in from `.env`,
  never the token itself, so it stays out of scrollback and CI logs
  (`authentik/blueprints/opencloud-enrollment.yaml`), admits only the listed
  names, each once, and creates nothing without the token. `akadmin` gets a
  generated `AUTHENTIK_BOOTSTRAP_PASSWORD` for recovery, which also closes the
  initial-setup flow that would otherwise make whoever reached it first the
  administrator. See ADR 0047.

### Changed

- **The Authentik stack runs Authentik 2026.8.2.** `docker-compose.authentik.yml`
  and the image the Docker setup wizard writes move from 2026.8.0 together, so
  a generated stack and the file next to the wizard still pin the same version.
- **`forwardedHostIgnored` names a missing default server on the reverse proxy
  as a cause.** The explanation used to trace every failure to an instance
  that was never told its address, so an operator with `OC_URL` set correctly
  was sent back to it. A proxy with no default server answers a `Host` it has
  no site for from whichever site it loaded first for that port - often
  another application on the same machine - and a redirect there built from
  `$host` repeats the probe host without OpenCloud ever seeing the request.
  The explanation now says so when only `Host` comes back as a redirect, the
  remediation gives an explicit nginx default server that refuses unknown names
  (and the Apache equivalent) plus how to tell which server answered, and
  `docs/reverse-proxy.md` and `docs/scanner-checks.md` describe the same.
- **`forwardedHostIgnored` names a missing default server on the reverse proxy
  as a cause.** The explanation used to trace every failure to an instance
  that was never told its address, so an operator with `OC_URL` set correctly
  was sent back to it. A proxy with no default server answers a `Host` it has
  no site for from whichever site it loaded first for that port - often
  another application on the same machine - and a redirect there built from
  `$host` repeats the probe host without OpenCloud ever seeing the request.
  The explanation now says so when only `Host` comes back as a redirect, the
  remediation gives an explicit nginx default server that refuses unknown names
  (and the Apache equivalent) plus how to tell which server answered, and
  `docs/reverse-proxy.md` and `docs/scanner-checks.md` describe the same.

### Fixed

- **Signing in to `/admin` through Authentik works.** The operator-area
  blueprint created a proxy outpost of its own, but named no configuration for
  it, so Authentik refused the entry - and, a blueprint being applied as a
  whole, rolled back the provider, application and binding with it. Nothing in
  the stack ran that outpost either, so the forward-auth path answered 404,
  which nginx turns into a 500 for every request to `/admin`. The provider is
  now assigned to Authentik's embedded outpost, which the server already serves
  on port 9000, and the old outpost is removed where an earlier version did
  create it. The embedded outpost is re-applied every hour with exactly the
  providers the blueprint lists, so a provider assigned to it by hand is taken
  off again.
- **The embedded outpost sends a browser to Authentik's public address.** Left
  unconfigured it redirects to `http://localhost/application/o/authorize/`,
  which no visitor can reach. The blueprint now sets it from
  `COS_AUTHENTIK_URL`, which `docker-compose.authentik.yml` passes to the
  server and worker from `AUTHENTIK_URL`, and which the Docker setup wizard
  writes into the compose file it generates.

- **Re-running the Docker setup wizard moves Authentik to its newer patch
  release.** The image tag is remembered with every other answer, so a newer
  wizard run against an existing deployment kept writing the release that
  deployment was first set up with - which is how a stack stayed on 2026.8.0
  after the wizard moved to 2026.8.2. A remembered pin in the same `YYYY.M`
  series is now moved up and the wizard says so; a pin in an older series is
  left alone with a warning, because an upgrade across series can carry
  migrations worth reading first.
- **The generated nginx configuration gives the forward auth room for
  Authentik's headers.** The `/admin` and `/outpost.goauthentik.io` locations
  now set `proxy_buffers 8 16k` and `proxy_buffer_size 32k`, as Authentik's own
  nginx example does: its session cookie and identity headers outgrow nginx's
  defaults and fail as "upstream sent too big header", a 502 for a sign-in that
  worked.
- **Verified end to end.** A generated stack with Authentik 2026.8.2 and the
  generated nginx configuration signs an operator in and serves `/admin`, and
  keeps an account outside the operator group out. A test now fails if the
  blueprint creates an outpost of its own again or stops setting the embedded
  outpost's address.
