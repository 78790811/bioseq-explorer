# generate_test_data.py
# Generates sample CSV and TSV test files for HUBA pipeline testing.
# Simulates data from different laboratories with different column naming
# conventions — exactly the kind of heterogeneous input HUBA is designed for.
#
# Usage:
#   python generate_test_data.py

from __future__ import annotations
import csv
from pathlib import Path


# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path("source")


# ---------------------------------------------------------------------------
# Sample sequence data (derived from real gene sequences)
# ---------------------------------------------------------------------------

# Each entry represents a sequence record with realistic biological data
SAMPLE_SEQUENCES = [
    {
        "gene": "BRCA1",
        "organism": "Homo sapiens",
        "sequence": "ATGATTGCTTTGAATGCAGATGGCATGATTCAGATTCCTGAAGAAGATGATGAAGATCCT",
        "length": 60,
        "gc_pct": 41.7,
    },
    {
        "gene": "BRCA2",
        "organism": "Homo sapiens",
        "sequence": "ATGCCTATTGGATCCAAAGAGAGGCCAACATTTTTTGAAATTTTTAAGAATGCTGATCCC",
        "length": 60,
        "gc_pct": 38.3,
    },
    {
        "gene": "TP53",
        "organism": "Homo sapiens",
        "sequence": "ATGGAGGAGCCGCAGTCAGATCCTAGCGTTGAATCCCAGGACCTGAAACGCACAGATTT",
        "length": 60,
        "gc_pct": 51.7,
    },
    {
        "gene": "CHEK2",
        "organism": "Homo sapiens",
        "sequence": "ATGTCAGTGAAGAAAGAAGCTAAAGAAGAAGATGAAGAGGATGATGATGATGAAGATGAT",
        "length": 60,
        "gc_pct": 38.3,
    },
    {
        "gene": "PALB2",
        "organism": "Homo sapiens",
        "sequence": "ATGAATATTCAGCACATTGCAGATGAAGATGATGAAGAGGAAGATGATGAAGAGGATGAT",
        "length": 61,
        "gc_pct": 38.7,
    },
    {
        "gene": "BRCA1",
        "organism": "Homo sapiens",
        "sequence": "NNNNATGATTGCTTTGAATGCAGATGGCATGATTCAGATTCCTGAAGAAGATGATGAAG",
        "length": 59,
        "gc_pct": 38.9,
    },
    {
        "gene": "TP53",
        "organism": "Homo sapiens",
        "sequence": "ATG",
        "length": 3,
        "gc_pct": 33.3,
    },
]


# ---------------------------------------------------------------------------
# CSV file generators — different column naming conventions
# ---------------------------------------------------------------------------

def generate_lab_a_csv(output_dir: Path) -> None:
    """Generate CSV file simulating data from Laboratory A.

    Column names: gene, organism, sequence
    Represents a clean, well-structured source.
    """
    path = output_dir / "lab_a_sequences.csv"
    rows = [
        {
            "gene": s["gene"],
            "organism": s["organism"],
            "sequence": s["sequence"],
        }
        for s in SAMPLE_SEQUENCES[:3]
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["gene", "organism", "sequence"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Saved: {path} ({len(rows)} records)")


def generate_lab_b_csv(output_dir: Path) -> None:
    """Generate CSV file simulating data from Laboratory B.

    Column names: GeneSymbol, Species, DNASequence
    Represents a source with different column naming convention.
    """
    path = output_dir / "lab_b_sequences.csv"
    rows = [
        {
            "GeneSymbol": s["gene"],
            "Species": s["organism"],
            "DNASequence": s["sequence"],
        }
        for s in SAMPLE_SEQUENCES[2:5]
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["GeneSymbol", "Species", "DNASequence"]
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Saved: {path} ({len(rows)} records)")


def generate_lab_c_csv(output_dir: Path) -> None:
    """Generate CSV file simulating data from Laboratory C.

    Column names: gene_id, seq, notes (with missing values)
    Represents a messy source with non-standard names and missing data.
    """
    path = output_dir / "lab_c_sequences.csv"
    rows = [
        {
            "gene_id": s["gene"],
            "seq": s["sequence"],
            "notes": "",
        }
        for s in SAMPLE_SEQUENCES[4:]
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["gene_id", "seq", "notes"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Saved: {path} ({len(rows)} records)")


# ---------------------------------------------------------------------------
# TSV file generators — tab-separated variants
# ---------------------------------------------------------------------------

def generate_institute_a_tsv(output_dir: Path) -> None:
    """Generate TSV file simulating data from Institute A.

    Column names: accession, dna_sequence, species
    Tab-separated format as exported from a genomics database.
    """
    path = output_dir / "institute_a_sequences.tsv"
    rows = [
        {
            "accession": f"{s['gene']}_001",
            "dna_sequence": s["sequence"],
            "species": s["organism"],
        }
        for s in SAMPLE_SEQUENCES[:4]
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["accession", "dna_sequence", "species"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Saved: {path} ({len(rows)} records)")


def generate_institute_b_tsv(output_dir: Path) -> None:
    """Generate TSV file simulating data from Institute B.

    Column names: ID, SEQUENCE, ORGANISM, GC_PCT
    Tab-separated with additional metadata columns.
    """
    path = output_dir / "institute_b_sequences.tsv"
    rows = [
        {
            "ID": f"{s['gene']}_ref",
            "SEQUENCE": s["sequence"],
            "ORGANISM": s["organism"],
            "GC_PCT": s["gc_pct"],
        }
        for s in SAMPLE_SEQUENCES[2:6]
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["ID", "SEQUENCE", "ORGANISM", "GC_PCT"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Saved: {path} ({len(rows)} records)")


def generate_institute_c_tsv(output_dir: Path) -> None:
    """Generate TSV file simulating data from Institute C.

    Column names: gene_name, nucleotides (minimal columns)
    Tab-separated with only essential fields.
    """
    path = output_dir / "institute_c_sequences.tsv"
    rows = [
        {
            "gene_name": s["gene"],
            "nucleotides": s["sequence"],
        }
        for s in SAMPLE_SEQUENCES[1:5]
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gene_name", "nucleotides"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Saved: {path} ({len(rows)} records)")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Generate all test CSV and TSV files."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("BioSeq Explorer — test data generator")
    print("=" * 60)
    print("\nGenerating CSV files (different column conventions):")
    generate_lab_a_csv(OUTPUT_DIR)
    generate_lab_b_csv(OUTPUT_DIR)
    generate_lab_c_csv(OUTPUT_DIR)

    print("\nGenerating TSV files (tab-separated variants):")
    generate_institute_a_tsv(OUTPUT_DIR)
    generate_institute_b_tsv(OUTPUT_DIR)
    generate_institute_c_tsv(OUTPUT_DIR)

    print("\n" + "=" * 60)
    print("Done. 6 test files generated in source/")
    print("Files include:")
    print("  - Different column naming conventions")
    print("  - Records with N content (will be filtered)")
    print("  - Records too short (will be filtered)")
    print("  - Missing values in some columns")
    print("\nNext step: run  python main.py --all  to test HUBA on these files")
    print("=" * 60)


if __name__ == "__main__":
    main()