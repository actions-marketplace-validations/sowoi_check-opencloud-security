"""
Property-based tests for the parsers that read text from outside.

Version strings come from a stranger's status.php, security headers from a
stranger's proxy, targets from a stranger's form field and lists from an
operator's YAML or environment. The example-based tests pin the forms we have
seen; these let Hypothesis look for the ones we have not. Reviewed in
security/dependencies/hypothesis.yml.
"""

from __future__ import annotations

import ipaddress
from unittest import mock

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from opencloud_local_scan import versions
from opencloud_local_scan.config import Configuration
from opencloud_local_scan.scanner import (
    _csp_directive,
    _csp_has_unsafe_inline,
    _hsts_max_age,
)
from webapp import ssrf

# The scanner's parsers are cheap; a deadline would only make a slow CI runner
# look like a bug.
settings.register_profile("cos", deadline=None, suppress_health_check=[HealthCheck.too_slow])
settings.load_profile("cos")

numbers = st.integers(min_value=0, max_value=10_000)
triples = st.tuples(numbers, numbers, numbers)


def _dotted(parts: tuple[int, ...]) -> str:
    return ".".join(str(part) for part in parts)


# ---------------------------------------------------------------------------
# Versions


@given(triples, st.sampled_from(["", "v", "V", "OpenCloud ", " "]),
       st.sampled_from(["", "-rc.1", "-beta", "+dev", "+build.7", " "]))
def test_a_version_parses_to_its_numbers_whatever_it_is_wrapped_in(parts, prefix, suffix):
    """'v7.2.0', 'OpenCloud 7.2.0' and '7.2.0-rc.1' must all mean 7.2.0, or a release is misjudged."""
    assert versions.parse_version(f"{prefix}{_dotted(parts)}{suffix}") == parts


@given(st.text())
def test_parsing_any_text_never_raises(text):
    """A hostile status.php must not crash the scan; unparsable is an empty tuple."""
    parsed = versions.parse_version(text)

    assert isinstance(parsed, tuple)
    assert all(isinstance(part, int) and part >= 0 for part in parsed)


@given(triples, triples)
def test_comparison_agrees_with_numeric_order_and_is_antisymmetric(left, right):
    """compare_versions is what decides 'older than the fix', so it must be a total order."""
    expected = (left > right) - (left < right)

    assert versions.compare_versions(_dotted(left), _dotted(right)) == expected
    assert versions.compare_versions(_dotted(right), _dotted(left)) == -expected


@given(triples)
def test_a_missing_trailing_zero_does_not_change_a_version(parts):
    """'7.2' and '7.2.0' are the same release; treating them apart flips a verdict."""
    major, minor, _ = parts

    assert versions.compare_versions(f"{major}.{minor}", f"{major}.{minor}.0") == 0
    assert versions.compare_versions(f"{major}.{minor}", f"{major}.{minor}.1") == -1


@given(st.lists(triples, min_size=3, max_size=3, unique=True))
def test_a_version_is_affected_exactly_between_introduced_and_fixed(points):
    """The advisory range is half-open: the fixed release itself is never affected."""
    low, middle, high = sorted(points)

    assert versions.is_in_range(_dotted(middle), _dotted(low), _dotted(high))
    assert versions.is_in_range(_dotted(low), _dotted(low), _dotted(high))
    assert not versions.is_in_range(_dotted(high), _dotted(low), _dotted(high))
    assert not versions.is_in_range(_dotted(low), _dotted(middle), _dotted(high))


@given(st.text())
def test_normalising_a_version_twice_changes_nothing(text):
    """Normalisation runs on values that were already normalised; it must be idempotent."""
    once = versions.normalise_version(text)

    assert versions.normalise_version(once) == once


@given(st.lists(triples, min_size=1, max_size=8))
def test_newest_is_the_maximum(candidates):
    """'Latest in branch' comes from newest(); it must never pick an older release."""
    chosen = versions.newest(_dotted(parts) for parts in candidates)

    assert versions.parse_version(chosen) == max(candidates)


# ---------------------------------------------------------------------------
# Security headers

whitespace = st.sampled_from([" ", "  ", "\t", "\n", " \t "])
directive_names = st.from_regex(r"[a-z]{1,8}(-[a-z]{1,8})?", fullmatch=True)
source_tokens = st.from_regex(r"[a-z0-9'*:/.-]{1,12}", fullmatch=True)


@given(st.integers(min_value=0, max_value=10**10), whitespace,
       st.sampled_from(["max-age", "Max-Age", "MAX-AGE"]), st.booleans(),
       st.sampled_from(["", "; includeSubDomains", "; preload", "; includeSubDomains; preload"]))
def test_hsts_max_age_is_read_however_it_is_spelled(seconds, space, name, quoted, rest):
    """The preload and strength checks read max-age; case, spaces and quotes are all legal."""
    value = f'"{seconds}"' if quoted else str(seconds)
    header = f"{name}{space}={space}{value}{rest}"

    assert _hsts_max_age(header) == seconds


@given(st.text(alphabet=st.characters(blacklist_characters="0123456789")))
def test_hsts_without_a_number_has_no_max_age(header):
    """A header whose max-age cannot be read must not be credited with one."""
    assert _hsts_max_age(header) is None


@given(st.dictionaries(directive_names, st.lists(source_tokens, max_size=4), min_size=1, max_size=6),
       whitespace, directive_names)
def test_every_csp_directive_is_found_whatever_separates_it(policy, space, absent):
    """A tab or newline between name and sources must not hide script-src (a silent pass)."""
    assume(absent not in policy)
    header = ";".join(f"{space}{name}{space}{' '.join(sources)}" for name, sources in policy.items())

    for name, sources in policy.items():
        assert _csp_directive(header, name) == " ".join(sources)
    assert _csp_directive(header, absent) is None


@given(st.lists(source_tokens, max_size=4), whitespace,
       st.sampled_from(["'unsafe-eval'", "'unsafe-inline'"]))
def test_an_unsafe_script_src_is_flagged_without_a_nonce(sources, space, unsafe):
    """'unsafe-inline' or 'unsafe-eval' in script-src is always reported when nothing neutralises it."""
    assume(not any("nonce" in token or "sha" in token for token in sources))
    header = f"default-src 'self'; script-src{space}{' '.join([*sources, unsafe])}"

    assert _csp_has_unsafe_inline(header) is True


@given(st.lists(source_tokens, max_size=4), whitespace)
def test_unsafe_inline_elsewhere_does_not_taint_script_src(sources, space):
    """style-src 'unsafe-inline' is common and harmless for scripts; it must not raise a finding."""
    assume(not any("unsafe" in token for token in sources))
    header = f"script-src{space}'self' {' '.join(sources)}; style-src 'unsafe-inline'"

    assert _csp_has_unsafe_inline(header) is False


# ---------------------------------------------------------------------------
# The SSRF guard

private_networks = [
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8", "169.254.0.0/16",
    "100.64.0.0/10", "0.0.0.0/8", "224.0.0.0/4", "::1/128", "fc00::/7", "fe80::/10",
]
private_addresses = st.one_of(
    *(st.ip_addresses(network=network) for network in private_networks)
)


def _literal(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> str:
    return f"[{address}]" if address.version == 6 else str(address)


@given(private_addresses, st.sampled_from(["http", "https"]))
def test_a_private_address_literal_is_always_refused(address, scheme):
    """No private, loopback, link-local or multicast address may be scanned."""
    try:
        ssrf.validate_target(f"{scheme}://{_literal(address)}")
    except ssrf.TargetRejected:
        return
    raise AssertionError(f"{address} was accepted")


@given(st.ip_addresses(v=4))
def test_an_ipv4_address_is_judged_the_same_when_mapped_into_ipv6(address):
    """::ffff:10.0.0.1 is 10.0.0.1; a mapped spelling must not slip past the guard."""
    mapped = ipaddress.IPv6Address(f"::ffff:{address}")

    assert ssrf._address_public(mapped) == ssrf._address_public(address)


@given(st.ip_addresses(v=4))
def test_a_6to4_address_is_never_more_public_than_what_it_embeds(address):
    """2002:0a00:0001:: routes to 10.0.0.1; 6to4 must not be a way around the guard."""
    embedded = ipaddress.IPv6Address((0x2002 << 112) | (int(address) << 80))

    assert embedded.sixtofour == address
    if not ssrf._address_public(address):
        assert not ssrf._address_public(embedded)


@settings(max_examples=300)
@given(st.text(max_size=80))
def test_any_input_is_either_refused_or_resolves_only_to_public_addresses(raw):
    """Whatever a visitor types, the guard answers with a TargetRejected or a public target."""
    # Every name "resolves" to a documentation address, so no DNS query leaves
    # the machine and a hostname is always refused as non-public.
    with mock.patch.object(ssrf, "_resolve", return_value=[ipaddress.ip_address("192.0.2.1")]):
        try:
            target = ssrf.validate_target(raw)
        except ssrf.TargetRejected:
            return

    assert target.scheme in {"http", "https"}
    assert target.addresses
    assert all(ssrf._address_public(ipaddress.ip_address(item)) for item in target.addresses)


# ---------------------------------------------------------------------------
# Configuration lists

list_items = st.text(
    alphabet=st.characters(blacklist_characters=";:", blacklist_categories=("Cs", "Cc")),
    min_size=1,
    max_size=20,
).map(str.strip).filter(bool)


@given(st.lists(list_items, max_size=6))
def test_a_yaml_list_and_its_environment_spelling_read_back_the_same(items):
    """`key: [a, b]` in the file and COS_KEY='a;b' must configure the same thing."""
    from_file = Configuration(values={"SCANNER_PATHS": items}, environ={})
    from_environment = Configuration(environ={"COS_SCANNER_PATHS": ";".join(items)})

    assert from_file.get_list("SCANNER_PATHS") == items
    assert from_environment.get_list("SCANNER_PATHS") == items


@given(st.lists(list_items, max_size=6), st.sampled_from([";", " ; ", ";;", "; ;"]))
def test_empty_entries_and_padding_in_a_list_are_dropped(items, separator):
    """A trailing ';' or doubled separator must not become an empty entry the scanner acts on."""
    configuration = Configuration(environ={"COS_SCANNER_PATHS": separator.join(items) + separator})

    assert configuration.get_list("SCANNER_PATHS") == items
