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


# --- edge cases ------------------------------------------------------------------
@pytest.mark.parametrize("days", [0, -3])
def test_no_days_left_is_not_an_early_warning(days, capsys):
    """Zero or fewer days is end of life, which the lifecycle state reports, not this window."""
    code, first = run(result(daysRemaining=days), capsys, eol_warning_days=30)

    assert code is NagiosExitCode.OK
    assert "end of life on" not in first


@pytest.mark.parametrize("state", ["eol", "unknown", None])
def test_only_a_supported_line_counts_down(state, capsys):
    """An unsupported or unknown line is not raised by the early warning."""
    _, first = run(result(state=state, daysRemaining=5), capsys, eol_warning_days=30)

    assert "end of life on" not in first
    assert "days left" not in first


@pytest.mark.parametrize("days", ["5", 5.0, None, [5]])
def test_a_days_remaining_that_is_not_a_whole_number_is_ignored(days, capsys):
    """A malformed lifecycle is not a reason to warn, nor to crash."""
    code, _ = run(result(daysRemaining=days), capsys, eol_warning_days=30)

    assert code is NagiosExitCode.OK


@pytest.mark.parametrize("lifecycle", [None, "supported", [], {}])
def test_a_missing_or_malformed_lifecycle_does_not_raise(lifecycle, capsys):
    """An older scan result without a lifecycle section is simply OK."""
    document = copy.deepcopy(RESULT)
    document["lifecycle"] = lifecycle

    code, _ = run(document, capsys, eol_warning_days=30)

    assert code is NagiosExitCode.OK


def test_the_warning_reads_sensibly_without_a_line_a_date_or_a_target(capsys):
    """Every optional part of the sentence has a fallback, never 'None'."""
    code, first = run(
        result(line=None, endOfLife=None, upgradeTo=None, daysRemaining=5),
        capsys,
        eol_warning_days=30,
    )

    assert code is NagiosExitCode.WARNING
    assert first == (
        "WARNING: This server version reaches end of life on an unknown date (5 days left)."
    )
    assert "None" not in first


def test_a_negative_option_is_a_usage_error(capsys):
    """A negative window is a typo, not a quiet 'off'."""
    parser = plugin.build_arg_parser()
    args = parser.parse_args(["-H", HOST, "--eol-warning", "-1"])

    with pytest.raises(SystemExit) as excinfo:
        plugin._validate_thresholds(parser, args)

    assert excinfo.value.code == 2
    assert "--eol-warning must be 0" in capsys.readouterr().err


def test_a_non_numeric_option_is_a_usage_error(capsys):
    """argparse refuses the flag outright rather than turning it into 0."""
    with pytest.raises(SystemExit) as excinfo:
        plugin.build_arg_parser().parse_args(["-H", HOST, "--eol-warning", "soon"])

    assert excinfo.value.code == 2
    assert "--eol-warning" in capsys.readouterr().err


def test_an_invalid_environment_value_falls_back_to_off(monkeypatch):
    """COS_EOL_WARNING=soon is logged and ignored, as every other integer setting is."""
    monkeypatch.setenv("COS_EOL_WARNING", "soon")
    original = plugin._CONFIG
    try:
        plugin._set_configuration(plugin._preparse_config([]))
        assert plugin.build_arg_parser().parse_args(["-H", HOST]).eol_warning == 0
    finally:
        plugin._set_configuration(original)


@pytest.mark.parametrize("value", ["", " ", "1.5", "1e3", "-0.5", "²", "¹⁰"])
def test_the_wizard_refuses_what_int_would_not_read_as_days(value):
    """
    Whatever the validator lets through, the int() cast after it must read.

    '²' is a digit to str.isdigit() and a ValueError to int(), which crashed
    the wizard mid-question before the validator was based on int() itself.
    """
    assert wizard._non_negative_int(value) is not None


@pytest.mark.parametrize("value", ["0", "30", " 30 ", "+5", "３"])
def test_every_value_the_wizard_accepts_is_one_int_can_read(value):
    """The validator and the cast agree, including on a full-width digit."""
    assert wizard._non_negative_int(value) is None
    assert int(value) >= 0

