"""
The golden corpus: the verdict a known instance earns must not drift.

Every other test here protects one property of one change. This one protects
the sum: a severity raised, a measure added to the catalogue, a threshold
moved, and every instance that looks like one of these is graded differently
- correctly according to each individual test, and with nobody deciding it.

A failure is a question, not a bug report. If the new verdict is what was
intended, `python scripts/update_golden_corpus.py` rewrites the corpus and
the change belongs in CHANGELOG.md; if it is not, the corpus just caught a
regression in the judgement before anybody's monitoring did.

The corpus is generated, so unlike everywhere else in this suite the
expectations are deliberately frozen rather than derived: derived
expectations cannot notice that the derivation itself changed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.golden_corpus import CASES, THRESHOLDS, record

CORPUS = Path(__file__).parent / "golden"


def _frozen(name: str) -> dict:
    path = CORPUS / f"{name}.json"
    assert path.exists(), (
        f"tests/golden/{name}.json is missing; "
        "run python scripts/update_golden_corpus.py"
    )
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", sorted(CASES))
def test_the_verdict_for_a_known_instance_has_not_changed(name):
    """
    The whole judgement for one instance, in one comparison.

    Rating, grade, failed checks, missing measures, the caps that produced
    the rating and the exit code under every threshold set - a change to any
    of them changes what somebody's monitoring does tonight.
    """
    assert record(name) == _frozen(name), (
        f"the verdict for '{name}' changed. If that was intended, run "
        "python scripts/update_golden_corpus.py and record it in CHANGELOG.md"
    )


def test_every_case_is_frozen_and_every_frozen_file_is_a_case():
    """A file nothing replays protects nothing, and so does a case with no file."""
    frozen = {path.stem for path in CORPUS.glob("*.json")}

    assert frozen == set(CASES)


def test_the_corpus_disagrees_with_itself_about_at_least_one_instance():
    """
    An assertion that would pass with the feature removed is worth nothing.

    A corpus whose cases all earn the same verdict would keep passing while
    the scanner stopped distinguishing them at all, which is the failure it
    is supposed to catch.
    """
    verdicts = [_frozen(name) for name in sorted(CASES)]
    ratings = {verdict["rating"] for verdict in verdicts}
    findings = {tuple(verdict["failedChecks"]) for verdict in verdicts}

    assert len(ratings) > 1
    assert len(findings) > 1


def test_no_recorded_verdict_carries_a_clock_or_a_host():
    """
    The corpus is a verdict, not a scan.

    A timestamp, a duration or the loopback address the fake instance
    happened to get would make it fail for reasons that have nothing to do
    with the judgement - and put a scan of somebody's machine in the
    repository the day it was recorded from one.
    """
    forbidden = ("scannedAt", "duration", "url", "domain", "addresses", "127.0.0.1")

    for name in sorted(CASES):
        text = (CORPUS / f"{name}.json").read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{name}.json carries {token}"


def test_every_threshold_set_is_recorded_for_every_case():
    """
    A profile added without a verdict is a profile nothing protects.

    The exit code is what a monitoring system acts on, so each named set has
    to be replayed - a rating that did not move can still start paging
    somebody if a threshold did.
    """
    for name in sorted(CASES):
        assert set(_frozen(name)["exitCodes"]) == set(THRESHOLDS)
