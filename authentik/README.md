# Authentik provisioning

`blueprints/opencloud-scanner.yaml` provisions the OAuth 2.0 provider and
application used to protect the `/mcp` endpoint in
`docker/docker-compose.authentik.yml`.

The compose stack mounts this directory into both Authentik containers. On the
first start, Authentik applies the blueprint and creates the provider without
manual admin-interface setup. It uses `state: created`, so later changes made
by an operator are not overwritten on restart.

`blueprints/opencloud-admin.yaml` provisions the proxy provider in front of
`/admin`. `blueprints/opencloud-mfa.yaml` requires every account to enrol and
use a second factor (TOTP or WebAuthn) when it signs in, and is re-applied so
the requirement stays on. `blueprints/opencloud-enrollment.yaml` provides the
invitation-only enrollment flow the Docker setup wizard prints a link to: a
listed username chooses a password and enrols a second factor, with nothing
created in the admin interface. Without `COS_AUTHENTIK_ENROLLMENT_TOKEN` it
creates no invitation.

The blueprints contain no secrets. It reads the client ID, client secret,
redirect URI, and application slug from environment variables written to
`docker/.env` by `docker/authentik-env.sh`. Keep that `.env` file private and
do not put its values in this directory or commit them.

The scanner is an OAuth resource server. It verifies asymmetric tokens against
the provider's JWKS and never issues, stores, or logs credentials. See
[`docs/authentik.md`](../docs/authentik.md) for deployment, backup, recovery,
and agent-token instructions.

This project is independent and is not affiliated with, endorsed by, or
supported by OpenCloud GmbH. "OpenCloud" and related marks belong to their
owners and are used only to identify the software being checked.
