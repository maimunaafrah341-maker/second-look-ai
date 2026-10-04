"""Leakage-aware preparation of the ingested SMS dataset.

Three steps, none of which modify the ingested CSV:

1. Exact deduplication: one record per distinct message text.
2. Near-duplicate grouping: messages that are almost the same share a group.
3. Group-aware, stratified split: a group is never divided between splits.

See docs/model_evaluation.md for the reasoning and the limitations.
"""

import unicodedata

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import normalize

from ingest_sms_spam import Record

LABEL_TO_INT = {"ham": 0, "spam": 1}
INT_TO_LABEL = {value: key for key, value in LABEL_TO_INT.items()}

DEFAULT_GROUP_THRESHOLD = 0.8
SPLITS = ("train", "validation", "test")


def normalize_for_grouping(text: str) -> str:
    """Normalize a message for duplicate grouping only. Models are trained on the original text.

    Unicode NFKC, lowercase, and whitespace collapsed to single spaces. Digits, URLs,
    and punctuation are deliberately left alone: replacing them can make genuinely
    different messages look identical.
    """
    return " ".join(unicodedata.normalize("NFKC", text).lower().split())


def encode_labels(labels: list[str]) -> np.ndarray:
    unknown = sorted(set(labels) - set(LABEL_TO_INT))
    if unknown:
        raise ValueError(f"Unknown labels: {unknown}")
    return np.array([LABEL_TO_INT[label] for label in labels])


def deduplicate_exact(records: list[Record]) -> list[Record]:
    """Keep the record with the lowest id for each exact message text."""
    kept: dict[str, Record] = {}
    for record in sorted(records, key=lambda record: record.id):
        first = kept.setdefault(record.text, record)
        if first.label != record.label:
            raise ValueError(
                f"Records {first.id} and {record.id} have the same text but different labels."
            )
    return list(kept.values())


def assign_groups(texts: list[str], threshold: float = DEFAULT_GROUP_THRESHOLD) -> list[int]:
    """Return a group number for each text; near-duplicates share a number.

    Two texts are linked when their normalized forms are identical, or when the cosine
    similarity of their character 3-gram sets is at least `threshold`. Groups are the
    connected components of those links, so a chain A~B~C puts A and C together even
    if they are not directly similar. The group number is the index of its first member.
    """
    normalized = [normalize_for_grouping(text) for text in texts]
    parent = list(range(len(texts)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(a: int, b: int) -> None:
        root_a, root_b = find(a), find(b)
        # The smaller index always becomes the root, so results do not depend on link order.
        parent[max(root_a, root_b)] = min(root_a, root_b)

    first_seen: dict[str, int] = {}
    for index, text in enumerate(normalized):
        union(index, first_seen.setdefault(text, index))

    try:
        counts = CountVectorizer(analyzer="char", ngram_range=(3, 3), binary=True, lowercase=False)
        vectors = normalize(counts.fit_transform(normalized).astype(np.float64))
    except ValueError:
        vectors = None  # every text is shorter than three characters

    if vectors is not None:
        chunk = 512  # compare in chunks to keep memory use small
        for start in range(0, len(texts), chunk):
            similarities = (vectors[start : start + chunk] @ vectors.T).toarray()
            rows, columns = np.nonzero(similarities >= threshold)
            for row, column in zip(rows.tolist(), columns.tolist()):
                if start + row < column:
                    union(start + row, column)

    return [find(index) for index in range(len(texts))]


def split_by_group(labels: np.ndarray, groups: list[int], seed: int) -> list[str]:
    """Assign each record to train (about 60%), validation (20%), or test (20%).

    Splits are stratified by label and never divide a group.
    """
    labels = np.asarray(labels)
    groups = np.asarray(groups)
    indices = np.arange(len(labels))

    outer = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
    rest, test = next(outer.split(indices, labels, groups))
    inner = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=seed)
    train, validation = next(inner.split(rest, labels[rest], groups[rest]))

    splits = np.empty(len(labels), dtype=object)
    splits[rest[train]] = "train"
    splits[rest[validation]] = "validation"
    splits[test] = "test"
    return splits.tolist()
