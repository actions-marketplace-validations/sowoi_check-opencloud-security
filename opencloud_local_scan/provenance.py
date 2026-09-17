"""
The conditions a scan ran under, recorded while it ran.

Two scans of the same instance can disagree without the instance having
changed at all. The advisory database learned a CVE. The release schedule
moved a line to end of life. A day passed and a support window closed. The
scanner itself was upgraded and started making a check it did not make
before. An operator's waiver expired.

Comparing two result documents cannot tell any of that from a real
regression, because the documents record what was observed and not what was
known at the time. This records what was known: the scanner's version, the
moment of the scan, the release track it was asked for, the waivers in force,
how much it managed to measure, and a stable identifier for the exact
reference data it judged against.

Three rules shape what goes in here:

* **It is captured from the data the scan was given**, at the moment it ran -
  never looked up afterwards. A worker that refreshes its advisory database
  between the scan and the report would otherwise describe the scan with
  data the scan never saw.
* **A digest, not a copy.** The point is to answer "was this the same
  reference data?", which a digest answers in 64 characters. Embedding the
  database would put megabytes of other people's advisories into every
  report, and embedding a file path would publish where this server keeps
  its files.
* **Publication time and scan time are different facts.** A schedule
  generated in June and read in September has one of each, and a comparison
  that confuses them will call a stale file a fresh one.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

#: The block's own version, so a reader can tell this shape from a later one.
PROVENANCE_SCHEMA = 1

#: What an unknown digest looks like. A scan with no advisory data at all is
#: a fact worth recording as one, rather than as an empty string that reads
#: like a missing field.
NO_DATA = "none"


def digest(payload: Any) -> str:
    """
    A stable identifier for a piece of reference data.

    Canonical JSON with sorted keys, so two databases carrying the same
    advisories hash the same however they were serialised, merged or
    re-ordered. That is the whole requirement: a digest that changed when a
    file was merely rewritten would report reference-data churn on every
    scan and teach a reader to ignore it.
    """
    if payload is None:
        return NO_DATA
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def advisory_digest(advisories: Iterable[Any]) -> str:
    """
    A digest of the advisories a scan judged against.

    Built from each advisory's own identifying fields rather than from the
    object, so that a database read from a file and the same database read
    from a feed produce the same value.
    """
    entries = sorted(
        (
            str(getattr(advisory, "identifier", "") or getattr(advisory, "id", "")),
            str(getattr(advisory, "severity", "")),
            str(getattr(advisory, "fixed", "") or ""),
        )
        for advisory in advisories
    )
    return digest(entries) if entries else NO_DATA


def schedule_digest(schedule: Any) -> str:
    """A digest of the release schedule's lines, independent of its file."""
    lines = getattr(schedule, "lines", None)
    if not isinstance(lines, Mapping) or not lines:
        return NO_DATA
    entries = sorted(
        (
            f"{line[0]}.{line[1]}",
            str(getattr(entry, "released", "") or ""),
            str(getattr(entry, "end_of_life", "") or ""),
            str(getattr(entry, "release_type", "") or ""),
        )
        for line, entry in lines.items()
    )
    return digest(entries)


def waiver_state(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """
    The waivers in force, reduced to what a comparison needs.

    The patterns and their states, not the reasons: a reason is prose an
    operator wrote for another person, and a comparison that diffed it would
    report a corrected typo as a policy change.
    """
    return {
        "active": sorted(
            str(record.get("pattern"))
            for record in records
            if record.get("state") == "active"
        ),
        "expired": sorted(
            str(record.get("pattern"))
            for record in records
            if record.get("state") == "expired"
        ),
    }


def build(
    *,
    scanner_version: str,
    scanned_at: str,
    release_track: str,
    advisories: Iterable[Any],
    schedule: Any,
    waivers: Sequence[Mapping[str, Any]],
    coverage: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    The ``provenance`` block, from the data this scan was actually given.

    Every argument comes from the scan's own scope. Nothing is read from a
    module-level default or from the environment, because the point is to
    describe this run rather than the machine that later reads the report.
    """
    advisory_list = list(advisories)
    counts = (coverage or {}).get("counts") or {}
    return {
        "schema": PROVENANCE_SCHEMA,
        "scannerVersion": scanner_version,
        "scannedAt": scanned_at,
        "releaseTrack": release_track,
        "advisoryData": {
            "digest": advisory_digest(advisory_list),
            "count": len(advisory_list),
        },
        "scheduleData": {
            "digest": schedule_digest(schedule),
            # When the schedule was generated, which is not when it was read.
            "updated": str(getattr(schedule, "updated", "") or "") or None,
        },
        "waivers": waiver_state(waivers),
        "coverage": {
            "measured": int(counts.get("passed", 0)) + int(counts.get("failed", 0)),
            "total": int(counts.get("total", 0)),
        },
    }


def provenance_of(result: Mapping[str, Any]) -> dict[str, Any] | None:
    """
    The provenance block of a result document, or nothing when it has none.

    A report written before this existed does not describe the conditions it
    ran under. A comparison involving one can still be made - it just cannot
    explain as much, and has to say so rather than guess.
    """
    block = result.get("provenance")
    if not isinstance(block, Mapping) or "schema" not in block:
        return None
    return dict(block)
