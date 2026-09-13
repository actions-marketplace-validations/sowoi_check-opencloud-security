## check-opencloud-security 1.22.2

### Changed

- **The Authentik stack runs Authentik 2026.8.2.** `docker-compose.authentik.yml`
  and the image the Docker setup wizard writes move from 2026.8.0 together, so
  a generated stack and the file next to the wizard still pin the same version.

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
  writes into `.env`.
