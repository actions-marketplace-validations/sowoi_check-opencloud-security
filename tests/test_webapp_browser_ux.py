"""
The web application in a real browser: what the templates promise once scripts
and styles actually run.

The ASGI tests prove the server renders the right markup. These prove the
markup behaves: the CSP lets every page's own scripts run and nothing else,
nothing leaves loopback, the layout holds on a phone, and the progressive
enhancements (navigation, theme, language, waiver search, site search, back
to top) do what their comments say - and leave the page usable without them.

Plumbing and browser choice: ``tests/browser_support.py`` (ADR 0061).
"""

from __future__ import annotations

import pytest

from tests.browser_support import (  # noqa: F401 - the fixtures register under their own names
    PHONE,
    PageWatch,
    browser_fixture,
    new_page,
    page_fixture,
    shown_but_hidden,
    site_fixture,
    watch_fixture,
)

# Every public page a visitor can land on without a scan of their own.
PUBLIC_PAGES = [
    "/",
    "/about",
    "/how-it-works",
    "/grades",
    "/catalogue",
    "/privacy",
    "/api",
    "/documentation",
    "/compare",
    "/search?q=tls",
]


def _overflow(page) -> int:
    """How many CSS pixels the document is wider than the viewport."""
    return page.evaluate("() => document.scrollingElement.scrollWidth - window.innerWidth")


@pytest.mark.parametrize("path", PUBLIC_PAGES)
def test_every_public_page_runs_clean_under_its_own_csp(page, site, watch, path):
    """No script error, no CSP violation and no request that leaves the site, on any public page."""
    response = page.goto(site.base + path)
    assert response is not None and response.status == 200
    page.wait_for_load_state("load")
    assert "script-src" in (response.headers.get("content-security-policy") or "")
    assert page.locator("h1").count() == 1
    watch.assert_clean()


@pytest.mark.parametrize("path", PUBLIC_PAGES)
def test_nothing_marked_hidden_is_shown(page, site, path):
    """A `display` rule never outranks the `hidden` attribute a template or script set."""
    page.goto(site.base + path)
    page.wait_for_load_state("load")
    assert shown_but_hidden(page) == []


def test_the_watch_would_notice_a_script_error_and_a_blocked_request(page, site, watch):
    """The clean-page assertion is only worth something if it can fail."""
    page.goto(site.base + "/")
    page.evaluate("() => setTimeout(() => { throw new Error('planted'); }, 0)")
    page.evaluate("() => { const img = new Image(); img.src = 'http://example.org/beacon.png'; }")
    page.wait_for_timeout(500)
    assert any("planted" in error for error in watch.page_errors)
    assert any("example.org" in violation for violation in watch.csp_violations())
    with pytest.raises(AssertionError):
        watch.assert_clean()


@pytest.mark.parametrize("path", PUBLIC_PAGES)
def test_no_public_page_scrolls_sideways_on_a_phone(browser, site, path):
    """A 390-pixel viewport never needs horizontal scrolling."""
    watch = PageWatch()
    phone = new_page(browser, watch, viewport=PHONE, is_mobile=False)
    try:
        phone.goto(site.base + path)
        phone.wait_for_load_state("load")
        assert _overflow(phone) <= 1, path
    finally:
        phone.context.close()


def test_the_skip_link_is_the_first_stop_and_lands_on_the_content(page, site):
    """Keyboard users reach the main content in one keystroke."""
    page.goto(site.base + "/")
    # Document order rather than a Tab press: WebKit, like Safari, skips links
    # on Tab unless the reader turned that on, so the order is what we own.
    first = page.evaluate(
        """() => [...document.querySelectorAll('a[href], button, input, select, textarea, [tabindex]')]
            .find(el => el.tabIndex >= 0 && !el.disabled && el.type !== 'hidden').className"""
    )
    assert "skip-link" in first
    link = page.locator(".skip-link")
    link.focus()
    assert link.is_visible()
    page.keyboard.press("Enter")
    page.wait_for_url("**#main")
    assert page.locator("main#main").is_visible()


def test_the_phone_menu_opens_closes_and_returns_focus(browser, site):
    """The navigation toggle reports its state, and Escape closes it and gives focus back."""
    watch = PageWatch()
    phone = new_page(browser, watch, viewport=PHONE)
    try:
        phone.goto(site.base + "/")
        toggle = phone.locator(".nav-toggle")
        nav = phone.locator("#site-nav")
        assert toggle.is_visible()
        assert toggle.get_attribute("aria-expanded") == "false"
        assert not nav.is_visible()

        toggle.click()
        assert toggle.get_attribute("aria-expanded") == "true"
        assert nav.is_visible()

        phone.keyboard.press("Escape")
        assert toggle.get_attribute("aria-expanded") == "false"
        assert not nav.is_visible()
        assert phone.evaluate("() => document.activeElement.classList.contains('nav-toggle')")
        watch.assert_clean()
    finally:
        phone.context.close()


def test_the_wide_layout_needs_no_menu_toggle(browser, site):
    """Above the 1360-pixel breakpoint nav.js watches, the navigation is simply there."""
    wide = new_page(browser, PageWatch(), viewport={"width": 1440, "height": 900})
    try:
        wide.goto(site.base + "/")
        assert wide.locator("#site-nav").is_visible()
        assert not wide.locator(".nav-toggle").is_visible()
    finally:
        wide.context.close()


BODY_BACKGROUND = "() => getComputedStyle(document.body).backgroundColor"


def test_the_theme_toggle_switches_and_is_remembered(page, site):
    """The chosen theme repaints the page and survives a reload."""
    page.goto(site.base + "/")
    before = page.evaluate(BODY_BACKGROUND)
    page.click("[data-theme-toggle]")
    chosen = page.get_attribute("html", "data-theme")
    assert chosen in ("light", "dark")
    page.wait_for_function(f"(before) => ({BODY_BACKGROUND})() !== before", arg=before)

    page.reload()
    assert page.get_attribute("html", "data-theme") == chosen
    page.click("[data-theme-toggle]")
    assert page.get_attribute("html", "data-theme") != chosen


def test_a_dark_system_preference_starts_in_the_dark_theme(browser, site):
    """Without a stored choice, the page follows the operating system."""
    watch = PageWatch()
    dark = new_page(browser, watch, color_scheme="dark")
    light = new_page(browser, PageWatch(), color_scheme="light")
    try:
        colours = []
        for tab in (dark, light):
            tab.goto(site.base + "/")
            colours.append(tab.evaluate(BODY_BACKGROUND))
        assert colours[0] != colours[1]
        dark.click("[data-theme-toggle]")
        assert dark.get_attribute("html", "data-theme") == "light"
    finally:
        dark.context.close()
        light.context.close()


def test_choosing_a_language_translates_the_page_and_sticks(browser, site):
    """The language switcher applies on change, without a separate button press."""
    watch = PageWatch()
    page = new_page(browser, watch, viewport={"width": 1440, "height": 900})
    try:
        page.goto(site.base + "/about")
        assert page.get_attribute("html", "lang") == "en"
        english = page.inner_text("h1")
        assert not page.locator(".language-apply").is_visible()

        with page.expect_navigation():
            page.select_option("#language-choice", "de")
        assert page.get_attribute("html", "lang") == "de"
        assert page.inner_text("h1") != english
        assert page.url.endswith("/about")

        page.goto(site.base + "/")
        assert page.get_attribute("html", "lang") == "de"
        watch.assert_clean()
    finally:
        page.context.close()


def test_the_language_switcher_is_reachable_from_the_phone_menu(browser, site):
    """Below the breakpoint the switcher lives in the menu, and works from there."""
    phone = new_page(browser, PageWatch(), viewport=PHONE)
    try:
        phone.goto(site.base + "/")
        assert not phone.locator("#language-choice").is_visible()
        phone.click(".nav-toggle")
        with phone.expect_navigation():
            phone.select_option("#language-choice", "fr")
        assert phone.get_attribute("html", "lang") == "fr"
    finally:
        phone.context.close()


def test_the_address_pattern_is_a_valid_expression_for_the_browser(page, site):
    """Browsers compile `pattern` with the `v` flag; an invalid one silently turns validation off."""
    page.goto(site.base + "/")
    error = page.evaluate(
        """() => { const source = document.getElementById('target_url').pattern;
            try { new RegExp('^(?:' + source + ')$', 'v'); return ''; } catch (e) { return String(e); } }"""
    )
    assert error == ""


def test_an_address_the_form_cannot_scan_is_refused_before_submission(page, site):
    """The browser's own validation stops an empty or malformed address, and the page stays put."""
    page.goto(site.base + "/")
    page.click("form.scan-form button[type=submit]")
    assert page.url.rstrip("/") == site.base
    assert page.evaluate("() => document.getElementById('target_url').validity.valueMissing")

    page.fill("#target_url", "not a host name!")
    page.click("form.scan-form button[type=submit]")
    assert page.url.rstrip("/") == site.base
    assert page.evaluate("() => document.getElementById('target_url').validity.patternMismatch")

    page.fill("#target_url", "https://opencloud.example.com")
    assert page.evaluate("() => document.getElementById('target_url').checkValidity()")


def test_an_address_the_server_refuses_is_explained_on_the_form(page, site):
    """A well-formed address the service will not scan comes back with a reason, and the input is kept."""
    page.goto(site.base + "/")
    page.fill("#target_url", "https://opencloud.invalid")
    page.click("form.scan-form button[type=submit]")
    alert = page.locator(".scan-form [role=alert]")
    alert.wait_for()
    assert alert.inner_text().strip()
    assert page.input_value("#target_url") == "https://opencloud.invalid"
    assert "/scan/" not in page.url


def test_the_waiver_search_narrows_the_list_and_gives_it_back(page, site):
    """Typing filters the waiver checkboxes, nonsense says so, clearing restores everything."""
    page.goto(site.base + "/")
    page.click("details.waivers summary")
    options = page.locator("[data-waiver-option]")
    total = options.count()
    assert total > 3

    first = options.first
    first.locator("input").check()
    identifier = first.locator("input").get_attribute("value")

    page.fill("#waiver-search", identifier.lower())
    visible = page.locator("[data-waiver-option]:not([hidden])")
    assert 1 <= visible.count() < total
    assert page.locator("#waiver-empty").is_hidden()

    page.fill("#waiver-search", "zzz-no-such-check")
    assert page.locator("[data-waiver-option]:not([hidden])").count() == 0
    assert page.locator("#waiver-empty").is_visible()
    assert page.locator("[data-waiver-group]:not([hidden])").count() == 0

    page.fill("#waiver-search", "")
    assert page.locator("[data-waiver-option]:not([hidden])").count() == total
    assert first.locator("input").is_checked()


def test_site_search_finds_pages_and_says_when_it_finds_none(page, site, watch):
    """The search page answers from the static index, with links, and admits an empty result."""
    page.goto(site.base + "/search?q=hardening")
    results = page.locator("[data-search-results] li")
    results.first.wait_for()
    assert results.count() >= 1
    href = results.first.locator("a").first.get_attribute("href")
    assert href and href.startswith("/")
    assert page.input_value("[data-search-root] input[name=q]") == "hardening"

    page.goto(site.base + "/search?q=zzzqqqnothingmatches")
    page.wait_for_function("() => document.querySelector('[data-search-status]').textContent.trim() !== ''")
    assert page.locator("[data-search-results] li").count() == 0
    watch.assert_clean()


def test_the_back_to_top_link_appears_only_after_scrolling(page, site):
    """The shortcut stays out of the way until there is somewhere to go back from."""
    page.goto(site.base + "/documentation")
    link = page.locator(".back-to-top")
    assert link.is_hidden()
    page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
    link.wait_for(state="visible")
    link.click()
    page.wait_for_function("() => window.scrollY < window.innerHeight")
    link.wait_for(state="hidden")


def test_the_landing_page_settles_visible_with_motion_allowed(browser, site):
    """Entrance animations finish: nothing stays transparent for a reader who did not reduce motion."""
    watch = PageWatch()
    moving = new_page(browser, watch, reduced_motion="no-preference")
    try:
        moving.goto(site.base + "/")
        moving.wait_for_function(
            "() => getComputedStyle(document.querySelector('.scan-form')).opacity === '1'", timeout=5_000
        )
        watch.assert_clean()
    finally:
        moving.context.close()


def test_form_controls_are_labelled_and_images_described(page, site):
    """Every control on the landing page has an accessible name, and every image an alt or is hidden."""
    page.goto(site.base + "/")
    page.click("details.waivers summary")
    unnamed = page.evaluate(
        """() => [...document.querySelectorAll('input, select, textarea, button')]
            .filter(el => el.type !== 'hidden')
            .filter(el => !(el.labels && el.labels.length) && !el.getAttribute('aria-label')
                          && !el.getAttribute('aria-labelledby') && !el.textContent.trim()
                          && !el.getAttribute('title'))
            .map(el => el.outerHTML.slice(0, 80))"""
    )
    assert unnamed == []
    undescribed = page.evaluate(
        "() => [...document.images].filter(img => !img.hasAttribute('alt')).map(img => img.src)"
    )
    assert undescribed == []
