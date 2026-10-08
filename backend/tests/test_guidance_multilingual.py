"""Tests for Telugu, Urdu and Bengali guidance retrieval through the term map.

The messages are short fixtures written for these tests and have not been reviewed by
native speakers. They check intended behaviour; they are not a measurement of retrieval
accuracy.
"""

import pytest

from app.guidance import DEFAULT_TERM_MAP, GuidanceIndex, TermMap, load_corpus

PHISHING = "certin-avoid-phishing"
CAPTCHA_JOBS = "i4c-captcha-jobs-2025"
REPORTING = "i4c-home"


@pytest.fixture(scope="module")
def index() -> GuidanceIndex:
    return GuidanceIndex.from_file()


def first_source(index: GuidanceIndex, message: str) -> str | None:
    matches = index.search(message)
    return matches[0].source.id if matches else None


# --- Positive retrieval ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("message", "expected_source"),
    [
        # Telugu
        ("మీ ఖాతా బ్లాక్ అవుతుంది, వెంటనే మీ ఓటీపీ చెప్పండి", PHISHING),
        ("లాటరీ బహుమతి కోసం మీ కార్డ్ వివరాలు పంపండి", PHISHING),
        ("క్యాప్చా జాబ్‌తో ఇంటి నుండి సంపాదించండి, రిజిస్ట్రేషన్ ఫీజు కట్టండి", CAPTCHA_JOBS),
        ("నేను మోసపోయాను, ఎక్కడ ఫిర్యాదు చేయాలి?", REPORTING),
        # Urdu
        ("آپ کا اکاؤنٹ بلاک ہو جائے گا، فوراً اپنا او ٹی پی بتائیں", PHISHING),
        ("لاٹری کے انعام کے لیے اپنے کارڈ کی تفصیلات بھیجیں", PHISHING),
        ("گھر بیٹھے کیپچا جاب سے کمائیں، رجسٹریشن فیس جمع کرائیں", CAPTCHA_JOBS),
        ("میرے ساتھ فراڈ ہوا ہے، شکایت کہاں کروں؟", REPORTING),
        # Bengali
        ("আপনার অ্যাকাউন্ট ব্লক হয়ে যাবে, এখনই আপনার ওটিপি বলুন", PHISHING),
        ("লটারির পুরস্কারের জন্য আপনার কার্ডের তথ্য পাঠান", PHISHING),
        ("ঘরে বসে ক্যাপচা জব করে আয় করুন, রেজিস্ট্রেশন ফি জমা দিন", CAPTCHA_JOBS),
        ("আমার সাথে প্রতারণা হয়েছে, কোথায় অভিযোগ করব?", REPORTING),
    ],
)
def test_messages_reach_existing_guidance(index, message, expected_source):
    assert first_source(index, message) == expected_source


@pytest.mark.parametrize(
    "message",
    [
        "నేను పొరపాటున నా ఓటీపీ చెప్పేశాను",
        "میں نے اپنا او ٹی پی بتا دیا ہے",
        "আমি আমার ওটিপি বলে দিয়েছি",
    ],
)
def test_responded_passage_is_found_for_someone_who_shared_a_code(index, message):
    matches = index.search(message)

    assert matches and matches[0].passage.id == "phishing-if-you-responded"


# --- Hard negatives ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "message",
    [
        # Safety advice
        "మీ ఓటీపీ ఎవరికీ చెప్పకండి",
        "బ్యాంక్ ఎప్పుడూ ఓటీపీ, పిన్ లేదా పాస్‌వర్డ్ అడగదు",
        "اپنا او ٹی پی کسی کو نہ بتائیں",
        "بینک کبھی او ٹی پی، پن یا پاس ورڈ نہیں مانگتا",
        "আপনার ওটিপি কাউকে বলবেন না",
        "ব্যাংক কখনো ওটিপি, পিন বা পাসওয়ার্ড চায় না",
        # Ordinary messages with mapped words
        "షాపు ఈరోజు మూసి ఉంటుంది",
        "నా కార్డ్ ఇంట్లో ఉంది",
        "دکان آج بند ہے",
        "میرا کارڈ گھر پر ہے",
        "দোকান আজ বন্ধ",
        "আমার কার্ড বাড়িতে আছে",
    ],
)
def test_safety_advice_and_ordinary_messages_get_no_guidance(index, message):
    assert index.search(message) == []


@pytest.mark.parametrize(
    "message",
    [
        "మీ ఓటీపీ ఎవరికీ చెప్పకండి. మీ ఖాతా బ్లాక్ అవుతుంది, వెంటనే ఓటీపీ పంపండి.",
        "اپنا او ٹی پی کسی کو نہ بتائیں۔ آپ کا اکاؤنٹ بلاک ہو جائے گا، فوراً او ٹی پی بھیجیں۔",
        "আপনার ওটিপি কাউকে বলবেন না। আপনার অ্যাকাউন্ট ব্লক হয়ে যাবে, এখনই ওটিপি পাঠান।",
    ],
)
def test_advice_in_one_sentence_does_not_hide_a_scam_in_another(index, message):
    assert first_source(index, message) == PHISHING


def test_term_map_does_not_bypass_the_match_rules(index):
    # One mapped word alone is not enough: the passage's match groups still apply.
    for word in ("ఓటీపీ", "ఖాతా", "او ٹی پی", "اکاؤنٹ", "ওটিপি", "অ্যাকাউন্ট"):
        assert index.search(word) == []


def test_matches_cite_the_same_validated_sources(index):
    sources, _ = load_corpus()

    for message in (
        "మీ ఖాతా బ్లాక్ అవుతుంది, వెంటనే మీ ఓటీపీ చెప్పండి",
        "آپ کا اکاؤنٹ بلاک ہو جائے گا، فوراً اپنا او ٹی پی بتائیں",
        "আপনার অ্যাকাউন্ট ব্লক হয়ে যাবে, এখনই আপনার ওটিপি বলুন",
    ):
        matches = index.search(message)
        assert matches
        for match in matches:
            assert match.source == sources[match.source.id]
            assert match.source.url.startswith("https://")


def test_term_map_expands_words_in_each_script(index):
    term_map = TermMap.from_file(DEFAULT_TERM_MAP, index.vocabulary)

    assert term_map.expand("ఓటీపీ") == ["otp"]
    assert term_map.expand("او ٹی پی") == ["otp"]
    assert term_map.expand("ওটিপি") == ["otp"]
    assert term_map.expand("ఖాతా") == ["account"]
    assert term_map.expand("اکاؤنٹ") == ["account"]
    assert term_map.expand("অ্যাকাউন্ট") == ["account"]
