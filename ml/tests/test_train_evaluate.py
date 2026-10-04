"""Tests for metrics, threshold selection, model saving and loading, and the full run.

All messages here are small fixtures generated for these tests. They are not
dataset records, and nothing here reads or writes the real dataset or model.
"""

import csv
import json
import random

import numpy as np
import pytest

from model_io import METADATA_FILE, MODEL_FILE, ModelNotAvailableError, load_model, save_model
from train_evaluate import candidate_models, compute_metrics, run, select_threshold, spam_scores

HAM_WORDS = (
    "lunch meeting home dinner tomorrow thanks sorry class train bus mum dad office "
    "weekend movie library coffee later tonight morning lecture garden football"
).split()
SPAM_WORDS = (
    "winner prize claim urgent cash award free voucher ringtone subscription reply "
    "guaranteed bonus offer mobile credit txt stop landline jackpot holiday entry"
).split()


def fixture_rows(count_per_label: int = 30) -> list[tuple[int, str, str]]:
    rng = random.Random(0)
    rows = []
    for index in range(count_per_label):
        rows.append((2 * index + 1, "ham", " ".join(rng.sample(HAM_WORDS, 6))))
        rows.append((2 * index + 2, "spam", " ".join(rng.sample(SPAM_WORDS, 6))))
    return rows


def test_compute_metrics_matches_hand_calculation():
    labels = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    scores = np.array([0.1, 0.2, 0.3, 0.8, 0.4, 0.6, 0.7, 0.9])

    metrics = compute_metrics(labels, scores, threshold=0.5)

    assert metrics["confusion_matrix"] == {
        "true_ham": 3,
        "false_spam": 1,
        "missed_spam": 1,
        "true_spam": 3,
    }
    assert metrics["spam_precision"] == pytest.approx(0.75)
    assert metrics["spam_recall"] == pytest.approx(0.75)
    assert metrics["spam_f1"] == pytest.approx(0.75)
    assert metrics["macro_f1"] == pytest.approx(0.75)
    assert metrics["false_positive_rate"] == pytest.approx(0.25)
    assert metrics["accuracy"] == pytest.approx(0.75)
    # Precision at each spam, ranked by score: 1/1, 2/3, 3/4, 4/5.
    assert metrics["average_precision"] == pytest.approx((1 + 2 / 3 + 3 / 4 + 4 / 5) / 4)


def test_compute_metrics_when_nothing_is_predicted_spam():
    metrics = compute_metrics(np.array([0, 0, 1]), np.array([0.1, 0.1, 0.1]), threshold=0.5)

    assert metrics["spam_precision"] == 0.0
    assert metrics["spam_recall"] == 0.0
    assert metrics["spam_f1"] == 0.0
    assert metrics["false_positive_rate"] == 0.0


def test_select_threshold_respects_false_positive_allowance():
    labels = np.array([0] * 100 + [1] * 5)
    ham_scores = np.linspace(0.0, 0.5, 100)
    spam = np.array([0.45, 0.6, 0.7, 0.8, 0.9])
    scores = np.concatenate([ham_scores, spam])

    threshold = select_threshold(labels, scores, max_fpr=0.02)

    false_positives = int((ham_scores >= threshold).sum())
    assert false_positives == 2
    # A lower threshold would let a third ham message through.
    assert threshold == pytest.approx(np.sort(ham_scores)[-2])


def test_select_threshold_with_zero_allowance_sits_above_every_ham_score():
    labels = np.array([0, 0, 0, 1, 1])
    scores = np.array([0.2, 0.4, 0.7, 0.6, 0.9])

    threshold = select_threshold(labels, scores, max_fpr=0.0)

    assert threshold == 0.9
    assert (scores[labels == 0] >= threshold).sum() == 0


def test_select_threshold_when_a_ham_message_has_the_top_score():
    labels = np.array([0, 0, 1])
    scores = np.array([0.9, 0.1, 0.5])

    threshold = select_threshold(labels, scores, max_fpr=0.0)

    assert (scores >= threshold).sum() == 0


def test_candidate_models_cover_the_three_baselines():
    assert list(candidate_models(seed=0)) == [
        "majority_class",
        "word_tfidf_naive_bayes",
        "char_tfidf_logistic_regression",
    ]


def train_small_pipeline():
    rows = fixture_rows()
    texts = [text for _, _, text in rows]
    labels = np.array([int(label == "spam") for _, label, _ in rows])
    _, pipeline = candidate_models(seed=0)["char_tfidf_logistic_regression"][0]
    return pipeline.fit(texts, labels), texts


def base_metadata() -> dict:
    return {"label_mapping": {"ham": 0, "spam": 1}, "positive_label": "spam", "threshold": 0.5}


def test_model_save_and_load_round_trip(tmp_path):
    pipeline, texts = train_small_pipeline()

    saved = save_model(pipeline, base_metadata(), tmp_path)
    loaded, metadata = load_model(tmp_path)

    assert metadata == saved
    assert metadata["label_mapping"] == {"ham": 0, "spam": 1}
    assert metadata["threshold"] == 0.5
    assert np.allclose(spam_scores(loaded, texts), spam_scores(pipeline, texts))
    assert not list(tmp_path.glob("*.part"))


def test_load_model_fails_safely_when_artifact_is_missing(tmp_path):
    with pytest.raises(ModelNotAvailableError, match="No trained model"):
        load_model(tmp_path)


def test_load_model_rejects_a_modified_model_file(tmp_path):
    pipeline, _ = train_small_pipeline()
    save_model(pipeline, base_metadata(), tmp_path)
    with (tmp_path / MODEL_FILE).open("ab") as handle:
        handle.write(b"tampered")

    with pytest.raises(ModelNotAvailableError, match="checksum"):
        load_model(tmp_path)


def test_load_model_rejects_a_different_sklearn_version(tmp_path):
    pipeline, _ = train_small_pipeline()
    save_model(pipeline, base_metadata(), tmp_path)
    metadata_path = tmp_path / METADATA_FILE
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["sklearn_version"] = "0.0.0"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(ModelNotAvailableError, match="scikit-learn"):
        load_model(tmp_path)


def test_load_model_rejects_incomplete_or_invalid_metadata(tmp_path):
    pipeline, _ = train_small_pipeline()
    save_model(pipeline, base_metadata(), tmp_path)
    metadata_path = tmp_path / METADATA_FILE

    metadata_path.write_text('{"threshold": 0.5}', encoding="utf-8")
    with pytest.raises(ModelNotAvailableError, match="missing fields"):
        load_model(tmp_path)

    metadata_path.write_text("not json", encoding="utf-8")
    with pytest.raises(ModelNotAvailableError, match="not valid JSON"):
        load_model(tmp_path)


def test_full_run_on_fixture_data_keeps_groups_apart_and_saves_a_loadable_model(tmp_path):
    rows = fixture_rows()
    # Add exact duplicates, which must be removed before splitting.
    rows += [(1000 + index, label, text) for index, (_, label, text) in enumerate(rows[:6])]
    source = tmp_path / "fixture.csv"
    with source.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("id", "label", "text"))
        writer.writerows(rows)
    model_dir = tmp_path / "model"

    report = run(source, model_dir, seed=42, group_threshold=0.8, max_fpr=0.01)

    assert report["dataset"]["ingested_records"] == 66
    assert report["dataset"]["exact_duplicates_removed"] == 6
    assert sum(split["records"] for split in report["splits"].values()) == 60
    assert sum(split["groups"] for split in report["splits"].values()) == report["dataset"]["groups"]
    assert set(report["models"]) == set(candidate_models(seed=42))
    for result in report["models"].values():
        assert sum(result["test"]["confusion_matrix"].values()) == report["splits"]["test"]["records"]

    _, metadata = load_model(model_dir)
    assert metadata["model_name"] == report["selected_model"]
    assert metadata["test_metrics"] == report["models"][report["selected_model"]]["test"]
    assert (model_dir / "evaluation.json").is_file()
