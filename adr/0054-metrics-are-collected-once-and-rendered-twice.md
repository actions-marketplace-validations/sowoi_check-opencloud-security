# ADR 0054: Metrics are collected once and rendered twice

- Status: Accepted
- Date: 2026-09-16

## Context

`--format prometheus` and the built-in `/metrics` exporter publish eight
metric families derived from a scan result document. Deciding what those
numbers *are* is not formatting: `opencloud_security_hardenings_missing_total`
has to skip the measures an operator waived, for the same reason the plugin's
own perfdata does, or an alert rule fires for exactly the findings somebody
switched off (see the comments that rule carries in
`opencloud_local_scan/metrics.py`). That reading lived inside
`opencloud_local_scan/prometheus.py`, interleaved with the text exposition it
was being rendered into.

OTLP is now the format many deployments reach for first: a collector is
already running, and adding a scrape target for a plugin that scans on a timer
is the awkward part. Writing an OTLP renderer against the result document
directly would have meant a second module deciding, again, which hardening
measures count - and ADR 0026 already records what that costs, where two
independent SARIF renderers exist in this repository and nothing but review
keeps their conventions in step. Two *metric* renderers disagreeing is worse
than two SARIF renderers disagreeing: the numbers are what alerts fire on, and
an instance that reads 0 in Grafana and 3 in a collector's backend has no
obviously wrong side.

## Decision

The reading and the rendering are separated. `opencloud_local_scan/metrics.py`
holds `collect()`, which turns one scan outcome into `MetricFamily` objects -
name, help text, unit and samples, with labels as plain strings and no wire
format anywhere in it. `prometheus.py` and the new `otlp.py` are formatters
over that one collection, and `prometheus.render()` keeps its signature and
its byte-for-byte output so that every existing scrape, alert rule and test
is unaffected.

`--format otlp` prints one OTLP/JSON `ExportMetricsServiceRequest` covering
every scanned host - several hosts are more data points on the same metrics,
distinguished by their `host` attribute, exactly as they are repeated samples
in a scrape. Every family is a gauge, which is what the exposition has always
typed them as, including the `_total` names: they are counts as they stand,
not monotonic counters.

**The plugin prints the document and never dials a collector.** The pipe to
`curl` in the documentation is the whole delivery mechanism. A `--otlp-endpoint`
would make the scanner a client of a second service - with its own proxy, TLS
and credential questions, its own retry behaviour and its own failure mode
inside a check whose exit code Icinga is waiting for - to replace one shell
pipe in a timer that already exists.

`--format otlp` exits `0` whatever the instance scored, as `--format
prometheus` already does, and reports a failed scan as
`opencloud_security_scrape_success 0`. A metrics pipeline has no other way to
distinguish an unreachable instance from a scan that stopped running, and the
exit code is how the *judging* formats speak.

## Consequences

The waiver rule, and every other decision about what a number means, now has
one home and one set of tests, and a third metric format would be a renderer
rather than a third opinion.

`MetricFamily` becomes an internal interface between the library and its
renderers. It is not part of the result document and not something the plugin
prints, so it can change with its callers - but it is now the place a new
metric is added, and adding one to a renderer instead would be the mistake
this record exists to prevent.

OTLP is hand-rendered against the protobuf JSON mapping rather than produced
by the OpenTelemetry SDK. A monitoring host installs one file and its scanner;
the mapping that matters here is small - 64-bit integers as strings,
`asDouble` as a number, typed attribute values - and a test asserts it.
Anything beyond metrics (traces, spans, the OTLP gRPC transport) stays out of
scope: this is an export of a scan, not instrumentation of one.

## Alternatives considered

**Render OTLP from the Prometheus text.** A parser for a format we just
produced, which would have to re-derive labels and types from strings, and
would silently mistype any family whose name conventions changed.

**Push to a collector from the plugin (`--otlp-endpoint`).** Rejected above:
egress, credentials and retries inside a monitoring check, for what a pipe
already does. It is also the pattern the webhook already covers for anybody
who wants the plugin itself to deliver something.

**Make OTLP a `--webhook-format`.** The webhook sends a *judged* payload -
status, exit code, message - on a trigger, which is a different thing from a
periodic reading of every host. Metrics on a webhook trigger would report only
the hosts that alerted, which is the one thing a metrics pipeline must not do.
