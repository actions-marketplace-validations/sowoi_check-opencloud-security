"""
`opencloud_local_scan.findings`: two documents compared finding by finding.

The baseline compares sets of names and answers "did anything get worse".
What is tested here is everything that answer throws away - the severity on
each side, the category a finding belongs to, and the difference between a
check that was fixed and one that was never measured - because those are the
three things the comparison in front of a reader is made of.
"""

from __future__ import annotations

import pytest

from opencloud_local_scan.findings import (
    ADVISORY_CATEGORY,
    APPEARED,
    DISAPPEARED,
    INTRODUCED,
    OPEN,
    PASSING,
    RESOLVED,
    compare,
    normalise_severity,
    severity_totals,
)


def _document(checks=(), advisories=()):
    """A result document with only the parts a comparison reads."""
    return {
        "domain": "opencloud.example.com",
        "rating": 4,
        "extraChecks": [
            {"id": identifier, "severity": severity, "passed": passed, "ignored": waived}
            for identifier, severity, passed, waived in checks
        ],
        "vulnerabilities": [
            {"id": identifier, "severity": severity} for identifier, severity in advisories
        ],
    }


def _by_id(deltas):
    return {delta.id: delta for delta in deltas}


def test_a_finding_that_stayed_open_and_got_worse_is_reported():
    """The gap this module exists to close: the baseline cannot see this move."""
    before = _document([("exposed:/.env", "high", False, False)])
    after = _document([("exposed:/.env", "critical", False, False)])

    delta = _by_id(compare(before, after))["exposed:/.env"]

    assert delta.status == OPEN
    assert delta.severity_change == ("high", "critical")
    assert delta.severity_worsened is True
    assert delta.changed is True


def test_a_severity_that_improved_is_not_reported_as_worsened():
    """Down is a direction too, and calling it a regression would be a lie."""
    before = _document([("exposed:/.env", "critical", False, False)])
    after = _document([("exposed:/.env", "low", False, False)])

    delta = _by_id(compare(before, after))["exposed:/.env"]

    assert delta.severity_change == ("critical", "low")
    assert delta.severity_worsened is False


def test_an_unmeasured_side_is_not_called_introduced_or_resolved():
    """ADR 0064: absent is absent. Claiming a fix nobody made is the worst answer."""
    before = _document([("basicAuthDisabled", "high", False, False)])
    after = _document([("cspWithoutUnsafeInline", "medium", False, False)])

    deltas = _by_id(compare(before, after))

    assert deltas["basicAuthDisabled"].status == DISAPPEARED
    assert deltas["basicAuthDisabled"].after is None
    assert deltas["cspWithoutUnsafeInline"].status == APPEARED
    assert deltas["cspWithoutUnsafeInline"].before is None
    assert {delta.status for delta in deltas.values()} == {APPEARED, DISAPPEARED}
    assert RESOLVED not in {delta.status for delta in deltas.values()}
    assert INTRODUCED not in {delta.status for delta in deltas.values()}


def test_a_waived_finding_is_still_a_finding():
    """A waiver silences an alert; it does not make the instance any safer."""
    before = _document([("exposed:/.env", "high", False, False)])
    after = _document([("exposed:/.env", "high", False, True)])

    delta = _by_id(compare(before, after))["exposed:/.env"]

    assert delta.after is not None
    assert delta.after.waived is True
    assert delta.after.failing is True
    assert severity_totals([delta]) == {"high": (1, 1)}


def test_findings_that_did_not_move_are_dropped_unless_asked_for():
    """"What changed" and "what is the state" are different questions."""
    before = _document([("basicAuthDisabled", "high", True, False)])
    after = _document([("basicAuthDisabled", "high", True, False)])

    assert compare(before, after) == ()

    everything = compare(before, after, changed_only=False)
    assert [delta.status for delta in everything] == [PASSING]


def test_a_category_filter_keeps_only_that_area():
    """The point of the filter: one question at a time, from one catalogue."""
    before = _document(
        [("Referrer-Policy", "low", False, False), ("exposed:/.env", "high", False, False)]
    )
    after = _document(
        [("Referrer-Policy", "low", True, False), ("exposed:/.env", "critical", False, False)]
    )

    headers = compare(before, after, categories=["headers"])
    exposure = compare(before, after, categories=["exposure"])

    assert [delta.id for delta in headers] == ["Referrer-Policy"]
    assert [delta.id for delta in exposure] == ["exposed:/.env"]
    assert {delta.id for delta in compare(before, after)} == {
        "Referrer-Policy",
        "exposed:/.env",
    }


def test_an_advisory_is_filed_under_its_own_category():
    """It is not a setting anybody can change, so no hardening category fits."""
    deltas = compare(_document(), _document(advisories=[("CVE-2026-0001", "high")]))

    assert [delta.category for delta in deltas] == [ADVISORY_CATEGORY]
    assert deltas[0].status == APPEARED
    assert compare(
        _document(), _document(advisories=[("CVE-2026-0001", "high")]),
        categories=["advisory"],
    ) == deltas


def test_the_worst_movement_is_reported_first():
    """A comparison is read from the top, so the top has to be worth reading."""
    before = _document(
        [
            ("Referrer-Policy", "low", False, False),
            ("exposed:/.env", "high", False, False),
            ("cspWithoutUnsafeInline", "medium", True, False),
        ]
    )
    after = _document(
        [
            ("Referrer-Policy", "low", True, False),
            ("exposed:/.env", "critical", False, False),
            ("cspWithoutUnsafeInline", "medium", False, False),
        ]
    )

    assert [delta.id for delta in compare(before, after)] == [
        "cspWithoutUnsafeInline",  # introduced
        "exposed:/.env",  # still open, and worse
        "Referrer-Policy",  # resolved
    ]


def test_the_severity_totals_count_both_sides():
    """The headline number: how bad it was, how bad it is."""
    before = _document(
        [("a", "critical", False, False), ("b", "low", False, False)]
    )
    after = _document([("a", "critical", False, False), ("b", "low", True, False)])

    assert severity_totals(compare(before, after, changed_only=False)) == {
        "critical": (1, 1),
        "low": (1, 0),
    }


@pytest.mark.parametrize(
    "value, expected",
    (
        ("CRITICAL", "critical"),
        (" high ", "high"),
        ("", "unknown"),
        (None, "unknown"),
        ("catastrophic", "unknown"),
    ),
)
def test_a_severity_is_read_from_the_document_never_guessed(value, expected):
    """Today's catalogue is not evidence about a scan written last month."""
    assert normalise_severity(value) == expected


def test_a_document_missing_the_lists_entirely_compares_to_nothing():
    """An old or partial document is empty here, never an exception."""
    assert compare({"rating": 4}, {"rating": 4}) == ()
    assert compare({"extraChecks": "nonsense"}, {"vulnerabilities": 7}) == ()
