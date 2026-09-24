"""Tests for scripts/verify_export.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from webapp.export_signing import sign_bytes

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "verify_export", REPO_ROOT / "scripts" / "verify_export.py"
)
assert SPEC and SPEC.loader
script = importlib.util.module_from_spec(SPEC)
sys.modules["verify_export"] = script
SPEC.loader.exec_module(script)

KEY = "test-export-signing-key"
BODY = b'{"rating": "A"}'
SIGNATURE = sign_bytes(BODY, KEY) or ""


@pytest.fixture
def export(tmp_path) -> Path:
    """One exported result on disk."""
    path = tmp_path / "result.json"
    path.write_bytes(BODY)
    return path


def run(monkeypatch, *arguments: str) -> int:
    """Run the script's entry point with the given command line."""
    monkeypatch.setattr(sys, "argv", ["verify_export.py", *arguments])
    return script.main()


def test_an_untouched_export_verifies(monkeypatch, export, capsys):
    """The documented check must accept the bytes the service signed."""
    monkeypatch.setenv("COS_WEB_EXPORT_SIGNING_KEY", KEY)

    assert run(monkeypatch, str(export), SIGNATURE) == 0

    assert "signature verified" in capsys.readouterr().out


def test_a_changed_export_fails(monkeypatch, export, capsys):
    """A verifier that accepts edited bytes gives false assurance."""
    monkeypatch.setenv("COS_WEB_EXPORT_SIGNING_KEY", KEY)
    export.write_bytes(BODY.replace(b"A", b"F"))

    assert run(monkeypatch, str(export), SIGNATURE) == 1

    assert "verification failed" in capsys.readouterr().err


def test_the_wrong_key_fails(monkeypatch, export):
    """A signature must only verify with the key that made it."""
    monkeypatch.setenv("COS_WEB_EXPORT_SIGNING_KEY", "another-key")

    assert run(monkeypatch, str(export), SIGNATURE) == 1


def test_a_missing_key_is_a_usage_error(monkeypatch, export, capsys):
    """Without a key nothing can be verified, so the script must not say it was."""
    monkeypatch.delenv("COS_WEB_EXPORT_SIGNING_KEY", raising=False)

    with pytest.raises(SystemExit) as raised:
        run(monkeypatch, str(export), SIGNATURE)

    assert raised.value.code == 2
    assert "COS_WEB_EXPORT_SIGNING_KEY is not set" in capsys.readouterr().err


def test_key_env_reads_the_named_variable(monkeypatch, export):
    """--key-env lets an operator keep the key under another name."""
    monkeypatch.delenv("COS_WEB_EXPORT_SIGNING_KEY", raising=False)
    monkeypatch.setenv("MY_EXPORT_KEY", KEY)

    assert run(monkeypatch, "--key-env", "MY_EXPORT_KEY", str(export), SIGNATURE) == 0
