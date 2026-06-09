# load_data.py
# Module responsible for loading input files from the source directory.
# Supports FASTA (.fasta, .fa), CSV (.csv) and TSV (.tsv) formats.
# Part of the HUBA data preparation pipeline.

from __future__ import annotations
from pathlib import Path
import csv


# ---------------------------------------------------------------------------
# FASTA file reader
# ---------------------------------------------------------------------------

def read_fasta(path: Path) -> list[dict]:
    """Read a single FASTA file and return a list of sequence records.

    Each record is a dictionary with keys:
        - id: sequence identifier (string after '>')
        - description: optional description from the header line
        - sequence: the nucleotide sequence (uppercase string)
        - _source: name of the file this record came from
    """
    records = []
    current_id = None
    current_desc = ""
    current_seq = []

    # Open file with UTF-8 encoding to handle special characters
    with path.open(mode="r", encoding="utf-8") as f:
        for line in f:

            # Remove leading/trailing whitespace from each line
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            if line.startswith(">"):
                # Save the previous record before starting a new one
                if current_id is not None:
                    records.append({
                        "id": current_id,
                        "description": current_desc,
                        "sequence": "".join(current_seq),
                        "_source": path.name,
                    })

                # Parse the header line: ">id description"
                parts = line[1:].split(sep=" ", maxsplit=1)
                current_id = parts[0]
                current_desc = parts[1] if len(parts) > 1 else ""
                current_seq = []

            else:
                # Sequence line — convert to uppercase and append
                current_seq.append(line.upper())

    # Save the last record in the file
    if current_id is not None:
        records.append({
            "id": current_id,
            "description": current_desc,
            "sequence": "".join(current_seq),
            "_source": path.name,
        })

    return records


# ---------------------------------------------------------------------------
# Column name mapping for CSV / TSV files
# ---------------------------------------------------------------------------

# Mapping from known column name variants to canonical names.
# Keys are lowercase — comparison uses .lower().strip() on actual column names.
COLUMN_MAP = {
    # sequence variants
    "dnaseq": "sequence",
    "dnasequence": "sequence",
    "dna_sequence": "sequence",
    "seq": "sequence",
    "nucleotides": "sequence",
    "sequence": "sequence",
    # id variants
    "gene": "id",
    "genesymbol": "id",
    "gene_id": "id",
    "gene_name": "id",
    "accession": "id",
    "id": "id",
    # organism variants
    "organism": "organism",
    "species": "organism",
    "org": "organism",
}


# ---------------------------------------------------------------------------
# CSV / TSV file reader
# ---------------------------------------------------------------------------

def read_csv_tsv(path: Path) -> list[dict]:
    """Read a single CSV or TSV file and return a list of row records.

    Automatically maps common column name variants to canonical names
    using COLUMN_MAP defined at module level.

    A '_source' key is added to each record with the filename.
    """
    # Choose delimiter based on file extension
    delimiter = "\t" if path.suffix == ".tsv" else ","

    records = []

    with path.open(mode="r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            record: dict = {}

            # Map each column to its canonical name if known
            for original_key, value in row.items():
                canonical = COLUMN_MAP.get(original_key.lower().strip())
                if canonical:
                    # Only set if not already set — first match wins
                    if canonical not in record:
                        record[canonical] = value
                else:
                    # Keep unmapped columns as-is
                    record[original_key] = value

            # Add source filename
            record["_source"] = path.name

            # Keep all records — even those without a sequence
            # Empty sequences will be caught by cleaner.py (EMPTY_SEQUENCE rule)
            records.append(record)

    return records


# ---------------------------------------------------------------------------
# Main loader: loads all supported files from a directory
# ---------------------------------------------------------------------------

def load_all_files(
    source_dir: Path,
    selected_files: list[Path] | None = None,
) -> tuple[list[dict], list[dict]]:
    """Load all supported files from the source directory.

    Supported formats: .fasta, .fa, .csv, .tsv

    Args:
        source_dir:     path to the source directory
        selected_files: optional list of specific files to load.
                        If None, all supported files are loaded.

    Returns:
        all_records: flat list of all records from all files
        file_profile: list of dicts summarising each loaded file
            (filename, format, number of records loaded)
    """
    all_records = []
    file_profile = []

    # Use selected files if provided, otherwise load all supported files
    if selected_files is not None:
        all_files = sorted(selected_files)
    else:
        # Collect all supported files and sort them alphabetically
        supported_extensions = {".fasta", ".fa", ".csv", ".tsv"}
        all_files = sorted([
            p for p in source_dir.iterdir()
            if p.suffix.lower() in supported_extensions
        ])

    for path in all_files:
        ext = path.suffix.lower()

        # Choose the correct reader based on file extension
        if ext in {".fasta", ".fa"}:
            records = read_fasta(path)
            file_format = "FASTA"
        elif ext in {".csv", ".tsv"}:
            records = read_csv_tsv(path)
            file_format = ext.upper().lstrip(".")
        else:
            # Should not happen due to filtering above, but safety first
            continue

        # Add records to the master list
        all_records.extend(records)

        # Build file profile entry
        file_profile.append({
            "file": path.name,
            "format": file_format,
            "n_records": len(records),
        })

        print(f"  Loaded: {path.name} ({file_format}) — {len(records)} records")

    return all_records, file_profile