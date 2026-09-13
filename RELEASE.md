## check-opencloud-security 1.22.5

### Changed

- **The Docker setup wizard sets the enrollment link apart.** It was one
  paragraph among the proxy commands and the `/admin` steps at the end of a
  long run, and easy to scroll past - leaving an operator to create accounts
  and group memberships by hand in Authentik that the link would have made.
  It now closes under its own `ENROLLMENT LINK` heading, with the command that
  builds the link from `.env` first, and says "Send it to scanokko. It asks for
  that username" for one name rather than "Send that link to each of
  scanokko".

### Documentation

- **Setting up an operator for `/admin`, by the wizard or by hand.**
  `docs/authentik.md` has a new section on the two places an operator has to
  be named - `COS_WEB_ADMIN_USERS` and Authentik's
  `opencloud-scanner-operators` group - and reaches it both ways: through the
  wizard's enrollment link, and in the Authentik interface or from a shell,
  including getting into `akadmin` with `ak create_recovery_key` when
  `AUTHENTIK_BOOTSTRAP_PASSWORD` is refused by a database older than `.env`.
  The second-factor section now says what a person sees when enrolling an
  authenticator app, a security key or recovery codes. The troubleshooting
  table gains the refused bootstrap password, a sign-in Authentik stops
  because the account is not in the group, and `password authentication
  failed for user "authentik"` from a database volume created under another
  `AUTHENTIK_PG_PASS`. `ADMIN.md` points there.
