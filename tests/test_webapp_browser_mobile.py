"""
The web application on a phone: a narrow, touch-driven screen.

``test_webapp_browser_ux.py`` already proves no page scrolls sideways and
the menu toggle answers Escape. These cover what a phone reader does with
a thumb: tap through the menu, run a scan, hit controls big enough to hit,
type without the page zooming - and what happens when the screen turns.

Plumbing and browser choice: ``tests/browser_support.py`` (ADR 0061).
``is_mobile`` is left alone because Firefox refuses it; ``has_touch`` is
what makes ``tap`` a touch.
"""

from __future__ import annotations

from typing import Any

import pytest

from tests.browser_support import (  # noqa: F401 - the fixtures register under their own names
    PHONE,
    PageWatch,
    browser_fixture,
    new_page,
    site_fixture,
    wait_until_final,
)

# The smallest target WCAG 2.2 accepts (2.5.8, Target Size (Minimum)).
MINIMUM_TARGET = 24

# Below this, iOS Safari zooms into a focused field and leaves the page zoomed.
MINIMUM_FIELD_FONT = 16


@pytest.fixture(name="phone")
def phone_fixture(browser: Any) -> Any:
    """A watched page on a 390-pixel touch screen."""
    watch = PageWatch()
    page = new_page(browser, watch, viewport=PHONE, has_touch=True)
    page.watch = watch
    yield page
    page.context.close()


def test_a_tapped_menu_link_takes_the_reader_there(phone, site):
    """The collapsed menu opens on a tap, and a link inside it navigates."""
    phone.goto(site.base + "/")
    phone.tap(".nav-toggle")
    nav = phone.locator("#site-nav")
    nav.wait_for(state="visible")
    link = nav.locator("a[href='/about']").first
    link.tap()
    phone.wait_for_url("**/about")
    assert phone.locator("h1").count() == 1
    assert phone.get_attribute(".nav-toggle", "aria-expanded") == "false"
    phone.watch.assert_clean()


def test_a_scan_runs_from_the_form_by_touch(phone, site):
    """A phone reader can submit the landing form with taps and read the finished report."""
    phone.goto(site.base + "/")
    phone.tap("#target_url")
    phone.fill("#target_url", site.targets["weak"])
    phone.tap("form.scan-form button[type=submit]")
    phone.wait_for_url("**/scan/**")
    wait_until_final(phone)
    assert phone.get_attribute("body", "data-scan-state") == "completed"
    assert phone.locator(".score-dial").is_visible()
    assert phone.evaluate("() => document.scrollingElement.scrollWidth - window.innerWidth") <= 1
    phone.watch.assert_clean()


def test_an_open_menu_closes_when_the_screen_turns_wide(phone, site):
    """nav.js shuts a menu left open once the header has room for the row again."""
    phone.goto(site.base + "/")
    phone.tap(".nav-toggle")
    assert phone.get_attribute(".nav-toggle", "aria-expanded") == "true"
    phone.set_viewport_size({"width": 1440, "height": 900})
    phone.wait_for_function(
        "() => document.querySelector('.nav-toggle').getAttribute('aria-expanded') === 'false'"
    )
    assert phone.locator("#site-nav").is_visible()
    assert not phone.locator(".nav-toggle").is_visible()
    phone.set_viewport_size(PHONE)
    phone.locator(".nav-toggle").wait_for(state="visible")
    assert not phone.locator("#site-nav").is_visible()


def test_every_menu_link_is_big_enough_to_tap(phone, site):
    """Each control in the open menu and the toggle itself meet the minimum target size."""
    phone.goto(site.base + "/")
    phone.tap(".nav-toggle")
    phone.locator("#site-nav").wait_for(state="visible")
    small = phone.evaluate(
        """(minimum) => [...document.querySelectorAll(
                '.nav-toggle, #site-nav a, #site-nav button, #site-nav select, #site-nav input')]
            .filter(el => el.getClientRects().length > 0)
            .map(el => [el, el.getBoundingClientRect()])
            .filter(([, box]) => box.width < minimum || box.height < minimum)
            .map(([el, box]) => `${el.outerHTML.slice(0, 60)} ${Math.round(box.width)}x${Math.round(box.height)}`)""",
        MINIMUM_TARGET,
    )
    assert small == []


def test_the_address_field_does_not_zoom_the_page_on_focus(phone, site):
    """Text fields use at least 16 pixels, so iOS keeps the page at its scale when one is focused."""
    phone.goto(site.base + "/")
    phone.click("details.waivers summary")
    tiny = phone.evaluate(
        """(minimum) => [...document.querySelectorAll('input:not([type=hidden]):not([type=checkbox])'
                + ':not([type=radio]), select, textarea')]
            .filter(el => el.getClientRects().length > 0)
            .filter(el => parseFloat(getComputedStyle(el).fontSize) < minimum)
            .map(el => el.outerHTML.slice(0, 80))""",
        MINIMUM_FIELD_FONT,
    )
    assert tiny == []


def test_without_scripting_every_menu_link_is_on_the_phone_screen(browser, site):
    """With nav.js blocked there is no collapsed menu: the links wrap and stay reachable."""
    plain = new_page(browser, PageWatch(), viewport=PHONE, java_script_enabled=False)
    try:
        plain.goto(site.base + "/")
        links = plain.locator("#site-nav a")
        assert links.count() > 0
        for index in range(links.count()):
            assert links.nth(index).is_visible(), links.nth(index).get_attribute("href")
        assert plain.evaluate("() => document.scrollingElement.scrollWidth - window.innerWidth") <= 1
    finally:
        plain.context.close()
