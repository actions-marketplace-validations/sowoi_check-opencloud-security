# ADR 0059: A comparison refuses two different instances

- Status: Accepted
- Date: 2026-09-16
- Supersedes: ADR 0029 (its "different instances are compared, not refused" rule)

## Context

[ADR 0029](0029-a-comparison-is-two-live-results-and-one-arithmetic.md)
decided that two documents describing different instances are compared and
the answer carries `sameTarget: false`, on the grounds that comparing staging
with production is a fair question.

In practice the web page made that question far too easy to ask by accident.
`/compare` takes two uuids a reader pastes in, and a reader holding several
results pastes the wrong one. The page then drew a full verdict - improved,
regressed, resolved, introduced - between two unrelated instances, and the
one line saying so sat above numbers that looked exactly like an answer.
The report upload of
[ADR 0057](0057-an-uploaded-report-is-evidence-not-a-scan.md) made it easier
still: a file from `staging.example.com` compared with a scan of
`opencloud.example.com` produced a confident "improved".

Meanwhile `check-opencloud-scanner diff` has always refused two different
hosts unless `--allow-different-hosts` is passed, for the reason its
documentation gives: "did the fix work" is a question about one instance, and
two hosts compared by accident is a wrong answer nobody notices. The three
surfaces ADR 0029 wanted to agree did not agree on this.

## Decision

**`workflows.compare_documents` refuses two documents that do not describe
the same instance, on every surface.**

- `workflows.refuse_different_instances` compares the documents' `domain`,
  trimmed, lowercased and without a trailing dot. A mismatch raises
  `WorkflowError` with status **422**, `retryable: false`.
- A document that names **no instance** is refused as well: it cannot be shown
  to be the same one. Every result this scanner writes, and every report
  `webapp/imports.py` rebuilds, carries `domain`.
- `compare_documents` runs the check, so the `/compare` page, the report upload
  (`POST /compare`) and the MCP tool `compare_scans` all refuse alike. The web
  pages show the translated `compare.error.different_targets`; the MCP tool
  returns the workflow's English message.
- There is **no opt-in** on the web or MCP surfaces. A request chooses what to
  compare, not whether the rules apply. The CLI keeps
  `--allow-different-hosts`, because an operator comparing two archived files
  on their own machine is a different situation from a stranger's browser.
- `sameTarget` stays in the answer and is always `true`, so a client that
  reads it keeps working.

## Consequences

- A reader or an agent can no longer get a verdict about two unrelated
  instances by pasting the wrong uuid or uploading the wrong file.
- The web and MCP surfaces now agree with the CLI's default.
- Comparing staging with production is no longer possible in the web service.
  Anybody who wants it can download both JSON results and run
  `check-opencloud-scanner diff --allow-different-hosts`.
- The "different instances" warning card and its string are gone from
  `compare.html` and the four catalogues. The new refusal replaces them.

## Alternatives considered

**Keep the warning, make it more prominent.** Rejected: the numbers below it
are still drawn, and a verdict reads as an answer however loud the caveat
above it is.

**An "allow different instances" checkbox on the page and a flag on the
tool.** Rejected: nobody asked for it, and it brings back the accident it
guards against, since the box gets ticked once and then stays ticked. The CLI
already covers the deliberate case.

**Refuse on the web pages only.** Rejected: ADR 0029's point was one
arithmetic and one set of rules across surfaces, and an agent pasting the
wrong uuid is the same mistake as a reader doing it.
