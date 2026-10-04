"""Save and load the trained classifier together with its metadata.

The artifact is a joblib (pickle) file. Loading a pickle runs code, so only load
artifacts produced locally by train_evaluate.py. The checksum in metadata.json
detects corruption or a mismatched file; it is not protection against someone who
can replace both files.
"""

import hashlib
import json
import os
import platform
from pathlib import Path

import joblib
import sklearn

MODEL_FILE = "model.joblib"
METADATA_FILE = "metadata.json"
REQUIRED_METADATA = ("model_sha256", "sklearn_version", "label_mapping", "positive_label", "threshold")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_DIR = REPO_ROOT / "ml" / "models" / "sms_spam"


class ModelNotAvailableError(Exception):
    """The model artifact is missing, incomplete, or unsafe to load."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _replace_atomically(destination: Path, write) -> None:
    temporary = destination.with_suffix(destination.suffix + ".part")
    try:
        write(temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def save_model(pipeline, metadata: dict, directory: Path = DEFAULT_MODEL_DIR) -> dict:
    """Write model.joblib and metadata.json, and return the full metadata that was saved."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    model_path = directory / MODEL_FILE
    _replace_atomically(model_path, lambda path: joblib.dump(pipeline, path))

    metadata = {
        **metadata,
        "model_file": MODEL_FILE,
        "model_sha256": _sha256(model_path),
        "sklearn_version": sklearn.__version__,
        "joblib_version": joblib.__version__,
        "python_version": platform.python_version(),
    }
    _replace_atomically(
        directory / METADATA_FILE,
        lambda path: path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"),
    )
    return metadata


def load_model(directory: Path = DEFAULT_MODEL_DIR):
    """Return (pipeline, metadata), or raise ModelNotAvailableError without loading anything doubtful."""
    directory = Path(directory)
    model_path = directory / MODEL_FILE
    metadata_path = directory / METADATA_FILE
    if not model_path.is_file() or not metadata_path.is_file():
        raise ModelNotAvailableError(
            f"No trained model in {directory}. Run: python ml/src/train_evaluate.py"
        )

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ModelNotAvailableError(f"{metadata_path} is not valid JSON: {error}") from None

    missing = [key for key in REQUIRED_METADATA if key not in metadata]
    if missing:
        raise ModelNotAvailableError(f"{metadata_path} is missing fields: {missing}")
    if metadata["sklearn_version"] != sklearn.__version__:
        raise ModelNotAvailableError(
            f"Model was saved with scikit-learn {metadata['sklearn_version']} but "
            f"{sklearn.__version__} is installed. Retrain the model."
        )
    if _sha256(model_path) != metadata["model_sha256"]:
        raise ModelNotAvailableError(f"{model_path} does not match the checksum in {METADATA_FILE}.")

    return joblib.load(model_path), metadata
