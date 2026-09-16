---
name: open-release-pr
description: Open the pull request for a prepared release/<version> branch of check-opencloud-security against main, with the [Unreleased] changelog as its body, then watch CI and report. Use after /release, only when the user asks to open the release pull request.
disable-model-invocation: true
argument-hint: "[version]"
---

# Open the release pull request

Arguments: $ARGUMENTS (the version; default: the current branch's
`release/<version>`).

Merging this pull request publishes to PyPI. **Never merge it, never enable
auto-merge, never create a tag or GitHub release** - those stay with the user.

## 1. Preconditions

```bash
git branch --show-current                       # must be release/<version>
grep -m1 '^version' pyproject.toml              # must equal <version>
git status --porcelain                          # clean (untracked .claude/ is fine)
git fetch origin
git status -sb                                  # branch pushed and not behind origin
gh auth status
gh pr list --head release/<version> --state open   # none open yet
```

If the branch is not pushed, stop and ask - do not push on your own unless the
user asked for it together with this skill. If a pull request already exists,
report its URL and go to step 4.

Check the changelog. The release branch is a skeleton from `/release`
and adds no entry of its own; the release
notes are the `## [Unreleased]` entries the merged pull requests wrote:

```bash
sed -n '/^## \[Unreleased\]/,/^## \[/p' CHANGELOG.md | sed '1d;$d'   # the release notes
git diff --stat origin/main...HEAD -- CHANGELOG.md RELEASE.md           # must be empty
```

Stop and tell the user if the `[Unreleased]` section is empty (there is
nothing to release), or if the branch changes `CHANGELOG.md` or `RELEASE.md`
(a release skeleton must not). Never add, edit or remove anything in either
file yourself.

Then run the version guard and stop on failure. `--labels skip-changelog`
turns off only its check for a new entry on this branch, which a skeleton
never has; the version check still applies:

```bash
python scripts/check_pull_request.py --base origin/main --labels skip-changelog
```

## 2. Build the body

Use the `[Unreleased]` entries from step 1, verbatim.

Body layout:

```markdown
Release <version>.

<the [Unreleased] entries, verbatim>

### Checklist
- [ ] CI green, including the release dry run (`release-dry-run.yml`)
- [ ] Security records decided (`python scripts/security_advisories.py --check`)
- [ ] Merging publishes <version> to PyPI

<attribution line from the session's instructions>
```

Write it to a file in the scratchpad directory rather than passing it inline.

## 3. Open it

```bash
gh pr create --base main --head release/<version> \
  --title "chore(release): <version>" --body-file <scratchpad>/pr-body.md
```

## 4. Watch CI

```bash
gh pr checks <number> --watch --interval 60
```

Run it in the background and wait for the completion notification rather than
polling. When it finishes, report: the pull request URL, each failed check with
`gh run view <run-id> --log-failed | tail -50`, and which checks are still
pending. A stale search index on the pull request is expected to be rebuilt by
`search-index.yml` (ADR 0050) - mention it, do not treat it as a failure.

Do not fix failures without asking.
