"""Auxiliary spam-likeness classifier.

The model was trained on the UCI SMS Spam Collection: English SMS from the UK and
Singapore, around 2011, labelled spam or ham. It is not an Indian fraud classifier.
Its label is an auxiliary signal only. It never changes the warning-sign findings or
the official guidance, and it never produces a verdict.

The artifact is checked the same way as ml/src/model_io.py checks it (required files,
required metadata, matching scikit-learn version, matching checksum) before it is
loaded. Training code is not imported here. Only the project's own artifact is ever
loaded, from a path set by the code or by the operator, never from a request.
"""

import hashlib
import json
import logging
import math
import os
import unicodedata
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_MODEL_DIR = Path(__file__).resolve().parent / "data" / "classifier"
MODEL_DIR_ENV = "SECOND_LOOK_MODEL_DIR"
MODEL_FILE = "model.joblib"
METADATA_FILE = "metadata.json"
REQUIRED_METADATA = ("model_sha256", "sklearn_version", "label_mapping", "positive_label", "threshold")
TRAINING_DATA = "UCI SMS Spam Collection: English SMS from the UK and Singapore, around 2011"

OK = "ok"
UNAVAILABLE = "unavailable"
NOT_APPLICABLE = "not_applicable"
SPAM_LIKE = "spam_like"
NOT_SPAM_LIKE = "not_spam_like"

# The model is not run on a message that clearly is not written in the Latin alphabet,
# or whose estimated language (app/language.py) is not English. "mixed" is included:
# the estimate gives "en" only when it can tell the message is mainly English. "unknown"
# is included too: a message with no letters to judge (only digits, emoji, an amount, or
# a link) is not English SMS text, and the training data has almost no such messages.
MIN_LETTERS_FOR_SCRIPT_CHECK = 4
MIN_LATIN_SHARE = 0.5
NOT_ENGLISH_LANGUAGES = frozenset({"hi", "hi-Latn", "te", "ur", "bn", "mixed", "unknown"})


class ModelUnavailable(Exception):
    """The artifact is missing, incomplete, or unsafe to load."""


@dataclass(frozen=True)
class ClassifierResult:
    status: str
    label: str | None
    model: dict | None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model_directory() -> Path:
    override = os.environ.get(MODEL_DIR_ENV)
    return Path(override).resolve() if override else DEFAULT_MODEL_DIR


def read_artifact(directory: Path):
    """Check the artifact, then load it.

    Returns (pipeline, metadata, index of the positive class) or raises ModelUnavailable.
    """
    model_path = directory / MODEL_FILE
    metadata_path = directory / METADATA_FILE
    if not model_path.is_file() or not metadata_path.is_file():
        raise ModelUnavailable(f"no model files in {directory}")

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        raise ModelUnavailable(f"{METADATA_FILE} is not valid JSON") from None
    if not isinstance(metadata, dict):
        raise ModelUnavailable(f"{METADATA_FILE} must be a JSON object")
    missing = [key for key in REQUIRED_METADATA if key not in metadata]
    if missing:
        raise ModelUnavailable(f"{METADATA_FILE} is missing fields: {missing}")

    mapping, positive, threshold = metadata["label_mapping"], metadata["positive_label"], metadata["threshold"]
    if not isinstance(mapping, dict) or positive not in mapping:
        raise ModelUnavailable("label_mapping does not contain the positive label")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not 0 < threshold < 1:
        raise ModelUnavailable("threshold must be a number between 0 and 1")

    try:
        import joblib
        import sklearn
    except ImportError:
        raise ModelUnavailable("scikit-learn or joblib is not installed") from None
    if metadata["sklearn_version"] != sklearn.__version__:
        raise ModelUnavailable(
            f"model needs scikit-learn {metadata['sklearn_version']}, found {sklearn.__version__}"
        )
    if _sha256(model_path) != metadata["model_sha256"]:
        raise ModelUnavailable(f"{MODEL_FILE} does not match the checksum in {METADATA_FILE}")

    try:
        pipeline = joblib.load(model_path)
        positive_column = list(pipeline.classes_).index(mapping[positive])
    except Exception:
        raise ModelUnavailable(f"{MODEL_FILE} could not be loaded") from None
    return pipeline, metadata, positive_column


def mostly_non_latin(text: str) -> bool:
    """True only when a message clearly is not in the Latin alphabet.

    Counts letters only (digits, punctuation, emoji, and spaces are ignored). Text with
    very few letters is treated as applicable, to stay conservative.
    """
    letters = [character for character in text if character.isalpha()]
    if len(letters) < MIN_LETTERS_FOR_SCRIPT_CHECK:
        return False
    latin = sum(1 for character in letters if unicodedata.name(character, "").startswith("LATIN"))
    return latin / len(letters) < MIN_LATIN_SHARE


class Classifier:
    """Holds the loaded model, or the reason it is unavailable."""

    def __init__(self, pipeline=None, metadata: dict | None = None, positive_column: int = 1):
        self._pipeline = pipeline
        self._metadata = metadata or {}
        self._positive_column = positive_column

    @classmethod
    def load(cls, directory: Path | None = None) -> "Classifier":
        directory = Path(directory) if directory else model_directory()
        try:
            pipeline, metadata, positive_column = read_artifact(directory)
        except ModelUnavailable as error:
            logger.warning("Auxiliary classifier unavailable: %s", error)
            return cls()
        return cls(pipeline, metadata, positive_column)

    @property
    def available(self) -> bool:
        return self._pipeline is not None

    @property
    def threshold(self) -> float:
        return float(self._metadata["threshold"])

    def model_info(self) -> dict | None:
        if not self.available:
            return None
        return {
            "name": self._metadata.get("model_name", "unknown"),
            "training_data": TRAINING_DATA,
            "model_sha256": self._metadata["model_sha256"],
        }

    def classify(self, text: str, language: str | None = None) -> ClassifierResult:
        """Label the message, or say why the model was not run.

        `language` is the estimated language tag. "en" or None leave the decision to the
        script check alone, which is how English is classified. Any other estimate,
        including "unknown", means the model is not run.
        """
        if not self.available:
            return ClassifierResult(UNAVAILABLE, None, None)
        if language in NOT_ENGLISH_LANGUAGES or mostly_non_latin(text):
            return ClassifierResult(NOT_APPLICABLE, None, self.model_info())
        try:
            score = float(self._pipeline.predict_proba([text])[0][self._positive_column])
        except Exception:
            logger.warning("Auxiliary classifier failed on a message; returning unavailable.")
            return ClassifierResult(UNAVAILABLE, None, None)
        if not math.isfinite(score):
            return ClassifierResult(UNAVAILABLE, None, None)
        # Same rule as training: spam-like when the score is at or above the threshold.
        label = SPAM_LIKE if score >= self.threshold else NOT_SPAM_LIKE
        return ClassifierResult(OK, label, self.model_info())
