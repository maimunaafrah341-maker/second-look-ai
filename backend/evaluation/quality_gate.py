"""Quality gate: re-measure Second Look's evaluations and fail if any is worse than recorded.

Usage, from the repository root:

    python backend/evaluation/quality_gate.py
    python backend/evaluation/quality_gate.py --require-classifier --report quality-report.md
    python backend/evaluation/quality_gate.py --update-baseline

The pipeline runs this on every merge request. It measures four things and compares each
with quality_baseline.json:

- agent check: on guard_eval.json, every verdict must be rejected (no tolerance), and the
  share of real model summaries allowed through must not fall. The second number stops
  the check being "fixed" by making it reject everything.
- guidance retrieval: precision and recall on the hand-written retrieval set, per split.
- warning signs: on the Telugu, Urdu and Bengali set, the service must still find no
  false warning signs, since it cannot read those languages.
- classifier: precision, recall, F1 and false-positive rate on the held-out test split of
  the UCI SMS Spam Collection, rebuilt exactly as ml/src/train_evaluate.py builds it. This
  needs the dataset (python ml/src/ingest_sms_spam.py). Without it the check is skipped,
  unless --require-classifier is given.

A number may only get better. Updating the baseline is a deliberate, reviewed change:
run with --update-baseline and commit quality_baseline.json in the same merge request.
These sets are small and written by the project; the gate catches regressions, it does
not prove real-world accuracy.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "ml" / "src")]

from app.agent import check_summary  # noqa: E402
from app.guidance import GuidanceIndex  # noqa: E402
from app.warning_signs import detect_warning_signs  # noqa: E402
from evaluation import evaluate_multilingual, evaluate_retrieval  # noqa: E402

HERE = Path(__file__).resolve().parent
BASELINE = HERE / "quality_baseline.json"
GUARD_SET = HERE / "guard_eval.json"

HIGHER = "higher"  # the metric may not go down
LOWER = "lower"  # the metric may not go up
EXACT = "exact"  # the metric must equal the baseline


def measure_guard(path: Path = GUARD_SET) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    messages = data["messages"]

    def rejected(item: dict) -> bool:
        message = messages[item["message"]]
        return check_summary(item["text"], message, bool(detect_warning_signs(message))) is not None

    verdicts = data["verdict"]
    honest = data["honest"]
    missed = [item["text"] for item in verdicts if not rejected(item)]
    blocked = [item["text"] for item in honest if rejected(item)]
    return {
        "metrics": {
            "verdicts_shown": len(missed),
            "honest_allowed_rate": round((len(honest) - len(blocked)) / len(honest), 4),
        },
        "details": {"verdicts": len(verdicts), "honest": len(honest), "verdicts_shown": missed, "honest_blocked": blocked},
    }


def measure_retrieval(index: GuidanceIndex) -> dict:
    items = evaluate_retrieval.load_items()
    metrics, details = {}, {}
    for split in ("development", "check"):
        result = evaluate_retrieval.evaluate(index, [item for item in items if item["split"] == split])
        metrics[f"{split}_precision"] = round(result["precision"], 4)
        metrics[f"{split}_recall"] = round(result["recall"], 4)
        details[split] = {key: result[key] for key in ("tp", "fp", "fn", "tn")}
    return {"metrics": metrics, "details": details}


def measure_unsupported_languages() -> dict:
    items = evaluate_multilingual.load_items()
    result = evaluate_multilingual.evaluate_findings(items)
    return {"metrics": {"false_warning_signs": result["fp"]}, "details": {"messages": result["items"]}}


def measure_classifier() -> dict | None:
    """Score the committed model on the held-out test split, or None without the dataset."""
    from app.classifier import model_directory, read_artifact
    from dataset_prep import assign_groups, deduplicate_exact, encode_labels, split_by_group
    from ingest_sms_spam import PROCESSED_CSV, read_csv
    from train_evaluate import compute_metrics

    if not PROCESSED_CSV.is_file():
        return None
    pipeline, metadata, positive_column = read_artifact(model_directory())
    records = deduplicate_exact(read_csv(PROCESSED_CSV))
    texts = [record.text for record in records]
    labels = encode_labels([record.label for record in records])
    group_index = assign_groups(texts, metadata["group_threshold"])
    groups = [records[index].id for index in group_index]
    splits = split_by_group(labels, groups, metadata["seed"])
    test = [position for position, split in enumerate(splits) if split == "test"]
    scores = pipeline.predict_proba([texts[position] for position in test])[:, positive_column]
    result = compute_metrics(labels[test], scores, metadata["threshold"])
    return {
        "metrics": {
            "spam_precision": round(result["spam_precision"], 4),
            "spam_recall": round(result["spam_recall"], 4),
            "spam_f1": round(result["spam_f1"], 4),
            "false_positive_rate": round(result["false_positive_rate"], 4),
        },
        "details": {"test_messages": len(test), "confusion_matrix": result["confusion_matrix"]},
    }


def measure_all() -> dict:
    index = GuidanceIndex.from_file()
    return {
        "agent_check": measure_guard(),
        "guidance_retrieval": measure_retrieval(index),
        "unsupported_languages": measure_unsupported_languages(),
        "classifier": measure_classifier(),
    }


def compare(results: dict, baseline: dict, require_classifier: bool) -> list[dict]:
    """One row per metric: its baseline, the value now, and whether it passed."""
    rows = []
    for section, rules in baseline["metrics"].items():
        measured = results.get(section)
        for name, rule in rules.items():
            row = {"section": section, "metric": name, "baseline": rule["value"], "direction": rule["direction"]}
            if measured is None:
                row.update(now=None, passed=not require_classifier, note="skipped: dataset not available")
            else:
                now = measured["metrics"][name]
                tolerance = rule.get("tolerance", 0)
                if rule["direction"] == HIGHER:
                    passed = now >= rule["value"] - tolerance
                elif rule["direction"] == LOWER:
                    passed = now <= rule["value"] + tolerance
                else:
                    passed = now == rule["value"]
                row.update(now=now, passed=passed, note="")
            rows.append(row)
    return rows


def markdown(rows: list[dict], results: dict) -> str:
    failed = [row for row in rows if not row["passed"]]
    lines = [
        "## Second Look quality gate",
        "",
        f"**{'FAILED' if failed else 'Passed'}**: {len(rows) - len(failed)} of {len(rows)} checks passed.",
        "",
        "| Area | Metric | Baseline | Now | Rule | Result |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    rules = {HIGHER: "may not fall", LOWER: "may not rise", EXACT: "must not change"}
    for row in rows:
        now = "—" if row["now"] is None else row["now"]
        result = "pass" if row["passed"] else "**FAIL**"
        if row["note"]:
            result += f" ({row['note']})"
        lines.append(f"| {row['section']} | {row['metric']} | {row['baseline']} | {now} | {rules[row['direction']]} | {result} |")
    guard = results["agent_check"]["details"]
    for title, texts in (("Verdicts the check let through", guard["verdicts_shown"]), ("Honest summaries the check blocked", guard["honest_blocked"])):
        if texts:
            lines += ["", f"**{title}:**", *[f"- {text}" for text in texts]]
    return "\n".join(lines) + "\n"


def update_baseline(results: dict, path: Path = BASELINE) -> None:
    baseline = json.loads(path.read_text(encoding="utf-8"))
    for section, rules in baseline["metrics"].items():
        if results.get(section) is None:
            continue
        for name, rule in rules.items():
            # A fixed rule, such as "no verdict gets through", is a requirement, not a measurement.
            if not rule.get("fixed"):
                rule["value"] = results[section]["metrics"][name]
    path.write_text(json.dumps(baseline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--require-classifier", action="store_true", help="Fail if the dataset is missing")
    parser.add_argument("--report", type=Path, help="Write a Markdown report here")
    parser.add_argument("--json", type=Path, help="Write the full results here")
    parser.add_argument("--update-baseline", action="store_true", help="Record the current numbers as the baseline")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    results = measure_all()
    if args.update_baseline:
        update_baseline(results)
        print(f"Baseline updated: {BASELINE.relative_to(ROOT)}")
    rows = compare(results, json.loads(BASELINE.read_text(encoding="utf-8")), args.require_classifier)
    report = markdown(rows, results)
    print(report)
    if args.report:
        args.report.write_text(report, encoding="utf-8")
    if args.json:
        args.json.write_text(json.dumps({"rows": rows, "results": results}, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0 if all(row["passed"] for row in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
