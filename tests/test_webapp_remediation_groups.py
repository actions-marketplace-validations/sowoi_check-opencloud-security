"""The grouped remediation plan on the result page, in the bundle and in the contract."""

from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("fastapi", reason="the web extra is not installed")

from fastapi.testclient import TestClient

from tests.fake_opencloud import FakeOpenCloud, InstanceBehaviour
from tests.webapp_support import (  # noqa: F401 - the fixtures are autouse
    _isolated_backend,
    _offline_resolver,
    settings,
)
from webapp.app import create_app
from webapp.catalog import summarise
from webapp.openapi import openapi_document
from webapp.remediation_bundle import remediation_html, remediation_markdown
from webapp.tasks import run_scan

IDENTIFIER = "0b5d7c2e-8f3a-4e61-9c2d-5a4b3c2d1e0f"


@pytest.fixture
def scanned() -> tuple[dict, str]:
    """A real scan with two exposed paths, and the page that renders it."""
    configured = settings(allow_private_targets=True, verify_tls=False, scan_timeout=5)
    app = create_app(configured)
    with TestClient(app) as test_client:
        store = app.state.store
        behaviour = InstanceBehaviour(
            basic_auth=True, exposed_paths={"/config/opencloud.yaml", "/.env"}
        )
        with FakeOpenCloud(behaviour) as instance:
            asyncio.run(
                store.create(
                    IDENTIFIER,
                    target=f"http://{instance.host}",
                    ignore_hardenings=(),
                    output_format="dashboard",
                )
            )
            asyncio.run(run_scan({"web_settings": configured, "store": store}, IDENTIFIER))
        record = asyncio.run(store.get(IDENTIFIER))
        assert record is not None and record.result is not None
        return record.result, test_client.get(f"/scan/{IDENTIFIER}").text


def test_the_page_shows_each_group_and_a_change_that_resolves_several(scanned):
    """The operator with the proxy config open must see every proxy change in one place."""
    result, page = scanned
    groups = summarise(result)["remediation"]["groups"]

    assert 'id="remediation-groups"' in page
    assert 'href="#remediation-groups"' in page
    targets = {group["target"] for group in groups}
    assert {"reverseProxy", "opencloud"} <= targets
    for target in targets:
        assert f'data-target="{target}"' in page
    assert 'data-target="dnsZone"' not in page, "an empty group is not rendered"
    assert "Resolves 2 findings together" in page


def test_every_group_and_change_carries_a_letter(scanned):
    """Letters come from the plugin's RATE_MAP; the page must not show a bare number."""
    result, _ = scanned
    for group in summarise(result)["remediation"]["groups"]:
        assert group["label"]
        assert all(change["label"] for change in group["changes"])


def test_both_bundles_list_the_changes_by_where_they_are_made(scanned):
    """The file handed to whoever fixes it has the same grouping as the page."""
    result, _ = scanned
    markdown = remediation_markdown(result, identifier=IDENTIFIER)
    html = remediation_html(result, identifier=IDENTIFIER)

    for text in (markdown, html):
        assert "Changes by where they are made" in text
        assert "Stop serving the deployment directory" in text
    assert "### Reverse proxy" in markdown


def test_a_clean_result_renders_no_group_section():
    """An empty section promising changes would be worse than none."""
    summary = summarise({"rating": 5, "remediationPlan": {"groups": [], "steps": []}})

    assert summary["remediation"]["groups"] == []
    assert "Changes by where they are made" not in remediation_markdown(
        {"rating": 5, "remediationPlan": {"groups": [], "steps": []}}
    )


def test_the_contract_describes_the_groups():
    """A client reading the OpenAPI document must learn the groups exist."""
    schemas = openapi_document()["components"]["schemas"]

    assert "groups" in schemas["RemediationPlan"]["properties"]
    assert schemas["RemediationGroup"]["properties"]["target"]["enum"] == [
        "reverseProxy",
        "identityProvider",
        "opencloud",
        "dnsZone",
    ]
    assert "resolvesSeveral" in schemas["RemediationChange"]["properties"]
