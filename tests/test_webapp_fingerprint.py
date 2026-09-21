"""
The configuration fingerprint, as a stranger's browser sees it.

The page has one job here: show enough of each digest to compare two scans by
eye, and none of the configuration behind it. A report that carries no
fingerprint has to read as one that cannot say, never as a deployment that
never changes.
"""

from __future__ import annotations

import json

import pytest

from opencloud_local_scan.fingerprint import GROUPS, build
from webapp.catalog import summarise
from webapp.i18n import SUPPORTED_LOCALES, Translator

pytest.importorskip("fastapi", reason="the web extra is not installed")

SECRET_CSP = "default-src 'self' https://vault.internal.example.com"


def _document(**extra: object) -> dict:
    document: dict = {"rating": 4, "extraChecks": [], "hardenings": {}, "setup": {}}
    document.update(extra)
    return document


def _fingerprinted() -> dict:
    scanned = {
        "setup": {"https": {"used": True, "enforced": True}},
        "hardenings": {"cspWithoutUnsafeInline": True},
        "identityProvider": {"detected": True, "external": True, "issuer": "https://idp.example.com"},
        "reverseProxy": {"detected": False, "vendor": ""},
        "alternativeServices": {"advertised": False, "http3": False, "entries": []},
    }
    return _document(
        configuration=build(
            scanned,
            headers={"Content-Security-Policy": SECRET_CSP},
            capabilities={"capabilities": {"files_sharing": {"public": {}}}},
        )
    )


def test_the_page_gets_every_group_with_a_short_digest():
    fingerprint = summarise(_fingerprinted())["fingerprint"]

    assert fingerprint["available"] is True
    assert [group["group"] for group in fingerprint["groups"]] == list(GROUPS)
    assert all(len(group["digest"]) in {0, 8} for group in fingerprint["groups"])
    assert len(fingerprint["digest"]) == 8


def test_nothing_the_scan_read_reaches_the_page():
    """A published page must never carry the policy it hashed."""
    rendered = json.dumps(summarise(_fingerprinted())["fingerprint"])

    assert SECRET_CSP not in rendered
    assert "vault.internal.example.com" not in rendered
    assert "idp.example.com" not in rendered


def test_a_group_with_nothing_measured_is_shown_as_such():
    fingerprint = summarise(_fingerprinted())["fingerprint"]
    sharing = next(group for group in fingerprint["groups"] if group["group"] == "sharing")

    assert sharing["measured"] is True

    bare = summarise(
        _document(configuration=build({}, headers=None, capabilities=None))
    )["fingerprint"]
    empty = next(group for group in bare["groups"] if group["group"] == "sharing")

    assert empty["measured"] is False
    assert empty["digest"] == ""


def test_a_report_without_a_fingerprint_is_not_a_deployment_that_held_still():
    fingerprint = summarise(_document())["fingerprint"]

    assert fingerprint["available"] is False
    assert fingerprint["groups"] == []


@pytest.mark.parametrize("locale", sorted(SUPPORTED_LOCALES))
def test_every_language_names_the_five_groups(locale):
    """A digest with no label beside it tells a reader nothing."""
    translate = Translator(locale)

    for group in GROUPS:
        label = translate(f"fingerprint.group.{group}")
        assert label and not label.startswith("fingerprint.")
    assert "{digest}" not in translate("result.fingerprint.overall", digest="ab12cd34")
