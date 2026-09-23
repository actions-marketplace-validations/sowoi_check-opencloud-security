# Dependency records

One record per Python dependency, written and approved **before** the package
is used. See [ADR 0060](../../adr/0060-a-new-dependency-is-justified-tested-and-reviewed-first.md)
and AGENTS.md, "Adding a Python dependency".

## Why this exists

Every package this project installs runs with the project's rights: inside the
monitoring agent, inside the public web service that scans strangers' URLs, and
inside CI, where a token is in reach. `pip-audit` and the dependency-review
action catch *known* vulnerabilities in what is already chosen. Neither asks
whether the package should be here at all, what it does at install time, or
whether it phones home, which [AGENTS.md](../../AGENTS.md) forbids. A record
is where those questions get answered, once, by a named person.

## The rule

`python scripts/check_dependencies.py --check` runs in CI on every pull
request and fails when:

- a declared dependency has neither an approved record here nor an entry in
  [`grandfathered.txt`](grandfathered.txt),
- a record is `proposed`, misses a field, or names tests that do not exist or
  never mention the package,
- a record's `scopes` differ from where the package is declared. Moving a
  test-only package into the runtime changes what it can reach, so the record
  has to be looked at again,
- a record or grandfather entry names a package nothing declares, or
- (on a pull request, with `--base`) `grandfathered.txt` gained a name.

"Declared" means every requirement in `pyproject.toml`: `[project]
dependencies`, every extra, every dependency group, and `[build-system]
requires`. It also covers every package a workflow runs with `uvx`.

`grandfathered.txt` lists the dependencies that were in use when the policy
was adopted. They have **not** had this review. The list may only shrink: a
name leaves it when its record is approved.

Transitive packages have no record of their own. The record of the direct
dependency that pulls them in lists them under `transitive_dependencies`, and
`pip-audit` audits the whole locked set.

## Who writes what

Anyone, including an agent, may draft a record with `status: proposed`, and
that includes the review findings. **Only a maintainer sets
`status: approved` and `approved_by`**, after reading the review. A proposed
record fails the check on purpose: the package cannot be merged until
somebody accountable has signed off.

## Fields

| Field | |
|:--|:--|
| `name` | The distribution name as on PyPI. The file is `<normalised name>.yml` (lowercase, runs of `-_.` become `-`). |
| `import_name` | What the code imports (`yaml` for PyYAML), or the command a CI tool runs. The listed tests must mention it. |
| `status` | `proposed` or `approved`. |
| `approved_by` | The maintainer who approved it. Required when approved. |
| `scopes` | Exactly where it is declared: `runtime`, `extra:<name>`, `group:<name>`, `build`, `ci`. |
| `reviewed_version` | The version the review looked at. A major upgrade deserves a new look. |
| `justification` | What it is needed for, and why the standard library or an existing dependency does not do. |
| `alternatives_considered` | What else was looked at, including writing it ourselves, and why not. |
| `tests` | Test files (or, for a `ci` tool, the workflow) that exercise it. |
| `review.reviewer`, `review.reviewed_on` | Who did the security review, and when (`YYYY-MM-DD`). |
| `review.known_vulnerabilities` | `pip-audit`/OSV result for `reviewed_version`, and the project's advisory history. |
| `review.maintenance` | Maintainers, release cadence, how security reports are handled. |
| `review.provenance` | Trusted publishing / attestations on PyPI, source repository matches the release. |
| `review.install_time` | Wheels available? Build backend? Anything executed at install time. |
| `review.runtime_network` | What it fetches or sends at runtime: telemetry, update checks, remote config. Must be nothing unexpected. |
| `review.native_code` | Compiled extensions, subprocesses, `eval`/`pickle` on untrusted input. |
| `review.transitive_dependencies` | The packages it adds to `uv.lock`, with a review of each package using the same criteria. |
| `review.license` | The license, and that it is compatible with this project's. |

## Template

```yaml
# A dependency record. See security/dependencies/README.md.
name: example-package
import_name: example_package
status: proposed
approved_by: ""
scopes:
  - extra:web
reviewed_version: "1.2.3"
justification: |
  What it is for, and why the standard library or an existing dependency does
  not already do it.
alternatives_considered: |
  The other packages looked at, and writing it ourselves, and why not.
tests:
  - tests/test_something.py
review:
  reviewer: ""
  reviewed_on: "YYYY-MM-DD"
  known_vulnerabilities: |
    uvx pip-audit -r <(echo example-package==1.2.3): no known vulnerabilities.
    GitHub advisories for the project: ...
  maintenance: |
  provenance: |
  install_time: |
  runtime_network: |
  native_code: |
  transitive_dependencies: |
  license: |
```
