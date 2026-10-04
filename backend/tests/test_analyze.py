import pytest
from fastapi.testclient import TestClient

from app.guidance import load_corpus
from app.main import MAX_MESSAGE_LENGTH, app

client = TestClient(app)


def test_analyze_returns_structured_findings():
    response = client.post(
        "/analyze",
        json={"message": "URGENT: Share your OTP to keep your account active."},
    )

    assert response.status_code == 200
    body = response.json()
    # No verdict or probability fields: rule-based findings and retrieved guidance only.
    assert set(body) == {"findings", "notice", "guidance"}
    assert [finding["category"] for finding in body["findings"]] == [
        "urgency_pressure",
        "credential_request",
    ]
    for finding in body["findings"]:
        assert set(finding) == {"category", "explanation", "evidence"}
    assert "cannot determine whether a message is fraudulent" in body["notice"]


def test_analyze_payment_demand_with_url():
    response = client.post(
        "/analyze",
        json={"message": "Pay Rs 500 customs fee to release your parcel: http://bit.ly/parcel-fee"},
    )

    assert response.status_code == 200
    assert [finding["category"] for finding in response.json()["findings"]] == [
        "link",
        "payment_demand",
    ]


def test_analyze_benign_message_returns_no_findings_but_keeps_notice():
    response = client.post(
        "/analyze",
        json={"message": "Hi, are we still meeting for lunch at 1 pm tomorrow?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["findings"] == []
    assert "may still be a scam" in body["notice"]


@pytest.mark.parametrize("message", ["", "   ", "\n\t  "])
def test_analyze_rejects_blank_message(message):
    response = client.post("/analyze", json={"message": message})

    assert response.status_code == 422


@pytest.mark.parametrize("payload", [{}, {"message": None}, {"message": 123}])
def test_analyze_rejects_missing_or_non_string_message(payload):
    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


def test_analyze_accepts_message_at_maximum_length():
    response = client.post("/analyze", json={"message": "a" * MAX_MESSAGE_LENGTH})

    assert response.status_code == 200


def test_analyze_rejects_message_over_maximum_length():
    response = client.post("/analyze", json={"message": "a" * (MAX_MESSAGE_LENGTH + 1)})

    assert response.status_code == 422


def test_analyze_returns_official_guidance_separately_from_findings():
    response = client.post(
        "/analyze",
        json={"message": "Earn Rs 5000 daily with a captcha typing job. Pay registration fee Rs 500 to start."},
    )

    assert response.status_code == 200
    guidance = response.json()["guidance"]
    assert set(guidance) == {"matches", "notice"}
    assert "not a judgement about this message" in guidance["notice"]

    first = guidance["matches"][0]
    assert set(first) == {"topic", "summary", "summary_note", "source", "matched_terms"}
    assert "not a quotation" in first["summary_note"]
    assert set(first["source"]) == {"title", "publisher", "url", "published", "retrieved", "section"}
    assert first["source"]["title"] == "Advisory on 'Rise in Fake Captcha Filling Jobs' based cybercrime"
    assert first["source"]["url"].startswith("https://i4c.mha.gov.in/")
    assert first["source"]["published"] == "2025-04-08"
    # Similarity is never presented as a score or a fraud probability.
    assert not {"score", "similarity", "confidence", "probability"} & set(first)


def test_analyze_guidance_sources_all_come_from_the_corpus():
    sources, _ = load_corpus()
    known = {(source.title, source.publisher, source.url) for source in sources.values()}

    response = client.post(
        "/analyze",
        json={"message": "Update KYC by clicking this link http://bit.ly/x or your account is blocked"},
    )

    matches = response.json()["guidance"]["matches"]
    assert matches
    for match in matches:
        source = match["source"]
        assert (source["title"], source["publisher"], source["url"]) in known


@pytest.mark.parametrize(
    "message",
    [
        "Hi, are we still meeting for lunch at 1 pm tomorrow?",
        "आपका खाता बंद हो जाएगा। तुरंत अपना ओटीपी बताएं।",
    ],
)
def test_analyze_without_matching_guidance_says_so_without_implying_safety(message):
    response = client.post("/analyze", json={"message": message})

    assert response.status_code == 200
    guidance = response.json()["guidance"]
    assert guidance["matches"] == []
    assert "No matching official guidance was found" in guidance["notice"]
    assert "does not mean the message is safe" in guidance["notice"]


@pytest.mark.parametrize(
    "payload",
    [
        {"message": "   "},
        {"message": "SECRET-MARKER-" + "x" * MAX_MESSAGE_LENGTH},
        {"message": ["SECRET-MARKER"]},
        {"text": "SECRET-MARKER"},
    ],
)
def test_validation_errors_do_not_echo_the_submitted_content(payload):
    response = client.post("/analyze", json=payload)

    assert response.status_code == 422
    assert "SECRET-MARKER" not in response.text
    for item in response.json()["detail"]:
        assert set(item) == {"loc", "msg", "type"}


def test_malformed_json_body_is_rejected_without_echo():
    response = client.post(
        "/analyze",
        content=b'{"message": "SECRET-MARKER',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert "SECRET-MARKER" not in response.text


# --- Rules and retrieval can disagree; neither silence means "safe" ---------------

NOT_SAFE_FINDINGS = "a message with no indicators may still be a scam"
NOT_SAFE_GUIDANCE = "does not mean the message is safe"
NOT_A_JUDGEMENT = "not a judgement about this message"


def analyze_message(message: str) -> dict:
    response = client.post("/analyze", json={"message": message})
    assert response.status_code == 200
    return response.json()


def test_findings_without_guidance():
    body = analyze_message("Your electricity will be disconnected tonight at 9.30 pm. Contact officer.")

    assert [finding["category"] for finding in body["findings"]] == ["urgency_pressure"]
    assert body["guidance"]["matches"] == []
    assert NOT_SAFE_GUIDANCE in body["guidance"]["notice"]


def test_guidance_without_findings():
    body = analyze_message(
        "I met someone on a matrimony site and he wants me to invest in crypto for high returns"
    )

    assert body["findings"] == []
    assert body["guidance"]["matches"]
    assert NOT_SAFE_FINDINGS in body["notice"]
    assert NOT_A_JUDGEMENT in body["guidance"]["notice"]


def test_neither_findings_nor_guidance_is_not_presented_as_safe():
    body = analyze_message("Hi, are we still meeting for lunch at 1 pm tomorrow?")

    assert body["findings"] == []
    assert body["guidance"]["matches"] == []
    assert NOT_SAFE_FINDINGS in body["notice"]
    assert NOT_SAFE_GUIDANCE in body["guidance"]["notice"]


def test_a_known_scam_pattern_can_return_nothing_at_all():
    # Guidance for this scam is held back for review and no rule covers it, so both sections
    # are empty. The notices are the only protection against reading that as "safe".
    body = analyze_message(
        "This is Mumbai police. A parcel in your name contains drugs. You are under digital "
        "arrest, stay on the video call."
    )

    assert body["findings"] == []
    assert body["guidance"]["matches"] == []
    assert NOT_SAFE_FINDINGS in body["notice"]
    assert NOT_SAFE_GUIDANCE in body["guidance"]["notice"]


@pytest.mark.parametrize(
    "message",
    [
        "Hi, are we still meeting for lunch at 1 pm tomorrow?",
        "Your electricity will be disconnected tonight at 9.30 pm. Contact officer.",
        "I met someone on a matrimony site and he wants me to invest in crypto for high returns",
        "URGENT: Share your OTP to keep your account active.",
    ],
)
def test_response_never_carries_a_verdict_or_safety_claim(message):
    response = client.post("/analyze", json={"message": message})
    body = response.json()

    assert set(body) == {"findings", "notice", "guidance"}
    assert set(body["guidance"]) == {"matches", "notice"}
    assert NOT_SAFE_FINDINGS in body["notice"]
    text = response.text.lower().replace(NOT_SAFE_GUIDANCE, "")
    for claim in ("is safe", "is legitimate", "is not a scam", "no risk", "verdict", "probability"):
        assert claim not in text
