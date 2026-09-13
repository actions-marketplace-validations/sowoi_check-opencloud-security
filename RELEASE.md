## check-opencloud-security 1.22.3

### Fixed

- **A Docker setup wizard downloaded on its own writes the Authentik
  blueprints.** `docker/README.md` says to `curl` just `setup-wizard.py`, but
  the wizard copied the blueprints from a checkout beside it and skipped any
  it could not find without a word. The generated stack mounted
  `./authentik/blueprints` anyway, Docker created it empty, and Authentik
  started with no provider: `/mcp` refused every token, and the forward auth
  in front of `/admin` answered 404, which nginx turns into a 500. The wizard
  now carries the four blueprints itself, generated into it from
  `authentik/blueprints/` by `scripts/embed_wizard_blueprints.py`, and a test
  fails when the embedded copies differ from those files. A deployment set up
  with an earlier download gets them by re-running the wizard.
