---
name: patch-release
description: Prepare a patch release of check-opencloud-security - bump the patch version, create and switch to release/<version>, refresh uv.lock, the bundled OpenCloud release schedule and advisory database, the frontend documentation and search indexes, then commit and push the branch. Use only when the user explicitly asks for a patch release.
disable-model-invocation: true
---

# Patch release

Invoking this skill **is** the user's decision to bump the version, which
`AGENTS.md` otherwise forbids doing on your own. It prepares and pushes a
`release/<version>` branch; it never merges to `main` (a bump landing on
`main` publishes to PyPI) and never publishes a security advisory.

Run every command from the repository root. Stop and report on the first
failure instead of working around it.

## 1. Preconditions

```bash
git status --porcelain          # must be empty (untracked .claude/ is fine)
git fetch origin --tags
```

If the tree has other changes, stop and ask the user what to do with them.

## 2. Work out the new version

The base is the version on `origin/main`, not the current branch:

```bash
git show origin/main:pyproject.toml | grep -m1 '^version'
git tag --list 'v*' --sort=-v:refname | head -1
```

Take `MAJOR.MINOR.PATCH` from `origin/main` and increment `PATCH` by one.
If the latest tag is already at or past that number, stop and tell the user -
`scripts/check_pull_request.py` requires the version to move past both `main`
and every tag. Also stop if `release/<version>` already exists locally or on
`origin`.

## 3. Create the branch and switch to it

```bash
git switch -c release/<version> origin/main
```

## 4. Bump the version

Edit the `version = "..."` line under `[project]` in `pyproject.toml` to the
new version. That is the only place the version lives - never write it
anywhere else (`opencloud_local_scan.__version__` derives from it).

## 5. Refresh generated files

Order matters: the release schedule rewrites the `README.md` table the
frontend documentation is generated from, and the search index embeds the
version and the documentation text, so it goes last.

```bash
uv lock                                              # new uv.lock with the bumped version
uv run python scripts/update_release_schedule.py     # new OpenCloud releases -> release_schedule.json + README table
uv run python scripts/update_vulnerability_db.py     # new OpenCloud advisories -> vulnerabilities.json
python scripts/build_frontend_documentation.py       # regenerate frontend/templates/docs
python scripts/build_search_index.py                 # regenerate frontend/static/search-index*.json
```

Then note what actually changed (`git diff --stat`), in particular whether
`opencloud_local_scan/data/release_schedule.json` or
`opencloud_local_scan/data/vulnerabilities.json` moved, and which new
OpenCloud releases or advisories appeared.

## 6. Verify

If the release schedule or the advisory database changed, run the suite -
tests that hardcode a current OpenCloud release go stale (fix them to read the
schedule rather than a new literal):

```bash
uv run pytest -q
```

Always run the version guard and the checks CI runs on generated files:

```bash
python scripts/build_frontend_documentation.py --check
python scripts/build_search_index.py --check
python scripts/security_advisories.py --check
```

## 7. Changelog

Add an entry under `## [Unreleased]` in `CHANGELOG.md` (usually `### Changed`)
describing what this refresh brought: new OpenCloud releases in the schedule,
new advisories (or that there were none), rebuilt documentation and search
indexes. Match the style of the existing entries. Never edit `RELEASE.md`.
If a new advisory warrants a `### Security` entry, stop and ask the user - it
needs a record in `security/advisories/`.

Then:

```bash
python scripts/check_pull_request.py --base origin/main
```

## 8. Commit and push

```bash
git add -A -- . ':!.claude'
git commit -m "chore(release): <version>" -m "<body: what was bumped and refreshed>"
git push -u origin release/<version>
```

End the commit message with the attribution lines from the current session's
instructions. Finish by reporting to the user: the new version, the branch,
what the schedule and advisory refresh found, test results, and the commit
hash. Do not open a pull request unless asked.
