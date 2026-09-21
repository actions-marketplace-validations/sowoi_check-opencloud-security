"""
OTLP/JSON metrics for OpenCloud scan result documents.

The same families :mod:`opencloud_local_scan.metrics` collected for the
Prometheus exposition, rendered as one ``ExportMetricsServiceRequest`` - the
body an OpenTelemetry collector accepts at ``POST /v1/metrics`` over
OTLP/HTTP. Nothing here decides anything: the names, labels and values are the
exporter's, so a collector and a scrape of the same instance agree.

Written by hand against the protobuf JSON mapping rather than through the
OpenTelemetry SDK, for the reason every other renderer in this package is: a
monitoring host installs one file and its scanner, not an instrumentation
stack. The mapping that matters is that 64-bit integers are strings while
``asDouble`` is a number, and that every attribute is a ``{"key", "value"}``
pair with its type named.

Every family is a gauge - the current reading of something - so a collector
sees the same shape a scrape does rather than counters that appear to reset on
every run.
"""

from __future__ import annotations

import time
from collections.abc import Iterable
from typing import Any

from . import __version__
from .metrics import MetricFamily

SERVICE_NAME = "check-opencloud-security"
SCOPE_NAME = "opencloud_local_scan"


def _attributes(labels: dict[str, str]) -> list[dict[str, Any]]:
    """Render labels as OTLP attributes, which are typed key/value pairs."""
    return [
        {"key": name, "value": {"stringValue": str(value)}}
        for name, value in labels.items()
    ]


def render(
    collections: Iterable[list[MetricFamily]],
    *,
    timestamp_ns: int | None = None,
) -> dict[str, Any]:
    """
    Render one or more hosts' metric families as a single OTLP/JSON document.

    Several hosts are several sets of data points on the *same* metrics rather
    than several documents, because they differ only in their `host` attribute
    - the same reason the Prometheus exposition declares each family once.
    One timestamp covers the whole run: the collections were produced by one
    invocation, and a per-family reading time would suggest a precision this
    does not have.
    """
    moment = str(timestamp_ns if timestamp_ns is not None else time.time_ns())
    metrics: dict[str, dict[str, Any]] = {}

    for families in collections:
        for family in families:
            metric = metrics.get(family.name)
            if metric is None:
                metric = {
                    "name": family.name,
                    "description": family.help_text,
                    "unit": family.unit,
                    "gauge": {"dataPoints": []},
                }
                metrics[family.name] = metric
            metric["gauge"]["dataPoints"].extend(
                {
                    "attributes": _attributes(sample.labels),
                    "timeUnixNano": moment,
                    "asDouble": sample.value,
                }
                for sample in family.samples
            )

    return {
        "resourceMetrics": [
            {
                "resource": {
                    "attributes": _attributes(
                        {
                            "service.name": SERVICE_NAME,
                            "service.version": __version__,
                        }
                    )
                },
                "scopeMetrics": [
                    {
                        "scope": {"name": SCOPE_NAME, "version": __version__},
                        "metrics": list(metrics.values()),
                    }
                ],
            }
        ]
    }
