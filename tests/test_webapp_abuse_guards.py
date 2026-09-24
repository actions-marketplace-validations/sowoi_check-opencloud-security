"""
The guards that make the service a poor tool for mapping other people's hosts.

The probe block itself - scans that find no OpenCloud - lives in
``test_webapp_probe_guard.py``. These are the measures around it: counting a
network rather than an address, blocks that grow when they are earned again,
refused targets as strikes, the daily cap, names built to mislead, and the
optional approval mode. Each is exercised through the submission endpoint
where a stranger would meet it, with the negative case beside the positive.
"""

from __future__ import annotations

import asyncio
import io

import pytest
from fastapi.testclient import TestClient

from tests.webapp_support import (  # noqa: F401 - the fixtures are autouse
    _isolated_backend,
    _offline_resolver,
    backend,
    client,
    settings,
)
from webapp import approval, ssrf
from webapp.app import create_app
from webapp.ratelimit import (
    ProbePolicy,
    network_of,
    probe_block_key,
    prober_fingerprint,
    record_strike,
)

GUARDED = {"trust_forwarded_for": True, "probe_limit": 5, "probe_window": 300, "probe_block": 3600}


def _submit(test_client, target: str, address: str):
    return test_client.post(
        "/api/scans", json={"target_url": target}, headers={"X-Forwarded-For": address}
    )


# ------------------------------------------------------- networks, not addresses


def test_an_ipv6_client_is_one_client_across_its_whole_64():
    """A subscriber handed a /64 must not get a fresh allowance per address in it."""
    assert network_of("2001:db8:1:2::1", 32, 64) == network_of("2001:db8:1:2:ffff::9", 32, 64)
    assert network_of("2001:db8:1:2::1", 32, 64) != network_of("2001:db8:1:3::1", 32, 64)


def test_an_ipv4_address_is_grouped_only_as_far_as_asked():
    """The probe guard counts a /24; the per-minute limit still counts one address."""
    assert network_of("203.0.113.7", 24, 64) == network_of("203.0.113.200", 24, 64)
    assert network_of("203.0.113.7", 32, 64) == "203.0.113.7"
    assert network_of("203.0.113.7", 32, 64) != network_of("203.0.113.8", 32, 64)
    # The same host spelt as a v4-mapped IPv6 address is the same client.
    assert network_of("::ffff:203.0.113.7", 24, 64) == network_of("203.0.113.7", 24, 64)


def test_the_client_limit_follows_an_ipv6_client_through_its_64():
    """Rotating the last 64 bits must not reset the per-minute limit."""
    test_client = client(trust_forwarded_for=True, ip_rate_limit=1, ip_rate_window=60)

    first = _submit(test_client, "https://one.example.com", "2001:db8:1:2::1")
    same_network = _submit(test_client, "https://two.example.com", "2001:db8:1:2::2")
    other_network = _submit(test_client, "https://three.example.com", "2001:db8:9:9::1")

    assert first.status_code == 202
    assert same_network.status_code == 429
    assert other_network.status_code == 202


def test_the_client_limit_does_not_lump_an_ipv4_24_together():
    """Strangers sharing a /24 must not share one per-minute allowance."""
    test_client = client(trust_forwarded_for=True, ip_rate_limit=1, ip_rate_window=60)

    assert _submit(test_client, "https://one.example.com", "203.0.113.1").status_code == 202
    assert _submit(test_client, "https://two.example.com", "203.0.113.2").status_code == 202


def test_the_probe_block_covers_the_whole_network_that_earned_it():
    """Moving to the next address in the same /24 must not step around a block."""
    test_client = client(**GUARDED)

    for last in range(1, 6):
        assert _submit(test_client, "http://10.0.0.1", f"203.0.113.{last}").status_code == 400

    neighbour = _submit(test_client, "https://opencloud.example.com", "203.0.113.99")
    elsewhere = _submit(test_client, "https://opencloud.example.com", "198.51.100.1")

    assert neighbour.status_code == 429
    assert elsewhere.status_code == 202


def test_a_blocked_network_cannot_upload_a_report_either():
    """
    The block is about the client, not about one endpoint.

    A network this service has stopped scanning for does not get to hand it a
    file to parse instead: the report upload is the one parser here fed from
    outside, and it costs this service work whether or not a scan follows.
    """
    test_client = client(**GUARDED)
    for _ in range(5):
        assert _submit(test_client, "http://10.0.0.1", "203.0.113.1").status_code == 400

    refused = _upload(test_client, "203.0.113.1")

    assert refused.status_code == 429
    assert int(refused.headers["Retry-After"]) > 0
    # Nothing was read and nothing was kept: the file never reached the parser,
    # so no comparison exists to come back to.
    assert asyncio.run(backend().keys_matching("compare:*")) == []
    # And the block is the whole network's, not one address's.
    assert _upload(test_client, "203.0.113.99").status_code == 429
    # A network that earned nothing still gets as far as the uuid it named,
    # which is the 404 an unknown scan answers with everywhere.
    assert _upload(test_client, "198.51.100.1").status_code == 404


def _upload(test_client, address: str):
    """One report upload from one address, as the compare form sends it."""
    return test_client.post(
        "/compare",
        data={"current": "c7a3d1d6-2d5c-4a5f-8b4c-1e4f9c8d2b31"},
        files={"report": ("scan.json", io.BytesIO(b'{"rating": 3}'), "application/json")},
        headers={"X-Forwarded-For": address},
        follow_redirects=False,
    )


# ------------------------------------------------------------ refused targets


def test_targets_the_guard_refuses_count_towards_the_probe_block():
    """Walking private ranges through the form is probing, whatever the scan says."""
    test_client = client(**GUARDED)

    for _ in range(5):
        assert _submit(test_client, "http://10.0.0.1", "203.0.113.1").status_code == 400

    refused = _submit(test_client, "https://opencloud.example.com", "203.0.113.1")

    assert refused.status_code == 429
    assert int(refused.headers["Retry-After"]) > 3500


def test_a_typo_is_not_a_strike():
    """Mistyping an address five times is a person, not a sweep."""
    test_client = client(**GUARDED)

    for _ in range(6):
        assert _submit(test_client, "ftp://opencloud.example.com", "203.0.113.1").status_code == 400

    assert _submit(test_client, "https://opencloud.example.com", "203.0.113.1").status_code == 202


# ------------------------------------------------------------ escalating blocks


def test_each_block_earned_again_soon_lasts_longer_up_to_the_ceiling():
    """An hour, six hours, a day, and never more than the ceiling."""
    policy = ProbePolicy(limit=5, window=300, block=3600, block_max=86400, repeat_window=86400)

    assert [policy.duration(repeat) for repeat in (1, 2, 3, 4)] == [3600, 21600, 86400, 86400]


def _earn_block(prober: str, policy: ProbePolicy):
    outcome = None
    for _ in range(policy.limit):
        outcome = asyncio.run(record_strike(backend(), prober, policy))
    return outcome


def test_a_network_that_comes_straight_back_is_blocked_for_longer():
    """
    The first block is the warning; the second must cost more.

    And a network that stays away for the repeat window starts again at an
    hour, or one bad afternoon would be held against it for ever.
    """
    policy = ProbePolicy(limit=5, window=300, block=3600, block_max=86400, repeat_window=86400)
    prober = prober_fingerprint("203.0.113.0/24", "salt")

    first = _earn_block(prober, policy)
    backend().advance(3601)
    second = _earn_block(prober, policy)
    remaining = asyncio.run(backend().ttl(probe_block_key(prober)))

    assert first.blocked and first.duration == 3600
    assert second.blocked and second.duration == 21600
    assert 21500 < remaining <= 21600

    backend().advance(21600 + 86400 + 1)
    forgiven = _earn_block(prober, policy)
    assert forgiven.blocked and forgiven.duration == 3600


def test_strikes_during_a_block_do_not_escalate_it():
    """Queued scans finishing during a block must not stretch it into the next tier."""
    policy = ProbePolicy(limit=5, window=300, block=3600, block_max=86400, repeat_window=86400)
    prober = prober_fingerprint("203.0.113.0/24", "salt")

    _earn_block(prober, policy)
    late = _earn_block(prober, policy)

    assert late.blocked is False
    assert asyncio.run(backend().ttl(probe_block_key(prober))) <= 3600


# ------------------------------------------------------------------ daily cap


def test_the_daily_cap_refuses_the_patient_version_of_a_burst():
    """Staying under the per-minute limit all night must still run out."""
    test_client = client(trust_forwarded_for=True, daily_scan_limit=3)

    accepted = [
        _submit(test_client, f"https://i{n}.example.com", "203.0.113.1").status_code
        for n in range(3)
    ]
    refused = _submit(test_client, "https://i9.example.com", "203.0.113.1")
    other = _submit(test_client, "https://i9.example.com", "198.51.100.1")

    assert accepted == [202, 202, 202]
    assert refused.status_code == 429
    assert int(refused.headers["Retry-After"]) > 3600
    assert refused.json()["selfHostUrl"]
    assert other.status_code == 202


def test_the_daily_cap_ends_with_its_day():
    """A cap that never lifts is a ban nobody decided on."""
    test_client = client(trust_forwarded_for=True, daily_scan_limit=1)
    _submit(test_client, "https://one.example.com", "203.0.113.1")
    assert _submit(test_client, "https://two.example.com", "203.0.113.1").status_code == 429

    backend().advance(86401)

    assert _submit(test_client, "https://two.example.com", "203.0.113.1").status_code == 202


# ------------------------------------------------------ names built to mislead


@pytest.mark.parametrize("name", ["10.0.0.1.nip.io", "127-0-0-1.sslip.io", "a.b.1u.ms", "nip.io"])
def test_wildcard_and_rebinding_dns_names_are_refused_by_name(name):
    """Such a name exists to point somewhere its reader did not expect."""
    with pytest.raises(ssrf.TargetRejected) as caught:
        ssrf.validate_target(f"https://{name}")

    assert caught.value.key == "error.target.wildcard_dns"


def test_a_name_that_merely_contains_a_wildcard_service_is_not_refused():
    """``nip.io.example.com`` is somebody's own zone, not the wildcard service."""
    target = ssrf.validate_target("https://nip.io.example.com")

    assert target.hostname == "nip.io.example.com"


def test_a_deployment_scanning_its_own_network_may_use_a_wildcard_name(monkeypatch):
    """With private targets allowed there is no guard for such a name to walk past."""
    monkeypatch.setattr(ssrf, "_resolve", lambda host: [ssrf.ipaddress.ip_address("10.0.0.1")])

    target = ssrf.validate_target("https://10.0.0.1.nip.io", allow_private=True)

    assert target.addresses == ("10.0.0.1",)


def _answers(monkeypatch, *answers: str):
    queue = [[ssrf.ipaddress.ip_address(value)] for value in answers]
    monkeypatch.setattr(ssrf, "_resolve", lambda host: queue.pop(0))


def test_a_name_that_answers_differently_each_time_is_refused(monkeypatch):
    """Two lookups that share nothing mean nobody knows what would be scanned."""
    _answers(monkeypatch, "203.0.113.10", "198.51.100.20")

    with pytest.raises(ssrf.TargetRejected) as caught:
        ssrf.validate_target("https://flip.example.com", check_consistency=True)

    assert caught.value.key == "error.target.unstable"


def test_a_second_answer_is_held_to_the_same_rules_as_the_first(monkeypatch):
    """A name that answers public, then public and private, is private."""
    queue = [
        [ssrf.ipaddress.ip_address("203.0.113.10")],
        [ssrf.ipaddress.ip_address("203.0.113.10"), ssrf.ipaddress.ip_address("10.0.0.7")],
    ]
    monkeypatch.setattr(ssrf, "_resolve", lambda host: queue.pop(0))

    with pytest.raises(ssrf.TargetRejected) as caught:
        ssrf.validate_target("https://flip.example.com", check_consistency=True)

    assert caught.value.key == "error.target.private"


def test_a_stable_name_passes_and_the_check_is_only_made_when_asked(monkeypatch):
    """Overlapping answers are ordinary DNS; the worker's own lookup is not doubled."""
    _answers(monkeypatch, "203.0.113.10", "203.0.113.10")
    assert ssrf.validate_target("https://stable.example.com", check_consistency=True)

    _answers(monkeypatch, "203.0.113.10", "198.51.100.20")
    assert ssrf.validate_target("https://flip.example.com")


# --------------------------------------------------------------- approval mode


def _approval(**overrides):
    return settings(require_approval=True, **overrides)


def _client_for(configured) -> TestClient:
    return TestClient(create_app(configured))


def test_approval_mode_scans_only_what_the_operator_listed(monkeypatch):
    """Anything unlisted is refused, and a listed suffix covers its subdomains."""
    monkeypatch.setattr(approval, "txt_records", lambda name, timeout=3.0: [])
    test_client = _client_for(_approval(approved_targets=(".example.org", "opencloud.example.com")))

    assert test_client.post("/api/scans", json={"target_url": "https://opencloud.example.com"}).status_code == 202
    assert test_client.post("/api/scans", json={"target_url": "https://cloud.example.org"}).status_code == 202
    refused = test_client.post("/api/scans", json={"target_url": "https://other.example.com"})
    assert refused.status_code == 403


def test_a_txt_record_naming_this_service_approves_the_instance(monkeypatch):
    """The owner of a name can opt in without asking the operator."""
    asked: list[str] = []

    def records(name, timeout=3.0):
        asked.append(name)
        if name.startswith("_check-opencloud-security.ok."):
            return ["check-opencloud-security=testserver"]
        return ["check-opencloud-security=another-service"]

    monkeypatch.setattr(approval, "txt_records", records)
    test_client = _client_for(_approval())

    assert test_client.post("/api/scans", json={"target_url": "https://ok.example.com"}).status_code == 202
    # A record approving a different deployment approves nothing here.
    assert test_client.post("/api/scans", json={"target_url": "https://no.example.com"}).status_code == 403
    assert asked[0] == "_check-opencloud-security.ok.example.com"


def test_the_dns_proof_is_ignored_when_the_operator_turned_it_off(monkeypatch):
    """An operator who wants the list alone must get the list alone."""
    monkeypatch.setattr(approval, "txt_records", lambda name, timeout=3.0: ["check-opencloud-security=testserver"])
    test_client = _client_for(_approval(approval_dns=False, approved_targets=("listed.example.com",)))

    assert test_client.post("/api/scans", json={"target_url": "https://ok.example.com"}).status_code == 403


def test_approval_off_asks_no_dns_at_all(monkeypatch):
    """The public service must not start looking up TXT records for every visitor."""
    def fail(name, timeout=3.0):
        raise AssertionError("no lookup expected")

    monkeypatch.setattr(approval, "txt_records", fail)

    assert client().post("/api/scans", json={"target_url": "https://ok.example.com"}).status_code == 202


def test_an_approval_mode_that_could_approve_nothing_refuses_to_start():
    """Required, with no list and no DNS proof, would refuse every visitor silently."""
    with pytest.raises(ValueError, match="no target could ever be scanned"):
        create_app(_approval(approval_dns=False))


def test_an_approved_entry_that_does_not_parse_refuses_to_start():
    """A typo in the list would approve nothing it was meant to."""
    with pytest.raises(ValueError, match="COS_WEB_APPROVED_TARGETS"):
        create_app(_approval(approved_targets=("not a host!",)))


def test_txt_character_strings_are_joined_as_one_record():
    """A long TXT value arrives split into 255-byte strings and means their join."""
    rdata = bytes([5]) + b"check" + bytes([20]) + b"-opencloud-security="

    assert approval._txt_strings(rdata) == "check-opencloud-security="


def test_dns_approval_without_a_public_address_refuses_to_start():
    """The record names this service by hostname; without one, no record could match."""
    with pytest.raises(ValueError, match="COS_WEB_APPROVAL_DNS needs COS_WEB_PUBLIC_BASE_URL"):
        approval.ensure_approval_ready(_approval(public_base_url=None))

    # The negative case: with the DNS proof off, a listed target needs no public address.
    approval.ensure_approval_ready(
        _approval(public_base_url=None, approval_dns=False, approved_targets=("ok.example.com",))
    )


def _target(hostname: str, *addresses: str) -> ssrf.Target:
    return ssrf.Target(hostname, 443, "https", "/", addresses or ("192.0.2.10",))


@pytest.mark.parametrize("hostname", ["192.0.2.10", "[2001:db8::1]", "2001:db8::1"])
def test_an_address_target_is_never_approved_by_dns(monkeypatch, hostname):
    """Nobody can publish a TXT record under an address, so none may approve one."""
    looked_up: list[str] = []

    def records(name, timeout=3.0):
        looked_up.append(name)
        return ["check-opencloud-security=testserver"]

    monkeypatch.setattr(approval, "txt_records", records)

    assert not approval.approved(_target(hostname), _approval())
    assert looked_up == []
    # The positive case: the same record approves a hostname.
    assert approval.approved(_target("ok.example.com"), _approval())


def test_approval_off_approves_every_target(monkeypatch):
    """The public service scans any public OpenCloud, listed or not."""
    monkeypatch.setattr(approval, "txt_records", lambda name, timeout=3.0: [])

    assert approval.approved(_target("any.example.com"), settings())
    assert not approval.approved(_target("any.example.com"), _approval())


def test_a_listed_address_approves_only_when_every_address_is_listed():
    """A name resolving partly outside the list must not ride on the listed part."""
    entries = ("192.0.2.0/28",)

    assert approval.listed(_target("x.example.com", "192.0.2.5"), entries)
    assert not approval.listed(_target("x.example.com", "192.0.2.5", "198.51.100.7"), entries)
    assert not approval.listed(_target("x.example.com", "192.0.2.5"), ())


def _txt_answer(*answers: tuple[int, bytes]) -> bytes:
    """A DNS answer message carrying the given (type, rdata) records."""
    question = b"".join(bytes([len(label)]) + label for label in (b"_x", b"example", b"com")) + b"\0"
    message = (
        (4242).to_bytes(2, "big")
        + (0x8180).to_bytes(2, "big")  # a response, recursion available, NOERROR
        + (1).to_bytes(2, "big")
        + len(answers).to_bytes(2, "big")
        + bytes(4)
        + question
        + (16).to_bytes(2, "big")
        + (1).to_bytes(2, "big")
    )
    for rtype, rdata in answers:
        message += (
            b"\xc0\x0c"
            + rtype.to_bytes(2, "big")
            + (1).to_bytes(2, "big")
            + (300).to_bytes(4, "big")
            + len(rdata).to_bytes(2, "big")
            + rdata
        )
    return message


def test_txt_records_reads_only_the_txt_answers(monkeypatch):
    """A record of another type in the answer must not count as the approval."""
    value = b"check-opencloud-security=testserver"
    answer = _txt_answer((16, bytes([len(value)]) + value), (1, bytes([192, 0, 2, 10])))
    monkeypatch.setattr(approval, "system_nameservers", lambda: ["192.0.2.53"])
    monkeypatch.setattr(approval, "ask", lambda name, qtype, nameserver, timeout: answer)

    assert approval.txt_records("_x.example.com") == ["check-opencloud-security=testserver"]


def test_a_failed_lookup_tries_the_next_resolver_and_then_refuses(monkeypatch):
    """A lookup that fails is a refusal, never an approval."""
    value = b"check-opencloud-security=testserver"
    asked: list[str] = []

    def ask(name, qtype, nameserver, timeout):
        asked.append(nameserver)
        if nameserver == "192.0.2.53":
            raise OSError("timed out")
        if nameserver == "192.0.2.54":
            return b"runt"
        return _txt_answer((16, bytes([len(value)]) + value))

    monkeypatch.setattr(approval, "ask", ask)
    monkeypatch.setattr(approval, "system_nameservers", lambda: ["192.0.2.53", "192.0.2.54"])

    assert approval.txt_records("_x.example.com") == []
    assert asked == ["192.0.2.53", "192.0.2.54"]

    # The positive case: a third resolver that answers is used.
    monkeypatch.setattr(approval, "system_nameservers", lambda: ["192.0.2.53", "192.0.2.55"])
    assert approval.txt_records("_x.example.com") == ["check-opencloud-security=testserver"]
