"""
The policy gate, in process: the exit code a violation forces and the policy
block the webhook carries.

tests/test_policy.py already drives --policy through the real CLI, which is
where the operator-facing behaviour belongs. That path runs the plugin as a
subprocess, so it can never see a mutated plugin. These tests call
check_vulnerabilities() directly with a Policy built in memory, so that the
wiring between the scan document and the gate - which result is judged,
against which rating and which vulnerabilities, and whether the verdict is
recorded - is covered by a test mutation testing can actually run.
"""

from __future__ import annotations

import json

import pytest

import check_opencloud_security as plugin
from check_opencloud_security import NagiosExitCode, Policy, ScanContext, ScanResult

#: A stock-looking result: one missing measure, one failed extra check, one
#: known vulnerability, so every kind of 'forbidden' entry has something real
#: to match against.
RESULT = {
    "domain": "opencloud.example.com",
    "product": "OpenCloud",
    "version": "5.0.0",
    "scannedAt": {"date": "2026-05-01 10:00:00.000000"},
    "rating": 3,
    "EOL": False,
    "vulnerabilities": [{"id": "CVE-2026-0001"}],
    "hardenings": {"basicAuthDisabled": False, "cspWithoutUnsafeInline": True},
    "setup": {"https": {"used": True, "enforced": True}, "headers": {}},
    "extraChecks": [
        {"id": "exposed:/opencloud.yaml", "severity": "critical", "passed": False}
    ],
}


@pytest.fixture
def posts(monkeypatch):
    """Record every webhook POST instead of sending it."""
    recorded = []

    class _Response:
        status_code = 200

        def close(self):
            pass

        def raise_for_status(self):
            pass

    def _post(self, url, **kwargs):
        # The plugin posts the bytes it signed, so read the document back out
        # of `data=` - that is what a receiver would see.
        recorded.append(json.loads(kwargs["data"]))
        return _Response()

    monkeypatch.setattr(plugin.requests.Session, "post", _post)
    return recorded


def run(policy, result=None, **kwargs):
    """Run the check against RESULT under `policy` and return its exit code."""
    context = ScanContext(
        host="opencloud.example.com",
        policy=policy,
        allow_private_webhooks=True,
        **kwargs,
    )
    with pytest.raises(SystemExit) as excinfo:
        plugin.check_vulnerabilities(
            context,
            ScanResult(response=result if result is not None else RESULT, uuid="local-x"),
            duration_seconds=1.0,
        )
    return excinfo.value.code


#: What the fixture rates without any policy: a policy never improves a
#: verdict, so every "no violation" case below has to land back here.
UNGATED = NagiosExitCode.WARNING


def test_no_policy_leaves_the_verdict_alone():
    """Without --policy nothing in this path may run at all."""
    assert run(None) == UNGATED


def test_a_rating_below_the_minimum_is_critical():
    """The gate is judged against the rating this scan produced, not a default."""
    assert run(Policy(minimum_rating=5, path="p.yml")) == NagiosExitCode.CRITICAL
    assert run(Policy(minimum_rating=3, path="p.yml")) == UNGATED


def test_a_required_hardening_that_is_missing_is_critical():
    """The measures come from the result document that was handed in."""
    missing = Policy(required_hardenings=("basicAuthDisabled",), path="p.yml")
    in_place = Policy(required_hardenings=("cspWithoutUnsafeInline",), path="p.yml")

    assert run(missing) == NagiosExitCode.CRITICAL
    assert run(in_place) == UNGATED


def test_a_forbidden_vulnerability_is_critical():
    """
    The vulnerabilities the gate sees are the ones read off this scan: a
    policy forbidding a CVE the instance has must fail, and one naming a CVE
    it does not have must not.
    """
    assert run(Policy(forbidden=("CVE-2026-0001",), path="p.yml")) == NagiosExitCode.CRITICAL
    assert run(Policy(forbidden=("CVE-2026-9999",), path="p.yml")) == UNGATED


def test_a_forbidden_extra_check_is_critical():
    """A failed extra check is a finding a policy can name, like any other."""
    policy = Policy(forbidden=("exposed:/opencloud.yaml",), path="p.yml")

    assert run(policy) == NagiosExitCode.CRITICAL


def test_the_payload_carries_the_policy_verdict(posts):
    """
    A pipeline that only reads the webhook has to learn the same thing the
    exit code says - which policy ran, whether it passed, and why not.
    """
    policy = Policy(minimum_rating=5, path="/etc/policy.yml")

    assert run(policy, webhook_url="http://127.0.0.1:9/hook") == NagiosExitCode.CRITICAL

    assert len(posts) == 1
    block = posts[0]["policy"]
    assert block["path"] == "/etc/policy.yml"
    assert block["passed"] is False
    assert block["violations"] == ["rating C is below the required A+"]


def test_a_met_policy_is_recorded_as_met(posts):
    """Passing is a verdict too: silence would be indistinguishable from no policy."""
    run(
        Policy(minimum_rating=3, path="/etc/policy.yml"),
        webhook_url="http://127.0.0.1:9/hook",
        webhook_on="always",
    )

    assert posts[0]["policy"] == {
        "path": "/etc/policy.yml",
        "passed": True,
        "violations": [],
    }


def test_without_a_policy_the_payload_has_no_policy_block(posts):
    """An absent policy must leave no trace, not an empty one."""
    run(None, webhook_url="http://127.0.0.1:9/hook", webhook_on="always")

    assert "policy" not in posts[0]
