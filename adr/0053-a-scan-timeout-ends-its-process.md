# ADR 0053: A scan timeout ends its process

- Status: Accepted
- Date: 2026-09-15

## Context

The ARQ worker limited how long it awaited a blocking scanner thread, not
how long that thread ran. A slow target could keep its probes alive after
the worker had released its slot. More queued scans then multiplied the
configured concurrency. Socket read timeouts alone do not stop a peer that
keeps sending small amounts of data.

## Decision

Each web scan runs in a spawned child process. The worker passes the same
validated target, operator settings and reference-data snapshot to the same
runner. The child revalidates the target as before. Only its result or a
classified failure returns over a private pipe; it never accesses Redis.

Timeout and cancellation kill and reap the child, including its probe
threads, before the ARQ job releases its slot. The parent alone logs the
lifecycle and stores results. The plugin and local scanner API are unchanged.

Incoming HTTP mutation requests are separately bounded before parsing: at
most 1 MiB and 30 seconds to receive the body, including chunked requests.
These are service-side bounds, not caller options. Oversized requests return
413 and incomplete bodies time out with 408. Ordinary submissions still
queue and are not rejected because workers are busy.

## Consequences

Web workers need permission to spawn child processes. Each active scan adds
one Python process and startup cost, bounded by the existing worker count.
There is no process pool with a timed-out scan hidden inside it. The
reference-data objects must remain serializable; private IPC is not a public
deserialization endpoint. In-memory monkeypatches do not cross the spawn
boundary, so tests exercise the child directly or replace the execution seam.

The body limit applies equally to forms, REST, admin actions and MCP. There
is no upload endpoint requiring larger bodies. Deployment-level connection
and bandwidth limits remain necessary; these bounds are not a DDoS defence.

## Alternatives considered

- Cancelling a thread future does not stop running Python or close its sockets.
- Cooperative cancellation cannot interrupt a blocked resolver or a slow
  response read, and would spread web worker policy into the scanner library.
- Forking inherits thread locks and connections from a live async worker;
  spawning starts a clean interpreter instead.
