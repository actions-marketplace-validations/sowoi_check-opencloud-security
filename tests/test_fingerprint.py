"""
The configuration fingerprint: drift an operator can see, secrets they cannot.

The block earns its place only if three things hold. It must change when the
deployment is configured differently, it must not change when nothing was
decided differently, and it must never carry the configuration itself - a
report is published, and a content security policy names the origins a
deployment trusts.
"""

from __future__ import annotations

import json

import pytest

from opencloud_local_scan.fingerprint import (
    AUTHENTICATION,
    FINGERPRINTED_HEADERS,
    GROUPS,
    HEADERS,
    NOT_MEASURED,
    PROXY,
    SHARING,
    TLS,
    build,
    digests,
    drift,
    fingerprint_of,
    incomparable,
    unmeasured,
)
from opencloud_local_scan.scanner import ScannerSettings, scan
from tests.fake_opencloud import FakeOpenCloud, InstanceBehaviour

SECRET_CSP = "default-src 'self' https://vault.internal.example.com"

DOCUMENT = {
    "setup": {"https": {"used": True, "enforced": True}},
    "hardenings": {"cspWithoutUnsafeInline": True, "basicAuthDisabled": True},
    "identityProvider": {"detected": True, "external": True, "issuer": "https://idp.example.com"},
    "reverseProxy": {"detected": True, "vendor": "nginx", "evidence": "nginx/1.25.3"},
    "alternativeServices": {"advertised": True, "http3": True, "entries": ["h3"]},
    "tls": None,
    "tlsByAddress": {},
}

HEADER_VALUES = {
    "Content-Security-Policy": SECRET_CSP,
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "X-Frame-Options": "SAMEORIGIN",
}

CAPABILITIES = {
    "capabilities": {
        "files_sharing": {"public": {"password": {"enforced": True}}},
        "core": {"password_policy": {"min_characters": 12}},
    }
}


def _built(**changes: object) -> dict:
    document = json.loads(json.dumps(DOCUMENT))
    document.update(changes)
    return build(document, headers=dict(HEADER_VALUES), capabilities=CAPABILITIES)


def test_the_same_deployment_fingerprints_the_same_every_time():
    """A digest that moved on its own would be one nobody could act on."""
    assert _built() == _built()


def test_every_group_is_present_and_named_once():
    block = _built()

    assert tuple(block["groups"]) == GROUPS
    assert block["schema"] == 1
    assert all(entry["digest"] != NOT_MEASURED for entry in block["groups"].values())


def test_nothing_in_the_block_is_the_configuration_itself():
    """
    The one property that makes this safe to publish.

    The header values, the issuer, the proxy banner and the capabilities
    document are all fed in; none of them, nor any fragment of them, may come
    back out.
    """
    rendered = json.dumps(_built())

    for secret in (
        SECRET_CSP,
        "vault.internal.example.com",
        "idp.example.com",
        "nginx/1.25.3",
        "min_characters",
        "max-age=31536000",
    ):
        assert secret not in rendered


def test_a_changed_header_value_changes_only_the_header_group():
    """Grouping is the whole point: "headers changed" has to mean that."""
    before = _built()
    after = build(
        DOCUMENT,
        headers={**HEADER_VALUES, "Content-Security-Policy": "default-src 'self'"},
        capabilities=CAPABILITIES,
    )

    assert drift(_group_digests(before), _group_digests(after)) == (HEADERS,)


def test_a_header_rewritten_with_different_spacing_is_not_a_change():
    """An operator who reformatted a policy did not change it."""
    after = build(
        DOCUMENT,
        headers={**HEADER_VALUES, "X-Frame-Options": "  sameorigin  "},
        capabilities=CAPABILITIES,
    )

    assert _group_digests(after) == _group_digests(_built())


def test_the_groups_a_change_belongs_to_are_the_ones_that_move():
    """A setting that changed has to move its own group, and be found there."""
    cases: dict[str, dict] = {
        SHARING: {
            "capabilities": {
                "files_sharing": {"public": {"password": {"enforced": False}}},
                "core": {"password_policy": {"min_characters": 12}},
            }
        },
        AUTHENTICATION: {
            "capabilities": {
                "files_sharing": {"public": {"password": {"enforced": True}}},
                "core": {"password_policy": {"min_characters": 8}},
            }
        },
    }
    for group, capabilities in cases.items():
        after = build(DOCUMENT, headers=dict(HEADER_VALUES), capabilities=capabilities)
        assert drift(_group_digests(_built()), _group_digests(after)) == (group,)


def test_a_different_proxy_is_proxy_drift():
    document = json.loads(json.dumps(DOCUMENT))
    document["reverseProxy"] = {"detected": True, "vendor": "traefik", "evidence": ""}

    after = build(document, headers=dict(HEADER_VALUES), capabilities=CAPABILITIES)

    assert drift(_group_digests(_built()), _group_digests(after)) == (PROXY,)


def test_a_proxy_that_only_moved_a_build_number_is_not_drift():
    """
    The evidence quotes a server banner, which a patch release rewrites.

    A fingerprint that moved on every upstream patch would teach an operator
    to ignore it, which is worse than not having one.
    """
    document = json.loads(json.dumps(DOCUMENT))
    document["reverseProxy"] = {"detected": True, "vendor": "nginx", "evidence": "nginx/1.27.0"}

    after = build(document, headers=dict(HEADER_VALUES), capabilities=CAPABILITIES)

    assert drift(_group_digests(_built()), _group_digests(after)) == ()


def test_a_renewed_certificate_is_not_a_configuration_change():
    """Renewal is routine; the issuer and the key are the decisions."""
    first = _with_certificate(serial="01", not_after="2026-01-01", issuer="Example CA")
    renewed = _with_certificate(serial="02", not_after="2026-04-01", issuer="Example CA")

    assert drift(_group_digests(first), _group_digests(renewed)) == ()

    moved = _with_certificate(serial="02", not_after="2026-04-01", issuer="Other CA")

    assert drift(_group_digests(first), _group_digests(moved)) == (TLS,)


def _with_certificate(*, serial: str, not_after: str, issuer: str) -> dict:
    document = json.loads(json.dumps(DOCUMENT))
    document["tls"] = {
        "reachable": True,
        "protocol": "TLSv1.3",
        "cipher": "TLS_AES_256_GCM_SHA384",
        "chainLength": 2,
        "deprecatedProtocolsAccepted": [],
        "certificate": {
            "issuer": issuer,
            "serialNumber": serial,
            "notAfter": not_after,
            "keyType": "EC",
            "keyBits": 256,
            "signatureAlgorithm": "ecdsa-with-SHA384",
            "selfSigned": False,
        },
    }
    return build(document, headers=dict(HEADER_VALUES), capabilities=CAPABILITIES)


def _group_digests(block: dict) -> dict[str, str]:
    """The combined scope-and-digest strings a comparison is given."""
    return {
        group: f"{entry['scope']}:{entry['digest']}"
        for group, entry in block["groups"].items()
    }


def test_a_group_with_nothing_to_measure_is_not_a_group_that_changed():
    """
    A probe that was turned off must not read as a redeployment.

    This is the failure mode the ``none`` marker exists for: without it, the
    first scan with the extra checks disabled would report drift in every
    group it stopped feeding.
    """
    without = build(DOCUMENT, headers=None, capabilities=None)

    # Sharing had nothing at all to hash without the capabilities document.
    assert without["groups"][SHARING]["digest"] == NOT_MEASURED
    assert SHARING in unmeasured(_group_digests(without))
    # The headers group still has a hardening flag in it, so it is not empty
    # - but it looked at fewer facts, which is reported as not comparable and
    # never as a deployment that changed.
    assert drift(_group_digests(_built()), _group_digests(without)) == ()
    assert HEADERS in incomparable(_group_digests(_built()), _group_digests(without))


def test_the_overall_digest_moves_with_any_group():
    after = build(
        DOCUMENT,
        headers={**HEADER_VALUES, "Referrer-Policy": "no-referrer"},
        capabilities=CAPABILITIES,
    )

    assert after["digest"] != _built()["digest"]


def test_a_report_without_the_block_says_so_rather_than_claiming_stability():
    assert fingerprint_of({}) is None
    assert fingerprint_of({"configuration": {"groups": {}}}) is None
    assert digests({}) == {}
    assert drift({}, {}) == ()


@pytest.mark.parametrize("name", FINGERPRINTED_HEADERS)
def test_every_fingerprinted_header_is_actually_hashed(name):
    """A header in the list that nothing reads would be a promise not kept."""
    after = build(DOCUMENT, headers={name: "something-else"}, capabilities=CAPABILITIES)

    assert after["groups"][HEADERS]["digest"] != build(
        DOCUMENT, headers={}, capabilities=CAPABILITIES
    )["groups"][HEADERS]["digest"]


# --- through a real scan ---
def test_a_real_scan_carries_a_fingerprint_for_every_group():
    with FakeOpenCloud() as fake:
        result = scan(fake.host, ScannerSettings(verify_tls=False, extra_checks=True))

    block = fingerprint_of(result)

    assert block is not None
    assert set(block["groups"]) == set(GROUPS)
    assert block["groups"][HEADERS]["digest"] != NOT_MEASURED


def test_a_changed_instance_drifts_and_an_unchanged_one_does_not():
    """The end-to-end claim, measured rather than constructed."""
    behaviour = InstanceBehaviour()
    with FakeOpenCloud(behaviour) as fake:
        settings = ScannerSettings(verify_tls=False, extra_checks=True)
        first = scan(fake.host, settings)
        again = scan(fake.host, settings)

    assert drift(digests(first), digests(again)) == ()

    changed = InstanceBehaviour()
    changed.headers["Referrer-Policy"] = "unsafe-url"
    with FakeOpenCloud(changed) as fake:
        after = scan(fake.host, ScannerSettings(verify_tls=False, extra_checks=True))

    assert HEADERS in drift(digests(first), digests(after))


def test_the_fingerprint_never_moves_a_grade():
    """
    Drift is reported, never judged.

    Two instances that differ only in a fingerprinted-but-unrated header get
    the same rating and the same explanation; only the digest differs.
    """
    plain = InstanceBehaviour()
    other = InstanceBehaviour()
    other.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"

    with FakeOpenCloud(plain) as fake:
        first = scan(fake.host, ScannerSettings(verify_tls=False, extra_checks=True))
    with FakeOpenCloud(other) as fake:
        second = scan(fake.host, ScannerSettings(verify_tls=False, extra_checks=True))

    assert first["rating"] == second["rating"]
    # The caps are the rating's own arithmetic; the details name the fake's
    # port, which differs between two instances and nothing here decides.
    assert [cap["check"] for cap in first["ratingExplanation"]["caps"]] == [
        cap["check"] for cap in second["ratingExplanation"]["caps"]
    ]
    assert digests(first)[HEADERS] != digests(second)[HEADERS]
