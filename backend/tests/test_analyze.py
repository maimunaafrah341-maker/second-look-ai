import logging

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.classifier import Classifier
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
    assert set(body) == {"findings", "notice", "guidance", "classifier", "language"}
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
        # Tamil is not mapped. (Telugu now is; see test_guidance_multilingual.py.)
        "உங்கள் வங்கி கணக்கு முடக்கப்படும், உடனே OTP சொல்லுங்கள்",
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

    assert set(body) == {"findings", "notice", "guidance", "classifier", "language"}
    assert set(body["guidance"]) == {"matches", "notice"}
    assert NOT_SAFE_FINDINGS in body["notice"]
    text = response.text.lower().replace(NOT_SAFE_GUIDANCE, "")
    for claim in ("is safe", "is legitimate", "is not a scam", "no risk", "verdict", "probability"):
        assert claim not in text


# --- Auxiliary classifier ------------------------------------------------------------


class StubPipeline:
    """Returns a fixed score, so tests control the classifier label exactly."""

    classes_ = [0, 1]

    def __init__(self, score):
        self.score = score

    def predict_proba(self, texts):
        return [[1 - self.score, self.score] for _ in texts]


def use_classifier(monkeypatch, score=None):
    """Swap in a stub classifier with a fixed score, or an unavailable one when score is None."""
    if score is None:
        stub = Classifier()
    else:
        metadata = {"model_name": "stub", "model_sha256": "0" * 64, "threshold": 0.5}
        stub = Classifier(StubPipeline(score), metadata, positive_column=1)
    monkeypatch.setattr(main_module, "classifier", stub)


def test_classifier_section_when_ok(monkeypatch):
    use_classifier(monkeypatch, score=0.9)

    section = analyze_message("Free entry! Call now to claim your reward")["classifier"]

    assert set(section) == {"status", "label", "model", "notice"}
    assert section["status"] == "ok"
    assert section["label"] == "spam_like"
    assert set(section["model"]) == {"name", "training_data", "model_sha256"}
    assert "UCI SMS Spam Collection" in section["model"]["training_data"]
    assert "cannot tell whether this message is fraudulent" in section["notice"]
    assert "does not mean the message is safe" in section["notice"]


def test_classifier_section_when_unavailable(monkeypatch):
    use_classifier(monkeypatch, score=None)

    body = analyze_message("URGENT: Share your OTP to keep your account active.")

    assert body["classifier"] == {
        "status": "unavailable",
        "label": None,
        "model": None,
        "notice": main_module.CLASSIFIER_UNAVAILABLE_NOTICE,
    }
    # The rest of the analysis still works.
    assert body["findings"]
    assert body["guidance"]["matches"]


def test_classifier_section_when_not_applicable(monkeypatch):
    use_classifier(monkeypatch, score=0.9)

    body = analyze_message("आपका खाता बंद हो जाएगा। तुरंत अपना ओटीपी बताएं।")

    assert body["classifier"]["status"] == "not_applicable"
    assert body["classifier"]["label"] is None
    assert "does not appear to be mainly in English" in body["classifier"]["notice"]
    # The Hindi warning-sign rules still run.
    assert body["findings"]


def test_real_classifier_is_loaded_at_startup():
    body = analyze_message("Hi, are we still meeting for lunch at 1 pm tomorrow?")

    assert body["classifier"]["status"] == "ok"
    assert body["classifier"]["model"]["name"] == "char_tfidf_logistic_regression"


@pytest.mark.parametrize("score", [0.0, 0.3, 0.9])
def test_classifier_never_exposes_a_score(monkeypatch, score):
    use_classifier(monkeypatch, score=score)

    response = client.post("/analyze", json={"message": "Update KYC by clicking http://bit.ly/x"})

    section = response.json()["classifier"]
    for key in ("score", "probability", "confidence", "similarity", "risk"):
        assert key not in section
    assert str(score) not in str(section)


@pytest.mark.parametrize(
    "message",
    [
        # Rules fire (urgency, credential request); guidance matches.
        "URGENT: Share your OTP to keep your account active.",
        # No rule fires; guidance matches.
        "I met someone on a matrimony site and he wants me to invest in crypto for high returns",
        # Rules fire; no guidance.
        "Your electricity will be disconnected tonight at 9.30 pm. Contact officer.",
    ],
)
def test_classifier_label_never_changes_findings_or_guidance(monkeypatch, message):
    use_classifier(monkeypatch, score=0.0)
    low = analyze_message(message)
    use_classifier(monkeypatch, score=1.0)
    high = analyze_message(message)
    use_classifier(monkeypatch, score=None)
    unavailable = analyze_message(message)

    assert low["classifier"]["label"] == "not_spam_like"
    assert high["classifier"]["label"] == "spam_like"
    for other in (high, unavailable):
        assert other["findings"] == low["findings"]
        assert other["notice"] == low["notice"]
        assert other["guidance"] == low["guidance"]


def test_classifier_and_warning_signs_can_disagree(monkeypatch):
    use_classifier(monkeypatch, score=0.0)
    body = analyze_message("URGENT: Share your OTP to keep your account active.")
    assert body["findings"] and body["classifier"]["label"] == "not_spam_like"

    use_classifier(monkeypatch, score=1.0)
    body = analyze_message("Hi, are we still meeting for lunch at 1 pm tomorrow?")
    assert body["findings"] == [] and body["classifier"]["label"] == "spam_like"
    assert NOT_SAFE_FINDINGS in body["notice"]


def test_classifier_and_guidance_can_disagree(monkeypatch):
    use_classifier(monkeypatch, score=0.0)

    body = analyze_message(
        "I met someone on a matrimony site and he wants me to invest in crypto for high returns"
    )

    assert body["guidance"]["matches"]
    assert body["classifier"]["label"] == "not_spam_like"
    assert "does not mean the message is safe" in body["classifier"]["notice"]


def test_genuine_bank_alert_is_rated_spam_like_by_the_real_model():
    # Documented false positive of the UCI-trained model on a genuine Indian bank alert.
    # The response must still carry no verdict, and the rules find nothing.
    body = analyze_message("Rs 2,000 debited from A/c XX1234 on 03-Oct. Not you? Call your bank.")

    assert body["classifier"]["status"] == "ok"
    assert body["classifier"]["label"] == "spam_like"
    assert body["findings"] == []
    assert "Genuine bank, OTP and delivery messages are often rated spam-like" in body["classifier"]["notice"]


def test_analyze_does_not_log_message_text(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)

    for score in (None, 0.0, 1.0):
        use_classifier(monkeypatch, score=score)
        client.post("/analyze", json={"message": "SECRET-MARKER URGENT share OTP http://bit.ly/x"})
    client.post("/analyze", json={"message": "SECRET-MARKER" + "x" * MAX_MESSAGE_LENGTH})

    assert "SECRET-MARKER" not in caplog.text
