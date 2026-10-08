"""Tests for the language estimate.

The messages are short fixtures written for these tests. They check the estimator's
behaviour on clear examples; they are not an evaluation of its accuracy.
"""

import pytest
from fastapi.testclient import TestClient

from app.language import (
    COVERAGE,
    METHOD,
    NOTICES,
    ROMAN_HINDI_CUES,
    estimate_language,
    estimate_tag,
)
from app.main import app

client = TestClient(app)

TAGS = {"en", "hi", "hi-Latn", "te", "ur", "bn", "mixed", "unknown"}


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        # English
        ("URGENT: Your SBI account will be blocked today. Update KYC at http://bit.ly/x", "en"),
        ("Hi, are we still meeting for lunch at 1 pm tomorrow?", "en"),
        # Common English words that look like Hindi are not counted.
        ("Is it me or is the train late again? Do you want to go to the main station?", "en"),
        ("The band played at the Bata showroom, Karen said it was great", "en"),
        ("ok", "en"),
        # Hindi in Devanagari, including a few English letters.
        ("आपका खाता बंद हो जाएगा। तुरंत अपना ओटीपी बताएं।", "hi"),
        ("आपका SBI खाता बंद हो जाएगा, तुरंत अपना ओटीपी बताएं", "hi"),
        # Clearly romanised Hindi.
        ("Aapka account block ho jayega, turant KYC update karein aur OTP batayein", "hi-Latn"),
        ("bhai OTP aaya kya? jaldi bata de", "hi-Latn"),
        # Mostly English with one Hindi word stays English.
        ("Hey, can you send the report today? Kal meeting hai, thanks", "en"),
        ("Your KYC is pending, please update today. धन्यवाद", "en"),
        # English and romanised Hindi in similar amounts.
        ("Please check the link, bhai, aur jaldi reply karo before the meeting tomorrow evening at the office", "mixed"),
        # Telugu, including English letters and a web address.
        ("మీ బ్యాంక్ ఖాతా బ్లాక్ చేయబడుతుంది, వెంటనే OTP చెప్పండి", "te"),
        ("మీ ఖాతా నిలిపివేయబడుతుంది. KYC అప్‌డేట్ చేయండి http://bit.ly/x", "te"),
        # Urdu and Bengali scripts.
        ("آپ کا اکاؤنٹ بند ہو جائے گا، فوراً او ٹی پی بتائیں", "ur"),
        ("আপনার অ্যাকাউন্ট বন্ধ হয়ে যাবে, এখনই ওটিপি দিন", "bn"),
        # Two scripts in similar amounts.
        ("Your account आपका खाता is blocked बंद हो जाएगा please update", "mixed"),
        # No letters, or a script outside the list.
        ("🙂🙂🙂", "unknown"),
        ("12345 678 ₹500", "unknown"),
        ("", "unknown"),
        ("   \n\t ", "unknown"),
        ("உங்கள் கணக்கு முடக்கப்படும்", "unknown"),
    ],
)
def test_estimated_tag(message, expected):
    assert estimate_tag(message) == expected


def test_web_addresses_do_not_count_as_english():
    telugu = "మీ ఖాతా నిలిపివేయబడుతుంది"
    with_links = f"{telugu} http://bit.ly/abcdefghijklmnop www.example.com/verify secure-bank.in/login"

    assert estimate_tag(with_links) == estimate_tag(telugu) == "te"


def test_one_romanised_hindi_word_is_not_enough():
    assert estimate_tag("Thanks bhai, see you at the office") == "en"


def test_cue_list_avoids_common_english_words_and_names():
    for word in ("is", "me", "to", "do", "main", "band", "mat", "hum", "karen", "bata", "the", "in", "a"):
        assert word not in ROMAN_HINDI_CUES


def test_estimate_is_deterministic():
    message = "Aapka account block ho jayega, turant KYC update karein"

    assert estimate_language(message) == estimate_language(message)


def test_every_tag_has_coverage_and_an_honest_notice():
    assert set(COVERAGE) == set(NOTICES) == TAGS
    assert COVERAGE["en"] == "supported"
    assert {COVERAGE[tag] for tag in ("te", "ur", "bn", "unknown")} == {"unsupported"}
    for tag, notice in NOTICES.items():
        assert notice.strip()
        assert "multilingual" not in notice.lower()
        if tag != "unknown":
            assert "estimate" in notice


# --- API ---------------------------------------------------------------------------


def test_analyze_includes_the_language_section():
    response = client.post("/analyze", json={"message": "आपका खाता बंद हो जाएगा। तुरंत अपना ओटीपी बताएं।"})

    assert response.status_code == 200
    assert response.json()["language"] == {
        "detected": "hi",
        "method": METHOD,
        "coverage": "partial",
        "notice": NOTICES["hi"],
    }


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Hi, are we still meeting for lunch at 1 pm tomorrow?", "en"),
        ("bhai OTP aaya kya? jaldi bata de", "hi-Latn"),
        ("మీ బ్యాంక్ ఖాతా బ్లాక్ చేయబడుతుంది, వెంటనే OTP చెప్పండి", "te"),
        ("🙂🙂🙂", "unknown"),
    ],
)
def test_analyze_reports_the_estimate(message, expected):
    language = client.post("/analyze", json={"message": message}).json()["language"]

    assert set(language) == {"detected", "method", "coverage", "notice"}
    assert language["detected"] == expected
    assert language["coverage"] == COVERAGE[expected]


def test_blank_message_is_still_rejected_before_estimation():
    response = client.post("/analyze", json={"message": "   "})

    assert response.status_code == 422


@pytest.mark.parametrize(
    "message",
    [
        "URGENT: Share your OTP to keep your account active.",
        "Aapka account block ho jayega, turant KYC update karein aur OTP batayein",
        "आपका खाता बंद हो जाएगा। तुरंत अपना ओटीपी बताएं।",
    ],
)
def test_language_estimate_does_not_change_findings_or_guidance(message, monkeypatch):
    import app.main as main_module

    before = client.post("/analyze", json={"message": message}).json()
    monkeypatch.setattr(main_module, "estimate_language", lambda text: estimate_language("unrelated english text"))
    after = client.post("/analyze", json={"message": message}).json()

    assert after["language"]["detected"] == "en"
    # The estimate only decides whether the English-only classifier runs.
    for key in ("findings", "notice", "guidance"):
        assert after[key] == before[key]
