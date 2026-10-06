"""Deterministic estimate of which language a message is written in.

This is an estimate, not language identification. It counts letters by Unicode script
and, for text in the Latin alphabet, looks for a short list of romanised-Hindi words.
It uses no model, no translation, and no network.

It does not change any analysis. It only reports what was estimated and how well the
current checks cover that language.
"""

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass

METHOD = "script_and_keyword_estimate"

# One script must supply at least this share of the letters, or the message is "mixed".
DOMINANT_SCRIPT_SHARE = 0.75
# Latin-alphabet text is tagged "hi-Latn" only with at least this many different
# romanised-Hindi words, making up at least this share of all words. Fewer give "mixed"
# or "en".
MIN_HINDI_CUES = 2
HINDI_CUE_SHARE = 0.25

# Distinctive romanised-Hindi words. Words that are also common English words or names
# (for example "is", "me", "to", "do", "main", "band", "mat", "hum", "karen", "bata")
# are left out on purpose, so ordinary English is not mistaken for Hindi.
ROMAN_HINDI_CUES = frozenset(
    """
    hai hain hoga hogi hoge ho nahi nahin nhi kya kyu kyun kyon kaise kaun kahan kab
    aap aapka aapke aapki apna apne apni mera meri mere mujhe hamara hamare hamein tum
    tumhara tumhare tumhe unka unki unke iska iski uska uski yeh woh
    aur bhi lekin abhi turant jaldi kuch sirf liye wala wali wale
    karo karein kare kijiye karna karke kiya kar raha rahe rahi gaya gayi gaye
    jayega jaayega jayegi jaega jaegi aaya aaye aayi
    batao bataye batayein bataiye bhejo bhejein bhejiye bhej dijiye
    bhai bhaiya yaar paise paisa accha acha theek thik ghar
    """.split()
)

_SCRIPT_BY_NAME = {"LATIN": "Latin", "DEVANAGARI": "Devanagari", "TELUGU": "Telugu", "ARABIC": "Arabic", "BENGALI": "Bengali"}
# Script-based estimates. Devanagari may also be Marathi or Nepali, Arabic script may be
# another language, and Bengali script may be Assamese; the tags are best guesses.
_TAG_BY_SCRIPT = {"Devanagari": "hi", "Telugu": "te", "Arabic": "ur", "Bengali": "bn"}

# Web addresses are Latin even inside Hindi or Telugu messages, so they are not counted.
_WEB_ADDRESS = re.compile(r"(?:https?://|www\.)\S+|\b[\w-]+\.[a-z]{2,}/\S*", re.IGNORECASE)
_WORD = re.compile(r"[a-z]+")

_CAVEAT = "This is an automatic estimate and may be wrong."
_LINKS_AND_AMOUNTS = "Links, rupee amounts and English words such as OTP or KYC are still checked."

# How well the current checks cover each language:
# - supported: the language's own words are checked by the warning-sign rules and the
#   official-guidance matching.
# - partial: only some of its words are checked.
# - unsupported: none of its words are checked; only links, rupee amounts and any
#   English words in the message are.
COVERAGE = {
    "en": "supported",
    "hi": "partial",
    "hi-Latn": "partial",
    "mixed": "partial",
    "te": "unsupported",
    "ur": "unsupported",
    "bn": "unsupported",
    "unknown": "unsupported",
}

NOTICES = {
    "en": f"Estimated language: English. All of Second Look's checks are designed for English. {_CAVEAT}",
    "hi": (
        "Estimated language: Hindi (Devanagari). Only a small set of Hindi warning phrases is "
        f"checked so far, and official guidance is matched in English only. {_LINKS_AND_AMOUNTS} {_CAVEAT}"
    ),
    "hi-Latn": (
        "Estimated language: Hindi written in English letters. Romanised Hindi phrases are not "
        f"analysed yet; only the English words in the message are. {_LINKS_AND_AMOUNTS} {_CAVEAT}"
    ),
    "mixed": (
        "Estimated language: a mix of languages or scripts. English parts are checked fully; "
        f"other parts may be checked only partly or not at all. {_CAVEAT}"
    ),
    "te": f"Estimated language: Telugu. Telugu text is not analysed yet. {_LINKS_AND_AMOUNTS} {_CAVEAT}",
    "ur": f"Estimated language: Urdu. Urdu text is not analysed. {_LINKS_AND_AMOUNTS} {_CAVEAT}",
    "bn": f"Estimated language: Bengali. Bengali text is not analysed. {_LINKS_AND_AMOUNTS} {_CAVEAT}",
    "unknown": (
        "The language could not be estimated, for example because the message has few or no "
        f"letters or uses a script Second Look does not recognise. {_LINKS_AND_AMOUNTS}"
    ),
}


@dataclass(frozen=True)
class LanguageEstimate:
    detected: str
    coverage: str
    notice: str
    method: str = METHOD


def _script(character: str) -> str:
    name = unicodedata.name(character, "")
    return _SCRIPT_BY_NAME.get(name.split(" ", 1)[0], "other")


def _latin_tag(text: str) -> str:
    words = _WORD.findall(text.lower())
    cues = sum(1 for word in words if word in ROMAN_HINDI_CUES)
    # Different cue words are needed: a repeated word ("ho ho", a laugh) is weak evidence.
    if len({word for word in words if word in ROMAN_HINDI_CUES}) < MIN_HINDI_CUES:
        return "en"
    return "hi-Latn" if cues / len(words) >= HINDI_CUE_SHARE else "mixed"


def estimate_tag(text: str) -> str:
    text = _WEB_ADDRESS.sub(" ", text)
    scripts = Counter(_script(character) for character in text if character.isalpha())
    total = sum(scripts.values())
    if not total:
        return "unknown"
    script, count = scripts.most_common(1)[0]
    if count / total < DOMINANT_SCRIPT_SHARE:
        return "mixed"
    if script == "Latin":
        return _latin_tag(text)
    return _TAG_BY_SCRIPT.get(script, "unknown")


def estimate_language(text: str) -> LanguageEstimate:
    tag = estimate_tag(text)
    return LanguageEstimate(detected=tag, coverage=COVERAGE[tag], notice=NOTICES[tag])
