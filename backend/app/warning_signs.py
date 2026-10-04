"""Rule-based detection of warning signs in a suspicious message.

These are transparent pattern matches, not a fraud classifier. A finding means
"this pattern is present", never "this message is fraudulent".

Links are inspected as text only. Nothing in this module makes a network request.
"""

import re

from pydantic import BaseModel

MAX_EVIDENCE_LENGTH = 120

URGENCY = "urgency_pressure"
CREDENTIAL_REQUEST = "credential_request"
LINK = "link"
PAYMENT_DEMAND = "payment_demand"

EXPLANATIONS = {
    URGENCY: (
        "The message uses urgency, a threat, or a deadline. Pressure to act quickly "
        "is a common tactic to stop people from checking whether a request is genuine."
    ),
    CREDENTIAL_REQUEST: (
        "The message asks for an OTP, PIN, password, or banking details. These are "
        "meant to be kept secret; sharing them can give someone else access to your account."
    ),
    LINK: (
        "The message contains a link. Do not open it unless you have confirmed the "
        "sender through an official channel."
    ),
    PAYMENT_DEMAND: (
        "The message asks for a payment, transfer, or fee. Being asked to pay before "
        "receiving a prize, refund, parcel, or service is a common advance-fee pattern."
    ),
}


class Finding(BaseModel):
    category: str
    explanation: str
    evidence: str


def _compile(*patterns: str) -> list[re.Pattern[str]]:
    return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]


# "Same sentence" window used between two related words.
_GAP = r"[^.!?।\n]"

_URGENCY_PATTERNS = _compile(
    r"\b(?:urgent(?:ly)?|immediately|right away|act now|asap)\b",
    r"\bwithin\s+\d+\s*(?:hours?|hrs?|minutes?|mins?|days?)\b",
    r"\b(?:last|final)\s+(?:warning|notice|reminder|chance)\b",
    r"\bexpir(?:es?|ing)\s+(?:today|tonight|soon)\b",
    r"\b(?:account|card|sim|number|service|kyc|connection|electricity|power)\b" + _GAP + r"{0,40}"
    r"\b(?:blocked|suspended|deactivated|disconnected|frozen|closed|terminated)\b",
    r"\b(?:legal action|arrest warrant|arrested|police case)\b",
    # Hindi: immediately, at once, final warning, account closed, will be blocked
    r"तुरंत|तत्काल|अंतिम चेतावनी|खाता बंद|ब्लॉक (?:हो|कर दिया) जाएगा",
)

_CREDENTIAL_TERMS = (
    r"(?:otp|one[- ]time (?:password|passcode|pin)|(?:upi|atm|card|m)?[- ]?pin(?!\s*code)"
    r"|cvv|password|passcode|net ?banking (?:id|password|details)"
    r"|(?:card|account|bank) (?:number|details)|login (?:details|credentials))"
)
_CREDENTIAL_PATTERNS = _compile(
    r"\b(?:share|send|provide|enter|tell|give|confirm|verify|update|submit|forward|reply with)\b"
    + _GAP + r"{0,40}?\b" + _CREDENTIAL_TERMS + r"\b",
)
# Hindi: OTP / PIN / password followed by tell, send, share, or enter
_HINDI_CREDENTIAL_PATTERNS = _compile(
    r"(?:ओटीपी|otp|पिन(?!\s*कोड)|पासवर्ड)" + _GAP + r"{0,30}?"
    r"(?:बताएं|बताइए|भेजें|भेजिए|शेयर करें|साझा करें|दर्ज करें)",
)
# "Never share your OTP" is safety advice, not a request.
_NEGATION_BEFORE = re.compile(
    r"\b(?:do not|don['’]?t|never|not|no one|nobody)\b" + _GAP + r"{0,30}$", re.IGNORECASE
)
_HINDI_NEGATION = re.compile(r"(?<!\S)न(?!\S)|मत|नहीं")

_MONEY = r"(?:₹|\brs\.?|\binr\b|\brupees\b)\s?\d[\d,]*"
_PAYMENT_PATTERNS = _compile(
    r"\b(?:pay|transfer|send|deposit|remit)\b" + _GAP + r"{0,40}?" + _MONEY,
    r"\b(?:pay|transfer|send|deposit)\b" + _GAP + r"{0,40}?"
    r"\b(?:fees?|fine|penalty|charges?|to (?:claim|receive|release|unlock|activate))\b",
    r"\b(?:processing|registration|delivery|customs|clearance|activation|verification|handling|release)"
    r"\s+(?:fees?|charges?|deposit)\b",
    r"\b(?:won|winner|prize|lottery|reward|cashback|gift)\b" + _GAP + r"{0,80}?"
    r"\b(?:pay|fees?|charges?|deposit)\b",
    r"\b(?:overdue|unpaid|pending)\s+(?:bill|payment|dues|challan|fine)\b",
    # Hindi: make the payment, send money, transfer money, processing fee
    r"भुगतान करें|पैसे भेजें|पैसे ट्रांसफर|प्रोसेसिंग शुल्क",
)

_NOT_MID_WORD = r"(?<![@\w.-])"
_URL_PATTERN = re.compile(
    _NOT_MID_WORD + r"(?:https?://|www\.)[^\s<>\"']+"
    # Bare domains such as "bit.ly/abc" or "example.co.in/login"
    r"|" + _NOT_MID_WORD + r"(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+"
    r"(?:com|in|net|org|info|xyz|top|click|link|online|site|live|shop|app|io|co|cc|ly|me|gl|gd|gy|at)\b"
    r"(?:/[^\s<>\"']*)?",
    re.IGNORECASE,
)
_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly",
    "rb.gy", "ow.ly", "shorturl.at", "tiny.cc",
}
_IP_HOST = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}")


def _excerpt(text: str) -> str:
    text = " ".join(text.split())
    if len(text) <= MAX_EVIDENCE_LENGTH:
        return text
    return text[: MAX_EVIDENCE_LENGTH - 1].rstrip() + "…"


def _earliest(matches: list[re.Match[str]]) -> re.Match[str] | None:
    return min(matches, key=lambda match: match.start(), default=None)


def _finding(category: str, evidence: str, extra: str = "") -> Finding:
    return Finding(
        category=category,
        explanation=EXPLANATIONS[category] + extra,
        evidence=_excerpt(evidence),
    )


def _detect_patterns(category: str, patterns: list[re.Pattern[str]], message: str) -> Finding | None:
    match = _earliest([m for pattern in patterns for m in pattern.finditer(message)])
    return _finding(category, match.group()) if match else None


def _detect_credential_request(message: str) -> Finding | None:
    matches = [
        m
        for pattern in _CREDENTIAL_PATTERNS
        for m in pattern.finditer(message)
        if not _NEGATION_BEFORE.search(message[: m.start()])
    ]
    matches += [
        m
        for pattern in _HINDI_CREDENTIAL_PATTERNS
        for m in pattern.finditer(message)
        if not _HINDI_NEGATION.search(m.group())
    ]
    match = _earliest(matches)
    return _finding(CREDENTIAL_REQUEST, match.group()) if match else None


def _link_traits(url: str) -> list[str]:
    """Describe structural traits of a link from its text alone."""
    authority = re.split(r"[/?#]", re.sub(r"^[a-z]+://", "", url, flags=re.IGNORECASE), maxsplit=1)[0]
    host = authority.rsplit("@", 1)[-1].split(":")[0].lower().removeprefix("www.")

    traits = []
    if host in _SHORTENERS:
        traits.append("uses a link-shortening service, which hides the real destination")
    if _IP_HOST.fullmatch(host):
        traits.append("uses a numeric IP address instead of a domain name")
    if "xn--" in host:
        traits.append("uses an encoded (punycode) domain, which can imitate another site's name")
    if "@" in authority:
        traits.append("has an '@' before the real address, which can disguise the destination")
    if url.lower().startswith("http://"):
        traits.append("uses unencrypted http")
    return traits


def _detect_link(message: str) -> Finding | None:
    urls = [match.group().rstrip(".,;:!?)]}") for match in _URL_PATTERN.finditer(message)]
    if not urls:
        return None

    # Prefer the first link with a notable trait; otherwise report the first link.
    for url in urls:
        traits = _link_traits(url)
        if traits:
            return _finding(LINK, url, " This link " + "; ".join(traits) + ".")
    return _finding(LINK, urls[0])


def detect_warning_signs(message: str) -> list[Finding]:
    """Return at most one finding per category, in a fixed category order."""
    findings = [
        _detect_patterns(URGENCY, _URGENCY_PATTERNS, message),
        _detect_credential_request(message),
        _detect_link(message),
        _detect_patterns(PAYMENT_DEMAND, _PAYMENT_PATTERNS, message),
    ]
    return [finding for finding in findings if finding is not None]
