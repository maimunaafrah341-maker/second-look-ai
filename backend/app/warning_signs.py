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

# --- Hindi building blocks -----------------------------------------------------------
# Devanagari has no reliable \b (vowel signs are not word characters), so word edges
# are written as "no Devanagari letter or sign on this side". The danda (।, ॥) and
# Devanagari digits are left out of the range so they count as word edges.
_DEV = "ऀ-ॣॱ-ॿ"
_D_START = rf"(?<![{_DEV}])"
_D_END = rf"(?![{_DEV}])"

# Devanagari verb forms: polite, informal, and "do it for me" forms, with common
# spelling variants (एं / एँ / यें, ए / ये).
_D_TELL = rf"बता(?:एं|एँ|यें|इए|इये|ओ|\s*(?:दें|दो|दीजिए|दीजिये)){_D_END}"
_D_SEND = rf"भेज(?:ें|िए|िये|ो|\s*(?:दें|दो|दीजिए|दीजिये)){_D_END}"
_D_DO = rf"(?:करें|कीजिए|कीजिये|करो|कर\s*(?:दें|दो|दीजिए|दीजिये)){_D_END}"
_D_FILL = rf"भर(?:ें|िए|िये|ो|\s*(?:दें|दो|दीजिए|दीजिये)){_D_END}"

# Romanised Hindi spelling variants, written as alternatives rather than by rewriting
# the text, so evidence is always cut from the original message. Bare "kar" and past
# forms such as "kar diya" are left out: they describe what someone did, not a request.
_R_TELL = r"(?:bata(?:o|iye|ye|yen|yein|en|ein)\b|bata\s+(?:do|de|dijiye|dena)\b)"
_R_SEND = r"(?:bhej(?:o|e|en|ein|iye)\b|bhej\s+(?:do|de|dijiye|dena)\b)"
_R_DO = r"(?:kar(?:o|e|en|ein|iye)\b|kar\s+(?:do|de|dijiye|dena)\b)"
_R_FILL = r"(?:bhar(?:o|e|en|ein|iye)\b|bhar\s+(?:do|de|dijiye)\b)"
_R_WILL_BE = r"(?:ho|kar\s+diya|kiya)\s+ja(?:a)?(?:yega|yegi|ega|egi|yenge|enge)\b"

_URGENCY_PATTERNS = _compile(
    r"\b(?:urgent(?:ly)?|immediately|right away|act now|asap)\b",
    r"\bwithin\s+\d+\s*(?:hours?|hrs?|minutes?|mins?|days?)\b",
    r"\b(?:last|final)\s+(?:warning|notice|reminder|chance)\b",
    r"\bexpir(?:es?|ing)\s+(?:today|tonight|soon)\b",
    r"\b(?:account|card|sim|number|service|kyc|connection|electricity|power)\b" + _GAP + r"{0,40}"
    r"\b(?:blocked|suspended|deactivated|disconnected|frozen|closed|terminated)\b",
    r"\b(?:legal action|arrest warrant|arrested|police case)\b",
    # Hindi: immediately, at once, final warning
    rf"{_D_START}(?:तुरंत|तुरन्त|तत्काल|अंतिम\s*चेतावनी){_D_END}",
    # Hindi: "now" / "today itself" only when followed by an action, since on their own
    # they are everyday words.
    rf"{_D_START}(?:अभी|आज\s*ही){_D_END}" + _GAP + r"{0,25}?"
    rf"(?:कॉल|संपर्क|क्लिक|भुगतान|अपडेट|{_D_DO}|{_D_SEND}|{_D_FILL}|{_D_TELL})",
    # Hindi: account / card / SIM / electricity ... will be closed or blocked
    rf"{_D_START}(?:खाता|खाते|अकाउंट|कार्ड|सिम|नंबर|बिजली|कनेक्शन|सेवा|केवाईसी){_D_END}" + _GAP + r"{0,25}?"
    rf"(?:बंद|ब्लॉक|निलंबित|सस्पेंड)\s*(?:हो|कर\s*दिया|कर\s*दी|किया)\s*जा(?:एगा|येगा|एगी|येगी|एंगे|येंगे){_D_END}",
    # Romanised Hindi: immediately, final warning
    r"\bturant\b|\bantim\s+chet(?:a|aa)vani\b",
    r"\b(?:abhi|aa?j\s+h(?:i|ee))\b" + _GAP + r"{0,25}?"
    rf"(?:\b(?:call|update|click|payment|bhugtan)\b|{_R_DO}|{_R_SEND}|{_R_FILL}|{_R_TELL})",
    r"\b(?:khaa?ta|account|card|sim|kyc|bijli|connection|number)\b" + _GAP + r"{0,25}?"
    rf"\b(?:bandh?|block|suspend|deactivate)\s+{_R_WILL_BE}",
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
# Hindi word order puts the object first: OTP / PIN / password, then tell, send, or share.
_HINDI_CREDENTIAL_TERMS = (
    rf"(?:{_D_START}(?:ओटीपी|पासवर्ड|सीवीवी|पिन(?!\s*कोड)){_D_END}"
    r"|\b(?:otp|password|cvv|pin(?!\s*code))\b)"
)
_HINDI_CREDENTIAL_PATTERNS = _compile(
    # Devanagari (also with OTP / PIN written in English letters)
    _HINDI_CREDENTIAL_TERMS + _GAP + r"{0,30}?"
    rf"(?:{_D_TELL}|{_D_SEND}|(?:शेयर|साझा|दर्ज)\s*{_D_DO})",
    # Romanised Hindi
    _HINDI_CREDENTIAL_TERMS + _GAP + r"{0,30}?" + rf"(?:{_R_TELL}|{_R_SEND}|\bshare\s+{_R_DO})",
)
# "Never share your OTP" is safety advice, not a request.
_NEGATION_BEFORE = re.compile(
    r"\b(?:do not|don['’]?t|never|not|no one|nobody)\b" + _GAP + r"{0,30}$", re.IGNORECASE
)
# Hindi negation sits between the object and the verb ("OTP kisi ko na batayein",
# "साझा न करें") or straight after the verb ("बताएं नहीं", "share karo mat").
# "na" / "ना" after a verb is usually a softener ("bata do na" = "please tell"), so only
# नहीं / मत / nahi / mat count when they follow the verb. When in doubt, no finding.
_HINDI_NEGATION_INSIDE = re.compile(
    rf"{_D_START}(?:न|ना|नहीं|मत){_D_END}|\b(?:na|naa|nahi|nahin|nhi|mat)\b", re.IGNORECASE
)
_HINDI_NEGATION_AFTER = re.compile(
    rf"\s*(?:{_D_START}(?:नहीं|मत){_D_END}|\b(?:nahi|nahin|nhi|mat)\b)", re.IGNORECASE
)

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
    # Hindi: send / transfer / deposit money, make the payment, pay the fee
    rf"{_D_START}(?:पैसे|पैसा|रुपये|रुपए|राशि|रकम){_D_END}\s*"
    rf"(?:{_D_SEND}|(?:ट्रांसफर|जमा)\s*{_D_DO}|ट्रांसफर{_D_END})",
    rf"{_D_START}भुगतान\s*{_D_DO}",
    rf"{_D_START}(?:शुल्क|फीस|फ़ीस|चार्ज){_D_END}\s*(?:{_D_FILL}|जमा\s*{_D_DO}|का\s*भुगतान\s*{_D_DO})",
    rf"{_D_START}(?:प्रोसेसिंग|पंजीकरण|रजिस्ट्रेशन|डिलीवरी|कस्टम|कस्टम्स|सत्यापन|वेरिफिकेशन)\s*"
    rf"(?:शुल्क|फीस|फ़ीस|चार्ज){_D_END}",
    # Romanised Hindi
    rf"\b(?:paise|paisa|paisey|rupaye|rupaiye|amount)\s+(?:{_R_SEND}|(?:transfer|jama)\s+{_R_DO})",
    rf"\b(?:payment|bhugtan)\s+{_R_DO}",
    rf"\b(?:fees?|fis|shulk|charges?)\s+(?:{_R_FILL}|(?:jama|pay)\s+{_R_DO})",
)

# --- Deferred: Telugu, Urdu and Bengali ----------------------------------------------------
# Not part of the current release. These patterns run only when detect_warning_signs is
# called with include_deferred_languages=True, which the service never does. They are
# kept, with their tests and evaluation set, for a future release after review by native
# speakers (docs/native_review_checklist.md).
#
# Same approach as Hindi: a limited list of phrases, written without review by native
# speakers. Each script gets its own word edges, since \b is unreliable for vowel signs.
# These patterns need the script's own words, so English and Hindi text never matches them.

# "Same sentence", also stopping at the Urdu full stop and question mark. The English and
# Hindi patterns keep _GAP unchanged.
_GAP_X = r"[^.!?।۔؟\n]"

_TE_LETTERS = r"ఀ-౿‌‍"
_BN_LETTERS = r"ঀ-৿‌‍"
# Arabic-script letters and vowel marks, without Arabic punctuation (، ؛ ؟ ۔) or digits.
_UR_LETTERS = r"ؐ-ؚؠ-ٟٮ-ۓە-ۯۺ-ۿ‌‍"
_T_START, _T_END = rf"(?<![{_TE_LETTERS}])", rf"(?![{_TE_LETTERS}])"
_B_START, _B_END = rf"(?<![{_BN_LETTERS}])", rf"(?![{_BN_LETTERS}])"
_U_START, _U_END = rf"(?<![{_UR_LETTERS}])", rf"(?![{_UR_LETTERS}])"

# OTP, PIN, password and CVV are often written in English letters inside these languages.
_LATIN_SECRET = r"\b(?:otp|pin(?!\s*code)|password|cvv)\b"
_LATIN_SUBJECT = r"\b(?:account|card|sim|kyc|atm|upi)\b"
_LATIN_ACTION = r"\b(?:call|click|update|pay)\b"


def _with_joiners(pattern: str, virama: str) -> str:
    """Accept a word typed with or without a zero-width (non-)joiner after the virama."""
    return pattern.replace("‌", "").replace("‍", "").replace(virama, virama + "[‌‍]?")


def _telugu(pattern: str) -> str:
    return _with_joiners(pattern, "్")


def _bengali(pattern: str) -> str:
    # য়, ড় and ঢ় can be typed as one character or as the base letter plus a nukta.
    pattern = _with_joiners(pattern, "্")
    for single, base in (("য়", "য"), ("ড়", "ড"), ("ঢ়", "ঢ")):
        pattern = pattern.replace(single, base + "়").replace(base + "়", f"(?:{single}|{base}়)")
    return pattern


def _urdu(pattern: str) -> str:
    # Arabic keyboards type ك ي ى ه where Urdu uses ک ی ہ.
    for urdu, alternatives in (("ک", "کك"), ("ی", "یيى"), ("ہ", "ہه")):
        pattern = pattern.replace(urdu, f"[{alternatives}]")
    return pattern


# Telugu. Polite requests end in -ండి; "don't" is -కండి or వద్దు, so negated advice
# ("చెప్పకండి") does not match the request forms below.
_TE_TELL = r"(?:చెప్పండి|చెప్పు|చెప్పేయండి)"
_TE_SEND = r"(?:పంపండి|పంపించండి|పంపు|పంపించు)"
_TE_GIVE = r"(?:ఇవ్వండి|ఇవ్వు|ఇచ్చేయండి)"
_TE_DO = r"(?:చేయండి|చెయ్యండి|చేయి|చెయ్యి)"
_TE_PAY = r"(?:చెల్లించండి|చెల్లించు|కట్టండి|కట్టు)"
# Any polite request word, except "come" (రండి) and "don't" (-కండి).
_TE_REQUEST = rf"{_T_START}[{_TE_LETTERS}]*(?<![కర])ండి{_T_END}"

_TE_URGENCY = [
    rf"{_T_START}(?:చివరి|తుది)\s*హెచ్చరిక{_T_END}",
    # "Immediately" / "today itself" only when followed by an action, since on their own
    # they are everyday words ("వెంటనే వస్తాను", "I'll come right away").
    rf"{_T_START}(?:వెంటనే|తక్షణమే|తక్షణం|ఈరోజే|ఇప్పుడే){_T_END}" + _GAP_X + r"{0,40}?"
    rf"(?:{_T_START}(?:కాల్|క్లిక్|అప్‌డేట్|పేమెంట్){_T_END}|{_LATIN_ACTION}|{_TE_REQUEST})",
    # Account / card / SIM / connection ... will be (or has been) blocked or cut off
    rf"(?:{_T_START}(?:ఖాతా|అకౌంట్|కార్డ్|కార్డు|సిమ్|కనెక్షన్|సేవ|నంబర్|కేవైసీ|కరెంట్|విద్యుత్)[{_TE_LETTERS}]*|{_LATIN_SUBJECT})"
    + _GAP_X + r"{0,40}?"
    r"(?:బ్లాక్|నిలిపివేయ|నిలిపి\s*వేయ|రద్దు|సస్పెండ్|డీయాక్టివేట్|కట్|మూసివేయ)\s*"
    rf"(?:అవుతుంది|అవుతాయి|అయింది|అయ్యింది|చేయబడుతుంది|చేయబడింది|చేయబడతాయి|బడుతుంది|బడింది|చేస్తాము|చేస్తాం){_T_END}",
]
_TE_SECRET = (
    rf"(?:{_T_START}(?:ఓటీపీ|ఓటిపి|పిన్(?!\s*కోడ్)|పాస్‌వర్డ్|సీవీవీ|(?:కార్డ్|కార్డు|బ్యాంక్)\s*వివరాలు)"
    rf"(?:ని|ను|లను)?{_T_END}|{_LATIN_SECRET})"
)
_TE_CREDENTIAL = (
    _TE_SECRET + _GAP_X + r"{0,30}?"
    rf"(?:{_TE_TELL}|{_TE_SEND}|{_TE_GIVE}|(?:షేర్|నమోదు|ఎంటర్)\s*{_TE_DO}){_T_END}"
)
_TE_PAYMENT = [
    rf"{_T_START}(?:రిజిస్ట్రేషన్|ప్రాసెసింగ్|డెలివరీ|కస్టమ్స్|వెరిఫికేషన్|యాక్టివేషన్)\s*(?:ఫీజు|రుసుము|ఛార్జీ|ఛార్జ్){_T_END}",
    rf"{_T_START}(?:ఫీజు|రుసుము|ఛార్జీ|ఛార్జ్|ఛార్జీలు){_T_END}" + _GAP_X + r"{0,30}?"
    rf"(?:{_TE_PAY}|(?:డిపాజిట్|జమ|పే)\s*{_TE_DO}){_T_END}",
    rf"(?:{_T_START}(?:డబ్బు|డబ్బులు|రూపాయలు|మొత్తం){_T_END}|(?:₹|{_T_START}రూ\.?)\s?\d[\d,]*)" + _GAP_X + r"{0,25}?"
    rf"(?:{_TE_SEND}|{_TE_PAY}|(?:డిపాజిట్|జమ|ట్రాన్స్‌ఫర్|పే)\s*{_TE_DO}){_T_END}",
    rf"{_T_START}(?:చెల్లించండి|(?:చెల్లింపు|పేమెంట్|డిపాజిట్)\s*{_TE_DO}){_T_END}",
]

# Urdu
_UR_TELL = r"(?:بتائیں|بتائیے|بتاؤ|بتا\s*دیں|بتا\s*دو|بتا\s*دیجیے)"
_UR_SEND = r"(?:بھیجیں|بھیجیے|بھیجو|بھیج\s*دیں|بھیج\s*دو)"
_UR_DO = r"(?:کریں|کرو|کیجیے|کیجئے|کر\s*دیں|کر\s*دو)"
_UR_DEPOSIT = r"(?:جمع\s*(?:کرائیں|کروائیں|کریں|کرو|کرا\s*دیں))"
_UR_PAY = r"(?:ادا\s*(?:کریں|کرو|کیجیے|کر\s*دیں)|ادائیگی\s*(?:کریں|کرو))"

_UR_URGENCY = [
    rf"{_U_START}آخری\s*(?:وارننگ|انتباہ|موقع|نوٹس){_U_END}",
    rf"{_U_START}(?:فوراً|فورا|فوری\s*طور\s*پر|ابھی|آج\s*ہی){_U_END}" + _GAP_X + r"{0,30}?"
    rf"(?:{_U_START}(?:کال|کلک|اپڈیٹ|اپ\s*ڈیٹ|ادائیگی){_U_END}|{_LATIN_ACTION}"
    rf"|(?:{_UR_TELL}|{_UR_SEND}|{_UR_DO}|{_UR_PAY}|{_UR_DEPOSIT}){_U_END})",
    rf"(?:{_U_START}(?:اکاؤنٹ|کھاتہ|کھاتا|کارڈ|سم|کنکشن|سروس|نمبر|بجلی){_U_END}|{_LATIN_SUBJECT})"
    + _GAP_X + r"{0,40}?"
    r"(?:بند|بلاک|معطل|منقطع|کاٹ|کٹ)\s*"
    r"(?:ہو\s*جائے\s*گا|ہو\s*جائے\s*گی|ہو\s*جائیں\s*گے|کر\s*دیا\s*جائے\s*گا|کر\s*دی\s*جائے\s*گی|دیا\s*جائے\s*گا"
    rf"|دی\s*جائے\s*گی|کر\s*دیا\s*گیا|کر\s*دی\s*گئی|ہو\s*گیا|ہو\s*گئی|جائے\s*گا|جائے\s*گی){_U_END}",
]
_UR_SECRET = (
    rf"(?:{_U_START}(?:او\s*ٹی\s*پی|پن(?!\s*کوڈ)|پاس\s*ورڈ|سی\s*وی\s*وی|(?:کارڈ|بینک)\s*کی\s*تفصیلات){_U_END}"
    rf"|{_LATIN_SECRET})"
)
# Bare "دو" is left out: it also means "two" ("OTP دو منٹ میں ختم ہو جائے گا").
_UR_CREDENTIAL = (
    _UR_SECRET + _GAP_X + r"{0,30}?" + rf"(?:{_UR_TELL}|{_UR_SEND}|(?:شیئر|درج|داخل)\s*{_UR_DO}|دیں){_U_END}"
)
_UR_PAYMENT = [
    rf"{_U_START}(?:رجسٹریشن|پروسیسنگ|پراسیسنگ|ڈلیوری|ڈیلیوری|کسٹمز|کسٹم|تصدیقی|ایکٹیویشن)\s*(?:فیس|چارجز|چارج){_U_END}",
    rf"{_U_START}(?:فیس|چارجز|چارج){_U_END}" + _GAP_X + r"{0,30}?" + rf"(?:{_UR_PAY}|{_UR_DEPOSIT}|بھریں|بھرو|دیں){_U_END}",
    rf"{_U_START}(?:پیسے|پیسہ|رقم|روپے|روپیہ){_U_END}" + _GAP_X + r"{0,25}?"
    rf"(?:{_UR_SEND}|{_UR_PAY}|{_UR_DEPOSIT}|ٹرانسفر\s*{_UR_DO}){_U_END}",
    # "شکریہ ادا کریں" means "say thank you".
    rf"{_U_START}(?<!شکریہ\s)(?:{_UR_PAY}|پیمنٹ\s*{_UR_DO}){_U_END}",
]

# Bengali. "Don't" uses a different verb form ("বলবেন না", "পাঠাবেন না"), so negated
# advice does not match the request forms below. "দিন না" is a polite "please give", so a
# trailing না is not treated as negation.
_BN_TELL = r"(?:বলুন|বলো|বলে\s*দিন|বলে\s*দাও)"
_BN_SEND = r"(?:পাঠান|পাঠাও|পাঠিয়ে\s*দিন|পাঠিয়ে\s*দাও)"
_BN_GIVE = r"(?:দিন|দাও|দিয়ে\s*দিন)"
_BN_DO = r"(?:করুন|করো|করে\s*দিন)"
_BN_PAY = rf"(?:(?:পরিশোধ|পেমেন্ট|পে)\s*{_BN_DO}|জমা\s*(?:দিন|দাও|করুন))"

_BN_URGENCY = [
    rf"{_B_START}(?:শেষ|চূড়ান্ত)\s*(?:সতর্কতা|সতর্কবার্তা|সুযোগ|নোটিশ){_B_END}",
    rf"{_B_START}(?:এখনই|অবিলম্বে|আজই|তাড়াতাড়ি|দ্রুত){_B_END}" + _GAP_X + r"{0,30}?"
    rf"(?:{_B_START}(?:কল|ক্লিক|আপডেট|পেমেন্ট|পরিশোধ){_B_END}|{_LATIN_ACTION}"
    rf"|(?:{_BN_TELL}|{_BN_SEND}|{_BN_GIVE}|{_BN_DO}|{_BN_PAY}){_B_END})",
    rf"(?:{_B_START}(?:অ্যাকাউন্ট|খাতা|কার্ড|সিম|সংযোগ|কানেকশন|পরিষেবা|সার্ভিস|নম্বর|বিদ্যুৎ)[{_BN_LETTERS}]*|{_LATIN_SUBJECT})"
    + _GAP_X + r"{0,40}?"
    r"(?:বন্ধ|ব্লক|স্থগিত|বিচ্ছিন্ন|সাসপেন্ড|নিষ্ক্রিয়|কেটে)\s*"
    rf"(?:হয়ে\s*যাবে|হবে|করা\s*হবে|করে\s*দেওয়া\s*হবে|দেওয়া\s*হবে|করা\s*হয়েছে|হয়েছে|হয়ে\s*গেছে){_B_END}",
]
_BN_SECRET = (
    rf"(?:{_B_START}(?:ওটিপি|ও\s*টি\s*পি|পিন(?!\s*কোড)|পাসওয়ার্ড|সিভিভি|(?:কার্ডের|ব্যাংকের|অ্যাকাউন্টের)\s*(?:তথ্য|বিবরণ|নম্বর))"
    rf"(?:টি|টা)?{_B_END}|{_LATIN_SECRET})"
)
_BN_CREDENTIAL = (
    _BN_SECRET + _GAP_X + r"{0,30}?" + rf"(?:{_BN_TELL}|{_BN_SEND}|{_BN_GIVE}|(?:শেয়ার|এন্টার)\s*{_BN_DO}|লিখুন){_B_END}"
)
_BN_PAYMENT = [
    rf"{_B_START}(?:রেজিস্ট্রেশন|প্রসেসিং|প্রক্রিয়াকরণ|ডেলিভারি|কাস্টমস|কাস্টম|ভেরিফিকেশন|অ্যাক্টিভেশন)\s*(?:ফি|চার্জ){_B_END}",
    rf"{_B_START}(?:ফি|ফিস|চার্জ){_B_END}" + _GAP_X + r"{0,30}?" + rf"(?:{_BN_PAY}|{_BN_GIVE}){_B_END}",
    rf"{_B_START}(?:টাকা|অর্থ){_B_END}" + _GAP_X + r"{0,25}?" + rf"(?:{_BN_SEND}|{_BN_PAY}|{_BN_GIVE}|ট্রান্সফার\s*{_BN_DO}){_B_END}",
    rf"{_B_START}(?:পরিশোধ|পেমেন্ট)\s*{_BN_DO}{_B_END}",
]

_INDIC_URGENCY_PATTERNS = _compile(
    *map(_telugu, _TE_URGENCY), *map(_urdu, _UR_URGENCY), *map(_bengali, _BN_URGENCY)
)
_INDIC_PAYMENT_PATTERNS = _compile(
    *map(_telugu, _TE_PAYMENT), *map(_urdu, _UR_PAYMENT), *map(_bengali, _BN_PAYMENT)
)
# Each credential pattern with the words that make a match safety advice instead: inside
# the match ("OTP کسی کو نہ بتائیں") or straight after it ("OTP చెప్పండి వద్దు").
_INDIC_CREDENTIAL_PATTERNS = [
    (
        re.compile(_telugu(_TE_CREDENTIAL), re.IGNORECASE),
        re.compile(_telugu(rf"{_T_START}(?:ఎవరికీ|ఎవరితోనూ|వద్దు|కూడదు|ఎప్పుడూ){_T_END}")),
        re.compile(_telugu(rf"\s*{_T_START}(?:వద్దు|కూడదు){_T_END}")),
    ),
    (
        re.compile(_urdu(_UR_CREDENTIAL), re.IGNORECASE),
        re.compile(_urdu(rf"{_U_START}(?:نہ|مت|نہیں|کبھی){_U_END}")),
        re.compile(_urdu(rf"\s*{_U_START}(?:نہیں|مت){_U_END}")),
    ),
    (
        re.compile(_bengali(_BN_CREDENTIAL), re.IGNORECASE),
        re.compile(_bengali(rf"{_B_START}(?:না|কখনো|কখনও|কাউকে){_B_END}")),
        None,
    ),
]

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


def _negated_after(message: str, match: re.Match[str]) -> bool:
    return bool(_HINDI_NEGATION_AFTER.match(message, match.end()))


def _detect_credential_request(message: str, include_deferred_languages: bool = False) -> Finding | None:
    matches = [
        m
        for pattern in _CREDENTIAL_PATTERNS
        for m in pattern.finditer(message)
        # English negation comes before the verb; Hinglish negation after it
        # ("share your OTP mat karo").
        if not _NEGATION_BEFORE.search(message[: m.start()]) and not _negated_after(message, m)
    ]
    matches += [
        m
        for pattern in _HINDI_CREDENTIAL_PATTERNS
        for m in pattern.finditer(message)
        if not _HINDI_NEGATION_INSIDE.search(m.group()) and not _negated_after(message, m)
    ]
    matches += [
        m
        for pattern, negation_inside, negation_after in (_INDIC_CREDENTIAL_PATTERNS if include_deferred_languages else ())
        for m in pattern.finditer(message)
        if not negation_inside.search(m.group())
        and not (negation_after and negation_after.match(message, m.end()))
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


def detect_warning_signs(message: str, *, include_deferred_languages: bool = False) -> list[Finding]:
    """Return at most one finding per category, in a fixed category order.

    English, Hindi and romanised-Hindi patterns always run. The Telugu, Urdu and Bengali
    patterns are deferred to a future release and run only when asked for.
    """
    urgency = _URGENCY_PATTERNS + (_INDIC_URGENCY_PATTERNS if include_deferred_languages else [])
    payment = _PAYMENT_PATTERNS + (_INDIC_PAYMENT_PATTERNS if include_deferred_languages else [])
    findings = [
        _detect_patterns(URGENCY, urgency, message),
        _detect_credential_request(message, include_deferred_languages),
        _detect_link(message),
        _detect_patterns(PAYMENT_DEMAND, payment, message),
    ]
    return [finding for finding in findings if finding is not None]
