---
name: check-changelog-docs
description: Check that every new CHANGELOG.md entry under ## [Unreleased] in the Added or Changed section is documented where a reader would look - README option table and table of contents, the example YAML, docs/ guides in all four languages, docs/webapp.md, the docs/README.md index, webapp/documentation.py and the generated /documentation pages. Reports gaps; fixes them only when asked. Use when asked to check for missing documentation, before opening a pull request with Added/Changed entries, or after /preflight.
---

# Check changelog entries for missing documentation

A `### Added` or `### Changed` entry describes something an operator, a
contributor or a web visitor can now do or will notice. This skill checks
that each **new** such entry is reflected in the documentation that
AGENTS.md (section "Documentation") requires. `Fixed`, `Security`,
`Removed`, `Deprecated` and `Documentation` entries are out of scope.

The `changelog_docs_gate.py` PreToolUse hook denies a `git commit` that
adds `Added`/`Changed` lines to `CHANGELOG.md` once and points here. Run
this skill, show the report, then retry the same commit - the hook lets the
same entries through the second time.

The skill **reports first**. Edit files only when the user asks for fixes,
and then follow the matching skill (`/add-setting`,
`/add-translation-string`, `/new-adr`) rather than hand-rolling it.

## 1. Collect the new entries

Only entries that are new on this branch count - not the whole
`[Unreleased]` section that other merged work already filled.

```bash
git fetch origin main --quiet
git diff origin/main...HEAD -- CHANGELOG.md
git diff -- CHANGELOG.md            # uncommitted work too
```

From the added lines, take each bullet (a `- ` line plus its indented
continuation) that sits under `### Added` or `### Changed` inside
`## [Unreleased]`. If the diff is ambiguous, read the section in
`CHANGELOG.md` and match bullets by text. If there are no such entries, say
so and stop.

Also note the code the branch touched (`git diff --stat origin/main...HEAD`
plus uncommitted changes) - it tells you what each entry actually changed.

## 2. Classify each entry

Decide, from the entry text and the diff, which kinds of change it is. One
entry can be several.

| Kind | Recognise it by |
|------|-----------------|
| Plugin/scanner option | new argparse flag, `COS_` variable, `factory.py` / `config.py` field |
| Web setting | new `COS_WEB_*` variable in `webapp/` |
| Scanner check / hardening | new entry in `hardening.py`, new extra check or finding |
| Output / interface | new output format, perfdata label, webhook or result-document key, exit behaviour |
| Web API / MCP | new or changed route, request field, MCP tool, OpenAPI schema |
| Frontend text / page | new template, visible string, new guide page |
| New guide | new file under `docs/` |
| Contributor tooling | skills, agents, hooks, scripts, CI, tests only |
| Architecture | layer boundary, public interface, security or deployment model |

## 3. Check the required places

For each kind, check each place with `grep`/Read, searching for the flag,
variable, key, route or page name - not for the changelog wording.

**Plugin/scanner option**
- `README.md` CLI option table has a row; the table of contents still
  matches the headings.
- `config/check-opencloud-security.example.yml` has the key.
- `docs/configuration.md` / `docs/cli-reference.md` (and `docs/de/`,
  `docs/fr/`, `docs/es/` counterparts when the English page changed).
- `docs/scanner-cli.md` if the `scan` subcommand gained it.
- Anything else `/add-setting` lists (setup wizard, web pinning).

**Web setting**
- A row in the settings table in `docs/webapp.md`.
- An entry in `docker/docker-compose.yml`.
- `webapp/README.md` does not contradict `docs/webapp.md`.

**Scanner check / hardening**
- `docs/scanner-checks.md` / `docs/hardening.md` (and the three
  translations) describe it.
- `opencloud_local_scan/README.md` if the result document changed.

**Output / interface**
- `docs/output-formats.md`, `docs/prometheus.md` or the webhook section of
  `README.md`, whichever the change affects.
- Result-document keys named in camelCase, plugin output in snake_case.

**Web API / MCP**
- `webapp/README.md` (API and input restrictions) and `docs/webapp.md`.
- `docs/mcp.md` for an MCP tool.

**Frontend text / page**
- The string exists in all four `webapp/locales/*.py` catalogues with the
  same keys (`/add-translation-string`).
- German uses "du", never `Sie`/`Ihr`/`Ihnen`.

**New guide**
- The page exists in `docs/`, `docs/de/`, `docs/fr/` and `docs/es/`.
- A row in the `docs/README.md` index.
- An entry in `webapp/documentation.py`.
- Relative links point one level up (`../README.md#anchor`).

**Contributor tooling**
- A new skill or agent is mentioned where contributors find it
  (`CLAUDE.md` / `AGENTS.md` / `tests/README.md`), if the existing ones
  are. A new script with a CI `--check` mode is listed in the AGENTS.md
  script table and the CLAUDE.md command list.

**Architecture**
- An ADR exists in `adr/` and a row in `adr/README.md`; the changelog entry
  links it. If missing, propose `/new-adr` - do not write it unasked.

**Always, when any `docs/` or README source changed**

```bash
python scripts/build_frontend_documentation.py --check
python scripts/check_documentation_links.py --warn-only   # only if links were added
```

A stale check means the generated `/documentation` pages need
regenerating.

## 4. Report

One table, one row per entry and place checked:

| Entry (short) | Kind | Place | Status | What is missing |
|---------------|------|-------|--------|-----------------|

Status is `ok`, `missing`, `stale` or `n/a`. Below it, list only the gaps
as concrete actions ("add a `--foo` row to the README option table",
"add `docs/es/foo.md`"). If everything is documented, say so in one line.

Do not propose documenting internals the changelog entry does not expose to
a reader, and do not treat a missing translation of an unchanged page as a
gap.

## Rules that still apply

- Never edit `RELEASE.md`, the README release-schedule block, or generated
  files by hand - regenerate them.
- Never use real hostnames in documentation examples; use
  `opencloud.example.com` or a 192.0.2.x address.
- Never bump the version.
- Adding this documentation is itself a change: it rides on the existing
  changelog entry, not a new one, unless the user says otherwise.
