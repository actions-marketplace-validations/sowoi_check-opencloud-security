## check-opencloud-security 1.23.2

### Fixed

- **Parallel scanner tests no longer overflow the fake server's backlog.**
  The fixture accepts a full burst of probes, so dropped local connections
  do not turn a reachable test finding into an intermittent pass.

### Security

- **Anonymous scans no longer inherit local credentials.** Scanner sessions, including
  parallel sessions, disable ambient Requests configuration. Explicit demo
  authentication remains intact. Webhook sessions also disable ambient credentials.
- **Pinned scans cannot be redirected through ambient proxies.** Scans ignore
  environment proxies. A pinned scan with an explicit resolving proxy is rejected.
  Unpinned CLI scans still support the explicitly configured proxy.
- **Workers cannot resurrect erased or expired scan results.** Worker transitions
  require the original metadata and status keys to exist, and check and write atomically
  in Redis. MemoryRedis follows the same contract. Deletion between reading metadata and
  committing completion cannot revive the UUID.
- **Browser-origin fallback checks validate the complete origin.** Opaque and
  malformed origins are rejected; comparison includes scheme, normalized hostname and
  effective port. The configured public origin is authoritative, not the request's
  internal Host header.
- **Webhook delivery dials only the addresses that passed validation.** Delivery pins
  the validated address set while preserving Host, TLS SNI and certificate hostname
  verification. Restricted delivery refuses an explicit resolving proxy and ignores
  ambient proxies. Redirects remain disabled and response bodies are not downloaded.
- **Redirect responses obey the scanner response-size limit.** Scanner sessions leave
  all redirect handling to the capped manual redirect loop, including the normally
  implicit Response.next preparation. Explicit request Authorization headers are not
  propagated to redirect targets.
- **A web scan timeout now stops its probes.** Each web scan runs in a spawned child
  process. Timeout and cancellation kill and reap it, including its probe threads,
  before the slot is released. Unexpected child failures return a generic
  classification; worker logs no longer include exception traces that may contain scan
  data.
- **Authentication-key fetches stay bounded during outages.** Only one key lookup may
  be in progress per verifier; concurrent attempts fail closed without queuing another
  blocking fetch. Failed fetches impose a 60-second retry floor, including initial
  fetches. Valid cached-key verification and key rotation retain their existing
  behavior.
- **Web request bodies are bounded before parsing.** An ASGI guard bounds mutation
  request bodies to 1 MiB and a 30-second total receive deadline before downstream
  parsing. Chunked bodies are counted as well. Oversized bodies return 413 and
  incomplete bodies return 408.
- **Unrelated browser pages cannot trigger loopback-service scans.** Scan-triggering
  GET and POST routes reject cross-site/same-site Fetch Metadata and foreign or opaque
  fallback Origins. Ordinary non-browser monitoring clients remain supported. Malformed
  Host values are refused instead of raising.
- **Existing wizard secret files are private before new secrets are written.** The
  wizard applies fchmod(0600) to the open descriptor before writing any secret data,
  including existing .env files, nginx admin-header files and secret backups.

### Documentation

- **Repository-wide security audit.** `security/audit-2026-09-16.md` records
  the review scope, eleven fixes, validation results and remaining deployment
  checks. Advisory records are drafts; nothing was published by the audit.
- **German, French and Spanish frontend wording and terminology have been
  polished.** The translated catalogues now use more natural phrasing and
  established technical terms across the public and operator-facing pages,
  without changing any scan behaviour or API contract.
- **Keeping the release schedule and advisories current.**
  `docs/reference-data.md` documents `check-opencloud-scanner refresh-data`:
  - the reviewed, Sigstore-attested files it fetches, and the three
    verification outcomes;
  - the structural checks that apply either way;
  - pointing `scanner.release_schedule` and `scanner.vulnerability_db` at the
    result;
  - the daily systemd timer;
  - mirrors for hosts without internet access.

  It also warns that a schedule file the check cannot read turns the
  end-of-life check off rather than falling back to the bundled schedule.
- **A reference for `check-opencloud-scanner`.** `docs/scanner-cli.md` covers
  the global options and configuration search, `scan`, `diff`, `explain`,
  `refresh-data`, `serve` and `configure`, with options and exit codes for
  each. It explains how they differ from the plugin's Nagios codes.
- **Signed exports are documented in `docs/webapp.md`.** A new section
  explains what `X-COS-Signature` covers and that it is a shared-secret HMAC
  rather than a public signature. It shows how to keep the header with the
  file, and how to verify it with `scripts/verify_export.py` or `openssl`.
- **The README no longer says the bundled advisory database is empty.** It
  names the advisory it carries and points to the refresh guide.
- Both new pages are listed in `docs/README.md` and published under
  `/documentation`. The frontend documentation and search indexes are rebuilt.
