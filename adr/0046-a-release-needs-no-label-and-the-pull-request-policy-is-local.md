# ADR 0046: A release needs no label, and the pull request policy is local

- Status: Accepted
- Date: 2026-09-13
- Supersedes: the pull request policy in ADR 0045

## Context

ADR 0045 ran `scripts/check_pull_request.py` as `pull-request-policy.yml` on
every pull request, and made a version change fail until the maintainer added a
`release` label. The first release pull request after it landed failed on
exactly that, and the maintainer does not want to label releases: the version
is already bumped by hand, by the maintainer alone, and a second deliberate
step for the same decision is friction without new information.

## Decision

**`pull-request-policy.yml` is removed, and the script asks for no label.**
`scripts/check_pull_request.py` stays as a check a contributor runs before
opening a pull request:

```bash
python scripts/check_pull_request.py --base origin/main
```

It still refuses a change without a new `CHANGELOG.md` entry and a
`RELEASE.md` under the declared version (`--labels skip-changelog` skips
that), a version that does not move past `main` and every tag, and a bump
commit whose subject names a different version. No workflow runs it.

The rest of ADR 0045 stands: the release publishes to PyPI last, and
`release-dry-run.yml` rehearses it on every pull request.

## Consequences

- A release pull request is not blocked by a missing label.
- A pull request without changelog notes, or with a version that does not
  move forward, is no longer turned red by CI; the checklist in the pull
  request template and the local script are what catch it.
- `tests/test_check_pull_request.py` keeps the script correct, so it can be
  wired back into a workflow without the label rule if that is wanted later.

## Alternatives considered

- **Keep the workflow and drop only the label rule.** Still possible, and the
  smaller change to CI; not what was asked for.
- **Accept the label.** Rejected by the maintainer.
