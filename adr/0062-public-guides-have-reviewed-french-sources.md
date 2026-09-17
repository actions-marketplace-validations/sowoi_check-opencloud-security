# Public guides have French source pages

- **Status:** Accepted; its Spanish English-fallback statement superseded by ADR 0063
- **Date:** 2026-09-16

## Context

The public documentation is authored in English and has a reviewed German
source tree. French visitors previously saw the English guide body even when
the rest of the interface was translated.

## Decision

Keep a French Markdown source for every public guide under `docs/fr/`. The
frontend generator, documentation route and search-index builder serve those
pages for the French locale. Spanish remains an explicit English fallback for
now; its interface translation is not changed by this decision.

The French files retain the same code examples, links and section anchors as
the English sources so a language switch does not change the documented
commands or navigation targets.

## Consequences

Adding or removing a public guide requires updating the English, German and
French source sets together. Generated French templates and the French search
overlay are checked in and must be regenerated with the existing build
scripts.
