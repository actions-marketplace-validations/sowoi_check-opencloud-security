"""
Launch and drive check-opencloud-security locally, with no OpenCloud, Redis or
Docker. Agent tooling, not product code: run it from the repository root.

    uv run python .claude/skills/run-check-opencloud-security/driver.py plugin [--profile weak] [-- PLUGIN ARGS]
    uv run python .claude/skills/run-check-opencloud-security/driver.py scan   [--profile weak] [--json]
    uv run python .claude/skills/run-check-opencloud-security/driver.py fake   [--profile weak] [--port 9200]
    uv run --extra web python .claude/skills/run-check-opencloud-security/driver.py web [--port 8811] [--profile weak]
    uv run --extra web --group test python .claude/skills/run-check-opencloud-security/driver.py browse [--base URL] [--target URL]

`fake` and `web` block until killed and print a line starting with READY.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess  # nosec B404 - runs this repository's own plugin
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

SHOTS = Path(os.environ.get("COS_DRIVER_SHOTS", "/tmp/cos-shots"))  # nosec B108 - local screenshots


def instance(profile: str):
    """A FakeOpenCloud configured as a named profile (not started)."""
    from tests.fake_opencloud import FakeOpenCloud, InstanceBehaviour

    behaviour = InstanceBehaviour()
    if profile == "eol":
        behaviour.status_payload["productversion"] = "2.3.0"
    if profile == "weak":
        behaviour.headers = {"Content-Type": "text/html"}
        behaviour.demo_users = True
        behaviour.debug_endpoints = True
        behaviour.directory_listing = True
        behaviour.trace_enabled = True
        behaviour.disclose_server = "nginx/1.18.0"
    return FakeOpenCloud(behaviour)


def cmd_fake(args: argparse.Namespace) -> int:
    fake = instance(args.profile)
    if args.port:
        from tests.fake_opencloud import FakeOpenCloud

        fake = FakeOpenCloud(fake.behaviour, port=args.port)
    with fake:
        print(f"READY http://{fake.host} profile={args.profile}", flush=True)
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            return 0


def cmd_plugin(args: argparse.Namespace) -> int:
    extra = [a for a in args.rest if a != "--"]
    with instance(args.profile) as fake:
        command = [
            sys.executable, str(ROOT / "check_opencloud_security.py"),
            "-H", "127.0.0.1", "--port", str(fake.port), "--scheme", "http",
            "--no-update-check", *extra,
        ]
        print("$ " + " ".join(command[1:]), file=sys.stderr)
        result = subprocess.run(command, check=False)  # nosec B603
        print(f"exit={result.returncode}", file=sys.stderr)
        return result.returncode


def cmd_scan(args: argparse.Namespace) -> int:
    """Call the library directly - no plugin, no thresholds - and print a summary."""
    from opencloud_local_scan import ReleaseSettings, ScannerSettings, scan

    settings = ScannerSettings(scheme="http", timeout=3, check_debug_ports=False, include_bundled_db=True)
    with instance(args.profile) as fake:
        result = scan(fake.host, settings=settings, release_settings=ReleaseSettings(mode="off"))
    if args.json:
        summary = {
            "version": result.get("version"),
            "rating": result.get("rating"),
            "EOL": result.get("EOL"),
            "failedExtraChecks": [
                check.get("name") or check.get("id")
                for check in result.get("extraChecks", [])
                if check.get("passed") is False
            ],
            "missingHardenings": [
                hardening_id
                for hardening_id, passed in result.get("hardenings", {}).items()
                if passed is False
            ],
        }
        print(json.dumps(summary, indent=2, default=str))
        return 0
    failed = [c.get("name") or c.get("id") for c in result.get("extraChecks", []) if c.get("passed") is False]
    print(f"version={result.get('version')} rating={result.get('rating')} EOL={result.get('EOL')}")
    print(f"failed extraChecks ({len(failed)}): {', '.join(map(str, failed))}")
    return 0


def cmd_web(args: argparse.Namespace) -> int:
    """The web app plus an in-process stand-in for the ARQ worker.

    `memory://` normally leaves scans `queued` forever (InertQueue). Here a
    loop drains that queue into `webapp.tasks.run_scan` with the app's own
    store, so a submitted scan really completes - no Redis, no worker process.
    """
    os.environ.setdefault("COS_WEB_REDIS_URL", "memory://driver")
    # The fake instance is on 127.0.0.1, which the SSRF guard refuses otherwise.
    os.environ.setdefault("COS_WEB_ALLOW_PRIVATE_TARGETS", "true")
    os.environ.setdefault("COS_WEB_PUBLIC_BASE_URL", f"http://127.0.0.1:{args.port}")
    os.environ.setdefault("COS_WEB_TARGET_COOLDOWN", "0")
    os.environ.setdefault("COS_WEB_ENABLE_DOCS", "true")

    import uvicorn

    from webapp import tasks
    from webapp.app import create_app

    app = create_app()

    async def worker() -> None:
        while True:
            await asyncio.sleep(0.2)
            queue = app.state.queue
            jobs = getattr(queue, "jobs", None)
            while jobs:
                uuid = jobs.pop(0)
                ctx = {"web_settings": app.state.settings, "store": app.state.store}
                state = await tasks.run_scan(ctx, uuid)
                print(f"worker: {uuid} -> {state}", flush=True)

    async def main() -> None:
        config = uvicorn.Config(app, host="127.0.0.1", port=args.port, log_level="warning")
        server = uvicorn.Server(config)
        with instance(args.profile) as fake:
            job = asyncio.create_task(worker())
            serve = asyncio.create_task(server.serve())
            while not server.started:
                await asyncio.sleep(0.05)
            print(
                f"READY http://127.0.0.1:{args.port} target=http://{fake.host} profile={args.profile}",
                flush=True,
            )
            await serve
            job.cancel()

    asyncio.run(main())
    return 0


def cmd_browse(args: argparse.Namespace) -> int:
    """Submit the landing-page form in headless WebKit and screenshot the result.

    WebKit, never Chromium (ADR 0061), behind the same dead proxy as the
    browser tests, so nothing the page asks for leaves loopback.
    """
    from playwright.sync_api import sync_playwright

    target = args.target
    if not target:
        print("--target is required (the target= URL `web` printed)", file=sys.stderr)
        return 2
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    with sync_playwright() as p:
        browser = p.webkit.launch(
            proxy={"server": "http://127.0.0.1:9", "bypass": "127.0.0.1,localhost,[::1]"}
        )
        # Hero blocks `rise` in with delays up to .35s and `backwards` fill
        # (app.css): until then they are opacity 0, and reduced motion zeroes
        # the duration but not the delay. Wait for the form to be opaque.
        page = browser.new_page(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
        page.on("console", lambda m: m.type == "error" and errors.append(m.text))
        page.goto(args.base + "/")
        page.wait_for_function(
            "() => getComputedStyle(document.querySelector('.scan-form')).opacity === '1'"
        )
        page.screenshot(path=str(SHOTS / "01-landing.png"), full_page=False)
        page.fill("#target_url", target)
        page.click("form.scan-form button[type=submit]")
        page.wait_for_url("**/scan/**", timeout=30_000)
        # The result page polls until the scan is done; wait for the grade.
        page.wait_for_function(
            "() => !document.body.innerText.match(/queued|running|Warteschlange/i)",
            timeout=60_000,
        )
        page.wait_for_timeout(500)
        page.screenshot(path=str(SHOTS / "02-result.png"))
        page.screenshot(path=str(SHOTS / "03-result-full.png"), full_page=True)
        print(f"url={page.url}")
        print(page.inner_text("main")[:1200])
        browser.close()
    print(f"screenshots={SHOTS}/01-landing.png {SHOTS}/02-result.png {SHOTS}/03-result-full.png")
    if errors:
        print("console errors:\n  " + "\n  ".join(errors))
    return 0


def cmd_api(args: argparse.Namespace) -> int:
    """Submit a scan over the JSON API, poll it, print grade and findings count."""
    body = json.dumps({"target_url": args.target}).encode()
    request = urllib.request.Request(
        args.base + "/api/scans", data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request) as response:  # nosec B310
        submitted = json.load(response)
    print("submitted:", json.dumps(submitted))
    uuid = submitted.get("uuid") or submitted.get("id")
    for _ in range(120):
        with urllib.request.urlopen(f"{args.base}/api/scans/{uuid}") as response:  # nosec B310
            record = json.load(response)
        if record.get("done") or record.get("state") in ("completed", "failed"):
            print(json.dumps(record, indent=2)[: args.limit])
            return 0 if record.get("state") == "completed" else 1
        time.sleep(0.5)
    print("timed out waiting for the scan", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    profiles = ("hardened", "weak", "eol")

    p = sub.add_parser("fake", help="serve a fake OpenCloud until killed")
    p.add_argument("--profile", choices=profiles, default="hardened")
    p.add_argument("--port", type=int, default=0)
    p.set_defaults(func=cmd_fake)

    p = sub.add_parser("plugin", help="run the Nagios plugin against a fresh fake instance")
    p.add_argument("--profile", choices=profiles, default="hardened")
    p.add_argument("rest", nargs=argparse.REMAINDER)
    p.set_defaults(func=cmd_plugin)

    p = sub.add_parser("scan", help="call opencloud_local_scan.scan() on a fresh fake instance")
    p.add_argument("--profile", choices=profiles, default="hardened")
    p.add_argument("--json", action="store_true", help="print the whole result document")
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("web", help="web app + in-process worker + fake instance, until killed")
    p.add_argument("--port", type=int, default=8811)
    p.add_argument("--profile", choices=profiles, default="hardened")
    p.set_defaults(func=cmd_web)

    p = sub.add_parser("browse", help="headless Chromium: submit the form, screenshot the result")
    p.add_argument("--base", default="http://127.0.0.1:8811")
    p.add_argument("--target", default="")
    p.set_defaults(func=cmd_browse)

    p = sub.add_parser("api", help="submit and poll a scan over the JSON API")
    p.add_argument("--base", default="http://127.0.0.1:8811")
    p.add_argument("--target", required=True)
    p.add_argument("--limit", type=int, default=3000)
    p.set_defaults(func=cmd_api)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
