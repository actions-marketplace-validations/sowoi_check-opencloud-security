---
name: add-translation-string
description: Add or change a frontend string in all four web application catalogues (webapp/locales/en.py, de.py, es.py, fr.py) with identical keys, placeholders and inline markup, wire it into the template, and rebuild the search index. Use when adding or rewording visible text in frontend/templates or JavaScript data-* values.
argument-hint: <key and English text, or the template text to translate>
---

# Add a translation string

Request: $ARGUMENTS

Frontend prose is a string catalogue, not copied templates (ADR 0020).
`webapp/locales/en.py` is the source; `de.py`, `es.py` and `fr.py` must carry
**the same keys, the same `{placeholders}` and the same inline markup**.
`tests/test_webapp_i18n.py::test_every_catalog_has_the_same_keys_placeholders_and_markup`
fails otherwise.

## 1. Choose the key

- Keys read `page.element` (`admin.config.title`, `admin.tabs.rules`) - what
  the template wants, not what it says. Look at neighbouring keys in `en.py`
  and reuse the existing prefix.
- Check it does not already exist: `grep -n '"<key>"' webapp/locales/*.py`.
- Place it in the same position (under the same section comment) in all four
  files, so the catalogues stay diffable side by side.

## 2. Write the four values

- **English** first, in the tone of the surrounding strings.
- **German, Spanish, French**: translate the meaning, not word by word. Keep
  product and technical terms as the file already does (`OpenCloud`,
  `COS_WEB_*`, header names, code spans).
- **German always uses the informal "du"** - `du`, `dein`, `dir`, and
  imperatives like `Prüfe`, `Starte`, `Gib ... ein` - never `Sie`, `Ihr`,
  `Ihnen`. `tests/test_webapp_i18n.py` fails on any formal German string.
- **Spanish and French** keep the register the existing entries in that file
  use (check neighbouring strings).
- Placeholders (`{name}`) and markup (`<code>`, `<em>`, `<a href=...>`) must be
  identical in all four. Never add markup to a translation that the English
  source lacks.
- When rewording an existing key, update all four in the same change - a stale
  translation is worse than none.

## 3. Use it

- In a template: `{{ t('key') }}`, or `{{ t.html('key', name=value) }}` when the
  value carries markup. Never inline the sentence.
- In JavaScript: render the translated value into a `data-*` attribute from
  the template and read it there; JavaScript never carries a catalogue.
- No `style=`, `<style>`, inline `<script>` or `onclick` (the CSP has no
  `unsafe-inline`).
- Keep OpenAPI, Arazzo, MCP, discovery documents and exports in English, and
  scan evidence verbatim - those are not translated.

## 4. Verify

```bash
python scripts/build_search_index.py          # overlays carry translated titles/summaries/text
uv run pytest tests/test_webapp_i18n.py -q
uv run pytest tests/test_webapp_search.py -q
```

Add a `CHANGELOG.md` entry under `## [Unreleased]` if the change is visible to
users (skip it only when it rides along with a change that already has one).
