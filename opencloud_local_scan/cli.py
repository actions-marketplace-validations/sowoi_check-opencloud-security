# PYTHON_ARGCOMPLETE_OK
"""
Command line entry point of the bundled scanner.

``check-opencloud-scanner`` has two sub-commands:

``scan``
    Scan one or more hosts and print the result documents as JSON. Useful
    for ad-hoc inspection and for cron jobs that archive scan results.

``serve``
    Run the HTTP scan service. The plugin never talks to it - it always scans
    in process - but the service lets several consumers share one cached
    result, or lets scans run from a host closer to the instance.

``diff``
    Compare two result documents that were archived earlier and say what
    changed between them. The plugin's ``--baseline`` spends the same
    comparison on staying quiet; this spends it on telling somebody what
    happened, which is the question after a change rather than during one.

``explain``
    Look one finding identifier up in the catalogue without scanning
    anything. A monitoring system prints ``cspWithoutUnsafeInline`` at three
    in the morning; until now the three ways to find out what that meant were
    to run a scan that fails the same check, open the web application, or read
    the source.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections.abc import Sequence
from dataclasses import replace
from difflib import get_close_matches
from pathlib import Path
from typing import Any

from .baseline import Baseline, Comparison, Snapshot, snapshot_of
from .changes import CATEGORIES as CHANGE_CATEGORIES
from .changes import explain
from .completion import enable as enable_completion
from .config import ConfigurationError, load_configuration
from .factory import release_settings_from_config, scanner_settings_from_config
from .findings import ADVISORY_CATEGORY, Delta, severity_totals
from .findings import CATEGORIES as FINDING_CATEGORIES
from .findings import compare as compare_findings
from .hardening import (
    CATEGORIES,
    Hardening,
    all_checks,
    catalogue_id,
    describe,
    header_names,
)
from .refresh_data import RefreshError, refresh_data
from .scanner import ScanError, scan
from .service import (
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_LISTEN,
    DEFAULT_PORT,
    ScanStore,
    ServiceMisconfigured,
    serve,
)
from .wizard import run as run_setup

LOGGER = logging.getLogger("check_opencloud.cli")


def build_arg_parser() -> argparse.ArgumentParser:
    """Create the argument parser for ``check-opencloud-scanner``."""
    parser = argparse.ArgumentParser(
        prog="check-opencloud-scanner",
        description=(
            "Scan OpenCloud instances and print the result as JSON, or run the "
            "scan service that shares one cached result between several "
            "monitoring consumers."
        ),
    )
    parser.add_argument("-c", "--config", help="Path to a configuration file.")
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase log verbosity."
    )

    sub = parser.add_subparsers(dest="command", required=True)

    scan_parser = sub.add_parser("scan", help="Scan hosts and print JSON results.")
    scan_parser.add_argument("hosts", nargs="+", help="Hostnames or URLs to scan.")
    scan_parser.add_argument(
        "--timeout", type=int, help="HTTP timeout per request in seconds."
    )
    scan_parser.add_argument(
        "--insecure",
        dest="verify_tls",
        action="store_false",
        default=None,
        help="Do not verify TLS certificates (OpenCloud self-signs by default).",
    )
    scan_parser.add_argument(
        "--ca-file", help="PEM CA bundle used to verify an internal TLS certificate."
    )
    scan_parser.add_argument(
        "--no-extra-checks",
        dest="extra_checks",
        action="store_false",
        default=None,
        help="Only check product, version and headers.",
    )
    scan_parser.add_argument(
        "--no-debug-ports",
        dest="check_debug_ports",
        action="store_false",
        default=None,
        help="Skip probing the OpenCloud debug ports.",
    )
    scan_parser.add_argument(
        "--login-throttling",
        dest="check_login_throttling",
        action="store_true",
        default=None,
        help=(
            "Send a few failed sign-ins for an account that cannot exist to the "
            "built-in identity provider and record whether they were throttled. "
            "Never graded."
        ),
    )
    scan_parser.add_argument(
        "--all-addresses",
        dest="check_all_addresses",
        action="store_true",
        default=None,
        help=(
            "Repeat the version, header, hardening and demo-account checks "
            "against every address the name resolves to, and report when "
            "they disagree."
        ),
    )
    scan_parser.add_argument("--port", type=int, help="Override the target port.")
    scan_parser.add_argument(
        "--concurrency",
        type=int,
        help="Number of probes to run in parallel (default 1, no multithreading).",
    )
    scan_parser.add_argument(
        "--scheme", choices=("https", "http"), help="Scheme used to reach the instance."
    )
    scan_parser.add_argument(
        "--no-update-check",
        action="store_true",
        help="Do not look up the newest OpenCloud release.",
    )
    scan_parser.add_argument(
        "--compact", action="store_true", help="Print compact instead of indented JSON."
    )

    serve_parser = sub.add_parser("serve", help="Run the HTTP scan service.")
    serve_parser.add_argument(
        "--listen",
        help=(
            f"Bind address (default {DEFAULT_LISTEN}). Anything but loopback "
            "requires --token."
        ),
    )
    serve_parser.add_argument("--port", type=int, help=f"Port (default {DEFAULT_PORT}).")
    serve_parser.add_argument(
        "--cache-ttl", type=int, help="Seconds a scan result is reused."
    )
    serve_parser.add_argument("--token", help="Require this token on API requests.")
    serve_parser.add_argument(
        "--concurrency",
        type=int,
        help="Number of probes to run in parallel per scan (default 1).",
    )
    serve_parser.add_argument(
        "--insecure",
        dest="verify_tls",
        action="store_false",
        default=None,
        help="Do not verify TLS certificates of scanned instances.",
    )

    configure_parser = sub.add_parser(
        "configure",
        help="Ask for the settings interactively and save them as JSON.",
    )
    configure_parser.add_argument(
        "--all",
        dest="include_optional",
        action="store_true",
        default=None,
        help="Go through the optional settings without asking first.",
    )
    configure_parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing file without confirming.",
    )
    configure_parser.add_argument(
        "--no-test-scan",
        dest="verify",
        action="store_false",
        default=None,
        help="Do not offer a test scan of the host before saving.",
    )
    configure_parser.add_argument(
        "--export-monitoring",
        dest="export",
        choices=("icinga", "systemd", "both", "none"),
        default=None,
        help=(
            "Also write the scheduled check next to the configuration: an "
            "Icinga 2 Service object, a systemd service and timer, or both. "
            "The files carry the thresholds and release track just answered "
            "and are written for review - nothing is installed or reloaded. "
            "Credentials stay in the configuration file. The default asks."
        ),
    )
    refresh_parser = sub.add_parser(
        "refresh-data",
        help="Fetch validated release and advisory data for a monitoring host.",
    )
    refresh_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("~/.cache/check-opencloud-security").expanduser(),
        help="Directory for the two JSON cache files.",
    )
    refresh_parser.add_argument(
        "--schedule-url",
        help=(
            "Lifecycle page or mirror URL. Without it, the reviewed schedule "
            "is read from this project's repository and its signature "
            "verified; an explicit URL is fetched live and unverified."
        ),
    )
    refresh_parser.add_argument(
        "--advisory-url",
        help=(
            "OSV query endpoint or mirror URL. Without it, the reviewed "
            "advisory database is read from this project's repository and "
            "its signature verified; an explicit URL is fetched live and "
            "unverified."
        ),
    )
    refresh_parser.add_argument("--timeout", type=int, default=30)

    diff_parser = sub.add_parser(
        "diff",
        help="Say what changed between two saved result documents.",
        description=(
            "Compare two result documents written by `scan` and report what "
            "changed: findings that appeared, findings that were resolved, and "
            "any movement in the rating, the version and the support horizon. "
            "Reads files only - it never scans anything."
        ),
    )
    diff_parser.add_argument(
        "before", type=Path, help="The earlier result document (JSON)."
    )
    diff_parser.add_argument(
        "after", type=Path, help="The later result document (JSON)."
    )
    diff_parser.add_argument(
        "--format",
        dest="diff_format",
        choices=("text", "markdown", "side-by-side", "json", "slack"),
        default="text",
        help=(
            "How to render the comparison: readable lines, a Markdown table, "
            "a two-column table of the findings on each side, the structured "
            "document the webhook carries, or Slack Block Kit. Default: text."
        ),
    )
    diff_parser.add_argument(
        "--category",
        dest="diff_categories",
        action="append",
        metavar="NAME",
        default=[],
        help=(
            "Show only this area, repeatable. A finding category ("
            + ", ".join(FINDING_CATEGORIES)
            + ") narrows the findings; a change category ("
            + ", ".join(CHANGE_CATEGORIES)
            + ") narrows the explanation of why they moved. Each namespace is "
            "filtered only when a value for it is given, so --category "
            "transport leaves the explanation intact."
        ),
    )
    diff_parser.add_argument(
        "--all-findings",
        action="store_true",
        help=(
            "List every finding the scans measured, not only the ones that "
            "moved. Without it a comparison answers what changed; with it, it "
            "also states what did not."
        ),
    )
    diff_parser.add_argument(
        "--allow-different-hosts",
        action="store_true",
        help=(
            "Compare documents from two different instances. Off by default: "
            "'did the fix work' is a question about one instance, and two "
            "hosts silently compared is a wrong answer nobody notices."
        ),
    )
    diff_parser.add_argument(
        "--exit-zero",
        action="store_true",
        help=(
            "Always exit 0. Without it, a comparison that got worse exits 1 so "
            "a pipeline can gate on it."
        ),
    )

    explain_parser = sub.add_parser(
        "explain",
        help="Say what a finding identifier means and how to fix it.",
        description=(
            "Look finding identifiers up in the same catalogue the scan "
            "output, the web application and `--debug` all read from. Reads "
            "nothing but its own package: no configuration, no network, no "
            "instance. With no identifier it prints the whole catalogue."
        ),
    )
    explain_parser.add_argument(
        "ids",
        nargs="*",
        metavar="ID",
        help=(
            "Identifiers to explain, such as cspWithoutUnsafeInline, "
            "Referrer-Policy or exposed:/config/opencloud.yaml. Without any, "
            "the whole catalogue is printed."
        ),
    )
    explain_parser.add_argument(
        "--category",
        choices=CATEGORIES,
        help="Print only the entries in one category of the catalogue.",
    )
    explain_parser.add_argument(
        "--list",
        dest="ids_only",
        action="store_true",
        help="Print bare identifiers, one per line, instead of explanations.",
    )
    explain_parser.add_argument(
        "--format",
        dest="explain_format",
        choices=("text", "json"),
        default="text",
        help="How to render the entries. Default: text.",
    )

    enable_completion(parser)
    return parser


def _configure_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")


def _run_scan(args: argparse.Namespace, scanner_settings, release_settings) -> int:
    exit_code = 0
    documents = []
    for host in args.hosts:
        try:
            documents.append(
                scan(host, settings=scanner_settings, release_settings=release_settings)
            )
        except ScanError as exc:
            LOGGER.error("Scan of %s failed: %s", host, exc)
            documents.append({"host": host, "error": str(exc)})
            exit_code = 1

    payload = documents[0] if len(documents) == 1 else documents
    print(json.dumps(payload, indent=None if args.compact else 2, sort_keys=False))
    return exit_code


class DiffError(Exception):
    """Raised when two documents cannot honestly be compared."""


def _load_result_document(path: Path) -> dict[str, Any]:
    """
    Read one archived result document.

    ``scan`` prints an array when it was given several hosts, so a
    single-element array is accepted as the document it contains. Anything
    longer is refused rather than guessed at: picking the first of four hosts
    would produce a confident comparison of the wrong instance.
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise DiffError(f"Cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise DiffError(f"{path} is not valid JSON: {exc}") from exc

    if isinstance(payload, list):
        if len(payload) != 1:
            raise DiffError(
                f"{path} holds {len(payload)} result documents. Compare one "
                "instance at a time; split the file first."
            )
        payload = payload[0]
    if not isinstance(payload, dict):
        raise DiffError(f"{path} does not contain a result document.")
    if payload.get("error"):
        raise DiffError(
            f"{path} records a scan that failed ({payload['error']}), so there "
            "is nothing in it to compare."
        )
    if "rating" not in payload:
        raise DiffError(
            f"{path} has no rating, so it is not a result document from "
            "`check-opencloud-scanner scan`."
        )
    return payload


def _document_host(document: dict[str, Any]) -> str:
    """The instance a document describes, however that document names it."""
    return str(document.get("domain") or document.get("host") or "unknown")


def _archived_snapshot(document: dict[str, Any]) -> Snapshot:
    """
    One document as the baseline sees it, but timestamped when it was scanned.

    ``snapshot_of`` stamps the current time, which is right when it is
    recording a run that just happened and wrong here: these two documents were
    written weeks ago, and when they were written is half of what the reader
    wants to know.
    """
    snapshot = snapshot_of(document, waived=document.get("ignored") or ())
    scanned_at = document.get("scannedAt")
    if isinstance(scanned_at, dict) and scanned_at.get("date"):
        return replace(snapshot, recorded_at=str(scanned_at["date"]))
    return snapshot


def _compare_documents(
    before: dict[str, Any], after: dict[str, Any]
) -> Comparison:
    """
    Compare two archived documents with the baseline's own arithmetic.

    Deliberately routed through :class:`Baseline` rather than reimplemented:
    what counts as a new finding here and what counts as one during monitoring
    must be the same question, or the diff would tell an operator something
    their alerts never will.
    """
    baseline = Baseline(path=Path(os.devnull))
    host = _document_host(after)
    baseline.record(host, _archived_snapshot(before))
    return baseline.compare(host, _archived_snapshot(after))


#: How one finding's movement is marked in the rendered comparison. The
#: glyphs are the ones a reader of a patch already knows, with `~` for the
#: case a patch has no glyph for: the same finding, weighted differently.
_DELTA_MARKS: dict[str, str] = {
    "introduced": "+",
    "appeared": "+",
    "resolved": "-",
    "disappeared": "-",
    "open": "~",
    "passing": " ",
}


def _split_categories(names: Sequence[str]) -> tuple[list[str], list[str]]:
    """
    Split the requested categories into the two namespaces they filter.

    A finding category says what an area of the instance is about; a change
    category says what kind of thing moved. They are different questions and
    do not share a value, so one flag can serve both without ambiguity.
    """
    findings: list[str] = []
    changes: list[str] = []
    unknown: list[str] = []
    for raw in names:
        name = raw.strip()
        if name in FINDING_CATEGORIES:
            findings.append(name)
        elif name in CHANGE_CATEGORIES:
            changes.append(name)
        else:
            unknown.append(name)
    if unknown:
        known = [*FINDING_CATEGORIES, *CHANGE_CATEGORIES]
        suggestions = get_close_matches(unknown[0], known, n=3)
        hint = f" Did you mean {', '.join(suggestions)}?" if suggestions else ""
        raise DiffError(
            f"Unknown category {unknown[0]!r}. Known categories: "
            f"{', '.join(known)}.{hint}"
        )
    return findings, changes


def _severity_line(deltas: Sequence[Delta]) -> str:
    """
    The failing findings by severity, before and after, on one line.

    Printed even when every count is unchanged: "critical 1 -> 1" is the
    answer to "how bad is it now", which is the question underneath "what
    changed" and the one a comparison of two lists never states outright.
    """
    totals = severity_totals(deltas)
    if not totals:
        return ""
    parts = [
        f"{severity} {before} -> {after}"
        for severity, (before, after) in totals.items()
    ]
    return "Failing by severity: " + ", ".join(parts)


def _delta_lines(deltas: Sequence[Delta], *, markdown: bool = False) -> list[str]:
    """One line per finding that moved, worst first, severities included."""
    lines = []
    for delta in deltas:
        mark = _DELTA_MARKS.get(delta.status, " ")
        moved = delta.severity_change
        if moved:
            detail = f"severity {moved[0]} -> {moved[1]}"
        elif delta.status in ("resolved", "disappeared") and delta.before:
            # What it was, not what it is. "Referrer-Policy: ok" is true and
            # tells the reader nothing about the line they are reading.
            detail = f"was {delta.before.label()}"
        else:
            side = delta.after or delta.before
            detail = side.label() if side else ""
        area = f" [{delta.category}]" if delta.category else ""
        if markdown:
            lines.append(f"- `{mark}` `{delta.id}`{area}: {detail}")
        else:
            lines.append(f"{mark} {delta.id}{area}: {detail}")
    if markdown and lines:
        lines = ["", "### Findings", "", *lines]
    return lines


def _missing(delta: Delta) -> str:
    """
    What an empty column means, which is not the same thing for both kinds.

    A check that is not in a document was not measured. An advisory that is
    not in one did not match the version, which is a measurement and not a
    gap - :mod:`opencloud_local_scan.findings` explains why the two must not
    be rendered with the same word.
    """
    return "not listed" if delta.category == ADVISORY_CATEGORY else "not measured"


def _side_by_side(
    host: str,
    before_at: str,
    after_at: str,
    deltas: Sequence[Delta],
    context: Sequence[str] = (),
) -> str:
    """
    The two documents as two columns, one finding per row.

    A reader comparing two scans is holding two states in their head at once,
    and the itemised list makes them reconstruct each side from the changes.
    This states both sides outright and leaves the reading to them, which is
    also why a finding that did not move can be shown here at all: the point
    of the view is the state, not only the difference.
    """
    header = ("Finding", before_at or "before", after_at or "after")
    rows = [header]
    for delta in deltas:
        mark = _DELTA_MARKS.get(delta.status, " ")
        rows.append(
            (
                f"{mark} {delta.id}",
                delta.before.label() if delta.before else _missing(delta),
                delta.after.label() if delta.after else _missing(delta),
            )
        )
    widths = [max(len(row[column]) for row in rows) for column in range(3)]
    rendered = [
        f"{host}",
        *context,
        "",
        "  ".join(cell.ljust(width) for cell, width in zip(rows[0], widths)).rstrip(),
        "  ".join("-" * width for width in widths),
    ]
    rendered.extend(
        "  ".join(cell.ljust(width) for cell, width in zip(row, widths)).rstrip()
        for row in rows[1:]
    )
    return "\n".join(rendered)


def _run_diff(args: argparse.Namespace) -> int:
    """Report what changed between two saved result documents."""
    try:
        before = _load_result_document(args.before)
        after = _load_result_document(args.after)
        finding_categories, change_categories = _split_categories(
            getattr(args, "diff_categories", []) or []
        )
    except DiffError as exc:
        LOGGER.error("%s", exc)
        return 2

    if (
        _document_host(before) != _document_host(after)
        and not args.allow_different_hosts
    ):
        LOGGER.error(
            "%s describes %s and %s describes %s. Pass "
            "--allow-different-hosts if comparing two instances is what you "
            "meant.",
            args.before,
            _document_host(before),
            args.after,
            _document_host(after),
        )
        return 2

    comparison = _compare_documents(before, after)
    # Why it differs, not only that it differs. The same model the web
    # comparison uses, so an operator's own monitoring and the service cannot
    # explain the same two documents differently.
    reasons = explain(before, after)
    # What differs, finding by finding, with the severity on each side. The
    # baseline above compares sets of names and is silent about a finding
    # that stayed open and got worse; this is where that movement comes from.
    deltas = compare_findings(
        before,
        after,
        categories=finding_categories,
        changed_only=not args.all_findings,
    )
    explained = [
        change
        for change in reasons.changes
        if change.code != "ratingChanged"
        and (not change_categories or change.category in change_categories)
    ]

    previous = comparison.previous
    assert previous is not None  # a diff always has both sides

    if args.diff_format == "json":
        print(
            json.dumps(
                {
                    **comparison.as_dict(),
                    "findings": [delta.as_dict() for delta in deltas],
                    "severityTotals": {
                        severity: {"before": counts[0], "after": counts[1]}
                        for severity, counts in severity_totals(deltas).items()
                    },
                    "explanation": reasons.as_dict(),
                },
                indent=2,
            )
        )
    elif args.diff_format == "slack":
        print(json.dumps(comparison.slack_blocks(), indent=2))
    elif args.diff_format == "side-by-side":
        print(
            _side_by_side(
                _document_host(after),
                previous.recorded_at or "before",
                comparison.current.recorded_at or "after",
                deltas,
                # The rating, the version and the support horizon belong to no
                # area of the instance, so they have no row in a table of
                # findings - and a findings table without them would leave the
                # reader working out the headline from the detail.
                [
                    f"{item['category']}: {item['change']}"
                    for item in comparison.items()
                    if item["category"] not in ("Security check", "Vulnerability")
                ],
            )
        )
        severities = _severity_line(deltas)
        if severities:
            print(severities)
        for change in explained:
            print(f"  [{change.category}] {change.summary}")
        if not change_categories:
            for limitation in reasons.limitations:
                print(f"  [limitation] {limitation}")
    else:
        markdown = args.diff_format == "markdown"
        print(
            f"{_document_host(after)}: {previous.recorded_at or 'unknown'} -> "
            f"{comparison.current.recorded_at or 'unknown'}"
        )
        if finding_categories:
            # The summary counts every new finding, which would contradict a
            # filtered list two lines below it: a reader would be told two is
            # new and shown one. What is being shown is said instead.
            print(f"Findings in {', '.join(finding_categories)}:")
        else:
            print(comparison.summary())
        if finding_categories:
            # The baseline's own itemised list is not filterable - it reports
            # the rating, the version and the lifecycle alongside the findings,
            # and none of those belong to an area of the instance. Asking for
            # one area is asking about findings, so that is what is rendered.
            for line in _delta_lines(deltas, markdown=markdown):
                print(line)
        else:
            changes = comparison.render(args.diff_format)
            if changes:
                print(changes)
            for line in _delta_lines(
                [delta for delta in deltas if delta.severity_change],
                markdown=markdown,
            ):
                print(line)
        severities = _severity_line(deltas)
        if severities:
            print(severities)
        for change in explained:
            print(f"  [{change.category}] {change.summary}")
        if not change_categories:
            for limitation in reasons.limitations:
                print(f"  [limitation] {limitation}")

    if args.exit_zero:
        return 0
    return 1 if comparison.regressed else 0


def _catalogue() -> list[Hardening]:
    """
    Every entry this build can explain, in the order the categories are listed.

    Header names are appended rather than merged into ``all_checks`` for the
    reason that function documents: a header has no catalogue entry of its own
    until one is built for it on demand.
    """
    entries = [*all_checks(), *(describe(name) for name in header_names())]
    order = {name: index for index, name in enumerate(CATEGORIES)}
    entries.sort(key=lambda entry: (order.get(entry.category, len(order)), entry.id))
    return entries


def _explain_entry(entry: Hardening) -> dict[str, Any]:
    """One catalogue entry as JSON, with the keys the result document uses."""
    return {
        "id": entry.id,
        "category": entry.category,
        "title": entry.title,
        "meaning": entry.meaning,
        "remediation": entry.remediation,
        "reference": entry.reference,
        "setting": entry.setting,
        "actionable": entry.actionable,
    }


def _run_explain(args: argparse.Namespace) -> int:
    """Explain finding identifiers, or print the catalogue."""
    known = _catalogue()

    if args.ids:
        entries: list[Hardening] = []
        unknown: list[str] = []
        for name in args.ids:
            entry = describe(name)
            # `describe` never fails - it names the unknown rather than
            # swallowing it - so the way to tell an explanation from a
            # placeholder is to ask whether the catalogue knows the id.
            if catalogue_id(name) is None:
                unknown.append(name)
                continue
            entries.append(entry)
        if unknown:
            for name in unknown:
                suggestions = get_close_matches(name, [item.id for item in known], n=3)
                hint = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
                LOGGER.error(
                    "No catalogue entry for '%s'.%s Run `explain --list` for "
                    "every identifier this build knows.",
                    name,
                    hint,
                )
            return 1
    else:
        entries = known

    if args.category:
        entries = [entry for entry in entries if entry.category == args.category]
        if not entries:
            LOGGER.error("No catalogue entry is in category '%s'.", args.category)
            return 1

    if args.ids_only:
        for entry in entries:
            print(entry.id)
    elif args.explain_format == "json":
        print(json.dumps([_explain_entry(entry) for entry in entries], indent=2))
    else:
        print("\n\n".join(entry.describe() for entry in entries))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point of ``check-opencloud-scanner``."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    if args.command == "explain":
        return _run_explain(args)
    if args.command == "diff":
        return _run_diff(args)
    if args.command == "configure":
        return run_setup(
            path=args.config,
            include_optional=args.include_optional,
            force=args.force,
            verify=args.verify,
            export=args.export,
        )
    if args.command == "refresh-data":
        try:
            paths = refresh_data(
                args.output_dir,
                schedule_url=args.schedule_url,
                advisory_url=args.advisory_url,
                timeout=args.timeout,
            )
        except RefreshError as exc:
            LOGGER.error("%s", exc)
            return 1
        for path in paths:
            print(path)
        return 0

    try:
        config = load_configuration(args.config)
    except ConfigurationError as exc:
        parser.error(str(exc))
        return 2

    try:
        scanner_settings = scanner_settings_from_config(
            config,
            timeout=getattr(args, "timeout", None),
            verify_tls=getattr(args, "verify_tls", None),
            tls_ca_file=getattr(args, "ca_file", None),
            extra_checks=getattr(args, "extra_checks", None),
            check_debug_ports=getattr(args, "check_debug_ports", None),
            check_all_addresses=getattr(args, "check_all_addresses", None),
            check_login_throttling=getattr(args, "check_login_throttling", None),
            port=getattr(args, "port", None) if args.command == "scan" else None,
            scheme=getattr(args, "scheme", None),
            concurrency=getattr(args, "concurrency", None),
        )
        release_settings = release_settings_from_config(config)
    except ConfigurationError as exc:
        parser.error(str(exc))
        return 2
    if getattr(args, "no_update_check", False):
        release_settings = release_settings.__class__(
            **{**release_settings.__dict__, "mode": "off"}
        )

    if args.command == "scan":
        return _run_scan(args, scanner_settings, release_settings)

    store = ScanStore(
        scanner_settings=scanner_settings,
        release_settings=release_settings,
        cache_ttl=args.cache_ttl
        or config.get_int("SERVICE_CACHE_TTL", DEFAULT_CACHE_TTL_SECONDS),
    )
    try:
        serve(
            store,
            listen=args.listen or config.get("SERVICE_LISTEN") or DEFAULT_LISTEN,
            port=args.port or config.get_int("SERVICE_PORT", DEFAULT_PORT),
            auth_token=args.token or config.get("SERVICE_TOKEN"),
        )
    except ServiceMisconfigured as exc:
        # A deployment mistake, not a crash: say what is wrong and how to fix
        # it, on stderr, with an exit code a supervisor will not retry through.
        print(f"UNKNOWN: {exc}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
