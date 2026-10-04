# Model evaluation: SMS spam baselines

This file records how the first classifier was trained and evaluated, the measured results, and what those results do and do not show.

**Scope.** The model separates `ham` from `spam` in the UCI SMS Spam Collection, an English SMS dataset from 2011 (see [datasets.md](datasets.md)). These results say nothing about Indian financial fraud, about Hindi, Urdu, Telugu, or Bengali, or about accuracy on messages people receive today.

## How to reproduce

From the repository root, with the virtual environment activated:

```powershell
python -m pip install -r requirements-dev.txt
python ml/src/ingest_sms_spam.py
python ml/src/train_evaluate.py
```

The run takes about 15 seconds on a laptop. With the default seed (42) it is deterministic: repeated runs produced a byte-identical model file.

Outputs, none of which are committed to Git:

| File | Contents |
| --- | --- |
| `ml/models/sms_spam/model.joblib` | The selected scikit-learn pipeline (about 0.7 MB) |
| `ml/models/sms_spam/metadata.json` | Label mapping, threshold, library versions, checksum, test metrics |
| `ml/models/sms_spam/evaluation.json` | Full results for every model |
| `ml/data/processed/sms_spam_prepared.csv` | Deduplicated records with their `group` and `split` |

Options: `--seed`, `--group-threshold`, `--max-fpr`, `--model-dir`.

## Protocol

1. **Exact deduplication.** One record is kept per distinct message text: the one with the lowest `id`. This removed 403 of 5,574 records, leaving 5,171. The ingested CSV is not modified.
2. **Near-duplicate grouping.** Messages that are almost the same are placed in one group (details below).
3. **Split by group.** Records are divided into train, validation, and test (about 60/20/20) with scikit-learn's `StratifiedGroupKFold`, seed 42. A group is never divided between splits, and the script stops if it finds one that is.
4. **Fit on train only.** Each model sees only the train split.
5. **Tune on validation only.** A small set of settings per model is compared by average precision on validation. The decision threshold is the lowest one that keeps the validation false-positive rate at or below 1%.
6. **Choose the model on validation only.** The model with the highest validation average precision is selected.
7. **Score the test split once.** Nothing is tuned on it. No calibration is fitted.

The saved artifact is the exact model that produced the test numbers below. It was not refitted on more data afterwards.

## Duplicate and near-duplicate handling

Grouping compares a normalized copy of each message. Models are trained on the original text.

- **Normalization:** Unicode NFKC, lowercase, whitespace collapsed to single spaces.
- **Not normalized:** digits, links, and punctuation. Replacing them with placeholders can make different messages identical, so they are left as they are.
- **Similarity:** cosine similarity between the sets of character 3-grams of two messages.
- **Linking:** two messages are linked when their normalized text is identical or their similarity is at least the threshold (default 0.8). Groups are the connected components of those links.

Measured on the 5,171 deduplicated records:

| Threshold | Groups | Groups with more than one record | Records in those groups | Largest group | Groups with both labels |
| --- | --- | --- | --- | --- | --- |
| 0.95 | 5,093 | 69 | 147 | 3 | 0 |
| 0.90 | 5,034 | 107 | 244 | 5 | 0 |
| **0.80 (default)** | 4,925 | 148 | 394 | 12 | 0 |
| 0.70 | 4,852 | 172 | 491 | 13 | 0 |
| 0.60 | 4,727 | 202 | 646 | 20 | 0 |

Most grouped records are spam sent from a template with a different phone number or claim code. At 0.8, 288 of the 394 grouped records are spam.

Limitations of the grouping:

- The threshold was chosen by reading sample groups, not by a measured criterion.
- Templates that were reworded more heavily fall below 0.8 and can still sit on both sides of a split. The 0.6 row shows there are more of them. This is the main remaining leakage risk.
- Linking is transitive, so a chain of similar messages can join two messages that are not similar to each other.
- Very short messages have few 3-grams, so their similarity scores are coarse.

## Split sizes

Seed 42, grouping threshold 0.8:

| Split | Records | Ham | Spam | Spam share | Groups |
| --- | --- | --- | --- | --- | --- |
| Train | 3,102 | 2,710 | 392 | 12.6% | 2,954 |
| Validation | 1,034 | 904 | 130 | 12.6% | 986 |
| Test | 1,035 | 904 | 131 | 12.7% | 985 |

## Models compared

| Model | Features | Classifier | Settings tried on validation | Selected |
| --- | --- | --- | --- | --- |
| Majority class | none | always predicts the class prior | none | n/a |
| Word TF-IDF + Naive Bayes | word 1- and 2-grams | Multinomial Naive Bayes | alpha 0.1, 0.5, 1.0 | alpha 0.1 |
| Character TF-IDF + Logistic Regression | character 2- to 5-grams within word boundaries, sublinear TF, minimum document frequency 2 | Logistic Regression, balanced class weights | C 1, 10, 100 | C 100 |

## Results on the test split

All three models were scored on the same 1,035 test messages (904 ham, 131 spam). "False spam" means a legitimate message flagged as spam.

| Model | True ham | False spam | Missed spam | True spam |
| --- | --- | --- | --- | --- |
| Majority class | 904 | 0 | 131 | 0 |
| Word TF-IDF + Naive Bayes | 899 | 5 | 15 | 116 |
| Character TF-IDF + Logistic Regression | 893 | 11 | 6 | 125 |

| Model | Spam precision | Spam recall | Spam F1 | Macro F1 | Average precision (PR-AUC) | False-positive rate | Accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Majority class | 0.000 | 0.000 | 0.000 | 0.466 | 0.127 | 0.00% | 0.873 |
| Word TF-IDF + Naive Bayes | 0.959 | 0.885 | 0.921 | 0.955 | 0.950 | 0.55% | 0.981 |
| Character TF-IDF + Logistic Regression | 0.919 | 0.954 | 0.936 | 0.963 | 0.973 | 1.22% | 0.984 |

The majority-class row shows why accuracy alone is misleading here: it scores 87% while catching no spam.

### Selected model

Character TF-IDF + Logistic Regression was selected because it had the highest validation average precision (0.993, against 0.979 for Naive Bayes). On validation, at the same 1% false-positive allowance, it missed 2 of 130 spam messages where Naive Bayes missed 8.

### Did it meet a 1% false-positive rate?

**No, not on the test split.** The threshold (0.1116) allowed 9 false positives among 904 validation ham messages, which is 1.00%. On the test split the same threshold produced 11 false positives among 904, which is 1.22%, with spam recall of 95.4%.

Naive Bayes stayed under 1% on test (0.55%) but with lower recall (88.5%).

With about 900 ham messages per split, each false positive moves the rate by 0.11 percentage points, so a threshold tuned to exactly 1% on validation can easily land on either side of 1% on new data.

### Robustness checks

These runs used different splits, with models saved to a temporary directory. They were not used to choose anything. Rows are for Character TF-IDF + Logistic Regression on each run's own test split.

| Run | Selected C | False spam | Missed spam | False-positive rate | Spam recall | Average precision |
| --- | --- | --- | --- | --- | --- | --- |
| Seed 42, threshold 0.8 (reported above) | 100 | 11 | 6 | 1.22% | 95.4% | 0.973 |
| Seed 7, threshold 0.8 | 1 | 8 | 3 | 0.88% | 97.7% | 0.988 |
| Seed 123, threshold 0.8 | 1 | 6 | 3 | 0.66% | 97.7% | 0.991 |
| Seed 42, threshold 0.6 | 100 | 6 | 8 | 0.66% | 93.9% | 0.980 |

The same model family was selected in every run. Results move by a few messages from split to split, which is the size of uncertainty to expect from a test set this small. The stricter grouping at 0.6 did not produce a clear drop.

## Loading the model

```python
from model_io import load_model, ModelNotAvailableError

pipeline, metadata = load_model()  # raises ModelNotAvailableError if it cannot be loaded safely
score = pipeline.predict_proba(["message text"])[0, metadata["label_mapping"]["spam"]]
is_spam_like = score >= metadata["threshold"]
```

`load_model` refuses to load when a file is missing, the metadata is incomplete, the installed scikit-learn version differs from the one used for training, or the model file does not match its recorded checksum.

The model file is a pickle. Loading a pickle can run code, so only load a model you trained yourself with `train_evaluate.py`. The checksum catches corruption, not deliberate replacement of both files.

## Limitations

- **Wrong domain for the product goal.** The training data is UK and Singapore SMS from around 2011. It contains no UPI, KYC, parcel, or electricity-disconnection scams. The model has not been tested on any Indian message.
- **Spam is not fraud.** The `spam` label includes ordinary promotions. A high score means "resembles 2011 SMS spam", not "is fraudulent".
- **English only.** No other language has been evaluated.
- **Small test set.** 131 spam and 904 ham messages. Differences of a few messages between models are within noise.
- **Residual leakage.** Reworded templates below the grouping threshold can appear in both train and test, which would make the test results optimistic.
- **Uncalibrated scores.** The score is not a probability of fraud and must not be shown to users as one. Balanced class weights shift scores upwards.
- **Narrow hyperparameter search.** Three settings per model. For the default seed the best C was the largest value tried, so a wider search might do better.
- **Single dataset.** Train, validation, and test all come from the same collection, so the results do not measure how the model handles a different source.
- **Not yet used by the API.** `/analyze` still returns rule-based findings only.
