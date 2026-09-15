---
name: run-check-opencloud-security
description: Run, start, drive and screenshot check-opencloud-security locally - the Nagios plugin, the opencloud_local_scan library, and the web app (webapp/ + frontend/) - against a fake OpenCloud with no Redis, Docker or real instance. Use when asked to run the plugin, start the web app, submit a scan, take a screenshot of a page, reproduce a rating, or check a change in the running app rather than only in tests.
---

Everything is driven by `.claude/skills/run-check-opencloud-security/driver.py`.
It starts the repo's own fake instance (`tests/fake_opencloud.py`) and points
the plugin, the library or the web app at it. The web app runs with its own
worker inside the same process, so a scan submitted in the browser really
finishes. Paths are relative to the repository root; run everything from there.

Verified on macOS (darwin, zsh) with `uv`. No Redis, Docker daemon or Node
needed.

## Prerequisites

`uv` on PATH. For browser screenshots only, a one-time Chromium download
(~95 MB, into `~/Library/Caches/ms-playwright`):

```bash
uv run --extra web --with playwright python -m playwright install chromium
```

## Pick the layer the change touches

| Change is in | Command |
|---|---|
| `opencloud_local_scan/` (findings, rating, lifecycle) | `driver.py scan` |
| `check_opencloud_security.py` (thresholds, output, exit codes) | `driver.py plugin` |
| `webapp/`, `frontend/` | `driver.py web` + `driver.py api` / `driver.py browse` |

All commands below use `D=.claude/skills/run-check-opencloud-security/driver.py`.

Every command takes `--profile hardened|weak|eol`:
- `hardened`: the defaults (OpenCloud 7.2.3), rated A+.
- `weak`: the same version with demo users, debug endpoints, directory listing, TRACE and a disclosed server header, rated D.
- `eol`: version 2.3.0, rated F.

## Run: library (direct invocation)

```bash
D=.claude/skills/run-check-opencloud-security/driver.py
uv run python $D scan --profile weak
# version=7.2.3 rating=2 EOL=False
# failed extraChecks (8): demoUsersDisabled, reverseProxyDetected, directoryListing, ...
uv run python $D scan --json      # the whole camelCase result document
```

## Run: Nagios plugin

The driver starts a fake instance and runs `check_opencloud_security.py -H 127.0.0.1 --port <port> --scheme http --no-update-check`.
It passes the plugin's own exit code through. Anything after `--` goes to the plugin.

```bash
uv run python $D plugin                   # OK: ... rating: A+   exit=0
uv run python $D plugin --profile weak    # WARNING: Rating D   exit=1
uv run python $D plugin --profile eol -- --format json   # CRITICAL, JSON   exit=2
```

To run the plugin against a long-lived fake instance yourself:

```bash
uv run python $D fake --profile eol --port 9200 > /tmp/cos-fake.log 2>&1 &
for i in $(seq 1 30); do grep -q READY /tmp/cos-fake.log && break; sleep 0.5; done
uv run python check_opencloud_security.py -H 127.0.0.1 --port 9200 --scheme http --no-update-check
lsof -ti:9200 -sTCP:LISTEN | xargs kill
```

## Run: web app (agent path)

Start the web app, the in-process worker and a fake instance together, in the background:

```bash
uv run --extra web python $D web --profile weak > /tmp/cos-web.log 2>&1 &
for i in $(seq 1 60); do grep -q READY /tmp/cos-web.log && break; sleep 1; done
cat /tmp/cos-web.log   # READY http://127.0.0.1:8811 target=http://127.0.0.1:<port> profile=weak
T=$(grep -o 'target=[^ ]*' /tmp/cos-web.log | cut -d= -f2)
```

Over the JSON API: submit to `POST /api/scans`, then poll `GET /api/scans/{uuid}` until the scan finishes.

```bash
uv run python $D api --target "$T" --limit 1500
```

In the browser: open the landing page, fill `#target_url`, click Start audit,
wait on `/scan/{uuid}` for the result, screenshot it and print any console errors.

```bash
uv run --extra web --with playwright python $D browse --target "$T"
```

Screenshots land in `/tmp/cos-shots/` (set `COS_DRIVER_SHOTS` to change it):
- `01-landing.png`: the landing page
- `02-result.png`: the verdict card with the grade dial
- `03-result-full.png`: the full result page, ~9000 px tall

Open them with the Read tool.

Stop:

```bash
lsof -ti:8811 -sTCP:LISTEN | xargs kill
```

`web` sets these unless they're already set in the environment:
- `COS_WEB_REDIS_URL=memory://driver`
- `COS_WEB_ALLOW_PRIVATE_TARGETS=true`
- `COS_WEB_TARGET_COOLDOWN=0`
- `COS_WEB_ENABLE_DOCS=true` (Swagger at `/docs`)

Export any other `COS_WEB_*` variable before launching to try a setting.

## Test

```bash
uv run pytest tests/test_webapp_api.py tests/test_local_scanner.py   # 163 passed, ~55s
uv run pytest                                                         # full suite, ~4 min here
```

## Gotchas

- **`memory://` alone never finishes a scan.** `webapp/queue.py` picks
  `InertQueue` for it, and jobs stay `queued` forever. That is why `driver.py web`
  runs the queue itself, calling `webapp.tasks.run_scan` with
  `app.state.store`. Running `uvicorn webapp.app:app` on its own shows the
  pages, but every scan stays queued.
- **The web app refuses `127.0.0.1` as a target** (SSRF guard) unless
  `COS_WEB_ALLOW_PRIVATE_TARGETS=true`. Without it you get HTTP 400 `"That
  address points into a private, loopback or link-local network, which this
  service will not scan."`
- **Early landing-page screenshots come out blank.** Hero blocks use
  `animation: rise … backwards` with delays up to .35s. Reduced motion
  shortens the duration but not the delay, so the content stays at opacity 0.
  The driver waits until `.scan-form` is opaque before taking the screenshot.
- **Known console error on `/`:** Chromium rejects the `pattern` attribute of
  `#target_url` ("Invalid character in character class" under the `/v`
  flag, caused by the unescaped `-` in `[A-Za-z0-9._~-]`). The browser then
  skips client-side validation of that field. It's an existing bug, not
  something the driver causes.
- **Hardcoded release numbers go stale.** The bundled schedule changes with
  every OpenCloud release, and `run_scan` rates against today's date. A
  profile that was "current" can become end-of-life, so read the latest
  version from `load_release_schedule().latest_for(track)`.
- **macOS has no `timeout`.** Poll with the `for … seq` loops shown above.
- **`sips -c H W` crops from the centre, not the top.** Use the viewport
  screenshot `02-result.png` rather than cropping the full-page one.

## Troubleshooting

- **`TypeError: ReleaseSettings.__init__() got an unexpected keyword argument 'source'`**:
  the field is `mode`. Use `ReleaseSettings(mode="off")` to skip the update check.
- **`web` exits with `SystemExit: 3` after `[Errno 48] error while attempting
  to bind on address ('127.0.0.1', 8811)`**: a previous `web` is still running. Run `lsof -ti:8811 -sTCP:LISTEN | xargs kill`, or pass `--port`
  (and `--base http://127.0.0.1:<port>` to `api`/`browse`).
- **`browse` fails with `Executable doesn't exist`**: run the one-time
  `playwright install chromium` from Prerequisites.
