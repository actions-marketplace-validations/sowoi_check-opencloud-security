"""
The grade badge: a picture of one finished scan, embeddable somewhere else.

An embedded image is the one rendering of a result that gets loaded by
browsers the visitor never chose, in pages this service did not write, so the
properties worth protecting are that it reaches nowhere else, says nothing the
scanned instance chose, and stays as unguessable and as short-lived as every
other reading of a uuid.
"""

from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET

from tests.fake_opencloud import FakeOpenCloud, InstanceBehaviour
from tests.webapp_support import (  # noqa: F401 - the fixtures are autouse
    MEMORY_URL,
    _isolated_backend,
    _offline_resolver,
    backend,
    client,
    settings,
)
from webapp.badge import LABEL, TONE_COLOURS, render
from webapp.catalog import rating_label
from webapp.redis_backend import memory_backend
from webapp.store import ScanStore
from webapp.tasks import run_scan

IDENTIFIER = "3f7d1a90-52b4-4a0c-9f1e-6b2c8d4e1a77"


def _finished_scan() -> None:
    """One real scan of the fake instance, stored and completed."""
    configured = settings(allow_private_targets=True, verify_tls=False, scan_timeout=5)
    store = ScanStore(backend=memory_backend(MEMORY_URL), ttl=configured.result_ttl)
    with FakeOpenCloud(InstanceBehaviour(basic_auth=True)) as instance:
        asyncio.run(
            store.create(
                IDENTIFIER,
                target=f"http://{instance.host}",
                ignore_hardenings=(),
                output_format="dashboard",
            )
        )
        asyncio.run(run_scan({"web_settings": configured, "store": store}, IDENTIFIER))


def test_the_badge_draws_the_grade_the_result_page_shows():
    """
    A badge that disagreed with the page it links to would be worse than none.

    The grade comes from the plugin's RATE_MAP by way of catalog.rating_label,
    so this asserts the letter rather than a colour somebody could change.
    """
    for rating in range(6):
        badge = ET.fromstring(render(rating))
        texts = [element.text for element in badge.iter() if element.tag.endswith("text")]

        assert rating_label(rating) in texts
        assert LABEL in texts


def test_a_good_and_a_bad_instance_do_not_look_alike():
    """
    The whole point is glanceable, and the colours are the dashboard's own.

    Asserted as the negative too: a badge that drew every grade in one colour
    would still pass a test that only looked at the letter.
    """
    good = render(5)
    bad = render(0)

    assert TONE_COLOURS["good"] in good
    assert TONE_COLOURS["bad"] in bad
    assert TONE_COLOURS["bad"] not in good


def test_a_rating_the_scan_never_produced_is_drawn_as_unknown():
    """A missing rating must not render as a grade, and must not raise either."""
    badge = render(None)

    assert "?" in badge
    assert TONE_COLOURS["good"] not in badge


def test_the_badge_fetches_nothing_and_runs_nothing():
    """
    An `<img>` pointing anywhere else would hand that server the result URL -
    whose uuid is the entire authorisation - in a referrer, on every view.
    """
    badge = render(4)
    # The one URL that may appear is the SVG namespace, which is an
    # identifier rather than an address anything fetches.
    assert badge.count('xmlns="http://www.w3.org/2000/svg"') == 1
    addressable = badge.replace('xmlns="http://www.w3.org/2000/svg"', "")

    for foreign in ("http", "<script", "<foreignObject", "@import", "<image", "xlink"):
        assert foreign not in addressable, foreign


def test_the_badge_says_nothing_the_scanned_instance_chose():
    """
    A hostname, product or version string is somebody else's text, and a badge
    is rendered into a document this project did not write.
    """
    _finished_scan()
    body = client().get(f"/api/scans/{IDENTIFIER}/badge.svg").text

    assert "127.0.0.1" not in body
    assert "OpenCloud" not in body.replace(LABEL, "")
    assert "localhost" not in body


def test_the_badge_is_served_as_an_image_that_may_not_be_cached_or_scripted():
    """
    It is a statement about somebody's instance, so it keeps the service-wide
    `no-store` that ADR 0031 makes the default - a shared cache holding one is
    what that rule exists to prevent - and it declares that it runs nothing.
    """
    _finished_scan()
    response = client().get(f"/api/scans/{IDENTIFIER}/badge.svg")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.headers["cache-control"] == "no-store"
    assert "default-src 'none'" in response.headers["content-security-policy"]
    assert ET.fromstring(response.text).tag.endswith("svg")


def test_an_unknown_or_unfinished_scan_answers_as_every_other_route_does():
    """
    A badge that drew "unknown" for a uuid nobody holds would be a way to ask
    whether one exists; 404 for unknown and 409 for pending keeps the badge
    from becoming the one reading of a uuid that answers differently.
    """
    test_client = client()
    identifier = test_client.post(
        "/api/scans", json={"target_url": "https://opencloud.example.com"}
    ).json()["uuid"]

    pending = test_client.get(f"/api/scans/{identifier}/badge.svg")
    unknown = test_client.get("/api/scans/0f4a1f22-7ce0-4f74-8a01-4d1d5b60e2aa/badge.svg")
    invalid = test_client.get("/api/scans/not-a-uuid/badge.svg")

    assert pending.status_code == 409
    assert unknown.status_code == 404
    assert invalid.status_code == 404
