"""
The Atom feeds: the reference data, subscribable.

A feed is read by software nobody here wrote, in an application nobody here
inspected, so the properties worth protecting are that it parses, that it
carries somebody else's text as text, and that it never becomes a question
about an instance.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from tests.webapp_support import (  # noqa: F401 - the fixtures are autouse
    MEMORY_URL,
    _isolated_backend,
    _offline_resolver,
    backend,
    client,
    settings,
)
from webapp.advisories import advisory_catalogue, _bundled
from webapp.feeds import advisories_feed, schedule_feed
from opencloud_local_scan.versions import load_release_schedule

ATOM = "{http://www.w3.org/2005/Atom}"


def _entries(document: str) -> list[ET.Element]:
    return list(ET.fromstring(document).iter(f"{ATOM}entry"))


def _text(entry: ET.Element, tag: str) -> str:
    found = entry.find(f"{ATOM}{tag}")
    return "" if found is None or found.text is None else found.text


def test_the_advisory_feed_carries_every_advisory_the_catalogue_shows():
    """
    A feed that omits an advisory the page lists is worse than no feed.

    The expectation is derived from the same function the page calls, so an
    advisory added to the database shows up in both without anybody
    remembering this file.
    """
    catalogue = advisory_catalogue(_bundled())
    feed = advisories_feed(catalogue, origin="https://scan.example.com", updated="2026-08-21")

    entries = _entries(feed)
    assert catalogue, "the bundled database must hold an advisory to test this"
    assert len(entries) == len(catalogue)
    ids = {_text(entry, "id") for entry in entries}
    for advisory in catalogue:
        assert f"urn:check-opencloud-security:advisory:{advisory['id']}" in ids


def test_an_advisory_carries_what_a_reader_needs_to_act():
    """Severity and the affected range are the two facts that decide whether it matters."""
    catalogue = advisory_catalogue(_bundled())
    entry = _entries(
        advisories_feed(catalogue, origin="https://scan.example.com", updated="2026-08-21")
    )[0]

    assert _text(entry, "title")
    assert "Severity:" in _text(entry, "summary")
    assert "Affects" in _text(entry, "summary")
    assert _text(entry, "updated") == "2026-08-21T00:00:00Z"


def test_advisory_text_is_carried_as_text_and_never_as_markup():
    """
    Titles and descriptions come from a feed this project does not control.

    A reader that rendered one as HTML would be running somebody else's
    markup, so the escaping is asserted on a hostile entry rather than assumed
    from the real database, which contains none.
    """
    hostile = [
        {
            "id": "OC-TEST",
            "title": "<script>alert(1)</script>",
            "description": "</summary><script>alert(2)</script>",
            "severity": "high",
            "url": "https://example.com/a?b=1&c=2",
            "cwe": "",
            "ranges": [{"introduced": "1.0.0", "fixed": "1.0.1"}],
        }
    ]

    feed = advisories_feed(hostile, origin="https://scan.example.com", updated="2026-08-21")

    assert "<script>" not in feed
    assert "&lt;script&gt;" in feed
    # It still parses, and the text survives intact for a reader to display.
    entry = _entries(feed)[0]
    assert _text(entry, "title").endswith("<script>alert(1)</script>")
    assert all(
        element.get("type") == "text"
        for element in entry
        if element.tag in {f"{ATOM}title", f"{ATOM}summary"}
    )


def test_the_schedule_feed_dates_each_line_by_its_release():
    """
    A release date does not move, so a subscriber hears about a line once -
    rather than every night, when the schedule is re-read.
    """
    schedule = load_release_schedule()
    entries = _entries(schedule_feed(schedule, origin="https://scan.example.com"))

    assert len(entries) == len(schedule.lines)
    for entry in entries:
        assert _text(entry, "updated").endswith("Z")
        assert "Supported until:" in _text(entry, "summary")
    dates = {_text(entry, "updated") for entry in entries}
    assert len(dates) > 1, "every line must keep its own date, not the fetch time"


def test_both_feeds_parse_and_are_publicly_cacheable():
    """
    They describe what this service knows, not anybody's instance, which is
    what ADR 0031 requires before a route may be cached at all.
    """
    test_client = client()

    for path in ("/advisories.atom", "/release-schedule.atom"):
        response = test_client.get(path)
        assert response.status_code == 200, path
        assert response.headers["content-type"].startswith("application/atom+xml"), path
        assert response.headers["cache-control"] == "public, max-age=3600", path
        assert ET.fromstring(response.text).tag == f"{ATOM}feed", path


def test_a_feed_names_no_instance_and_answers_no_question_about_one():
    """
    This is the one part of the service that has never been able to say
    anything about a particular instance, and a feed must not become the
    exception - a filter by hostname would be exactly that.
    """
    test_client = client()
    response = test_client.get("/advisories.atom?target=opencloud.example.com")

    assert response.status_code == 200
    assert "opencloud.example.com" not in response.text
    # The query is ignored rather than honoured: the body is the whole feed.
    assert response.text == test_client.get("/advisories.atom").text
