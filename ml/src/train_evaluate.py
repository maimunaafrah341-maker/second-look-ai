"""Train and evaluate lightweight SMS spam baselines, then save the selected model.

Usage, from the repository root (run ingest_sms_spam.py first):

    python ml/src/train_evaluate.py

Protocol:

- Exact duplicates are removed and near-duplicates are grouped (dataset_prep.py).
- Records are split by group into train, validation, and test.
- Every model is fitted on train only.
- Hyperparameters, the decision threshold, and the choice of model use validation only.
- The test split is scored once, at the end, with nothing tuned on it.

The saved artifact is the exact model whose test metrics are reported.
"""

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline, make_pipeline

from dataset_prep import (
    DEFAULT_GROUP_THRESHOLD,
    LABEL_TO_INT,
    SPLITS,
    assign_groups,
    deduplicate_exact,
    encode_labels,
    split_by_group,
)
from ingest_sms_spam import PROCESSED_CSV, REPO_ROOT, read_csv
from model_io import DEFAULT_MODEL_DIR, save_model

DEFAULT_SEED = 42
DEFAULT_MAX_FPR = 0.01
POSITIVE_LABEL = "spam"
PREPARED_CSV = PROCESSED_CSV.with_name("sms_spam_prepared.csv")
EVALUATION_FILE = "evaluation.json"


def candidate_models(seed: int) -> dict[str, list[tuple[dict, Pipeline]]]:
    """Model families, each with a small set of settings to compare on validation."""
    return {
        "majority_class": [({}, make_pipeline(DummyClassifier(strategy="prior")))],
        "word_tfidf_naive_bayes": [
            (
                {"alpha": alpha},
                make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), MultinomialNB(alpha=alpha)),
            )
            for alpha in (0.1, 0.5, 1.0)
        ],
        "char_tfidf_logistic_regression": [
            (
                {"C": c},
                make_pipeline(
                    TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, min_df=2),
                    LogisticRegression(C=c, class_weight="balanced", max_iter=2000, random_state=seed),
                ),
            )
            for c in (1.0, 10.0, 100.0)
        ],
    }


def spam_scores(pipeline: Pipeline, texts: list[str]) -> np.ndarray:
    return pipeline.predict_proba(texts)[:, LABEL_TO_INT[POSITIVE_LABEL]]


def select_threshold(labels: np.ndarray, scores: np.ndarray, max_fpr: float) -> float:
    """Lowest threshold whose false-positive rate on these examples is at most `max_fpr`.

    A message is predicted spam when its score is >= the threshold. If no observed
    score qualifies, the threshold is set just above the highest score, so nothing
    is predicted spam.
    """
    labels = np.asarray(labels)
    scores = np.asarray(scores, dtype=float)
    ham_scores = np.sort(scores[labels == 0])[::-1]
    allowed = int(np.floor(max_fpr * len(ham_scores)))
    if allowed >= len(ham_scores):
        return float(scores.min())
    # The threshold must sit above the first ham score that would exceed the allowance.
    qualifying = scores[scores > ham_scores[allowed]]
    if qualifying.size == 0:
        return float(np.nextafter(scores.max(), np.inf))
    return float(qualifying.min())


def compute_metrics(labels: np.ndarray, scores: np.ndarray, threshold: float) -> dict:
    labels = np.asarray(labels)
    predictions = (np.asarray(scores) >= threshold).astype(int)
    tn, fp, fn, tp = (int(value) for value in confusion_matrix(labels, predictions, labels=[0, 1]).ravel())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "confusion_matrix": {"true_ham": tn, "false_spam": fp, "missed_spam": fn, "true_spam": tp},
        "spam_precision": precision,
        "spam_recall": recall,
        "spam_f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "macro_f1": float(f1_score(labels, predictions, average="macro", zero_division=0)),
        "average_precision": float(average_precision_score(labels, scores)),
        "false_positive_rate": fp / (fp + tn) if fp + tn else 0.0,
        "accuracy": (tp + tn) / len(labels),
    }


def describe_split(labels: np.ndarray, groups: np.ndarray) -> dict:
    return {
        "records": int(len(labels)),
        "ham": int((labels == 0).sum()),
        "spam": int((labels == 1).sum()),
        "spam_share": float((labels == 1).mean()),
        "groups": int(len(set(groups.tolist()))),
    }


def write_prepared_csv(records, groups, splits, destination: Path) -> None:
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("id", "label", "text", "group", "split"))
        for record, group, split in zip(records, groups, splits):
            writer.writerow((record.id, record.label, record.text, group, split))


def run(source: Path, model_dir: Path, seed: int, group_threshold: float, max_fpr: float) -> dict:
    ingested = read_csv(source)
    records = deduplicate_exact(ingested)
    texts = [record.text for record in records]
    labels = encode_labels([record.label for record in records])

    group_index = assign_groups(texts, group_threshold)
    # Name each group after the id of its first record.
    groups = np.array([records[index].id for index in group_index])
    splits = np.array(split_by_group(labels, groups, seed))

    in_split = {name: splits == name for name in SPLITS}
    for a, b in (("train", "validation"), ("train", "test"), ("validation", "test")):
        shared = set(groups[in_split[a]].tolist()) & set(groups[in_split[b]].tolist())
        if shared:
            raise RuntimeError(f"{len(shared)} groups appear in both {a} and {b}.")

    def subset(name: str) -> tuple[list[str], np.ndarray]:
        mask = in_split[name]
        return [text for text, keep in zip(texts, mask) if keep], labels[mask]

    train_texts, train_labels = subset("train")
    validation_texts, validation_labels = subset("validation")
    test_texts, test_labels = subset("test")

    group_sizes = Counter(groups.tolist())
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": seed,
        "max_fpr_target": max_fpr,
        "dataset": {
            "source_file": source.relative_to(REPO_ROOT).as_posix() if source.is_relative_to(REPO_ROOT) else str(source),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "ingested_records": len(ingested),
            "exact_duplicates_removed": len(ingested) - len(records),
            "records_after_exact_deduplication": len(records),
            "group_threshold": group_threshold,
            "groups": len(group_sizes),
            "groups_with_more_than_one_record": sum(1 for size in group_sizes.values() if size > 1),
            "records_in_those_groups": sum(size for size in group_sizes.values() if size > 1),
            "largest_group": max(group_sizes.values()),
        },
        "splits": {name: describe_split(labels[in_split[name]], groups[in_split[name]]) for name in SPLITS},
        "models": {},
    }

    fitted = {}
    for family, candidates in candidate_models(seed).items():
        tried = []
        best = None
        for params, pipeline in candidates:
            pipeline.fit(train_texts, train_labels)
            validation_scores = spam_scores(pipeline, validation_texts)
            validation_ap = float(average_precision_score(validation_labels, validation_scores))
            tried.append({"params": params, "validation_average_precision": validation_ap})
            if best is None or validation_ap > best[0]:
                best = (validation_ap, params, pipeline, validation_scores)

        _, params, pipeline, validation_scores = best
        threshold = select_threshold(validation_labels, validation_scores, max_fpr)
        fitted[family] = (pipeline, threshold)
        report["models"][family] = {
            "selected_params": params,
            "settings_tried": tried,
            "threshold": threshold,
            "validation": compute_metrics(validation_labels, validation_scores, threshold),
            "test": compute_metrics(test_labels, spam_scores(pipeline, test_texts), threshold),
        }

    selected = max(
        report["models"], key=lambda family: report["models"][family]["validation"]["average_precision"]
    )
    report["selected_model"] = selected
    report["selection_rule"] = "highest average precision on the validation split"

    pipeline, threshold = fitted[selected]
    metadata = save_model(
        pipeline,
        {
            "model_name": selected,
            "params": report["models"][selected]["selected_params"],
            "created_at": report["created_at"],
            "label_mapping": LABEL_TO_INT,
            "positive_label": POSITIVE_LABEL,
            "threshold": threshold,
            "threshold_rule": f"lowest threshold with validation false-positive rate <= {max_fpr}",
            "trained_on": "train split only",
            "seed": seed,
            "group_threshold": group_threshold,
            "dataset": "UCI SMS Spam Collection (English SMS, 2011); labels are ham/spam, not fraud",
            "dataset_sha256": report["dataset"]["source_sha256"],
            "test_metrics": report["models"][selected]["test"],
        },
        model_dir,
    )
    report["artifact"] = {"directory": str(model_dir), "model_sha256": metadata["model_sha256"]}

    (model_dir / EVALUATION_FILE).write_text(json.dumps(report, indent=2), encoding="utf-8")
    if source == PROCESSED_CSV:
        write_prepared_csv(records, groups.tolist(), splits.tolist(), PREPARED_CSV)
    return report


def print_report(report: dict) -> None:
    dataset = report["dataset"]
    print(f"Ingested records: {dataset['ingested_records']}")
    print(f"Exact duplicates removed: {dataset['exact_duplicates_removed']}")
    print(f"Records after exact deduplication: {dataset['records_after_exact_deduplication']}")
    print(
        f"Near-duplicate groups (threshold {dataset['group_threshold']}): {dataset['groups']} groups, "
        f"{dataset['groups_with_more_than_one_record']} with more than one record covering "
        f"{dataset['records_in_those_groups']} records, largest {dataset['largest_group']}"
    )
    for name, split in report["splits"].items():
        print(
            f"{name:<10} records={split['records']} ham={split['ham']} spam={split['spam']} "
            f"spam_share={split['spam_share']:.3f} groups={split['groups']}"
        )
    for family, result in report["models"].items():
        print(f"\n{family} params={result['selected_params']} threshold={result['threshold']:.4f}")
        for split in ("validation", "test"):
            m = result[split]
            cm = m["confusion_matrix"]
            print(
                f"  {split:<10} TN={cm['true_ham']} FP={cm['false_spam']} FN={cm['missed_spam']} TP={cm['true_spam']} "
                f"precision={m['spam_precision']:.4f} recall={m['spam_recall']:.4f} f1={m['spam_f1']:.4f} "
                f"macro_f1={m['macro_f1']:.4f} AP={m['average_precision']:.4f} "
                f"FPR={m['false_positive_rate']:.4f} accuracy={m['accuracy']:.4f}"
            )
    print(f"\nSelected model: {report['selected_model']} ({report['selection_rule']})")
    print(f"Saved to: {report['artifact']['directory']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--group-threshold",
        type=float,
        default=DEFAULT_GROUP_THRESHOLD,
        help="character 3-gram cosine similarity at which two messages are grouped",
    )
    parser.add_argument(
        "--max-fpr",
        type=float,
        default=DEFAULT_MAX_FPR,
        help="false-positive rate allowed on validation when choosing the threshold",
    )
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    if not PROCESSED_CSV.is_file():
        print(f"ERROR: {PROCESSED_CSV} not found. Run: python ml/src/ingest_sms_spam.py", file=sys.stderr)
        return 1

    print_report(run(PROCESSED_CSV, args.model_dir, args.seed, args.group_threshold, args.max_fpr))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
