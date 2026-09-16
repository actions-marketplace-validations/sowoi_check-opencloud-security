"""
The metric families a scan result yields, independent of any wire format.

Prometheus text and OTLP are two renderings of one reading of a scan, not two
readings. What counts as a missing hardening measure - and, above all, that a
waived one does not - is decided here once, so an alert rule written against
the exporter and a dashboard fed from a collector cannot disagree about the
same instance. The renderers in :mod:`opencloud_local_scan.prometheus` and
:mod:`opencloud_local_scan.otlp` only format what this module counted.

Every family is a gauge: each one is the current reading of something, and
even the `_total` names are counts as they stand rather than monotonic
counters, which is how the Prometheus exposition has always typed them.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

# OTLP wants a unit for every metric; Prometheus carries it in the name
# instead. UCUM, in which "1" is the unit of a dimensionless count.
UNIT_COUNT = "1"
UNIT_SECONDS = "s"
UNIT_DAYS = "d"


@dataclass(frozen=True)
class Sample:
    """One reading, with the labels that identify what was read."""

    labels: dict[str, str]
    value: float


@dataclass(frozen=True)
class MetricFamily:
    """One named gauge and every sample of it this scan produced."""

    name: str
    help_text: str
    unit: str
    samples: list[Sample]


def _family(
    name: str,
    help_text: str,
    unit: str,
    samples: list[tuple[dict[str, object], float]],
) -> MetricFamily:
    return MetricFamily(
        name=name,
        help_text=help_text,
        unit=unit,
        samples=[
            Sample(labels={key: str(value) for key, value in labels.items()}, value=float(value))
            for labels, value in samples
        ],
    )


def collect(
    host: str,
    result: dict[str, Any] | None,
    *,
    duration_seconds: float,
    success: bool,
) -> list[MetricFamily]:
    """
    Read one scan outcome as metric families.

    A failed scan yields only its duration and scrape-success families. This
    prevents stale findings from being presented as current evidence.
    """
    outcome = result or {}
    product = outcome.get("product") or "unknown"
    domain = outcome.get("domain") or host
    version = outcome.get("version") or "unknown"
    base_labels: dict[str, object] = {"host": host}
    families: list[MetricFamily] = []

    if success:
        rating = outcome.get("rating")
        if isinstance(rating, int):
            families.append(
                _family(
                    "opencloud_security_rating_score",
                    "OpenCloud security rating score from zero to five.",
                    UNIT_COUNT,
                    [
                        (
                            {
                                "host": host,
                                "domain": domain,
                                "product": product,
                                "version": version,
                            },
                            rating,
                        )
                    ],
                )
            )

        vulnerabilities = outcome.get("vulnerabilities")
        counts = Counter(
            str(entry.get("severity") or "unknown").lower()
            for entry in vulnerabilities if isinstance(entry, dict)
        ) if isinstance(vulnerabilities, list) else Counter()
        families.append(
            _family(
                "opencloud_security_vulnerabilities_total",
                "Known OpenCloud vulnerabilities by severity.",
                UNIT_COUNT,
                [
                    ({"host": host, "severity": severity}, count)
                    for severity, count in sorted(counts.items())
                ]
                or [({"host": host, "severity": "unknown"}, 0)],
            )
        )

        # A waiver hides an alert, so it has to hide this one too. The scan
        # records what the operator accepted under `ignored`; counting those
        # anyway would leave an alert built on this metric firing for exactly
        # the measures the operator switched off, while the plugin's own
        # `hardenings_missing` perfdata for the same instance reported zero.
        ignored = outcome.get("ignored")
        waived = {str(name) for name in ignored} if isinstance(ignored, list) else set()

        hardenings = outcome.get("hardenings")
        missing_hardenings = sum(
            not enabled for name, enabled in hardenings.items() if name not in waived
        ) if isinstance(hardenings, dict) else 0
        setup = outcome.get("setup")
        if isinstance(setup, dict):
            https = setup.get("https")
            if (
                isinstance(https, dict)
                and not https.get("enforced", True)
                and "httpsEnforced" not in waived
            ):
                missing_hardenings += 1
            headers = setup.get("headers")
            if isinstance(headers, dict):
                missing_hardenings += sum(
                    not enabled for name, enabled in headers.items() if name not in waived
                )
        families.append(
            _family(
                "opencloud_security_hardenings_missing_total",
                "Missing OpenCloud hardening measures.",
                UNIT_COUNT,
                [(base_labels, missing_hardenings)],
            )
        )

        # Same rule as `failed_extra_checks()` in the scanner, which is the
        # canonical reading of this list: a check the operator has explicitly
        # accepted is still in the document, but it is not a failure to report.
        extra_checks = outcome.get("extraChecks")
        failed_checks = (
            sum(
                isinstance(check, dict)
                and check.get("passed") is False
                and not check.get("ignored", False)
                for check in extra_checks
            )
            if isinstance(extra_checks, list)
            else 0
        )
        families.append(
            _family(
                "opencloud_security_failed_extra_checks_total",
                "Failed additional OpenCloud security checks.",
                UNIT_COUNT,
                [(base_labels, failed_checks)],
            )
        )

        lifecycle = outcome.get("lifecycle")
        release_type = "unknown"
        if isinstance(lifecycle, dict) and lifecycle.get("releaseType"):
            release_type = str(lifecycle["releaseType"])
        # Deliberately its own family rather than a negative
        # `support_days_remaining`: a rolling or production release that has
        # not been dated yet reports no days at all, and "unknown" must not
        # read as "expiring today" in the one alert nobody may miss.
        families.append(
            _family(
                "opencloud_security_end_of_life",
                "Whether the OpenCloud release has reached end of life.",
                UNIT_COUNT,
                [
                    (
                        {"host": host, "release_type": release_type},
                        int(bool(outcome.get("EOL"))),
                    )
                ],
            )
        )

        if isinstance(lifecycle, dict) and isinstance(lifecycle.get("daysRemaining"), int):
            families.append(
                _family(
                    "opencloud_security_support_days_remaining",
                    "Days remaining before the OpenCloud release reaches end of life.",
                    UNIT_DAYS,
                    [
                        (
                            {
                                "host": host,
                                "release_type": lifecycle.get("releaseType") or "unknown",
                            },
                            lifecycle["daysRemaining"],
                        )
                    ],
                )
            )

        updates = outcome.get("updates")
        if isinstance(updates, dict):
            families.append(
                _family(
                    "opencloud_security_update_available",
                    "Whether an OpenCloud update is available.",
                    UNIT_COUNT,
                    [
                        (
                            {
                                "host": host,
                                "target_version": updates.get("availableVersion")
                                or updates.get("version")
                                or "unknown",
                            },
                            int(bool(updates.get("available"))),
                        )
                    ],
                )
            )

    families.append(
        _family(
            "opencloud_security_scan_duration_seconds",
            "Duration of the OpenCloud security scan.",
            UNIT_SECONDS,
            [(base_labels, duration_seconds)],
        )
    )
    families.append(
        _family(
            "opencloud_security_scrape_success",
            "Whether the OpenCloud security scan completed successfully.",
            UNIT_COUNT,
            [(base_labels, int(success))],
        )
    )
    return families
