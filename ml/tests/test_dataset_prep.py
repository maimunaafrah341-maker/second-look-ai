"""Tests for deduplication, grouping, and splitting.

All messages here are small fixtures written for these tests. They are not
dataset records and are never used for training.
"""

from collections import Counter

import numpy as np
import pytest

from dataset_prep import (
    INT_TO_LABEL,
    LABEL_TO_INT,
    assign_groups,
    deduplicate_exact,
    encode_labels,
    normalize_for_grouping,
    split_by_group,
)
from ingest_sms_spam import Record


def test_label_mapping_is_fixed():
    assert LABEL_TO_INT == {"ham": 0, "spam": 1}
    assert INT_TO_LABEL == {0: "ham", 1: "spam"}
    assert encode_labels(["spam", "ham", "ham"]).tolist() == [1, 0, 0]


def test_encode_labels_rejects_unknown_labels():
    with pytest.raises(ValueError, match="Unknown labels"):
        encode_labels(["ham", "fraud"])


def test_deduplicate_exact_keeps_lowest_id_regardless_of_input_order():
    records = [
        Record(id=7, label="ham", text="see you soon"),
        Record(id=2, label="ham", text="see you soon"),
        Record(id=5, label="spam", text="win a prize"),
        Record(id=9, label="ham", text="See you soon"),
    ]

    kept = deduplicate_exact(records)

    assert [record.id for record in kept] == [2, 5, 9]
    assert deduplicate_exact(list(reversed(records))) == kept
    # The input is not modified.
    assert len(records) == 4


def test_deduplicate_exact_rejects_conflicting_labels():
    records = [Record(id=1, label="ham", text="hello"), Record(id=2, label="spam", text="hello")]

    with pytest.raises(ValueError, match="different labels"):
        deduplicate_exact(records)


def test_normalize_for_grouping_is_deterministic_and_idempotent():
    text = "  WIN  £100\tNOW!!\nCall ０９０６ "

    once = normalize_for_grouping(text)

    assert once == "win £100 now!! call 0906"
    assert normalize_for_grouping(text) == once
    assert normalize_for_grouping(once) == once


def test_normalize_for_grouping_keeps_digits_and_links_distinct():
    assert normalize_for_grouping("Your code is 1234") != normalize_for_grouping("Your code is 9999")
    assert normalize_for_grouping("see a.example/x") != normalize_for_grouping("see b.example/y")


def test_assign_groups_links_identical_and_near_identical_texts():
    texts = [
        "You have won a cash prize, call 09061701461 to claim now",
        "Are we still meeting for lunch tomorrow?",
        "You have won a cash prize, call 09061701999 to claim now",
        "ARE WE STILL  MEETING FOR LUNCH TOMORROW?",
        "Completely unrelated note about the weather",
        "ok",
        "Ok",
    ]

    groups = assign_groups(texts, threshold=0.8)

    assert groups == [0, 1, 0, 1, 4, 5, 5]
    assert assign_groups(texts, threshold=0.8) == groups


def test_assign_groups_threshold_is_configurable():
    texts = [
        "You have won a cash prize, call 09061701461 to claim now",
        "You have won a cash prize, call 09061701999 to claim now",
    ]

    assert len(set(assign_groups(texts, threshold=0.8))) == 1
    assert len(set(assign_groups(texts, threshold=0.99))) == 2


def test_assign_groups_handles_only_very_short_texts():
    assert assign_groups(["ok", "no", "OK"]) == [0, 1, 0]


def test_split_by_group_never_divides_a_group():
    rng = np.random.default_rng(0)
    # 150 groups of one to four records; every fifth group is spam.
    groups = np.repeat(np.arange(150), rng.integers(1, 5, size=150))
    labels = (groups % 5 == 0).astype(int)

    splits = np.array(split_by_group(labels, groups, seed=42))

    assert set(splits) == {"train", "validation", "test"}
    for group in np.unique(groups):
        assert len(set(splits[groups == group])) == 1
    for name in ("train", "validation", "test"):
        assert labels[splits == name].sum() > 0
    shares = {name: count / len(splits) for name, count in Counter(splits).items()}
    assert shares["train"] > shares["validation"]
    assert shares["train"] > shares["test"]


def test_split_by_group_is_deterministic_for_a_seed():
    groups = np.arange(100)
    labels = (groups % 4 == 0).astype(int)

    assert split_by_group(labels, groups, seed=1) == split_by_group(labels, groups, seed=1)
    assert split_by_group(labels, groups, seed=1) != split_by_group(labels, groups, seed=2)
