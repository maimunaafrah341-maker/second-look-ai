"""Check warning signs and guidance retrieval on the Telugu, Urdu and Bengali set.

Usage, from the repository root:

    python backend/evaluation/evaluate_multilingual.py

The messages were written by the project for engineering validation. They are not real
messages and have not been reviewed by native speakers, so these numbers show whether
the rules behave as intended on these examples. They are not evidence of accuracy in
Telugu, Urdu or Bengali, and must not be presented as such.

Warning signs are counted per category, per message:

- correct (TP): the category was expected and found.
- missed (FN): the category was expected and not found.
- false (FP): the category was found but not expected.

A message is "exact" when the found categories are exactly the expected ones.
Guidance retrieval is counted with the same rules as evaluate_retrieval.py.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.guidance import GuidanceIndex  # noqa: E402
from app.warning_signs import detect_warning_signs  # noqa: E402
from evaluation.evaluate_retrieval import evaluate as evaluate_retrieval  # noqa: E402

EVAL_SET = Path(__file__).resolve().parent / "multilingual_eval.json"
LANGUAGES = ("te", "ur", "bn")
SPLITS = ("development", "check")
CATEGORIES = ("scam", "help_request", "safety_advice", "ordinary")
FINDING_CATEGORIES = ("urgency_pressure", "credential_request", "link", "payment_demand")


def load_items(path: Path = EVAL_SET) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["items"]


def evaluate_findings(items: list[dict]) -> dict:
    counts = {"tp": 0, "fp": 0, "fn": 0}
    exact, mismatches = 0, []

    for item in items:
        expected = set(item["expected_findings"])
        found = {finding.category for finding in detect_warning_signs(item["message"])}
        counts["tp"] += len(expected & found)
        counts["fn"] += len(expected - found)
        counts["fp"] += len(found - expected)
        if found == expected:
            exact += 1
        else:
            mismatches.append(
                {
                    "id": item["id"],
                    "missed": [c for c in FINDING_CATEGORIES if c in expected - found],
                    "false": [c for c in FINDING_CATEGORIES if c in found - expected],
                }
            )
    return {"items": len(items), "exact": exact, **counts, "mismatches": mismatches}


def evaluate(index: GuidanceIndex, items: list[dict]) -> dict:
    """Results per language and split."""
    results = {}
    for language in LANGUAGES:
        for split in SPLITS:
            subset = [item for item in items if item["language"] == language and item["split"] == split]
            results[(language, split)] = {
                "findings": evaluate_findings(subset),
                "retrieval": evaluate_retrieval(index, subset),
            }
    return results


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    print("Engineering validation only: written by the project, not native-reviewed.")
    results = evaluate(GuidanceIndex.from_file(), load_items())
    for (language, split), result in results.items():
        findings, retrieval = result["findings"], result["retrieval"]
        print(f"\n{language} {split}: {findings['items']} messages")
        print(
            f"  warning signs: {findings['exact']}/{findings['items']} exact; "
            f"correct {findings['tp']}, missed {findings['fn']}, false {findings['fp']}"
        )
        print(
            f"  guidance: correct matches {retrieval['tp']}, false matches {retrieval['fp']}, "
            f"missed {retrieval['fn']}, correct silences {retrieval['tn']}"
        )
        for mismatch in findings["mismatches"]:
            print(f"    {mismatch['id']}: missed {mismatch['missed']}, false {mismatch['false']}")
        for entry in retrieval["false_matches"] + retrieval["missed"]:
            print(f"    {entry['id']}: guidance returned {entry['returned']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
