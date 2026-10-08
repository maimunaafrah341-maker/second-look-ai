"""Retrieval of official cyber-safety guidance from a small, hand-checked local corpus.

Retrieval is keyword similarity (TF-IDF with cosine similarity) written in plain
Python. It makes no network requests, uses no model, and is independent of the
warning-sign rules, the classifier, and any language-model provider.

Every title, publisher, and URL returned comes from the validated corpus file.
A match means "this guidance uses similar words", not "this message is fraudulent".

Hindi and romanised-Hindi messages reach the same English passages through a small
term map (data/term_map.json). The map only adds existing corpus terms to the query.
It is not a translation, and the user's message is never changed.
"""

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from app.language import ROMAN_HINDI_CUES

DEFAULT_CORPUS = Path(__file__).resolve().parent / "data" / "guidance.json"
DEFAULT_TERM_MAP = Path(__file__).resolve().parent / "data" / "term_map.json"

# Only sources whose site policy allows linking, or states no restriction.
ALLOWED_HOSTS = frozenset({"i4c.mha.gov.in", "www.csk.gov.in"})
SUPPORTED_LANGUAGE = "en"
VERIFIED = "verified"
VERIFICATION_STATUSES = frozenset({VERIFIED, "needs_review"})

MAX_MATCHES = 3
# A passage matches only when all three hold: the message has a term from every one of the
# passage's match groups, at least MIN_MATCHED_TERMS distinct terms are shared, and
# similarity is at least MIN_SCORE.
MIN_SCORE = 0.15
MIN_MATCHED_TERMS = 2

_TOKEN = re.compile(r"[a-z0-9]+")
_LINK_IN_TEXT = re.compile(r"https?://|www\.", re.IGNORECASE)
_LINK_TERM = "link"
# Safety advice ("Never share your OTP", "Beware of fake links") talks about a scam without
# being one. Text from such a cue to the end of its sentence is ignored when matching.
_ADVICE = re.compile(
    r"\b(?:never|do not|don['’]?t|beware|be careful|avoid)\b[^.!?\n]*", re.IGNORECASE
)
_STOP_WORDS = frozenset(
    """
    a about after again all also am an and any are as at be been before being but by can could
    did do does doing for from get got had has have having he her here him his how i if in into
    is it its just like me more most my no not now of on once one only or other our out over
    own please she so some such than that the their them then there these they this those to
    too up us very was we were what when where which who why will with would you your yours
    dear hi hello ok okay thanks thank well http https www com
    """.split()
)


class CorpusError(Exception):
    """The guidance corpus is missing, malformed, or fails validation."""


@dataclass(frozen=True)
class Source:
    id: str
    title: str
    publisher: str
    url: str
    document_type: str
    published: str | None
    retrieved: str
    language: str
    licence_note: str
    verification: str


@dataclass(frozen=True)
class Passage:
    id: str
    source_id: str
    topic: str
    section: str
    summary: str
    # A message must contain a term from every group, e.g. what is asked for and the pressure used.
    match_groups: tuple[tuple[str, ...], ...]
    verification_status: str
    verification_note: str


@dataclass(frozen=True)
class Match:
    passage: Passage
    source: Source
    matched_terms: tuple[str, ...]


def tokenize(text: str) -> list[str]:
    tokens = []
    for token in _TOKEN.findall(text.lower()):
        # Fold simple plurals so "jobs" matches "job" and "fees" matches "fee".
        if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
            token = token[:-1]
        if len(token) > 1 and token not in _STOP_WORDS:
            tokens.append(token)
    return tokens


def _text(record: dict, field: str, where: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise CorpusError(f"{where}: '{field}' must be a non-empty string.")
    return value


def _iso_date(value, field: str, where: str, required: bool) -> str | None:
    if value is None and not required:
        return None
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError):
        raise CorpusError(f"{where}: '{field}' must be a date in YYYY-MM-DD form.") from None
    return value


def _records(data: dict, key: str) -> list[dict]:
    records = data.get(key)
    if not isinstance(records, list) or not records or not all(isinstance(r, dict) for r in records):
        raise CorpusError(f"'{key}' must be a non-empty list of objects.")
    return records


def _parse_source(record: dict) -> Source:
    where = f"source {record.get('id')!r}"
    url = _text(record, "url", where)
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in ALLOWED_HOSTS or parts.username or parts.port:
        raise CorpusError(f"{where}: URL must be https on one of {sorted(ALLOWED_HOSTS)}.")
    language = _text(record, "language", where)
    if language != SUPPORTED_LANGUAGE:
        raise CorpusError(f"{where}: only '{SUPPORTED_LANGUAGE}' sources are supported.")
    return Source(
        id=_text(record, "id", where),
        title=_text(record, "title", where),
        publisher=_text(record, "publisher", where),
        url=url,
        document_type=_text(record, "document_type", where),
        published=_iso_date(record.get("published"), "published", where, required=False),
        retrieved=_iso_date(record.get("retrieved"), "retrieved", where, required=True),
        language=language,
        licence_note=_text(record, "licence_note", where),
        verification=_text(record, "verification", where),
    )


def _parse_passage(record: dict, sources: dict[str, Source]) -> Passage:
    where = f"passage {record.get('id')!r}"
    source_id = _text(record, "source_id", where)
    if source_id not in sources:
        raise CorpusError(f"{where}: unknown source {source_id!r}.")
    summary = _text(record, "summary", where)
    if _LINK_IN_TEXT.search(summary):
        raise CorpusError(f"{where}: summaries must not contain links.")
    groups = record.get("match_groups")
    if (
        not isinstance(groups, list)
        or not groups
        or not all(isinstance(group, list) and group for group in groups)
        or not all(isinstance(term, str) and tokenize(term) for group in groups for term in group)
    ):
        raise CorpusError(f"{where}: 'match_groups' must be a non-empty list of lists of terms.")
    status = _text(record, "verification_status", where)
    if status not in VERIFICATION_STATUSES:
        raise CorpusError(f"{where}: unknown verification_status {status!r}.")
    return Passage(
        id=_text(record, "id", where),
        source_id=source_id,
        topic=_text(record, "topic", where),
        section=_text(record, "section", where),
        summary=summary,
        match_groups=tuple(tuple(group) for group in groups),
        verification_status=status,
        verification_note=_text(record, "verification_note", where),
    )


def load_corpus(path: Path = DEFAULT_CORPUS) -> tuple[dict[str, Source], list[Passage]]:
    """Read and validate the corpus. Raises CorpusError rather than serving doubtful data."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as error:
        raise CorpusError(f"Cannot read guidance corpus: {error}") from None
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise CorpusError(f"Guidance corpus is not valid JSON: {error}") from None
    if not isinstance(data, dict):
        raise CorpusError("Guidance corpus must be a JSON object.")

    sources: dict[str, Source] = {}
    for record in _records(data, "sources"):
        source = _parse_source(record)
        if source.id in sources:
            raise CorpusError(f"Duplicate source id {source.id!r}.")
        sources[source.id] = source

    passages: list[Passage] = []
    seen: set[str] = set()
    for record in _records(data, "passages"):
        passage = _parse_passage(record, sources)
        if passage.id in seen:
            raise CorpusError(f"Duplicate passage id {passage.id!r}.")
        seen.add(passage.id)
        passages.append(passage)
    return sources, passages


# Words in Devanagari (letters and vowel signs, not the danda) or in Latin letters, and
# words in the Telugu, Bengali and Arabic (Urdu) scripts. A word in those three scripts
# must start with one of its letters, so a stray zero-width joiner is never a word.
_UR_LETTERS = "ؐ-ؚؠ-ٟٮ-ۓە-ۯۺ-ۿ"
_HINDI_OR_LATIN_WORD = re.compile(
    r"[ऀ-ॣॱ-ॿ]+|[a-z0-9]+"
    "|[ఀ-౿][ఀ-౿‌‍]*"
    "|[ঀ-৿][ঀ-৿‌‍]*"
    f"|[{_UR_LETTERS}][{_UR_LETTERS}‌‍]*"
)
_SENTENCE = re.compile(r"[^.!?।۔؟\n]+")
# The same Telugu, Bengali or Urdu word can be typed in more than one way: with or without
# zero-width joiners, Bengali য় ড় ঢ় as one character or as letter plus nukta, and Urdu
# with Arabic-keyboard letters (ك ي ى ه for ک ی ہ). Words in those scripts are reduced to
# one spelling. Devanagari and Latin words are left exactly as they are.
_ONE_SPELLING = str.maketrans(
    {
        "‌": None,
        "‍": None,
        "ড়": "ড়",
        "ঢ়": "ঢ়",
        "য়": "য়",
        "ك": "ک",
        "ي": "ی",
        "ى": "ی",
        "ه": "ہ",
    }
)
# Hindi negation usually follows the object ("OTP किसी को न बताएं", "OTP share mat
# karo"), so the English rule of ignoring text after "never" does not work. A sentence
# with a Hindi negation word is left out of matching entirely: a missed match is safer
# than showing a phishing warning for safety advice.
_DEVANAGARI_NEGATION = frozenset({"न", "ना", "नहीं", "मत"})
_ROMAN_NEGATION = frozenset({"nahi", "nahin", "nhi"})
# "na" and "mat" are also English or abbreviations, so they count only next to other
# romanised-Hindi words.
_ROMAN_NEGATION_IF_HINDI = frozenset({"na", "naa", "mat"})
# Telugu, Urdu and Bengali negation words, treated the same way. Telugu also forms
# "don't" with a suffix (చెప్పకండి, పంపవద్దు), checked in _is_hindi_advice.
_OTHER_NEGATION = frozenset(
    word.translate(_ONE_SPELLING)
    for word in ("వద్దు", "కూడదు", "ఎప్పుడూ", "ఎవరికీ", "ఎవరితోనూ", "نہ", "مت", "نہیں", "کبھی", "না", "কখনো", "কখনও", "নয়")
)


def _one_spelling(word: str) -> str:
    return word.translate(_ONE_SPELLING) if "؀" <= word[0] < "ऀ" or word[0] >= "ঀ" else word


def _hindi_words(text: str) -> list[str]:
    return [_one_spelling(word) for word in _HINDI_OR_LATIN_WORD.findall(text.lower())]


def _is_hindi_advice(sentence: str) -> bool:
    words = set(_hindi_words(sentence))
    if words & (_DEVANAGARI_NEGATION | _ROMAN_NEGATION | _OTHER_NEGATION):
        return True
    if any(word.endswith("కండి") or "వద్దు" in word for word in words):
        return True
    return bool(words & _ROMAN_NEGATION_IF_HINDI) and bool(words & ROMAN_HINDI_CUES)


def _drop_hindi_advice(text: str) -> str:
    # Only advice sentences are blanked; everything else, including links, is kept as is.
    return _SENTENCE.sub(lambda sentence: " " if _is_hindi_advice(sentence.group()) else sentence.group(), text)


class TermMap:
    """Maps Hindi, romanised-Hindi, Telugu, Urdu and Bengali words and short phrases to existing corpus terms."""

    def __init__(self, phrases: dict[tuple[str, ...], str]):
        self._phrases = phrases
        self._longest = max((len(phrase) for phrase in phrases), default=0)

    @classmethod
    def from_file(cls, path: Path, vocabulary: set[str]) -> "TermMap":
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except OSError as error:
            raise CorpusError(f"Cannot read term map: {error}") from None
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise CorpusError(f"Term map is not valid JSON: {error}") from None
        concepts = data.get("concepts") if isinstance(data, dict) else None
        if not isinstance(concepts, dict) or not concepts:
            raise CorpusError("Term map must have a non-empty 'concepts' object.")

        phrases: dict[tuple[str, ...], str] = {}
        for concept, terms in concepts.items():
            if tokenize(concept) != [concept] or concept not in vocabulary:
                raise CorpusError(f"Term map concept {concept!r} is not a retrieval term in the corpus.")
            if not isinstance(terms, list) or not terms:
                raise CorpusError(f"Term map concept {concept!r} needs a non-empty list of terms.")
            for term in terms:
                words = tuple(_hindi_words(term)) if isinstance(term, str) else ()
                # Spelling variants are reduced as in _hindi_words; Devanagari and Latin
                # terms are compared exactly as before.
                if not words or "".join(words) != "".join(str(term).lower().split()).translate(_ONE_SPELLING):
                    raise CorpusError(f"Term map entry {term!r} for {concept!r} is not a plain word or phrase.")
                # A single Latin word that is already a corpus term would change English results.
                if len(words) == 1 and words[0].isascii() and words[0] in vocabulary:
                    raise CorpusError(f"Term map entry {term!r} is already an English retrieval term.")
                if words in phrases:
                    raise CorpusError(f"Term map entry {term!r} appears more than once.")
                phrases[words] = concept
        return cls(phrases)

    def expand(self, text: str) -> list[str]:
        """Return the corpus terms for every mapped word or phrase found in the text."""
        words = _hindi_words(text)
        found = []
        for start in range(len(words)):
            for length in range(1, min(self._longest, len(words) - start) + 1):
                concept = self._phrases.get(tuple(words[start : start + length]))
                if concept:
                    found.append(concept)
        return found


class GuidanceIndex:
    """TF-IDF index over the verified passages of a corpus."""

    def __init__(self, sources: dict[str, Source], passages: list[Passage]):
        self._sources = sources
        # Passages still awaiting review are kept in the file but never served.
        self._passages = [passage for passage in passages if passage.verification_status == VERIFIED]

        self._groups = [
            [{token for term in group for token in tokenize(term)} for group in passage.match_groups]
            for passage in self._passages
        ]
        documents = [
            Counter(tokenize(" ".join((passage.topic, passage.summary))) + sorted(set().union(*groups)))
            for passage, groups in zip(self._passages, self._groups)
        ]
        document_frequency = Counter(term for document in documents for term in document)
        total = len(documents)
        self._idf = {
            term: math.log((1 + total) / (1 + frequency)) + 1
            for term, frequency in document_frequency.items()
        }
        self._vectors = [self._weigh(document) for document in documents]
        self._term_map = TermMap({})

    @property
    def vocabulary(self) -> set[str]:
        return set(self._idf)

    def verified_passage(self, passage_id: str) -> tuple[Passage, Source]:
        """Return one verified passage and its source by id, for fixed (non-search) use."""
        for passage in self._passages:
            if passage.id == passage_id:
                return passage, self._sources[passage.source_id]
        raise CorpusError(f"No verified passage with id {passage_id!r}.")

    def use_term_map(self, term_map: TermMap) -> "GuidanceIndex":
        self._term_map = term_map
        return self

    @classmethod
    def from_file(cls, path: Path = DEFAULT_CORPUS, term_map_path: Path | None = DEFAULT_TERM_MAP) -> "GuidanceIndex":
        index = cls(*load_corpus(path))
        if term_map_path is not None:
            index.use_term_map(TermMap.from_file(term_map_path, index.vocabulary))
        return index

    def _weigh(self, counts: Counter) -> dict[str, float]:
        weights = {
            term: (1 + math.log(count)) * self._idf[term]
            for term, count in counts.items()
            if term in self._idf
        }
        norm = math.sqrt(sum(weight * weight for weight in weights.values()))
        return {term: weight / norm for term, weight in weights.items()} if norm else {}

    def search(self, text: str, limit: int = MAX_MATCHES) -> list[Match]:
        """Return the most similar passages, or an empty list when nothing is similar enough."""
        text = _drop_hindi_advice(_ADVICE.sub(" ", text))
        tokens = tokenize(text) + self._term_map.expand(text)
        if _LINK_IN_TEXT.search(text):
            tokens.append(_LINK_TERM)  # a web address in the message counts as the word "link"
        query = self._weigh(Counter(tokens))
        if not query:
            return []

        scored = []
        for position, vector in enumerate(self._vectors):
            shared = sorted(query.keys() & vector.keys())
            score = sum(query[term] * vector[term] for term in shared)
            if (
                score >= MIN_SCORE
                and len(shared) >= MIN_MATCHED_TERMS
                and all(group.intersection(shared) for group in self._groups[position])
            ):
                scored.append((score, position, shared))

        scored.sort(key=lambda item: (-item[0], item[1]))
        return [
            Match(
                passage=self._passages[position],
                source=self._sources[self._passages[position].source_id],
                matched_terms=tuple(shared),
            )
            for _, position, shared in scored[:limit]
        ]
