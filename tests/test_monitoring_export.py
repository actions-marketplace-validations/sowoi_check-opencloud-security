"""
The wizard's answers, rendered as the files a scheduler actually reads.

Two things have to be true of these artefacts and are easy to lose.

They must say what the operator answered. A generated Icinga service that
quietly carries the example thresholds is worse than no generator, because it
looks reviewed. The threshold and release-track assertions here are against
the values put into the wizard, never against a literal copied from the
renderer.

And they must not carry a credential. The configuration file is owner-only; an
Icinga object in a zone directory and a systemd unit are not, so a webhook URL
rendered into either is a credential published to everyone who can read the
monitoring configuration.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import check_opencloud_security as plugin
from opencloud_local_scan import monitoring
from opencloud_local_scan.monitoring import (
    SETTINGS,
    icinga_service,
    service_name,
    systemd_environment,
    systemd_units,
)

WEBHOOK = "https://hooks.example.com/T000/B000/XXXXXXXXXXXX"
TOKEN = "ghp_examplereleasetoken"  # an example value, not a credential


def _answers(**overrides: object) -> dict:
    """A configuration shaped the way the wizard writes one."""
    data: dict = {
        "host": "opencloud.example.com",
        "warning": 4,
        "critical": 2,
        "check_hardening": True,
        "eol_warning": 30,
        "scanner": {
            "target_port": 9200,
            "release_track": "production",
            "verify_tls": False,
            "check_debug_ports": False,
            "ignore_hardenings": ["hstsPreload", "debugPort:*"],
        },
        "webhook": {"url": WEBHOOK},
        "releases": {"token": TOKEN},
    }
    data.update(overrides)
    return data


# --- what the artefacts have to say


def test_the_icinga_service_states_the_thresholds_that_were_answered():
    """
    A generated service carrying the example thresholds looks reviewed and is not.

    This is the whole point of generating it rather than copying one out of
    the documentation.
    """
    rendered = icinga_service(_answers())

    assert "vars.opencloud_warning = 4" in rendered
    assert "vars.opencloud_critical = 2" in rendered
    assert 'vars.opencloud_release_track = "production"' in rendered


def test_the_thresholds_and_release_track_are_stated_even_when_left_at_default():
    """
    "What does it alert on" is a reviewer's first question.

    An artefact that answers it only when the operator happened to change the
    value sends them to the documentation for the common case.
    """
    rendered = icinga_service({"host": "opencloud.example.com"})

    assert f"vars.opencloud_warning = {plugin.DEFAULT_WARNING_RATING}" in rendered
    assert f"vars.opencloud_critical = {plugin.DEFAULT_CRITICAL_RATING}" in rendered
    assert 'vars.opencloud_release_track = "auto"' in rendered


def test_the_stated_defaults_are_the_plugin_s_own():
    """A default restated in a second place is a default that can drift."""
    assert monitoring.DEFAULT_WARNING == plugin.DEFAULT_WARNING_RATING
    assert monitoring.DEFAULT_CRITICAL == plugin.DEFAULT_CRITICAL_RATING


def test_a_setting_the_operator_never_answered_is_not_invented():
    """
    Writing a value nobody chose is how a generator starts deciding things.

    Only the three in ALWAYS_STATED are filled in; everything else is absent
    from the artefact and read from the configuration file instead.
    """
    rendered = icinga_service({"host": "opencloud.example.com"})

    assert "opencloud_proxy" not in rendered
    assert "opencloud_eol_warning" not in rendered
    assert "opencloud_concurrency" not in rendered


# --- the inversions


def test_an_inverted_setting_becomes_the_flag_in_icinga_and_stays_itself_in_the_env():
    """
    `verify_tls: false` is `--insecure`, but it is *not* `COS_..._VERIFY_TLS=true`.

    The Icinga variable feeds a flag and has to be inverted; the environment
    variable is the setting itself. Inverting both would produce a check that
    verifies the certificate the operator just said not to verify - and the
    scan would then fail on the self-signed certificate they set this for.
    """
    data = _answers()

    rendered = icinga_service(data)
    assert "vars.opencloud_insecure = true" in rendered
    assert "vars.opencloud_no_debug_ports = true" in rendered

    environment = systemd_environment(data)
    assert "COS_SCANNER_VERIFY_TLS=false" in environment
    assert "COS_SCANNER_CHECK_DEBUG_PORTS=false" in environment
    assert "COS_SCANNER_VERIFY_TLS=true" not in environment


def test_a_list_setting_uses_each_format_s_own_syntax():
    """Icinga wants an array; the configuration reader wants a ';' joined string."""
    data = _answers()

    assert (
        'vars.opencloud_ignore_hardening = [ "hstsPreload", "debugPort:*" ]'
        in icinga_service(data)
    )
    assert "COS_SCANNER_IGNORE_HARDENINGS=hstsPreload;debugPort:*" in systemd_environment(
        data
    )


# --- what must never be in them


@pytest.mark.parametrize("secret", [WEBHOOK, TOKEN])
def test_no_credential_reaches_a_review_artefact(secret):
    """
    The configuration file is owner-only; these files are not.

    An Icinga object lives in a directory a whole team reads and a unit file
    is world-readable, so a webhook URL rendered into either is a credential
    published to everyone who can read the monitoring configuration.
    """
    data = _answers()
    config = "/etc/check-opencloud-security/.env.json"

    assert secret not in icinga_service(data, config_path=config)
    for text in systemd_units(data, config_path=config).values():
        assert secret not in text


def test_a_withheld_credential_is_named_rather_than_silently_dropped():
    """
    Silence would read as "no webhook configured".

    An operator who set one and sees no mention of it in the generated service
    has no way to tell whether it will fire.
    """
    config = "/etc/check-opencloud-security/.env.json"
    rendered = icinga_service(_answers(), config_path=config)

    assert "webhook.url" in rendered
    assert "releases.token" in rendered
    assert f'vars.opencloud_config = "{config}"' in rendered


def test_every_secret_setting_is_withheld_from_both_renderings():
    """A credential added to SETTINGS later must not have to be remembered twice."""
    data = _answers()
    # Give every secret setting a value that would be visible if rendered.
    for index, setting in enumerate(s for s in SETTINGS if s.secret):
        target = data
        parts = setting.key.split(".")
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = f"secret-value-{index}"

    rendered = icinga_service(data) + "".join(systemd_units(data).values())
    for index, _ in enumerate(s for s in SETTINGS if s.secret):
        assert f"secret-value-{index}" not in rendered


# --- the systemd units


def test_the_units_are_a_service_a_timer_and_an_environment_file():
    """A timer without its service, or either without settings, runs nothing."""
    units = systemd_units(_answers())

    assert set(units) == {
        "check-opencloud-security.service",
        "check-opencloud-security.timer",
        "check-opencloud-security.env",
    }
    service = units["check-opencloud-security.service"]
    assert "Type=oneshot" in service
    assert "ExecStart=" in service
    assert "[Install]" in units["check-opencloud-security.timer"]
    assert "OnCalendar=daily" in units["check-opencloud-security.timer"]


def test_the_generated_service_keeps_the_hardening_the_shipped_unit_has():
    """
    A generated unit weaker than the one in contrib/ is a silent downgrade.

    Nobody compares the two, so the generator has to carry the same
    directives rather than a simplified subset.
    """
    generated = systemd_units(_answers())["check-opencloud-security.service"]
    shipped = (
        Path(__file__).resolve().parent.parent
        / "contrib"
        / "systemd"
        / "check-opencloud-security.service"
    ).read_text(encoding="utf-8")

    for line in shipped.splitlines():
        directive = line.strip()
        if "=" not in directive or directive.startswith("#"):
            continue
        name = directive.split("=", 1)[0]
        if name in {"EnvironmentFile", "ExecStart", "Description"}:
            continue  # these are the parts the generator fills in
        assert directive in generated, f"{directive} was dropped from the generated unit"


def test_the_unit_reads_the_configuration_file_the_wizard_wrote():
    """The credentials it must not carry have to reach it some other way."""
    config = "/etc/check-opencloud-security/.env.json"
    environment = systemd_units(_answers(), config_path=config)[
        "check-opencloud-security.env"
    ]

    assert f"COS_CONFIG_FILE={config}" in environment


# --- naming


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("opencloud.example.com", "opencloud-security-opencloud.example.com"),
        ("https://cloud.example.com/", "opencloud-security-cloud.example.com"),
        ("opencloud.example.com:9200", "opencloud-security-opencloud.example.com"),
        ("a.example.com, b.example.com", "opencloud-security-a.example.com"),
    ],
)
def test_the_service_is_named_after_the_instance_not_the_url(host, expected):
    """
    A scheme or a port in an Icinga object name is a name nobody can filter on.

    A comma-separated host list is still one service, because the plugin scans
    every host in one run.
    """
    assert service_name({"host": host}) == expected
