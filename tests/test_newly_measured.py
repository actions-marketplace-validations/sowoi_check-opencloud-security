"""
A check only one of two scans made is neither new nor resolved.

An older scanner that did not know a check leaves nothing in its document for
that check, and the set arithmetic of a comparison read that nothing as
"passing". Scanning again with a newer scanner then reported the failure as a
regression of the instance - and the other way round, a check a later scan no
longer made read as fixed. Every document here comes from a real scan of
``tests/fake_opencloud.py``; the "older scanner" is that scan with one check
taken out of it, the way a scanner that never had the check would have
written it.
"""

from __future__ import annotations

import asyncio
import copy
from collections.abc import Callable
from pathlib import Path

import pytest

import check_opencloud_security as check
from opencloud_local_scan.baseline import Baseline, Snapshot, snapshot_of
from opencloud_local_scan.changes import explain
from opencloud_local_scan.scanner import ScannerSettings, scan
from tests.fake_opencloud import FakeOpenCloud, InstanceBehaviour
from tests.webapp_support import (  # noqa: F401 - the fixtures are autouse
    MEMORY_URL,
    _isolated_backend,
    _offline_resolver,
    client,
    settings,
)
from webapp.redis_backend import memory_backend
from webapp.store import ScanStore
from webapp.tasks import run_scan
from webapp.workflows import compare_documents

EXPOSED = "exposed:/opencloud.yaml"
FINDING = f"check:{EXPOSED}"
EARLIER = "e1a2b3c4-5d6e-4f70-8a9b-0c1d2e3f4a5b"
LATER = "f2b3c4d5-6e7f-4a81-9b0c-1d2e3f4a5b6c"


def _scan(exposed: bool) -> dict:
    """One real scan of the fake instance, with the deployment file exposed or not."""
    behaviour = InstanceBehaviour(exposed_paths={"/opencloud.yaml"} if exposed else set())
    with FakeOpenCloud(behaviour) as fake:
        return scan(fake.host, ScannerSettings(verify_tls=False))


def _without_check(result: dict, check_id: str) -> dict:
    """The same result as a scanner that never had this check would have written it."""
    older = copy.deepcopy(result)
    older["extraChecks"] = [
        entry for entry in older["extraChecks"] if entry.get("id") != check_id
    ]
    older["coverage"]["checks"] = [
        entry for entry in older["coverage"]["checks"] if entry.get("id") != check_id
    ]
    return older


@pytest.fixture(scope="module")
def failing() -> dict:
    result = _scan(exposed=True)
    assert FINDING in snapshot_of(result).findings, "the fixture must fail the check"
    return result


@pytest.fixture(scope="module")
def passing() -> dict:
    result = _scan(exposed=False)
    assert FINDING not in snapshot_of(result).findings
    return result


def test_a_failure_the_earlier_scan_never_checked_is_newly_measured_not_new(passing, failing):
    """The instance did not get worse; the scanner started looking."""
    older = _without_check(passing, EXPOSED)

    answer = compare_documents("a", "b", older, failing)

    assert FINDING in answer["newlyMeasured"]
    assert FINDING not in answer["introduced"]
    assert any(
        item["change"] == f"+ {EXPOSED} (not checked before)" for item in answer["changes"]
    )


def test_a_check_that_passed_before_and_fails_now_is_still_introduced(passing, failing):
    """The negative: a real regression must never be softened into 'newly measured'."""
    answer = compare_documents("a", "b", passing, failing)

    assert FINDING in answer["introduced"]
    assert FINDING not in answer["newlyMeasured"]
    assert answer["verdict"] == "regressed"


def test_a_failure_the_later_scan_did_not_check_is_not_resolved(failing, passing):
    """Nobody fixed it: the later scan did not look, so the result is not an improvement."""
    later = _without_check(failing, EXPOSED)
    # The same instance, the same evidence, one check fewer: only that check moved.
    later["rating"] = failing["rating"]

    answer = compare_documents("a", "b", failing, later)

    assert answer["noLongerMeasured"] == [FINDING]
    assert FINDING not in answer["resolved"]
    assert answer["verdict"] != "improved"


def test_a_report_that_does_not_list_its_checks_is_compared_as_before(passing, failing):
    """An uploaded report carries no check list; guessing from it would hide a regression."""
    older = copy.deepcopy(passing)
    older["coverage"]["checks"] = []

    answer = compare_documents("a", "b", older, failing)

    assert FINDING in answer["introduced"]
    assert answer["newlyMeasured"] == []


def test_the_explanation_blames_the_scanner_rather_than_the_instance(passing, failing):
    """A check the first scan never made did not 'start failing' on the instance."""
    older = _without_check(passing, EXPOSED)

    changes = {change.code: change for change in explain(older, failing).changes}

    assert "checksNewlyMeasured" in changes
    assert changes["checksNewlyMeasured"].category == "scanner"
    assert changes["checksNewlyMeasured"].evidence["failing"] == [EXPOSED]
    appeared = changes.get("findingsAppeared")
    assert appeared is None or EXPOSED not in appeared.evidence["checks"]

    # And the negative: a check both scans made still started failing on the instance.
    changes = {change.code: change for change in explain(passing, failing).changes}
    assert EXPOSED in changes["findingsAppeared"].evidence["checks"]
    assert "checksNewlyMeasured" not in changes


def test_the_considered_checks_survive_the_baseline_file(failing):
    """The plugin compares against what it wrote to disk, not against the document."""
    snapshot = snapshot_of(failing)
    restored = Snapshot.from_dict(snapshot.as_dict())

    assert restored is not None
    assert restored.considered == snapshot.considered
    assert FINDING in (restored.considered or ())


def test_a_baseline_written_before_the_check_list_is_compared_as_before(passing, failing):
    """An old baseline file cannot say what it checked, so nothing is excused."""
    stored = snapshot_of(_without_check(passing, EXPOSED)).as_dict()
    stored.pop("considered")
    previous = Snapshot.from_dict(stored)
    assert previous is not None and previous.considered is None

    baseline = Baseline(path=Path("unused"))
    baseline.record("opencloud.example.com", previous)
    comparison = baseline.compare("opencloud.example.com", snapshot_of(failing))

    assert FINDING in comparison.new_findings
    assert comparison.newly_measured == ()


def test_warn_on_new_still_alerts_on_a_newly_measured_failure(tmp_path, passing, failing):
    """Nobody has been told about it yet, so going quiet would hide it for good."""
    context = check.ScanContext(
        host="opencloud.example.com",
        baseline_path=str(tmp_path / "baseline.json"),
        warn_on_new=True,
    )

    def apply(result: dict, code: check.NagiosExitCode):
        return check._apply_baseline(
            context, result, hardenings=[], waived=[],
            message=f"{code.name}: original", exit_code=code,
        )

    apply(_without_check(passing, EXPOSED), check.NagiosExitCode.WARNING)
    message, code, lines, comparison = apply(failing, check.NagiosExitCode.WARNING)

    assert comparison.newly_measured == (FINDING,)
    assert comparison.regressed
    assert (message, code) == ("WARNING: original", check.NagiosExitCode.WARNING)
    assert any("Newly measured (1)" in line for line in lines)

    # The next run knows the check, so the unchanged failure goes quiet as usual.
    _, code, _, comparison = apply(failing, check.NagiosExitCode.WARNING)
    assert comparison.newly_measured == ()
    assert code is check.NagiosExitCode.OK


def _stored_pair(rewrite: Callable[[dict], dict]) -> None:
    """Two finished scans of one fake instance, the earlier one passed through *rewrite*."""
    configured = settings(allow_private_targets=True, verify_tls=False, scan_timeout=5)
    store = ScanStore(backend=memory_backend(MEMORY_URL), ttl=configured.result_ttl)
    with FakeOpenCloud(InstanceBehaviour(exposed_paths={"/opencloud.yaml"})) as instance:
        target = f"http://{instance.host}"
        for identifier in (EARLIER, LATER):
            asyncio.run(
                store.create(
                    identifier, target=target, ignore_hardenings=(), output_format="dashboard"
                )
            )
            asyncio.run(run_scan({"web_settings": configured, "store": store}, identifier))
    record = asyncio.run(store.get(EARLIER))
    assert record is not None and record.result is not None
    asyncio.run(store.mark_completed(EARLIER, rewrite(record.result)))


def test_the_page_lists_a_newly_measured_failure_apart_from_new_findings():
    """The reader sees the failure, and is told it is not the instance's doing."""
    _stored_pair(lambda result: _without_check(result, EXPOSED))

    page = client().get(f"/compare?baseline={EARLIER}&current={LATER}")

    assert page.status_code == 200
    assert "Checked for the first time (1)" in page.text
    assert "New findings (0)" in page.text


def test_the_page_has_no_such_section_when_both_scans_made_the_same_checks():
    """An empty 'checked for the first time' card would suggest the scanner changed."""
    _stored_pair(lambda result: result)

    page = client().get(f"/compare?baseline={EARLIER}&current={LATER}")

    assert page.status_code == 200
    assert "Checked for the first time" not in page.text
    assert "No longer checked" not in page.text
