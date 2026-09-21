"""
The golden corpus: a frozen set of instances and the verdicts they earn.

Every other test in this suite asserts one property of one change. Nothing
asserts that the *whole* judgement stays the same, and that is the failure
this exists for: a hardening measure added to the catalogue, a severity
raised, a threshold moved, and suddenly every instance in the world is graded
differently - correctly, according to each individual test, and silently.

So a handful of instances are described here once, scanned for real against
``tests/fake_opencloud.py``, and the verdict each one earns is written to
``tests/golden/<case>.json``. The test replays them and compares. A diff is
not a failure: it is the question "did you mean to re-grade every instance
that looks like this?", and the answer is either a fix or a regenerated file
and a changelog entry.

Two rules keep the answer stable over time:

- **The reference data is pinned here**, not read from the bundled files. The
  release schedule and the advisory database refresh themselves (ADR 0016,
  ADR 0017), and a corpus that moved every time OpenCloud published a release
  would be a weekly chore instead of a signal.
- **Nothing derived from the clock or the host is recorded.** No timestamp,
  no duration, no address, no port - only the identifiers, the ratings and
  the exit codes, which is what the corpus is about.
"""

from __future__ import annotations

from typing import Any

import check_opencloud_security as plugin
from check_opencloud_security import NagiosExitCode, ScanContext
from opencloud_local_scan import failed_extra_checks
from opencloud_local_scan.releases import ReleaseSettings
from opencloud_local_scan.scanner import ScannerSettings, scan
from opencloud_local_scan.versions import schedule_from_document
from opencloud_local_scan.vulndb import VulnerabilityDatabase, parse_document
from tests.fake_opencloud import STATUS_PAYLOAD, FakeOpenCloud, InstanceBehaviour

# The fake instance runs 7.2.3. 7.2 is the current production line here, so a
# stock instance is one patch behind and nothing in this corpus depends on
# what OpenCloud released this month.
SCHEDULE = schedule_from_document(
    {
        "lifetime_days": {"rolling": 21, "production": 183, "lts": 730},
        "lines": [
            {
                "line": "7.2",
                "tracks": ["production", "rolling"],
                "released": "2026-06-25",
                "latest": "7.2.4",
            },
            {
                "line": "7.3",
                "tracks": ["rolling"],
                "released": "2026-07-14",
                "latest": "7.3.0",
            },
        ],
    }
)

# One advisory, affecting a line no case runs except the one that is meant
# to, so that the corpus covers a rated vulnerability without every other
# case being graded by it.
DATABASE = VulnerabilityDatabase(
    parse_document(
        {
            "advisories": [
                {
                    "id": "GOLDEN-0001",
                    "severity": "high",
                    "introduced": "7.0.0",
                    "fixed": "7.1.0",
                    "summary": "A finding used only by the golden corpus.",
                }
            ]
        }
    ),
    ["golden"],
)


def _running(version: str) -> dict[str, Any]:
    """The status document of an instance running ``version``."""
    payload = dict(STATUS_PAYLOAD)
    payload["productversion"] = version
    return payload


SETTINGS = ScannerSettings(
    scheme="http",
    timeout=3,
    check_debug_ports=False,
    include_bundled_db=False,
    release_schedule=SCHEDULE,
)
NO_UPDATES = ReleaseSettings(mode="off")


# The instances, each one a shape somebody actually runs. Adding a case is
# cheap and welcome; changing one is changing what the corpus protects.
CASES: dict[str, tuple[str, InstanceBehaviour]] = {
    "default": (
        "OpenCloud behind its own proxy, configured the way it ships.",
        InstanceBehaviour(),
    ),
    "directory_listing": (
        "A proxy serving an Apache-style index of the document root.",
        InstanceBehaviour(directory_listing=True),
    ),
    "unprotected_endpoints": (
        "Endpoints that must ask for credentials answering with a body.",
        InstanceBehaviour(unprotected=True),
    ),
    "demo_users": (
        "An instance left with the documented demo accounts enabled.",
        InstanceBehaviour(demo_users=True),
    ),
    "server_disclosed": (
        "A proxy naming its backend in Server and X-Powered-By.",
        InstanceBehaviour(disclose_server="nginx/1.27.0"),
    ),
    "basic_auth": (
        "PROXY_ENABLE_BASIC_AUTH=true, so the browser is offered Basic.",
        InstanceBehaviour(basic_auth=True),
    ),
    "outdated_release": (
        "An instance on an older line, which an advisory also names.",
        InstanceBehaviour(status_payload=_running("7.0.5")),
    ),
}

# The profiles a verdict is recorded under, plus the plugin's own defaults.
# A corpus that recorded one set of thresholds would not notice a profile
# being redefined, which is exactly the kind of silent re-grade it is for.
THRESHOLDS: dict[str, tuple[int, int]] = {
    "default": (plugin.DEFAULT_WARNING_RATING, plugin.DEFAULT_CRITICAL_RATING),
    **{
        name: (int(values["warning"]), int(values["critical"]))  # type: ignore[call-overload]
        for name, values in plugin.PROFILES.items()
    },
}


def scan_case(behaviour: InstanceBehaviour) -> dict[str, Any]:
    """Scan one fake instance against the pinned reference data."""
    with FakeOpenCloud(behaviour) as instance:
        return scan(
            instance.host,
            settings=SETTINGS,
            release_settings=NO_UPDATES,
            database=DATABASE,
        )


def _flags(mapping: object) -> list[str]:
    """The names in a pass/fail mapping that did not pass, in order."""
    if not isinstance(mapping, dict):
        return []
    return sorted(name for name, passed in mapping.items() if not passed)


def verdict(name: str, result: dict[str, Any]) -> dict[str, Any]:
    """
    Everything about a scan the corpus remembers.

    Identifiers and numbers only: what failed, what the rating was and why,
    and which exit code each threshold set turns it into.
    """
    setup = result.get("setup") or {}
    rating = plugin._rating_of(result)
    vulnerabilities = result.get("vulnerabilities") or []
    explanation = result.get("ratingExplanation") or {}
    exit_codes = {}
    for threshold, (warning, critical) in sorted(THRESHOLDS.items()):
        context = ScanContext(
            host="opencloud.example.com",
            warning_rating=warning,
            critical_rating=critical,
        )
        _, code = plugin._evaluate_rating(context, result, rating, len(vulnerabilities))
        exit_codes[threshold] = NagiosExitCode(code).name

    return {
        "case": name,
        "description": CASES[name][0],
        "rating": rating,
        "grade": plugin.RATE_MAP.get(rating, "?"),
        "endOfLife": bool(result.get("EOL")),
        "advisories": sorted(
            str(item.get("id")) for item in vulnerabilities if isinstance(item, dict)
        ),
        "failedChecks": sorted(failed_extra_checks(result)),
        "missingHardenings": _flags(result.get("hardenings")),
        "missingHeaders": _flags(setup.get("headers")),
        "ratingBase": (explanation.get("base") or {}).get("rating"),
        "ratingCaps": sorted(
            f"{cap.get('check')}:{cap.get('severity')}:{cap.get('cap')}"
            for cap in explanation.get("caps") or ()
            if isinstance(cap, dict) and cap.get("applied")
        ),
        "exitCodes": exit_codes,
    }


def record(name: str) -> dict[str, Any]:
    """Scan the named case and return the verdict to freeze."""
    return verdict(name, scan_case(CASES[name][1]))
