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


def test_urgent_message_requesting_otp():
    message = "URGENT: Your account will be blocked within 24 hours. Share your OTP to verify."

    findings = {finding.category: finding for finding in detect_warning_signs(message)}

    assert set(findings) == {URGENCY, CREDENTIAL_REQUEST}
    assert findings[URGENCY].evidence == "URGENT"
    assert findings[CREDENTIAL_REQUEST].evidence == "Share your OTP"
    assert findings[CREDENTIAL_REQUEST].explanation


def test_payment_demand_with_url():
    message = "Pay Rs 500 customs fee to release your parcel: http://bit.ly/parcel-fee."

    findings = {finding.category: finding for finding in detect_warning_signs(message)}

    assert set(findings) == {LINK, PAYMENT_DEMAND}
    assert findings[PAYMENT_DEMAND].evidence == "Pay Rs 500"
    assert findings[LINK].evidence == "http://bit.ly/parcel-fee"
    assert "link-shortening" in findings[LINK].explanation
    assert "unencrypted http" in findings[LINK].explanation


def test_benign_message_has_no_findings():
    assert detect_warning_signs("Hi, are we still meeting for lunch at 1 pm tomorrow?") == []


def test_multiple_indicators_in_one_message():
    message = (
        "Final warning! Your account is suspended. Confirm your ATM PIN and pay "
        "Rs 200 processing fee at http://192.168.10.5/verify now."
    )

    findings = detect_warning_signs(message)

    assert [finding.category for finding in findings] == [
        URGENCY,
        CREDENTIAL_REQUEST,
        LINK,
        PAYMENT_DEMAND,
    ]
    link = findings[2]
    assert link.evidence == "http://192.168.10.5/verify"
    assert "numeric IP address" in link.explanation


@pytest.mark.parametrize(
    "message",
    [
        # Safety advice mentions an OTP but does not ask for it.
        "Your OTP is 482913. Never share your OTP with anyone.",
        "Do not share your password or PIN with anyone, including bank staff.",
        # A postal pin code is not a credential.
        "Please confirm your pin code so the courier can find you.",
        # An email address is not a link.
        "You can reach me at priya@example.com after six.",
        "अपना ओटीपी किसी को न बताएं।",
    ],
)
def test_negative_cases_are_not_flagged(message):
    assert detect_warning_signs(message) == []


def test_plain_https_link_is_reported_without_extra_traits():
    findings = detect_warning_signs("Here are the photos: https://example.com/album")

    assert [finding.category for finding in findings] == [LINK]
    assert findings[0].evidence == "https://example.com/album"
    assert "This link" not in findings[0].explanation


@pytest.mark.parametrize(
    ("url", "trait"),
    [
        ("https://sbi.co.in@example.net/login", "'@' before the real address"),
        ("https://xn--bnk-example.com/kyc", "punycode"),
        ("tinyurl.com/abc123", "link-shortening"),
    ],
)
def test_link_traits(url, trait):
    findings = detect_warning_signs(f"Update your details at {url} today")

    assert [finding.category for finding in findings] == [LINK]
    assert findings[0].evidence == url
    assert trait in findings[0].explanation


def test_reward_release_payment():
    message = "Congratulations, you won a lottery prize. A small registration charge applies."

    assert categories(message) == [PAYMENT_DEMAND]


def test_disconnection_threat():
    message = "Dear customer, your electricity will be disconnected tonight at 9.30 pm."

    assert categories(message) == [URGENCY]


def test_hindi_urgency_and_otp_request():
    message = "आपका खाता बंद हो जाएगा। तुरंत अपना ओटीपी बताएं।"

    assert categories(message) == [URGENCY, CREDENTIAL_REQUEST]


def test_evidence_is_truncated():
    url = "https://example.com/" + "a" * 500

    findings = detect_warning_signs(f"See {url}")

    assert len(findings[0].evidence) == MAX_EVIDENCE_LENGTH
    assert findings[0].evidence.endswith("…")
