# ADR 0070: The operator area installs attested releases in place

- Status: Proposed
- Date: 2026-09-19

## Context

Operators asked for the operator's area to say when a newer release of this
service is published and to install it with a button - from GitHub, not by
editing the compose stack, and volatile changes are acceptable. The web and
worker containers run read-only and unprivileged, and must stay that way: no
Docker socket, no writable image.

Installing code at runtime means the web process - the one strangers talk
to - downloads and runs code. A checksum published in the same GitHub
release would prove the download is intact, not who built it.

## Decision

- The area asks GitHub's releases API for the newest release, cached in Redis
  for six hours (`COS_WEB_UPDATE_CHECK`).
- The button - operator-only, same-origin POST - downloads that release's
  `check_opencloud_security_web.tar.gz` and **verifies its Sigstore build
  attestation** with the existing verifier of ADR 0027, pinned to this
  repository's `.github/workflows/publish-pypi.yml` on `refs/heads/main`. A
  bundle that cannot be verified - no attestation, no trust root, the
  `signing` extra missing - is refused, not merely logged.
- The verified bundle is unpacked (plain files under its one top directory
  only) onto a tmpfs named by `COS_WEB_ADMIN_UPDATE_DIR`, and the process
  re-executes its own command from there. Workers follow through a Redis key
  with a ten-minute TTL, each verifying the bundle itself.
- The update is volatile: a container restart runs the image again. A
  version a container has tried once is not retried, so a release that does
  not start cannot crash-loop.

## Consequences

- The web image installs the `signing` extra (`sigstore`), already a
  reviewed dependency of the project.
- Whoever can make this repository's release workflow on `main` sign a
  bundle can run code on every deployment that presses the button - the
  same trust already placed in the image and the PyPI package.
- A new release whose Python dependencies changed may not start from the old
  image; the container then restarts on the image and stays there.
- A scan running at the moment of the switch is cut short.
