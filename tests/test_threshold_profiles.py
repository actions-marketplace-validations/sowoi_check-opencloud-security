"""
The named threshold sets behind --profile.

A profile is a judgement setting and nothing else, so the properties worth
protecting are that it changes only how a rating becomes an exit code, that
it never overrules something the operator wrote, and that a misspelled one is
refused rather than read as "no profile at all".
"""

from __future__ import annotations

import pytest

import check_opencloud_security as plugin


def parse(argv):
    """Parse argv the way main() does, profile included."""
    parser = plugin.build_arg_parser()
    args = parser.parse_args(argv)
    plugin._apply_profile(args, argv)
    return args


HOST = ["--host", "opencloud.example.com"]


def test_no_profile_leaves_every_default_alone():
    """An existing monitoring definition must behave exactly as it did."""
    args = parse(HOST)

    assert args.profile is None
    assert (args.warning, args.critical) == (
        plugin.DEFAULT_WARNING_RATING,
        plugin.DEFAULT_CRITICAL_RATING,
    )
    assert args.check_hardening is False
    assert args.update_warning is False
    assert args.eol_warning == 0


@pytest.mark.parametrize("name", sorted(plugin.PROFILES))
def test_every_profile_decides_the_same_five_settings(name):
    """A profile that forgot one would leave a default nobody chose behind."""
    assert set(plugin.PROFILES[name]) == set(plugin.PROFILE_OPTIONS)


@pytest.mark.parametrize("name", sorted(plugin.PROFILES))
def test_no_profile_changes_what_is_probed(name):
    """
    The point of the flag: it judges the same scan.

    Every setting a profile decides is a judgement setting, so none of them
    may be one of the flags that narrow or widen the evidence.
    """
    probing = {
        "no_extra_checks",
        "all_addresses",
        "login_throttling",
        "no_debug_ports",
        "port",
        "scheme",
        "concurrency",
        "timeout",
        "retries",
    }

    assert not probing.intersection(plugin.PROFILES[name])


def test_strict_alerts_on_anything_below_an_a():
    """The set a team adopts when a C is not acceptable."""
    args = parse([*HOST, "--profile", "strict"])

    assert (args.warning, args.critical) == (4, 2)
    assert args.check_hardening is True
    assert args.update_warning is True
    assert args.eol_warning == 90


def test_lenient_only_alerts_on_a_rating_that_means_trouble():
    """And it must not quietly switch hardening reporting on."""
    args = parse([*HOST, "--profile", "lenient"])

    assert (args.warning, args.critical) == (2, 0)
    assert args.check_hardening is False
    assert args.eol_warning == 0


def test_ops_keeps_the_default_thresholds():
    """It differs from no profile only in what it reports, not in what alerts."""
    args = parse([*HOST, "--profile", "ops"])

    assert (args.warning, args.critical) == (
        plugin.DEFAULT_WARNING_RATING,
        plugin.DEFAULT_CRITICAL_RATING,
    )
    assert args.check_hardening is True
    assert args.eol_warning == 30


def test_an_explicit_flag_wins_over_the_profile():
    """Precedence is the same as everywhere else: what you wrote is what you get."""
    args = parse([*HOST, "--profile", "strict", "--critical", "1"])

    assert args.critical == 1
    assert args.warning == 4


def test_an_attached_short_flag_counts_as_explicit():
    """'-w2' is the same instruction as '-w 2', and argparse cannot say so."""
    args = parse([*HOST, "--profile", "strict", "-w2"])

    assert args.warning == 2


def test_an_equals_spelling_counts_as_explicit():
    """'--eol-warning=5' must not be overwritten by the profile's 90."""
    args = parse([*HOST, "--profile", "strict", "--eol-warning=5"])

    assert args.eol_warning == 5


def test_a_threshold_from_the_environment_wins_over_the_profile(monkeypatch):
    """
    A profile is the weakest source of a value.

    Flag > environment > file > default is the documented order, and a
    profile supplies only what none of those did.
    """
    monkeypatch.setenv("COS_CRITICAL", "0")
    plugin._set_configuration(plugin.Configuration())
    try:
        args = parse([*HOST, "--profile", "strict"])
    finally:
        monkeypatch.delenv("COS_CRITICAL", raising=False)
        plugin._set_configuration(plugin.Configuration())

    assert args.critical == 0
    assert args.warning == 4


def test_the_profile_can_be_named_in_the_environment(monkeypatch):
    """Docker and systemd configure this plugin by environment, not by flag."""
    monkeypatch.setenv("COS_PROFILE", "lenient")
    plugin._set_configuration(plugin.Configuration())
    try:
        args = parse(HOST)
    finally:
        monkeypatch.delenv("COS_PROFILE", raising=False)
        plugin._set_configuration(plugin.Configuration())

    assert args.profile == "lenient"
    assert (args.warning, args.critical) == (2, 0)


def test_an_unknown_profile_is_refused_rather_than_ignored():
    """
    It arrives as a default when it comes from the environment.

    argparse validates 'choices' only for a value it parsed off the command
    line, so without this check a typo would silently judge the instance by
    rules nobody asked for.
    """
    parser = plugin.build_arg_parser()
    args = parser.parse_args(HOST)
    args.profile = "strikt"

    with pytest.raises(SystemExit):
        plugin._validate_thresholds(parser, args)


def test_a_profile_still_has_to_produce_valid_thresholds():
    """Every profile has to survive the plugin's own validation."""
    parser = plugin.build_arg_parser()
    for name in plugin.PROFILES:
        args = parser.parse_args([*HOST, "--profile", name])
        plugin._apply_profile(args, [*HOST, "--profile", name])
        plugin._validate_thresholds(parser, args)
        assert args.critical <= args.warning


def test_the_explanation_names_the_profile_a_rating_was_judged_by():
    """Somebody reading a result has to be able to see which rules applied."""
    context = plugin.ScanContext(host="opencloud.example.com", profile="strict")
    lines = plugin._explain_lines(context, {"rating": 4}, [], [])

    assert any("Profile: strict." in line for line in lines)


def test_the_explanation_stays_silent_without_a_profile():
    """A line about a setting nobody used is noise."""
    context = plugin.ScanContext(host="opencloud.example.com")
    lines = plugin._explain_lines(context, {"rating": 4}, [], [])

    assert not any("Profile:" in line for line in lines)
