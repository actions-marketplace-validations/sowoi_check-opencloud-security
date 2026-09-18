"""
The Docker setup wizard when the ground under it is not what it expects.

``test_docker_wizard.py`` protects what the wizard writes on an ordinary
run. These protect it against the rest: a symbolic link where a file
belongs, an answers file or `.env` somebody else edited, input that runs out
or is interrupted, and answers the prompt has to turn away. Each of those
failing is either a credential written somewhere nobody named, a compose
file Docker cannot read, or a traceback where a sentence belonged.
"""

from __future__ import annotations

import io
import json
import os
import stat
from pathlib import Path

import pytest
import yaml

from tests.test_docker_wizard import (  # noqa: F401 - the autouse fixture registers under its own name
    _compose,
    _env,
    _run,
    _the_host_stays_out_of_it,
    wizard_module,
)

ANSWERS = ".docker-compose.yml.answers.json"


def _question(key: str):
    for section in wizard_module.build_sections(wizard_module.Setup()):
        for question in section.questions:
            if question.key == key:
                return question
    raise AssertionError(f"no question for {key}")


# ------------------------------------------------------------------ security


def test_a_dangling_link_in_place_of_the_env_file_is_refused(tmp_path: Path, capsys) -> None:
    """A link to a file that does not exist yet is not 'no file': the secrets must not follow it."""
    output = tmp_path / "out"
    output.mkdir()
    elsewhere = tmp_path / "elsewhere.env"
    (output / ".env").symlink_to(elsewhere)

    assert _run(output) == 1

    assert not elsewhere.exists()
    assert not (output / "docker-compose.yml").exists()
    assert "symbolic link" in capsys.readouterr().err


def test_force_does_not_write_through_a_link_to_an_existing_file(tmp_path: Path) -> None:
    """--force answers the overwrite question; it does not make a link the file it points at."""
    output = tmp_path / "out"
    output.mkdir()
    target = tmp_path / "someone-elses.txt"
    target.write_text("keep me\n", encoding="utf-8")
    (output / ".env").symlink_to(target)

    assert _run(output, "--force") == 1

    assert target.read_text(encoding="utf-8") == "keep me\n"


def test_a_link_in_place_of_the_compose_file_is_refused(tmp_path: Path) -> None:
    """The compose file is refused as a link too, so nothing outside the directory is replaced."""
    output = tmp_path / "out"
    output.mkdir()
    target = tmp_path / "unrelated.yml"
    target.write_text("# not ours\n", encoding="utf-8")
    (output / "docker-compose.yml").symlink_to(target)

    assert _run(output, "--force") == 1

    assert target.read_text(encoding="utf-8") == "# not ours\n"
    assert not (output / ".env").exists()


def test_the_env_file_is_never_opened_through_a_link(tmp_path: Path) -> None:
    """Below main(), write_files itself refuses a link: the flag is on the open, not only on the check."""
    target = tmp_path / "stolen.env"
    link = tmp_path / ".env"
    link.symlink_to(target)

    with pytest.raises(OSError):
        wizard_module.write_files(wizard_module.Setup(), tmp_path / "docker-compose.yml", link)

    assert not target.exists()


def test_an_ordinary_run_still_writes_an_owner_only_env_file(tmp_path: Path) -> None:
    """The negative case: without a link in the way, the refusal costs nothing."""
    assert _run(tmp_path) == 0

    mode = stat.S_IMODE(os.stat(tmp_path / ".env").st_mode)
    assert mode == 0o600
    assert _env(tmp_path)["COS_WEB_PURGE_TOKEN"]


def test_a_newline_in_a_remembered_answer_cannot_rewrite_the_compose_file(tmp_path: Path) -> None:
    """An edited answers file is untrusted: a value that could not be typed at the prompt is dropped."""
    assert _run(tmp_path) == 0
    answers_path = tmp_path / ANSWERS
    answers = json.loads(answers_path.read_text(encoding="utf-8"))
    for name, value in answers.items():
        if isinstance(value, str) and not name.startswith("_"):
            answers[name] = value + "\n    INJECTED: yes"
    answers_path.write_text(json.dumps(answers), encoding="utf-8")

    assert _run(tmp_path, "--force") == 0

    text = (tmp_path / "docker-compose.yml").read_text(encoding="utf-8")
    assert "INJECTED" not in text
    assert "INJECTED" not in (tmp_path / ".env").read_text(encoding="utf-8")
    yaml.safe_load(text)


def test_a_remembered_answer_outside_its_choices_is_dropped(tmp_path: Path) -> None:
    """A choice question only ever takes one of its choices, whatever the notebook says."""
    assert _run(tmp_path) == 0
    answers_path = tmp_path / ANSWERS
    answers = json.loads(answers_path.read_text(encoding="utf-8"))
    answers["image_source"] = "evil-registry"
    answers_path.write_text(json.dumps(answers), encoding="utf-8")

    assert _run(tmp_path, "--force") == 0

    web = _compose(tmp_path)["services"]["web_app"]
    assert web["image"] == wizard_module.DOCKERHUB_IMAGE


def test_a_valid_remembered_answer_is_still_taken(tmp_path: Path) -> None:
    """The negative case: an answer the prompt would accept is carried into the next run."""
    assert _run(tmp_path) == 0
    answers_path = tmp_path / ANSWERS
    answers = json.loads(answers_path.read_text(encoding="utf-8"))
    answers["project_name"] = "scanner-two"
    answers_path.write_text(json.dumps(answers), encoding="utf-8")

    assert _run(tmp_path, "--force") == 0

    answers = json.loads((tmp_path / ANSWERS).read_text(encoding="utf-8"))
    assert answers["project_name"] == "scanner-two"


def test_a_secret_in_the_answers_file_is_never_read_back(tmp_path: Path) -> None:
    """Credentials come from .env alone; one planted in the notebook does not reach .env."""
    assert _run(tmp_path) == 0
    before = _env(tmp_path)["COS_WEB_PURGE_TOKEN"]
    answers_path = tmp_path / ANSWERS
    answers = json.loads(answers_path.read_text(encoding="utf-8"))
    answers["purge_token"] = "planted"
    answers_path.write_text(json.dumps(answers), encoding="utf-8")

    assert _run(tmp_path, "--force") == 0

    assert _env(tmp_path)["COS_WEB_PURGE_TOKEN"] == before
    assert "planted" not in (tmp_path / ".env").read_text(encoding="utf-8")


# ---------------------------------------------------------------- robustness


@pytest.mark.parametrize(
    "content",
    [b"", b"{", b"[1, 2]", b"null", b'"text"', b"\xff\xfe\x80 not utf-8", b'{"host_port": true}'],
)
def test_an_unreadable_answers_file_starts_from_the_defaults(tmp_path: Path, content: bytes) -> None:
    """A notebook nobody can read is one nobody wrote: the run goes on with the defaults."""
    (tmp_path / ANSWERS).write_bytes(content)

    assert _run(tmp_path, "--force") == 0

    assert _compose(tmp_path)["services"]["web_app"]["ports"] == ["127.0.0.1:8811:8811"]


def test_an_env_file_that_is_not_text_stops_the_run_instead_of_replacing_it(tmp_path: Path, capsys) -> None:
    """Regenerating every credential over an unreadable .env would break what depends on them."""
    original = b"COS_WEB_PURGE_TOKEN=\xff\xfe\x80\n"
    (tmp_path / ".env").write_bytes(original)

    assert _run(tmp_path, "--force") == 2

    assert (tmp_path / ".env").read_bytes() == original
    assert not (tmp_path / "docker-compose.yml").exists()
    error = capsys.readouterr().err
    assert "cannot be read" in error
    assert "Traceback" not in error


def test_an_env_file_with_stray_lines_keeps_the_credentials_it_holds(tmp_path: Path) -> None:
    """Comments, blank lines, unknown names and a line without '=' are passed over, not fatal."""
    token = "a" * 64
    (tmp_path / ".env").write_text(
        f"# a comment\n\nnot a pair\nUNRELATED=1\n=nothing\nCOS_WEB_PURGE_TOKEN=\"{token}\"\n",
        encoding="utf-8",
    )

    assert _run(tmp_path, "--force") == 0

    assert _env(tmp_path)["COS_WEB_PURGE_TOKEN"] == token


@pytest.mark.parametrize(("raised", "said"), [(EOFError, "No more input."), (KeyboardInterrupt, "Interrupted.")])
def test_input_that_ends_mid_walk_aborts_cleanly_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys, raised, said
) -> None:
    """Ctrl-D or Ctrl-C at a prompt is a sentence and exit 1, never a traceback or a half-written file."""

    def ends(prompt: str = "") -> str:
        raise raised

    monkeypatch.setattr("builtins.input", ends)

    assert wizard_module.main(["--output-dir", str(tmp_path)]) == 1

    assert list(tmp_path.iterdir()) == []
    error = capsys.readouterr().err
    assert f"Setup aborted: {said}" in error
    assert "Traceback" not in error


def test_a_second_run_over_its_own_output_changes_nothing(tmp_path: Path) -> None:
    """Re-running with the same answers is an edit that edits nothing: same compose file, same secrets."""
    assert _run(tmp_path) == 0
    compose = (tmp_path / "docker-compose.yml").read_text(encoding="utf-8")
    secrets = _env(tmp_path)

    assert _run(tmp_path, "--force") == 0

    assert (tmp_path / "docker-compose.yml").read_text(encoding="utf-8") == compose
    assert _env(tmp_path) == secrets


# ------------------------------------------------------------------------ ux


def _ask(monkeypatch: pytest.MonkeyPatch, key: str, typed: list[str]):
    setup = wizard_module.Setup()
    wizard = wizard_module.Wizard(setup, style=wizard_module.Style(enabled=False))
    answers = iter(typed)
    monkeypatch.setattr(wizard_module.Wizard, "_read", lambda self, prompt: next(answers))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    wizard.ask(_question(key), offer_rest=False)
    return setup, out.getvalue()


def test_a_port_the_prompt_cannot_take_is_explained_and_asked_again(monkeypatch: pytest.MonkeyPatch) -> None:
    """A wrong answer costs one more line, not the run: the reason is shown and the question stays open."""
    setup, said = _ask(monkeypatch, "host_port", ["not a port", "99999", "8080"])

    assert setup.host_port == 8080
    refusals = [line for line in said.splitlines() if line.strip().startswith("!")]
    assert len(refusals) == 2
    assert "65535" in refusals[1]


def test_a_choice_can_be_given_by_its_number(monkeypatch: pytest.MonkeyPatch) -> None:
    """The numbers printed beside the choices are answers too."""
    question = _question("image_source")
    setup, _ = _ask(monkeypatch, "image_source", [str(question.choices.index("build") + 1)])

    assert setup.image_source == "build"


def test_an_unknown_choice_is_refused_and_the_default_kept(monkeypatch: pytest.MonkeyPatch) -> None:
    """The negative case: a word that is no choice changes nothing, and Enter then keeps the default."""
    setup, said = _ask(monkeypatch, "image_source", ["evil-registry", ""])

    assert setup.image_source == wizard_module.Setup().image_source
    assert "evil-registry" not in _compose_text_or_empty(setup)
    assert said


def _compose_text_or_empty(setup) -> str:
    return wizard_module.render_compose_file(setup)


def test_a_credential_already_set_is_never_printed_at_its_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """A re-run reads .env back; its prompt says a value is set and never shows it."""
    setup = wizard_module.Setup()
    setup.purge_token = "s3cret-value-from-env"
    wizard = wizard_module.Wizard(setup, style=wizard_module.Style(enabled=False))
    monkeypatch.setattr(wizard_module.Wizard, "_read_secret", lambda self, prompt: "")
    monkeypatch.setattr(wizard_module.Wizard, "_read", lambda self, prompt: "")
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)

    wizard.ask(_question("purge_token"), offer_rest=False)

    assert "s3cret-value-from-env" not in out.getvalue()
    assert setup.purge_token == "s3cret-value-from-env"


def test_help_describes_the_unattended_flags_and_exits_cleanly(capsys) -> None:
    """--help is how an operator scripting the wizard learns it can be scripted."""
    with pytest.raises(SystemExit) as raised:
        wizard_module.main(["--help"])

    assert raised.value.code == 0
    text = capsys.readouterr().out
    for flag in ("--non-interactive", "--force", "--output-dir", "--answers"):
        assert flag in text
