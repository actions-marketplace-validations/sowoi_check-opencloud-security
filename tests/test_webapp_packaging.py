"""
What ends up on PyPI, and what deliberately does not.

The plugin is installed on monitoring hosts by people who want a check, not a
web application. The wheel therefore carries the plugin and the scanner
library and nothing else: no FastAPI wrapper, no templates, no CSS, and no
dependency on any of it.

These tests build the real artefacts with the real backend, because the only
thing worth asserting is what ``pip install`` would actually receive.
"""

from __future__ import annotations

import hashlib
import re
import shlex
import subprocess  # nosec B404 - builds this project's own artefacts
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytest.importorskip("build", reason="the packaging tests need the build front end")
pytest.importorskip("hatchling", reason="the packaging tests build without isolation")


@pytest.fixture(scope="module")
def artefacts(tmp_path_factory) -> tuple[Path, Path]:
    """Build the wheel and the sdist once, the way the release workflow does."""
    out = tmp_path_factory.mktemp("dist")
    subprocess.run(  # nosec B603 - fixed argument list, no shell
        [sys.executable, "-m", "build", "--no-isolation", "--outdir", str(out), str(ROOT)],
        check=True,
        capture_output=True,
    )
    wheel = next(out.glob("*.whl"))
    sdist = next(out.glob("*.tar.gz"))
    return wheel, sdist


def _wheel_names(wheel: Path) -> list[str]:
    with zipfile.ZipFile(wheel) as archive:
        return archive.namelist()


def _sdist_names(sdist: Path) -> list[str]:
    with tarfile.open(sdist) as archive:
        # Strip the leading 'project-1.2.3/' so the assertions read naturally.
        return [name.split("/", 1)[-1] for name in archive.getnames()]


def test_the_wheel_carries_the_plugin_and_the_scanner(artefacts):
    """A positive assertion first: the exclusions must not have excluded the check."""
    wheel, _ = artefacts
    names = _wheel_names(wheel)

    assert "check_opencloud_security.py" in names
    assert any(name.startswith("opencloud_local_scan/") for name in names)
    assert any(name.endswith("release_schedule.json") for name in names)


def test_the_wheel_contains_no_frontend_asset(artefacts):
    """
    Templates, CSS, JavaScript and SVGs have no business on a monitoring host.

    They are also the part most likely to be dragged in by accident, since a
    later change to the include list would pick up whole directories.
    """
    wheel, _ = artefacts
    names = _wheel_names(wheel)

    assert not [name for name in names if name.startswith("frontend/")]
    assert not [name for name in names if name.startswith("webapp/")]
    assert not [name for name in names if name.endswith((".html", ".css", ".js", ".svg"))]


def test_the_sdist_contains_no_frontend_or_web_application(artefacts):
    """
    The sdist is what a distribution packager builds from.

    Shipping the web application there would put a FastAPI service into
    somebody's system package without them ever asking for one.
    """
    _, sdist = artefacts
    names = _sdist_names(sdist)

    assert "check_opencloud_security.py" in names
    assert not [name for name in names if name.startswith("frontend/")]
    assert not [name for name in names if name.startswith("webapp/")]


def test_the_web_application_is_an_extra_and_never_a_dependency(artefacts):
    """
    Installing the plugin must not pull in FastAPI, Redis or ARQ.

    The check runs from cron on hosts where every added dependency is another
    thing that can fail at three in the morning.
    """
    wheel, _ = artefacts
    with zipfile.ZipFile(wheel) as archive:
        metadata = next(
            archive.read(name).decode("utf-8")
            for name in archive.namelist()
            if name.endswith(".dist-info/METADATA")
        )

    required = re.findall(
        r"^Requires-Dist: ([A-Za-z0-9._-]+)(.*)$", metadata, re.MULTILINE
    )
    unconditional = {name.lower() for name, tail in required if "extra ==" not in tail}

    for package in ("fastapi", "uvicorn", "redis", "arq", "jinja2"):
        assert package not in unconditional
    # ... and they are on offer, so the extra actually installs something.
    conditional = {
        name.lower() for name, tail in required if "extra ==" in tail and "web" in tail
    }
    assert {"fastapi", "arq", "redis"} <= conditional


def test_the_web_tests_are_not_shipped_with_the_sdist(artefacts):
    """
    The sdist's tests must run against what the sdist contains.

    Shipping a test that imports ``webapp`` into an archive that has no
    ``webapp`` turns a packager's test run into a failure they cannot fix.
    """
    _, sdist = artefacts
    names = _sdist_names(sdist)

    assert "tests/test_local_scanner.py" in names
    assert not [name for name in names if name.startswith("tests/test_webapp_")]


def _bundle(tmp_path: Path) -> tuple[Path, list[str]]:
    """Build the release tarball and return it with its member names."""
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import build_web_bundle
    finally:
        sys.path.pop(0)

    archive = build_web_bundle.build(tmp_path, "bundle")
    with tarfile.open(archive) as tar:
        names = [name.split("/", 1)[-1] for name in tar.getnames()]
    return archive, names


def test_the_release_bundle_carries_everything_needed_to_run_the_service(tmp_path):
    """
    The tarball is the only way to get the web application, so it must be whole.

    Somebody downloads this instead of installing from PyPI precisely because
    the wheel leaves the frontend out; an archive missing a template or the
    compose file would strand them with no second source.
    """
    _, names = _bundle(tmp_path)

    for required in (
        "webapp/app.py",
        "webapp/tasks.py",
        "frontend/templates/index.html",
        "frontend/templates/scan.html",
        "frontend/static/css/app.css",
        "frontend/static/js/scan.js",
        "frontend/static/js/webmcp.js",
        "frontend/static/llms.txt",
        "opencloud_local_scan/scanner.py",
        "opencloud_local_scan/data/release_schedule.json",
        "check_opencloud_security.py",
        "docker/Dockerfile.web",
        "docker/docker-compose.yml",
        "docs/webapp.md",
        "QUICKSTART.md",
    ):
        assert required in names, f"the bundle is missing {required}"


def test_the_release_bundle_leaks_no_local_state(tmp_path):
    """
    This archive is downloaded by strangers from a checkout that is somebody's
    working copy, so caches, keys and dotfiles must be filtered rather than
    trusted not to exist.
    """
    _, names = _bundle(tmp_path)

    assert not [name for name in names if "__pycache__" in name]
    assert not [name for name in names if name.endswith((".pyc", ".env", ".key", ".pem"))]
    assert not [name for name in names if name.startswith(("tests/", ".git"))]


def test_the_release_bundle_is_published_with_a_checksum(tmp_path):
    """A download nobody can verify is a download nobody should run."""
    archive, _ = _bundle(tmp_path)
    checksum = archive.with_suffix(archive.suffix + ".sha256")

    assert checksum.is_file()
    digest, _, filename = checksum.read_text(encoding="utf-8").strip().partition("  ")
    assert filename == archive.name
    assert digest == hashlib.sha256(archive.read_bytes()).hexdigest()


def test_every_container_file_lives_in_the_docker_directory():
    """
    One place to look for a Dockerfile, so nobody edits the stale copy.

    The files moved out of the repository root; a new one landing back there
    would be found by half the documentation and none of the readers.
    """
    stray = [
        path.name
        for path in ROOT.iterdir()
        if path.name.startswith(("Dockerfile", "docker-compose"))
    ]
    assert not stray, f"container files belong in docker/: {stray}"

    for expected in (
        "docker/Dockerfile",
        "docker/Dockerfile.web",
        "docker/docker-compose.yml",
        "docker/docker-compose.monitoring.yml",
    ):
        assert (ROOT / expected).is_file(), f"missing {expected}"

    # The context root, and the only place the daemon reads it from.
    assert (ROOT / ".dockerignore").is_file()


@pytest.mark.parametrize(
    "compose", ("docker/docker-compose.yml", "docker/docker-compose.monitoring.yml")
)
def test_a_compose_file_builds_from_the_repository_root(compose):
    """
    An image needs webapp/, frontend/ and the wheel sources, which sit above it.

    A context of '.' inside docker/ builds an image that is missing the
    application, and it fails at run time rather than at build time.
    """
    text = (ROOT / compose).read_text(encoding="utf-8")

    assert "context: .." in text
    assert "context: .\n" not in text
    for line in text.splitlines():
        if line.strip().startswith("dockerfile:"):
            assert line.split(":", 1)[1].strip().startswith("docker/"), line


STACKS_WITH_REDIS = (
    "docker/docker-compose.yml",
    "docker/docker-compose.dockerhub.yml",
    "docker/docker-compose.authentik.yml",
)


def _service_commands(compose: str) -> dict[str, list[str]]:
    """Every string `command:` in one compose file, split the way Compose does."""
    import yaml

    document = yaml.safe_load((ROOT / compose).read_text(encoding="utf-8"))
    return {
        name: shlex.split(service["command"])
        for name, service in (document.get("services") or {}).items()
        if isinstance(service.get("command"), str)
    }


@pytest.mark.parametrize("compose", STACKS_WITH_REDIS)
def test_a_folded_command_block_carries_no_commentary(compose):
    """
    `command: >` is a folded scalar, so a '#' inside it is text, not a comment.

    Prose written between the options is folded into the command line and handed
    to the entrypoint as arguments. For Redis that put fifty words between
    --maxmemory-policy and --requirepass, so the server either refuses the
    directive outright or comes up with no password at all on a store holding
    every live scan. The comments belong above the block; this asserts they
    stayed there.
    """
    commands = _service_commands(compose)
    assert commands, f"{compose} defines no string command to check"

    for name, argv in commands.items():
        assert "#" not in argv, (
            f"{compose}: the {name} command carries a folded-in comment: {argv}"
        )


@pytest.mark.parametrize("compose", STACKS_WITH_REDIS)
def test_the_redis_password_option_reaches_the_server(compose):
    """
    The one option in that block whose loss is silent rather than loud.

    A missing --maxmemory shows up as memory growth. A missing --requirepass
    shows up as nothing at all, on a Redis holding every result inside its TTL -
    so it is asserted to be a directive of its own rather than merely a string
    present somewhere in the command.
    """
    argv = _service_commands(compose)["redis"]

    assert "--requirepass" in argv, compose
    # Directly after the option before it: anything in between is a word that
    # was folded in, which would make this an argument to that option instead.
    assert argv[argv.index("--requirepass") - 1] == "allkeys-lru", compose
    # And it takes exactly one value - the interpolation Compose fills in.
    assert argv[argv.index("--requirepass") + 1 :] == ["${COS_REDIS_PASSWORD:-}"], compose


def test_the_release_bundle_carries_the_signed_in_stack(tmp_path):
    """
    The Authentik stack is useless without the two files that provision it.

    Somebody downloading the tarball gets the compose file either way; without
    the bootstrap script there are no secrets for it to read, and without the
    blueprint there is no provider, so the stack starts and then refuses every
    token.
    """
    _, names = _bundle(tmp_path)

    for required in (
        "docker/docker-compose.authentik.yml",
        "docker/authentik-env.sh",
        "authentik/blueprints/opencloud-scanner.yaml",
        # And the second one, which is the only way into /admin. The wizard
        # copies whichever blueprint a deployment asked for, and can copy only
        # what the tarball carried - a missing one is an area nobody reaches.
        "authentik/blueprints/opencloud-admin.yaml",
        # Without these the wizard's enrollment link leads nowhere and nobody
        # is asked for a second factor.
        "authentik/blueprints/opencloud-mfa.yaml",
        "authentik/blueprints/opencloud-enrollment.yaml",
        "docs/authentik.md",
    ):
        assert required in names, f"the bundle is missing {required}"


def test_the_release_bundle_carries_the_setup_wizard(tmp_path):
    """
    Whoever unpacks the tarball is setting up a deployment, which is exactly
    what the wizard is for - and it has to arrive executable, or the first
    thing they meet is a permission error.
    """
    archive, names = _bundle(tmp_path)

    assert "docker/setup-wizard.py" in names, "the bundle is missing the setup wizard"

    with tarfile.open(archive) as tar:
        wizard = next(m for m in tar.getmembers() if m.name.endswith("docker/setup-wizard.py"))
    assert wizard.mode == 0o755, "the wizard has to stay executable"


def test_the_release_bundle_does_not_inherit_the_umask_of_whoever_built_it(tmp_path):
    """
    A tarball built under a restrictive umask used to ship files nobody could
    read, and the account name of the person who built it.

    Authentik reads the blueprint as an unprivileged uid inside its container:
    a mode of 0640 means the provider is never created, and the failure is
    silent. The owner matters for a different reason - a public download
    should not carry somebody's login name.
    """
    archive, _ = _bundle(tmp_path)

    with tarfile.open(archive) as tar:
        members = tar.getmembers()

    assert members, "the bundle is empty"
    for member in members:
        assert member.uname == "root" and member.gname == "root", member.name
        assert member.uid == 0 and member.gid == 0, member.name
        # World-readable, and world-traversable where it is a directory.
        assert member.mode & 0o044, f"{member.name} is {member.mode:o}"

    script = next(m for m in members if m.name.endswith("docker/authentik-env.sh"))
    assert script.mode == 0o755, "the bootstrap script has to stay executable"
    blueprint = next(m for m in members if m.name.endswith("opencloud-scanner.yaml"))
    assert blueprint.mode == 0o644, "a blueprint is data, never a program"


def test_the_authentik_stack_ties_the_sign_in_to_the_endpoint():
    """
    Authentik is there to guard /mcp, so the guard must not be separately
    switchable off.

    If the two settings could disagree, the failure mode is an operator who
    brought up an identity provider, believes the endpoint is protected, and
    is serving it open. Tying one to the other removes that combination
    entirely: no /mcp, no sign-in; /mcp, sign-in.
    """
    text = (ROOT / "docker/docker-compose.authentik.yml").read_text(encoding="utf-8")

    assert 'COS_WEB_MCP_AUTH_ENABLED: "${COS_WEB_ENABLE_MCP:-true}"' in text
    # The negative case: nothing may pin it off, or default it independently.
    assert 'COS_WEB_MCP_AUTH_ENABLED: "false"' not in text
    assert "COS_WEB_MCP_AUTH_ENABLED: \"${COS_WEB_MCP_AUTH_ENABLED" not in text


def test_the_authentik_stack_can_send_mail_from_both_of_its_processes():
    """
    A password recovery is sent by the worker and a test message by the server,
    so mail configured on only one of them works until the moment it matters.

    An identity provider that cannot send mail locks out the one account it
    starts with, and the way back in is editing the database. The settings are
    empty by default, which leaves Authentik on local delivery rather than on a
    half-configured session.
    """
    import yaml

    document = yaml.safe_load(
        (ROOT / "docker/docker-compose.authentik.yml").read_text(encoding="utf-8")
    )

    for name in ("authentik_server", "authentik_worker"):
        environment = document["services"][name]["environment"]
        assert environment["AUTHENTIK_EMAIL__HOST"] == "${AUTHENTIK_EMAIL_HOST:-}"
        assert environment["AUTHENTIK_EMAIL__PASSWORD"] == "${AUTHENTIK_EMAIL_PASSWORD:-}"
        assert environment["AUTHENTIK_EMAIL__FROM"].startswith("${AUTHENTIK_EMAIL_FROM:-")
        # The two ways of encrypting the session must stay separately settable.
        assert environment["AUTHENTIK_EMAIL__USE_TLS"] == "${AUTHENTIK_EMAIL_USE_TLS:-true}"
        assert environment["AUTHENTIK_EMAIL__USE_SSL"] == "${AUTHENTIK_EMAIL_USE_SSL:-false}"


def test_the_provisioning_blueprint_holds_no_secret_and_signs_asymmetrically():
    """
    The blueprint is committed, so anything literal in it is published.

    The signing key matters just as much: without one Authentik falls back to
    signing with the client secret, and a token nobody can verify against a
    JWKS is a token this service refuses - a stack that provisions itself into
    that state would fail with no obvious cause.
    """
    import yaml

    class _Loader(yaml.SafeLoader):
        pass

    seen: list[str] = []

    def _tag(loader, node):
        seen.append(node.tag)
        return node.tag

    for tag in ("!Env", "!Find", "!KeyOf", "!Format", "!Context", "!If"):
        _Loader.add_constructor(tag, _tag)

    path = ROOT / "authentik/blueprints/opencloud-scanner.yaml"
    document = yaml.load(path.read_text(encoding="utf-8"), Loader=_Loader)  # nosec B506

    assert document["version"] == 1
    provider = next(
        entry
        for entry in document["entries"]
        if entry["model"] == "authentik_providers_oauth2.oauth2provider"
    )
    attrs = provider["attrs"]

    assert attrs["signing_key"] == "!Find", "an unsigned provider issues HS256"
    assert attrs["client_secret"] == "!Env", "a literal secret here would be published"
    assert attrs["client_id"] == "!Env"
    assert "client_credentials" in attrs["grant_types"], "a headless agent needs it"
    # Provisioning must not undo an operator's later edits.
    assert provider["state"] == "created"


def test_the_admin_blueprint_hands_its_provider_to_the_outpost_that_actually_runs():
    """
    The forward auth for /admin is answered by authentik's embedded outpost.

    The generated reverse proxy sends `/outpost.goauthentik.io/` to the server's
    own port, where only the embedded outpost listens, and it routes a request
    only for a host belonging to a provider assigned to it. The blueprint used
    to create a separate outpost instead - one nothing in the stack runs, and
    an entry authentik refused for lacking a `config`, which rolled back the
    whole blueprint with it. Every request to /admin then answered 500.
    """
    import yaml

    class _Loader(yaml.SafeLoader):
        pass

    def _tag(loader, node):
        if isinstance(node, yaml.SequenceNode):
            return [node.tag, *loader.construct_sequence(node, deep=True)]
        return [node.tag, loader.construct_scalar(node)]

    for tag in ("!Env", "!Find", "!KeyOf", "!Format", "!Context", "!If"):
        _Loader.add_constructor(tag, _tag)

    path = ROOT / "authentik/blueprints/opencloud-admin.yaml"
    document = yaml.load(path.read_text(encoding="utf-8"), Loader=_Loader)  # nosec B506
    outposts = [e for e in document["entries"] if e["model"] == "authentik_outposts.outpost"]

    embedded = [e for e in outposts if e["identifiers"].get("managed") == "goauthentik.io/outposts/embedded"]
    assert len(embedded) == 1
    entry = embedded[0]
    # `created` would do nothing: the embedded outpost always exists already.
    assert entry.get("state", "present") == "present"
    assert entry["attrs"]["providers"] == [["!KeyOf", "admin-provider"]]
    # Where the outpost sends a browser; empty, that is http://localhost.
    assert entry["attrs"]["config"]["authentik_host"][:2] == ["!Env", "COS_AUTHENTIK_URL"]

    # No outpost is created that would need a deployment of its own, and the
    # one an earlier version created is removed rather than left unhealthy.
    for other in outposts:
        if other is entry:
            continue
        assert other["state"] == "absent", other

    # Both stacks that mount this blueprint give it the address to use.
    compose = yaml.safe_load(
        (ROOT / "docker/docker-compose.authentik.yml").read_text(encoding="utf-8")
    )
    for name in ("authentik_server", "authentik_worker"):
        environment = compose["services"][name]["environment"]
        assert environment["COS_AUTHENTIK_URL"].startswith("${AUTHENTIK_URL:-")
        assert environment["COS_WEB_ADMIN_URL"].startswith("${COS_WEB_PUBLIC_BASE_URL:-")


def _load_blueprint(name: str) -> dict:
    """A blueprint with authentik's tags kept as ``[tag, *arguments]`` lists."""
    import yaml

    class _Loader(yaml.SafeLoader):
        pass

    def _tag(loader, node):
        if isinstance(node, yaml.SequenceNode):
            return [node.tag, *loader.construct_sequence(node, deep=True)]
        return [node.tag, loader.construct_scalar(node)]

    for tag in ("!Env", "!Find", "!KeyOf", "!Format", "!Context", "!If", "!Condition"):
        _Loader.add_constructor(tag, _tag)

    path = ROOT / "authentik/blueprints" / name
    return yaml.load(path.read_text(encoding="utf-8"), Loader=_Loader)  # nosec B506


def test_every_sign_in_requires_a_second_factor_and_one_is_enrolled_rather_than_skipped():
    """
    Authentik's default flow checks a second factor only for somebody who has one.

    Shipped, `default-authentication-mfa-validation` *skips* an account without
    an authenticator - on a fresh directory, everybody. The blueprint turns that
    stage itself to *configure*, so a person is taken through enrolling TOTP or
    WebAuthn before the sign-in completes, and it is re-applied rather than
    created once, so the requirement cannot be switched off and forgotten.
    """
    document = _load_blueprint("opencloud-mfa.yaml")
    stages = [
        e
        for e in document["entries"]
        if e["model"] == "authentik_stages_authenticator_validate.authenticatorvalidatestage"
    ]
    assert len(stages) == 1
    stage = stages[0]
    # The default flow's own stage, not a second one that would ask twice.
    assert stage["identifiers"] == {"name": "default-authentication-mfa-validation"}
    assert stage["state"] == "present"
    assert stage["attrs"]["not_configured_action"] == "configure"
    assert stage["attrs"]["not_configured_action"] not in {"skip", "deny"}

    offered = {item[2][1] for item in stage["attrs"]["configuration_stages"]}
    assert offered == {"default-authenticator-totp-setup", "default-authenticator-webauthn-setup"}
    assert {"totp", "webauthn"} <= set(stage["attrs"]["device_classes"])
    # Nothing here can enrol these, so nothing should advertise them.
    assert not {"sms", "duo", "email"} & set(stage["attrs"]["device_classes"])

    # Ordered after the default blueprints that create what it looks up.
    required = {
        e["attrs"]["identifiers"]["name"]
        for e in document["entries"]
        if e["model"] == "authentik_blueprints.metaapplyblueprint"
    }
    assert {
        "Default - Authentication flow",
        "Default - TOTP MFA setup flow",
        "Default - WebAuthn MFA setup flow",
    } <= required


def test_the_enrollment_link_admits_only_the_listed_names_and_enrols_a_factor_first():
    """
    The link is how a person gets an account without anybody clicking one.

    That makes it a way in for whoever reads it unless three things hold: the
    invitation behind it is keyed by the secret token from `.env` and absent
    without one, a username not on COS_AUTHENTIK_ACCOUNTS is refused at the
    form, and the second factor is enrolled before the login stage issues a
    session. The invitation is not single-use, because deleting it after the
    first person would leave the rest of the list without a way in - the
    `username` field type, which refuses an existing name, is what makes each
    name claimable once.
    """
    document = _load_blueprint("opencloud-enrollment.yaml")
    entries = document["entries"]

    invitations = [e for e in entries if e["model"] == "authentik_stages_invitation.invitation"]
    assert len(invitations) == 1
    invitation = invitations[0]
    assert invitation["identifiers"]["pk"][:2] == ["!Env", "COS_AUTHENTIK_ENROLLMENT_TOKEN"]
    assert invitation["conditions"] == [["!If", ["!Env", "COS_AUTHENTIK_ENROLLMENT_TOKEN", ""]]]
    assert invitation["attrs"]["single_use"] is False
    # No token in the file itself.
    assert not re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        (ROOT / "authentik/blueprints/opencloud-enrollment.yaml").read_text(encoding="utf-8"),
    )

    invitation_stage = next(
        e for e in entries if e["model"] == "authentik_stages_invitation.invitationstage"
    )
    assert invitation_stage["attrs"]["continue_flow_without_invitation"] is False

    username = next(
        e for e in entries
        if e["model"] == "authentik_stages_prompt.prompt" and e["attrs"]["field_key"] == "username"
    )
    assert username["attrs"]["type"] == "username", "a plain text field would allow a name twice"

    # The order of the flow: invitation, form, account, second factor, session.
    bindings = sorted(
        (e for e in entries if e["model"] == "authentik_flows.flowstagebinding"),
        key=lambda e: e["identifiers"]["order"],
    )
    stage_of = [b["identifiers"]["stage"] for b in bindings]
    assert stage_of[0] == ["!KeyOf", "invitation-stage"]
    mfa = stage_of.index(
        [
            "!Find",
            "authentik_stages_authenticator_validate.authenticatorvalidatestage",
            ["name", "default-authentication-mfa-validation"],
        ]
    )
    login = stage_of.index(
        ["!Find", "authentik_stages_user_login.userloginstage", ["name", "default-authentication-login"]]
    )
    assert stage_of.index(["!KeyOf", "write-stage"]) < mfa < login

    # The listed-name check, executed the way authentik runs an expression.
    policy = next(
        e for e in entries
        if e["model"] == "authentik_policies_expression.expressionpolicy"
        and e["id"] == "policy-listed-username"
    )
    prompt_stage = next(e for e in entries if e["model"] == "authentik_stages_prompt.promptstage")
    assert prompt_stage["attrs"]["validation_policies"] == [["!KeyOf", "policy-listed-username"]]

    def allowed(name: str, listed: str) -> bool:
        import os
        from types import SimpleNamespace
        from unittest import mock

        source = "def result():\n" + "".join(
            f"    {line}\n" for line in policy["attrs"]["expression"].splitlines()
        )
        scope = {
            "request": SimpleNamespace(context={"prompt_data": {"username": name}}),
            "ak_message": lambda _message: None,
        }
        with mock.patch.dict(os.environ, {"COS_AUTHENTIK_ACCOUNTS": listed}):
            exec(compile(source, "policy", "exec"), scope)  # nosec B102 - the file under test
            return scope["result"]()

    assert allowed("alice", "alice;okko")
    assert allowed("okko", " alice ; okko ")
    assert not allowed("mallory", "alice;okko")
    assert not allowed("alic", "alice")
    assert not allowed("", "")
    assert not allowed("alice", "")
