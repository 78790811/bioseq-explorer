# integrator.py
# Module responsible for standardising and exporting cleaned records.
# Takes accepted records from cleaner.py and saves them as a single
# unified CSV file (clean_dataset.csv) for use by BioSeq Explorer.
# Part of the HUBA data preparation pipeline.

from __future__ import annotations
import csv
from pathlib import Path


# ---------------------------------------------------------------------------
# Column standardisation
# ---------------------------------------------------------------------------

# These are the canonical column names used in clean_dataset.csv.
# All records will be mapped to these columns regardless of source format.
CANONICAL_COLUMNS = [
    "id",           # Sequence identifier (e.g. BRCA1, seq01)
    "sequence",     # Nucleotide sequence (uppercase string)
    "description",  # Optional description from FASTA header or CSV field
    "organism",     # Organism name if available (e.g. Homo sapiens)
    "_source",      # Source filename (added by load_data.py)
]


def standardise_record(record: dict) -> dict:
    """Map a record to the canonical column set.

    Missing fields are filled with an empty string.
    Extra fields not in CANONICAL_COLUMNS are discarded.

    Args:
        record: a single sequence record (dict) from cleaner.py

    Returns:
        a new dict with exactly the keys defined in CANONICAL_COLUMNS
    """
    # Build a new dict with canonical columns only
    # If a key is missing in the record, use empty string as default
    return {col: record.get(col, "") for col in CANONICAL_COLUMNS}


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def save_clean_dataset(
    records: list[dict],
    output_path: Path,
) -> None:
    """Save a list of standardised records to a CSV file.

    Creates parent directories automatically if they do not exist.
    Overwrites the file if it already exists.

    Args:
        records:     list of accepted records from cleaner.py
        output_path: full path to the output CSV file
    """
    # Create parent directories if they do not exist yet
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Standardise all records to canonical columns before saving
    standardised = [standardise_record(r) for r in records]

    # Write to CSV file
    with output_path.open(mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CANONICAL_COLUMNS)

        # Write the header row (column names)
        writer.writeheader()

        # Write all data rows
        writer.writerows(standardised)

    print(f"  Saved: {output_path} ({len(standardised)} records)")


# ---------------------------------------------------------------------------
# Rejected records export
# ---------------------------------------------------------------------------

def save_rejected(
    records: list[dict],
    output_path: Path,
) -> None:
    """Save rejected records with rejection reasons to a CSV file.

    Useful for auditing — shows which records were removed and why.

    Args:
        records:     list of rejected records from cleaner.py
        output_path: full path to the output CSV file
    """
    if not records:
        return

    # Create parent directories if they do not exist yet
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Columns for the rejected records file
    rejected_columns = CANONICAL_COLUMNS + ["reason"]

    # Standardise and add reason field
    rows = []
    for record in records:
        row = standardise_record(record)
        row["reason"] = record.get("reason", "UNKNOWN")
        rows.append(row)

    with output_path.open(mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rejected_columns)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Saved: {output_path} ({len(rows)} rejected records)")