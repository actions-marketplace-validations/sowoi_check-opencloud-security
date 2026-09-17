#!/usr/bin/env python3
"""
Check the four frontend catalogues and the translated guides.

Two kinds of check live here, and the difference between them is the point.

**Structural checks** compare a translation against the English source as
data: the same keys, the same ``{placeholders}``, the same inline markup, the
same link targets, and a relative link that resolves to a file that exists.
A translator cannot argue with any of these, a machine can decide all of
them, and each one breaks a page or a format string when it is wrong. They
are errors and they fail the build.

**Style checks** are heuristics about prose: the form of address a language
was chosen to use, a sentence left in English, a product name dropped in
translation, a glossary term rendered two ways. None of these can be decided
by a machine - "natural" is not a property this script can measure - so they
are warnings that name a key for a human to look at. ``--strict`` turns them
into errors for somebody who wants a clean sheet, which is not the default.

What is deliberately absent: any network request, any translation service,
and any attempt to score prose quality. The catalogues are source code and
this reads them as source code.

See ``TRANSLATING.md`` for the conventions each language follows and for the
review workflow these checks support.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from string import Formatter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from webapp.documentation import GUIDE_LANGUAGES
from webapp.locales import de, en, es, fr

#: The source language every other catalogue is compared against.
SOURCE = "en"

#: Each language's own catalogue, before the documentation manifest fills in
#: the guide titles it has no translation for. The distinction matters: a
#: manifest title is an English fallback this project chose on purpose (see
#: ``webapp/locales/__init__.py``), not a sentence somebody forgot to
#: translate, and reading the merged catalogue would report all of them.
OWN_MESSAGES: dict[str, dict[str, str]] = {
    "en": en.MESSAGES,
    "de": de.MESSAGES,
    "es": es.MESSAGES,
    "fr": fr.MESSAGES,
}

#: The languages translated from English, in report order.
TRANSLATIONS: tuple[str, ...] = ("de", "es", "fr")

#: Where each catalogue lives, for a report a reader can open.
CATALOGUE_FILES: dict[str, str] = {
    locale: f"webapp/locales/{locale}.py" for locale in OWN_MESSAGES
}

#: The inline elements a catalogue string may carry. ``Translator.html``
#: renders these as markup, so an element outside this set is either a typo
#: or an escalation of what a catalogue is allowed to do.
ALLOWED_TAGS = frozenset(
    {"a", "abbr", "code", "em", "kbd", "li", "ol", "p", "strong", "sub", "sup", "ul"}
)


@dataclass(frozen=True)
class Finding:
    """One thing worth a reviewer's attention, in one place."""

    rule: str
    severity: str
    locale: str
    location: str
    detail: str
    action: str

    def render(self) -> str:
        """The finding as one line, opening at the file it is about."""
        return (
            f"{self.severity.upper():7s} {self.locale}  {self.location}\n"
            f"        rule: {self.rule}\n"
            f"        {self.detail}\n"
            f"        -> {self.action}"
        )


#: Findings a reviewer has looked at and accepted, by rule, language and
#: location, each with the reason it is not a defect. An entry here is a
#: decision that has been made, not a check that has been switched off: it
#: still appears in ``--show-accepted``.
ACCEPTED: dict[tuple[str, str, str], str] = {
    (
        "untranslated",
        locale,
        "admin.exclusions.add.placeholder",
    ): "An example hostname, which is the same in every language."
    for locale in TRANSLATIONS
}


# --------------------------------------------------------------- structure

_HREF = re.compile(r'href="([^"]*)"')
_TAG = re.compile(r"</?([A-Za-z][A-Za-z0-9]*)")
_TAGS = re.compile(r"</?[^>]+>")


def _placeholders(value: str) -> Counter[str]:
    """
    How often each ``{name}`` appears, or nothing when the string is broken.

    Counted rather than listed in order, because word order is the first
    thing a translation changes and a reordered sentence is correct.
    """
    return Counter(
        field
        for _, field, _, _ in Formatter().parse(value)
        if field is not None
    )


def _format_error(value: str) -> str | None:
    """The reason ``str.format`` would refuse this string, if it would."""
    try:
        list(Formatter().parse(value))
    except ValueError as error:
        return str(error)
    return None


def _tags(value: str) -> tuple[str, ...]:
    """Every inline element in the string, in order."""
    return tuple(_TAGS.findall(value))


def structural_findings() -> list[Finding]:
    """Every difference from English that is a defect rather than a choice."""
    findings: list[Finding] = []
    source = OWN_MESSAGES[SOURCE]
    for locale in TRANSLATIONS:
        messages = OWN_MESSAGES[locale]
        file = CATALOGUE_FILES[locale]
        for key in sorted(set(source) - set(messages)):
            findings.append(
                Finding(
                    "missing-key",
                    "error",
                    locale,
                    f"{file}:{key}",
                    "The English catalogue has this key and this one does not.",
                    "Translate the English string under the same key.",
                )
            )
        for key in sorted(set(messages) - set(source)):
            findings.append(
                Finding(
                    "extra-key",
                    "error",
                    locale,
                    f"{file}:{key}",
                    "No English string has this key, so nothing reads it.",
                    "Remove it, or add the English source it belongs to.",
                )
            )
        for key in sorted(set(messages) & set(source)):
            findings.extend(_compare(locale, file, key, source[key], messages[key]))
    return findings


def _compare(
    locale: str, file: str, key: str, source: str, translated: str
) -> list[Finding]:
    """The structural checks for one translated string."""
    findings: list[Finding] = []
    location = f"{file}:{key}"

    broken = _format_error(translated)
    if broken is not None:
        return [
            Finding(
                "format-syntax",
                "error",
                locale,
                location,
                f"The string cannot be formatted: {broken}.",
                "Write a literal brace as {{ or }}.",
            )
        ]

    expected, actual = _placeholders(source), _placeholders(translated)
    if expected != actual:
        missing = sorted((expected - actual).elements())
        added = sorted((actual - expected).elements())
        findings.append(
            Finding(
                "placeholder",
                "error",
                locale,
                location,
                f"Placeholders differ from English: missing {missing}, extra {added}.",
                "Use exactly the English placeholder names; reordering is fine.",
            )
        )

    if _tags(source) != _tags(translated):
        findings.append(
            Finding(
                "markup",
                "error",
                locale,
                location,
                f"Inline markup differs: English {_tags(source)}, "
                f"{locale} {_tags(translated)}.",
                "Keep the same elements around the same part of the sentence.",
            )
        )

    unknown = sorted(
        {name.lower() for name in _TAG.findall(translated)} - ALLOWED_TAGS
    )
    if unknown:
        findings.append(
            Finding(
                "markup",
                "error",
                locale,
                location,
                f"Elements a catalogue may not carry: {unknown}.",
                f"Use one of {sorted(ALLOWED_TAGS)}, or no markup at all.",
            )
        )

    if sorted(_HREF.findall(source)) != sorted(_HREF.findall(translated)):
        findings.append(
            Finding(
                "link-target",
                "error",
                locale,
                location,
                f"Link targets differ: English {sorted(_HREF.findall(source))}, "
                f"{locale} {sorted(_HREF.findall(translated))}.",
                "Translate the link text, never the address.",
            )
        )
    return findings


# ------------------------------------------------------------------- style

#: How each language addresses the reader, and the markers of the register it
#: does not use. German is informal by AGENTS.md; French and Spanish are
#: polite, which is what their catalogues were written in - see
#: ``TRANSLATING.md`` for why each was chosen.
#:
#: The German markers are ambiguous at the start of a sentence, where "Sie"
#: is just as likely to be "they", so those are exempt: a detector that
#: flagged them would push a translator into worse German. "tu" and "tú" are
#: not ambiguous in the same way.
REGISTER: dict[str, tuple[str, str, re.Pattern[str], bool]] = {
    "de": (
        "informal (du)",
        "formal (Sie)",
        re.compile(r"\b(?:Sie|Ihnen|Ihr(?:e[mnrs]?)?)\b"),
        True,
    ),
    "fr": (
        "polite (vous)",
        "familiar (tu)",
        re.compile(r"\b(?:tu|toi|ton|ta|tes|tien(?:ne)?s?)\b"),
        False,
    ),
    "es": (
        "polite (usted)",
        "familiar (tú)",
        re.compile(r"\b(?:t[úu]|tus|tuyos?|tuyas?|vosotros|vuestr[oa]s?)\b"),
        False,
    ),
}

#: Names this project does not translate. Losing one of these from a sentence
#: costs the reader the one word they could have searched for.
PROTECTED_TERMS: tuple[str, ...] = (
    "OpenCloud",
    "Nagios",
    "Icinga",
    "Checkmk",
    "Prometheus",
    "Redis",
    "Ansible",
    "Kubernetes",
    "Docker",
    "Keycloak",
    "Authentik",
    "Authelia",
    "PyPI",
    "GitHub",
    "OpenAPI",
    "Arazzo",
    "MCP",
    "HSTS",
    "CSP",
    "TLS",
    "DNS",
    "SSRF",
    "OIDC",
    "WebFinger",
    "IPv4",
    "IPv6",
)

#: Terms this project renders one way in each language. The check is one
#: directional: an English string using the term should produce a translation
#: using the agreed word. It is a warning because a rewritten sentence can be
#: right without it.
GLOSSARY: dict[str, dict[str, tuple[str, ...]]] = {
    "hardening": {
        "de": ("Härtung",),
        "fr": ("durcissement",),
        "es": ("refuerzo",),
    },
    "instance": {
        "de": ("Instanz",),
        "fr": ("instance",),
        "es": ("instancia",),
    },
    "waiver": {
        "de": ("Ausnahme", "ausgenommen"),
        "fr": ("exemption", "exempté", "exclusion"),
        "es": ("exención", "eximid", "exclusión"),
    },
}

_URL = re.compile(r"https?://\S+")
_CODE = re.compile(r"`[^`]*`")
_PLACEHOLDER = re.compile(r"\{[^}]*\}")
_DOTTED = re.compile(r"\S+\.\S+")
_WORD = re.compile(r"[^\W\d_]{2,}", re.UNICODE)


def _prose(value: str) -> str:
    """The sentence with everything that is not prose taken out."""
    without = _TAGS.sub(" ", value)
    without = _URL.sub(" ", without)
    without = _CODE.sub(" ", without)
    without = _PLACEHOLDER.sub(" ", without)
    # A hostname, a file name or a dotted identifier is the same in every
    # language, and three of them in a row are not a sentence.
    return _DOTTED.sub(" ", without)


def _is_prose(value: str) -> bool:
    """Whether there is enough of a sentence here to expect a translation."""
    return len(_WORD.findall(_prose(value))) >= 3


def _register_hits(text: str, pattern: re.Pattern[str], exempt_start: bool) -> list[str]:
    """Every marker of the wrong register, skipping ambiguous positions."""
    stripped = _TAGS.sub("", text)
    found = []
    for match in pattern.finditer(stripped):
        if exempt_start:
            before = stripped[: match.start()].rstrip()
            if not before or before[-1] in ".!?:-–":
                continue
        found.append(match.group(0))
    return found


def style_findings() -> list[Finding]:
    """Heuristics about prose, for a reviewer rather than for a build."""
    findings: list[Finding] = []
    source = OWN_MESSAGES[SOURCE]
    for locale in TRANSLATIONS:
        messages = OWN_MESSAGES[locale]
        file = CATALOGUE_FILES[locale]
        used, avoided, pattern, exempt_start = REGISTER[locale]
        for key in sorted(set(messages) & set(source)):
            location = f"{file}:{key}"
            translated, original = messages[key], source[key]

            hits = _register_hits(translated, pattern, exempt_start)
            if hits:
                findings.append(
                    Finding(
                        "register",
                        "warning",
                        locale,
                        location,
                        f"{avoided} address here: {sorted(set(hits))}.",
                        f"This language addresses the reader as {used}.",
                    )
                )

            if translated == original and _is_prose(original):
                findings.append(
                    Finding(
                        "untranslated",
                        "warning",
                        locale,
                        location,
                        "The string is identical to the English source.",
                        "Translate it, or record it in ACCEPTED with a reason.",
                    )
                )

            dropped = [
                term
                for term in PROTECTED_TERMS
                if term in original and term not in translated
            ]
            if dropped:
                findings.append(
                    Finding(
                        "protected-term",
                        "warning",
                        locale,
                        location,
                        f"English names this and the translation does not: {dropped}.",
                        "Keep the name; translate the sentence around it.",
                    )
                )

            # Matched against the prose only: `{waivers}` is a placeholder
            # name the translation must keep verbatim, not a word in a
            # sentence, and reading it as one asks for the German for a
            # variable.
            english_prose = _prose(original)
            for term, renderings in GLOSSARY.items():
                if not re.search(rf"\b{term}", english_prose, re.IGNORECASE):
                    continue
                accepted = renderings[locale]
                if not any(word.lower() in translated.lower() for word in accepted):
                    findings.append(
                        Finding(
                            "glossary",
                            "warning",
                            locale,
                            location,
                            f'English "{term}" is rendered as {accepted} here, '
                            "and this string uses none of them.",
                            "Use the agreed term, or rewrite so it is not needed.",
                        )
                    )
    return findings


# ------------------------------------------------------------------ guides

_LINK = re.compile(r"\]\((?!https?://|mailto:|#)([^)\s]+)\)")
_FENCE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`\n]*`")


def _guide_prose(text: str) -> str:
    """The guide with code fences blanked out and line numbers preserved."""
    without = _FENCE.sub(lambda block: "\n" * block[0].count("\n"), text)
    return _INLINE_CODE.sub("", without)


def guide_findings() -> list[Finding]:
    """Dead relative links and the wrong register in the translated guides."""
    findings: list[Finding] = []
    # The English guides are read for dead links only. They have no register
    # to get wrong, but they are where a link into a translated directory is
    # written, and that link breaks the same way as any other.
    for path in sorted((ROOT / "docs").glob("*.md")):
        relative = path.relative_to(ROOT).as_posix()
        findings.extend(
            _guide_links(SOURCE, path, relative, path.read_text(encoding="utf-8"))
        )
    for locale in GUIDE_LANGUAGES:
        used, avoided, pattern, exempt_start = REGISTER[locale]
        directory = ROOT / "docs" / locale
        for path in sorted(directory.glob("*.md")):
            relative = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8")
            for number, line in enumerate(_guide_prose(text).splitlines(), start=1):
                hits = _register_hits(line, pattern, exempt_start)
                if hits:
                    findings.append(
                        Finding(
                            "register",
                            "warning",
                            locale,
                            f"{relative}:{number}",
                            f"{avoided} address here: {sorted(set(hits))}.",
                            f"This language addresses the reader as {used}.",
                        )
                    )
            findings.extend(_guide_links(locale, path, relative, text))
    return findings


def _guide_links(
    locale: str, path: Path, relative: str, text: str
) -> list[Finding]:
    """Every relative link in one guide that leads nowhere."""
    findings = []
    body = _FENCE.sub("", text)
    for number, line in enumerate(body.splitlines(), start=1):
        for match in _LINK.finditer(line):
            target = match.group(1).split("#", 1)[0]
            if not target or (path.parent / target).exists():
                continue
            findings.append(
                Finding(
                    "dead-link",
                    "error",
                    locale,
                    f"{relative}:{number}",
                    f"The link target {match.group(1)} does not exist.",
                    "Point it at a file that exists. The usual cause is "
                    "depth: a guide under docs/<language>/ is one level "
                    "deeper than its English source, so a path out of docs/ "
                    "needs ../../ rather than ../.",
                )
            )
    return findings


# ------------------------------------------------------------------ report


def all_findings() -> tuple[list[Finding], list[Finding]]:
    """Every finding, split into the ones nobody has looked at and the rest."""
    found = structural_findings() + style_findings() + guide_findings()
    open_findings: list[Finding] = []
    accepted: list[Finding] = []
    for finding in found:
        key = (finding.rule, finding.locale, finding.location.split(":", 1)[-1])
        (accepted if key in ACCEPTED else open_findings).append(finding)
    return open_findings, accepted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="print only what fails the build (structural errors)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="fail on style warnings as well as structural errors",
    )
    parser.add_argument(
        "--show-accepted",
        action="store_true",
        help="also list the findings ACCEPTED records a decision for",
    )
    arguments = parser.parse_args(argv)

    findings, accepted = all_findings()
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]

    shown = errors if arguments.check else findings
    for finding in shown:
        print(finding.render())
        print()

    if arguments.show_accepted:
        print(f"Accepted, with a recorded reason ({len(accepted)}):")
        for finding in accepted:
            print(f"  {finding.locale}  {finding.location}  [{finding.rule}]")
        print()

    print(
        f"{len(errors)} structural error(s), {len(warnings)} style warning(s), "
        f"{len(accepted)} accepted."
    )
    if errors:
        print(
            "Structural errors break a page or a format string; fix them.",
            file=sys.stderr,
        )
    if warnings and not arguments.check:
        print("Style warnings name a key for a human to judge; see TRANSLATING.md.")
    return 1 if errors or (arguments.strict and warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
