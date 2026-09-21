"""
--policy: the organization's requirements, enforced as a deployment gate.

Driven through the real CLI against a fake OpenCloud, because the point of a
policy is the exit code a pipeline sees, and that is decided on the same path
the thresholds, waivers and baseline all use.
"""

from __future__ import annotations

import json

import pytest

from tests.fake_opencloud import FakeOpenCloud, InstanceBehaviour
from tests.test_e2e_cli import (  # noqa: F401
    CRITICAL,
    OK,
    UNKNOWN,
    healthy,
    run_plugin,
)

#: Missing on the fake instance out of the box, so a policy that requires it
#: fails. Derived from an actual scan rather than assumed - see tests/CLAUDE.md.
MISSING_MEASURE = "httpsEnforced"
#: A check the fake instance fails, so a policy that forbids it fails.
PRESENT_FINDING = "reverseProxyDetected"


def write_policy(tmp_path, body: str, name: str = "policy.yml") -> str:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return str(path)


def test_a_met_policy_leaves_the_verdict_alone(tmp_path, healthy):  # noqa: F811
    """A policy is a gate, not a grader: meeting it must not change anything."""
    policy = write_policy(tmp_path, "minimum_rating: 4\n")

    result = run_plugin("-H", healthy.host, "--policy", policy)

    assert result.returncode == OK, result.stdout
    assert "Policy: every requirement met" in result.stdout
    assert "policy violation" not in result.stdout


def test_a_rating_below_the_minimum_is_critical(tmp_path):
    """The whole point: fail a deployment on explicit policy, not on a grade."""
    behaviour = InstanceBehaviour()
    with FakeOpenCloud(behaviour) as instance:
        result = run_plugin(
            "-H", instance.host, "--policy", write_policy(tmp_path, "minimum_rating: 5\n")
        )
        assert result.returncode == OK, result.stdout  # A+ meets it

        stricter = write_policy(tmp_path, "minimum_rating: 5\n", name="strict.yml")
        behaviour.status_payload["productversion"] = "2.0.0"
        worse = run_plugin("-H", instance.host, "--policy", stricter)

    assert worse.returncode == CRITICAL, worse.stdout
    assert "is below the required" in worse.stdout


def test_a_required_hardening_that_is_missing_is_critical(tmp_path, healthy):  # noqa: F811
    policy = write_policy(tmp_path, f"required_hardenings:\n  - {MISSING_MEASURE}\n")

    result = run_plugin("-H", healthy.host, "--policy", policy)

    assert result.returncode == CRITICAL, result.stdout
    assert f"required hardening '{MISSING_MEASURE}' is not in place" in result.stdout


def test_a_required_hardening_that_is_in_place_passes(tmp_path, healthy):  # noqa: F811
    """The negative case: a requirement the instance meets must stay silent."""
    policy = write_policy(tmp_path, "required_hardenings:\n  - basicAuthDisabled\n")

    result = run_plugin("-H", healthy.host, "--policy", policy)

    assert result.returncode == OK, result.stdout
    assert "basicAuthDisabled" not in result.stdout


def test_a_forbidden_finding_that_is_present_is_critical(tmp_path, healthy):  # noqa: F811
    policy = write_policy(tmp_path, f"forbidden:\n  - {PRESENT_FINDING}\n")

    result = run_plugin("-H", healthy.host, "--policy", policy)

    assert result.returncode == CRITICAL, result.stdout
    assert f"forbidden finding '{PRESENT_FINDING}' is present" in result.stdout


def test_a_forbidden_finding_that_is_absent_passes(tmp_path, healthy):  # noqa: F811
    policy = write_policy(tmp_path, "forbidden:\n  - directoryListing\n")

    result = run_plugin("-H", healthy.host, "--policy", policy)

    assert result.returncode == OK, result.stdout


def test_a_waiver_does_not_excuse_a_policy_requirement(tmp_path, healthy):  # noqa: F811
    """
    --ignore-hardening is the local operator accepting a finding; a policy is
    the organization saying it may not be accepted. If a waiver could silence
    a requirement, a policy would describe nothing enforceable.
    """
    policy = write_policy(tmp_path, f"required_hardenings:\n  - {MISSING_MEASURE}\n")

    result = run_plugin(
        "-H",
        healthy.host,
        "--policy",
        policy,
        "--check-hardening",
        "--ignore-hardening",
        MISSING_MEASURE,
    )

    assert result.returncode == CRITICAL, result.stdout
    assert f"required hardening '{MISSING_MEASURE}' is not in place" in result.stdout


def test_every_violation_is_reported_not_only_the_first(tmp_path, healthy):  # noqa: F811
    policy = write_policy(
        tmp_path,
        "minimum_rating: 5\n"
        f"required_hardenings:\n  - {MISSING_MEASURE}\n"
        f"forbidden:\n  - {PRESENT_FINDING}\n",
    )

    result = run_plugin("-H", healthy.host, "--policy", policy)

    assert result.returncode == CRITICAL, result.stdout
    assert "Policy violations (2):" in result.stdout
    assert MISSING_MEASURE in result.stdout
    assert PRESENT_FINDING in result.stdout
    assert "more)" in result.stdout.splitlines()[0]


def test_the_payload_carries_the_policy_verdict(tmp_path, healthy):  # noqa: F811
    """A CI job reading --format json must not have to parse the alert line."""
    policy = write_policy(tmp_path, f"forbidden:\n  - {PRESENT_FINDING}\n")

    result = run_plugin("-H", healthy.host, "--policy", policy, "--format", "json")

    block = json.loads(result.stdout)[0]["policy"]
    assert block["passed"] is False
    assert block["path"] == policy
    assert block["violations"] == [f"forbidden finding '{PRESENT_FINDING}' is present"]


def test_without_a_policy_the_payload_has_no_policy_block(healthy):  # noqa: F811
    """The negative case: --policy is opt-in and adds nothing when unused."""
    result = run_plugin("-H", healthy.host, "--format", "json")

    assert "policy" not in json.loads(result.stdout)[0]


def test_a_policy_file_is_read_as_json_when_it_ends_in_json(tmp_path, healthy):  # noqa: F811
    """Format follows the suffix, the rule every other file here follows."""
    policy = write_policy(
        tmp_path, json.dumps({"forbidden": [PRESENT_FINDING]}), name="policy.json"
    )

    result = run_plugin("-H", healthy.host, "--policy", policy)

    assert result.returncode == CRITICAL, result.stdout


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("minimum_ratingg: 4\n", "unknown key(s) minimum_ratingg"),
        ("minimum_rating: 9\n", "outside 0-5"),
        ("minimum_rating: high\n", "must be a whole number"),
        ("required_hardenings: hstsLongMaxAge\n", "must be a list of names"),
        ("required_hardenings:\n  - noSuchMeasure\n", "names no such measure"),
        ("forbidden:\n  - ''\n", "has an empty entry"),
    ],
)
def test_a_broken_policy_is_unknown_never_a_silent_pass(
    tmp_path, healthy, body, expected  # noqa: F811
):
    """
    A policy exists to fail deployments, so a typo that quietly requires
    nothing is the worst outcome available - it must be a usage error.
    """
    result = run_plugin("-H", healthy.host, "--policy", write_policy(tmp_path, body))

    assert result.returncode == UNKNOWN, result.stdout
    assert expected in result.stdout


def test_a_policy_applies_to_every_host_of_a_multi_host_run(tmp_path):
    healthy_instance = InstanceBehaviour()
    broken = InstanceBehaviour()
    broken.status_payload["productversion"] = "2.0.0"
    policy = write_policy(tmp_path, "minimum_rating: 5\n")

    with FakeOpenCloud(healthy_instance) as good, FakeOpenCloud(broken) as bad:
        result = run_plugin(
            "-H", f"{good.host},{bad.host}", "--policy", policy, "--format", "json"
        )

    verdicts = {
        document["host"]: document["policy"]["passed"]
        for document in json.loads(result.stdout)
    }
    assert verdicts == {good.host: True, bad.host: False}
