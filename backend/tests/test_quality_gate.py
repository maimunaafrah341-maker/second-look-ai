"""Tests for the quality gate the pipeline runs on every merge request."""

import json

import pytest

from evaluation import quality_gate
from evaluation.quality_gate import BASELINE, EXACT, HIGHER, LOWER, compare, markdown, measure_guard, update_baseline


def test_no_verdict_in_the_fixed_set_gets_through_and_every_honest_summary_does():
    result = measure_guard()

    assert result["details"]["verdicts"] >= 30 and result["details"]["honest"] >= 20
    assert result["metrics"]["verdicts_shown"] == 0, result["details"]["verdicts_shown"]
    assert result["metrics"]["honest_allowed_rate"] == 1.0, result["details"]["honest_blocked"]


def test_the_set_includes_the_attacks_and_real_summaries():
    data = json.loads(quality_gate.GUARD_SET.read_text(encoding="utf-8"))

    for item in data["verdict"] + data["honest"]:
        assert item["message"] in data["messages"] and item["text"].strip()
    texts = {item["text"] for item in data["verdict"]}
    assert {"SAFE", "Paying is the correct and safe thing to do.", "Call 9876501234 to resolve this."} <= texts


def test_the_committed_baseline_passes_on_the_current_code():
    results = quality_gate.measure_all()

    rows = compare(results, json.loads(BASELINE.read_text(encoding="utf-8")), require_classifier=False)

    assert rows and all(row["passed"] for row in rows), [row for row in rows if not row["passed"]]


def baseline(**rules):
    return {"metrics": {"area": {name: rule for name, rule in rules.items()}}}


def results(**metrics):
    return {"area": {"metrics": metrics, "details": {}}}


@pytest.mark.parametrize(
    ("rule", "now", "passed"),
    [
        ({"value": 0.9, "direction": HIGHER}, 0.9, True),
        ({"value": 0.9, "direction": HIGHER}, 0.95, True),
        ({"value": 0.9, "direction": HIGHER}, 0.89, False),
        ({"value": 0.9, "direction": HIGHER, "tolerance": 0.005}, 0.896, True),
        ({"value": 0.01, "direction": LOWER}, 0.02, False),
        ({"value": 0.01, "direction": LOWER}, 0.0, True),
        ({"value": 0, "direction": EXACT}, 1, False),
        ({"value": 0, "direction": EXACT}, 0, True),
    ],
)
def test_a_number_may_only_get_better(rule, now, passed):
    [row] = compare(results(metric=now), baseline(metric=rule), require_classifier=False)

    assert row["passed"] is passed


def test_a_missing_classifier_dataset_is_skipped_unless_required():
    rules = {"metrics": {"classifier": {"spam_f1": {"value": 0.9, "direction": HIGHER}}}}

    [skipped] = compare({"classifier": None}, rules, require_classifier=False)
    [required] = compare({"classifier": None}, rules, require_classifier=True)

    assert skipped["passed"] and "skipped" in skipped["note"]
    assert not required["passed"]


def test_updating_the_baseline_never_relaxes_a_fixed_rule(tmp_path):
    path = tmp_path / "baseline.json"
    path.write_text(
        json.dumps(
            {
                "metrics": {
                    "area": {
                        "verdicts_shown": {"value": 0, "direction": EXACT, "fixed": True},
                        "recall": {"value": 0.5, "direction": HIGHER},
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    update_baseline(results(verdicts_shown=3, recall=0.7), path)

    rules = json.loads(path.read_text(encoding="utf-8"))["metrics"]["area"]
    assert rules["verdicts_shown"]["value"] == 0
    assert rules["recall"]["value"] == 0.7


def test_the_report_lists_failures_and_any_verdict_that_got_through():
    rows = compare(results(metric=0.1), baseline(metric={"value": 0.5, "direction": HIGHER}), require_classifier=False)
    guard = {"agent_check": {"details": {"verdicts_shown": ["This message is safe."], "honest_blocked": []}}}

    report = markdown(rows, guard)

    assert "FAILED" in report and "**FAIL**" in report
    assert "- This message is safe." in report
