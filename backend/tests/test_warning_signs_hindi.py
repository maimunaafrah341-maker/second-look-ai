"""Tests for the Hindi (Devanagari) and romanised-Hindi warning-sign patterns.

The messages are short fixtures written for these tests. They check that the listed
phrases behave as intended; they are not an evaluation of accuracy on real messages.
"""

import pytest

from app.warning_signs import (
    CREDENTIAL_REQUEST,
    LINK,
    MAX_EVIDENCE_LENGTH,
    PAYMENT_DEMAND,
    URGENCY,
    detect_warning_signs,
)


def categories(message: str) -> list[str]:
    return [finding.category for finding in detect_warning_signs(message)]


def evidence(message: str, category: str) -> str:
    return next(f.evidence for f in detect_warning_signs(message) if f.category == category)


# --- Hindi (Devanagari) ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("message", "expected_evidence"),
    [
        ("तुरंत कॉल करें", "तुरंत"),
        ("अंतिम चेतावनी: अपना केवाईसी अपडेट करें", "अंतिम चेतावनी"),
        ("आपका अकाउंट आज रात ब्लॉक कर दिया जाएगा", "अकाउंट आज रात ब्लॉक कर दिया जाएगा"),
        ("आपका खाता बंद हो जाएगा।", "खाता बंद हो जाएगा"),
        ("बिल बकाया है, आज ही भुगतान करें", "आज ही भुगतान"),
    ],
)
def test_hindi_urgency(message, expected_evidence):
    assert URGENCY in categories(message)
    assert evidence(message, URGENCY) == expected_evidence


@pytest.mark.parametrize(
    ("message", "expected_evidence"),
    [
        ("कृपया अपना OTP भेजें", "OTP भेजें"),
        ("अपना ओटीपी बताएं", "ओटीपी बताएं"),
        ("अपना ओटीपी बताएँ", "ओटीपी बताएँ"),
        ("अपना एटीएम पिन बता दीजिए", "पिन बता दीजिए"),
        ("पासवर्ड शेयर करें और इनाम पाएं", "पासवर्ड शेयर करें"),
        ("अपना पासवर्ड हमारे साथ साझा करें", "पासवर्ड हमारे साथ साझा करें"),
    ],
)
def test_hindi_credential_request(message, expected_evidence):
    assert CREDENTIAL_REQUEST in categories(message)
    assert evidence(message, CREDENTIAL_REQUEST) == expected_evidence


@pytest.mark.parametrize(
    ("message", "expected_evidence"),
    [
        ("पार्सल छुड़ाने के लिए पैसे भेजें", "पैसे भेजें"),
        ("बिल का भुगतान करें", "भुगतान करें"),
        ("नौकरी के लिए फीस जमा करें", "फीस जमा करें"),
        ("इनाम के लिए 500 रुपये प्रोसेसिंग शुल्क जमा करें", "प्रोसेसिंग शुल्क"),
        ("पंजीकरण शुल्क भरें", "पंजीकरण शुल्क"),
    ],
)
def test_hindi_payment_demand(message, expected_evidence):
    assert PAYMENT_DEMAND in categories(message)
    assert evidence(message, PAYMENT_DEMAND) == expected_evidence


@pytest.mark.parametrize(
    "message",
    [
        "OTP किसी को न बताएं",
        "OTP किसी के साथ साझा न करें",
        "PIN किसी को मत भेजें",
        "अपना पासवर्ड किसी को ना बताएं",
        # Negation after the verb, then a danda.
        "बैंक कभी भी आपसे ओटीपी नहीं मांगता। ओटीपी बताएं नहीं।",
        "आपका ओटीपी 482913 है। इसे किसी के साथ साझा न करें।",
    ],
)
def test_hindi_safety_advice_is_not_a_credential_request(message):
    assert CREDENTIAL_REQUEST not in categories(message)


@pytest.mark.parametrize(
    "message",
    [
        # Everyday "now", "will close", and "I have paid" are not warning signs.
        "मैं अभी घर पर हूँ, शाम को मिलते हैं",
        "दुकान आज रात 9 बजे बंद हो जाएगी",
        "मैंने बिल का भुगतान कर दिया है",
        "आपका पिन कोड क्या है?",
    ],
)
def test_ordinary_hindi_is_not_flagged(message):
    assert detect_warning_signs(message) == []


# --- Romanised Hindi ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("message", "expected_evidence"),
    [
        ("Aapka account block ho jayega, turant KYC update karein.", "account block ho jayega"),
        ("Aapka khaata bandh ho jaayega", "khaata bandh ho jaayega"),
        ("Aapka khata band ho jayega", "khata band ho jayega"),
        ("Antim chetavani: KYC pending", "Antim chetavani"),
        ("Turant call karo", "Turant"),
        ("Abhi call karo warna service ruk jayegi", "Abhi call"),
        ("Aaj hi payment karein", "Aaj hi payment"),
    ],
)
def test_romanised_urgency(message, expected_evidence):
    assert URGENCY in categories(message)
    assert evidence(message, URGENCY) == expected_evidence


@pytest.mark.parametrize(
    ("message", "expected_evidence"),
    [
        ("Apna OTP batao jaldi", "OTP batao"),
        ("OTP bataye please", "OTP bataye"),
        ("Apna OTP batayein", "OTP batayein"),
        ("OTP bata do bhai", "OTP bata do"),
        # "na" after the verb is a softener ("please tell"), not a negation.
        ("OTP bata do na", "OTP bata do"),
        ("OTP bhejo", "OTP bhejo"),
        ("Apna OTP bhejein", "OTP bhejein"),
        ("OTP share karo", "OTP share karo"),
        ("Apna OTP share karein verification ke liye", "OTP share karein"),
        ("ATM PIN bhejiye", "PIN bhejiye"),
        ("Apna password batao", "password batao"),
    ],
)
def test_romanised_credential_request(message, expected_evidence):
    assert CREDENTIAL_REQUEST in categories(message)
    assert evidence(message, CREDENTIAL_REQUEST) == expected_evidence


@pytest.mark.parametrize(
    ("message", "expected_evidence"),
    [
        ("Inaam ke liye paise bhejo", "paise bhejo"),
        ("Paisa bhej do", "Paisa bhej do"),
        ("Turant paise bhejein", "paise bhejein"),
        ("Payment karo", "Payment karo"),
        ("Payment kar do warna connection kat jayega", "Payment kar do"),
        ("Fees bharo", "Fees bharo"),
        ("Loan ke liye fees bharein", "fees bharein"),
        ("Registration fee Rs 499 jama karo", "Registration fee"),
        ("Processing fee pehle deni hogi", "Processing fee"),
    ],
)
def test_romanised_payment_demand(message, expected_evidence):
    assert PAYMENT_DEMAND in categories(message)
    assert evidence(message, PAYMENT_DEMAND) == expected_evidence


@pytest.mark.parametrize(
    "message",
    [
        "OTP kisi ko na batayein",
        "OTP kisi ko mat bhejo",
        "OTP share mat karo",
        "PIN kisi ko mat bhejo",
        "OTP share na karein",
        "Bank kabhi OTP nahi maangta, OTP share na karein",
        "OTP share karo mat",
        "OTP batao nahi kisi ko",
    ],
)
def test_romanised_safety_advice_is_not_a_credential_request(message):
    assert CREDENTIAL_REQUEST not in categories(message)


@pytest.mark.parametrize(
    "message",
    [
        # Past tense describes what someone did; it is not a request.
        "Maine payment kar diya hai bhai",
        "OTP share kar diya maine, ab kya karun?",
        # Everyday "now" / "today itself".
        "Main abhi ghar pe hoon",
        "Aaj hi milte hain shaam ko",
        # "Tatkal" is also a railway booking quota.
        "Tatkal ticket book ho gaya",
        # English words that look like Hindi forms.
        "The band played well and Karen loved the show",
    ],
)
def test_ordinary_romanised_hindi_is_not_flagged(message):
    assert detect_warning_signs(message) == []


# --- Mixed Hindi and English -----------------------------------------------------------------


def test_mixed_account_block_threat_is_urgency_but_not_a_credential_request():
    # "Update your KYC" is not a request for an OTP, PIN, or password.
    assert categories("Aapka account block ho jayega, turant KYC update karein.") == [URGENCY]


def test_mixed_request_negated_in_hindi_is_not_a_credential_request():
    # "Please share your OTP, don't (do it)": contradictory, so no finding.
    assert CREDENTIAL_REQUEST not in categories("Please share your OTP mat karo")


def test_mixed_scam_produces_findings_from_both_languages():
    message = "Dear customer, OTP batayein warna account block ho jayega. Visit http://bit.ly/x"

    assert categories(message) == [URGENCY, CREDENTIAL_REQUEST, LINK]


def test_language_independent_signals_still_work_in_other_scripts():
    telugu = "మీ ఖాతా బ్లాక్ అవుతుంది. Pay ₹500 now at http://bit.ly/x"

    assert categories(telugu) == [LINK, PAYMENT_DEMAND]
    assert evidence(telugu, LINK) == "http://bit.ly/x"
    assert evidence(telugu, PAYMENT_DEMAND) == "Pay ₹500"


# --- Regression: shared behaviour ----------------------------------------------------------


def test_evidence_is_cut_from_the_original_text():
    message = "Aapka   KHAATA   bandh ho jaayega!!"

    # Case and spacing as written; only whitespace is collapsed, as for English.
    assert evidence(message, URGENCY) == "KHAATA bandh ho jaayega"


def test_category_order_and_maximum_count_are_unchanged():
    message = (
        "अंतिम चेतावनी! अपना ओटीपी बताएं और प्रोसेसिंग शुल्क जमा करें: http://bit.ly/x. "
        "URGENT: share your PIN and pay Rs 200 processing fee."
    )

    assert categories(message) == [URGENCY, CREDENTIAL_REQUEST, LINK, PAYMENT_DEMAND]


def test_hindi_evidence_respects_the_length_limit():
    message = "आपका खाता " + "बहुत " * 3 + "जल्द बंद हो जाएगा" + " अतिरिक्त" * 60

    for finding in detect_warning_signs(message):
        assert len(finding.evidence) <= MAX_EVIDENCE_LENGTH
