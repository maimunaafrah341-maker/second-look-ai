"""Deploy Second Look to Render and check that the live service works.

Used by the GitLab pipeline, and runnable by hand from the repository root:

    python ops/release.py mirror --commit <sha>       # wait for the GitHub mirror to have <sha>
    python ops/release.py deploy                      # call the Render deploy hooks
    python ops/release.py wait --commit <sha>         # wait until the backend serves <sha>
    python ops/release.py smoke                       # check the live site
    python ops/release.py smoke --agent               # also run the AI agent once

Deploy hooks are read from RENDER_BACKEND_DEPLOY_HOOK and RENDER_FRONTEND_DEPLOY_HOOK, and
the site addresses from SECOND_LOOK_BACKEND_URL and SECOND_LOOK_FRONTEND_URL (defaults:
the public Render services). The hooks are secrets: they are never printed.

The smoke checks use fixed messages and expect the same results the tests expect. They
send no personal data. With --agent, one fixed message goes through the agent, which
sends it to Google or Groq like any other agent run.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from evaluation.evaluate_agent import CLAIM_PHRASES, find_in, model_written  # noqa: E402

DEFAULT_BACKEND = "https://second-look-ai.onrender.com"
DEFAULT_FRONTEND = "https://second-look-ai-1.onrender.com"
USER_AGENT = "second-look-release/1.0"

SCAM = "URGENT: Your account will be blocked within 24 hours. Share your OTP at http://bit.ly/verify-now"
BENIGN = "Hi, are we still meeting for lunch at 1 pm tomorrow?"
EXPECTED_SCAM_SIGNS = {"urgency_pressure", "credential_request", "link"}
AGENT_ANSWER = "shared_details"


@dataclass
class Check:
    name: str
    passed: bool
    detail: str
    seconds: float


def request(url: str, payload: dict | None = None, timeout: float = 120.0) -> tuple[int, bytes]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"User-Agent": USER_AGENT}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def get_json(url: str, payload: dict | None = None, timeout: float = 120.0) -> tuple[int, dict]:
    status, body = request(url, payload, timeout)
    try:
        return status, json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return status, {}


def timed(name: str, check: Callable[[], tuple[bool, str]]) -> Check:
    started = time.monotonic()
    try:
        passed, detail = check()
    except (urllib.error.URLError, OSError, KeyError, TypeError, ValueError) as error:
        passed, detail = False, f"{type(error).__name__}: {error}"
    return Check(name, passed, detail, round(time.monotonic() - started, 2))


# --- Checks ------------------------------------------------------------------------------


def check_health(backend: str, wake_seconds: float, sleep: Callable[[float], None] = time.sleep) -> tuple[bool, str]:
    # A free Render service sleeps when idle; the first request can take a minute or more.
    deadline = time.monotonic() + wake_seconds
    while True:
        try:
            status, body = get_json(f"{backend}/health", timeout=60)
            if status == 200 and body == {"status": "ok"}:
                return True, "backend is up"
            detail = f"HTTP {status}"
        except (urllib.error.URLError, OSError) as error:
            detail = type(error).__name__
        if time.monotonic() >= deadline:
            return False, f"backend did not answer: {detail}"
        sleep(10)


def check_scam_analysis(backend: str) -> tuple[bool, str]:
    status, body = get_json(f"{backend}/analyze", {"message": SCAM})
    found = {finding["category"] for finding in body.get("findings", [])}
    if status != 200 or not EXPECTED_SCAM_SIGNS <= found:
        return False, f"HTTP {status}, warning signs {sorted(found)}"
    if "cannot determine whether a message is fraudulent" not in body["notice"]:
        return False, "the notice that rules cannot decide fraud is missing"
    return True, f"found {', '.join(sorted(found))}"


def check_benign_analysis(backend: str) -> tuple[bool, str]:
    status, body = get_json(f"{backend}/analyze", {"message": BENIGN})
    if status != 200 or body.get("findings") != []:
        return False, f"HTTP {status}, findings {body.get('findings')}"
    if "may still be a scam" not in body["notice"]:
        return False, "no findings, but the notice no longer says that is not a sign of safety"
    return True, "no warning signs, and the notice still says that is not proof of safety"


def check_next_steps(backend: str) -> tuple[bool, str]:
    status, body = get_json(f"{backend}/next-steps")
    situations = {situation["id"]: situation for situation in body.get("situations", [])}
    if status != 200 or len(situations) != 4:
        return False, f"HTTP {status}, {len(situations)} situations"
    first = situations["lost_money"]["steps"][0]
    if (first.get("action") or {}).get("href") != "tel:1930":
        return False, "losing money no longer puts the 1930 helpline first"
    return True, "4 situations; losing money starts with Call 1930"


def check_frontend(frontend: str) -> tuple[bool, str]:
    status, page = request(frontend, timeout=60)
    if status != 200:
        return False, f"HTTP {status}"
    scripts = re.findall(rb'src="(/assets/[^"]+\.js)"', page)
    if not scripts:
        return False, "no script found on the page"
    status, bundle = request(frontend.rstrip("/") + scripts[0].decode(), timeout=60)
    if status != 200 or b"Investigate with AI agent" not in bundle:
        return False, "the page does not contain the agent button"
    return True, "page loads and offers the agent"


def check_agent(backend: str) -> tuple[bool, str]:
    status, first = get_json(f"{backend}/agent", {"message": SCAM}, timeout=240)
    if status != 200:
        return False, f"HTTP {status}"
    responses = [first]
    if first["status"] == "needs_input":
        status, second = get_json(f"{backend}/agent", {"message": SCAM, "situation": AGENT_ANSWER}, timeout=240)
        if status != 200:
            return False, f"second request: HTTP {status}"
        responses.append(second)
    last = responses[-1]
    claims = find_in([text for response in responses for text in model_written(response)], CLAIM_PHRASES)
    if claims:
        return False, f"a verdict reached the user: {claims[0]}"
    if last["status"] != "finished":
        return False, f"the agent ended with status {last['status']}"
    steps = sum(len(response["trace"]) for response in responses)
    providers = sorted({step["provider"] for response in responses for step in response["trace"] if step.get("provider")})
    return True, f"finished in {steps} steps via {'/'.join(providers)}, no verdict shown"


def run_smoke(backend: str, frontend: str, agent: bool, wake_seconds: float) -> list[Check]:
    checks = [timed("Backend health", lambda: check_health(backend, wake_seconds))]
    if not checks[0].passed:
        return checks
    checks += [
        timed("Warning signs on a known scam", lambda: check_scam_analysis(backend)),
        timed("No false alarm on an ordinary message", lambda: check_benign_analysis(backend)),
        timed("Official next steps", lambda: check_next_steps(backend)),
        timed("Frontend", lambda: check_frontend(frontend)),
    ]
    if agent:
        checks.append(timed("AI agent end to end", lambda: check_agent(backend)))
    return checks


def markdown(checks: list[Check], backend: str) -> str:
    failed = [check for check in checks if not check.passed]
    lines = [
        "## Second Look live checks",
        "",
        f"Backend: {backend}",
        "",
        f"**{'FAILED' if failed else 'Passed'}**: {len(checks) - len(failed)} of {len(checks)} checks passed.",
        "",
        "| Check | Result | Seconds | Detail |",
        "| --- | --- | --- | --- |",
    ]
    lines += [f"| {c.name} | {'pass' if c.passed else '**FAIL**'} | {c.seconds} | {c.detail} |" for c in checks]
    return "\n".join(lines) + "\n"


# --- Deploy --------------------------------------------------------------------------------


def deploy(hooks: dict[str, str]) -> int:
    missing = [name for name, url in hooks.items() if not url]
    if missing:
        print(f"Missing deploy hook variables: {', '.join(missing)}")
        return 1
    for name, url in hooks.items():
        status, _ = request(url, payload={}, timeout=60)
        # The hook URL holds a secret key, so only the variable name is printed.
        print(f"{name}: HTTP {status}")
        if status >= 300:
            return 1
    return 0


def wait_for_commit(backend: str, commit: str, timeout: float, sleep: Callable[[float], None] = time.sleep) -> bool:
    deadline = time.monotonic() + timeout
    while True:
        try:
            status, body = get_json(f"{backend}/version", timeout=60)
            live = body.get("commit", "") if status == 200 else ""
        except (urllib.error.URLError, OSError):
            live = ""
        if live and live[:12] == commit[:12]:
            print(f"The backend is serving {live[:12]}.")
            return True
        print(f"Live commit {live[:12] or 'unknown'}; waiting for {commit[:12]}...")
        if time.monotonic() >= deadline:
            return False
        sleep(20)


def wait_for_mirror(repo: str, branch: str, commit: str, timeout: float, sleep: Callable[[float], None] = time.sleep) -> bool:
    """Wait until a GitHub push mirror has the commit, so Render builds the right one.

    Only needed while the Render services are still connected to the GitHub copy of the
    repository rather than to GitLab.
    """
    deadline = time.monotonic() + timeout
    while True:
        try:
            status, body = get_json(f"https://api.github.com/repos/{repo}/commits/{branch}", timeout=60)
            mirrored = body.get("sha", "") if status == 200 else ""
        except (urllib.error.URLError, OSError):
            mirrored = ""
        if mirrored == commit:
            print(f"{repo} {branch} is at {commit[:12]}.")
            return True
        print(f"{repo} {branch} is at {mirrored[:12] or 'unknown'}; waiting for {commit[:12]}...")
        if time.monotonic() >= deadline:
            return False
        sleep(15)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--backend", default=os.environ.get("SECOND_LOOK_BACKEND_URL") or DEFAULT_BACKEND)
    parser.add_argument("--frontend", default=os.environ.get("SECOND_LOOK_FRONTEND_URL") or DEFAULT_FRONTEND)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("deploy", help="Call the Render deploy hooks")
    mirror = commands.add_parser("mirror", help="Wait for the GitHub mirror to have a commit")
    mirror.add_argument("--commit", required=True)
    mirror.add_argument("--repo", default=os.environ.get("GITHUB_MIRROR_REPO", ""))
    mirror.add_argument("--branch", default="main")
    mirror.add_argument("--timeout", type=float, default=600)
    wait = commands.add_parser("wait", help="Wait until the backend serves a commit")
    wait.add_argument("--commit", required=True)
    wait.add_argument("--timeout", type=float, default=900)
    smoke = commands.add_parser("smoke", help="Check the live site")
    smoke.add_argument("--agent", action="store_true", help="Also run the AI agent once")
    smoke.add_argument("--wake-seconds", type=float, default=180)
    smoke.add_argument("--report", type=Path)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    backend, frontend = args.backend.rstrip("/"), args.frontend.rstrip("/")

    if args.command == "deploy":
        return deploy(
            {
                "RENDER_BACKEND_DEPLOY_HOOK": os.environ.get("RENDER_BACKEND_DEPLOY_HOOK", ""),
                "RENDER_FRONTEND_DEPLOY_HOOK": os.environ.get("RENDER_FRONTEND_DEPLOY_HOOK", ""),
            }
        )
    if args.command == "mirror":
        if not args.repo:
            print("No GitHub mirror configured (GITHUB_MIRROR_REPO); nothing to wait for.")
            return 0
        return 0 if wait_for_mirror(args.repo, args.branch, args.commit, args.timeout) else 1
    if args.command == "wait":
        return 0 if wait_for_commit(backend, args.commit, args.timeout) else 1

    checks = run_smoke(backend, frontend, args.agent, args.wake_seconds)
    report = markdown(checks, backend)
    print(report)
    if args.report:
        args.report.write_text(report, encoding="utf-8")
        args.report.with_suffix(".json").write_text(json.dumps([asdict(check) for check in checks], indent=2), encoding="utf-8")
    return 0 if all(check.passed for check in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
