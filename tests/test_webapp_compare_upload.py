"""
Comparing a scan against a report somebody uploads.

An uploaded file is the only structure this application parses that it did not
write itself, so most of what is pinned here is a refusal: what the parser
does with a file that is too large, not text, not a report, or a report with
somebody else's ideas in it. The rest pins the two promises the page makes to
a reader who hands over a report about their own infrastructure - that the
file is not kept, and that what *is* kept goes away within five minutes.

The comparisons themselves are derived from two real scans of
``tests/fake_opencloud.py``, the same instance with a finding fixed in
between, rather than from a hardcoded list of identifiers that would go stale
the moment a check is added.
"""

from __future__ import annotations

import asyncio
import io
import json

import pytest

from tests.fake_opencloud import FakeOpenCloud, InstanceBehaviour
from tests.webapp_support import (  # noqa: F401 - the fixtures are autouse
    MEMORY_URL,
    _isolated_backend,
    _offline_resolver,
    backend,
    client,
    settings,
)
from webapp.comparisons import (
    MAX_COMPARISON_TTL_SECONDS,
    ComparisonStore,
    clamp_ttl,
    comparison_key,
    is_comparison_token,
    new_token,
)
from webapp.imports import (
    MAX_UPLOAD_BYTES,
    ReportRejected,
    parse_report,
)
from webapp.redis_backend import memory_backend
from webapp.reports import csv_report
from webapp.store import ScanStore
from webapp.tasks import run_scan

EARLIER = "b6f2c0c5-1c4b-4f4e-9a3b-0d3f8b7c1a20"
LATER = "c7a3d1d6-2d5c-4a5f-8b4c-1e4f9c8d2b31"
UNKNOWN = "d8b4e2e7-3e6d-4b60-9c5d-2f50ad9e3c42"
FIXED_FINDING = "exposed:/opencloud.yaml"


def _configured():
    return settings(allow_private_targets=True, verify_tls=False, scan_timeout=5)


def _scan(store: ScanStore, configured, identifier: str, target: str) -> None:
    asyncio.run(
        store.create(
            identifier,
            target=target,
            ignore_hardenings=(),
            output_format="dashboard",
        )
    )
    asyncio.run(run_scan({"web_settings": configured, "store": store}, identifier))


@pytest.fixture
def improved_pair():
    """The same instance twice: an exposed deployment file, and then not."""
    configured = _configured()
    store = ScanStore(backend=memory_backend(MEMORY_URL), ttl=configured.result_ttl)
    with FakeOpenCloud(InstanceBehaviour(exposed_paths={"/opencloud.yaml"})) as instance:
        target = f"http://{instance.host}"
        _scan(store, configured, EARLIER, target)
        instance.behaviour.exposed_paths = set()
        _scan(store, configured, LATER, target)

    earlier = asyncio.run(store.get(EARLIER))
    later = asyncio.run(store.get(LATER))
    assert earlier is not None and earlier.result is not None
    assert later is not None and later.result is not None
    return earlier.result, later.result


def _upload(test_client, payload: bytes, *, current: str = LATER, name: str = "scan.json"):
    return test_client.post(
        "/compare",
        data={"current": current},
        files={"report": (name, io.BytesIO(payload), "application/octet-stream")},
        follow_redirects=False,
    )


# --------------------------------------------------------------- the round trip


@pytest.mark.parametrize("fmt", ["json", "csv"])
def test_an_uploaded_report_answers_the_question_the_two_uuids_answer(
    improved_pair, fmt
):
    """
    The whole point: the earlier scan is gone, but its file is not.

    Both formats have to reach the same verdict about the same pair, because
    which file a reader happened to download is not a fact about their
    instance.
    """
    earlier, _later = improved_pair
    payload = (
        json.dumps(earlier).encode() if fmt == "json" else csv_report(earlier).encode()
    )
    test_client = client(**vars_of(_configured()))

    posted = _upload(test_client, payload, name=f"scan.{fmt}")
    assert posted.status_code == 303
    location = posted.headers["location"]
    assert location.startswith("/compare/")
    assert is_comparison_token(location.removeprefix("/compare/"))

    page = test_client.get(location)
    assert page.status_code == 200
    assert 'data-verdict="improved"' in page.text
    assert FIXED_FINDING in page.text


def vars_of(configured):
    """The overrides `client()` takes, from a settings object built here."""
    return {
        "allow_private_targets": configured.allow_private_targets,
        "verify_tls": configured.verify_tls,
        "scan_timeout": configured.scan_timeout,
    }


def test_the_page_says_the_earlier_side_came_from_a_file(improved_pair):
    """A comparison with an uploaded side is not the same claim as one without."""
    earlier, _later = improved_pair
    test_client = client()
    posted = _upload(test_client, json.dumps(earlier).encode())
    page = test_client.get(posted.headers["location"])

    assert "compare-source" in page.text
    # And the uploaded side is not offered a result page it does not have.
    assert f'href="/scan/{EARLIER}"' not in page.text


def test_a_csv_without_the_update_row_compares_neither_sides_updates(improved_pair):
    """
    A format that never recorded something must not be read as recording "none".

    An export written before the update row existed cannot say whether one was
    pending. Reading its silence as "no update then" would invent a regression
    out of a gap in the file, so the family is dropped from both sides and the
    page says so.
    """
    earlier, _later = improved_pair
    older_style = "\n".join(
        line
        for line in csv_report(earlier).splitlines()
        if not line.startswith("Update available")
    )
    imported = parse_report(older_style.encode())

    assert "update" not in imported.carries
    assert imported.missing_records == ("update",)

    test_client = client()
    posted = _upload(test_client, older_style.encode(), name="old.csv")
    page = test_client.get(posted.headers["location"])
    assert page.status_code == 200
    assert "update" in page.text.lower()


def test_a_fresh_csv_carries_the_pending_update(improved_pair):
    """The row added for the round trip is written, and read back."""
    earlier, _later = improved_pair
    rendered = csv_report(earlier)

    assert "Update available" in rendered
    assert parse_report(rendered.encode()).carries >= {"update"}


# ------------------------------------------------------------- what is refused


def test_a_file_larger_than_a_report_is_refused_before_it_is_parsed():
    """The ceiling is the parser's, not the body limit's, and it is much lower."""
    with pytest.raises(ReportRejected) as refusal:
        parse_report(b"{" + b" " * MAX_UPLOAD_BYTES)
    assert refusal.value.status == 413


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"\x89PNG\r\n\x1a\n binary",
        b"{\"rating\": 3\x00}",
        "{\"rating\": 3, \"caf\xe9\": 1}".encode("latin-1"),
        b"not json and not csv either, just a sentence",
        b"{}",
        b"[]",
        b'{"unrelated": "object"}',
    ],
)
def test_a_file_that_is_not_a_scan_report_is_refused(payload):
    """Every one of these is a 4xx with a sentence, never a traceback."""
    with pytest.raises(ReportRejected):
        parse_report(payload)


def test_deep_nesting_is_refused_rather_than_walked():
    """A document nested past any real one never reaches the rebuild."""
    payload = json.dumps({"rating": 3, "nest": _nested(60)}).encode()
    with pytest.raises(ReportRejected):
        parse_report(payload)


def _nested(depth: int):
    value: dict = {}
    for _ in range(depth):
        value = {"deeper": value}
    return value


def test_the_upload_endpoint_refuses_a_cross_site_post(improved_pair):
    """A page elsewhere must not be able to spend a borrowed browser's budget."""
    earlier, _later = improved_pair
    response = client().post(
        "/compare",
        data={"current": LATER},
        files={"report": ("s.json", io.BytesIO(json.dumps(earlier).encode()), "application/json")},
        headers={"Sec-Fetch-Site": "cross-site"},
        follow_redirects=False,
    )
    assert response.status_code == 403


def test_an_unknown_current_scan_is_a_404_and_an_unfinished_one_a_409(improved_pair):
    """The uuid on the later side keeps the meaning it has everywhere else."""
    earlier, _later = improved_pair
    test_client = client()

    missing = _upload(test_client, json.dumps(earlier).encode(), current=UNKNOWN)
    assert missing.status_code == 404

    asyncio.run(
        ScanStore(backend=memory_backend(MEMORY_URL), ttl=3600).create(
            UNKNOWN, target="https://opencloud.example.com",
            ignore_hardenings=(), output_format="dashboard",
        )
    )
    queued = _upload(test_client, json.dumps(earlier).encode(), current=UNKNOWN)
    assert queued.status_code == 409


def test_a_missing_file_or_a_missing_uuid_is_said_rather_than_guessed(improved_pair):
    """Neither half of the question is assumed."""
    earlier, _later = improved_pair
    test_client = client()

    without_uuid = test_client.post(
        "/compare",
        data={"current": ""},
        files={"report": ("s.json", io.BytesIO(json.dumps(earlier).encode()), "application/json")},
        follow_redirects=False,
    )
    assert without_uuid.status_code == 422

    without_file = test_client.post(
        "/compare", data={"current": LATER}, follow_redirects=False
    )
    assert without_file.status_code == 422


# -------------------------------------------------- what an upload cannot do


def test_nothing_from_the_upload_reaches_the_comparison_but_the_allow_list():
    """
    The boundary, stated as a test.

    A report carrying extra keys, a script tag, an over-long string and a
    finding identifier that is not one this scanner writes must produce a
    document built only of what `imports._rebuild` names.
    """
    hostile = {
        "rating": 2,
        "domain": "<script>alert(1)</script>opencloud.example.com",
        "version": "x" * 5000,
        "EOL": False,
        "__proto__": {"polluted": True},
        "extraChecks": [
            {"id": "basicAuthDisabled", "severity": "warning", "passed": False},
            {"id": "'; DROP TABLE scans; --", "severity": "critical", "passed": False},
            {"id": "ok", "severity": "<b>made up</b>", "passed": False},
        ],
        "scannedAt": {"date": "2026-01-01 00:00:00.0", "extra": "ignored"},
        "somethingElse": {"deeply": {"nested": "value"}},
    }
    imported = parse_report(json.dumps(hostile).encode())
    document = imported.document

    assert set(document) == {
        "domain", "product", "version", "releaseType", "rating", "EOL",
        "scannedAt", "extraChecks", "vulnerabilities", "hardenings", "setup",
        "updates", "ignored",
    }
    assert "__proto__" not in document and "somethingElse" not in document
    # Markup is not stripped here - escaping belongs to the renderer, and a
    # parser that half-stripped it would hand the template something that
    # looked safe. What this layer owes is the flattening and the cap.
    assert "\n" not in document["domain"] and "\r" not in document["domain"]
    assert len(document["version"]) <= 300
    # The identifier that is not one this scanner writes was dropped, and
    # counted rather than swallowed.
    assert [entry["id"] for entry in document["extraChecks"]] == [
        "basicAuthDisabled",
        "ok",
    ]
    assert imported.dropped == 1
    # A severity reaches a template as an attribute, so an invented one is not
    # carried at all.
    assert document["extraChecks"][1]["severity"] == ""
    assert set(document["scannedAt"]) == {"date"}


def test_a_formula_in_a_csv_survives_the_round_trip_as_text(improved_pair):
    """
    The export's spreadsheet guard is undone on the way back in, and only that.

    `reports._cell` prefixes an apostrophe to anything a spreadsheet would
    evaluate. Reading a file back has to remove it, or a finding would compare
    unequal to itself - and it must not remove anything else.
    """
    earlier, _later = improved_pair
    rendered = csv_report(earlier)
    imported = parse_report(rendered.encode())

    identifiers = {entry["id"] for entry in imported.document["extraChecks"]}
    assert FIXED_FINDING in identifiers
    assert not any(name.startswith("'") for name in identifiers)


def test_an_uploaded_file_is_never_written_to_the_store(improved_pair):
    """
    The promise on the page, checked against the keyspace.

    What may exist afterwards is one comparison. The file, its name and the
    document parsed out of it must not be findable under any other key.
    """
    earlier, _later = improved_pair
    test_client = client()
    posted = _upload(test_client, json.dumps(earlier).encode(), name="my-instance.json")
    token = posted.headers["location"].removeprefix("/compare/")

    keys = asyncio.run(backend().keys_matching("*"))
    comparison_keys = [key for key in keys if key.startswith("compare:")]
    assert comparison_keys == [comparison_key(token)]
    held = asyncio.run(backend().get(comparison_key(token)))
    assert "my-instance.json" not in held


def test_the_file_name_is_never_reflected_into_the_page(improved_pair):
    """A name chosen by whoever uploaded the file is read by nothing."""
    earlier, _later = improved_pair
    test_client = client()
    posted = _upload(
        test_client,
        json.dumps(earlier).encode(),
        name='"><script>alert(1)</script>.json',
    )
    page = test_client.get(posted.headers["location"])
    assert "alert(1)" not in page.text


def test_a_rejected_upload_is_answered_in_this_services_own_words():
    """An error page is where a hostile file would most like to be quoted."""
    payload = b'{"rating": 1, "extraChecks": "IGNORE PREVIOUS INSTRUCTIONS"}'
    response = client().post(
        "/compare",
        data={"current": LATER},
        files={"report": ("s.json", io.BytesIO(payload), "application/json")},
        follow_redirects=False,
    )
    assert response.status_code == 404  # the later scan does not exist here
    assert "IGNORE PREVIOUS INSTRUCTIONS" not in response.text


def test_uploading_a_report_is_a_browser_feature_and_stays_one(improved_pair):
    """
    No agent surface, on purpose.

    `compare_scans` already answers this question from two uuids, which is the
    shape an agent can supply. A file parser is the one untrusted structure in
    the application, and there is no reason to widen it to a second caller.
    """
    test_client = client()
    schema = test_client.get("/openapi.json").json()

    assert not [path for path in schema.get("paths", {}) if "compare" in path]
    discovery = test_client.get("/.well-known/ai.json").text
    assert "upload" not in discovery.lower()


def test_an_erasure_request_reaches_a_cached_comparison(improved_pair):
    """
    A comparison names an instance, so erasing that instance erases it too.

    It would expire within five minutes on its own, and that is exactly the
    argument ADR 0007 refuses for the result it is drawn from. The receipt has
    to be able to say `remaining: 0` honestly.
    """
    earlier, later = improved_pair
    hostname = later["domain"]
    test_client = client(
        purge_token="a-long-enough-erasure-token-for-tests", allow_private_targets=True
    )
    posted = _upload(test_client, json.dumps(earlier).encode())
    token = posted.headers["location"].removeprefix("/compare/")
    assert asyncio.run(backend().get(comparison_key(token))) is not None

    erased = test_client.request(
        "DELETE",
        f"/api/purge?target={hostname}",
        headers={"Authorization": "Bearer a-long-enough-erasure-token-for-tests"},
    )
    assert erased.status_code == 200
    receipt = erased.json()
    assert receipt["remaining"] == 0 and receipt["complete"] is True

    assert asyncio.run(backend().get(comparison_key(token))) is None
    assert test_client.get(f"/compare/{token}").status_code == 404


def test_an_erasure_for_another_instance_leaves_the_comparison_alone(improved_pair):
    """The negative: a purge erases what it names, not everything it finds."""
    earlier, _later = improved_pair
    test_client = client(
        purge_token="a-long-enough-erasure-token-for-tests", allow_private_targets=True
    )
    posted = _upload(test_client, json.dumps(earlier).encode())
    token = posted.headers["location"].removeprefix("/compare/")

    test_client.request(
        "DELETE",
        "/api/purge?target=someone-else.example.com",
        headers={"Authorization": "Bearer a-long-enough-erasure-token-for-tests"},
    )
    assert test_client.get(f"/compare/{token}").status_code == 200


# ------------------------------------------------------------ the five minutes


def test_a_comparison_is_kept_for_five_minutes_at_the_outside():
    """The promise is enforced by a clamp, not by a default nobody changed."""
    assert clamp_ttl(99_999) == MAX_COMPARISON_TTL_SECONDS
    assert clamp_ttl(60) == 60
    assert clamp_ttl(1) == 30
    assert ComparisonStore(backend=memory_backend(MEMORY_URL), ttl=3600).ttl == 300


def test_the_configured_window_may_be_shortened_but_never_lengthened():
    """An operator setting is honoured downwards and ignored upwards."""
    long_lived = client(comparison_ttl=86_400)
    short = client(comparison_ttl=60)
    assert long_lived.app.state.comparisons.ttl == MAX_COMPARISON_TTL_SECONDS
    assert short.app.state.comparisons.ttl == 60


def test_a_comparison_carries_that_ttl_into_redis(improved_pair):
    """The key expires on its own; nothing has to remember to delete it."""
    earlier, _later = improved_pair
    test_client = client()
    posted = _upload(test_client, json.dumps(earlier).encode())
    token = posted.headers["location"].removeprefix("/compare/")

    remaining = asyncio.run(backend().ttl(comparison_key(token)))
    assert 0 < remaining <= MAX_COMPARISON_TTL_SECONDS


def test_an_expired_comparison_is_the_same_404_as_one_that_never_existed(
    improved_pair,
):
    """
    Five minutes later there is nothing behind the token.

    And a token that was never issued answers identically, because telling the
    two apart is telling somebody whether a capability was ever real.
    """
    earlier, _later = improved_pair
    test_client = client()
    posted = _upload(test_client, json.dumps(earlier).encode())
    token = posted.headers["location"].removeprefix("/compare/")
    assert test_client.get(f"/compare/{token}").status_code == 200

    backend().advance(MAX_COMPARISON_TTL_SECONDS + 1)

    expired = test_client.get(f"/compare/{token}")
    never_existed = test_client.get(f"/compare/{new_token()}")
    assert expired.status_code == never_existed.status_code == 404


@pytest.mark.parametrize(
    "token",
    [
        "not-a-uuid",
        "../../etc/passwd",
        "{b6f2c0c5-1c4b-4f4e-9a3b-0d3f8b7c1a20}",
        "b6f2c0c5-1c4b-4f4e-9a3b-0d3f8b7c1a20 ",
        "B6F2C0C5-1C4B-4F4E-9A3B-0D3F8B7C1A20",
    ],
)
def test_a_token_that_is_not_one_we_issued_never_reaches_redis(token):
    """
    Caller-controlled text is kept out of a key name entirely.

    The canonical spelling is the test, not merely that ``UUID`` accepts the
    string: upper case and a stray space are each a *different* key for the
    same comparison, exactly as they would be for a scan.
    """
    assert not is_comparison_token(token)
    assert client().get(f"/compare/{token}").status_code == 404


def test_a_comparison_is_not_listed_anywhere(improved_pair):
    """
    There is no endpoint that enumerates them, exactly as for scans.

    ``/compare/`` is the form, not an index: a reader who trims the token off
    the address gets somewhere to ask again, never a list of what other people
    have asked.
    """
    earlier, _later = improved_pair
    test_client = client()
    posted = _upload(test_client, json.dumps(earlier).encode())
    token = posted.headers["location"].removeprefix("/compare/")

    index = test_client.get("/compare/")
    assert index.status_code == 200
    assert "compare-verdict" not in index.text
    assert token not in index.text
    assert test_client.get("/api/comparisons").status_code == 404


@pytest.mark.parametrize("domain", ["staging.example.com", ""])
def test_a_report_of_another_instance_is_refused_and_nothing_is_cached(
    improved_pair, domain
):
    """
    A file from staging against a scan of production answers nothing.

    Uploading the wrong file is the easiest way to get a confident verdict
    about two unrelated instances, and a report that names no instance cannot
    be shown to be the right one (ADR 0059). Nothing is held either: there is
    no comparison to come back to.
    """
    earlier, _later = improved_pair
    other = {**earlier, "domain": domain}
    test_client = client()

    posted = _upload(test_client, json.dumps(other).encode())

    assert posted.status_code == 422
    assert "different instances" in posted.text
    assert "compare-verdict" not in posted.text
    assert "staging.example.com" not in posted.text
    backend = memory_backend(MEMORY_URL)
    assert asyncio.run(backend.keys_matching("compare:*")) == []


def test_a_report_of_the_same_instance_in_other_capitals_is_compared(
    improved_pair,
):
    """A hostname is case-insensitive, so the refusal must be too."""
    earlier, _later = improved_pair
    shouted = {**earlier, "domain": earlier["domain"].upper() + "."}

    posted = _upload(client(), json.dumps(shouted).encode())

    assert posted.status_code == 303


def test_a_hostile_string_in_an_uploaded_report_is_escaped_in_the_page(
    improved_pair,
):
    """
    The renderer's job, checked where it matters most.

    The parser deliberately does not strip markup - escaping belongs to the
    template - so this is the test that says the template actually does it,
    for a string that arrived in a file rather than from a scanned host. The
    scan time carries it, because a report of another instance is refused
    before its domain could reach the page (ADR 0059).
    """
    earlier, _later = improved_pair
    hostile = {**earlier, "scannedAt": {"date": '<img src=x onerror="alert(1)">'}}
    test_client = client()
    posted = _upload(test_client, json.dumps(hostile).encode())
    page = test_client.get(posted.headers["location"])

    # The string is rendered, and rendered inert: no tag is opened and no
    # attribute is closed, so what a browser sees is text.
    assert "<img src=x" not in page.text
    assert 'onerror="alert(1)"' not in page.text
    assert "&lt;img src=x onerror=&#34;alert(1)&#34;&gt;" in page.text


def test_a_comparison_is_never_offered_to_a_shared_cache_or_a_crawler(
    improved_pair,
):
    """
    It is a statement about somebody's instance, like a result page.

    Indexing matters as much as caching here: the token in the address is the
    whole of the authorisation, so a crawler that kept the URL would be
    publishing the capability along with it.
    """
    earlier, _later = improved_pair
    test_client = client(allow_indexing=True)
    posted = _upload(test_client, json.dumps(earlier).encode())
    page = test_client.get(posted.headers["location"])

    assert "no-store" in page.headers.get("cache-control", "")
    assert "noindex" in page.headers.get("x-robots-tag", "")
    assert "noindex" in page.text
    # And the address never turns up anywhere a crawler is pointed at.
    token = posted.headers["location"].removeprefix("/compare/")
    assert token not in test_client.get("/sitemap.xml").text
