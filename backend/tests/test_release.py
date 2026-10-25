"""Tests for ops/release.py: deploy hooks, waiting for a commit, and the live checks.

No test here reaches the network; requests are replaced with fixed replies.
"""

import json

import pytest

import release
from release import Check, deploy, markdown, run_smoke, wait_for_commit

BACKEND = "https://backend.example"
FRONTEND = "https://frontend.example"

GOOD_SCAM = {
    "findings": [{"category": name} for name in ("urgency_pressure", "credential_request", "link")],
    "notice": "These are rule-based indicators only. They cannot determine whether a message is fraudulent.",
}
GOOD_BENIGN = {"findings": [], "notice": "a message with no indicators may still be a scam"}
GOOD_STEPS = {
    "situations": [
        {"id": "not_responded", "steps": []},
        {"id": "clicked_link", "steps": []},
        {"id": "shared_details", "steps": []},
        {"id": "lost_money", "steps": [{"action": {"label": "Call 1930", "href": "tel:1930"}}]},
    ]
}
AGENT_QUESTION = {"status": "needs_input", "text": None, "trace": [{"provider": "gemini", "reason": None, "args": {}}]}
AGENT_DONE = {
    "status": "finished",
    "text": "Three warning signs were found. Call 1930 to report it.",
    "trace": [{"provider": "groq", "reason": "Checking first.", "args": {}}],
}


def fake_site(monkeypatch, overrides=None):
    """Replace HTTP with fixed replies, keyed by method and path."""
    replies = {
        ("GET", "/health"): (200, {"status": "ok"}),
        ("POST", "/analyze", release.SCAM): (200, GOOD_SCAM),
        ("POST", "/analyze", release.BENIGN): (200, GOOD_BENIGN),
        ("GET", "/next-steps"): (200, GOOD_STEPS),
        ("POST", "/agent", None): (200, AGENT_QUESTION),
        ("POST", "/agent", "shared_details"): (200, AGENT_DONE),
        ("GET", "page"): (200, b'<script type="module" src="/assets/index-abc.js"></script>'),
        ("GET", "/assets/index-abc.js"): (200, b"...Investigate with AI agent..."),
    }
    replies.update(overrides or {})
    calls = []

    def fake_request(url, payload=None, timeout=120.0):
        calls.append((url, payload))
        if url == FRONTEND:
            status, body = replies[("GET", "page")]
        else:
            path = url.split(".example", 1)[1]
            if payload is None:
                status, body = replies[("GET", path)]
            elif path == "/analyze":
                status, body = replies[("POST", path, payload["message"])]
            elif path == "/agent":
                status, body = replies[("POST", path, payload.get("situation"))]
            else:
                status, body = 200, {}
        return status, body if isinstance(body, bytes) else json.dumps(body).encode()

    monkeypatch.setattr(release, "request", fake_request)
    return calls


def test_a_working_site_passes_every_check(monkeypatch):
    calls = fake_site(monkeypatch)

    checks = run_smoke(BACKEND, FRONTEND, agent=True, wake_seconds=0)

    assert [check.name for check in checks] == [
        "Backend health",
        "Warning signs on a known scam",
        "No false alarm on an ordinary message",
        "Official next steps",
        "Frontend",
        "AI agent end to end",
    ]
    assert all(check.passed for check in checks), [check for check in checks if not check.passed]
    assert "via gemini/groq" in checks[-1].detail
    assert sum(1 for url, _ in calls if url.endswith("/agent")) == 2


def test_the_agent_is_only_run_when_asked(monkeypatch):
    calls = fake_site(monkeypatch)

    checks = run_smoke(BACKEND, FRONTEND, agent=False, wake_seconds=0)

    assert len(checks) == 5
    assert not any(url.endswith("/agent") for url, _ in calls)


@pytest.mark.parametrize(
    ("override", "failing", "detail"),
    [
        ({("POST", "/analyze", release.SCAM): (200, {"findings": [], "notice": "x"})}, "Warning signs on a known scam", "warning signs"),
        ({("POST", "/analyze", release.BENIGN): (200, {"findings": [], "notice": "All clear."})}, "No false alarm on an ordinary message", "not a sign of safety"),
        ({("GET", "/next-steps"): (200, {"situations": GOOD_STEPS["situations"][:3]})}, "Official next steps", "3 situations"),
        ({("GET", "/assets/index-abc.js"): (200, b"old build")}, "Frontend", "agent button"),
        ({("POST", "/agent", "shared_details"): (200, {**AGENT_DONE, "text": "This message is safe."})}, "AI agent end to end", "verdict"),
        ({("POST", "/agent", "shared_details"): (200, {**AGENT_DONE, "status": "unavailable", "text": None})}, "AI agent end to end", "unavailable"),
    ],
)
def test_each_check_catches_its_own_failure(monkeypatch, override, failing, detail):
    fake_site(monkeypatch, override)

    checks = {check.name: check for check in run_smoke(BACKEND, FRONTEND, agent=True, wake_seconds=0)}

    assert not checks[failing].passed and detail in checks[failing].detail
    assert all(check.passed for name, check in checks.items() if name != failing)


def test_a_backend_that_never_wakes_stops_the_other_checks(monkeypatch):
    fake_site(monkeypatch, {("GET", "/health"): (503, {})})
    monkeypatch.setattr(release.time, "sleep", lambda seconds: None)

    checks = run_smoke(BACKEND, FRONTEND, agent=True, wake_seconds=0)

    assert len(checks) == 1 and not checks[0].passed and "503" in checks[0].detail


def test_waits_until_the_new_commit_is_live(monkeypatch):
    commits = iter(["oldcommit000000", "oldcommit000000", "newcommit111111aaaa"])
    monkeypatch.setattr(release, "get_json", lambda url, payload=None, timeout=120.0: (200, {"commit": next(commits)}))
    waits = []

    assert wait_for_commit(BACKEND, "newcommit111111aaaabbbb", timeout=600, sleep=waits.append)
    assert len(waits) == 2


def test_gives_up_when_the_commit_never_arrives(monkeypatch):
    monkeypatch.setattr(release, "get_json", lambda url, payload=None, timeout=120.0: (200, {"commit": "unknown"}))

    assert not wait_for_commit(BACKEND, "newcommit", timeout=0, sleep=lambda seconds: None)


def test_deploy_needs_both_hooks_and_never_prints_them(monkeypatch, capsys):
    secret = "https://api.render.com/deploy/srv-123?key=SECRET-KEY"
    monkeypatch.setattr(release, "request", lambda url, payload=None, timeout=60: (200, b""))

    assert deploy({"RENDER_BACKEND_DEPLOY_HOOK": secret, "RENDER_FRONTEND_DEPLOY_HOOK": ""}) == 1
    assert deploy({"RENDER_BACKEND_DEPLOY_HOOK": secret, "RENDER_FRONTEND_DEPLOY_HOOK": secret}) == 0
    assert "SECRET-KEY" not in capsys.readouterr().out


def test_report_marks_failures():
    report = markdown([Check("Frontend", False, "HTTP 502", 1.0), Check("Backend health", True, "up", 0.5)], BACKEND)

    assert "FAILED" in report and "| Frontend | **FAIL** | 1.0 | HTTP 502 |" in report


def test_waits_for_the_github_mirror_before_render_builds(monkeypatch):
    seen = iter(["old", "new-sha"])
    urls = []

    def fake_get_json(url, payload=None, timeout=120.0):
        urls.append(url)
        return 200, {"sha": next(seen)}

    monkeypatch.setattr(release, "get_json", fake_get_json)

    assert release.wait_for_mirror("owner/repo", "main", "new-sha", timeout=600, sleep=lambda seconds: None)
    assert urls[0] == "https://api.github.com/repos/owner/repo/commits/main"
