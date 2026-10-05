# Evaluation protocol: Indian messages

This document fixes how Second Look will be evaluated on Indian messages, before any of that data exists. Writing it first means the categories, labels, and metrics cannot be adjusted afterwards to flatter the results.

It covers the three parts of `/analyze` separately: the ML classifier, the warning-sign rules, and the official-guidance retrieval.

## 1. Why a separate Indian evaluation is needed

The classifier's reported results (see [model_evaluation.md](model_evaluation.md)) come from the test split of the UCI SMS Spam Collection. That is an **in-domain English SMS benchmark**:

- the messages are English SMS from the UK and Singapore, collected around 2011;
- the label is `spam` versus `ham`, and `spam` includes ordinary promotions as well as scams;
- training, validation, and test messages all come from the same collection.

So the UCI result shows how well the model recognises 2011 English SMS spam. **It is not evidence of how well Second Look handles Indian fraud.** The collection contains no UPI, KYC, digital-arrest, or courier-fee scams and no Indian bank messages.

A quick check of the saved model on a few hand-written Indian examples already showed the gap: a genuine bank debit alert and a genuine OTP notice were both rated spam-like. Those are anecdotes, not a measurement. This protocol defines the measurement.

The rules and the retrieval have never been measured on real messages at all. The retrieval has only a 70-message hand-written set (see [guidance_sources.md](guidance_sources.md)), which stays as it is.

## 2. Labels

Every message gets exactly one label.

| Label | Meaning | Scored? |
| --- | --- | --- |
| `fraud` | An attempt to obtain money, credentials, personal data, or device access by deception. | Yes, as positive |
| `legitimate` | A genuine personal, transactional, or official message. | Yes, as negative |
| `promotional` | Genuine marketing from a real business. Unwanted, perhaps, but not fraud. | Reported separately (see section 6) |
| `ambiguous` | Cannot be labelled confidently from the text alone, for example a "registration fee" for a real job fair. | No. Listed with outputs, left out of all metrics. |

Labelling rules:

- **Judge the text alone.** Do not use information that the system cannot see.
- **When unsure, use `ambiguous`.** It is better to drop an item than to score against a guessed label.
- **Second opinion.** Where possible, a second person labels the holdout independently. Disagreements become `ambiguous` unless both agree after discussion.

## 3. Categories

Each message also gets one category. Categories exist so that results can be broken down and gaps made visible.

### Fraud categories

| Category | Typical pattern |
| --- | --- |
| `kyc_account_block` | Account, card, wallet, or SIM will be blocked unless KYC is "updated" |
| `credential_request` | Asks for an OTP, PIN, CVV, password, or net-banking details |
| `upi_payment` | UPI collect request, or "scan this QR / enter your UPI PIN to receive money" |
| `authority_impersonation` | Police, CBI, customs, TRAI, or court; includes "digital arrest" |
| `utility_disconnection` | Electricity or gas will be cut off tonight; call an "officer" |
| `courier_customs` | Parcel held; pay a customs, address, or redelivery fee |
| `job_task` | Part-time job, tasks, likes, or captcha work that requires a fee |
| `investment_crypto` | Trading tips, crypto, or high-return groups, including romance-led pitches |
| `loan` | Instant loan approval, app download, processing fee, or later harassment |
| `prize_reward` | Lottery, prize, KBC-style win, cashback, or reward points to "redeem" |
| `fake_support_refund` | Fake customer care number, refund, or reversal |
| `family_impersonation` | "New number, send money urgently", claiming to be a relative or friend |

### Legitimate and promotional categories

| Category | Example |
| --- | --- |
| `bank_alert` | Debit or credit alert, including "Not you? Call…" |
| `otp_genuine` | A real OTP, including "do not share it" |
| `kyc_reminder_genuine` | A real reminder to update KYC at the branch or in the official app |
| `delivery_genuine` | A real delivery update with a tracking link |
| `utility_reminder_genuine` | A real electricity, gas, or recharge reminder with amount and date |
| `security_awareness` | Bank, telecom, or government advice that uses scam vocabulary |
| `personal_conversation` | Chat that mentions money, OTPs, police, jobs, or links in an ordinary way |
| `transaction_confirmation` | UPI "payment received", booking, or appointment confirmation |
| `promotional_genuine` | Real brand offers and sales messages |

### Hard negatives

The first seven legitimate categories above (bank alerts through personal conversations) are **hard negatives**: genuine messages that look like scams. Each item carries a `hard_negative` flag. These matter most, because flagging a genuine bank alert as suspicious teaches users to ignore the tool.

Hard positives should also be included: scams without links or urgency words, digital-arrest messages written as chat, romanised Hindi, and lightly obfuscated text.

## 4. Two pools: development and holdout

| Pool | Purpose | Who may see it | Size |
| --- | --- | --- | --- |
| Development | Trying ideas: rule changes, retrieval terms, presentation decisions | Anyone, including whoever tunes the system | About 40–60 messages |
| Holdout | One honest measurement for the submission | Collected or written by someone who is **not** tuning the rules or retrieval; not shared with the tuner before it is frozen | About 100–120 messages |

Separation rules:

- **No overlap.** Before freezing, check the holdout against the development pool and against the UCI collection for exact and near-duplicate messages (the grouping code in `ml/src/dataset_prep.py` can do this). Variants of the same scam template go entirely into one pool.
- **Freeze before running.** Commit the holdout file, then record its SHA-256 checksum and the commit in the results document. Any later edit is then visible.
- **One run.** Evaluate the frozen holdout once, with the system as committed at that point.
- **No tuning afterwards.** Do not change rules, retrieval terms, the corpus, the classifier, or its threshold in response to holdout results and then report the holdout again as if it were fresh. If something is changed after the run, say so in the results. Further claims then need a new holdout.
- **Never train on it.** The holdout is never used to train, choose a threshold for, or calibrate any model.

### Suggested holdout composition

This is a practical target, not a research benchmark.

| Group | Count | Notes |
| --- | --- | --- |
| Fraud | About 48 | Four per category across the twelve categories |
| Legitimate | About 42 | At least 28 hard negatives (four per hard-negative category), plus about 14 ordinary messages |
| Promotional | About 10 | Real brand offers |
| Ambiguous | As they arise | Not scored |
| **Total** | **About 100–120** | |

Within that total, include about 12–15 non-English or code-mixed messages, spread across labels. Use Hindi in Devanagari and romanised Hindi; include other languages only if a native speaker writes or checks them. They are part of the counts above, not extra.

## 5. Provenance

Every message records where it came from. Results are broken down by provenance, because the type of source changes what the numbers mean.

| Type | Requirements | What results on it mean |
| --- | --- | --- |
| `real_redacted` | Contributed by a team member with the sender's or recipient's consent. Names, phone numbers, account fragments, and links that could identify a person are replaced with placeholders such as `[NAME]` or `XX1234`. If redaction is doubtful, keep the file out of the public repository and commit only its checksum. | Closest to real-world behaviour |
| `public_dataset` | From a published dataset whose licence permits this use, cited with its source. Licence and origin are verified before use. | Real-world behaviour on that dataset's population |
| `advisory_pattern` | Written in our own words to follow a pattern described in an official advisory. Not copied. The advisory is cited. | How the system handles known scam patterns |
| `authored` | Written by a team member from experience or imagination. | Behaviour on illustrative examples only |

Do not describe results on `authored` or `advisory_pattern` items as real-world performance.

## 6. What is measured

Each part of `/analyze` is evaluated separately. There is no combined score, because the product deliberately gives no combined verdict.

### Positive and negative

- **Positive:** `fraud`.
- **Negative:** `legitimate`.
- **Promotional:** reported both ways, as negative and as excluded. The UCI classifier was trained to call promotions "spam", so promotional items flagged as spam-like are expected and are not fraud errors.
- **Ambiguous:** excluded from all metrics.

### ML classifier

- **Predicted positive:** the saved model's score is at or above its existing threshold (0.1116). The threshold is not changed for this evaluation.
- **Non-English messages:** not scored. They count towards **not-applicable coverage**, the share of messages the classifier cannot meaningfully handle, reported per language. The model uses English character patterns, so scores on other scripts carry no meaning.
- **Metrics:** confusion matrix, precision, recall, F1, false-positive rate, false-negative rate, and PR-AUC (average precision) from the model's internal scores. PR-AUC is meaningful here because the model produces a ranking. The API does not expose these scores.

### Warning-sign rules

- **Predicted positive:** at least one finding.
- **Metrics:** confusion matrix, precision, recall, F1, false-positive rate, false-negative rate. PR-AUC is not reported, because the rules give yes or no and no ranking.
- **Per finding category:** how often each finding type appears on fraud versus legitimate messages. The `link` finding is expected to fire on every genuine delivery link, and that should be visible rather than hidden.
- **Language:** the rules include a small set of Hindi (Devanagari) phrases, so Hindi messages are scored. Results are reported per language.

### Official-guidance retrieval

- **Labels:** each item lists `expected_guidance_sources`, the corpus sources that would be a correct first result. Many items will correctly expect nothing, because the corpus has no verified guidance for several categories (for example UPI, electricity, courier, and loan scams). That gap should show in the results.
- **Counts:** correct match, false match, missed, and correct silence, defined exactly as in [guidance_sources.md](guidance_sources.md). Precision and recall follow from those counts.
- **Language:** retrieval is English-only, so non-English items should expect nothing and are reported separately.
- **Separation from existing sets:** the existing retrieval development and check parts in `backend/evaluation/retrieval_eval.json` are not changed. The Indian holdout is reported as a separate result.

### Breakdowns and uncertainty

- **Per category:** recall for each fraud category; false-positive rate for each legitimate category, with hard negatives also reported as one group. With about four items per category these are indicative only and are shown as counts (for example "3 of 4"), not percentages.
- **Per provenance and per language:** as described above.
- **Intervals:** every rate is reported with a 95% Wilson interval, which behaves sensibly for small counts. For example, 0 errors out of 40 still means the true rate could be as high as about 9%.

## 7. How the classifier result will be used

The UCI-trained classifier remains an **auxiliary signal**. It is not an Indian fraud classifier and will not drive a risk judgement, whatever the holdout shows. A test set of about 110 messages cannot justify that.

The holdout decides only how prominently the classifier is shown. This rule is fixed now, before the data exists:

> If the classifier's false-positive rate on the legitimate hard negatives is above 25%, the interface labels its output as experimental and shows it last. Otherwise it is shown as an auxiliary signal with its standard notice.

The 25% figure is a proposal and should be confirmed or changed **before** the holdout is evaluated, never after.

## 8. Retraining

- **Not before 10 October.** The current model is evaluated as it is.
- **Never on the holdout.** It is not used to train, choose a threshold for, or calibrate any model.
- **Later.** If an Indian training set with a suitable licence and consent becomes available, train on it, use the development pool for thresholds, and report on a new holdout.

## 9. Reporting

The results document records:

- the holdout checksum, the commit evaluated, and the model checksum;
- counts per label, category, language, and provenance;
- all metrics above with intervals, plus every misclassified holdout message and what each component returned;
- any changes made after the run.

The results document must also state these limitations plainly:

- **Small sample.** About 110 messages. Intervals are wide and per-category results are indicative only.
- **Domain mismatch.** The classifier was trained on 2011 English UK/Singapore SMS, not on Indian fraud.
- **Provenance mix.** How much of the holdout is real, and how much is written by the team.
- **Author overlap.** Whether anyone who tuned the rules or retrieval also wrote holdout items.
- **Coverage.** Which languages and channels are represented, and which are not.
- **No general claim.** The numbers describe these messages, not Indian fraud messages in general.

## 10. File format

When the data is created, each pool is a JSON Lines file with one message per line, stored under `evaluation/indian_messages/` (`dev.jsonl` and `holdout.jsonl`).

```json
{"id": "h-001", "text": "…", "label": "fraud", "category": "kyc_account_block",
 "hard_negative": false, "language": "en", "channel": "sms",
 "expected_guidance_sources": ["certin-avoid-phishing"],
 "provenance": "advisory_pattern", "provenance_note": "I4C advisory, March 2025",
 "template_group": "kyc-01", "notes": ""}
```

| Field | Values |
| --- | --- |
| `label` | `fraud`, `legitimate`, `promotional`, `ambiguous` |
| `category` | One of the categories in section 3 |
| `language` | `en`, `hi-Deva` (Hindi in Devanagari), `hi-Latn` (romanised Hindi), or another code checked by a native speaker |
| `channel` | `sms`, `whatsapp`, `email`, `other` |
| `provenance` | `real_redacted`, `public_dataset`, `advisory_pattern`, `authored` |
| `template_group` | Shared by variants of the same template, so they stay in one pool |
