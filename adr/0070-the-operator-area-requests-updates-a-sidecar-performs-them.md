# ADR 0070: The operator area requests updates, a sidecar performs them

- Status: Proposed
- Date: 2026-09-19

## Context

Operators asked for the operator's area to say when a newer release of this
service is published and to install it. The web and worker containers run
read-only, unprivileged, with every capability dropped and without the Docker
socket - a process that anybody on the internet talks to must not be able to
replace containers on its host. Installing an image needs exactly that power.

## Decision

- The web process asks PyPI for the newest `check-opencloud-security`
  version (the plugin and the service are released together from one
  version), for the operator's area only, cached in Redis for six hours.
  `COS_WEB_UPDATE_CHECK=false` turns it off.
- The "install" button writes a request file into a directory shared with a
  separate, opt-in `updater` service (`--profile autoupdate` in
  `docker-compose.dockerhub.yml`), named by `COS_WEB_ADMIN_UPDATE_DIR`. The
  version written is the one PyPI named, never one a form sent.
- The updater holds the Docker socket, is on no network, and runs a fixed
  command: pull the published image and recreate `web_app` and `arq_worker`.
  It reads only a version string from the request, checks it against
  `x.y.z` and logs it. A short downtime is accepted.

## Consequences

- The web process keeps its privileges unchanged; compromising it lets an
  attacker at most trigger a pull of the already-published image.
- The updater is root-equivalent on the host by virtue of the socket, which is
  why it is opt-in and exposes no network surface.
- A deployment built from source (`docker-compose.yml`) cannot pull, so the
  area only reports that an update exists there.
