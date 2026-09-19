"""
What each release worth moving to would do, before anybody installs it.

``upgradePath`` answers the question for the one release the scan
recommends. An operator choosing between a patch on the current line and a
jump to the next one has a second question: what would *each* of them fix,
what would it leave, and where would the rating end up? This module answers
it by replaying the scanner's own version rules - end of life, matching
advisories, a line behind, a patch behind - for every candidate release in
the schedule, and then applying the caps the instance's findings already
impose. An upgrade changes the version, not the reverse proxy, so the
findings stay exactly as the scan measured them.

**It measures, it does not judge.** Ratings are the scanner's 0-5 numbers;
the letters belong to the plugin's ``RATE_MAP``.

**It knows nothing new.** Every candidate comes from the release schedule the
scan already used, every advisory from the same database, so a rehearsal
cannot disagree with the scan that runs after the upgrade - short of new
advisories or releases being published in between.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import Any

from .versions import ReleaseSchedule, compare_versions, release_line
from .vulndb import VulnerabilityDatabase

MIN_RATING = 0
MAX_RATING = 5

_SEVERE = frozenset({"critical", "high"})


def _candidate_line(version: str) -> tuple[int, int]:
    """Return a valid schedule version's numeric line for sorting."""
    line = release_line(version)
    assert line is not None
    return line


def candidates(
    schedule: ReleaseSchedule, version: str | None, track: str | None = None
) -> list[str]:
    """
    The releases worth rehearsing, oldest first.

    The newest release of the installed line, when it is newer, and the
    newest release of every later line. With a declared ``track`` only the
    lines published on it count: a production instance is not rehearsed onto
    a rolling release it never signed up for.
    """
    installed = release_line(version)
    if installed is None:
        return []
    found = [
        entry.latest
        for key, entry in schedule.lines.items()
        if key >= installed
        and (not track or track in entry.tracks)
        and compare_versions(entry.latest, version) > 0
    ]
    return sorted(set(found), key=_candidate_line)


def _base_rating(
    *,
    end_of_life: bool,
    severities: Iterable[str],
    candidate: str,
    recommended: str | None,
) -> int:
    """The scanner's version rules, for a version that is not installed yet."""
    if end_of_life:
        return MIN_RATING
    matched = [severity.lower() for severity in severities]
    if matched:
        return 1 if _SEVERE.intersection(matched) else 2
    if recommended and compare_versions(candidate, recommended) < 0:
        if release_line(candidate) != release_line(recommended):
            return 3
        return 4
    return MAX_RATING


def rehearse(
    *,
    version: str | None,
    database: VulnerabilityDatabase,
    schedule: ReleaseSchedule,
    findings_ceiling: int = MAX_RATING,
    recommended: str | None = None,
    track: str | None = None,
    use_release_schedule: bool = True,
    today: date | None = None,
) -> list[dict[str, Any]]:
    """
    Simulate every candidate release; the ``upgradeRehearsal`` result key.

    ``findings_ceiling`` is the rating the instance's failed checks allow on
    their own - ``MAX_RATING`` when they do not affect the rating. Each entry
    names the ``version`` and its ``line``, the advisories it ``fixes``, the
    ones it is ``stillAffected`` by and any it ``introduces``, whether it is
    ``endOfLife``, and the ``rating`` it would reach alongside the
    ``versionRating`` its version alone would allow.
    """
    current = {advisory.id for advisory in database.matches(version)}
    rehearsed: list[dict[str, Any]] = []
    for candidate in candidates(schedule, version, track):
        matched = database.matches(candidate)
        ids = {advisory.id for advisory in matched}
        end_of_life = bool(
            use_release_schedule
            and schedule.status_for(candidate, today, track=track).eol
        )
        base = _base_rating(
            end_of_life=end_of_life,
            severities=(str(advisory.severity or "") for advisory in matched),
            candidate=candidate,
            recommended=recommended,
        )
        line = release_line(candidate)
        assert line is not None
        rehearsed.append(
            {
                "version": candidate,
                "line": f"{line[0]}.{line[1]}",
                "recommended": bool(recommended) and compare_versions(candidate, recommended) == 0,
                "fixes": sorted(current - ids),
                "stillAffected": sorted(current & ids),
                "introduces": sorted(ids - current),
                "endOfLife": end_of_life,
                "versionRating": base,
                "rating": max(MIN_RATING, min(base, findings_ceiling)),
            }
        )
    return rehearsed


__all__ = ["candidates", "rehearse"]
