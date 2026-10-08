"""Tests for the deferred Telugu, Urdu and Bengali warning-sign patterns.

These languages are not part of the current release: the service does not run these
patterns. They are kept for a future release, and these tests keep them working by
calling detect_warning_signs with include_deferred_languages=True. The last tests check
that the service itself leaves them switched off.

The messages are short fixtures written for these tests and have not been reviewed by
native speakers. They check that the listed phrases behave as intended; they are not an
evaluation of accuracy on real messages.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.warning_signs import (
    CREDENTIAL_REQUEST,
    LINK,
    MAX_EVIDENCE_LENGTH,
    PAYMENT_DEMAND,
    URGENCY,
    detect_warning_signs,
)

client = TestClient(app)


def detect(message: str):
    """Detection with the deferred Telugu, Urdu and Bengali patterns switched on."""
    return detect_warning_signs(message, include_deferred_languages=True)


def categories(message: str) -> list[str]:
    return [finding.category for finding in detect(message)]


def evidence(message: str, category: str) -> str:
    return next(f.evidence for f in detect(message) if f.category == category)


def assert_found(message: str, category: str, key: str) -> None:
    """The category is found, and its evidence is cut from the message and contains the key words."""
    assert category in categories(message), message
    quote = evidence(message, category)
    assert quote in " ".join(message.split())
    assert key in quote


# --- Telugu ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("message", "key"),
    [
        ("మీ ఖాతా బ్లాక్ అవుతుంది", "బ్లాక్ అవుతుంది"),
        ("మీ బ్యాంక్ ఖాతా రేపు బ్లాక్ చేయబడుతుంది", "బ్లాక్ చేయబడుతుంది"),
        ("మీ SIM నిలిపివేయబడుతుంది", "నిలిపివేయబడుతుంది"),
        ("చివరి హెచ్చరిక: మీ బిల్లు బకాయి ఉంది", "చివరి హెచ్చరిక"),
        ("వెంటనే కాల్ చేయండి", "వెంటనే"),
        ("తక్షణమే అప్‌డేట్ చేయండి", "తక్షణమే"),
    ],
)
def test_telugu_urgency(message, key):
    assert_found(message, URGENCY, key)


@pytest.mark.parametrize(
    ("message", "key"),
    [
        ("మీ OTP చెప్పండి", "OTP"),
        ("మీ ఓటీపీ పంపండి", "ఓటీపీ"),
        ("మీ ATM పిన్ చెప్పు", "పిన్"),
        ("మీ పాస్‌వర్డ్ షేర్ చేయండి", "పాస్‌వర్డ్"),
        # The same word typed without the zero-width non-joiner.
        ("మీ పాస్వర్డ్ చెప్పండి", "పాస్వర్డ్"),
        ("మీ కార్డ్ వివరాలు పంపండి", "కార్డ్ వివరాలు"),
        ("మీ CVV ఇవ్వండి", "CVV"),
    ],
)
def test_telugu_credential_request(message, key):
    assert_found(message, CREDENTIAL_REQUEST, key)


@pytest.mark.parametrize(
    ("message", "key"),
    [
        ("రిజిస్ట్రేషన్ ఫీజు రూ.499 చెల్లించండి", "ఫీజు"),
        ("ప్రాసెసింగ్ ఫీజు కట్టండి", "ఫీజు"),
        ("వెంటనే డబ్బు పంపండి", "డబ్బు పంపండి"),
        ("ఈ బిల్లు చెల్లించండి", "చెల్లించండి"),
    ],
)
def test_telugu_payment_demand(message, key):
    assert_found(message, PAYMENT_DEMAND, key)


@pytest.mark.parametrize(
    "message",
    [
        "మీ OTP ఎవరికీ చెప్పకండి",
        "OTP ఎవరితోనూ షేర్ చేయకండి",
        "పిన్ ఎవరికీ పంపవద్దు",
        "బ్యాంక్ ఎప్పుడూ OTP అడగదు",
    ],
)
def test_telugu_safety_advice_is_not_a_credential_request(message):
    assert CREDENTIAL_REQUEST not in categories(message)


@pytest.mark.parametrize(
    "message",
    [
        "నేను ఇప్పుడు ఇంట్లో ఉన్నాను",
        # "Right away" about the speaker's own action is not pressure.
        "నేను వెంటనే ఇంటికి వెళ్తాను",
        "షాపు ఈరోజు మూసి ఉంటుంది",
        "మీ పిన్ కోడ్ ఏమిటి?",
        # Past tense: "I paid the bill".
        "నేను బిల్లు చెల్లించాను",
    ],
)
def test_ordinary_telugu_is_not_flagged(message):
    assert detect(message) == []


# --- Urdu --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("message", "key"),
    [
        ("آپ کا اکاؤنٹ بند ہو جائے گا", "بند ہو جائے گا"),
        ("آپ کی SIM بلاک ہو جائے گی", "بلاک ہو جائے گی"),
        ("آخری وارننگ: آپ کا بل باقی ہے", "آخری وارننگ"),
        ("فوراً کال کریں", "فوراً"),
        ("فوری طور پر اپڈیٹ کریں", "فوری طور پر"),
    ],
)
def test_urdu_urgency(message, key):
    assert_found(message, URGENCY, key)


@pytest.mark.parametrize(
    ("message", "key"),
    [
        ("اپنا او ٹی پی بتائیں", "او ٹی پی"),
        ("اپنا OTP بھیجیں", "OTP"),
        ("اپنا پن بتاؤ", "پن"),
        ("اپنا پاس ورڈ شیئر کریں", "پاس ورڈ"),
        ("اپنے کارڈ کی تفصیلات بھیجیں", "کارڈ کی تفصیلات"),
    ],
)
def test_urdu_credential_request(message, key):
    assert_found(message, CREDENTIAL_REQUEST, key)


@pytest.mark.parametrize(
    ("message", "key"),
    [
        ("رجسٹریشن فیس جمع کرائیں", "فیس"),
        ("پروسیسنگ فیس ادا کریں", "فیس"),
        ("فوراً پیسے بھیجیں", "پیسے بھیجیں"),
        ("یہ بل ادا کریں", "ادا کریں"),
    ],
)
def test_urdu_payment_demand(message, key):
    assert_found(message, PAYMENT_DEMAND, key)


@pytest.mark.parametrize(
    "message",
    [
        "اپنا او ٹی پی کسی کو نہ بتائیں",
        "OTP کسی کے ساتھ شیئر نہ کریں",
        "پن کسی کو مت بھیجو",
        "بینک کبھی او ٹی پی نہیں مانگتا",
    ],
)
def test_urdu_safety_advice_is_not_a_credential_request(message):
    assert CREDENTIAL_REQUEST not in categories(message)


@pytest.mark.parametrize(
    "message",
    [
        "میں ابھی گھر پر ہوں",
        "میں فوراً گھر جاؤں گا",
        "دکان آج بند ہے",
        "آپ کا پن کوڈ کیا ہے؟",
        # "Punjab" begins with the letters of "pin"; it is not a PIN.
        "میں پنجاب جا رہا ہوں، بتاؤ کیا لانا ہے",
        # Past tense: "I have paid the bill".
        "میں نے بل ادا کر دیا ہے",
    ],
)
def test_ordinary_urdu_is_not_flagged(message):
    assert detect(message) == []


# --- Bengali -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("message", "key"),
    [
        ("আপনার অ্যাকাউন্ট বন্ধ হয়ে যাবে", "বন্ধ হয়ে যাবে"),
        ("আপনার SIM ব্লক হয়ে যাবে", "ব্লক হয়ে যাবে"),
        ("শেষ সতর্কতা: আপনার বিল বকেয়া", "শেষ সতর্কতা"),
        ("এখনই কল করুন", "এখনই"),
        ("অবিলম্বে আপডেট করুন", "অবিলম্বে"),
    ],
)
def test_bengali_urgency(message, key):
    assert_found(message, URGENCY, key)


@pytest.mark.parametrize(
    ("message", "key"),
    [
        ("আপনার ওটিপি বলুন", "ওটিপি"),
        ("আপনার OTP পাঠান", "OTP"),
        ("আপনার পিন দিন", "পিন"),
        ("আপনার পাসওয়ার্ড শেয়ার করুন", "পাসওয়ার্ড"),
        ("আপনার কার্ডের তথ্য পাঠান", "কার্ডের তথ্য"),
    ],
)
def test_bengali_credential_request(message, key):
    assert_found(message, CREDENTIAL_REQUEST, key)


@pytest.mark.parametrize(
    ("message", "key"),
    [
        ("রেজিস্ট্রেশন ফি জমা দিন", "ফি"),
        ("প্রসেসিং ফি দিন", "ফি"),
        ("এখনই টাকা পাঠান", "টাকা পাঠান"),
        ("এই বিল পরিশোধ করুন", "পরিশোধ করুন"),
    ],
)
def test_bengali_payment_demand(message, key):
    assert_found(message, PAYMENT_DEMAND, key)


@pytest.mark.parametrize(
    "message",
    [
        "আপনার ওটিপি কাউকে বলবেন না",
        "OTP কারো সাথে শেয়ার করবেন না",
        "পিন কাউকে পাঠাবেন না",
        "ব্যাংক কখনো ওটিপি চায় না",
    ],
)
def test_bengali_safety_advice_is_not_a_credential_request(message):
    assert CREDENTIAL_REQUEST not in categories(message)


@pytest.mark.parametrize(
    "message",
    [
        "আমি এখন বাড়িতে আছি",
        # "Right now" about the speaker's own action is not pressure.
        "আমি এখনই বাড়ি যাচ্ছি",
        "দোকান আজ বন্ধ থাকবে",
        "আপনার পিন কোড কী?",
        # Past tense: "I have paid the bill".
        "আমি বিল পরিশোধ করেছি",
        # "Every day" ends in the letters of "give"; it is not a request.
        "আমি প্রতিদিন সকালে হাঁটি",
    ],
)
def test_ordinary_bengali_is_not_flagged(message):
    assert detect(message) == []


# --- Shared behaviour --------------------------------------------------------------------


@pytest.mark.parametrize(
    "message",
    [
        "చివరి హెచ్చరిక! మీ OTP చెప్పండి, రిజిస్ట్రేషన్ ఫీజు చెల్లించండి: http://bit.ly/x",
        "آخری وارننگ! اپنا OTP بتائیں اور رجسٹریشن فیس ادا کریں: http://bit.ly/x",
        "শেষ সতর্কতা! আপনার OTP বলুন এবং রেজিস্ট্রেশন ফি জমা দিন: http://bit.ly/x",
    ],
)
def test_category_order_and_maximum_count_are_unchanged(message):
    assert categories(message) == [URGENCY, CREDENTIAL_REQUEST, LINK, PAYMENT_DEMAND]


@pytest.mark.parametrize(
    "message",
    [
        "మీ ఖాతా " + "చాలా " * 3 + "త్వరలో బ్లాక్ అవుతుంది" + " అదనపు" * 60,
        "آپ کا اکاؤنٹ " + "بہت " * 3 + "جلد بند ہو جائے گا" + " اضافی" * 60,
        "আপনার অ্যাকাউন্ট " + "খুব " * 3 + "শীঘ্রই বন্ধ হয়ে যাবে" + " অতিরিক্ত" * 60,
    ],
)
def test_evidence_respects_the_length_limit(message):
    for finding in detect(message):
        assert len(finding.evidence) <= MAX_EVIDENCE_LENGTH


def test_advice_in_one_sentence_does_not_hide_a_request_in_another():
    message = "OTP ఎవరికీ చెప్పకండి అని బ్యాంక్ చెబుతుంది. కానీ ఇప్పుడు మీ OTP పంపండి."

    assert CREDENTIAL_REQUEST in categories(message)


@pytest.mark.parametrize(
    "message",
    [
        "మీ బ్యాంక్ ఖాతా బ్లాక్ అవుతుంది, వెంటనే మీ OTP చెప్పండి",
        "آپ کا اکاؤنٹ بند ہو جائے گا، فوراً اپنا OTP بتائیں",
        "আপনার অ্যাকাউন্ট বন্ধ হয়ে যাবে, এখনই আপনার OTP বলুন",
    ],
)
def test_the_service_does_not_apply_the_deferred_patterns(message):
    # With the switch on, these are an urgency threat and a credential request.
    assert categories(message) == [URGENCY, CREDENTIAL_REQUEST]
    # The default, which the service uses, finds nothing in these languages.
    assert detect_warning_signs(message) == []

    body = client.post("/analyze", json={"message": message}).json()

    assert body["findings"] == []
    assert body["guidance"]["matches"] == []
    assert body["language"]["coverage"] == "unsupported"
    assert "is not analysed" in body["language"]["notice"]
    assert "does not mean the message is safe" in body["guidance"]["notice"]
    assert body["classifier"]["status"] == "not_applicable"
    assert set(body) == {"findings", "notice", "guidance", "classifier", "language"}


def test_signals_that_need_no_language_are_still_found_in_these_scripts():
    body = client.post("/analyze", json={"message": "మీ ఖాతా బ్లాక్ అవుతుంది. Pay ₹500 now at http://bit.ly/x"}).json()

    assert [finding["category"] for finding in body["findings"]] == [LINK, PAYMENT_DEMAND]
