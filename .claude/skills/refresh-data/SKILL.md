---
name: refresh-data
description: Refresh the bundled OpenCloud release schedule, advisory database, frontend documentation and search indexes of check-opencloud-security outside a release, on a branch, without bumping the version - then commit and push. Use only when the user asks to refresh the bundled data between releases.
disable-model-invocation: true
---

# Refresh bundled data

Between releases, OpenCloud can ship a release or an advisory the bundled data
does not know yet. This refreshes it **without changing the version** - never
edit `version` in `pyproject.toml` here. Use `/release patch` when a release
is wanted.

## 1. Branch

```bash
git status --porcelain       # must be clean (untracked .claude/ is fine)
git fetch origin
git switch -c chore/refresh-data-$(date +%Y-%m-%d) origin/main
```

Stop if that branch already exists, or if an open pull request from the
scheduled workflows (`release-schedule.yml`, `vulnerability-db.yml`) already
carries the same refresh - `gh pr list --state open` - and tell the user.

## 2. Refresh

Order matters: the schedule rewrites the README block the documentation is
generated from, and the search index includes that documentation.

```bash
uv run python scripts/update_release_schedule.py
uv run python scripts/update_vulnerability_db.py
python scripts/build_frontend_documentation.py
python scripts/build_search_index.py
git diff --stat
```

If nothing changed, say so, switch back (`git switch -`), delete the branch
and stop.

Both refreshes may only **gain** knowledge. If the diff removes a release line
from `release_schedule.json` or an advisory from `vulnerabilities.json`, stop
and show the user - that is a bad fetch, not an update.

## 3. Verify

```bash
uv run pytest -q
python scripts/build_frontend_documentation.py --check
python scripts/build_search_index.py --check
```

Tests that hardcode a current OpenCloud release go stale when the schedule
moves; fix them to read the schedule rather than a new literal.

## 4. Changelog, commit, push

Add a `### Changed` entry under `## [Unreleased]` in `CHANGELOG.md` naming
what is new: which OpenCloud releases the schedule now knows (and which track
they are on), which advisories were added (or that there were none), and that
documentation and search indexes were rebuilt.

If a new advisory affects how the scanner rates versions and the user should
decide on a `### Security` entry, ask - it needs `/security-fix-record`.

```bash
python scripts/check_pull_request.py --base origin/main
git add -A -- . ':!.claude'
git commit -m "chore(data): refresh release schedule and advisories" -m "<what changed>"
git push -u origin HEAD
```

End the commit message with the session's attribution lines. Report the branch,
what the refresh found, test results and the commit hash. Do not open a pull
request unless asked.
