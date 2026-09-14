"""
The operator area's rules tab.

It is only worth having if it describes what the service actually enforces.
So these tests change a setting and look for the change on the page, look for
the lists the enforcing code holds rather than a copy of them, and check the
tab is exactly as hidden as the rest of the area.
"""

from __future__ import annotations

import asyncio
import re

import pytest
from fastapi.testclient import TestClient
from markupsafe import escape

from tests.webapp_support import (  # noqa: F401 - the fixtures are autouse
    _isolated_backend,
    _offline_resolver,
    settings,
)
from webapp.app import create_app
from webapp.i18n import SUPPORTED_LOCALES, Translator
from webapp.rules import GROUPS, duration, enforcement_groups, escalation
from webapp.ssrf import SUSPICIOUS_REJECTIONS, WILDCARD_DNS_SUFFIXES

SECRET = "b" * 48
OPERATOR = "okko"

FORWARDED = {
    "x-cos-admin-proxy": SECRET,
    "x-authentik-username": OPERATOR,
    "sec-fetch-site": "same-origin",
}


def _admin_settings(**overrides):
    return settings(
        admin_enabled=True,
        admin_proxy_secret=SECRET,
        admin_users=(OPERATOR,),
        **overrides,
    )


def _page(headers=FORWARDED, **overrides) -> str:
    with TestClient(create_app(_admin_settings(**overrides))) as client:
        response = client.get("/admin/rules", headers=headers)
    assert response.status_code == 200
    return response.text


def _state(page: str, rule: str) -> str:
    match = re.search(rf'data-rule="{rule}" data-state="(on|off)"', page)
    assert match, f"rule {rule} is not on the page"
    return match.group(1)


def test_the_tab_is_as_absent_as_the_rest_of_the_area_to_a_stranger():
    """A stranger must not learn from this path that an operator area exists."""
    with TestClient(create_app(_admin_settings())) as client:
        assert client.get("/admin/rules").status_code == 404
        assert client.get("/admin/rules", headers={**FORWARDED, "x-cos-admin-proxy": "x" * 48}).status_code == 404
        assert client.get("/admin/rules", headers=FORWARDED).status_code == 200


def test_the_tab_does_not_exist_when_the_area_is_off():
    """Off means absent, not protected."""
    with TestClient(create_app(settings())) as client:
        assert client.get("/admin/rules", headers=FORWARDED).status_code == 404


def test_the_tab_is_in_the_strip_and_marks_itself_current():
    """A tab nobody can reach from the navigation is a tab nobody opens."""
    page = _page()
    overview = _page_at("/admin")

    assert re.search(r'href="/admin/rules"\s+aria-current="page"', page)
    assert 'href="/admin/rules"' in overview
    assert not re.search(r'href="/admin/rules"\s+aria-current="page"', overview)


def _page_at(path: str) -> str:
    with TestClient(create_app(_admin_settings())) as client:
        return client.get(path, headers=FORWARDED).text


def test_the_numbers_on_the_page_are_the_ones_this_deployment_runs_with():
    """
    A limit changed in the environment must change on the page.

    Two different configurations, each looked for in its own page and absent
    from the other's, so the test cannot pass on a sentence that merely
    happens to contain the default.
    """
    tight = _page(
        ip_rate_limit=7, ip_rate_window=120, probe_limit=3, probe_block=600,
        probe_block_max=21600, probe_repeat_window=3600, daily_scan_limit=12,
    )
    loose = _page(
        ip_rate_limit=40, ip_rate_window=60, probe_limit=9, probe_block=3600,
        probe_block_max=86400, probe_repeat_window=86400, daily_scan_limit=200,
    )

    assert "At most 7 submissions per client every 2 min" in tight
    assert "At most 40 submissions per client every 1 min" in loose
    assert "3 strikes within" in tight and "3 strikes within" not in loose
    assert "10 min → 1 h → 6 h" in tight
    assert "1 h → 6 h → 24 h" in loose
    assert "10 min → 1 h → 6 h" not in loose
    assert "At most 12 submissions" in tight and "At most 200 submissions" in loose


def test_a_rule_that_is_switched_off_says_so():
    """An operator must be able to tell a limit that is off from one that is on."""
    off = _page(daily_scan_limit=0, probe_limit=0, target_cooldown=0)
    on = _page(daily_scan_limit=5, probe_limit=5, target_cooldown=300)

    for rule in ("daily_cap", "probe_block", "probe_escalation", "strike_scans", "target_cooldown"):
        assert _state(off, rule) == "off"
        assert _state(on, rule) == "on"


def test_a_deployment_scanning_its_own_network_shows_the_address_rules_off():
    """Allowing private targets lifts the guard, and the page must not claim otherwise."""
    public = _page()
    private = _page(allow_private_targets=True)

    for rule in ("private_addresses", "internal_names", "wildcard_dns", "dns_consistency"):
        assert _state(public, rule) == "on"
        assert _state(private, rule) == "off"
    # Following a redirect is checked either way.
    assert _state(private, "redirects") == "on"


def test_the_lists_are_the_ones_the_guard_holds():
    """A name added to the guard appears here without anybody editing the page."""
    page = _page()

    for suffix in WILDCARD_DNS_SUFFIXES:
        assert f"<code>{suffix}</code>" in page
    refusals = enforcement_groups(_admin_settings(), 0)[1][1][-1]
    assert refusals.key == "strike_refusals"
    assert len(refusals.labels) == len(SUSPICIOUS_REJECTIONS)


def test_approval_mode_lists_what_the_operator_approved_and_the_record_that_approves():
    """The operator wrote those entries; the page reads them back."""
    on = _page(require_approval=True, approved_targets=("opencloud.example.com", ".example.org"))
    off = _page()

    assert _state(on, "approval") == "on"
    assert "<code>opencloud.example.com</code>" in on
    assert "check-opencloud-security=testserver" in on
    assert _state(off, "approval") == "off"
    assert "check-opencloud-security=testserver" not in off


def test_the_rating_section_carries_the_scanners_own_ceilings():
    """The ceilings are imported from the scanner, so the tab shows its numbers."""
    from webapp.catalog import severity_caps

    page = _page()

    assert 'id="admin-rules-rating"' in page
    for _, cap, label in severity_caps():
        assert f"at best <strong>{label}</strong>" in page


def test_the_page_names_nothing_anybody_scanned():
    """The same property as the rest of the area: counts and the operator's own lists."""
    identifier = "8c1d0e3c-9b2f-4c81-a7e6-2f0b4d9c1e73"
    app = create_app(_admin_settings())
    with TestClient(app) as client:
        asyncio.run(
            app.state.store.create(
                identifier,
                target="https://secret-instance.example.com",
                ignore_hardenings=(),
                output_format="dashboard",
            )
        )
        page = client.get("/admin/rules", headers=FORWARDED).text

    assert "secret-instance" not in page
    assert identifier not in page


@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
def test_every_rule_renders_in_every_language(locale):
    """A placeholder a translation forgot would break the tab for that language only."""
    with TestClient(create_app(_admin_settings(require_approval=True, approved_targets=("a.example.com",)))) as client:
        client.cookies.set("cos_locale", locale)
        response = client.get("/admin/rules", headers=FORWARDED)

    assert response.status_code == 200
    translate = Translator(locale)
    for group in GROUPS:
        assert str(escape(translate(f"admin.rules.group.{group}"))) in response.text
    assert "admin.rules." not in response.text


def test_durations_read_in_the_largest_whole_unit():
    """Seconds nobody can picture are how a limit gets misread."""
    assert [duration(value) for value in (45, 60, 300, 3600, 86400, 259200, 5400)] == [
        "45 s", "1 min", "5 min", "1 h", "24 h", "3 d", "1 h 30 min",
    ]


def test_the_escalation_stops_where_the_ceiling_does():
    """Past the ceiling every block is the same, so the page stops listing them."""
    assert escalation(_admin_settings(probe_block=3600, probe_block_max=86400)) == ("1 h", "6 h", "24 h")
    assert escalation(_admin_settings(probe_block=3600, probe_block_max=3600)) == ("1 h",)
    assert escalation(_admin_settings(probe_block=3600, probe_repeat_window=0)) == ("1 h",)
