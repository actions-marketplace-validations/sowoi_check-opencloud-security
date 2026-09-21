"""
The pages only a deployment turns on, in a real browser: the operator's
area behind the authentik outpost and the interactive API documentation.

The ASGI tests prove the routes answer and the markup is right. These prove
the scripts do their part under the page's own CSP: admin.js replaces the
placeholders with readings from /admin/state, docs.js starts Swagger UI
without the inline script the policy would block, and ReDoc renders from
the vendored bundle - with nothing leaving loopback.

The refresh buttons are not pressed here: a refresh fetches published
sources, and a browser test has no network to fetch them from.

Plumbing and browser choice: ``tests/browser_support.py`` (ADR 0061).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from tests.browser_support import (  # noqa: F401 - the fixtures register under their own names
    LiveSite,
    PageWatch,
    browser_fixture,
    new_page,
)

# Placeholders only: the outpost's shared secret and the operator it vouches for.
SECRET = "b" * 48
OPERATOR = "operator"

#: What the outpost adds to a request it has already authenticated.
FORWARDED = {
    "x-cos-admin-proxy": SECRET,
    "x-authentik-username": OPERATOR,
}

#: The one foreign address ReDoc's bundle asks for; see the ReDoc test.
REDOC_LOGO = "https://cdn.redoc.ly/redoc/logo-mini.svg"

ADMIN_PAGES = ["/admin", "/admin/configuration", "/admin/rules"]


@pytest.fixture(scope="module", name="site")
def operator_site_fixture() -> Iterator[LiveSite]:
    """A live site with the operator's area and the API documentation turned on."""
    with LiveSite(
        profiles=("hardened",),
        admin_enabled=True,
        admin_proxy_secret=SECRET,
        admin_users=(OPERATOR,),
        enable_docs=True,
    ) as live:
        yield live


@pytest.fixture(name="operator")
def operator_fixture(browser: Any) -> Iterator[Any]:
    """A watched page whose every request carries the outpost's headers."""
    watch = PageWatch()
    page = new_page(browser, watch, extra_http_headers=FORWARDED)
    page.watch = watch
    yield page
    page.context.close()


@pytest.mark.parametrize("path", ADMIN_PAGES)
def test_every_admin_page_runs_clean_under_its_own_csp(operator, site, path):
    """No script error, no CSP violation and no stray request in the operator's area."""
    response = operator.goto(site.base + path)
    assert response is not None and response.status == 200
    operator.wait_for_load_state("load")
    assert "noindex" in (response.headers.get("x-robots-tag") or "")
    assert operator.locator("h1").count() == 1
    operator.watch.assert_clean()


def test_the_poll_replaces_every_placeholder_with_a_reading(operator, site):
    """admin.js asks /admin/state and writes an answer into each tile the server left as '-'."""
    operator.goto(site.base + "/admin")
    operator.wait_for_function(
        "() => [...document.querySelectorAll('[data-value]')].every(el => el.textContent.trim() !== '-')"
    )
    assert operator.get_attribute("[data-value=worker]", "data-state") in {"good", "bad", "warn"}
    operator.watch.assert_clean()


def test_a_stranger_finds_no_admin_area_in_the_browser(browser, site):
    """Without the outpost's headers the area is the ordinary 404 page, not a sign-in."""
    watch = PageWatch()
    stranger = new_page(browser, watch)
    try:
        for path in ADMIN_PAGES:
            response = stranger.goto(site.base + path)
            assert response is not None and response.status == 404, path
        assert stranger.locator("main a[href='/']").count() >= 1
        assert stranger.locator("[data-admin]").count() == 0
        # The 404 itself is a console error in every browser, so the rest is checked by hand.
        assert watch.page_errors == []
        assert watch.csp_violations() == []
        assert watch.foreign_requests == []
    finally:
        stranger.context.close()


def test_without_scripting_the_admin_actions_are_plain_forms(browser, site):
    """The refresh and probe buttons stay usable as ordinary form posts when admin.js never runs."""
    plain = new_page(browser, PageWatch(), java_script_enabled=False, extra_http_headers=FORWARDED)
    try:
        plain.goto(site.base + "/admin")
        forms = plain.locator("form[data-admin-action], form[data-admin-probe]")
        assert forms.count() >= 3
        for index in range(forms.count()):
            form = forms.nth(index)
            assert form.get_attribute("method") == "post"
            assert form.locator("button[type=submit]").is_visible()
    finally:
        plain.context.close()


def test_swagger_ui_renders_the_api_under_the_csp(browser, site):
    """docs.js starts Swagger UI from the vendored bundle and it lists this service's operations."""
    watch = PageWatch()
    page = new_page(browser, watch)
    try:
        response = page.goto(site.base + "/docs")
        assert response is not None and response.status == 200
        page.locator("#swagger-ui .opblock").first.wait_for(state="visible")
        assert page.locator("#swagger-ui .opblock").count() >= 1
        watch.assert_clean()
    finally:
        page.context.close()


def test_redoc_renders_the_api_under_the_csp(browser, site):
    """ReDoc draws the same document from the vendored bundle, with nothing fetched from outside."""
    watch = PageWatch()
    page = new_page(browser, watch)
    try:
        response = page.goto(site.base + "/redoc")
        assert response is not None and response.status == 200
        page.locator("redoc h1, [role=main] h1, .api-content h1").first.wait_for(state="visible")
        # ReDoc 2.5.3 always draws Redocly's logo from its CDN in the sidebar,
        # with no option to leave it out, and the vendored bundle is not
        # edited by hand. Chromium starts that request (WebKit and Firefox do
        # not); the page's policy must block it, and it must be the only one.
        assert set(watch.foreign_requests) <= {REDOC_LOGO}
        if watch.foreign_requests:
            page.wait_for_function("() => (window.__cspViolations || []).length > 0")
            assert any("cdn.redoc.ly" in violation for violation in watch.csp_violations())
            assert page.evaluate(
                "(src) => [...document.images].filter(img => img.src === src)"
                ".every(img => !img.complete || img.naturalWidth === 0)",
                REDOC_LOGO,
            )
        assert watch.page_errors == []
    finally:
        page.context.close()
