"""Prometheus text exposition for OpenCloud scan result documents."""

from __future__ import annotations

from typing import Any

from .metrics import MetricFamily, collect


def _escape_label(value: object) -> str:
    """Escape arbitrary scan values for a Prometheus label string."""
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("\r", "\\r")
        .replace("\n", "\\n")
        .replace('"', '\\"')
    )


def _labels(values: dict[str, str]) -> str:
    """Render label values safely, including hostnames and scanner metadata."""
    return "{" + ",".join(
        f'{name}="{_escape_label(value)}"' for name, value in values.items()
    ) + "}"


def render_families(families: list[MetricFamily]) -> str:
    """Render collected metric families in Prometheus' text exposition format."""
    lines: list[str] = []
    for family in families:
        lines.append(f"# HELP {family.name} {family.help_text}")
        lines.append(f"# TYPE {family.name} gauge")
        lines.extend(
            f"{family.name}{_labels(sample.labels)} {sample.value:g}"
            for sample in family.samples
        )
    return "\n".join(lines) + "\n"


def render(
    host: str,
    result: dict[str, Any] | None,
    *,
    duration_seconds: float,
    success: bool,
) -> str:
    """
    Convert one scan outcome to Prometheus metrics.

    A failed scan emits only its duration and scrape-success samples. This
    prevents stale findings from being presented as current evidence.
    """
    return render_families(
        collect(host, result, duration_seconds=duration_seconds, success=success)
    )
