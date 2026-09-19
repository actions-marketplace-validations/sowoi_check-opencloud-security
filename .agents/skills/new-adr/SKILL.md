---
name: new-adr
description: Write a new architectural decision record in adr/ for check-opencloud-security - next zero-padded number, the house template, the index row in adr/README.md, and superseded markers on older records. Use when a change alters a layer boundary, public interface, security or deployment model, data lifecycle, or long-lived dependency, or when asked to write an ADR.
argument-hint: <the decision in one sentence>
---

# New ADR

Request: $ARGUMENTS

## 0. Is an ADR warranted?

Yes for a durable change to a layer boundary, public interface, security or
deployment model, data lifecycle, or long-lived dependency. **No** for routine
implementation details or temporary tasks - say so and stop.

Read the accepted ADRs in the same area first (`adr/README.md` index). If the
new decision changes one of them, this ADR supersedes or extends it - never
rewrite an accepted record's decision.

## 1. Number and filename

```bash
ls adr/ | grep -E '^[0-9]{4}-' | sort | tail -1
```

Next number, zero-padded, never reused. Filename:
`adr/NNNN-the-decision-as-a-sentence.md` - lowercase, hyphenated, and
phrased as the decision itself (see existing names such as
`0044-the-operator-area-may-write-the-exclusions.md`).

## 2. Write it

```markdown
# ADR NNNN: The decision as a sentence

- Status: Proposed
- Date: YYYY-MM-DD
- Extends: ADR XXXX          (only if it builds on one)
- Supersedes: ADR XXXX       (only if it replaces one)

## Context

What problem requires a durable decision? The gap, the constraint, the
incident. Concrete, no real hostnames (use opencloud.example.com).

## Decision

The chosen approach, as bold lead-ins with the specifics: names of settings,
modules, limits.

## Consequences

What becomes easier, harder, required, or deliberately out of scope.

## Alternatives considered

Each credible alternative and why it was rejected.
```

- Status is `Proposed` unless the user says the decision is accepted (it
  usually is when the ADR lands with the implementation - ask if unclear).
- Date is today's date.
- Match the tone of recent records: explain *why*, name the files and settings.

## 3. Update the index and older records

- Add a row to the table in `adr/README.md`:
  `| [NNNN](NNNN-....md) | Title as in the record | Status |`
- If it supersedes an older ADR, change **only** the older record's `Status`
  line (`Superseded by ADR NNNN`, or `Accepted; its <part> superseded by ADR
  NNNN`) and its index row. Leave its decision text alone.
- If `AGENTS.md`, `CLAUDE.md` or `.github/copilot-instructions.md` cite the
  rule, add the ADR link there, keeping the three consistent.

## 4. Changelog

ADRs normally ride along with the change they document; mention the ADR in
that change's `CHANGELOG.md` entry. A standalone ADR gets a
`### Documentation` entry under `## [Unreleased]`.
