"""Regression check on the Telugu, Urdu and Bengali evaluation set.

The set was written by the project and has not been reviewed by native speakers. The
recorded counts are engineering validation on these examples only; they are not
evidence of accuracy in these languages. A change that moves any count should be looked
at, then recorded here.
"""

from pathlib import Path

import pytest

from app.guidance import GuidanceIndex, load_corpus
from app.language import estimate_tag
from evaluation.evaluate_multilingual import (
    CATEGORIES,
    FINDING_CATEGORIES,
    LANGUAGES,
    SPLITS,
    evaluate,
    load_items,
)

# Before the Telugu, Urdu and Bengali rules, only links were found (development: exact 6,
# tp 2, fn 8; check: exact 5, tp 1, fn 7), and guidance only for the KYC message, through
# its English words (development tp 1; check tp 0).
#
# With the rules: the one check miss per language is the same conditional payment demand
# ("if you don't pay today, the connection will be cut"), which the request forms do not
# cover. The check split was not used to adjust the rules, so the miss is left as found.
#
# The one false guidance match per language on the check split is the UPI PIN reward
# message (chk-04). The corpus has no verified guidance on UPI PIN requests, so nothing is
# expected, as for the comparable English item dev-17 in retrieval_eval.json; the phishing
# guidance it retrieves is counted as a false match.
RECORDED = {
    ("te", "development"): {"exact": 12, "tp": 10, "fn": 0, "fp": 0, "retrieval": {"tp": 6, "fp": 0, "fn": 0, "tn": 6}},
    ("te", "check"): {"exact": 9, "tp": 7, "fn": 1, "fp": 0, "retrieval": {"tp": 5, "fp": 1, "fn": 0, "tn": 4}},
    ("ur", "development"): {"exact": 12, "tp": 10, "fn": 0, "fp": 0, "retrieval": {"tp": 6, "fp": 0, "fn": 0, "tn": 6}},
    ("ur", "check"): {"exact": 9, "tp": 7, "fn": 1, "fp": 0, "retrieval": {"tp": 5, "fp": 1, "fn": 0, "tn": 4}},
    ("bn", "development"): {"exact": 12, "tp": 10, "fn": 0, "fp": 0, "retrieval": {"tp": 6, "fp": 0, "fn": 0, "tn": 6}},
    ("bn", "check"): {"exact": 9, "tp": 7, "fn": 1, "fp": 0, "retrieval": {"tp": 5, "fp": 1, "fn": 0, "tn": 4}},
}

TESTS_DIR = Path(__file__).resolve().parent


@pytest.fixture(scope="module")
def items() -> list[dict]:
    return load_items()


def test_evaluation_set_is_well_formed(items):
    sources, _ = load_corpus()

    assert len({item["id"] for item in items}) == len(items)
    assert len({item["message"] for item in items}) == len(items)
    for language in LANGUAGES:
        for split in SPLITS:
            subset = [item for item in items if item["language"] == language and item["split"] == split]
            assert {item["category"] for item in subset} == set(CATEGORIES)
    for item in items:
        assert item["language"] in LANGUAGES
        assert item["split"] in SPLITS
        assert item["id"].startswith(f"{item['language']}-{'dev' if item['split'] == 'development' else 'chk'}-")
        assert item["message"].strip()
        # Expected findings are listed once each, in the fixed category order.
        assert item["expected_findings"] == [c for c in FINDING_CATEGORIES if c in item["expected_findings"]]
        assert set(item["expected_sources"]) <= set(sources)
        if item["category"] != "scam":
            assert item["expected_findings"] == []
        if item["category"] in ("safety_advice", "ordinary"):
            assert item["expected_sources"] == []


def test_every_message_is_estimated_as_its_language(items):
    # The estimate decides the coverage notice and keeps the English classifier off.
    for item in items:
        assert estimate_tag(item["message"]) == item["language"], item["id"]


def test_check_messages_are_not_reused_in_unit_tests(items):
    # The check split stays held out: no rule fixture may copy one of its messages.
    test_text = "".join(
        path.read_text(encoding="utf-8") for path in TESTS_DIR.glob("test_*.py") if path.name != Path(__file__).name
    )
    for item in items:
        if item["split"] == "check":
            assert item["message"] not in test_text, item["id"]


@pytest.mark.parametrize(("language", "split"), sorted(RECORDED))
def test_counts_match_the_recorded_results(items, language, split):
    result = evaluate(GuidanceIndex.from_file(), items)[(language, split)]
    findings, retrieval = result["findings"], result["retrieval"]

    assert {key: findings[key] for key in ("exact", "tp", "fn", "fp")} | {
        "retrieval": {key: retrieval[key] for key in ("tp", "fp", "fn", "tn")}
    } == RECORDED[(language, split)]


def test_evaluation_is_deterministic(items):
    index = GuidanceIndex.from_file()

    assert evaluate(index, items) == evaluate(index, items)
