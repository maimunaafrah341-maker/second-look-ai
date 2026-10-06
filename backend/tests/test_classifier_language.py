"""Tests for running the English-only classifier according to the estimated language.

Messages are short fixtures written for these tests.
"""

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.classifier import NOT_APPLICABLE, NOT_ENGLISH_LANGUAGES, OK, UNAVAILABLE, Classifier
from app.language import estimate_tag
from app.main import app

client = TestClient(app)


class StubPipeline:
    classes_ = [0, 1]

    def predict_proba(self, texts):
        return [[0.1, 0.9] for _ in texts]


def stub() -> Classifier:
    return Classifier(StubPipeline(), {"model_name": "stub", "model_sha256": "0" * 64, "threshold": 0.5})


def test_gated_languages_are_exactly_the_non_english_estimates():
    assert NOT_ENGLISH_LANGUAGES == {"hi", "hi-Latn", "te", "ur", "bn", "mixed"}


@pytest.mark.parametrize("language", sorted(NOT_ENGLISH_LANGUAGES))
def test_non_english_estimates_are_not_classified(language):
    # Plain English letters, so only the language estimate can stop the model.
    result = stub().classify("Your account will be blocked, share OTP now", language)

    assert result.status == NOT_APPLICABLE
    assert result.label is None
    assert result.model["name"] == "stub"


@pytest.mark.parametrize("language", ["en", "unknown", None])
def test_english_unknown_or_missing_estimate_leaves_the_existing_behaviour(language):
    result = stub().classify("Your account will be blocked, share OTP now", language)

    assert result.status == OK
    assert result.label == "spam_like"


def test_script_check_still_applies_when_the_estimate_is_unknown():
    assert stub().classify("உங்கள் கணக்கு முடக்கப்படும்", "unknown").status == NOT_APPLICABLE


def test_unavailable_model_stays_unavailable_for_any_language():
    for language in ("en", "hi", "mixed", None):
        assert Classifier().classify("hello there friend", language).status == UNAVAILABLE


# --- Through the API -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("message", "expected_language", "expected_status"),
    [
        ("Hi, are we still meeting for lunch at 1 pm tomorrow?", "en", "ok"),
        ("URGENT: Share your OTP to keep your account active.", "en", "ok"),
        ("आपका खाता बंद हो जाएगा। तुरंत अपना ओटीपी बताएं।", "hi", "not_applicable"),
        ("Aapka account block ho jayega, turant KYC update karein aur OTP batayein", "hi-Latn", "not_applicable"),
        ("bhai OTP aaya kya? jaldi bata de", "hi-Latn", "not_applicable"),
        ("Please check the link, bhai, aur jaldi reply karo before the meeting tomorrow evening at the office", "mixed", "not_applicable"),
        ("Your account आपका खाता is blocked बंद हो जाएगा please update", "mixed", "not_applicable"),
        ("మీ బ్యాంక్ ఖాతా బ్లాక్ చేయబడుతుంది, వెంటనే OTP చెప్పండి", "te", "not_applicable"),
        ("آپ کا اکاؤنٹ بند ہو جائے گا، فوراً او ٹی پی بتائیں", "ur", "not_applicable"),
        ("আপনার অ্যাকাউন্ট বন্ধ হয়ে যাবে, এখনই ওটিপি দিন", "bn", "not_applicable"),
        # Mostly English with one Hindi word is still classified.
        ("Hey, can you send the report today? Kal meeting hai, thanks", "en", "ok"),
        # A laugh is not Hindi.
        ("Ho ho - big belly laugh! See ya tomo", "en", "ok"),
    ],
)
def test_api_classifier_follows_the_language_estimate(monkeypatch, message, expected_language, expected_status):
    monkeypatch.setattr(main_module, "classifier", stub())

    body = client.post("/analyze", json={"message": message}).json()

    assert body["language"]["detected"] == expected_language
    assert body["classifier"]["status"] == expected_status
    if expected_status == "not_applicable":
        assert body["classifier"]["label"] is None
        assert body["classifier"]["notice"] == main_module.CLASSIFIER_NOT_APPLICABLE_NOTICE
        assert "does not mean the message is safe" in body["classifier"]["notice"]


def test_romanised_hindi_scam_keeps_its_findings_and_guidance_when_not_classified(monkeypatch):
    monkeypatch.setattr(main_module, "classifier", stub())

    body = client.post("/analyze", json={"message": "Aapka account block ho jayega, OTP batayein"}).json()

    assert body["classifier"]["status"] == "not_applicable"
    assert body["findings"]
    assert body["guidance"]["matches"]


def test_real_model_is_not_run_on_romanised_hindi():
    # With the committed model: a romanised-Hindi job scam that the model used to rate
    # spam-like is now not classified at all, rather than given an untested label.
    message = "Ghar baithe kamaayein, captcha job ke liye registration fee Rs 500 bharein, jaldi karo bhai"

    body = client.post("/analyze", json={"message": message}).json()

    assert estimate_tag(message) in NOT_ENGLISH_LANGUAGES
    assert body["classifier"]["status"] == "not_applicable"
