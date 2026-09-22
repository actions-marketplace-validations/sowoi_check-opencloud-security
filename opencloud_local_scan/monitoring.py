"""
The answers the wizard collected, as the files a scheduler actually reads.

``--configure`` ends with a working configuration and a check that can be run
by hand. What it does not end with is the thing an operator came for: the
instance checked every day, by Icinga or by a systemd timer, without anybody
remembering the flags. That last step is copied out of the documentation, and
copying is where the thresholds quietly become somebody else's defaults.

This module renders it instead. Given the configuration the wizard just wrote,
it produces an Icinga 2 ``Service`` object and a systemd service, timer and
environment file, each carrying the values that were actually chosen.

Three rules shape what comes out.

**It renders, it does not decide.** Every value here was answered in the
wizard or is the plugin's own documented default, and the mapping from a
configuration key to a flag is :data:`SETTINGS`, which exists so that the
Icinga variable name and the ``COS_`` name for one setting cannot drift apart.
Nothing is judged: the thresholds are written down, not chosen.

**A secret never reaches a review artefact.** The configuration file is
written owner-only because a webhook URL or a release token is a credential.
These files are not: an Icinga object goes into a zone directory that a whole
team can read, and a unit file is world-readable by default. So a setting
marked :attr:`Setting.secret` is never rendered - the artefact points at the
configuration file with ``--config`` instead, and says so where the value
would have been.

**The result is reviewed, not applied.** Nothing here installs, reloads or
enables anything. The files are written where the operator asked, with the
command that would install them printed next to them, because a wizard that
edits ``/etc/icinga2`` and restarts a daemon is a wizard nobody runs twice.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import ENV_PREFIX
from .versions import TRACK_AUTO

#: The plugin's own defaults, repeated here so a rendered artefact states the
#: threshold it runs with rather than leaving a reader to look it up. They are
#: asserted against ``check_opencloud_security`` in the tests, so this cannot
#: drift into stating a threshold the plugin does not use.
DEFAULT_WARNING = 3
DEFAULT_CRITICAL = 1

#: How often a scheduled check runs, and why it is not more often. A scan is a
#: few dozen real requests against a real instance, and nothing about an
#: instance's rating changes from minute to minute.
DEFAULT_INTERVAL_HOURS = 24
DEFAULT_ON_CALENDAR = "daily"

#: Where the plugin usually lands. Only a default for the unit file; the
#: wizard offers to correct it.
DEFAULT_EXECUTABLE = "/usr/local/bin/check-opencloud-security"

#: The Icinga 2 CheckCommand these services import, from
#: ``contrib/icinga2/check_opencloud_security.conf``.
COMMAND_NAME = "check_opencloud_security"


@dataclass(frozen=True)
class Setting:
    """One configuration key, and the three names the tools know it by."""

    key: str
    """The wizard's own key, dotted as it appears in the configuration file."""

    icinga: str
    """
    The Icinga custom variable, without its ``opencloud_`` prefix.

    Taken from the CheckCommand rather than from the key: ``scanner.
    target_port`` is ``--port`` is ``vars.opencloud_port``, and the three
    spellings have no reason to agree.
    """

    invert: bool = False
    """
    Whether the flag says the opposite of the setting.

    ``scanner.verify_tls: false`` is ``--insecure``, and
    ``scanner.check_debug_ports: false`` is ``--no-debug-ports``. Rendering
    either one straight through would produce a check that verifies
    certificates when the operator asked it not to.
    """

    secret: bool = False
    """Whether the value is a credential, and so never rendered. See above."""

    quote: bool = True
    """Whether Icinga wants the value in quotes. Numbers and booleans do not."""


#: Every wizard answer that reaches a scheduled check, in the order an
#: operator reads them: what to scan, how hard to judge it, then the details.
#:
#: A setting the wizard can collect but that is missing here is simply not
#: rendered - the configuration file still carries it, and ``--config`` in
#: both artefacts means the check still reads it.
SETTINGS: tuple[Setting, ...] = (
    Setting("host", "host"),
    Setting("scanner.target_port", "port", quote=False),
    Setting("scanner.scheme", "scheme"),
    Setting("scanner.verify_tls", "insecure", invert=True, quote=False),
    Setting("proxy", "proxy"),
    Setting("timeout", "timeout", quote=False),
    Setting("warning", "warning", quote=False),
    Setting("critical", "critical", quote=False),
    Setting("check_hardening", "check_hardening", quote=False),
    Setting("scanner.release_track", "release_track"),
    Setting("update_source", "update_source"),
    Setting("update_warning", "update_warning", quote=False),
    Setting("eol_warning", "eol_warning", quote=False),
    Setting("scanner.concurrency", "concurrency", quote=False),
    Setting("scanner.check_debug_ports", "no_debug_ports", invert=True, quote=False),
    Setting("scanner.check_login_throttling", "login_throttling", quote=False),
    Setting("scanner.check_all_addresses", "all_addresses", quote=False),
    Setting("scanner.ignore_hardenings", "ignore_hardening"),
    # Credentials. Present so that the renderers know to say where the value
    # went, rather than silently producing a check that never notifies.
    Setting("webhook.url", "webhook_url", secret=True),
    Setting("webhook.headers", "webhook_header", secret=True),
    Setting("releases.token", "release_token", secret=True),
)

#: The settings a rendered artefact always states, even when the operator kept
#: the default. A reviewer's first two questions are "what does it alert on"
#: and "which release line is this judged against", and an artefact that
#: answers neither sends them to the documentation.
ALWAYS_STATED: dict[str, Any] = {
    "warning": DEFAULT_WARNING,
    "critical": DEFAULT_CRITICAL,
    "scanner.release_track": TRACK_AUTO,
}


def env_name(key: str) -> str:
    """The ``COS_`` environment variable for one configuration key."""
    return f"{ENV_PREFIX}{key.upper().replace('.', '_')}"


def _lookup(data: Mapping[str, Any], key: str) -> Any:
    """One dotted key out of the nested configuration, or ``None``."""
    current: Any = data
    for part in key.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def _effective(data: Mapping[str, Any], setting: Setting, *, as_flag: bool) -> Any:
    """
    The value to render, with defaults filled in.

    ``as_flag`` decides whether :attr:`Setting.invert` applies, and it is the
    whole reason the two renderers cannot share one value. An Icinga variable
    feeds a *flag*: ``verify_tls: false`` has to become
    ``vars.opencloud_insecure = true``. An environment variable *is* the
    setting: ``COS_SCANNER_VERIFY_TLS`` keeps the answer as given, and
    inverting it there would produce a check that verifies the certificate the
    operator just said not to verify.

    Returns ``None`` for anything that should not appear at all: a setting the
    operator never answered and that is not in :data:`ALWAYS_STATED`.
    """
    value = _lookup(data, setting.key)
    if value is None:
        if setting.key not in ALWAYS_STATED:
            return None
        value = ALWAYS_STATED[setting.key]
    if as_flag and setting.invert:
        return not value
    return value


def _icinga_value(value: Any, setting: Setting) -> str:
    """One value as Icinga 2 writes it."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        inner = ", ".join(f'"{item!s}"' for item in value)
        return f"[ {inner} ]"
    if setting.quote:
        return f'"{value}"'
    return str(value)


def _env_value(value: Any) -> str:
    """One value as the configuration reader parses it back out of the environment."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        # config.py joins list-valued settings with ";".
        return ";".join(str(item) for item in value)
    return str(value)


def service_name(data: Mapping[str, Any]) -> str:
    """
    A service name derived from the first host, for a ready-to-review object.

    One wizard run configures one check, so a comma-separated ``host`` list
    still produces one service: the plugin scans every host in one run, and
    naming the object after all of them would produce something nobody wants
    to type into a dashboard filter.
    """
    host = str(_lookup(data, "host") or "opencloud")
    first = host.split(",")[0].strip()
    for prefix in ("https://", "http://"):
        first = first.removeprefix(prefix)
    first = first.split("/")[0].strip("[]")
    return f"opencloud-security-{first.rsplit(':', 1)[0] or 'instance'}"


def _rendered_settings(
    data: Mapping[str, Any], *, as_flag: bool
) -> tuple[list[tuple[Setting, Any]], list[Setting]]:
    """The settings with a value to render, and the credentials withheld."""
    rendered: list[tuple[Setting, Any]] = []
    withheld: list[Setting] = []
    for setting in SETTINGS:
        value = _effective(data, setting, as_flag=as_flag)
        if value is None:
            continue
        if setting.secret:
            withheld.append(setting)
            continue
        rendered.append((setting, value))
    return rendered, withheld


def icinga_service(
    data: Mapping[str, Any],
    *,
    config_path: Path | str | None = None,
    host_name: str | None = None,
    name: str | None = None,
    interval_hours: int = DEFAULT_INTERVAL_HOURS,
) -> str:
    """
    The wizard's answers as an Icinga 2 ``Service`` object.

    The object imports ``generic-service`` and the CheckCommand from
    ``contrib/icinga2/check_opencloud_security.conf``, which has to be
    installed as well - the service sets variables, the command turns them
    into flags, and neither works without the other.
    """
    rendered, withheld = _rendered_settings(data, as_flag=True)
    target = str(config_path) if config_path else None
    chosen = name or service_name(data)
    monitored = host_name or str(_lookup(data, "host") or "").split(",")[0].strip()

    lines = [
        "// Generated by check-opencloud-security --configure.",
        "// Review it, then copy it into /etc/icinga2/conf.d/ or a zone directory.",
        "//",
        f"// It needs the CheckCommand object \"{COMMAND_NAME}\" as well; that is",
        "// contrib/icinga2/check_opencloud_security.conf in this project.",
        "//",
        "// The scan only talks to your own instance, so there is no external rate",
        "// limit to respect. A full scan is still a few dozen requests plus the",
        f"// debug-port probes, so one check every {interval_hours} hours is a sensible default.",
    ]
    if withheld:
        lines += [
            "//",
            "// Deliberately not written here: "
            + ", ".join(sorted(setting.key for setting in withheld))
            + ".",
            "// Those are credentials, and this file is readable by everyone who can",
            "// read the Icinga configuration. They stay in the configuration file",
            "// that vars.opencloud_config points at, which is owner-only."
            if target
            else "// Those are credentials. Pass them through a configuration file"
            " instead of writing them here.",
        ]
    lines += [
        f'object Service "{chosen}" {{',
        '    import "generic-service"',
        f'    host_name = "{monitored}"',
        f'    check_command = "{COMMAND_NAME}"',
        f"    check_interval = {interval_hours}h",
        "",
    ]
    if target:
        lines.append(f'    vars.opencloud_config = "{target}"')
    for setting, value in rendered:
        lines.append(
            f"    vars.opencloud_{setting.icinga} = {_icinga_value(value, setting)}"
        )
    lines.append("}")
    return "\n".join(lines) + "\n"


def systemd_environment(
    data: Mapping[str, Any], *, config_path: Path | str | None = None
) -> str:
    """
    The answers as an ``EnvironmentFile`` for the unit below.

    Credentials are left out for the same reason as above, and this file is
    the one that most wants the warning: an environment file is commonly world
    readable, and every variable in it is visible in the unit's environment to
    anything that can read ``/proc``.
    """
    rendered, withheld = _rendered_settings(data, as_flag=False)
    target = str(config_path) if config_path else None

    lines = [
        "# Generated by check-opencloud-security --configure.",
        "# Review it, then install it as /etc/check-opencloud-security/env.",
        "#",
        "# Give it owner-only permissions if you add anything sensitive:",
        "#   install -m 0600 env /etc/check-opencloud-security/env",
    ]
    if withheld:
        lines += [
            "#",
            "# Deliberately not written here: "
            + ", ".join(sorted(setting.key for setting in withheld))
            + ".",
            "# Those are credentials, and an environment file is readable by anything",
            "# that can read the process's /proc entry.",
        ]
        if target:
            lines.append(f"# They stay in {target}, which is owner-only.")
    lines.append("")
    if target:
        lines += [
            "# Everything else the check reads, including the credentials above.",
            f"{env_name('config_file')}={target}",
            "",
        ]
    for setting, value in rendered:
        lines.append(f"{env_name(setting.key)}={_env_value(value)}")
    return "\n".join(lines) + "\n"


def systemd_service(
    *,
    executable: str = DEFAULT_EXECUTABLE,
    environment_file: str = "/etc/check-opencloud-security/env",
) -> str:
    """
    The unit that runs one scan.

    The hardening directives are the ones in
    ``contrib/systemd/check-opencloud-security.service`` and are not derived
    from any answer: they describe what the scan needs to do - resolve a name,
    open an outbound socket - rather than anything about the instance, so
    there is nothing here for the wizard to ask about.
    """
    return f"""[Unit]
Description=Check an OpenCloud instance for known vulnerabilities and misconfiguration
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
EnvironmentFile={environment_file}
ExecStart={executable}
DynamicUser=yes
# Only used when a baseline is configured; an unused StateDirectory is just an
# empty directory systemd owns.
StateDirectory=check-opencloud-security

# Hardening. Run `systemd-analyze security check-opencloud-security.service`
# to see the effect of these directives.
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictSUIDSGID=yes
LockPersonality=yes
MemoryDenyWriteExecute=yes
RestrictAddressFamilies=AF_INET AF_INET6
CapabilityBoundingSet=
SystemCallFilter=@system-service
"""


def systemd_timer(*, on_calendar: str = DEFAULT_ON_CALENDAR) -> str:
    """
    The timer that runs it on a schedule.

    ``RandomizedDelaySec`` is not tuning for its own sake: the scan talks only
    to your instance, but the update check reads the GitHub release feed,
    which is rate limited per IP address, so many hosts behind one address
    firing at the same second is the one way a scheduled check rate-limits
    itself.
    """
    return f"""[Unit]
Description=Run check-opencloud-security on a schedule

[Timer]
OnCalendar={on_calendar}
RandomizedDelaySec=30min
Persistent=true

[Install]
WantedBy=timers.target
"""


def systemd_units(
    data: Mapping[str, Any],
    *,
    config_path: Path | str | None = None,
    executable: str = DEFAULT_EXECUTABLE,
    on_calendar: str = DEFAULT_ON_CALENDAR,
    environment_file: str = "/etc/check-opencloud-security/env",
) -> dict[str, str]:
    """Every systemd file for this configuration, keyed by the name to write it under."""
    return {
        "check-opencloud-security.service": systemd_service(
            executable=executable, environment_file=environment_file
        ),
        "check-opencloud-security.timer": systemd_timer(on_calendar=on_calendar),
        "check-opencloud-security.env": systemd_environment(
            data, config_path=config_path
        ),
    }


#: What to run once the files have been reviewed. Printed, never executed -
#: installing a unit and reloading a daemon is the operator's decision, and a
#: wizard that did it on its own is one nobody runs a second time.
INSTALL_HINTS: dict[str, tuple[str, ...]] = {
    "icinga": (
        "sudo install -m 0644 {path} /etc/icinga2/conf.d/{name}",
        "sudo icinga2 daemon -C && sudo systemctl reload icinga2",
    ),
    "systemd": (
        (
            "sudo install -m 0600 {directory}/check-opencloud-security.env"
            " /etc/check-opencloud-security/env"
        ),
        (
            "sudo install -m 0644"
            " {directory}/check-opencloud-security.{{service,timer}}"
            " /etc/systemd/system/"
        ),
        "sudo systemctl daemon-reload",
        "sudo systemctl enable --now check-opencloud-security.timer",
    ),
}
