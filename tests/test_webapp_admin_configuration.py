"""
The operator area's configuration tab.

It is only worth having if it is complete and if it is safe to leave on a
screen. So these tests are about those two things: that the list of
variables is the list the settings actually read - in both directions, so a
new setting cannot be added without appearing here - and that no credential
ever reaches the page, whether it was set in the environment or not.
"""

from __future__ import annotations

import dataclasses

from fastapi.testclient import TestClient

from tests.webapp_support import (  # noqa: F401 - the fixtures are autouse
    _isolated_backend,
    _offline_resolver,
    settings,
)
from webapp import settings as settings_module
from webapp.app import create_app
from webapp.configuration import (
    FRONTEND_DIR,
    VARIABLES,
    VARIABLES_BY_NAME,
    grouped_rows,
    rows,
    unrecognised,
)
from webapp.environment_reference import REFERENCE
from webapp.settings import ENV_PREFIX, WebSettings

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


class _RecordingEnvironment(dict):
    """An environment that remembers every name somebody asked it for."""

    def __init__(self) -> None:
        super().__init__()
        self.asked: set[str] = set()

    def get(self, key, default=None):
        self.asked.add(key)
        return super().get(key, default)


# ------------------------------------------------------- the list is complete


def test_the_tab_lists_exactly_the_variables_the_settings_read(monkeypatch):
    """
    Written out by hand, and held to the code in both directions.

    A setting added to ``from_env`` and not here would be invisible on the one
    page meant to show everything; one listed here and no longer read would
    tell an operator a variable still does something.
    """
    recorded = _RecordingEnvironment()
    monkeypatch.setattr(settings_module.os, "environ", recorded)

    WebSettings.from_env()

    read = {name.removeprefix(ENV_PREFIX) for name in recorded.asked}
    listed = {
        variable.name
        for variable in VARIABLES
        if variable.name not in {FRONTEND_DIR, "ENCRYPTION_KEY_<n>"}
    }
    assert read == listed


def test_every_settings_field_is_shown_by_exactly_one_variable():
    """No value the service runs with may be left off the page, or shown twice."""
    fields = [field.name for field in dataclasses.fields(WebSettings)]
    shown = [variable.field for variable in VARIABLES if variable.field]

    assert sorted(shown) == sorted(fields)


def test_every_variable_carries_its_documented_description():
    """The table in docs/webapp.md is where a variable is explained; none may be missing."""
    assert set(VARIABLES_BY_NAME) == set(REFERENCE)
    assert all(REFERENCE[name]["description"] for name in REFERENCE)


def test_every_credential_shaped_setting_is_marked_secret():
    """
    The name is the cheap tripwire: a new ``*_TOKEN`` or ``*_KEY`` that was
    not marked would be printed on the page in full.
    """
    words = ("TOKEN", "SECRET", "KEY", "SALT", "PASSWORD")
    for variable in VARIABLES:
        if any(word in variable.name for word in words):
            assert variable.secret, variable.name


# -------------------------------------------------------- the values are true


def test_a_variable_from_the_environment_is_marked_and_shows_its_value_in_effect():
    """The value is the parsed one, and the source says the deployment named it."""
    configured = settings(scan_timeout=42)
    environ = {"COS_WEB_SCAN_TIMEOUT": "42"}

    by_name = {row.name: row for row in rows(configured, environ)}

    assert by_name["SCAN_TIMEOUT"].source == "environment"
    assert by_name["SCAN_TIMEOUT"].value == "42"
    assert by_name["RESULT_TTL"].source == "default"
    assert by_name["RESULT_TTL"].value == str(configured.result_ttl)


def test_an_empty_variable_counts_as_unset_the_way_the_settings_read_it():
    """``COS_WEB_X=`` falls back to the default in from_env, so it is no source here."""
    by_name = {row.name: row for row in rows(settings(), {"COS_WEB_SCAN_TIMEOUT": "  "})}

    assert by_name["SCAN_TIMEOUT"].source == "default"


def test_lists_and_switches_read_the_way_they_are_written():
    """A tuple is not ``('a', 'b')`` to an operator, and a flag is true or false."""
    configured = settings(blocked_targets=("a.example.com", ".example.org"), verify_tls=False)

    by_name = {row.name: row for row in rows(configured, {})}

    assert by_name["BLOCKED_TARGETS"].value == "a.example.com; .example.org"
    assert by_name["VERIFY_TLS"].value == "false"
    assert by_name["ALLOWED_HOSTS"].value is None


def test_groups_come_in_display_order_and_hold_every_row():
    """Grouping may reorder the page, never drop a variable from it."""
    groups = grouped_rows(settings(), {})

    assert sum(len(group_rows) for _, group_rows in groups) == len(VARIABLES)
    assert groups[0][0] == "storage"


# ------------------------------------------------- no credential on the page


def test_no_credential_reaches_the_page_set_or_not(monkeypatch):
    """
    Every secret gets a value nobody could mistake, and none may appear.

    Both halves: the environment names each one, and the settings carry it,
    because the page reads the value from one and the source from the other.
    """
    markers = {
        "rate_limit_salt": "marker-rate-limit-salt",
        "releases_token": "marker-releases-token",
        "webhook_secret": "marker-webhook-secret",
        "audit_salt": "marker-audit-salt",
        "purge_token": "marker-purge-token-" + "p" * 32,
        "purge_signing_key": "marker-purge-signing-key",
        "export_signing_key": "marker-export-signing-key",
    }
    for field, value in markers.items():
        variable = next(v for v in VARIABLES if v.field == field)
        monkeypatch.setenv(variable.env_name, value)
    monkeypatch.setenv("COS_WEB_ADMIN_PROXY_SECRET", SECRET)
    monkeypatch.setenv("COS_WEB_ENCRYPTION_KEY_1", "c" * 64)
    configured = _admin_settings(encryption_keys={1: "c" * 64}, **markers)

    with TestClient(create_app(configured)) as client:
        page = client.get("/admin/configuration", headers=FORWARDED).text

    assert "COS_WEB_PURGE_TOKEN" in page
    for value in (*markers.values(), SECRET, "c" * 64):
        assert value not in page
    # Which key versions exist is what a rotation needs checking; that stays.
    assert "ENCRYPTION_KEY_1" in page


def test_the_redis_password_is_hidden_and_the_rest_of_the_address_is_not():
    """Where Redis is still has to be readable; what gets in does not."""
    configured = settings(redis_url="redis://:hunter2-redis@redis:6379/0")

    by_name = {row.name: row for row in rows(configured, {})}

    redis_url = by_name["REDIS_URL"].value
    assert redis_url is not None and "hunter2-redis" not in redis_url
    assert by_name["REDIS_URL"].value == "redis://:******@redis:6379/0"


def test_an_address_without_a_password_is_shown_as_it_is():
    """The negative case: redaction must not mangle an ordinary URL."""
    by_name = {row.name: row for row in rows(settings(redis_url="memory://tests"), {})}

    assert by_name["REDIS_URL"].value == "memory://tests"


def test_a_misspelt_variable_is_named_and_its_value_is_not():
    """A typo is silent at startup; the tab is where it gets noticed."""
    environ = {
        "COS_WEB_IP_RATELIMIT": "maybe-a-credential",
        "COS_WEB_SCAN_TIMEOUT": "20",
        "COS_WEB_ENCRYPTION_KEY_2": "d" * 64,
        "COS_WEB_ENCRYPTION_KEY_NEW": "e" * 64,
        "OTHER_VARIABLE": "x",
    }

    assert unrecognised(environ) == ["COS_WEB_ENCRYPTION_KEY_NEW", "COS_WEB_IP_RATELIMIT"]


def test_the_page_lists_a_misspelt_variable_without_its_value(monkeypatch):
    """The same, through the rendered page rather than the helper."""
    monkeypatch.setenv("COS_WEB_IP_RATELIMIT", "maybe-a-credential")

    with TestClient(create_app(_admin_settings())) as client:
        page = client.get("/admin/configuration", headers=FORWARDED).text

    assert "COS_WEB_IP_RATELIMIT" in page
    assert "maybe-a-credential" not in page


# ------------------------------------------------------- the area's own rules


def test_the_tab_is_as_absent_as_the_rest_of_the_area_to_a_stranger():
    """A configuration page is the last thing to answer without the outpost's secret."""
    with TestClient(create_app(_admin_settings())) as client:
        forged = client.get(
            "/admin/configuration", headers={"x-authentik-username": OPERATOR}
        )
        admitted = client.get("/admin/configuration", headers=FORWARDED)

    assert forged.status_code == 404
    assert admitted.status_code == 200


def test_the_tab_does_not_exist_when_the_area_is_off():
    """Off means unregistered, for this path like every other one in the area."""
    with TestClient(create_app(settings())) as client:
        assert client.get("/admin/configuration").status_code == 404


def test_the_tab_is_reachable_from_the_strip_and_marks_itself_current():
    """The overview links to it, and on the tab itself the strip says where you are."""
    with TestClient(create_app(_admin_settings())) as client:
        overview = client.get("/admin", headers=FORWARDED).text
        tab = client.get("/admin/configuration", headers=FORWARDED).text

    assert 'href="/admin/configuration"' in overview
    assert 'href="/admin/configuration"\n     aria-current="page"' in tab
    assert "noindex" in tab
