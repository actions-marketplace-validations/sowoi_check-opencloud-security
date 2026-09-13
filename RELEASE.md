## check-opencloud-security 1.22.1

### Added

- **The Docker setup wizard generates for rootless Docker too.** Under a
  rootless daemon, uid 10001 in a container is the user's subordinate uid at
  that offset on the host, so the `sudo chown 10001` the wizard printed for a
  bind-mounted audit or Redis directory handed it to an account the container
  never runs as, and the container could not write to it. The wizard now asks
  whether the daemon is rootful or rootless - detected from the socket, which a
  rootless daemon serves under `/run/user/<uid>` - and for a rootless one
  prints a `chown` that runs inside a container instead and needs no sudo. A
  logrotate policy names the mapped host ids from `/etc/subuid` and
  `/etc/subgid`, and the wizard says so when there is no range to read. It
  also points out that the default rootless port driver hides the client
  address from a port published beyond `127.0.0.1`. Verified end to end on
  `docker:dind-rootless`: both containers write to their directories.

- **The Docker setup wizard writes Authentik's site into the proxy
  configuration too.** `docker/setup-wizard.py` already wrote nginx, Apache,
  Caddy or Traefik for the scan service, including the forward auth in front
  of `/admin` - but a stack that brought Authentik still left its sign-in page
  to be proxied by hand, and every sign-in redirects a browser there. When the
  stack brings Authentik, the same file now carries a second server block,
  virtual host or router answering to the host name of Authentik's public
  address and proxying to its published port, with the WebSocket its
  interface keeps open and `X-Forwarded-For` set rather than appended. nginx
  and Apache are asked for a certificate for that name, since it is not the
  scanner's; Caddy and Traefik fetch their own. An address that is
  `localhost`, a bare IP or the scanner's own host name gets no site, and the
  warning that used to cover only `/admin` now says so for any stack with
  Authentik behind a generated proxy.

### Fixed

- **Automatic updates work on Docker 29 again.** The Watchtower the Docker
  setup wizard adds with `--auto-updates` was `containrrr/watchtower`, which
  was archived in December 2025 and always speaks Docker API 1.25. Docker 29.0
  raised the daemon's minimum to 1.44 and 29.3 to 1.40, so the container
  panicked on start with `client version 1.25 is too old` unless
  `DOCKER_API_VERSION` was pinned by hand. The wizard now writes
  `nickfedor/watchtower`, the maintained fork, which negotiates the API
  version with the daemon and reads the same variables and enable label - so
  no version is pinned, and none goes stale when a daemon raises its minimum
  again. Reproduced and verified against Docker 29.6.

- **The Docker setup wizard no longer lets the audit trail and Redis share a
  host directory.** The web image writes as uid 10001 and Redis as uid 999,
  and a directory has one owner, so whichever was chowned last kept the other
  container from writing. The same directory - however it is spelled - or one
  inside the other is now refused at the question, blocks the summary, and
  makes an unattended run write nothing.
- **A generated logrotate policy names the audit file by its absolute path.**
  The default `./audit` was written into the policy as it was, and logrotate
  resolves a relative path against wherever cron runs it from rather than
  against the compose file, so the policy rotated nothing.
