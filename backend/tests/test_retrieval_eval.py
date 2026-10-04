"""Regression check on the hand-written retrieval evaluation set.

The recorded counts are what the retriever produced when the set was written. They
describe these examples only. A change to the corpus or the matching rules that moves
any count should be looked at, then recorded here and in docs/guidance_sources.md.
"""

import pytest

from app.guidance import GuidanceIndex, load_corpus
from evaluation.evaluate_retrieval import CATEGORIES, evaluate, load_items

RECORDED = {
    "development": {"tp": 12, "fp": 0, "fn": 0, "tn": 23},
    "check": {"tp": 7, "fp": 3, "fn": 4, "tn": 13},
}


@pytest.fixture(scope="module")
def items() -> list[dict]:
    return load_items()


def test_evaluation_set_is_well_formed(items):
    sources, _ = load_corpus()

    assert len({item["id"] for item in items}) == len(items)
    assert len({item["message"] for item in items}) == len(items)
    for split in RECORDED:
        categories = {item["category"] for item in items if item["split"] == split}
        assert categories == set(CATEGORIES)
    for item in items:
        assert item["split"] in RECORDED
        assert item["message"].strip()
        assert set(item["expected_sources"]) <= set(sources)
        if item["category"] != "malicious":
            assert item["expected_sources"] == []


def test_evaluation_set_keeps_the_two_earlier_false_matches(items):
    by_message = {item["message"]: item for item in items}

    otp = by_message["Your OTP is 482913. Never share your OTP with anyone."]
    link = by_message["Can you send me the link to the meeting? I forgot my password for the portal again."]

    assert otp["category"] == "benign_security_awareness" and otp["expected_sources"] == []
    assert link["category"] == "unrelated" and link["expected_sources"] == []


@pytest.mark.parametrize("split", sorted(RECORDED))
def test_retrieval_counts_match_the_recorded_results(items, split):
    result = evaluate(GuidanceIndex.from_file(), [item for item in items if item["split"] == split])

    assert {key: result[key] for key in ("tp", "fp", "fn", "tn")} == RECORDED[split]


def test_evaluation_is_deterministic(items):
    index = GuidanceIndex.from_file()

    assert evaluate(index, items) == evaluate(index, items)
