"""Download and normalize the UCI SMS Spam Collection.

Usage, from the repository root:

    python ml/src/ingest_sms_spam.py

The original archive is saved under ml/data/raw/ and is never modified once
downloaded. The normalized CSV under ml/data/processed/ is rebuilt from it on
every run, so rerunning cannot duplicate records.

Message text and labels are copied unchanged. Duplicates are counted and
reported, not removed. See docs/datasets.md for provenance and limitations.
"""

import argparse
import csv
import hashlib
import io
import os
import sys
import urllib.request
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

DATASET_URL = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"
# SHA-256 of the archive as retrieved on 2026-10-04.
EXPECTED_SHA256 = "1587ea43e58e82b14ff1f5425c88e17f8496bfcdb67a583dbff9eefaf9963ce3"
ARCHIVE_MEMBER = "SMSSpamCollection"
EXPECTED_RECORDS = 5574
VALID_LABELS = ("ham", "spam")
COLUMNS = ("id", "label", "text")

MAX_DOWNLOAD_BYTES = 5 * 1024 * 1024
MAX_MEMBER_BYTES = 10 * 1024 * 1024

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_ARCHIVE = REPO_ROOT / "ml" / "data" / "raw" / "sms_spam_collection.zip"
PROCESSED_CSV = REPO_ROOT / "ml" / "data" / "processed" / "sms_spam.csv"


class IngestionError(Exception):
    pass


@dataclass(frozen=True)
class Record:
    id: int  # 1-based line number in the original file
    label: str
    text: str


@dataclass
class ParseResult:
    records: list[Record] = field(default_factory=list)
    # (line number, reason) for every line that was not kept
    excluded: list[tuple[int, str]] = field(default_factory=list)


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download(url: str, destination: Path) -> None:
    """Download to a temporary file, then move it into place once complete."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read(MAX_DOWNLOAD_BYTES + 1)
        if len(data) > MAX_DOWNLOAD_BYTES:
            raise IngestionError(f"Download is larger than {MAX_DOWNLOAD_BYTES} bytes; refusing to save it.")
        temporary.write_bytes(data)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def read_member(archive: Path, member: str) -> bytes:
    """Read one file from the archive into memory. Nothing is extracted to disk or executed."""
    with zipfile.ZipFile(archive) as zf:
        for name in zf.namelist():
            parts = Path(name.replace("\\", "/")).parts
            if name.startswith(("/", "\\")) or ":" in name or ".." in parts:
                raise IngestionError(f"Archive contains an unsafe path: {name!r}")
        try:
            info = zf.getinfo(member)
        except KeyError:
            raise IngestionError(f"Archive does not contain {member!r}. Found: {zf.namelist()}") from None
        if info.file_size > MAX_MEMBER_BYTES:
            raise IngestionError(f"{member!r} is {info.file_size} bytes; larger than expected.")
        return zf.read(info)


def parse(raw: bytes) -> ParseResult:
    """Parse 'label<TAB>text' lines. Text is kept exactly as it appears in the source."""
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise IngestionError(f"Source file is not valid UTF-8: {error}") from None

    result = ParseResult()
    # Split on "\n" only: str.splitlines() would also break on characters inside messages.
    for number, line in enumerate(content.split("\n"), start=1):
        line = line.removesuffix("\r")
        if not line:
            if number <= content.count("\n"):
                result.excluded.append((number, "blank line"))
            continue  # otherwise this is the empty string after the final newline
        label, separator, text = line.partition("\t")
        if not separator:
            result.excluded.append((number, "no tab separator"))
        elif label not in VALID_LABELS:
            result.excluded.append((number, f"unknown label {label!r}"))
        elif not text.strip():
            result.excluded.append((number, "empty message"))
        else:
            result.records.append(Record(id=number, label=label, text=text))
    return result


def summarize(records: list[Record]) -> dict:
    by_text: dict[str, list[Record]] = {}
    for record in records:
        by_text.setdefault(record.text, []).append(record)
    repeated = [group for group in by_text.values() if len(group) > 1]
    return {
        "records": len(records),
        "labels": dict(Counter(record.label for record in records)),
        "unique_texts": len(by_text),
        # Records beyond the first occurrence of each exact text
        "duplicate_records": len(records) - len(by_text),
        "texts_appearing_more_than_once": len(repeated),
        "duplicate_records_by_label": dict(
            Counter(record.label for group in repeated for record in group[1:])
        ),
        "texts_with_conflicting_labels": sum(
            1 for group in repeated if len({record.label for record in group}) > 1
        ),
    }


def write_csv(records: list[Record], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(COLUMNS)
            writer.writerows((record.id, record.label, record.text) for record in records)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def read_csv(source: Path) -> list[Record]:
    with source.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = tuple(next(reader))
        if header != COLUMNS:
            raise IngestionError(f"Unexpected columns in {source}: {header}")
        return [Record(id=int(row[0]), label=row[1], text=row[2]) for row in reader]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="download again even if the raw archive already exists",
    )
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    try:
        if args.force_download or not RAW_ARCHIVE.exists():
            print(f"Downloading {DATASET_URL}")
            download(DATASET_URL, RAW_ARCHIVE)
        else:
            print(f"Using existing archive {RAW_ARCHIVE.relative_to(REPO_ROOT)}")

        digest = sha256_of(RAW_ARCHIVE)
        print(f"Archive SHA-256: {digest}")
        if digest != EXPECTED_SHA256:
            raise IngestionError(
                "Archive checksum does not match EXPECTED_SHA256. The file may be corrupt or "
                "the dataset may have been republished. Inspect it before updating the constant."
            )

        result = parse(read_member(RAW_ARCHIVE, ARCHIVE_MEMBER))
        for number, reason in result.excluded:
            print(f"Excluded line {number}: {reason}")
        if len(result.records) + len(result.excluded) != EXPECTED_RECORDS:
            raise IngestionError(
                f"Expected {EXPECTED_RECORDS} source records, found "
                f"{len(result.records) + len(result.excluded)}."
            )

        write_csv(result.records, PROCESSED_CSV)
        if read_csv(PROCESSED_CSV) != result.records:
            raise IngestionError("Processed CSV does not match the parsed records when read back.")
    except (IngestionError, OSError, zipfile.BadZipFile) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Wrote {PROCESSED_CSV.relative_to(REPO_ROOT)}")
    print(f"Excluded records: {len(result.excluded)}")
    for key, value in summarize(result.records).items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
