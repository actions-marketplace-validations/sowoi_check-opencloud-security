---
name: mutation-test
description: Run manual mutation testing (mutmut) on check-opencloud-security's plugin or scanner functions and report which surviving mutants are real test gaps - a wrong verdict, exit code or silenced alert no test notices - and which are noise. Manual only, never in CI. Use when asked for mutation tests, how strong the tests are, or whether the tests would catch a wrong rating.
argument-hint: "[function or module ...]"
context: fork
agent: mutation-tester
background: false
---

# Mutation test

Arguments: $ARGUMENTS - functions (`_evaluate_rating`), methods
(`Comparison.regressed`) or modules (`opencloud_local_scan/baseline.py`) to
mutate. Empty means the judging core: `_evaluate_rating`, `_apply_baseline`
and `check_vulnerabilities` in `check_opencloud_security.py`.

This skill runs in the `mutation-tester` agent
(`.claude/agents/mutation-tester.md`), so the long mutmut output stays out of
the main conversation and nothing is changed while it runs. Follow that
agent's steps: turn the arguments into mutmut name globs, run only those,
triage every survivor into gap, unreachable or noise, and report.

Background:

- mutmut is a reviewed dependency in its own `mutation` group
  (`security/dependencies/mutmut.yml`, ADR 0060). It is never installed by CI
  or a plain `uv sync`, and never run through `uvx`.
- `[tool.mutmut]` in `pyproject.toml` fixes what may be mutated and which
  fast, in-process test files judge the mutants. Subprocess tests
  (`test_e2e_cli.py`) and browser tests cannot see a mutant and are left out
  on purpose.
- A run of the three default functions takes a few minutes; a whole module
  can take far longer - say so before starting one.

Afterwards, in the main conversation: offer to write the tests the report
names under "Gap". Surviving mutants are a to-do list, not a score - there is
no threshold to reach.
