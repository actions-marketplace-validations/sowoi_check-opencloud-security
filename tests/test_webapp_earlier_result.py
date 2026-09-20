"""
A submission the target cooldown refuses, answered with the reader's own
earlier result instead of a dead end.

The server's part is small on purpose: it names the refused target on the
page and marks an earlier result as earlier. Which result that is comes from
the tab's own scan history, so nothing here ever hands one visitor a scan
somebody else started (ADR 0002).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

from tests.fake_opencloud import FakeOpenCloud, InstanceBehaviour
from tests.webapp_support import (  # noqa: F401 - the fixtures are autouse
    _isolated_backend,
    _offline_resolver,
    client,
    settings,
)
from webapp.app import create_app
from webapp.locales import de, en, es, fr
from webapp.tasks import run_scan

IDENTIFIER = "7c2e4a91-3d5b-4f60-8a17-9e0b1c2d3f45"
STATIC_JS = Path(__file__).resolve().parent.parent / "frontend" / "static" / "js"
NOTE = 'data-earlier-result'


def _pages(cooldown: int, *, claim: bool) -> tuple[str, str]:
    """The result page with and without ``?earlier=1``."""
    configured = settings(
        allow_private_targets=True, verify_tls=False, scan_timeout=5,
        target_cooldown=cooldown,
    )
    app = create_app(configured)
    with TestClient(app) as test_client:
        store = app.state.store
        with FakeOpenCloud(InstanceBehaviour()) as instance:
            asyncio.run(
                store.create(
                    IDENTIFIER,
                    target=f"http://{instance.host}",
                    ignore_hardenings=(),
                    output_format="dashboard",
                )
            )
            asyncio.run(run_scan({"web_settings": configured, "store": store}, IDENTIFIER))
            if claim:
                hostname = instance.host.rsplit(":", 1)[0]
                asyncio.run(app.state.limiter.check_target(hostname))
            return (
                test_client.get(f"/scan/{IDENTIFIER}?earlier=1").text,
                test_client.get(f"/scan/{IDENTIFIER}").text,
            )


def test_an_earlier_result_inside_a_cooldown_says_so_beside_the_countdown():
    earlier, plain = _pages(300, claim=True)

    assert NOTE in earlier
    assert "This is your earlier result" in earlier
    # The note sits above the countdown to the next scan, which is the timer.
    assert earlier.index(NOTE) < earlier.index('id="rescan-note"')
    assert "Ready to scan again in" in earlier
    # Without the parameter the page is the ordinary report.
    assert NOTE not in plain


def test_no_earlier_note_when_there_is_no_wait_to_explain():
    earlier, _ = _pages(0, claim=False)
    assert NOTE not in earlier


def test_a_cooldown_refusal_names_the_target_for_the_tabs_own_history():
    test_client = client(target_cooldown=300)
    form = {"target_url": "https://opencloud.example.com"}

    test_client.post("/api/scans", data=form, headers={"Accept": "text/html"})
    refused = test_client.post("/api/scans", data=form, headers={"Accept": "text/html"})

    assert refused.status_code == 429
    assert 'data-cooldown-target="https://opencloud.example.com"' in refused.text
    assert '<script src="/static/js/cooldown-offer.js" defer></script>' in refused.text
    # The refusal hands out no uuid: the script only has the ones this tab holds.
    assert "/scan/" not in refused.text.split("data-cooldown-offer", 1)[1][:400]


def test_other_refusals_offer_no_earlier_result():
    refused = client().post(
        "/api/scans",
        data={"target_url": "http://127.0.0.1:9200"},
        headers={"Accept": "text/html"},
    )
    assert refused.status_code == 400
    assert "data-cooldown-offer" not in refused.text


def test_the_script_reads_only_the_tabs_history_and_carries_no_english():
    source = (STATIC_JS / "cooldown-offer.js").read_text()
    code = "\n".join(
        line for line in source.splitlines()
        if not line.lstrip().startswith(("*", "/*", "//"))
    )
    assert "sessionStorage" in code
    assert "localStorage" not in code
    assert "fetch(" not in code and "XMLHttpRequest" not in code
    assert "?earlier=1" in code


def test_the_new_sentences_exist_in_every_catalogue():
    for catalogue in (en, de, es, fr):
        for key in ("index.cooldown.opening", "result.earlier.note"):
            assert catalogue.MESSAGES[key].strip()
