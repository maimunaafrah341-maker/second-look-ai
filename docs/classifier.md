# Auxiliary classifier

`POST /analyze` includes a `classifier` section produced by a small machine-learning model. This file explains what its label means, why it is only an auxiliary signal, and what it needs to run.

## What the label means

The model compares a message with English SMS spam from the [UCI SMS Spam Collection](datasets.md). It returns one of two labels:

- **`spam_like`:** the message resembles that 2011 spam.
- **`not_spam_like`:** it does not.

That is all the label means. It does **not** mean "fraud" or "not fraud".

## Why it is only an auxiliary signal

- **Wrong training data for the goal.** The model learned from English SMS sent in the UK and Singapore around 2011. It has never seen a UPI, KYC, digital-arrest, or courier-fee scam, or a genuine Indian bank message.
- **Spam is not fraud.** The training label `spam` includes ordinary promotions as well as scams.
- **Known false positives.** A genuine Indian bank debit alert is rated spam-like. A test keeps this case visible so that any change in behaviour is noticed.
- **Known misses.** A hand-written digital-arrest message was rated not spam-like.
- **No Indian evaluation yet.** How it should be measured on Indian messages is set out in [evaluation_protocol.md](evaluation_protocol.md). Until then, its only measured result is on UCI data (see [model_evaluation.md](model_evaluation.md)).

So the classifier:

- never produces a verdict or a combined score;
- never changes the warning-sign `findings` or the official `guidance` (tests check this);
- always carries a notice saying it cannot tell whether a message is fraudulent, and that "not spam-like" does not mean safe.

The protocol also fixes a presentation rule for later: if the classifier's false-positive rate on genuine look-alike messages in the Indian holdout is above 25%, an interface should mark it as experimental and show it last. That rule affects presentation only. It does not change the model or its threshold.

## Why no score is shown

The model produces a number internally, and the label comes from comparing it with a fixed threshold. The number is not returned because:

- **It is not a fraud probability.** It measures resemblance to 2011 English spam.
- **It is not calibrated.** Training used balanced class weights, which push scores upwards, so a value such as 0.3 has no reliable meaning.
- **A number invites misreading.** Users would read "0.95" as "95% likely to be a scam".

## Response format

```json
"classifier": {
  "status": "ok",
  "label": "spam_like",
  "model": {
    "name": "char_tfidf_logistic_regression",
    "training_data": "UCI SMS Spam Collection: English SMS from the UK and Singapore, around 2011",
    "model_sha256": "bd1079ed0b0ac41ca0dead4a1c113e963f40a160301f3bd543558192b2f62561"
  },
  "notice": "…"
}
```

| `status` | `label` | When |
| --- | --- | --- |
| `ok` | `spam_like` or `not_spam_like` | The model ran |
| `not_applicable` | `null` | The message does not appear to be mainly in English |
| `unavailable` | `null` | The model could not be loaded safely, or failed on this message |

`model` is `null` when the status is `unavailable`. Every status has its own notice.

## Language handling

The model uses English character patterns and was trained only on English SMS. It is run only when a message appears to be mainly in English. Two checks decide this, and either one can stop the model:

1. **The language estimate** (`language.detected` in the response, from `backend/app/language.py`). The model is not run when the estimate is `hi`, `hi-Latn`, `te`, `ur`, `bn`, or `mixed`. `mixed` is included because the estimate only gives `en` when it can tell the message is mainly English.
2. **A script check.** The model is not run when fewer than half of the letters are Latin. Only letters are counted, and messages with fewer than four letters pass this check.

When the estimate is `en` or `unknown` (for example a message of only numbers, emoji, or a link), only the script check applies, exactly as before the language estimate existed.

The effect:

- **English** is classified, as before. Across all 5,574 UCI English messages, adding the language estimate changed the classifier result for one message only, and that message is romanised Hindi.
- **Mostly English with a Hindi word or two** ("…Kal meeting hai, thanks") is classified.
- **Romanised Hindi (Hinglish)** is `not_applicable` when the estimate recognises it. Text with too few romanised-Hindi words is estimated as English and is still classified.
- **Hindi in Devanagari, Telugu, Urdu, Bengali,** other non-Latin scripts, and mixed-script messages are `not_applicable`.

No multilingual ML support is claimed. The warning-sign rules still run on every message, including their small set of Hindi phrases.

## The artifact

| Item | Value |
| --- | --- |
| Files | `backend/app/data/classifier/model.joblib` (731,716 bytes) and `metadata.json` |
| SHA-256 | `bd1079ed0b0ac41ca0dead4a1c113e963f40a160301f3bd543558192b2f62561` |
| Model | Character 2- to 5-gram TF-IDF with logistic regression (C = 100), 28,016 features |
| Threshold | 0.1116, chosen on UCI validation data for a 1% false-positive rate there |
| Trained with | scikit-learn 1.9.1, joblib 1.6.0, Python 3.11.0 |
| Produced by | `python ml/src/train_evaluate.py` (seed 42), then copied here unchanged |

The file is a copy of `ml/models/sms_spam/model.joblib`, which stays out of Git. `.gitignore` excludes every `*.joblib` file except this one. `evaluation.json` from the training run is not copied, because it contains a local file path and is not needed at runtime.

### Checks before loading

The API repeats the checks in `ml/src/model_io.py` before it loads anything:

1. `model.joblib` and `metadata.json` both exist.
2. The metadata is valid JSON and has `model_sha256`, `sklearn_version`, `label_mapping`, `positive_label`, and `threshold`.
3. The threshold is a number between 0 and 1, and the label mapping contains the positive label.
4. The installed scikit-learn version equals the recorded one.
5. The model file's SHA-256 matches the recorded checksum.

If any check fails, the classifier reports `unavailable` and the rest of `/analyze` keeps working. A short reason is logged; message text is never logged.

A `.joblib` file is a pickle, and loading a pickle can run code. The API loads only this project's artifact, from a path set in code or by the operator. It never loads a file supplied in a request. The checksum catches corruption or an accidental swap, not someone able to replace both files.

### Updating the artifact

1. Retrain with `python ml/src/train_evaluate.py`.
2. Copy `model.joblib` and `metadata.json` from `ml/models/sms_spam/` to `backend/app/data/classifier/`.
3. Update the checksum and threshold expected in `backend/tests/test_classifier.py`, and the details in this file.
4. Run `python -m pytest`.

## Deployment requirements

- **Python 3.11.** Set the Python version on the host (on Render, the `PYTHON_VERSION` environment variable) so the pinned wheels install.
- **Pinned packages.** `requirements.txt` pins scikit-learn 1.9.1 with numpy, scipy, joblib, and their required helpers (threadpoolctl, narwhals, cloudpickle). A different scikit-learn version makes the classifier `unavailable`.
- **No download, no build-time training.** The artifact is in the repository.
- **Optional override.** Set `SECOND_LOOK_MODEL_DIR` to load the model from another directory. The default is found relative to the code, not the working directory.
- **Single-threaded maths.** Setting `OPENBLAS_NUM_THREADS=1` and `OMP_NUM_THREADS=1` is recommended on small instances to limit memory reserved for thread pools.

### Measured on the development machine

Windows, Python 3.11, with Uvicorn serving the full API:

| Measurement | Value |
| --- | --- |
| Memory after startup | 136 MB working set (45 MB before the classifier was added) |
| Memory after 200 `/analyze` requests | 139 MB working set |
| Importing scikit-learn and joblib | 2.3 s (about 12 s on a cold first run) |
| Checking and loading the model | 0.3 s |
| Classifying one message | 1.8 ms; 6.9 ms for a 5,000-character message |

Windows also reports about 1.1 GB of reserved memory once numpy loads. That is address space set aside for thread pools, not memory in use. Linux figures on Render will differ and should be measured there.
