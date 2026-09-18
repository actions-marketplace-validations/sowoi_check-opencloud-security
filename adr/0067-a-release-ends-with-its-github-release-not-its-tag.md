# ADR 0067: A release ends with its GitHub release, not its tag

- Status: Accepted
- Date: 2026-09-18
- Extends: ADR 0045

## Context

ADR 0045 made the release publish last and promised that a failed release is
repaired by pushing to `main` again. That held for every failure before the
tag, and for none after it.

`publish-pypi.yml` decided whether a version still had to be released by
asking whether its tag existed. The tag was pushed and the GitHub release
created in one step, tag first. v1.25.0 reached PyPI, pushed `v1.25.0`, and
then `gh release create` failed on an HTTP 500 from GitHub's asset upload
endpoint. The re-run found the tag and skipped every step, green. PyPI and
Docker Hub had 1.25.0; GitHub had a tag with no release, no `.deb`, no `.rpm`,
no web bundle, and `releases/latest/download/setup-wizard.py` still served
1.24.2. No push to `main` could change that, and an agent may not create the
release by hand.

## Decision

**The published GitHub release is what ends a version.** The workflow reads
two facts, the tag and the release, and runs in one of three modes:

- `release` - no tag yet: write the notes, build, publish, tag, release, as
  before.
- `resume` - tagged, but no published release (none, or a draft): check out
  the tag, rebuild and attest every artifact from it, and finish the release.
  The notes, the release schedule and the search index are not touched; the
  tagged commit already carries them.
- `done` - tagged and released: nothing runs.

A resumed run still passes through `uv publish --check-url`. The wheel and the
sdist build reproducibly from the tag, so PyPI's copies are skipped; a rebuild
that came out different would fail the upload instead of attaching a file
PyPI does not serve.

**The release is a draft until every asset is on it.** It is created without
assets, each asset is uploaded with retries, and only then is the release
published. A draft left behind is picked up again by the next run, and
`releases/latest` never names a release that lacks the wizard.

**The workflow can be started by hand** (`workflow_dispatch`), and runs of it
never overlap (`concurrency: release`). Merging any change into `main` also
resumes an unfinished release, because the version on `main` is still the
tagged one.

## Consequences

- A release stopped after its tag is repaired by merging to `main` or by
  running the workflow by hand; nothing is tagged or uploaded by a person.
- A resumed release carries fresh attestations for the rebuilt artifacts. For
  the wheel and the sdist they attest the same digests as the first run.
- Every push to `main` makes one extra API call to look up the release.
- A resume builds what the tag holds, not what `main` holds, so commits merged
  after the tag never reach an older version's assets.
