#!/usr/bin/env python3
"""
Regenerate the golden corpus in ``tests/golden/``.

The corpus freezes the verdict a handful of fake instances earn, so that a
change to the catalogue, a severity or a threshold cannot re-grade every
instance in the world without somebody seeing it. ``tests/golden_corpus.py``
describes the instances and what is remembered about them; this script scans
them and writes the files the test compares against.

    python scripts/update_golden_corpus.py            # rewrite the corpus
    python scripts/update_golden_corpus.py --check    # fail if it is stale

Regenerating is a decision, not a fix: a diff means the judgement changed,
and that belongs in ``CHANGELOG.md`` before the file is rewritten.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.golden_corpus import CASES, record

CORPUS = ROOT / "tests" / "golden"


def _written(verdict: dict[str, object]) -> str:
    """One case, formatted the way the file on disk is."""
    return json.dumps(verdict, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report a stale corpus instead of rewriting it.",
    )
    args = parser.parse_args(argv)

    CORPUS.mkdir(parents=True, exist_ok=True)
    stale: list[str] = []
    for name in CASES:
        path = CORPUS / f"{name}.json"
        content = _written(record(name))
        if args.check:
            current = path.read_text(encoding="utf-8") if path.exists() else ""
            if current != content:
                stale.append(name)
            continue
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")

    # A file for a case nobody describes any more is a verdict nothing
    # replays, which is worse than no file at all.
    orphaned = sorted(
        path.stem for path in CORPUS.glob("*.json") if path.stem not in CASES
    )
    if args.check:
        if stale or orphaned:
            for name in stale:
                print(f"stale: {name}", file=sys.stderr)
            for name in orphaned:
                print(f"orphaned: {name}", file=sys.stderr)
            print(
                "The golden corpus no longer matches what the scan produces. "
                "If the change to the judgement was intended, run "
                "python scripts/update_golden_corpus.py and say so in "
                "CHANGELOG.md.",
                file=sys.stderr,
            )
            return 1
        print(f"The golden corpus is current ({len(CASES)} cases).")
        return 0

    for name in orphaned:
        (CORPUS / f"{name}.json").unlink()
        print(f"removed tests/golden/{name}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
