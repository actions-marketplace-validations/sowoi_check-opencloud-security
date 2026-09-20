"""
Remediation verification: re-measure a few findings without a full scan.

The library half (opencloud_local_scan.verification) is checked against a
fake OpenCloud directly; the plugin half (--verify-remediation) is run the
way a monitoring daemon or an operator would, as a subprocess.
"""

from __future__ import annotations

import json

import pytest

from opencloud_local_scan.releases import ReleaseSettings
from opencloud_local_scan.scanner import ScannerSettings, scan
from opencloud_local_scan.verification import probe_group, verify
from tests.fake_opencloud import FakeOpenCloud, InstanceBehaviour
from tests.test_e2e_cli import CRITICAL, OK, UNKNOWN, WARNING, run_plugin

SETTINGS = ScannerSettings(
    scheme="http", timeout=3, check_debug_ports=False, include_bundled_db=True
)


def _result(document: dict, finding_id: str) -> dict:
    return next(entry for entry in document["results"] if entry["id"] == finding_id)


@pytest.mark.parametrize(
    ("finding_id", "group"),
    [
        ("Strict-Transport-Security", "root"),
        ("cookieSecure", "root"),
        ("versionDisclosure:Server", "root"),
        ("corsOriginRestricted", "cors"),
        ("exposed", "exposedPaths"),
        ("exposed:/.env", "exposedPaths"),
        ("httpsEnforced", "https"),
        ("tlsProtocol", "tls"),
        ("tlsCaaRecord", "caa"),
        ("securityTxtPublished", "advisoryChecks"),
        ("basicAuthDisabled", "identity"),
        ("eol", None),
        ("vulnerability:CVE-2025-0001", None),
        ("addressParity", None),
        ("noSuchCheck", None),
    ],
)
def test_every_finding_id_maps_to_the_probe_that_measures_it(finding_id, group):
    assert probe_group(finding_id) == group


def test_only_the_requested_probe_groups_run():
    """Asking about one header must not walk the whole instance."""
    with FakeOpenCloud(InstanceBehaviour()) as instance:
        document = verify(instance.host, ["X-Content-Type-Options"], settings=SETTINGS)

    assert document["probeGroups"] == ["root"]
    entry = _result(document, "X-Content-Type-Options")
    assert entry["verifiable"] is True
    assert entry["passed"] is True


def test_a_header_still_missing_is_reported_as_failing():
    behaviour = InstanceBehaviour()
    behaviour.headers.pop("Referrer-Policy")
    with FakeOpenCloud(behaviour) as instance:
        document = verify(instance.host, ["Referrer-Policy"], settings=SETTINGS)

    assert _result(document, "Referrer-Policy")["passed"] is False


def test_a_family_root_verifies_every_member():
    behaviour = InstanceBehaviour(exposed_paths={"/.env"})
    with FakeOpenCloud(behaviour) as instance:
        document = verify(instance.host, ["exposed"], settings=SETTINGS)

    entry = _result(document, "exposed")
    assert entry["passed"] is False
    assert any(check["id"] == "exposed:/.env" for check in entry["checks"])


def test_verification_agrees_with_a_full_scan():
    """The same probes, so the same answer the next full scan would give."""
    behaviour = InstanceBehaviour(webfinger_version=True, debug_endpoints=True)
    with FakeOpenCloud(behaviour) as instance:
        full = scan(
            instance.host, settings=SETTINGS, release_settings=ReleaseSettings(mode="off")
        )
        document = verify(
            instance.host,
            ["webfingerVersionDisclosure", "debugEndpoint", "traceMethodDisabled"],
            settings=SETTINGS,
        )

    for entry in document["results"]:
        expected = {
            check["id"]: check["passed"]
            for check in full["extraChecks"]
            if check["id"] == entry["id"] or check["id"].startswith(entry["id"] + ":")
        }
        assert {check["id"]: check["passed"] for check in entry["checks"]} == expected


def test_an_id_needing_a_full_scan_is_unverifiable_and_probes_nothing():
    with FakeOpenCloud(InstanceBehaviour()) as instance:
        document = verify(instance.host, ["eol", "eol", " "], settings=SETTINGS)

    assert document["probeGroups"] == []
    assert len(document["results"]) == 1
    entry = document["results"][0]
    assert entry["verifiable"] is False
    assert entry["passed"] is None
    assert "full scan" in entry["reason"]


def test_the_plugin_is_ok_once_the_fix_has_landed():
    with FakeOpenCloud(InstanceBehaviour()) as instance:
        result = run_plugin(
            "-H", instance.host, "--verify-remediation", "X-Frame-Options,corsOriginRestricted"
        )

    assert result.returncode == OK, result.stdout + result.stderr
    assert result.stdout.startswith("OK: ")
    assert "verified: X-Frame-Options, corsOriginRestricted" in result.stdout


def test_the_plugin_warns_while_a_header_is_still_missing():
    behaviour = InstanceBehaviour()
    behaviour.headers.pop("Referrer-Policy")
    with FakeOpenCloud(behaviour) as instance:
        result = run_plugin("-H", instance.host, "--verify-remediation", "Referrer-Policy")

    assert result.returncode == WARNING, result.stdout + result.stderr
    assert "still failing: Referrer-Policy" in result.stdout


def test_the_plugin_is_critical_while_a_severe_check_still_fails():
    behaviour = InstanceBehaviour(exposed_paths={"/.env"})
    with FakeOpenCloud(behaviour) as instance:
        result = run_plugin("-H", instance.host, "--verify-remediation", "exposed")

    assert result.returncode == CRITICAL, result.stdout + result.stderr
    assert "exposed:/.env: fails" in result.stdout


def test_the_plugin_is_unknown_for_an_id_it_cannot_verify_alone():
    with FakeOpenCloud(InstanceBehaviour()) as instance:
        result = run_plugin("-H", instance.host, "--verify-remediation", "eol")

    assert result.returncode == UNKNOWN, result.stdout + result.stderr
    assert "not verified: eol" in result.stdout


def test_the_plugin_prints_the_document_as_json():
    with FakeOpenCloud(InstanceBehaviour()) as instance:
        result = run_plugin(
            "-H", instance.host, "--verify-remediation", "Referrer-Policy", "--format", "json"
        )

    assert result.returncode == OK, result.stdout + result.stderr
    documents = json.loads(result.stdout)
    assert documents[0]["results"][0]["id"] == "Referrer-Policy"
    assert documents[0]["exit_code"] == OK
