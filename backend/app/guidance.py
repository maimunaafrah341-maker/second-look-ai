"""Retrieval of official cyber-safety guidance from a small, hand-checked local corpus.

Retrieval is keyword similarity (TF-IDF with cosine similarity) written in plain
Python. It makes no network requests, uses no model, and is independent of the
warning-sign rules, the classifier, and any language-model provider.

Every title, publisher, and URL returned comes from the validated corpus file.
A match means "this guidance uses similar words", not "this message is fraudulent".
"""

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT_CORPUS = Path(__file__).resolve().parent / "data" / "guidance.json"

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

    @classmethod
    def from_file(cls, path: Path = DEFAULT_CORPUS) -> "GuidanceIndex":
        return cls(*load_corpus(path))

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
        text = _ADVICE.sub(" ", text)
        tokens = tokenize(text)
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
