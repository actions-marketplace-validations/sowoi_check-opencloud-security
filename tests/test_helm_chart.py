"""
The shipped Helm chart, held against the plugin it installs.

A chart is not documentation either: it is applied, and a flag renamed two
releases ago becomes a CrashLoopBackOff on somebody's cluster rather than a
review comment. Every flag the templates can produce is checked against the
plugin's own argument parser, and the four values an install must not be
allowed to default are checked to be refused. The `helm` binary is used where
it exists and skipped where it does not, so the checks that matter do not
depend on it.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

import check_opencloud_security as plugin

ROOT = Path(__file__).resolve().parent.parent
CHART = ROOT / "contrib" / "helm" / "check-opencloud-security"
TEMPLATES = CHART / "templates"

HELM = shutil.which("helm")
needs_helm = pytest.mark.skipif(HELM is None, reason="helm is not installed")

# `--host=…`, `--check-hardening`, `--port={{ … }}`: the flag is what matters.
_FLAG = re.compile(r"(?<![\w-])--[a-z][a-z-]+")

MINIMAL = [
    "--set", "image.tag=1.0.0",
    "--set", "cronJob.hosts={opencloud.example.com}",
]


def _template_text() -> str:
    """
    Every template that renders a manifest.

    NOTES.txt is left out: it is prose printed after an install, and the
    `kubectl` flags in it are not the plugin's.
    """
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(TEMPLATES.iterdir())
        if path.is_file() and path.name != "NOTES.txt"
    )


def _render(*overrides: str) -> subprocess.CompletedProcess:
    assert HELM is not None
    return subprocess.run(
        [HELM, "template", "release", str(CHART), *overrides],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def _documents(rendered: str) -> list[dict]:
    return [document for document in yaml.safe_load_all(rendered) if document]


def test_every_flag_the_chart_can_emit_is_a_flag_the_plugin_accepts():
    """
    A renamed flag would surface as a container that exits 2 on a cluster.

    The expectation comes from the parser itself rather than a list here,
    which is the only version of this test that cannot go stale.
    """
    accepted = {
        option
        for action in plugin.build_arg_parser()._actions
        for option in action.option_strings
    }
    # The scan service is a different entry point with its own parser; its two
    # flags are asserted by the rendering tests below instead.
    scanner_flags = {"--cache-ttl"}

    emitted = set(_FLAG.findall(_template_text())) - scanner_flags

    assert emitted, "the chart passes no flags at all"
    assert emitted <= accepted, sorted(emitted - accepted)


def test_the_chart_names_no_release_of_its_own():
    """
    The version has one source, pyproject.toml.

    An `appVersion` here would be a second one, and a chart whose appVersion
    silently became the default tag would choose which release schedule an
    operator scans against - see the note in Chart.yaml.
    """
    chart = yaml.safe_load((CHART / "Chart.yaml").read_text(encoding="utf-8"))
    values = yaml.safe_load((CHART / "values.yaml").read_text(encoding="utf-8"))

    assert chart["name"] == CHART.name
    assert "appVersion" not in chart
    assert values["image"]["tag"] == ""


def test_an_install_must_name_its_image_and_its_service_token():
    """
    Two values a default would answer wrongly, so the templates refuse them.

    A tag that defaults to `latest` changes the verdict under a running alert,
    and a scan service without a token will scan any host its callers name.
    """
    text = _template_text()

    for value in (".Values.image.tag", ".Values.scanService.existingSecret"):
        assert re.search(rf'required "[^"]+" {re.escape(value)}', text), value


def test_the_two_list_values_are_guarded_by_fail_rather_than_required():
    """
    `required` lets an empty list through - it only rejects nil and "".

    Guarding `cronJob.hosts` with it rendered `--host=` and installed a Job
    that scanned nothing, which is why these two are checked for emptiness
    explicitly. The test names the mechanism because the mechanism is the bug.
    """
    text = _template_text()

    assert "if not $cron.hosts }}{{ fail" in text
    assert "if not $targets }}{{ fail" in text
    # The negative half: neither list may go back to `required`, which is
    # what silently rendered an empty one.
    assert 'required "cronJob.hosts' not in text
    assert "required \"scanService.networkPolicy" not in text


def test_neither_workload_mounts_a_kubernetes_token():
    """A scanner reads no Kubernetes API, so a mounted token is only a credential to steal."""
    text = _template_text()

    assert text.count("automountServiceAccountToken: false") == 3
    assert "automountServiceAccountToken: true" not in text


@needs_helm
def test_the_chart_lints_clean():
    """`helm lint` is what a reviewer runs first; a chart that fails it never gets installed."""
    assert HELM is not None
    result = subprocess.run(
        [HELM, "lint", str(CHART), *MINIMAL],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


@needs_helm
def test_a_minimal_install_renders_one_cronjob_and_nothing_else():
    """
    The default is the thing most people want: a scheduled scan, no service.

    The scan service is a listening HTTP endpoint that scans what it is told
    to; it must never arrive because somebody installed the chart.
    """
    result = _render(*MINIMAL)

    assert result.returncode == 0, result.stderr
    documents = _documents(result.stdout)
    assert [document["kind"] for document in documents] == ["CronJob"]

    spec = documents[0]["spec"]["jobTemplate"]["spec"]["template"]["spec"]
    container = spec["containers"][0]
    assert container["image"] == "registry.example.com/check-opencloud-security:1.0.0"
    assert "--host=opencloud.example.com" in container["args"]
    assert "--check-hardening" in container["args"]
    assert spec["restartPolicy"] == "Never"
    assert container["securityContext"]["readOnlyRootFilesystem"] is True


@needs_helm
def test_several_hosts_become_one_scan():
    """
    The plugin takes a comma-separated list and returns the worst result, so
    one Job covers an estate - not one Job per instance competing for the
    schedule.
    """
    result = _render(
        "--set", "image.tag=1.0.0",
        "--set", "cronJob.hosts={one.example.com,two.example.com}",
    )

    container = _documents(result.stdout)[0]["spec"]["jobTemplate"]["spec"]["template"]["spec"]["containers"][0]
    assert "--host=one.example.com,two.example.com" in container["args"]


@needs_helm
def test_an_install_without_a_tag_is_refused_rather_than_following_latest():
    """The negative case: the verdict must not change because a mutable tag moved."""
    result = _render("--set", "cronJob.hosts={opencloud.example.com}")

    assert result.returncode != 0
    assert "image.tag is required" in result.stderr


@needs_helm
def test_an_install_naming_no_host_is_refused_rather_than_scanning_nothing():
    """
    A Job with `--host=` runs daily, fails in a way nobody reads, and looks
    like monitoring. This is the case `required` let through.
    """
    result = _render("--set", "image.tag=1.0.0")

    assert result.returncode != 0
    assert "cronJob.hosts" in result.stderr


@needs_helm
def test_the_scan_service_is_refused_without_a_token():
    """An untokened scan service scans any host anybody who can reach the pod names."""
    result = _render(*MINIMAL, "--set", "scanService.enabled=true")

    assert result.returncode != 0
    assert "scanService.existingSecret" in result.stderr


@needs_helm
def test_the_scan_service_renders_with_a_policy_naming_what_it_may_reach():
    """
    The positive half: asked for, the service arrives with its egress bounded
    and its token mounted from a Secret the chart did not write.
    """
    result = _render(
        *MINIMAL,
        "--set", "scanService.enabled=true",
        "--set", "scanService.existingSecret=opencloud-security",
        "--set", "scanService.networkPolicy.enabled=true",
        "--set", "scanService.networkPolicy.allowedTargets[0].cidr=192.0.2.10/32",
        "--set", "scanService.networkPolicy.allowedTargets[0].ports[0]=9200",
    )

    assert result.returncode == 0, result.stderr
    documents = {document["kind"]: document for document in _documents(result.stdout)}
    assert {"CronJob", "Deployment", "Service", "NetworkPolicy"} <= set(documents)

    policy = documents["NetworkPolicy"]["spec"]
    assert policy["policyTypes"] == ["Egress"]
    assert any(
        rule.get("to", [{}])[0].get("ipBlock", {}).get("cidr") == "192.0.2.10/32"
        for rule in policy["egress"]
    )

    container = documents["Deployment"]["spec"]["template"]["spec"]["containers"][0]
    token = next(item for item in container["env"] if item["name"] == "COS_SERVICE_TOKEN")
    assert token["valueFrom"]["secretKeyRef"]["name"] == "opencloud-security"
    assert container["livenessProbe"]["httpGet"]["path"] == "/healthz"


@needs_helm
def test_an_empty_allowlist_is_refused_rather_than_rendered_as_a_policy():
    """A NetworkPolicy with no egress rule is a different policy, not an unfinished one."""
    result = _render(
        *MINIMAL,
        "--set", "scanService.enabled=true",
        "--set", "scanService.existingSecret=opencloud-security",
        "--set", "scanService.networkPolicy.enabled=true",
    )

    assert result.returncode != 0
    assert "allowedTargets" in result.stderr


@needs_helm
def test_a_secret_is_referenced_and_never_written_by_the_chart():
    """
    A values file is committed and copied; a token in one outlives every place
    the operator remembers putting it. The chart creates no Secret at all.
    """
    result = _render(
        *MINIMAL,
        "--set", "cronJob.existingSecret=opencloud-security",
        "--set", "cronJob.webhook.enabled=true",
        "--set", "scanService.enabled=true",
        "--set", "scanService.existingSecret=opencloud-security",
    )

    assert result.returncode == 0, result.stderr
    assert "Secret" not in {document["kind"] for document in _documents(result.stdout)}
    assert "webhook-url" in result.stdout
    # The URL itself reaches the plugin through the environment, never as an
    # argument, where it would be readable in `kubectl describe` and in `ps`.
    assert "--webhook-url=$(COS_WEBHOOK_URL)" in result.stdout
    assert "https://" not in result.stdout
