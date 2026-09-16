# ADR 0060: A new dependency is justified, tested and reviewed first

- Status: Accepted
- Date: 2026-09-16

## Context

A direct Python dependency executes with the project's rights: on monitoring
hosts, in the public web service, during a build, or in CI with a token in
reach. A known-vulnerability scan answers whether somebody has already
reported a defect in a chosen version. It does not answer whether the package
is necessary, maintained, published by the expected source, active at install
time, able to make network requests, or appropriate for the scope where it is
installed.

The repository already pins and audits its resolved dependency set, but a new
direct dependency could previously enter `pyproject.toml` or an `uvx` workflow
command without recording those decisions. Reviewing that only after it has
become structural makes removal harder and leaves future maintainers to repeat
the same investigation.

## Decision

Every new direct Python dependency has an approved record in
`security/dependencies/<normalised-name>.yml` before it is used.

- The record states why the package is needed, alternatives considered, its
  exact declaration scopes, tests that exercise it, and a security review of
  the version, maintenance, provenance, install-time behaviour, runtime
  network access, native code, transitive dependencies and licence.
- An agent may prepare a `proposed` record and its evidence. Only a maintainer
  may set it to `approved` and name themselves in `approved_by`.
- `scripts/check_dependencies.py --check` covers project dependencies,
  optional extras, dependency groups, build requirements, and packages run
  through `uvx` in GitHub workflows. CI runs it for every pull request.
- Dependencies already present when this decision was adopted are listed in
  `security/dependencies/grandfathered.txt`. This is an inventory, not an
  approval. It may only shrink as records are approved or packages removed.
  On the policy's first pull request, a grandfather entry is accepted only if
  the base commit already declared that package.
- Transitive packages do not each receive a record. The direct dependency's
  review names them, while the locked set remains covered by vulnerability
  auditing and dependency review.

## Consequences

- A dependency addition cannot be merged until a named maintainer accepts its
  necessity and security characteristics.
- Moving a package into a wider scope requires the record to change and be
  reviewed again.
- Existing packages are explicitly visible as review debt rather than being
  retrospectively described as approved.
- The checker and record format become security controls and require tests and
  ordinary code review themselves.

## Alternatives considered

**Rely only on `pip-audit` and GitHub dependency review.** Rejected: they find
known advisories and changed resolved packages, but do not justify a package
or inspect its install-time and runtime behaviour.

**Record every transitive package separately.** Rejected: lockfile auditing
already covers known defects, while hundreds of mechanically generated
records would hide the judgment attached to the dependency the project chose.

**Treat all existing dependencies as approved.** Rejected: adoption of a new
policy is not evidence that those packages received the review it requires.
