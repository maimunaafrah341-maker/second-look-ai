"""Tests for the auxiliary classifier.

Unit tests use small fixture models trained on made-up text in a temporary folder.
The messages are test fixtures, not dataset records. Tests that need the real,
committed artifact say so in their names.
"""

import hashlib
import json
import logging
import subprocess
import sys
from pathlib import Path

import joblib
import pytest
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from app.classifier import (
    DEFAULT_MODEL_DIR,
    METADATA_FILE,
    MODEL_DIR_ENV,
    MODEL_FILE,
    NOT_APPLICABLE,
    NOT_SPAM_LIKE,
    OK,
    SPAM_LIKE,
    UNAVAILABLE,
    Classifier,
    model_directory,
    mostly_non_latin,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SPAM_TEXTS = [f"winner claim free prize cash now txt {n}" for n in range(12)]
HAM_TEXTS = [f"see you at lunch tomorrow with mum {n}" for n in range(12)]


def train_fixture_pipeline():
    texts = SPAM_TEXTS + HAM_TEXTS
    labels = [1] * len(SPAM_TEXTS) + [0] * len(HAM_TEXTS)
    return make_pipeline(TfidfVectorizer(), LogisticRegression(random_state=0)).fit(texts, labels)


def write_artifact(directory: Path, **overrides) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    joblib.dump(train_fixture_pipeline(), directory / MODEL_FILE)
    metadata = {
        "model_name": "fixture_model",
        "model_sha256": hashlib.sha256((directory / MODEL_FILE).read_bytes()).hexdigest(),
        "sklearn_version": sklearn.__version__,
        "label_mapping": {"ham": 0, "spam": 1},
        "positive_label": "spam",
        "threshold": 0.5,
    }
    metadata.update(overrides)
    (directory / METADATA_FILE).write_text(json.dumps(metadata), encoding="utf-8")
    return directory


class StubPipeline:
    """Returns a fixed score, to test labels at exact threshold values."""

    classes_ = [0, 1]

    def __init__(self, score):
        self.score = score

    def predict_proba(self, texts):
        return [[1 - self.score, self.score] for _ in texts]


def stub_classifier(score: float, threshold: float = 0.5) -> Classifier:
    metadata = {"model_name": "stub", "model_sha256": "0" * 64, "threshold": threshold}
    return Classifier(StubPipeline(score), metadata, positive_column=1)


# --- Loading ---------------------------------------------------------------------


def test_fixture_model_loads_and_classifies(tmp_path):
    classifier = Classifier.load(write_artifact(tmp_path))

    assert classifier.available
    assert classifier.classify("winner claim free prize cash now").label == SPAM_LIKE
    assert classifier.classify("see you at lunch tomorrow with mum").label == NOT_SPAM_LIKE
    assert classifier.model_info()["name"] == "fixture_model"


def test_model_saved_by_training_code_loads_in_the_api(tmp_path):
    # Contract between ml/src/model_io.py (writer) and the API loader (reader).
    from model_io import save_model

    save_model(
        train_fixture_pipeline(),
        {"model_name": "contract", "label_mapping": {"ham": 0, "spam": 1}, "positive_label": "spam", "threshold": 0.5},
        tmp_path,
    )

    classifier = Classifier.load(tmp_path)

    assert classifier.available
    assert classifier.classify("winner claim free prize cash now").status == OK


def test_missing_model_is_unavailable(tmp_path):
    classifier = Classifier.load(tmp_path / "absent")

    assert not classifier.available
    assert classifier.classify("anything") == classifier.classify("anything")
    assert classifier.classify("anything").status == UNAVAILABLE
    assert classifier.classify("anything").label is None


@pytest.mark.parametrize(
    "metadata_text",
    [
        "not json",
        "[]",
        '{"threshold": 0.5}',
    ],
)
def test_invalid_metadata_is_unavailable(tmp_path, metadata_text):
    write_artifact(tmp_path)
    (tmp_path / METADATA_FILE).write_text(metadata_text, encoding="utf-8")

    assert Classifier.load(tmp_path).classify("hello").status == UNAVAILABLE


@pytest.mark.parametrize(
    "overrides",
    [
        {"threshold": 1.5},
        {"threshold": 0},
        {"threshold": "0.5"},
        {"threshold": True},
        {"positive_label": "fraud"},
        {"label_mapping": "spam"},
    ],
)
def test_metadata_with_bad_values_is_unavailable(tmp_path, overrides):
    assert Classifier.load(write_artifact(tmp_path, **overrides)).classify("hello").status == UNAVAILABLE


def test_checksum_mismatch_is_unavailable(tmp_path):
    write_artifact(tmp_path)
    with (tmp_path / MODEL_FILE).open("ab") as handle:
        handle.write(b"tampered")

    assert not Classifier.load(tmp_path).available


def test_wrong_checksum_in_metadata_is_unavailable(tmp_path):
    assert not Classifier.load(write_artifact(tmp_path, model_sha256="f" * 64)).available


def test_scikit_learn_version_mismatch_is_unavailable(tmp_path):
    assert not Classifier.load(write_artifact(tmp_path, sklearn_version="0.0.1")).available


def test_corrupt_model_file_with_matching_checksum_is_unavailable(tmp_path):
    write_artifact(tmp_path)
    (tmp_path / MODEL_FILE).write_bytes(b"not a model")
    metadata = json.loads((tmp_path / METADATA_FILE).read_text(encoding="utf-8"))
    metadata["model_sha256"] = hashlib.sha256(b"not a model").hexdigest()
    (tmp_path / METADATA_FILE).write_text(json.dumps(metadata), encoding="utf-8")

    assert not Classifier.load(tmp_path).available


def test_model_directory_defaults_to_the_backend_path_and_accepts_an_override(monkeypatch, tmp_path):
    monkeypatch.delenv(MODEL_DIR_ENV, raising=False)
    assert model_directory() == DEFAULT_MODEL_DIR
    assert DEFAULT_MODEL_DIR.is_absolute()

    monkeypatch.setenv(MODEL_DIR_ENV, str(write_artifact(tmp_path)))
    assert model_directory() == tmp_path.resolve()
    assert Classifier.load().model_info()["name"] == "fixture_model"


def test_default_path_does_not_depend_on_the_working_directory(monkeypatch, tmp_path):
    monkeypatch.delenv(MODEL_DIR_ENV, raising=False)
    monkeypatch.chdir(tmp_path)

    assert model_directory() == DEFAULT_MODEL_DIR


# --- Labels ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("score", "label"),
    [(0.0, NOT_SPAM_LIKE), (0.4999, NOT_SPAM_LIKE), (0.5, SPAM_LIKE), (0.5001, SPAM_LIKE), (1.0, SPAM_LIKE)],
)
def test_label_at_the_threshold_boundary(score, label):
    assert stub_classifier(score, threshold=0.5).classify("some english text").label == label


def test_classification_is_deterministic(tmp_path):
    classifier = Classifier.load(write_artifact(tmp_path))
    messages = ["winner claim free prize", "lunch tomorrow", "mixed winner lunch"]

    assert [classifier.classify(m) for m in messages] == [classifier.classify(m) for m in messages]


def test_a_failing_or_invalid_prediction_is_unavailable():
    class Broken(StubPipeline):
        def predict_proba(self, texts):
            raise RuntimeError("boom")

    broken = Classifier(Broken(0.0), {"model_name": "x", "model_sha256": "0", "threshold": 0.5})
    assert broken.classify("hello there").status == UNAVAILABLE
    assert stub_classifier(float("nan")).classify("hello there").status == UNAVAILABLE


# --- Language handling -------------------------------------------------------------


@pytest.mark.parametrize(
    ("message", "expected_status"),
    [
        ("Your account will be blocked. Update KYC now.", OK),
        # Romanised Hindi (Hinglish) is Latin script, so it is classified.
        ("bhai OTP aaya kya? jaldi bata de, paise bhejne hai", OK),
        ("Aapka account band ho jayega, turant KYC update karein", OK),
        # Mostly Devanagari Hindi is not classified.
        ("आपका खाता बंद हो जाएगा। तुरंत अपना ओटीपी बताएं।", NOT_APPLICABLE),
        # A Devanagari message with a few English words is still mostly Devanagari.
        ("आपका SBI खाता बंद हो जाएगा, तुरंत अपना ओटीपी बताएं", NOT_APPLICABLE),
        # An English message with one Hindi word is still mostly Latin.
        ("Your KYC is pending, please update today. धन्यवाद", OK),
        # Bengali and Urdu scripts are not classified either.
        ("আপনার অ্যাকাউন্ট বন্ধ হয়ে যাবে", NOT_APPLICABLE),
        ("آپ کا اکاؤنٹ بند ہو جائے گا", NOT_APPLICABLE),
        # Too few letters to judge: classified, to stay conservative.
        ("Rs 500 ₹ 12345 !!!", OK),
        ("🙂🙂 ok", OK),
    ],
)
def test_language_handling(message, expected_status):
    assert stub_classifier(0.9).classify(message).status == expected_status


def test_script_check_ignores_digits_punctuation_and_emoji():
    assert not mostly_non_latin("OTP 482913 !!! 🙂🙂🙂 ₹₹₹")
    assert mostly_non_latin("ओटीपी 482913 बताएं !!!")


def test_not_applicable_result_still_names_the_model():
    result = stub_classifier(0.9).classify("आपका खाता बंद हो जाएगा। तुरंत अपना ओटीपी बताएं।")

    assert result.label is None
    assert result.model["name"] == "stub"


# --- The real, committed artifact ----------------------------------------------------


def test_real_artifact_matches_its_recorded_checksum():
    metadata = json.loads((DEFAULT_MODEL_DIR / METADATA_FILE).read_text(encoding="utf-8"))
    actual = hashlib.sha256((DEFAULT_MODEL_DIR / MODEL_FILE).read_bytes()).hexdigest()

    assert actual == metadata["model_sha256"]
    assert actual == "bd1079ed0b0ac41ca0dead4a1c113e963f40a160301f3bd543558192b2f62561"
    assert metadata["sklearn_version"] == sklearn.__version__
    assert metadata["threshold"] == pytest.approx(0.11158484149077182)


def test_real_artifact_rates_a_genuine_bank_alert_spam_like():
    # Documented false positive: a genuine Indian bank debit alert is rated spam-like.
    # Kept as a regression case so any change in this behaviour is noticed.
    classifier = Classifier.load(DEFAULT_MODEL_DIR)

    result = classifier.classify("Rs 2,000 debited from A/c XX1234 on 03-Oct. Not you? Call your bank.")

    assert result.status == OK
    assert result.label == SPAM_LIKE


# --- Safety of the running service --------------------------------------------------


def test_api_import_does_not_load_training_code():
    code = (
        "import sys; sys.path.insert(0, 'backend'); import app.main; "
        "names = ['train_evaluate', 'dataset_prep', 'ingest_sms_spam', 'model_io', 'torch', 'pandas']; "
        "print([n for n in names if n in sys.modules])"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=REPO_ROOT, capture_output=True, text=True, timeout=120
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "[]"


def test_load_failures_are_logged_without_message_text(tmp_path, caplog):
    caplog.set_level(logging.DEBUG)

    classifier = Classifier.load(tmp_path / "absent")
    classifier.classify("SECRET-MARKER my OTP is 482913")

    assert "Auxiliary classifier unavailable" in caplog.text
    assert "SECRET-MARKER" not in caplog.text
