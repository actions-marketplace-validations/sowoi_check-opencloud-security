# ADR 0075: The remediation plan groups changes by where they are made

- Status: Accepted
- Date: 2026-09-24
- Extends: ADR 0012

## Context

ADR 0012 made the remediation plan a derived part of every result: an
ordered list of fixes, each with the rating it produces. The order answers
"what first". It does not answer the question an operator has once they sit
down to work: "I have the reverse proxy configuration open - what do I change
while I am here?"

Eleven findings are rarely eleven edits. Missing headers are one header
block, certificate complaints are one new certificate, three exposed paths
are one proxy rule, and one update closes every advisory matching the
installed release. The ordered list scatters those across its steps, and
leaves out findings that cap nothing - a missing header - even though they
are a line in the same file.

## Decision

**`remediationPlan.groups` places every open, actionable, unwaived finding
in the system its fix is made in** - `reverseProxy`, `identityProvider`,
`opencloud` or `dnsZone`. The table is explicit, in
`opencloud_local_scan/remediation_groups.py`, keyed by catalogue id; a test
fails when a catalogued check has no entry, rather than letting it fall into
a default group. It is not inferred from the wording of a fix.

**A change is one edit and lists every finding it resolves.** Members of a
finding family share their family's change; related checks share a named
change from `SHARED_CHANGES`; a shared change may only group checks fixed in
the same place, which a test also enforces.

**Every rating beside a change is replayed.** The planner hands the grouping
the same rating arithmetic its steps use, so "this change alone gives 4/5" is
the rating function run with those findings removed and the version ceiling
lifted only when the update is among them. Blocked (hardcoded) and waived
findings are not offered as changes, for the same reasons the plan gives.

**It stays a measurement.** The library groups and replays numbers; the
plugin and the web layer add the letters, exactly as they do for the steps.

## Consequences

The result document gains two additive keys under `remediationPlan`:
`groups` and `groupSummary`. No existing key changed meaning. The plugin's
`--debug` output, the web dashboard, the remediation bundle, the OpenAPI
schema and the `plan_remediation` MCP tool carry them.

Adding a hardening check now also means placing it in `CHECK_TARGETS`.

Rejected: grouping by the catalogue's `category`, which says what a check is
about, not where it is fixed - cookies and headers are both set at the proxy,
while "authentication" spans OpenCloud and the identity provider.
