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
# CSV / TSV file reader
# ---------------------------------------------------------------------------

def read_csv_tsv(path: Path) -> list[dict]:
    """Read a single CSV or TSV file and return a list of row records.

    Each record is a dictionary where keys are column headers
    and values are the corresponding cell values.
    A '_source' key is added to each record with the filename.
    """
    # Choose delimiter based on file extension
    delimiter = "\t" if path.suffix == ".tsv" else ","

    records = []

    with path.open(mode="r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            # Convert row to regular dict and add source filename
            record = dict(row)
            record["_source"] = path.name
            records.append(record)

    return records


# ---------------------------------------------------------------------------
# Main loader: loads all supported files from a directory
# ---------------------------------------------------------------------------

def load_all_files(source_dir: Path) -> tuple[list[dict], list[dict]]:
    """Load all supported files from the source directory.

    Supported formats: .fasta, .fa, .csv, .tsv

    Returns:
        all_records: flat list of all records from all files
        file_profile: list of dicts summarising each loaded file
            (filename, format, number of records loaded)
    """
    all_records = []
    file_profile = []

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