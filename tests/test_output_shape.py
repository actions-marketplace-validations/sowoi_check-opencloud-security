"""
The shape of the two documents operators build on.

The scan result's keys are camelCase and the plugin's own output
(``--format json`` and the webhook payload) is snake_case. Receivers,
dashboards and jq filters key on those names, so a rename is a breaking
change even when every value stays correct. These tests pin the top-level
names and the spelling convention. A deliberate change edits the set here and
says so under ``### Changed`` in CHANGELOG.md, with what operators must update.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest

from opencloud_local_scan import scan
from opencloud_local_scan.releases import ReleaseSettings
from opencloud_local_scan.scanner import ScannerSettings
from tests.fake_opencloud import FakeOpenCloud, InstanceBehaviour
from tests.test_e2e_cli import OK, run_plugin

SETTINGS = ScannerSettings(
    scheme="http", timeout=3, check_debug_ports=False, include_bundled_db=True
)

RESULT_KEYS = frozenset({
    "EOL", "addressObservations", "addresses", "advisorySources", "alternativeServices",
    "capabilitiesAvailable", "configuration", "coverage", "domain", "edition", "extraChecks", "hardenings",
    "identityProvider", "ignored", "integrations", "ipv6Enabled", "latestVersionInBranch",
    "legacyVersion", "lifecycle", "loginThrottling", "product", "provenance", "rating",
    "ratingExplanation", "releaseType", "remediationPlan", "reverseProxy", "scannedAt",
    "scanner", "setup", "tls", "tlsByAddress", "updates", "upgradePath", "upgradeRehearsal", "url", "version",
    "vulnerabilities", "waivers",
})

PAYLOAD_KEYS = frozenset({
    "configuration", "coverage", "domain", "duration_seconds", "eol", "eol_warning", "eol_warning_days", "exit_code",
    "failed_extra_checks", "host", "lifecycle", "message", "missing_hardenings", "plugin",
    "plugin_version", "product", "product_version", "rating", "rating_label",
    "release_type", "scan_backend", "scan_uuid", "scanned_at", "status", "timestamp",
    "update", "upgrade_path", "upgrade_rehearsal", "vulnerabilities", "vulnerability_count",
})

# Sections of the payload that are the scanner's own documents, copied as-is.
PASSED_THROUGH = {"lifecycle", "update"}

CAMEL = re.compile(r"[a-z][a-zA-Z0-9]*")
SNAKE = re.compile(r"[a-z][a-z0-9]*(_[a-z0-9]+)*")

# Keys that are data rather than names we chose: HTTP header names as the
# server spells them.
DATA_KEYED = {"setup.headers", "setup.advisoryHeaders"}
# Established exceptions, each already part of the published document: the
# shouted EOL flag, the PHP DateTime shape of scannedAt, and one coverage count.
LEGACY_KEYS = {("", "EOL"), ("scannedAt", "timezone_type"), ("coverage.counts", "not_checked")}


def _keys(document: Any, path: str = "") -> list[tuple[str, str]]:
    """Every (parent path, key) pair in a nested document, list items included."""
    found: list[tuple[str, str]] = []
    if isinstance(document, dict):
        for key, value in document.items():
            found.append((path, str(key)))
            if path.lstrip(".") in DATA_KEYED:
                continue
            found.extend(_keys(value, f"{path}.{key}".lstrip(".")))
    elif isinstance(document, list):
        for item in document:
            found.extend(_keys(item, path))
    return found


@pytest.fixture(scope="module")
def result() -> dict:
    """A real scan of the fake instance with findings, so optional sections are filled."""
    behaviour = InstanceBehaviour(basic_auth=True, exposed_paths={"/opencloud.yaml"})
    behaviour.headers.pop("X-Content-Type-Options")
    with FakeOpenCloud(behaviour) as instance:
        return scan(
            instance.host, settings=SETTINGS, release_settings=ReleaseSettings(mode="off")
        )


@pytest.fixture(scope="module")
def payload() -> dict:
    """The plugin's --format json document for one healthy host."""
    with FakeOpenCloud() as instance:
        completed = run_plugin("-H", instance.host, "--format", "json")
    assert completed.returncode == OK, completed.stdout
    documents = json.loads(completed.stdout)
    assert len(documents) == 1
    return documents[0]


def test_the_result_document_keeps_its_top_level_keys(result):
    """Renaming or dropping a result key breaks every consumer of the scan subcommand."""
    assert set(result) == RESULT_KEYS


def test_every_result_key_we_chose_is_camel_case(result):
    """A snake_case key in the result is a key a camelCase consumer will never find."""
    offenders = [
        (parent, key) for parent, key in _keys(result)
        if parent not in DATA_KEYED and (parent, key) not in LEGACY_KEYS
        and not CAMEL.fullmatch(key)
    ]

    assert offenders == []


def test_the_plugin_output_keeps_its_top_level_keys(payload):
    """The webhook payload and --format json are one contract for receivers."""
    assert set(payload) == PAYLOAD_KEYS


def test_every_plugin_output_key_is_snake_case(payload):
    """The plugin's own names are snake_case; a camelCase key there is a leak from the scanner."""
    offenders = [
        (parent, key) for parent, key in _keys(payload)
        if parent.split(".")[0] not in PASSED_THROUGH and not SNAKE.fullmatch(key)
    ]

    assert offenders == []


def test_sections_passed_through_from_the_scanner_keep_its_spelling(payload):
    """lifecycle and update are the scanner's documents; re-spelling them would break both sides."""
    passed = [(parent, key) for parent, key in _keys(payload) if parent.split(".")[0] in PASSED_THROUGH]

    assert passed, "the fake instance fills lifecycle and update"
    assert [(parent, key) for parent, key in passed if not CAMEL.fullmatch(key)] == []


def test_the_key_checks_would_notice_a_wrongly_spelled_key():
    """The spelling checks must fail on the mistake they exist to catch."""
    assert not CAMEL.fullmatch("rating_explanation")
    assert not SNAKE.fullmatch("ratingLabel")
    assert ("setup", "tls_by_address") in _keys({"setup": {"tls_by_address": 1}})
