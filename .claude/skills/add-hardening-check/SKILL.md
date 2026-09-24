---
name: add-hardening-check
description: Add a new hardening measure, extra check or advisory observation to the check-opencloud-security scanner - the hardening.py catalogue entry, the measurement in scanner.py, the fake OpenCloud behaviour, tests, documentation and changelog. Use when asked to add a new scanner check, hardening flag, finding or header check.
argument-hint: <check id and what it should detect>
---

# Add a hardening check

Request: $ARGUMENTS

The scanner **measures**; the plugin judges and the web application serves. A
new check lives in `opencloud_local_scan/` and produces evidence in the result
document - never a WARNING/CRITICAL decision.

## 0. Decide before writing code

Answer each of these and state the answers to the user before editing:

1. **Can an operator actually change it?** Verify against the OpenCloud source
   (e.g. `services/frontend/pkg/revaconfig/config.go`). A flag OpenCloud
   hardcodes gets `actionable=False` and stays out of the alert line, the
   `hardenings_missing` metric and the webhook.
2. **Which dictionary does it belong in?** (`opencloud_local_scan/hardening.py`)
   - `HARDENINGS` - an OpenCloud setting the operator controls. It becomes a
     waiver tick box in the web catalogue.
   - `CHECKS` - an extra check (reported under `extraChecks`).
   - `ADVISORY_CHECKS` - something **no** OpenCloud deployment passes by
     default. Reported, explained, never alerted on and never offered as a
     waiver (ADR 0028, ADR 0034). Do not put such a check in `HARDENINGS`.
3. **Is the probe allowed?** Only `GET`, `HEAD`, `PROPFIND` or `TRACE`; only
   the origin the scan was pointed at, never an address taken from the target's
   response (ADR 0036); DNS only through the system resolver (ADR 0024); no
   credential except the documented demo passwords. If the check cannot be
   measured, it is **absent** from the result, never passing (ADR 0013).
4. **Severity and category.** Category must be one of `CATEGORIES`. Severity
   caps the rating via `SEVERITY_RATING_CAP` (critical 2, high 3, medium 4,
   low 5).
5. **Does it need an ADR?** A new kind of probe or a new trust decision does -
   use `/new-adr`.

## 1. Find the wiring by example

Pick the most similar existing check and follow every place it appears:

```bash
grep -rn "securityTxtPublished" --exclude-dir=.git --exclude-dir=__pycache__ .   # advisory check
grep -rn "basicAuthDisabled"   --exclude-dir=.git --exclude-dir=__pycache__ .   # hardening
```

Ignore generated hits (`frontend/static/search-index*.json`,
`frontend/templates/docs/`) - they are regenerated below.

## 2. Implement

1. **`opencloud_local_scan/hardening.py`** - a `Hardening(...)` entry with
   `id`, `category`, `title` (short, readable in a notification), `meaning`
   (what was observed and why it matters), `remediation` (names the setting),
   `reference` (a `DOCS_*` constant or official URL), `setting`, and
   `env_fix` / `header_fix` only when the value is not deployment-specific.
2. **`opencloud_local_scan/scanner.py`** - the measurement, registered where
   the similar check is. Result keys are **camelCase**. Keep concurrency per
   call site (`_run_all`), never nested; probe a second base URL with
   `_Probe.derive(url)`, never a shared session.
3. **`tests/fake_opencloud.py`** - an `InstanceBehaviour` field that makes the
   fake instance pass or fail the check.
4. If a `snippets.py` rendering applies (Compose, .env, nginx, Caddy,
   Traefik), confirm the new `env_fix` / `header_fix` renders.
5. **`opencloud_local_scan/remediation_groups.py`** - place the check in
   `CHECK_TARGETS` (the reverse proxy, the identity provider, OpenCloud or
   the DNS zone - where its fix is made), and add it to a `SHARED_CHANGES`
   entry when one edit also resolves related checks.
   `tests/test_remediation_groups.py` fails until it is placed.

## 3. Tests

Sentence names, one-line docstrings, derived from a real scan of the fake
instance - not hardcoded lists:

- the check fails when the fake instance is misconfigured **and** passes when
  it is not;
- it is absent when it cannot be measured;
- it caps the rating as its severity says (or, for an advisory check, never
  reaches the alert line, the metric, the webhook or the waiver list - see
  `tests/test_advisory_checks.py`);
- a waiver suppresses the alert but keeps the finding with `"ignored": true`
  (hardenings only);
- `tests/test_hardening.py` still passes (known category, catalogued once).

## 4. Documentation and regeneration

- `docs/scanner-checks.md` - describe the check in the right section.
- `opencloud_local_scan/README.md` - the result document fields, if it adds any.
- `CHANGELOG.md` - an entry under `## [Unreleased]`, `### Added`.

```bash
python scripts/build_frontend_documentation.py
python scripts/build_search_index.py
uv run pytest tests/test_hardening.py tests/test_advisory_checks.py -q
uv run pytest -q
uvx ruff check .
uv run mypy --config-file mypy.ini
python scripts/check_documentation_links.py --list   # confirms the new reference is picked up
```
