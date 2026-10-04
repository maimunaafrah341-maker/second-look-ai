"""Tests for the guidance corpus and retriever.

The queries below are written for these tests. They check that retrieval behaves
sensibly on a few examples; they are not a measured evaluation.
"""

import copy
import json
import socket
from urllib.parse import urlsplit

import pytest

from app.guidance import (
    ALLOWED_HOSTS,
    DEFAULT_CORPUS,
    MAX_MATCHES,
    CorpusError,
    GuidanceIndex,
    load_corpus,
    tokenize,
)


@pytest.fixture(scope="module")
def index() -> GuidanceIndex:
    return GuidanceIndex.from_file()


@pytest.fixture
def corpus_data() -> dict:
    return copy.deepcopy(json.loads(DEFAULT_CORPUS.read_text(encoding="utf-8")))


def write_corpus(tmp_path, data) -> object:
    path = tmp_path / "guidance.json"
    path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
    return path


# --- The shipped corpus -------------------------------------------------------


def test_shipped_corpus_loads_and_every_passage_has_provenance():
    sources, passages = load_corpus()

    assert len(sources) == 5
    assert len(passages) == 10
    for source in sources.values():
        assert source.title and source.publisher and source.retrieved
        assert source.licence_note and source.verification
        assert source.language == "en"
    for passage in passages:
        assert passage.source_id in sources
        assert passage.section and passage.verification_note
        assert len(passage.match_groups) >= 2
    held_back = {p.id for p in passages if p.verification_status != "verified"}
    assert held_back == {"digital-arrest-how-it-works", "digital-arrest-precautions"}


def test_shipped_corpus_links_only_to_allowed_official_hosts():
    sources, passages = load_corpus()

    for source in sources.values():
        parts = urlsplit(source.url)
        assert parts.scheme == "https"
        assert parts.hostname in ALLOWED_HOSTS
    # Sites whose policies require permission to link are named in words only.
    corpus_text = DEFAULT_CORPUS.read_text(encoding="utf-8").lower()
    for host in ("cybercrime.gov.in", "rbi.org.in", "sancharsaathi.gov.in"):
        assert host not in corpus_text
    for passage in passages:
        assert "http" not in passage.summary.lower()
        assert "www." not in passage.summary.lower()


# --- Relevance ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("message", "expected_first"),
    [
        (
            "Earn Rs 5000 daily with a captcha typing job. Pay registration fee Rs 500 to start.",
            "captcha-jobs-how-it-works",
        ),
        (
            "I met someone on a matrimony site and he wants me to invest in crypto for high returns",
            "matrimonial-investment-precautions",
        ),
        (
            "Dear customer your account will be blocked today. Update KYC by clicking this "
            "link http://bit.ly/x",
            "phishing-donts",
        ),
        ("I clicked the link and entered my password, what should I do", "phishing-if-you-responded"),
        ("I lost money in an online fraud, where do I report", "report-helpline-1930"),
    ],
)
def test_relevant_guidance_is_ranked_first(index, message, expected_first):
    matches = index.search(message)

    assert matches, "expected at least one match"
    assert matches[0].passage.id == expected_first
    assert len(matches) <= MAX_MATCHES
    assert len(matches[0].matched_terms) >= 2


def test_search_is_deterministic(index):
    message = "Your card is blocked. Update KYC by clicking this link and enter your PIN."

    first = [match.passage.id for match in index.search(message)]

    assert first
    assert first == [match.passage.id for match in index.search(message)]


def test_passages_held_back_for_review_are_not_served_from_the_shipped_corpus(index):
    messages = [
        "This is Mumbai police. A parcel in your name contains drugs. You are under digital "
        "arrest, stay on the video call.",
        "CBI officer says my Aadhaar is linked to money laundering and I will be arrested",
    ]

    for message in messages:
        assert all(match.source.id != "i4c-digital-arrest-2025" for match in index.search(message))


@pytest.mark.parametrize(
    "message",
    [
        # Safety advice that mentions a scam is not itself a request.
        "Your OTP is 482913. Never share your OTP with anyone.",
        "Bank never asks for your PIN or password. Beware of fake KYC update links.",
        "Cyber safety tip: do not click on unknown links and never share your card details.",
        # A link and a password with no pressure or lure.
        "Can you send me the link to the meeting? I forgot my password for the portal again.",
    ],
)
def test_advice_and_ordinary_mentions_do_not_match(index, message):
    assert index.search(message) == []


def test_advice_in_one_sentence_does_not_hide_a_request_in_another(index):
    message = "Do not ignore this message. Your account is blocked, update KYC at http://bit.ly/x"

    matches = index.search(message)

    assert matches and matches[0].source.id == "certin-avoid-phishing"


# --- Citation integrity -------------------------------------------------------


def test_every_match_cites_a_corpus_record_exactly(index):
    sources, passages = load_corpus()
    passages_by_id = {passage.id: passage for passage in passages}

    matches = index.search(
        "urgent captcha job registration fee, matrimony crypto investment, blocked kyc link "
        "password, clicked link, report fraud helpline",
        limit=50,
    )

    assert len(matches) >= 5
    for match in matches:
        assert match.passage == passages_by_id[match.passage.id]
        assert match.source == sources[match.passage.source_id]
        group_terms = [term for group in match.passage.match_groups for term in group]
        passage_text = " ".join((match.passage.topic, match.passage.summary, *group_terms))
        assert set(match.matched_terms) <= set(tokenize(passage_text))


def test_search_makes_no_network_calls(index, monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)

    assert index.search("Update KYC by clicking http://bit.ly/x or your account is blocked")


# --- Empty and unrelated results ----------------------------------------------


@pytest.mark.parametrize(
    "message",
    [
        "Hi, are we still meeting for lunch at 1 pm tomorrow?",
        "Call me when you reach home, I will send the money for groceries to your bank account.",
        "The job interview went well, they will call me next week about the offer.",
        "Police station road is closed today, take the other route.",
        "Report for class 8 is due Monday; please email it to the teacher.",
        "Here are the photos: https://example.com/album",
        # Outside the corpus: no guidance on this topic has been verified yet.
        "Your electricity will be disconnected tonight at 9.30 pm. Contact officer 98xxxxxx10",
        # Hindi: retrieval is English-only.
        "आपका खाता बंद हो जाएगा। तुरंत अपना ओटीपी बताएं।",
    ],
)
def test_unrelated_or_unsupported_messages_return_nothing(index, message):
    assert index.search(message) == []


@pytest.mark.parametrize(
    "message",
    ["", "   ", "?!...,,;;", "\x00\x01\x02\t\n", "the and of to", "<script>alert(1)</script>", "a" * 5000],
)
def test_malformed_input_returns_nothing_without_error(index, message):
    assert index.search(message) == []


# --- Corrupt corpus data ------------------------------------------------------


def test_missing_corpus_file_is_rejected(tmp_path):
    with pytest.raises(CorpusError, match="Cannot read"):
        load_corpus(tmp_path / "absent.json")


@pytest.mark.parametrize("content", ["not json", "[]", '{"sources": [], "passages": []}', '{"sources": "x"}'])
def test_malformed_corpus_file_is_rejected(tmp_path, content):
    with pytest.raises(CorpusError):
        load_corpus(write_corpus(tmp_path, content))


@pytest.mark.parametrize(
    "url",
    [
        "http://i4c.mha.gov.in/advisory.pdf",
        "https://example.com/advisory.pdf",
        "https://i4c.mha.gov.in.example.com/advisory.pdf",
        "https://user@i4c.mha.gov.in/advisory.pdf",
        "https://cybercrime.gov.in/",
        "javascript:alert(1)",
        "",
    ],
)
def test_source_with_disallowed_url_is_rejected(tmp_path, corpus_data, url):
    corpus_data["sources"][0]["url"] = url

    with pytest.raises(CorpusError):
        load_corpus(write_corpus(tmp_path, corpus_data))


def test_duplicate_ids_are_rejected(tmp_path, corpus_data):
    duplicate_source = copy.deepcopy(corpus_data)
    duplicate_source["sources"].append(duplicate_source["sources"][0])
    with pytest.raises(CorpusError, match="Duplicate source"):
        load_corpus(write_corpus(tmp_path, duplicate_source))

    duplicate_passage = copy.deepcopy(corpus_data)
    duplicate_passage["passages"].append(duplicate_passage["passages"][0])
    with pytest.raises(CorpusError, match="Duplicate passage"):
        load_corpus(write_corpus(tmp_path, duplicate_passage))


def test_passage_with_unknown_source_is_rejected(tmp_path, corpus_data):
    corpus_data["passages"][0]["source_id"] = "invented-source"

    with pytest.raises(CorpusError, match="unknown source"):
        load_corpus(write_corpus(tmp_path, corpus_data))


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("sources", "title", ""),
        ("sources", "publisher", None),
        ("sources", "retrieved", "yesterday"),
        ("sources", "published", "2025-13-40"),
        ("sources", "language", "hi"),
        ("sources", "licence_note", " "),
        ("passages", "summary", ""),
        ("passages", "summary", "See https://example.com for details."),
        ("passages", "section", None),
        ("passages", "match_groups", "arrest"),
        ("passages", "match_groups", []),
        ("passages", "match_groups", [["link"], []]),
        ("passages", "match_groups", [["link"], [""]]),
        ("passages", "verification_status", "probably fine"),
    ],
)
def test_record_with_invalid_field_is_rejected(tmp_path, corpus_data, section, field, value):
    corpus_data[section][0][field] = value

    with pytest.raises(CorpusError):
        load_corpus(write_corpus(tmp_path, corpus_data))


def test_review_status_alone_decides_whether_a_passage_is_served(tmp_path, corpus_data):
    message = "police say I am under digital arrest on a video call about drugs"
    for passage in corpus_data["passages"]:
        if passage["source_id"] == "i4c-digital-arrest-2025":
            passage["verification_status"] = "verified"
    verified = GuidanceIndex.from_file(write_corpus(tmp_path, corpus_data))
    assert verified.search(message)[0].source.id == "i4c-digital-arrest-2025"

    for passage in corpus_data["passages"]:
        if passage["source_id"] == "i4c-digital-arrest-2025":
            passage["verification_status"] = "needs_review"
    held_back = GuidanceIndex.from_file(write_corpus(tmp_path, corpus_data))
    assert held_back.search(message) == []
