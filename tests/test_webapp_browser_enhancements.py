"""
The report page and landing form enhancements no other browser test drives:
the remembered form settings, the configuration-fragment picker, the share
buttons, the rescan countdown and the expiry warning.

Each of these is a script that rewrites server-rendered markup; the ASGI tests
only see the markup before the script ran. Plumbing and browser choice:
``tests/browser_support.py`` (ADR 0061).
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from tests.browser_support import (  # noqa: F401 - the fixtures register under their own names
    LiveSite,
    PageWatch,
    browser_fixture,
    new_page,
    page_fixture,
    site_fixture,
    submit_scan,
    watch_fixture,
)


@pytest.fixture(scope="module")
def weak_report(browser, site) -> str:
    """One finished report of the weak target, which has findings and fragments."""
    tab = new_page(browser, PageWatch())
    try:
        return submit_scan(tab, site, site.targets["weak"])
    finally:
        tab.context.close()


# ------------------------------------------------------------ remember.js


def test_submitted_settings_are_offered_back_and_applied_on_request(page, site):
    """A second visit offers the last settings; nothing changes until the visitor applies them."""
    page.goto(site.base + "/")
    offer = page.locator("[data-remember]")
    assert offer.is_hidden()

    page.click("details.waivers summary")
    waiver = page.locator("[data-waiver-option] input").first
    waiver.check()
    identifier = waiver.get_attribute("value")
    submit_scan_from_open_form(page, site.targets["hardened"])

    page.goto(site.base + "/")
    offer.wait_for(state="visible")
    assert page.locator("[data-remember-text]").inner_text().strip()
    # Offered, not applied.
    assert not page.locator(f"input[name=ignore_hardenings][value='{identifier}']").is_checked()
    # Never the address.
    assert page.input_value("#target_url") == ""

    page.click("[data-remember-apply]")
    assert offer.is_hidden()
    assert page.locator(f"input[name=ignore_hardenings][value='{identifier}']").is_checked()
    assert page.evaluate("() => document.querySelector('details.waivers').open")
    assert page.evaluate("() => document.activeElement.id") == "target_url"

    stored = page.evaluate("() => localStorage.getItem('cos-form-settings')")
    assert stored and site.targets["hardened"] not in stored


def submit_scan_from_open_form(page, target: str) -> None:
    page.fill("#target_url", target)
    page.click("form.scan-form button[type=submit]")
    page.wait_for_url("**/scan/**")


def test_forgetting_the_settings_removes_them_for_good(page, site):
    """Forget hides the offer and clears storage, so the next visit offers nothing."""
    page.goto(site.base + "/")
    page.evaluate(
        "() => localStorage.setItem('cos-form-settings', JSON.stringify({track: '', format: 'json', waivers: []}))"
    )
    page.reload()
    if page.locator("[data-remember]").is_hidden():
        pytest.skip("the stored settings equal the form's defaults on this deployment")
    page.click("[data-remember-forget]")
    assert page.locator("[data-remember]").is_hidden()
    assert page.evaluate("() => localStorage.getItem('cos-form-settings')") is None
    page.reload()
    assert page.locator("[data-remember]").is_hidden()


def test_garbage_in_storage_is_ignored(page, site, watch):
    """A corrupt or stale entry never breaks the form nor offers something unknown."""
    page.goto(site.base + "/")
    page.evaluate("() => localStorage.setItem('cos-form-settings', '{not json')")
    page.reload()
    assert page.locator("[data-remember]").is_hidden()
    page.evaluate(
        "() => localStorage.setItem('cos-form-settings', "
        "JSON.stringify({track: 'no-such-track', format: 'no-such-format', waivers: ['no-such-check']}))"
    )
    page.reload()
    assert page.locator("[data-remember]").is_hidden()
    watch.assert_clean()


# ------------------------------------------------------------ fragment.js


def test_the_fragment_picker_shows_one_flavour_and_remembers_it(page, site, weak_report, watch):
    """Scripted, the fragments collapse to one; the pressed flavour is the visible one and sticks."""
    page.goto(f"{site.base}/scan/{weak_report}")
    card = page.locator("#fragment-card")
    if card.count() == 0:
        pytest.skip("the weak target produced no configuration fragments")
    assert page.locator(".flavour-picker").is_visible()
    buttons = page.locator("[data-flavour]")
    assert buttons.count() >= 2
    assert page.locator("[data-fragment]:not([hidden])").count() == 1

    second = buttons.nth(1)
    chosen = second.get_attribute("data-flavour")
    second.click()
    assert second.get_attribute("aria-pressed") == "true"
    assert buttons.first.get_attribute("aria-pressed") == "false"
    visible = page.locator("[data-fragment]:not([hidden])")
    assert visible.count() == 1
    assert visible.get_attribute("data-fragment") == chosen

    page.reload()
    assert page.locator("[data-fragment]:not([hidden])").get_attribute("data-fragment") == chosen
    watch.assert_clean()


def test_without_scripting_every_fragment_stays_on_the_page(browser, site, weak_report):
    """No picker, no dead buttons: all flavours rendered, none hidden."""
    plain = new_page(browser, PageWatch(), java_script_enabled=False)
    try:
        plain.goto(f"{site.base}/scan/{weak_report}")
        if plain.locator("#fragment-card").count() == 0:
            pytest.skip("the weak target produced no configuration fragments")
        assert plain.locator(".flavour-picker").is_hidden()
        fragments = plain.locator("[data-fragment]")
        assert fragments.count() >= 2
        assert plain.locator("[data-fragment]:not([hidden])").count() == fragments.count()
        assert plain.locator("[data-copy-fragment]:visible").count() == 0
    finally:
        plain.context.close()


# ------------------------------------------------------------ share.js


def test_share_buttons_and_the_fallback_are_never_both_offered(page, site, weak_report):
    """With a clipboard the buttons replace the address fallback; without one, the fallback stays."""
    page.goto(f"{site.base}/scan/{weak_report}")
    buttons = page.locator("[data-share-copy]")
    if buttons.count() == 0:
        pytest.skip("this report has no share section")
    fallback = page.locator("[data-share-fallback]")
    has_clipboard = page.evaluate("() => !!(navigator.clipboard && navigator.clipboard.writeText)")
    if has_clipboard:
        assert buttons.first.is_visible()
        assert fallback.is_hidden()
    else:
        assert buttons.first.is_hidden()
        assert fallback.is_visible()


def test_a_share_button_confirms_the_copy_and_restores_its_label(page, site, weak_report):
    """Clicking copies the report address and says so, then the label comes back."""
    page.add_init_script(
        """(() => { window.__copied = [];
            const fake = { writeText: (text) => { window.__copied.push(text); return Promise.resolve(); } };
            Object.defineProperty(navigator, 'clipboard', { configurable: true, get: () => fake }); })()"""
    )
    page.goto(f"{site.base}/scan/{weak_report}")
    button = page.locator("[data-share-copy=link]")
    if button.count() == 0:
        pytest.skip("this report has no share section")
    label = button.inner_text()
    button.click()
    page.wait_for_function("() => document.querySelector('[data-share-copy=link]').dataset.shareState === 'done'")
    assert button.inner_text() == button.get_attribute("data-share-done")
    copied = page.evaluate("() => window.__copied")
    assert copied == [f"{site.base}/scan/{weak_report}"] or weak_report in copied[0]
    page.wait_for_function(
        "(label) => document.querySelector('[data-share-copy=link]').textContent === label", arg=label, timeout=5_000
    )


# ------------------------------------------------------------ rescan.js / expiry.js


# The cooldown is keyed by host without the port, so every fake target on
# 127.0.0.1 shares one; each timing test gets a site of its own.
@pytest.fixture(name="cooldown_site")
def cooldown_site_fixture() -> Iterator[LiveSite]:
    """A site that makes a target wait two minutes before it can be scanned again."""
    with LiveSite(profiles=("hardened",), redis_url="memory://browser-cooldown", target_cooldown=120) as live:
        yield live


@pytest.fixture(name="expiring_site")
def expiring_site_fixture() -> Iterator[LiveSite]:
    """A site whose results live less than the five-minute warning window."""
    with LiveSite(profiles=("hardened",), redis_url="memory://browser-expiry", result_ttl=240) as live:
        yield live


def test_the_rescan_button_waits_out_the_cooldown(browser, cooldown_site):
    """Disabled with a running countdown, re-enabled once the wait is over."""
    watch = PageWatch()
    page = new_page(browser, watch)
    try:
        submit_scan(page, cooldown_site, cooldown_site.targets["hardened"])
        card = page.locator("[data-rescan-after]")
        if card.count() == 0:
            pytest.skip("no rescan card on this report")
        button = page.locator("[data-rescan-button]")
        assert button.is_disabled()
        note = page.locator("#rescan-note")
        first = note.inner_text()
        assert ":" in first
        page.wait_for_function(
            "(first) => document.getElementById('rescan-note').textContent !== first", arg=first, timeout=5_000
        )

        # Jump the clock past the deadline instead of waiting two minutes.
        page.clock.install()
        page.reload()
        assert button.is_disabled()
        page.clock.run_for(125_000)
        page.wait_for_function("() => !document.querySelector('[data-rescan-button]').disabled")
        assert note.inner_text() == card.get_attribute("data-rescan-ready")
        watch.assert_clean()
    finally:
        page.context.close()


def test_the_expiry_warning_counts_down_and_says_when_the_report_is_gone(browser, expiring_site):
    """Inside the warning window the warning shows; past the deadline it says gone and drops the download link."""
    page = new_page(browser, PageWatch())
    try:
        uuid = submit_scan(page, expiring_site, expiring_site.targets["hardened"])
        warning = page.locator("[data-expiry-warning]")
        assert warning.is_visible()
        assert page.locator("[data-expiry-warning-text]").inner_text().strip()

        page.clock.install()
        page.goto(f"{expiring_site.base}/scan/{uuid}")
        page.clock.run_for(250_000)
        gone = warning.get_attribute("data-expiry-gone")
        page.wait_for_function(
            "(gone) => document.querySelector('[data-expiry-warning-text]').textContent === gone", arg=gone
        )
        assert page.locator("#expiry-note").inner_text() == gone
        action = page.locator("[data-expiry-warning-action]")
        if action.count():
            assert action.is_hidden()
    finally:
        page.context.close()
