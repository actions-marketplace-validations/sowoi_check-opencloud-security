"""--eol-warning: an otherwise OK result warns while support is running out."""

from __future__ import annotations

import copy

import pytest

import check_opencloud_security as plugin
from check_opencloud_security import NagiosExitCode, ScanContext, ScanResult
from opencloud_local_scan import wizard

HOST = "opencloud.example.com"

RESULT = {
    "domain": HOST,
    "product": "OpenCloud",
    "version": "7.2.0",
    "scannedAt": {"date": "2026-05-01 10:00:00.000000"},
    "rating": 5,
    "EOL": False,
    "vulnerabilities": [],
    "hardenings": {},
    "setup": {"https": {"used": True, "enforced": True}, "headers": {}},
    "updates": {"available": False, "version": "7.2.0", "source": "pinned"},
    "lifecycle": {
        "state": "supported",
        "line": "7.2",
        "releaseType": "production",
        "endOfLife": "2026-06-01",
        "daysRemaining": 20,
        "upgradeTo": "7.3.1",
    },
}


def result(**lifecycle):
    document = copy.deepcopy(RESULT)
    document["lifecycle"].update(lifecycle)
    return document


def run(document, capsys, **kwargs):
    context = ScanContext(host=HOST, **kwargs)
    with pytest.raises(SystemExit) as excinfo:
        plugin.check_vulnerabilities(
            context, ScanResult(response=document, uuid="local-x"), duration_seconds=1.0
        )
    first = capsys.readouterr().out.split("\n", 1)[0].split(" | ", 1)[0]
    return NagiosExitCode(excinfo.value.code), first


def test_support_ending_within_the_window_warns_and_names_the_target(capsys):
    """Twenty days left inside a thirty-day window is a WARNING with the upgrade."""
    code, first = run(result(), capsys, eol_warning_days=30)

    assert code is NagiosExitCode.WARNING
    assert first == (
        "WARNING: The 7.2 release line reaches end of life on 2026-06-01 "
        "(20 days left). Upgrade to 7.3.1."
    )


def test_support_ending_outside_the_window_stays_ok(capsys):
    """Twenty days left is not a concern for a ten-day window."""
    code, _ = run(result(), capsys, eol_warning_days=10)

    assert code is NagiosExitCode.OK


def test_the_last_day_of_the_window_still_warns(capsys):
    """The window is inclusive: exactly N days left warns."""
    code, _ = run(result(daysRemaining=30), capsys, eol_warning_days=30)

    assert code is NagiosExitCode.WARNING


def test_the_warning_is_off_by_default(capsys):
    """Without the option, a release one day from end of life is still OK."""
    code, _ = run(result(daysRemaining=1), capsys)

    assert code is NagiosExitCode.OK


def test_a_line_without_an_end_of_life_date_never_warns(capsys):
    """A current release with no published end of life has nothing to count down."""
    code, _ = run(result(daysRemaining=None, endOfLife=None), capsys, eol_warning_days=365)

    assert code is NagiosExitCode.OK


def test_a_worse_result_is_not_lowered_to_warning(capsys):
    """A CRITICAL rating keeps its own, more urgent alert line."""
    document = result()
    document["rating"] = 1
    code, first = run(document, capsys, eol_warning_days=30)

    assert code is NagiosExitCode.CRITICAL
    assert "end of life on" not in first


def test_the_option_is_read_from_the_environment(monkeypatch):
    """COS_EOL_WARNING sets the default; the flag overrides it."""
    monkeypatch.setenv("COS_EOL_WARNING", "45")
    original = plugin._CONFIG
    try:
        plugin._set_configuration(plugin._preparse_config([]))
        parser = plugin.build_arg_parser()
        assert parser.parse_args(["-H", HOST]).eol_warning == 45
        assert parser.parse_args(["-H", HOST, "--eol-warning", "7"]).eol_warning == 7
    finally:
        plugin._set_configuration(original)


def test_the_option_is_read_from_the_configuration_file(monkeypatch, tmp_path):
    """The YAML key eol_warning sets the default when the environment is silent."""
    monkeypatch.delenv("COS_EOL_WARNING", raising=False)
    path = tmp_path / "config.yml"
    path.write_text("eol_warning: 60\n", encoding="utf-8")
    original = plugin._CONFIG
    try:
        plugin._set_configuration(plugin._preparse_config(["--config", str(path)]))
        assert plugin.build_arg_parser().parse_args(["-H", HOST]).eol_warning == 60
    finally:
        plugin._set_configuration(original)


def test_the_option_defaults_to_off(monkeypatch):
    """Nothing configured means no early warning."""
    monkeypatch.delenv("COS_EOL_WARNING", raising=False)
    original = plugin._CONFIG
    try:
        plugin._set_configuration(plugin._preparse_config([]))
        assert plugin.build_arg_parser().parse_args(["-H", HOST]).eol_warning == 0
    finally:
        plugin._set_configuration(original)


def test_the_wizard_accepts_days_and_refuses_anything_else():
    """The wizard question takes 0 or a whole number of days."""
    assert wizard._non_negative_int("0") is None
    assert wizard._non_negative_int("30") is None
    assert wizard._non_negative_int("-1") is not None
    assert wizard._non_negative_int("soon") is not None
