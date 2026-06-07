# config.py
# Central configuration file for BioSeq Explorer.
# All paths, parameters and analysis variants are defined here.

from pathlib import Path

# ---------------------------------------------------------------------------
# Directory paths
# ---------------------------------------------------------------------------

# Directory with raw input files (FASTA, CSV, TSV)
SOURCE_DIR = Path("source")

# Directory where all results are saved
RESULTS_DIR = Path("results")

# Path to the cleaned and integrated output file produced by the pipeline
CLEAN_OUTPUT = RESULTS_DIR / "tables" / "clean_dataset.csv"

# ---------------------------------------------------------------------------
# Analysis variants
# A = lenient filter (exploration, initial review)
# B = standard filter (typical analysis)
# C = strict filter (high-quality sequences, clinical use)
# ---------------------------------------------------------------------------

VARIANTS = {
    "A": {
        "min_len": 10,       # Minimum sequence length in base pairs
        "max_n_pct": 0.5,    # Maximum allowed fraction of N bases (50%)
    },
    "B": {
        "min_len": 20,       # Stricter minimum length
        "max_n_pct": 0.2,    # Stricter N content threshold (20%)
    },
    "C": {
        "min_len": 50,       # Only long sequences accepted
        "max_n_pct": 0.05,   # Very low N tolerance (5%) - clinical quality
    },
}

# ---------------------------------------------------------------------------
# Supported input file formats
# ---------------------------------------------------------------------------

# File extensions that HUBA will attempt to load
SUPPORTED_FORMATS = [".fasta", ".fa", ".csv", ".tsv"]