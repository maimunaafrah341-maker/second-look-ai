"""Tests for Hindi and romanised-Hindi guidance retrieval through the term map.

The messages are short fixtures written for these tests. They check intended behaviour;
they are not a measurement of retrieval accuracy.
"""

import json

import pytest

from app.guidance import (
    DEFAULT_CORPUS,
    DEFAULT_TERM_MAP,
    CorpusError,
    GuidanceIndex,
    TermMap,
    load_corpus,
)

PHISHING = "certin-avoid-phishing"
CAPTCHA_JOBS = "i4c-captcha-jobs-2025"
MATRIMONIAL = "i4c-matrimonial-investment-2025"
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
        # Credential scams
        ("आपका खाता बंद हो जाएगा। तुरंत अपना ओटीपी बताएं।", PHISHING),
        ("Turant OTP bhejo warna khata band ho jayega", PHISHING),
        # Account / KYC scam
        ("आपका केवाईसी लंबित है, खाता ब्लॉक हो जाएगा, तुरंत लिंक पर क्लिक करें", PHISHING),
        # Prize scam asking for card details
        ("लॉटरी में इनाम जीता है, अपना कार्ड विवरण भेजें तुरंत", PHISHING),
        # Fee-for-job scams
        ("घर बैठे कमाई करें, कैप्चा जॉब के लिए पंजीकरण शुल्क जमा करें", CAPTCHA_JOBS),
        ("Ghar baithe kamai karein, captcha job ke liye registration fee jama karo", CAPTCHA_JOBS),
        ("Naukri ke liye shulk jama karo, roz 2000 kamao", CAPTCHA_JOBS),
        # Matrimonial investment scam
        ("शादी की वेबसाइट पर मिले व्यक्ति ने क्रिप्टो में निवेश करने को कहा", MATRIMONIAL),
        # Someone who has already responded
        ("मैंने लिंक पर क्लिक कर दिया और पासवर्ड डाल दिया, अब क्या करूं", PHISHING),
        ("Maine OTP bata diya, ab kya karun?", PHISHING),
        # Reporting
        ("मेरे साथ धोखाधड़ी हुई है, शिकायत कहां करें", REPORTING),
        ("Mere saath dhokha hua, shikayat kaise karein", REPORTING),
    ],
)
def test_hindi_messages_reach_existing_guidance(index, message, expected_source):
    assert first_source(index, message) == expected_source


@pytest.mark.parametrize(
    "message",
    [
        "Aapka account block ho jayega, OTP batayein",
        "Your account will be blocked, OTP बताएं",
    ],
)
def test_mixed_hindi_and_english_terms_combine(index, message):
    matches = index.search(message)

    assert matches and matches[0].source.id == PHISHING
    assert {"account", "blocked", "otp"} <= set(matches[0].matched_terms)


def test_responded_passage_is_found_for_a_hindi_victim(index):
    matches = index.search("Maine OTP bata diya, ab kya karun?")

    assert matches[0].passage.id == "phishing-if-you-responded"


# --- Hard negatives ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "message",
    [
        "OTP किसी को न बताएं",
        "OTP किसी के साथ साझा न करें",
        "OTP kisi ko na batayein",
        "OTP kisi ko mat bhejo",
        "OTP share mat karo",
        "Bank kabhi OTP nahi maangta",
        # Personal conversation mentioning an OTP
        "भाई, ओटीपी आया क्या? मम्मी के फोन पर आया होगा",
        # Genuine bank OTP message and a bank safety notice
        "आपका ओटीपी 482913 है। यह 10 मिनट में समाप्त हो जाएगा। इसे किसी के साथ साझा न करें। - SBI",
        "बैंक कभी भी ओटीपी, पिन या पासवर्ड नहीं मांगता। ऐसे कॉल से सावधान रहें।",
        # Advice that describes a scam message
        "Bank kabhi OTP nahi maangta. Turant block ho jayega aisa koi message aaye to dhyan rakhein",
        # Everyday words that are also mapped
        "दुकान आज बंद है, कल मिलते हैं",
        "मेरा कार्ड घर पर रह गया",
    ],
)
def test_hindi_safety_advice_and_ordinary_messages_get_no_guidance(index, message):
    assert index.search(message) == []


def test_advice_in_one_sentence_does_not_hide_a_scam_in_another(index):
    message = "OTP किसी को न बताएं। आपका खाता ब्लॉक हो जाएगा, तुरंत ओटीपी भेजें।"

    assert first_source(index, message) == PHISHING


def test_term_map_does_not_bypass_the_match_rules(index):
    # One mapped term alone is not enough: the passage's match groups still apply.
    assert index.search("ओटीपी") == []
    assert index.search("खाता") == []
    assert index.search("शुल्क जमा करें") == []


def test_hindi_matches_cite_the_same_validated_sources(index):
    sources, _ = load_corpus()

    for message in ("आपका खाता बंद हो जाएगा। तुरंत अपना ओटीपी बताएं।", "Naukri ke liye shulk jama karo, roz 2000 kamao"):
        for match in index.search(message):
            assert match.source == sources[match.source.id]
            assert match.source.url.startswith("https://")


def test_without_the_term_map_hindi_retrieves_nothing():
    plain = GuidanceIndex.from_file(term_map_path=None)

    assert plain.search("आपका खाता बंद हो जाएगा। तुरंत अपना ओटीपी बताएं।") == []


# --- Term map file -------------------------------------------------------------------------


def test_shipped_term_map_is_small_and_points_only_to_corpus_terms(index):
    data = json.loads(DEFAULT_TERM_MAP.read_text(encoding="utf-8"))
    terms = [term for group in data["concepts"].values() for term in group]

    # Hindi, romanised Hindi, Telugu, Urdu and Bengali together.
    assert len(terms) <= 300
    assert set(data["concepts"]) <= index.vocabulary
    # The map is not used to restate English words.
    for word in ("account", "otp", "fee", "fees", "block", "band", "link", "card", "registration", "delivery"):
        assert word not in terms


def write_map(tmp_path, concepts) -> object:
    path = tmp_path / "term_map.json"
    path.write_text(json.dumps({"concepts": concepts}, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "concepts",
    [
        {},
        {"not_a_corpus_term": ["ओटीपी"]},
        {"otp": []},
        {"otp": [""]},
        {"otp": ["ओटीपी!"]},
        # An English corpus term may not be remapped.
        {"otp": ["account"]},
        {"otp": ["ओटीपी"], "pin": ["ओटीपी"]},
    ],
)
def test_invalid_term_maps_are_rejected(tmp_path, index, concepts):
    with pytest.raises(CorpusError):
        TermMap.from_file(write_map(tmp_path, concepts), index.vocabulary)


def test_unreadable_term_map_is_rejected(tmp_path, index):
    path = tmp_path / "term_map.json"
    path.write_text("not json", encoding="utf-8")

    with pytest.raises(CorpusError):
        TermMap.from_file(path, index.vocabulary)
    with pytest.raises(CorpusError):
        GuidanceIndex.from_file(DEFAULT_CORPUS, tmp_path / "missing.json")


def test_term_map_expands_words_and_phrases(index):
    term_map = TermMap.from_file(DEFAULT_TERM_MAP, index.vocabulary)

    assert term_map.expand("ओटीपी") == ["otp"]
    assert term_map.expand("Khata band ho jayega") == ["account", "blocked"]
    assert term_map.expand("maine OTP bata diya") == ["shared"]
    assert term_map.expand("Hello, how are you?") == []
