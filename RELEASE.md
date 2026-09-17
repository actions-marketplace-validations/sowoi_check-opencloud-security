## check-opencloud-security 1.24.2

### Changed

- **The German interface and guides now address the reader as "du"
  throughout.** The remaining formal strings in the German catalogue and the
  last formal sentences in `docs/de/` are rewritten, and the test that
  tolerated a list of older formal strings now fails on any formal German
  string, in the catalogue and in the German guides alike.
- **Spanish guide sources are now available in the frontend.** Every public
  guide has a matching `docs/es/` source, generated Spanish template and
  search index entry, so a Spanish visitor no longer gets the English guide
  under a notice. The languages with guide sources are listed once, in
  `GUIDE_LANGUAGES`, for the generator, the route and the search index. See
  [ADR 0063](adr/0063-public-guides-have-spanish-sources.md).

### Fixed

- **The browser tests pass in Firefox again.** Playwright's Firefox drops an
  emulated colour scheme once a page sends
  `Cross-Origin-Opener-Policy: same-origin`, so the dark-theme test now gives
  Firefox a browser whose system theme is dark instead; and waiting for a
  finished scan tolerates the moment during the result page's reload when the
  new document has no body yet.
- **The MCP sign-in no longer warns about `validate_token_resource` at
  startup.** The token verifier already checks a token's audience against
  `COS_WEB_MCP_AUTH_AUDIENCE`, so the MCP SDK is now told explicitly not to
  also require the token's resource to equal the resource URL, which would
  have refused valid tokens once SDK 3.0 turns that check on by default.
- **The grade page test matches the reworded English copy again.** It now
  looks for "Explanations for failed checks", the heading the copy polish
  gave that item.
