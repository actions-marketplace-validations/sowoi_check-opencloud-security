# ADR 0047: The bundled provider requires a second factor and provisions its accounts

- Status: Accepted
- Date: 2026-09-13

## Context

The Authentik the Docker setup wizard brings provisioned its providers
(ADR 0015, ADR 0035), but a person still had to finish it in the admin
interface: set `akadmin`'s password at the initial-setup flow, create each
account, put operators in `opencloud-scanner-operators`, and - if anyone
thought of it - edit the authentication flow so a second factor was required.
Authentik's default flow checks a second factor only for an account that has
one, so in practice nobody had one.

Two of those steps were also risks rather than chores. The initial-setup flow
makes whoever reaches it first the administrator, and it is reachable from the
moment the containers start. And `/admin` and `/mcp` act on systems the
signed-in person is responsible for, behind a password alone.

## Decision

**Every sign-in to the bundled Authentik requires a second factor.**
`authentik/blueprints/opencloud-mfa.yaml` sets the default flow's own
`default-authentication-mfa-validation` stage to *configure*, offering TOTP
and WebAuthn, with `state: present` so it is re-applied rather than left to be
switched off. It is mounted by both the wizard's stack and
`docker-compose.authentik.yml`. Grants that run no flow - `client_credentials`
with an app password - are unaffected.

**Accounts are claimed, not created by an administrator.** The wizard asks who
signs in, by username (the operator guest list is always included), generates
`AUTHENTIK_ENROLLMENT_TOKEN` into `.env`, and prints one link to an
invitation-only enrollment flow in `opencloud-enrollment.yaml`. The flow
admits only a username in `COS_AUTHENTIK_ACCOUNTS`, only if it does not exist
yet, only with the token; writes the account; enrols the second factor; and
only then starts a session. A name on `COS_WEB_ADMIN_USERS` joins the operator
group on the way. Without a token, no invitation exists.

**`akadmin` gets a generated `AUTHENTIK_BOOTSTRAP_PASSWORD`**, which closes the
initial-setup flow on first start and is the recovery path for a lost factor.

## Consequences

- A person chooses only a password and a second factor; nothing is clicked in
  Authentik. Adding somebody is a wizard re-run and the same link.
- The link is a credential until everybody listed has used it: it can claim
  any listed name that has not enrolled. It is printed to the operator and
  kept in `.env`, never in the compose file, and rotating the token retires it.
- The requirement cannot be turned off in the interface while the blueprint is
  mounted. Removing the file is the switch, deliberately.
- Usernames and the token reach Authentik as environment variables read at
  run time, so no answer becomes Python source in an expression policy.
- The scan service is unchanged: it still authenticates nobody and verifies
  tokens only.

## Alternatives considered

- **Create accounts in a blueprint with a wizard-chosen password.** The
  password would pass through the wizard, `.env` and the blueprint database
  before its owner ever saw it, and the second factor would still need a
  separate sign-in.
- **A second validation stage bound beside the default one.** Somebody with a
  factor would be asked for it twice.
- **A single-use invitation.** Authentik deletes it after the first person, so
  the rest of the list would have no way in, and the hourly re-apply would
  recreate it anyway; one-per-name is enforced by the username field instead.
- **Leave `akadmin` to the initial-setup flow.** That keeps the window in which
  whoever reaches port 9000 first becomes the administrator.
