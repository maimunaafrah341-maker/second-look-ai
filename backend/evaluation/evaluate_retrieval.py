"""Check guidance retrieval against a small hand-written labelled set.

Usage, from the repository root:

    python backend/evaluation/evaluate_retrieval.py

The set is tiny and written by the project, so these numbers describe behaviour
on these examples only. They are not an estimate of real-world performance.

Counting rules, per message:

- correct match (TP): a result was expected and the first result is from an expected source.
- missed (FN): a result was expected and the first result is absent or from another source.
- false match (FP): the first result is from a source that was not expected. This includes
  any result for a message where nothing was expected.
- correct silence (TN): nothing was expected and nothing was returned.

Ambiguous items are listed but left out of the counts.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.guidance import GuidanceIndex  # noqa: E402

EVAL_SET = Path(__file__).resolve().parent / "retrieval_eval.json"
CATEGORIES = ("malicious", "benign_security_awareness", "unrelated", "ambiguous")


def load_items(path: Path = EVAL_SET) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["items"]


def evaluate(index: GuidanceIndex, items: list[dict]) -> dict:
    counts = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    false_matches, missed, ambiguous = [], [], []

    for item in items:
        matches = index.search(item["message"])
        first = matches[0].source.id if matches else None
        if item["category"] == "ambiguous":
            ambiguous.append({"id": item["id"], "returned": first})
            continue

        expected = item["expected_sources"]
        if expected and first in expected:
            counts["tp"] += 1
        else:
            if expected:
                counts["fn"] += 1
                missed.append({"id": item["id"], "returned": first})
            if first is not None:
                counts["fp"] += 1
                false_matches.append({"id": item["id"], "returned": first})
            elif not expected:
                counts["tn"] += 1

    tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
    return {
        "scored_items": len(items) - len(ambiguous),
        **counts,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "false_matches": false_matches,
        "missed": missed,
        "ambiguous": ambiguous,
    }


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    index = GuidanceIndex.from_file()
    items = load_items()
    for split in sorted({item["split"] for item in items}):
        result = evaluate(index, [item for item in items if item["split"] == split])
        print(f"\n{split}: {result['scored_items']} scored items, {len(result['ambiguous'])} ambiguous")
        print(
            f"  correct matches {result['tp']}, false matches {result['fp']}, "
            f"missed {result['fn']}, correct silences {result['tn']}"
        )
        for name in ("precision", "recall"):
            value = result[name]
            print(f"  {name}: " + ("n/a" if value is None else f"{value:.3f}"))
        for name in ("false_matches", "missed", "ambiguous"):
            for entry in result[name]:
                print(f"  {name}: {entry['id']} -> {entry['returned']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
