"""
The monitoring tools must learn the same things about the same instance.

One scan result goes through the Nagios/Icinga perfdata, the Checkmk local
check and the Prometheus exposition (OTLP renders the same metric families as
Prometheus, see opencloud_local_scan/metrics.py). Every metric one of them
carries has to reach the others under the name listed in METRICS, with the
same value - so a measurement added to one output and forgotten in another
fails here rather than in somebody's dashboard.

Adding a metric: add a row to METRICS, emit it from all three outputs and
document it in docs/checkmk.md and docs/prometheus.md. A metric that must
exist in only one tool goes into PROMETHEUS_ONLY with the reason.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

import check_opencloud_security as plugin

HOST = "opencloud.example.com"

# perfdata label -> (Checkmk metric, Prometheus family)
METRICS = {
    "rating": ("rating", "opencloud_security_rating_score"),
    "vulnerabilities": ("vulnerabilities", "opencloud_security_vulnerabilities_total"),
    "hardenings_missing": ("hardenings_missing", "opencloud_security_hardenings_missing_total"),
    "extra_checks_failed": ("extra_checks_failed", "opencloud_security_failed_extra_checks_total"),
    "update_available": ("update_available", "opencloud_security_update_available"),
    "support_days_left": ("support_days_left", "opencloud_security_support_days_remaining"),
    "cert_days_left": ("cert_days_left", "opencloud_security_certificate_days_remaining"),
    "upgrade_path_complete": ("upgrade_path_complete", "opencloud_security_upgrade_path_complete"),
    "waiver_days_left": ("waiver_days_left", "opencloud_security_waiver_days_remaining"),
    "coverage_inconclusive": ("coverage_inconclusive", "opencloud_security_coverage_inconclusive_total"),
    "coverage_not_checked": ("coverage_not_checked", "opencloud_security_coverage_not_checked_total"),
    "time": ("execution_time", "opencloud_security_scan_duration_seconds"),
}

# Timing is measured per run, so only its presence is compared.
UNCOMPARABLE = {"time"}

PROMETHEUS_ONLY = {
    # Nagios and Checkmk carry the verdict in the service state itself; a
    # Prometheus alert has only the series, so it needs these as numbers.
    "opencloud_security_end_of_life": "the state is CRITICAL at end of life",
    "opencloud_security_scrape_success": "a failed scan is the UNKNOWN state",
}

RESULT = {
    "domain": "cloud.example.com",
    "product": "OpenCloud",
    "version": "7.2.0",
    "rating": 3,
    "EOL": False,
    "vulnerabilities": [
        {"id": "CVE-2026-0001", "severity": "high"},
        {"id": "CVE-2026-0002", "severity": "medium"},
    ],
    "hardenings": {"hstsLongMaxAge": False, "basicAuthDisabled": True},
    "setup": {
        "https": {"used": True, "enforced": True},
        "headers": {"X-Frame-Options": False},
    },
    "extraChecks": [{"id": "tlsTrusted", "passed": False}],
    "lifecycle": {"daysRemaining": 42, "releaseType": "production"},
    "updates": {"available": True, "availableVersion": "7.4.0"},
    "tls": {"host": HOST, "certificate": {"daysRemaining": 67}},
    "upgradePath": {
        "target": "7.4.0",
        "fixes": ["CVE-2026-0001"],
        "stillAffected": ["CVE-2026-0002"],
    },
    "scannedAt": {"date": "2026-05-01 10:00:00.000000"},
    "ignored": ["debugPort:9205"],
    "waivers": [
        {
            "pattern": "debugPort:9205",
            "reason": "Firewall change scheduled",
            "expiresAt": "2026-05-09T10:00:00+00:00",
            "state": "active",
            "matched": ["debugPort:9205"],
        }
    ],
    "coverage": {
        "schema": 1,
        "checks": [
            {"id": "tlsTrusted", "group": "extraCheck", "state": "failed"},
            {"id": "dnsCaa", "group": "dns", "state": "inconclusive", "reason": "timeout"},
            {"id": "debugPort:9205", "group": "extraCheck", "state": "not_checked",
             "reason": "probe_disabled"},
        ],
    },
}


def _run(monkeypatch, capsys, *arguments: str) -> str:
    monkeypatch.setattr(plugin, "local_scan", lambda *args, **kwargs: RESULT)
    monkeypatch.setattr(
        sys, "argv", ["check-opencloud-security", "-H", HOST, "--check-hardening", *arguments]
    )
    # The Nagios and Checkmk paths exit with the state; Prometheus returns.
    try:
        plugin.main()
    except SystemExit:
        pass
    return capsys.readouterr().out


def _perfdata(output: str) -> dict[str, float]:
    perfdata = output.split("|", 1)[1]
    values = {}
    for item in perfdata.split():
        name, rest = item.split("=", 1)
        number = re.match(r"-?[\d.]+", rest)
        assert number, item
        values[name.strip("'")] = float(number.group())
    return values


def _checkmk(output: str) -> dict[str, float]:
    metrics = output.strip().split(" ", 3)[2]
    return {name: float(value) for name, value in (m.split("=", 1) for m in metrics.split("|"))}


def _prometheus(output: str) -> dict[str, float]:
    # Families with several samples (vulnerabilities by severity) are summed:
    # the other tools carry the total.
    values: dict[str, float] = {}
    for line in output.splitlines():
        if line and not line.startswith("#"):
            series, value = line.rsplit(" ", 1)
            name = series.split("{", 1)[0]
            values[name] = values.get(name, 0.0) + float(value)
    return values


@pytest.fixture
def outputs(monkeypatch, capsys):
    return {
        "nagios": _perfdata(_run(monkeypatch, capsys)),
        "checkmk": _checkmk(_run(monkeypatch, capsys, "--format", "checkmk")),
        "prometheus": _prometheus(_run(monkeypatch, capsys, "--format", "prometheus")),
    }


def test_every_tool_carries_every_metric(outputs):
    """A measurement graphed in one tool and forgotten in another is invisible there."""
    assert set(outputs["nagios"]) == set(METRICS), (
        "A perfdata metric is missing from METRICS - add it to Checkmk and "
        "Prometheus as well, then list it here."
    )
    assert set(outputs["checkmk"]) == {checkmk for checkmk, _ in METRICS.values()}
    assert set(outputs["prometheus"]) == {
        prometheus for _, prometheus in METRICS.values()
    } | set(PROMETHEUS_ONLY)


@pytest.mark.parametrize("perfdata", sorted(set(METRICS) - UNCOMPARABLE))
def test_every_tool_reports_the_same_value(outputs, perfdata):
    """Two tools disagreeing about one instance leaves nobody knowing which is right."""
    checkmk, prometheus = METRICS[perfdata]
    value = outputs["nagios"][perfdata]

    assert outputs["checkmk"][checkmk] == value
    assert outputs["prometheus"][prometheus] == value


# --- Icinga 2 / Nagios: the CheckCommand definitions ------------------------

ROOT = Path(__file__).resolve().parent.parent

# Complete definitions: every plugin option not in ICINGA_EXCLUDED is an argument.
CHECKCOMMANDS = [
    ROOT / "contrib" / "icinga2" / "check_opencloud_security.conf",
    ROOT / "ansible" / "roles" / "opencloud_check_native" / "templates" / "checkcommand.conf.j2",
    ROOT / "ansible" / "roles" / "opencloud_check_docker" / "templates" / "checkcommand.conf.j2",
]

# Options that have no place on an Icinga service, and why.
ICINGA_EXCLUDED = {
    "--help": "interactive",
    "--version": "interactive",
    "--configure": "interactive setup wizard",
    "--upgrade-self": "maintenance of the plugin, not a check",
    "--self-update-check": "maintenance of the plugin, not a check",
    "--check-only": "only modifies --upgrade-self",
    "--format": "Icinga reads the default Nagios output",
    "--prometheus-listen-port": "Prometheus exporter",
    "--prometheus-listen-addr": "Prometheus exporter",
    "--scrape-interval": "Prometheus exporter",
    "--verify-remediation": "a one-off check after a fix, not a recurring service",
}

_ARGUMENT = re.compile(r'^\s*"(--[a-z-]+)"\s*=\s*\{', re.MULTILINE)


def _plugin_options() -> set[str]:
    parser = plugin.build_arg_parser()
    return {
        option
        for action in parser._actions
        for option in action.option_strings
        if option.startswith("--")
    }


@pytest.mark.parametrize("path", CHECKCOMMANDS, ids=lambda path: path.parent.parent.name)
def test_every_checkcommand_offers_every_plugin_option(path):
    """A new option must reach Icinga users, or say here why it cannot."""
    arguments = set(_ARGUMENT.findall(path.read_text(encoding="utf-8"))) - {"--rm"}

    missing = _plugin_options() - set(ICINGA_EXCLUDED) - arguments
    assert not missing, f"{path.name} lacks {sorted(missing)}; add them or exclude them here"
    excluded = arguments & set(ICINGA_EXCLUDED)
    assert not excluded, f"{path.name} offers excluded options {sorted(excluded)}"


def test_every_excluded_option_still_exists():
    """An exclusion for a removed option would hide the next one of that name."""
    assert set(ICINGA_EXCLUDED) <= _plugin_options()


def _documented_checkcommand_options() -> list[tuple[Path, str]]:
    found = []
    for document in sorted((ROOT / "docs").rglob("*.md")):
        text = document.read_text(encoding="utf-8")
        for block in re.findall(r"object CheckCommand.*?\n}", text, re.DOTALL):
            found += [(document, option) for option in _ARGUMENT.findall(block)]
        # Icinga Director's argument table: | `--flag` | ...
        if "icinga-director" in document.name:
            found += [(document, option) for option in re.findall(r"^\| `(--[a-z-]+)`", text, re.MULTILINE)]
    return found


def test_documented_checkcommands_only_use_options_that_exist():
    """A renamed flag in a copied example makes every check UNKNOWN."""
    documented = _documented_checkcommand_options()
    known = _plugin_options() | {"--rm"}

    assert documented, "no CheckCommand examples found in docs/"
    stale = sorted({f"{path.relative_to(ROOT)}: {option}" for path, option in documented if option not in known})
    assert not stale
