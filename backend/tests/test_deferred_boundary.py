"""The deferred Telugu, Urdu and Bengali rules cannot be reached through the service.

The rules are kept behind include_deferred_languages=True for a later release. These tests
send requests the way a caller could, with extra body fields, query parameters and headers
that try to switch the rules on, and check that the answer is the same as for a plain
request: nothing found in those languages, and the language reported as not analysed.

They also start the service in a fresh interpreter and watch which files it opens, to show
that the deferred term map is not read at startup or while answering a request.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.guidance import DEFERRED_TERM_MAP, GuidanceIndex
from app.main import app
from app.warning_signs import detect_warning_signs

client = TestClient(app)
BACKEND = Path(__file__).resolve().parents[1]

# Each is an urgency threat and a credential request once the deferred rules are on, and
# reaches phishing guidance through the deferred term map.
SCAMS = {
    "te": "మీ ఖాతా బ్లాక్ అవుతుంది, వెంటనే మీ ఓటీపీ చెప్పండి",
    "ur": "آپ کا اکاؤنٹ بلاک ہو جائے گا، فوراً اپنا او ٹی پی بتائیں",
    "bn": "আপনার অ্যাকাউন্ট ব্লক হয়ে যাবে, এখনই আপনার ওটিপি বলুন",
}

# Things a caller might add to a request to try to switch the deferred rules on.
ATTEMPTS = [
    {"include_deferred_languages": True},
    {"include_deferred_languages": "true", "deferred": True, "deferred_languages": True},
    {"language": "{tag}", "languages": ["te", "ur", "bn"], "lang": "{tag}", "locale": "{tag}"},
    {"coverage": "supported", "detected": "en", "term_map_path": "term_map_deferred.json"},
    {"options": {"include_deferred_languages": True}, "config": {"deferred": True}},
]


def _for_language(attempt: dict, tag: str) -> dict:
    return {key: tag if value == "{tag}" else value for key, value in attempt.items()}


@pytest.fixture(scope="module")
def deferred_index():
    return GuidanceIndex.from_file(include_deferred_languages=True)


@pytest.mark.parametrize("tag", SCAMS)
def test_the_deferred_rules_would_fire_if_they_were_on(tag, deferred_index):
    # Without this, the tests below would pass for a message the rules never matched.
    assert detect_warning_signs(SCAMS[tag], include_deferred_languages=True)
    assert deferred_index.search(SCAMS[tag])


@pytest.mark.parametrize("tag", SCAMS)
def test_a_plain_request_gets_no_deferred_behaviour(tag):
    body = client.post("/analyze", json={"message": SCAMS[tag]}).json()

    assert body["findings"] == []
    assert body["guidance"]["matches"] == []
    assert body["language"]["detected"] == tag
    assert body["language"]["coverage"] == "unsupported"
    assert "is not analysed" in body["language"]["notice"]
    assert body["classifier"]["status"] == "not_applicable"


@pytest.mark.parametrize("tag", SCAMS)
@pytest.mark.parametrize("attempt", ATTEMPTS)
def test_extra_body_fields_cannot_switch_the_deferred_rules_on(tag, attempt):
    plain = client.post("/analyze", json={"message": SCAMS[tag]})
    tried = client.post("/analyze", json={"message": SCAMS[tag], **_for_language(attempt, tag)})

    assert tried.status_code == 200
    assert tried.json() == plain.json()
    assert tried.json()["findings"] == []
    assert tried.json()["guidance"]["matches"] == []


@pytest.mark.parametrize("tag", SCAMS)
def test_query_parameters_and_headers_cannot_switch_the_deferred_rules_on(tag):
    plain = client.post("/analyze", json={"message": SCAMS[tag]})
    tried = client.post(
        "/analyze",
        json={"message": SCAMS[tag]},
        params={"include_deferred_languages": "true", "deferred": "1", "language": tag, "lang": tag},
        headers={
            "Accept-Language": tag,
            "Content-Language": tag,
            "X-Include-Deferred-Languages": "true",
            "Cookie": "include_deferred_languages=true",
        },
    )

    assert tried.status_code == 200
    assert tried.json() == plain.json()
    assert tried.json()["findings"] == []
    assert tried.json()["guidance"]["matches"] == []


def test_the_request_accepts_only_a_message():
    schema = client.get("/openapi.json").json()
    request = schema["components"]["schemas"]["AnalyzeRequest"]
    operation = schema["paths"]["/analyze"]["post"]

    assert set(request["properties"]) == {"message"}
    assert operation.get("parameters", []) == []
    # The other routes take no input at all.
    assert schema["paths"]["/next-steps"]["get"].get("parameters", []) == []
    assert schema["paths"]["/health"]["get"].get("parameters", []) == []


def test_next_steps_are_the_same_whatever_is_sent():
    plain = client.get("/next-steps").json()
    tried = client.get("/next-steps", params={"include_deferred_languages": "true", "language": "te"}).json()

    assert tried == plain
    text = json.dumps(plain, ensure_ascii=False)
    assert not any("ఀ" <= c <= "౿" or "ঀ" <= c <= "৿" or "؀" <= c <= "ۿ" for c in text)


# --- The deferred term map is not read by the service -------------------------------------

_WATCH_OPENED_FILES = """
import json, sys
opened = []
sys.addaudithook(lambda event, args: opened.append(str(args[0])) if event == "open" else None)

from fastapi.testclient import TestClient
import app.main as main

client = TestClient(main.app)
bodies = [client.post("/analyze", json={"message": m, "include_deferred_languages": True}).json() for m in MESSAGES]
client.get("/next-steps")
client.get("/health")
service = [name for name in opened if "term_map" in name]

from app.guidance import GuidanceIndex
GuidanceIndex.from_file(include_deferred_languages=True)
after_switch = [name for name in opened if "term_map" in name]

print(json.dumps({
    "findings": [len(body["findings"]) + len(body["guidance"]["matches"]) for body in bodies],
    "service": service,
    "after_switch": after_switch,
}))
"""


def test_the_service_never_reads_the_deferred_term_map():
    script = f"MESSAGES = {list(SCAMS.values())!r}\n{_WATCH_OPENED_FILES}"
    run = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", script], cwd=BACKEND, capture_output=True, text=True, encoding="utf-8", timeout=120
    )
    assert run.returncode == 0, run.stderr
    seen = json.loads(run.stdout.strip().splitlines()[-1])

    def names(paths):
        return {Path(path).name for path in paths}

    # Startup and requests read the Hindi map only.
    assert names(seen["service"]) == {"term_map.json"}
    assert seen["findings"] == [0, 0, 0]
    # The watcher does see the deferred map once the switch is used on purpose.
    assert DEFERRED_TERM_MAP.name in names(seen["after_switch"])
