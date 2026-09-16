"""
--format otlp: the Prometheus metrics, rendered as the body an OpenTelemetry
collector accepts. The property worth protecting is that the two are one
reading of a scan and not two, so most of this compares them against each
other rather than against a hardcoded list that would go stale.
"""

from __future__ import annotations

import json

from opencloud_local_scan.metrics import collect
from opencloud_local_scan.otlp import render
from opencloud_local_scan.prometheus import render_families
from tests.fake_opencloud import FakeOpenCloud, InstanceBehaviour
from tests.test_e2e_cli import OK, run_plugin

RESULT = {
    "domain": "cloud.example.com",
    "product": "OpenCloud",
    "version": "7.2.0",
    "rating": 4,
    "vulnerabilities": [{"id": "CVE-2026-0001", "severity": "high"}],
    "hardenings": {"hstsLongMaxAge": False, "basicAuthDisabled": True},
    "extraChecks": [{"id": "tlsTrusted", "passed": False}],
    "lifecycle": {"daysRemaining": 42, "releaseType": "production"},
    "updates": {"available": True, "availableVersion": "7.4.0"},
}


def _metrics(document: dict) -> dict[str, dict]:
    """The metrics of an OTLP document, keyed by name."""
    scope = document["resourceMetrics"][0]["scopeMetrics"][0]
    return {metric["name"]: metric for metric in scope["metrics"]}


def _attributes(point: dict) -> dict[str, str]:
    return {item["key"]: item["value"]["stringValue"] for item in point["attributes"]}


def test_otlp_reports_the_same_metrics_as_the_prometheus_exposition():
    """
    A collector and a scrape of the same instance must not disagree.

    Both formats render one collection, so every metric name the text
    exposition declares has to appear in the OTLP document and vice versa -
    if one renderer ever grows a metric of its own, this fails.
    """
    families = collect("opencloud.example.com", RESULT, duration_seconds=1.25, success=True)
    exposition = render_families(families)
    metrics = _metrics(render([families]))

    declared = {
        line.split()[2] for line in exposition.splitlines() if line.startswith("# TYPE ")
    }
    assert declared == set(metrics)
    assert "opencloud_security_rating_score" in metrics


def test_every_otlp_metric_is_a_gauge_carrying_its_prometheus_labels():
    """
    Gauges, because each family is a current reading rather than a counter
    that appears to reset on every run; the labels stay the exposition's so
    that one dashboard query works against either pipeline.
    """
    document = render([collect("opencloud.example.com", RESULT, duration_seconds=1.25, success=True)])
    metrics = _metrics(document)

    assert all("gauge" in metric for metric in metrics.values())
    rating = metrics["opencloud_security_rating_score"]["gauge"]["dataPoints"][0]
    assert _attributes(rating) == {
        "host": "opencloud.example.com",
        "domain": "cloud.example.com",
        "product": "OpenCloud",
        "version": "7.2.0",
    }
    assert rating["asDouble"] == 4
    duration = metrics["opencloud_security_scan_duration_seconds"]
    assert duration["unit"] == "s"
    assert duration["gauge"]["dataPoints"][0]["asDouble"] == 1.25


def test_a_failed_scan_reports_its_failure_and_no_findings():
    """
    Stale findings must never be presented as current evidence: an
    unreachable instance reports that it was unreachable, not the rating it
    had the last time it answered.
    """
    metrics = _metrics(
        render([collect("opencloud.example.com", None, duration_seconds=0.5, success=False)])
    )

    assert metrics["opencloud_security_scrape_success"]["gauge"]["dataPoints"][0]["asDouble"] == 0
    assert "opencloud_security_rating_score" not in metrics
    assert "opencloud_security_vulnerabilities_total" not in metrics


def test_int64_fields_are_strings_and_values_are_numbers():
    """
    The protobuf JSON mapping a collector validates against: 64-bit integers
    arrive as strings, asDouble as a number. Getting this wrong is rejected
    at /v1/metrics rather than showing up as a wrong number.
    """
    point = _metrics(
        render(
            [collect("opencloud.example.com", RESULT, duration_seconds=1, success=True)],
            timestamp_ns=1_700_000_000_000_000_000,
        )
    )["opencloud_security_scrape_success"]["gauge"]["dataPoints"][0]

    assert point["timeUnixNano"] == "1700000000000000000"
    assert isinstance(point["asDouble"], float)


def test_several_hosts_become_data_points_on_the_same_metrics():
    """
    One document, however many hosts: several JSON objects in a row do not
    parse as one, and a metric per host would defeat a query that groups by
    host the way the same query does against a scrape.
    """
    document = render(
        [
            collect("one.example.com", RESULT, duration_seconds=1, success=True),
            collect("two.example.com", RESULT, duration_seconds=2, success=True),
        ]
    )

    points = _metrics(document)["opencloud_security_scan_duration_seconds"]["gauge"]["dataPoints"]
    assert {_attributes(point)["host"] for point in points} == {
        "one.example.com",
        "two.example.com",
    }


def test_the_cli_prints_one_otlp_document_for_every_host():
    """
    The real code path: a metrics format reports a scan rather than judging
    it, so - like --format prometheus - it exits 0 even when the instance
    would have alerted, and the finding count travels as a sample instead.
    """
    behaviour = InstanceBehaviour(exposed_paths={"/opencloud.yaml"})
    with FakeOpenCloud(behaviour) as instance:
        result = run_plugin("-H", instance.host, "--format", "otlp")

    assert result.returncode == OK, result.stdout
    metrics = _metrics(json.loads(result.stdout))
    failed = metrics["opencloud_security_failed_extra_checks_total"]["gauge"]["dataPoints"][0]
    assert failed["asDouble"] >= 1
    assert _attributes(failed) == {"host": instance.host}
