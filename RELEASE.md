## check-opencloud-security 1.22.6

### Security

- **The Docker setup wizard no longer shows a stored credential when it is
  run again.** A re-run reads `.env` back so that its credentials survive, and
  every question then offered the value in brackets as the default - the SMTP
  password, the erasure token, the signing keys, the audit salt, the
  encryption key, the `/admin` proxy secret and the releases token, in plain
  text on the screen and in the scrollback. Those prompts now say `[set,
  hidden - Enter keeps it]` instead, Enter still keeps the stored value, and
  what is typed at them is read without an echo when the wizard runs in a
  terminal. Settings kept in `.env` that are not credentials - the issuer, the
  audience, the key set and resource URLs - are still shown, so they can be
  checked.
- **The scan service no longer lets a submitted host write its own log
  lines.** `opencloud-local-scan serve` logged a failed scan with the host
  exactly as the request body held it, so a newline in `url=` started a new
  line in the service log that looked like any other. The host and the error
  are now logged in quoted, escaped form. Found by CodeQL.

### Added

- **The Docker setup wizard is downloaded from a release, checksummed, and
  knows its version.** Every release now attaches `setup-wizard.py` with a
  `setup-wizard.py.sha256` beside it, built and attested by the release
  workflow, and the guides download that copy instead of whatever `main` held.
  `setup-wizard.py --version` names the release it came from: stamped into the
  download, and read from `pyproject.toml` in a checkout or the web bundle.
  See ADR 0049. The release asset first exists with the next release.
- **The Docker setup wizard asks how much to ask.** `quick`, the default on a
  first run, asks only the image, the port and public address, `/mcp` and its
  sign-in, `/admin`, the identity provider and its mail, and the reverse proxy;
  `private` asks the same from the private preset; `full` asks everything and
  is the default when editing an existing deployment. `--mode` answers it in
  advance, and a section passed over is now named as skipped so the step
  counter adds up.
- **The Docker setup wizard shows what a re-run would change, and keeps what
  it replaces.** Before asking to overwrite, it prints a diff of the compose
  file and the proxy and logrotate files - never of `.env` - and every replaced
  file is kept as `<name>.<UTC time>.bak`, the `.env` copy owner-readable only.
- **The Docker setup wizard checks the host and can start the stack.** The
  summary points out Docker or the Compose plugin missing, the host port
  already in use, and a certificate the proxy configuration names that does
  not exist. After writing it offers `docker compose config`, then
  `docker compose up -d` and a wait for `/healthz` - each only when asked, and
  `up` only when nothing has to be done as root first.
- **Answers can travel between hosts.** `--print-answers` prints every
  non-credential answer as JSON and writes nothing; `--answers FILE` starts a
  run from such a file, read as untrusted, and refuses one with nothing usable
  in it.

### Changed

- **The Docker setup wizard no longer binds every interface to check a
  port.** When `bind_address` publishes on all interfaces (`0.0.0.0`, `::` or
  empty), the check that the host port is free now probes loopback - a port
  taken on every interface is taken there too - instead of briefly binding the
  wildcard address itself.

- **Web: page titles no longer repeat the site name.** A title that already
  says "OpenCloud Security Scanner" - most documentation guides - is no longer
  followed by `· OpenCloud Security Scan`, so a search result shows the part
  that tells the pages apart. Every page also declares its language as
  `og:locale`, and the `/ai` description is short enough not to be cut off.
  An address with a trailing slash (`/about/`) now redirects permanently
  (308) instead of temporarily (307), so a crawler keeps one address per
  page, and `/favicon.ico` redirects to the site icon instead of answering 404.

- **The Docker setup wizard is easier to read.** A question opens with its
  first sentence, and `?` shows the rest with a link to the page documenting
  the setting, at the release the wizard came from. Text wraps to the width of
  the terminal. The summary labels each answer with its question, gives the
  name to type in brackets and marks every answer that differs from the
  default, and the enrollment link block uses the same rules as the rest of
  the output.
- **The Docker setup wizard offers the bundled Authentik once a sign-in is
  wanted.** Switching on the operator's area at `/admin` or the sign-in on
  `/mcp` now makes *yes* the default at the identity provider question, because
  nearly every deployment asking for either has no provider of its own and was
  otherwise sent on to issuer, audience and key questions it could not answer.
  Answering `no` still checks tokens against a provider you run. The default
  moves only when a sign-in is switched on, so re-running over a deployment
  that already declined Authentik keeps it out, and `--sign-in` on its own
  still adds no provider.
- **The Docker setup wizard is easier to follow.** It opens with a framed
  title, the list of steps ahead and a table of what can be typed at a
  question; every section heading shows `Step N of 12` with a progress bar;
  the question, its current value and a refused answer stand out from the
  explanation; and the summary and closing screens are grouped under rules.
  The styling is plain ANSI from the standard library - Rich, questionary and
  InquirerPy were considered and would each need installing on a host that
  has only Docker - and it is left out entirely when the output is not a
  terminal, `NO_COLOR` is set or `TERM=dumb`, so piped and logged runs print
  exactly the plain text they did before.

### Documentation

- **`tests/README.md` indexes the test suite.** Every test module is listed by
  area with a line on what it protects, alongside the shared fixtures, how to
  run the suite and its conventions. `tests/test_documentation_indexes.py`
  fails when a test module is added, renamed or removed without the index
  following.
