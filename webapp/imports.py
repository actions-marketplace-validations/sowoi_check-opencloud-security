"""
Reading a scan report somebody uploads, without believing any of it.

Every other document this service compares came out of its own scanner a few
minutes earlier. This one arrives as a file from a stranger's disk, which
makes it the only untrusted *structure* in the application - elsewhere the
untrusted part is a string inside a document this service built.

So nothing here parses the upload into the thing it will use. It parses it
into a throwaway, and then *rebuilds* a result document from an allow-list:
the handful of keys :func:`opencloud_local_scan.baseline.snapshot_of` reads,
each one type-checked, length-capped and shape-checked on the way across. A
key nobody named below cannot reach the comparison, the template or Redis,
whatever the file contains - which is what makes "a hostile file" a question
about this module alone rather than about every surface downstream.

The two formats are the two this service hands out: the JSON of
``GET /api/scans/{uuid}`` and the CSV of ``.../export/csv``. Neither is
extended for the upload path; a report is read back through the same shape it
was written in.

What a format cannot carry is reported rather than guessed at. A CSV written
before this feature existed has no row for a pending update, and a comparison
that silently read its absence as "no update was available then" would invent
a regression the reader never had. :attr:`ImportedReport.carries` names the
facts the file actually recorded, and :func:`restrict_to` neutralises the rest
on *both* sides before they are compared.
"""

from __future__ import annotations

import csv
import io
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from opencloud_local_scan.coverage import COVERAGE_SCHEMA
from opencloud_local_scan.provenance import PROVENANCE_SCHEMA

#: The largest upload that is read at all. Deliberately far below the
#: 1 MiB `RequestBodyLimit` ceiling: a scan of one instance renders to a few
#: tens of kilobytes in either format, and everything above that is either a
#: different kind of file or somebody seeing how much work a parse can be made
#: to do.
MAX_UPLOAD_BYTES = 256 * 1024

#: Rows a CSV may have before it stops being a scan report. The export writes
#: one row per finding plus a header block; an instance with a thousand
#: findings does not exist.
MAX_CSV_ROWS = 2_000

#: How deep a JSON document may nest. `json.loads` defends its own recursion
#: with a C stack limit that raises before this matters for the parse - this
#: bounds the *walk* afterwards, which is ordinary Python.
MAX_JSON_DEPTH = 20

#: Entries a block may carry, and characters kept per string. Both are
#: generous for a real report and small enough that a crafted one cannot make
#: the comparison, the page or the cached document large.
#:
#: A block past the entry cap is *refused*, not truncated. Reading the first
#: five hundred findings of a longer list would answer the reader's question
#: from part of their evidence, and the part left out is exactly where the
#: finding that mattered would be: everything after it reads as resolved on
#: the earlier side and as introduced on the later one, with nothing on the
#: page able to say the file was only partly read. :data:`MAX_CSV_ROWS`
#: refuses a long file for the same reason.
MAX_ENTRIES = 500
MAX_TEXT = 300

#: What a finding identifier may look like. The scanner's own names, plus the
#: path a path-exposure check carries (`exposed:/opencloud.yaml`) and the
#: punctuation an advisory identifier uses. Anything else is not a name this
#: service ever wrote, so it is dropped rather than repaired: a half-repaired
#: identifier would compare unequal to the real one and read as a finding that
#: appeared or disappeared on its own.
_IDENTIFIER = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9 ._:/@+-]{0,119}\Z")
#: A digest this project wrote: 64 hex characters, or the "none" it
#: records when there was no reference data at all.
_DIGEST = re.compile(r"\A(?:[0-9a-f]{64}|none)\Z")

#: Severities the scanner writes. An upload claiming any other is recorded
#: with none, because severity reaches a template as a CSS attribute.
_SEVERITIES = frozenset({"critical", "high", "warning", "medium", "low", "info", "hardening", "header"})

#: The two facts a report can fail to record, named so that a comparison can
#: leave them out rather than guess at them.
#:
#: Failed checks, missing hardenings and advisories are not here, because both
#: formats have always carried all three - a row per finding is what the CSV
#: table *is*. These two are different: each is a single measurement that
#: lives outside that table, so an export written before it was added is
#: silent about it, and silence is not the same answer as "no".
RECORDS_UPDATES = "update"
RECORDS_HTTPS_ENFORCEMENT = "httpsEnforced"
ALL_RECORDS = frozenset({RECORDS_UPDATES, RECORDS_HTTPS_ENFORCEMENT})

#: The CSV section labels, as `reports.csv_report` writes them.
_SECTION_CHECK = "failed check"
_SECTION_HARDENING = "missing hardening"
_SECTION_HEADER = "missing header"
_SECTION_WAIVED = "waived"
_SECTION_UNFIXABLE = "not actionable"
_SECTION_ADVISORY = "advisory"

#: The header rows the CSV export writes before the findings, and the document
#: key each one is read back into.
_CSV_HEADER_FIELDS = {
    "instance": "domain",
    "product": "product",
    "version": "version",
    "release track": "releaseType",
    "end of life": "EOL",
    "rating": "rating",
    "scanned at": "scannedAt",
    "update available": "updates",
    "https enforced": "httpsEnforced",
}


class ReportRejected(Exception):
    """
    An upload that is not a scan report this service can read.

    ``key`` names the sentence the reader is shown. The message is English and
    is for a log; nothing in it repeats any part of the uploaded file, because
    an error page is the one place a hostile upload would most like to have
    its own text rendered.
    """

    def __init__(self, message: str, *, key: str, status: int = 422) -> None:
        super().__init__(message)
        self.key = key
        self.status = status


@dataclass(frozen=True)
class ImportedReport:
    """One uploaded report, rebuilt as a result document this service wrote."""

    document: dict[str, Any]
    """The allow-listed rebuild. Nothing from the upload is in here that is
    not named in :func:`_rebuild`."""

    source_format: str
    """``json`` or ``csv``, decided by looking at the bytes rather than at the
    file name - a name is chosen by whoever uploaded it and is never read."""

    carries: frozenset[str] = field(default_factory=lambda: ALL_RECORDS)
    """The facts of :data:`ALL_RECORDS` this file actually recorded."""

    dropped: int = 0
    """Entries left out because their identifier was not one this service
    writes, or because they were not the shape their block is written in.
    Reported rather than swallowed: a comparison drawn from a file that was
    partly unreadable is a comparison the reader should know about. A file
    whose blocks are too long to read at all is refused instead, because that
    is a hole the count could not describe - see :data:`MAX_ENTRIES`."""

    @property
    def missing_records(self) -> tuple[str, ...]:
        """The facts this file never recorded, in a stable order."""
        return tuple(sorted(ALL_RECORDS - self.carries))


def parse_report(raw: bytes) -> ImportedReport:
    """
    Turn uploaded bytes into a result document, or refuse them.

    The order is deliberate: size, then encoding, then format, then content.
    Each step is cheaper than the one after it, so the expensive parse only
    ever runs on something that already looks like a report.
    """
    if not raw:
        raise ReportRejected("The upload is empty.", key="compare.upload.error.empty")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise ReportRejected(
            f"The upload is larger than {MAX_UPLOAD_BYTES} bytes.",
            key="compare.upload.error.too_large",
            status=413,
        )
    text = _decode(raw)
    if text.lstrip().startswith(("{", "[")):
        return _from_json(text)
    return _from_csv(text)


def _decode(raw: bytes) -> str:
    """
    The upload as text, or a refusal.

    Strict UTF-8, because both formats this service writes are UTF-8 and a
    lenient decode would invent characters that were never in the file. A NUL
    byte is refused separately: it is legal in neither format, and it is how a
    parser is talked past a check that stopped at it.
    """
    if b"\x00" in raw:
        raise ReportRejected(
            "The upload contains NUL bytes.", key="compare.upload.error.unreadable"
        )
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ReportRejected(
            "The upload is not UTF-8 text.", key="compare.upload.error.unreadable"
        ) from None
    return text


def _from_json(text: str) -> ImportedReport:
    """The JSON of a result page or of the API, read back."""
    try:
        payload = json.loads(text)
    except (ValueError, RecursionError):
        raise ReportRejected(
            "The upload is not valid JSON.", key="compare.upload.error.unreadable"
        ) from None
    if not isinstance(payload, Mapping):
        raise ReportRejected(
            "The JSON is not an object.", key="compare.upload.error.not_a_report"
        )
    _refuse_deep(payload)
    # `GET /api/scans/{uuid}` wraps the document; a download of the result
    # itself is the document. Both are things a reader plausibly has.
    inner = payload.get("result")
    document = inner if isinstance(inner, Mapping) else payload
    if not _looks_like_a_report(document):
        raise ReportRejected(
            "The JSON does not look like a scan result.",
            key="compare.upload.error.not_a_report",
        )
    rebuilt, dropped = _rebuild(document)
    return ImportedReport(document=rebuilt, source_format="json", dropped=dropped)


def _refuse_deep(value: Any, depth: int = 0) -> None:
    """Refuse a document nested deeper than any real result document is."""
    if depth > MAX_JSON_DEPTH:
        raise ReportRejected(
            "The JSON nests too deeply.", key="compare.upload.error.unreadable"
        )
    if isinstance(value, Mapping):
        for item in value.values():
            _refuse_deep(item, depth + 1)
    elif isinstance(value, list):
        for item in value[:MAX_ENTRIES]:
            _refuse_deep(item, depth + 1)


def _looks_like_a_report(document: Mapping[str, Any]) -> bool:
    """
    Whether this object is a scan result at all.

    Not a schema check - a rebuild tolerates a missing key everywhere - but
    the difference between "your file is not a scan report" and a comparison
    against an empty document, which would read as every finding resolved.
    """
    return any(
        key in document
        for key in ("rating", "extraChecks", "hardenings", "ratingExplanation")
    )


def _from_csv(text: str) -> ImportedReport:
    """The CSV export, read back through the shape it was written in."""
    rows: list[list[str]] = []
    try:
        for index, row in enumerate(csv.reader(io.StringIO(text, newline=""))):
            if index >= MAX_CSV_ROWS:
                raise ReportRejected(
                    f"The CSV has more than {MAX_CSV_ROWS} rows.",
                    key="compare.upload.error.too_large",
                    status=413,
                )
            rows.append([_uncell(cell) for cell in row[:8]])
    except csv.Error:
        raise ReportRejected(
            "The upload is not valid CSV.", key="compare.upload.error.unreadable"
        ) from None

    document, recorded = _csv_header(rows)
    document, dropped = _csv_findings(rows, document)
    if not _looks_like_a_report(document):
        raise ReportRejected(
            "The CSV does not look like a scan report.",
            key="compare.upload.error.not_a_report",
        )
    # An export written before these rows existed cannot say what they say,
    # and "absent" must not be read as "no".
    carries = frozenset(recorded)
    rebuilt, more_dropped = _rebuild(document)
    return ImportedReport(
        document=rebuilt,
        source_format="csv",
        carries=carries,
        dropped=dropped + more_dropped,
    )


def _uncell(value: str) -> str:
    """
    Undo the export's spreadsheet guard.

    `reports._cell` prefixes an apostrophe to anything a spreadsheet would
    evaluate as a formula. Reading it back leaves the value as it was
    measured, so a finding survives the round trip under its own name.
    """
    text = value[:MAX_TEXT * 2]
    if text.startswith("'") and text[1:2] in {"=", "+", "-", "@"}:
        return text[1:]
    return text


def _csv_header(rows: list[list[str]]) -> tuple[dict[str, Any], set[str]]:
    """
    The label/value block the export writes before the findings.

    Returns what it read, and which of :data:`ALL_RECORDS` the file turned out
    to record at all.
    """
    document: dict[str, Any] = {}
    recorded: set[str] = set()
    for row in rows:
        if not row:
            continue
        label = row[0].strip().lower()
        if label == "section":
            # The findings table starts here; everything after it is a row,
            # not a fact.
            break
        key = _CSV_HEADER_FIELDS.get(label)
        if key is None:
            continue
        value = row[1].strip() if len(row) > 1 else ""
        if key == "EOL":
            document["EOL"] = value.lower() in {"yes", "true", "1"}
        elif key == "rating":
            document["rating"] = value
        elif key == "scannedAt":
            document["scannedAt"] = {"date": value}
        elif key == "updates":
            recorded.add(RECORDS_UPDATES)
            available = value.lower() not in {"", "no", "none", "false"}
            document["updates"] = (
                {"available": True, "availableVersion": value} if available else {}
            )
        elif key == "httpsEnforced":
            recorded.add(RECORDS_HTTPS_ENFORCEMENT)
            document.setdefault("setup", {})["https"] = {
                "enforced": value.lower() not in {"no", "false", "0"}
            }
        else:
            document[key] = value
    return document, recorded


def _csv_findings(
    rows: list[list[str]], document: dict[str, Any]
) -> tuple[dict[str, Any], int]:
    """
    The findings table, read back into the blocks `snapshot_of` looks in.

    A row's section says which block it came from, which is why the export
    writes one: without it a sorted spreadsheet is a list of identifiers with
    no way to tell a missing header from a failed check, and the two are
    counted differently.
    """
    checks: list[dict[str, Any]] = []
    hardenings: dict[str, bool] = {}
    headers: dict[str, bool] = {}
    vulnerabilities: list[dict[str, Any]] = []
    waived: list[str] = []
    dropped = 0
    started = False

    for row in rows:
        if not row:
            continue
        section = row[0].strip().lower()
        if section == "section":
            started = True
            continue
        if not started or section not in {
            _SECTION_CHECK,
            _SECTION_HARDENING,
            _SECTION_HEADER,
            _SECTION_WAIVED,
            _SECTION_UNFIXABLE,
            _SECTION_ADVISORY,
        }:
            continue
        identifier = (row[1].strip() if len(row) > 1 else "")
        severity = (row[2].strip().lower() if len(row) > 2 else "")
        if not _IDENTIFIER.match(identifier):
            dropped += 1
            continue
        if section == _SECTION_CHECK:
            checks.append(
                {"id": identifier, "severity": severity, "passed": False}
            )
        elif section == _SECTION_HARDENING:
            hardenings[identifier] = False
        elif section == _SECTION_HEADER:
            headers[identifier] = False
        elif section == _SECTION_UNFIXABLE:
            # Kept so the rebuild matches the instance that was measured. The
            # baseline drops these itself, because they cannot be acted on.
            hardenings[identifier] = False
        elif section == _SECTION_WAIVED:
            checks.append(
                {"id": identifier, "severity": severity, "passed": False, "ignored": True}
            )
            waived.append(identifier)
        elif section == _SECTION_ADVISORY:
            vulnerabilities.append({"id": identifier, "severity": severity})

    if checks:
        document["extraChecks"] = checks
    if hardenings:
        document["hardenings"] = hardenings
    if headers:
        document.setdefault("setup", {})["headers"] = headers
    if vulnerabilities:
        document["vulnerabilities"] = vulnerabilities
    if waived:
        document["ignored"] = waived
    return document, dropped


def _provenance(source: Mapping[str, Any]) -> dict[str, Any]:
    """
    The conditions the uploaded scan ran under, if it recorded them.

    Only the fields a comparison reads, each one retyped. A digest is checked
    against its own shape rather than trusted: it reaches a comparison, and a
    comparison renders it.
    """
    block = source.get("provenance")
    if not isinstance(block, Mapping) or "schema" not in block:
        return {}
    advisory = block.get("advisoryData")
    schedule = block.get("scheduleData")
    waivers = block.get("waivers")
    rebuilt: dict[str, Any] = {
        "schema": PROVENANCE_SCHEMA,
        "scannerVersion": _text(block.get("scannerVersion"))[:32],
        "scannedAt": _text(block.get("scannedAt"))[:64],
        "releaseTrack": _text(block.get("releaseTrack"))[:32],
        "advisoryData": {
            "digest": _digest(advisory.get("digest") if isinstance(advisory, Mapping) else None),
            "count": _count(advisory.get("count") if isinstance(advisory, Mapping) else None),
        },
        "scheduleData": {
            "digest": _digest(schedule.get("digest") if isinstance(schedule, Mapping) else None),
            "updated": _text(schedule.get("updated") if isinstance(schedule, Mapping) else "")[:32]
            or None,
        },
        "waivers": {
            state: _patterns(waivers.get(state) if isinstance(waivers, Mapping) else None)
            for state in ("active", "expired")
        },
    }
    return {"provenance": rebuilt}


def _coverage(source: Mapping[str, Any]) -> dict[str, Any]:
    """How much of the uploaded scan reached a conclusion, if it said."""
    block = source.get("coverage")
    if not isinstance(block, Mapping) or not isinstance(block.get("checks"), list):
        return {}
    counts = block.get("counts")
    if not isinstance(counts, Mapping):
        return {}
    return {
        "coverage": {
            "schema": COVERAGE_SCHEMA,
            "counts": {
                state: _count(counts.get(state))
                for state in ("passed", "failed", "not_checked", "inconclusive", "total")
            },
            # The detail is not rebuilt: nothing in a comparison reads an
            # individual entry, and an allow-list that copies a list of
            # arbitrary objects is not an allow-list.
            "checks": [],
        }
    }


def _digest(value: object) -> str:
    """A digest, or nothing. Anything that is not one of ours is dropped."""
    text = _text(value)
    return text if _DIGEST.match(text) else ""


def _count(value: object) -> int:
    """A non-negative count, clamped away from anything a template cannot print."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return 0
    return max(0, min(int(value), 100_000))


def _patterns(value: object) -> list[str]:
    """Waiver patterns from an upload, bounded in count and in length."""
    if not isinstance(value, list):
        return []
    return [_text(item)[:128] for item in value[:64] if _text(item)]


def _rebuild(source: Mapping[str, Any]) -> tuple[dict[str, Any], int]:
    """
    A result document built from an allow-list, and nothing else.

    This is the boundary. Whatever the upload was - a result document, a CSV
    already read into one, or something wearing the shape of either - what
    leaves here is a dictionary this module assembled key by key. A field that
    is not named below does not exist downstream, so a comparison, a template
    and a cached document cannot be reached by one that was never expected.
    """
    dropped = 0
    document: dict[str, Any] = {
        "domain": _text(source.get("domain")),
        "product": _text(source.get("product")),
        "version": _text(source.get("version")),
        "releaseType": _text(source.get("releaseType")),
        "rating": _rating(source.get("rating")),
        "EOL": bool(source.get("EOL")),
        "scannedAt": {"date": _scanned_at(source.get("scannedAt"))},
    }

    checks: list[dict[str, Any]] = []
    entries, unreadable = _entries(source.get("extraChecks"))
    dropped += unreadable
    for entry in entries:
        identifier = _text(entry.get("id"))
        if not _IDENTIFIER.match(identifier):
            dropped += 1
            continue
        checks.append(
            {
                "id": identifier,
                "severity": _severity(entry.get("severity")),
                "passed": bool(entry.get("passed")),
                "ignored": bool(entry.get("ignored")),
            }
        )
    document["extraChecks"] = checks

    vulnerabilities: list[dict[str, Any]] = []
    entries, unreadable = _entries(source.get("vulnerabilities"))
    dropped += unreadable
    for entry in entries:
        identifier = _text(entry.get("id") or entry.get("cve") or entry.get("title"))
        if not _IDENTIFIER.match(identifier):
            dropped += 1
            continue
        vulnerabilities.append(
            {"id": identifier, "severity": _severity(entry.get("severity"))}
        )
    document["vulnerabilities"] = vulnerabilities

    hardenings, hardening_dropped = _flags(source.get("hardenings"))
    document["hardenings"] = hardenings
    dropped += hardening_dropped

    setup = source.get("setup")
    headers, header_dropped = _flags(
        setup.get("headers") if isinstance(setup, Mapping) else None
    )
    dropped += header_dropped
    https = setup.get("https") if isinstance(setup, Mapping) else None
    document["setup"] = {
        "headers": headers,
        "https": {
            "enforced": bool(https.get("enforced"))
            if isinstance(https, Mapping) and "enforced" in https
            # Absent means the report never said, and the baseline reads a
            # missing `enforced` as enforced. Matching that keeps an upload
            # from inventing an httpsEnforced finding on either side.
            else True
        },
    }

    # The two blocks a comparison explains itself with, rebuilt key by key
    # like everything else here. An upload that carries neither is a report
    # that cannot say what it was judged against, which the explanation
    # reports as a limitation rather than guessing at.
    document.update(_provenance(source))
    document.update(_coverage(source))

    updates = source.get("updates")
    if isinstance(updates, Mapping) and updates.get("available"):
        document["updates"] = {
            "available": True,
            "availableVersion": _text(updates.get("availableVersion")) or "unknown",
        }
    else:
        document["updates"] = {}

    waived: list[str] = []
    names, _ = _entries(source.get("ignored"), mappings_only=False)
    for name in names:
        text = _text(name)
        if _IDENTIFIER.match(text):
            waived.append(text)
        else:
            dropped += 1
    document["ignored"] = waived

    return document, dropped


def _too_many(count: int) -> None:
    """Refuse a block no report this service wrote could have."""
    if count > MAX_ENTRIES:
        raise ReportRejected(
            f"A block of the report carries more than {MAX_ENTRIES} entries.",
            key="compare.upload.error.not_a_report",
        )


def _entries(value: Any, *, mappings_only: bool = True) -> tuple[list[Any], int]:
    """
    The items of one list, and how many of them could not be read.

    An entry that is not the shape its block is written in carries no
    identifier at all, so it is counted rather than passed over in silence -
    the same rule an identifier this scanner never writes meets below.
    """
    if not isinstance(value, list):
        return [], 0
    _too_many(len(value))
    if not mappings_only:
        return list(value), 0
    kept = [item for item in value if isinstance(item, Mapping)]
    return kept, len(value) - len(kept)


def _flags(value: Any) -> tuple[dict[str, bool], int]:
    """A block of ``name: bool`` measurements, names checked and count capped."""
    if not isinstance(value, Mapping):
        return {}, 0
    _too_many(len(value))
    flags: dict[str, bool] = {}
    dropped = 0
    for name, enabled in value.items():
        text = _text(name)
        if not _IDENTIFIER.match(text):
            dropped += 1
            continue
        flags[text] = bool(enabled)
    return flags, dropped


def _text(value: Any) -> str:
    """
    One string from the upload, flattened and capped.

    The same treatment `workflows._safe_text` gives a string a scanned host
    chose, for the same reason and one step earlier: the line structure goes,
    because that is what an injected instruction needs to look like a message,
    and the length goes, because a cached document is rendered into a page.
    """
    if value is None or isinstance(value, (Mapping, list)):
        return ""
    text = " ".join(str(value).split())
    text = "".join(character for character in text if character.isprintable())
    return text[:MAX_TEXT]


def _severity(value: Any) -> str:
    """A severity the scanner writes, or none. This reaches a CSS attribute."""
    text = _text(value).lower()
    return text if text in _SEVERITIES else ""


def _rating(value: Any) -> int | None:
    """
    The 0-5 grade, or ``None`` where the report did not carry one.

    Read through :func:`_text`, so the grade is capped like every other string
    that crosses this boundary. ``int`` on a quarter of a megabyte of digits
    is work chosen by whoever wrote the file - quadratic before 3.12 - and the
    interpreter's own digit limit that would otherwise refuse it is a default
    an operator can turn off. A grade is one character, so there is nothing to
    lose by not relying on either.
    """
    try:
        rating = int(_text(value))
    except (TypeError, ValueError):
        return None
    return rating if 0 <= rating <= 5 else None


def _scanned_at(value: Any) -> str:
    """When the uploaded report says it was taken, as a flat string."""
    if isinstance(value, Mapping):
        return _text(value.get("date") or value.get("iso"))
    return _text(value)


def restrict_to(document: Mapping[str, Any], carries: frozenset[str]) -> dict[str, Any]:
    """
    A copy of a document with the facts an upload never recorded neutralised.

    Applied to *both* sides or to neither. A file that never recorded whether
    an update was pending is not evidence that none was, so the honest
    comparison is the one that does not mention updates at all - and
    neutralising the fact on one side only would turn a gap in the file into a
    finding that appeared out of nowhere.

    Each missing fact is set to the value that yields no finding, which is
    what a document that never mentioned it would have produced anyway.

    This is not a judgement about the instance: it removes an input from the
    arithmetic, it does not decide what the arithmetic makes of what is left.
    """
    missing = ALL_RECORDS - carries
    if not missing:
        return dict(document)
    restricted = dict(document)
    if RECORDS_UPDATES in missing:
        restricted["updates"] = {}
    if RECORDS_HTTPS_ENFORCEMENT in missing:
        setup = dict(restricted.get("setup") or {})
        setup["https"] = {**(setup.get("https") or {}), "enforced": True}
        restricted["setup"] = setup
    return restricted
