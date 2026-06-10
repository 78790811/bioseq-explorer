# app/config.py
# Central configuration file for BioSeq Explorer GUI.
# All paths, GUI settings and analysis constants are defined here.

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths to HUBA output files (inputs for BioSeq Explorer)
# ---------------------------------------------------------------------------

# Directory where HUBA saves all results
RESULTS_DIR = Path("results")

# Directory with HUBA-generated tables
TABLES_DIR = RESULTS_DIR / "tables"

# Directory with HUBA-generated plots
PLOTS_DIR = RESULTS_DIR / "plots"

# Pattern for clean dataset files produced by HUBA
# Actual filenames: clean_dataset_A.csv, clean_dataset_B.csv, clean_dataset_C.csv
CLEAN_DATASET_PATTERN = "clean_dataset_*.csv"

# Path to the HUBA summary report
HUBA_REPORT = RESULTS_DIR / "REPORT.md"

# ---------------------------------------------------------------------------
# Output directory for BioSeq Explorer reports and exports
# ---------------------------------------------------------------------------

# Directory where BioSeq Explorer saves generated reports and plots
APP_OUTPUT_DIR = RESULTS_DIR / "app_output"

# ---------------------------------------------------------------------------
# GUI settings
# ---------------------------------------------------------------------------

# Main application window
APP_TITLE = "BioSeq Explorer"
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 720
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 600

# CustomTkinter appearance
APPEARANCE_MODE = "system"       # "system", "light" or "dark"
COLOR_THEME = "blue"             # "blue", "green" or "dark-blue"

# Font sizes
FONT_SIZE_TITLE = 20
FONT_SIZE_HEADER = 14
FONT_SIZE_BODY = 13
FONT_SIZE_SMALL = 11

# ---------------------------------------------------------------------------
# DNA motif analysis — predefined motifs
# ---------------------------------------------------------------------------

# Common regulatory and structural motifs used in motif search tab.
# Keys are display names, values are the motif sequences.
PREDEFINED_MOTIFS = {
    "Start codon (ATG)":     "ATG",
    "TATA box":              "TATAAA",
    "CCAAT box":             "CCAAT",
    "GC box":                "GGGCGG",
    "Kozak consensus":       "GCCACC",
    "Splice donor (GT)":     "GT",
    "Splice acceptor (AG)":  "AG",
    "CpG site":              "CG",
}

# ---------------------------------------------------------------------------
# ORF analysis constants
# ---------------------------------------------------------------------------

# Standard start codon
ORF_START_CODON = "ATG"

# Standard stop codons
ORF_STOP_CODONS = frozenset({"TAA", "TAG", "TGA"})

# Minimum ORF length in base pairs to be reported
ORF_MIN_LENGTH = 100

# ---------------------------------------------------------------------------
# Quality control thresholds
# ---------------------------------------------------------------------------

# GC content warning boundaries (outside this range = flagged)
GC_LOW_THRESHOLD = 0.30    # 30%
GC_HIGH_THRESHOLD = 0.70   # 70%

# N content warning threshold
N_WARNING_THRESHOLD = 0.10  # 10%

# ---------------------------------------------------------------------------
# Statistics settings
# ---------------------------------------------------------------------------

# Significance level for statistical tests
ALPHA = 0.05

# Available statistical tests shown in the Statistics tab
STAT_TESTS = ["t-test", "ANOVA", "Mann-Whitney U"]