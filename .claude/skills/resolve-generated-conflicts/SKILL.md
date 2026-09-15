---
name: resolve-generated-conflicts
description: Resolve merge or rebase conflicts in check-opencloud-security's generated files - search indexes, generated documentation templates, uv.lock, the README release-schedule block, the bundled release schedule and advisory database, embedded wizard blueprints, architecture diagram sources - by regenerating them instead of hand-merging, and merge CHANGELOG.md conflicts by keeping both sides. Use when a merge or rebase stops with conflicts in those files.
---

# Resolve conflicts in generated files

Generated files are a pure function of their sources. Resolving their
conflicts by hand means choosing between two stale answers - regenerate them
instead. Hand-written files are resolved normally.

## 1. See what conflicts

```bash
git status --porcelain | grep -E '^(UU|AA|DU|UD)'
git config --get merge.search-index.driver || echo "merge driver not registered"
```

If the search-index merge driver is not registered, suggest
`python scripts/setup_git_merge_drivers.py` for next time (it is per clone and
never automatic).

**Resolve the hand-written files first** (code, tests, templates, catalogues,
`README.md` outside the generated block, `docs/`), because the generators read
them. Ask the user about any conflict in hand-written code whose intent is not
clear from both sides.

## 2. Per file

| Conflicted file | Resolution |
|:--|:--|
| `CHANGELOG.md` | Keep **both** sides' entries under `## [Unreleased]`, merged into the right `###` sections, no duplicates. Never invent a version heading. |
| `pyproject.toml` `version` | Do not choose. Show both and ask the user - a version change is their decision. Other `pyproject.toml` conflicts: merge by hand. |
| `uv.lock` | `git checkout --theirs uv.lock` (or `--ours`), then `uv lock` after `pyproject.toml` is resolved. |
| `opencloud_local_scan/data/vulnerabilities.json` | Take the side with more advisories, then `uv run python scripts/update_vulnerability_db.py` - it only adds. Check no advisory present on either side was lost. |
| `opencloud_local_scan/data/release_schedule.json` and the `<!-- release-schedule:start -->` block in `README.md` | Take either side, then `uv run python scripts/update_release_schedule.py`; confirm no release line either side knew was lost. Resolve the rest of `README.md` by hand first. |
| `frontend/templates/docs/*.html`, `frontend/templates/admin-docs/*.html` | Take either side, then `python scripts/build_frontend_documentation.py`. |
| `frontend/static/search-index*.json` | Take either side, then `python scripts/build_search_index.py` (last - it reads templates, catalogues, documentation and the version). |
| Embedded blueprints (the output of `scripts/embed_wizard_blueprints.py`) | Resolve `authentik/blueprints/` by hand, then `python scripts/embed_wizard_blueprints.py`. |
| Diagram sources written by `scripts/render_architecture_diagrams.py` | Resolve `ARCHITECTURE.md` by hand, then `uv run python scripts/render_architecture_diagrams.py`. The PNGs are rendered by CI; take either side for them. |
| `RELEASE.md` | Take `main`'s version (`--theirs` when merging main in) - the release workflow writes it (ADR 0048). |

`--ours` / `--theirs` swap meaning during a rebase: in a rebase, `--ours` is the
branch being rebased onto. Since every generated file is rewritten anyway, the
side barely matters - the order of regeneration does.

## 3. Regenerate in order

After all hand-written conflicts are resolved:

```bash
uv lock
uv run python scripts/update_release_schedule.py     # only if it conflicted
uv run python scripts/update_vulnerability_db.py     # only if it conflicted
python scripts/embed_wizard_blueprints.py            # only if it conflicted
python scripts/build_frontend_documentation.py
python scripts/build_search_index.py
```

## 4. Verify and continue

```bash
git diff --check                                     # no leftover conflict markers
grep -rn '^<<<<<<< \|^>>>>>>> ' --exclude-dir=.git . || true
python scripts/build_frontend_documentation.py --check
python scripts/build_search_index.py --check
python scripts/embed_wizard_blueprints.py --check
uv run pytest -q
git add <resolved files>
```

Then tell the user which files were regenerated and which were merged by hand,
and let them run `git merge --continue` / `git rebase --continue` (or do it if
they asked). Never `git merge --abort`, `git reset --hard` or force-push on
your own.
