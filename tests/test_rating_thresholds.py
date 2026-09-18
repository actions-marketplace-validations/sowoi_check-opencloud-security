"""Tests for the Nagios exit code mapping and the rating thresholds."""

import pytest

import check_opencloud_security as plugin
from check_opencloud_security import NagiosExitCode, ScanContext


def make_context(**kwargs):
    """A context with the plugin's default thresholds."""
    return ScanContext(host="cloud.example.com", **kwargs)


def evaluate(rating, num_vulns=0, eol=False, **kwargs):
    """Run the rating evaluation and return (message, exit code)."""
    return plugin._evaluate_rating(make_context(**kwargs), {"EOL": eol}, rating, num_vulns)


def test_exit_codes_follow_the_nagios_convention():
    """0/1/2/3 is what every monitoring system expects."""
    assert int(NagiosExitCode.OK) == 0
    assert int(NagiosExitCode.WARNING) == 1
    assert int(NagiosExitCode.CRITICAL) == 2
    assert int(NagiosExitCode.UNKNOWN) == 3


def test_rating_scale_matches_the_scanner():
    """The plugin and the scanner must agree on what a rating means."""
    assert plugin.RATE_MAP == {5: "A+", 4: "A", 3: "C", 2: "D", 1: "E", 0: "F"}


def test_perfect_rating_is_ok():
    """A+ with no vulnerabilities is the only fully clean result."""
    message, code = evaluate(5)

    assert code is NagiosExitCode.OK
    assert message.startswith("OK: Server is up to date")


def test_rating_a_is_ok_but_mentions_the_update():
    """Rating A means "current enough", not "perfect"."""
    message, code = evaluate(4)

    assert code is NagiosExitCode.OK
    assert "Update available" in message


def test_rating_at_the_warning_threshold_warns():
    """The threshold is inclusive."""
    _, code = evaluate(3)

    assert code is NagiosExitCode.WARNING


def test_rating_at_the_critical_threshold_is_critical():
    """The critical threshold is inclusive as well."""
    _, code = evaluate(1)

    assert code is NagiosExitCode.CRITICAL


def test_end_of_life_is_always_critical():
    """An unmaintained release is critical no matter what the rating says."""
    message, code = evaluate(5, eol=True)

    assert code is NagiosExitCode.CRITICAL
    assert "end-of-life" in message


def test_rating_zero_is_treated_as_end_of_life():
    """Rating F and EOL mean the same thing to an operator."""
    _, code = evaluate(0)

    assert code is NagiosExitCode.CRITICAL


def test_vulnerabilities_always_raise_at_least_a_warning():
    """A known CVE matters even when the rating still looks acceptable."""
    message, code = evaluate(5, num_vulns=2)

    assert code is NagiosExitCode.WARNING
    assert "Found 2 vulnerabilities" in message


def test_vulnerabilities_below_the_critical_threshold_are_critical():
    """The worst combination gets the worst state."""
    message, code = evaluate(1, num_vulns=3)

    assert code is NagiosExitCode.CRITICAL
    assert "Found 3 vulnerabilities" in message


def test_unknown_rating_is_unknown():
    """A result we cannot interpret must not be reported as OK."""
    message, code = evaluate(-1)

    assert code is NagiosExitCode.UNKNOWN
    assert "unclear" in message


def test_custom_thresholds_are_honoured():
    """An operator running a lab can loosen the thresholds."""
    _, code = evaluate(3, warning_rating=2, critical_rating=0)

    assert code is NagiosExitCode.OK


def test_stricter_thresholds_are_honoured():
    """A regulated environment can demand A+."""
    _, code = evaluate(4, warning_rating=4, critical_rating=3)

    assert code is NagiosExitCode.WARNING


@pytest.mark.parametrize(
    ("argv", "fragment"),
    [
        (["-H", "h", "-w", "9"], "between 0 and 5"),
        (["-H", "h", "-c", "-1"], "between 0 and 5"),
        (["-H", "h", "-w", "1", "-c", "3"], "must not be higher"),
        (["-H", "h", "--timeout", "0"], "positive number"),
        (["-H", "h", "--webhook-timeout", "0"], "positive number"),
        (["-H", "h", "--port", "70000"], "between 1 and 65535"),
        (["-H", "h", "--webhook-url", "ftp://x"], "http(s) URL"),
    ],
)
def test_invalid_thresholds_are_rejected(argv, fragment, capsys):
    """Bad input is a usage error, not a silently wrong check."""
    parser = plugin.build_arg_parser()
    args = parser.parse_args(argv)

    with pytest.raises(SystemExit):
        plugin._validate_thresholds(parser, args)

    assert fragment in capsys.readouterr().err


def test_valid_thresholds_pass():
    """The defaults must survive their own validation."""
    parser = plugin.build_arg_parser()
    args = parser.parse_args(["-H", "cloud.example.com"])

    plugin._validate_thresholds(parser, args)


def test_aggregate_exit_code_prefers_real_problems():
    """UNKNOWN must never mask a confirmed CRITICAL on another host."""
    assert (
        plugin._aggregate_exit_code([NagiosExitCode.UNKNOWN, NagiosExitCode.CRITICAL])
        is NagiosExitCode.CRITICAL
    )
    assert (
        plugin._aggregate_exit_code([NagiosExitCode.OK, NagiosExitCode.UNKNOWN])
        is NagiosExitCode.UNKNOWN
    )
    assert plugin._aggregate_exit_code([NagiosExitCode.OK]) is NagiosExitCode.OK


def test_end_of_life_names_the_release_line_and_the_upgrade():
    """The operator reads which line is dead and where to go, not just that it is."""
    lifecycle = {"releaseType": "rolling", "line": "2.x", "upgradeTo": "3.0.0"}
    message, _ = plugin._evaluate_rating(make_context(), {"EOL": True, "lifecycle": lifecycle}, 5, 0)

    assert message == (
        "CRITICAL: The 2.x rolling release line is end-of-life and has no security fixes. "
        "Upgrade to 3.0.0."
    )


def test_end_of_life_without_lifecycle_details_stays_generic():
    """No line and no target must not leave placeholders or a dangling hint."""
    message, _ = evaluate(5, eol=True)

    assert message == "CRITICAL: This server version is end-of-life and has no security fixes."


def test_threshold_messages_name_the_threshold_grade():
    """'at or below the threshold' is only useful with the threshold in it."""
    critical, _ = evaluate(2, critical_rating=2)
    warning, _ = evaluate(3, warning_rating=4)

    assert critical == "CRITICAL: Rating D is at or below the critical threshold D."
    assert warning == (
        "WARNING: Rating C is at or below the warning threshold A, but no known vulnerabilities."
    )


def test_ok_and_unknown_messages_are_exact():
    """The first word of the alert line is what monitoring systems parse."""
    assert evaluate(4)[0] == "OK: Update available, but no known vulnerabilities."
    assert evaluate(-1)[0] == "UNKNOWN: Scan result unclear. Please verify manually."


def test_end_of_life_without_a_release_type_names_only_the_line():
    """A missing track must not leave a placeholder in the sentence."""
    lifecycle = {"line": "2.x"}
    message, _ = plugin._evaluate_rating(make_context(), {"EOL": True, "lifecycle": lifecycle}, 5, 0)

    assert message == "CRITICAL: The 2.x release line is end-of-life and has no security fixes."


def test_a_threshold_outside_the_scale_is_named_as_unknown():
    """A caller that bypasses the argument checks gets '?', never 'None'."""
    critical, _ = plugin._evaluate_rating(make_context(critical_rating=6), {}, 5, 0)
    warning, _ = plugin._evaluate_rating(
        make_context(critical_rating=-1, warning_rating=6), {}, 5, 0
    )

    assert critical == "CRITICAL: Rating A+ is at or below the critical threshold ?."
    assert warning == (
        "WARNING: Rating A+ is at or below the warning threshold ?, but no known vulnerabilities."
    )
