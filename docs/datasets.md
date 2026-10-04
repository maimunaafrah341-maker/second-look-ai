# Datasets

This file records where each dataset comes from, how it is licensed, how to reproduce it, and what it cannot tell us.

## SMS Spam Collection (UCI)

| | |
| --- | --- |
| Dataset page | https://archive.ics.uci.edu/dataset/228/sms+spam+collection |
| Download URL | https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip |
| DOI | https://doi.org/10.24432/C5CC84 |
| License | Creative Commons Attribution 4.0 International (CC BY 4.0) |
| Retrieved | 2026-10-04 |
| Archive SHA-256 | `1587ea43e58e82b14ff1f5425c88e17f8496bfcdb67a583dbff9eefaf9963ce3` |
| Contents | 5,574 English SMS messages labelled `ham` (legitimate) or `spam` |

### Attribution and citation

This project uses the SMS Spam Collection by Tiago Almeida and José María Gómez Hidalgo, made available by the UCI Machine Learning Repository under CC BY 4.0. Second Look copies the message text and labels unchanged and adds an `id` column.

Dataset citation, as given by UCI:

> Almeida, T. & Hidalgo, J. (2011). SMS Spam Collection [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CC84

The archive's own `readme` asks users to also cite the paper that introduced the collection:

> Almeida, T. A., Gómez Hidalgo, J. M., & Yamakami, A. (2011). Contributions to the Study of SMS Spam Filtering: New Collection and Results. Proceedings of the 2011 ACM Symposium on Document Engineering (DocEng'11).

The data files are not stored in this repository. `ml/data/raw/` and `ml/data/processed/` are excluded by `.gitignore`.

### How to reproduce

From the repository root, with the virtual environment activated:

```powershell
python ml/src/ingest_sms_spam.py
```

The script uses only the Python standard library. It:

1. Downloads the archive to `ml/data/raw/sms_spam_collection.zip`, unless that file already exists. Use `--force-download` to fetch it again.
2. Checks the archive's SHA-256 against the value above and stops if it differs.
3. Checks every path in the archive, then reads the `SMSSpamCollection` file into memory. Nothing is extracted to disk and nothing from the archive is executed.
4. Parses and validates each line, then writes `ml/data/processed/sms_spam.csv`.
5. Reads the CSV back and confirms it matches the parsed records.

The raw archive is never modified after download. The processed CSV is rebuilt from scratch on every run, so rerunning cannot duplicate records.

### Processed file format

`ml/data/processed/sms_spam.csv` is UTF-8, comma-separated, with a header row.

| Column | Meaning |
| --- | --- |
| `id` | 1-based line number of the record in the original `SMSSpamCollection` file |
| `label` | `ham` or `spam`, copied from the source without renaming |
| `text` | The message, copied from the source without changes |

Label mapping: the source uses `ham` for legitimate messages and `spam` for unsolicited ones. The same two values are kept. No label is renamed to "fraud", because the source does not label fraud.

### Validation results

Measured by the ingestion script on 2026-10-04:

| Check | Result |
| --- | --- |
| Encoding | Valid UTF-8 |
| Source records | 5,574 (matches the documented count) |
| Excluded records | 0 |
| Malformed lines, unknown labels, empty messages | 0 |
| `ham` | 4,827 (86.6%) |
| `spam` | 747 (13.4%) |
| Unique message texts (exact match) | 5,171 |
| Duplicate records beyond the first occurrence | 403 (309 `ham`, 94 `spam`) |
| Texts that appear more than once | 281 |
| Texts that appear with both labels | 0 |

### Cleaning decisions

- **No records are removed.** The script would exclude lines with no tab separator, an unknown label, or an empty message, and would print each one with its line number. None were found.
- **Duplicates are kept and counted.** 403 records repeat an earlier message exactly. They stay in the processed file so that the decision is made openly at training time. If the same text lands in both the training and test split, test scores will be inflated, so the split must keep duplicates together or drop them.
- **Message wording is untouched.** No lowercasing, trimming, or character replacement is applied. This means some quirks of the source remain:
  - 309 messages contain HTML entities such as `&lt;` and `&gt;`.
  - 187 messages have leading or trailing whitespace.
  - Collapsing case and whitespace would reduce 5,171 unique texts to 5,159, so a few near-duplicates exist beyond the exact ones.

### Limitations

- **Not an Indian fraud dataset.** According to the archive's `readme`, the messages come from sources such as a UK consumer forum and a Singapore university SMS corpus. It must not be described as representative of scams seen in India.
- **English only.** It provides no evidence about Hindi, Urdu, Telugu, or Bengali performance.
- **Old.** The collection was published in 2011. It predates UPI, KYC-update, parcel, and electricity-disconnection scams, and it contains few links.
- **Spam is not fraud.** The `spam` label covers unsolicited promotions and premium-rate offers as well as scams. A model trained on it learns "spam-like", not "fraudulent".
- **SMS only.** There are no emails or WhatsApp messages.
- **Imbalanced.** About 13% of records are `spam`, so plain accuracy is a misleading metric.
