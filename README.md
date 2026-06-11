# BioSeq Explorer

A bioinformatics platform for integration, standardisation and analysis
of disease-associated gene sequences.

BioSeq Explorer consists of two components:
- **HUBA** — a terminal-based data preparation pipeline (ETL)
- **BioSeq Explorer App** — a GUI-based analytical tool

---

## Biological question

> Can genes associated with a specific disease display common sequence
> features identifiable by bioinformatic methods?

The first case study focuses on genes associated with breast cancer:
BRCA1, BRCA2, TP53, CHEK2 and PALB2.

---

## Project structure

```
bioseq_explorer/
├── app/                      ← BioSeq Explorer GUI
│   ├── main.py               ← main application window (tabbed layout)
│   ├── config.py             ← GUI configuration and analysis constants
│   └── src/
│       ├── analyzer.py       ← GC%, N%, sequence length metrics
│       ├── motif_analyzer.py ← motif search (predefined and custom)
│       ├── orf_analyzer.py   ← ORF identification (3 forward frames)
│       ├── plots.py          ← matplotlib visualisations
│       ├── stats.py          ← statistical tests and correlation
│       └── report.py         ← Markdown report generation
├── source/                   ← input files (FASTA, CSV, TSV)
├── results/
│   ├── tables/               ← CSV output files from HUBA
│   ├── plots/                ← PNG charts from HUBA
│   ├── app_output/           ← reports and plots from BioSeq Explorer
│   └── REPORT.md             ← auto-generated pipeline report
├── src/                      ← HUBA modules
│   ├── load_data.py          ← file loader (FASTA, CSV, TSV)
│   ├── cleaner.py            ← sequence validation and filtering
│   ├── integrator.py         ← standardisation and CSV export
│   ├── pipeline.py           ← orchestrator (connects all modules)
│   └── stats.py              ← statistics, plots, CSV utilities
├── tests/
│   └── verify_orfs.py        ← ORF algorithm verification (Biopython)
├── run.py                    ← launcher window
├── main.py                   ← HUBA entry point
├── fetch_ncbi.py             ← download sequences from NCBI
├── generate_test_data.py     ← generate CSV/TSV test files
├── config.py                 ← HUBA paths and parameters
└── requirements.txt
```

---

## Installation

**Requirements:** Python 3.11+

```bash
pip install -r requirements.txt
```

---

## Quick start

### 1. Launch the application

```bash
python run.py
```

Opens the launcher window with two options:
- **Run HUBA Pipeline** — prepare and clean input data
- **Open BioSeq Explorer** — open the analytical GUI

### 2. Download sequences from NCBI

```bash
python fetch_ncbi.py
```

Downloads FASTA sequences for BRCA1, BRCA2, TP53, CHEK2 and PALB2
into `source/`. Skips files that already exist.

### 3. (Optional) Generate CSV and TSV test files

```bash
python generate_test_data.py
```

Creates 6 test files in `source/` simulating data from different
laboratories with varying column naming conventions.

---

## HUBA pipeline

### Run commands

```bash
# Check that files load correctly (no filtering or saving)
python main.py --dry-run

# Run a single variant
python main.py --variant A
python main.py --variant B
python main.py --variant C

# Run all variants and generate comparison
python main.py --all

# Interactively select which files to process
python main.py --select

# Interactively delete files from source/
python main.py --delete
```

### Filter variants

| Variant | `min_len` | `max_n_pct` | Use case |
|---------|-----------|-------------|----------|
| A | 10 bp | 50% | Lenient — exploration and initial review |
| B | 20 bp | 20% | Standard — typical analysis |
| C | 50 bp | 5% | Strict — high-quality sequences, clinical use |

### Supported input formats

| Format | Extensions | Notes |
|--------|------------|-------|
| FASTA | `.fasta`, `.fa` | Standard nucleotide sequence format |
| CSV | `.csv` | Comma-separated, various column conventions |
| TSV | `.tsv` | Tab-separated, various column conventions |

Column names are automatically mapped to canonical names:

| Canonical | Accepted variants |
|-----------|-------------------|
| `id` | gene, GeneSymbol, gene_id, gene_name, accession, ID |
| `sequence` | DNASequence, dna_sequence, seq, nucleotides, Sequence |
| `organism` | organism, species, org |

### Sequence validation rules

1. **EMPTY_SEQUENCE** — sequence is empty
2. **INVALID_CHARACTERS** — sequence contains characters other than A, T, G, C, N
3. **TOO_SHORT** — sequence length is below `min_len`
4. **HIGH_N** — proportion of N bases exceeds `max_n_pct`

### Output files

| File | Description |
|------|-------------|
| `results/tables/file_profile.csv` | Summary of loaded input files |
| `results/tables/input_stats.csv` | Per-sequence GC%, N% and length |
| `results/tables/clean_dataset_{A\|B\|C}.csv` | Accepted sequences per variant |
| `results/tables/after_filter_{A\|B\|C}.csv` | Stats after filtering |
| `results/tables/rejected_{A\|B\|C}.csv` | Rejected sequences with reasons |
| `results/tables/param_compare.csv` | Variant comparison table |
| `results/plots/input_lengths.png` | Sequence length distribution |
| `results/plots/param_compare.png` | Accepted vs rejected per variant |
| `results/plots/gc_boxplot.png` | GC% distribution per source file |
| `results/plots/gc_vs_length_scatter.png` | GC% vs sequence length |
| `results/REPORT.md` | Auto-generated pipeline summary |

---

## BioSeq Explorer App

A GUI analytical tool built with CustomTkinter. Launch via `python run.py`.

### Tabs

| Tab | Functionality |
|-----|---------------|
| **Home** | Load `clean_dataset_*.csv`, preview data, display HUBA report |
| **Quality Control** | GC%, N%, sequence length — table, flags, 5 plots |
| **Motif Analysis** | Search predefined or custom motifs, per-gene comparison |
| **ORF Analysis** | Identify open reading frames, per-gene summary, plots |
| **Statistics** | t-test, ANOVA, Mann-Whitney U, correlation matrix |
| **Report** | Generate Markdown report with all plots and statistics |

### ORF analysis — scope note

The ORF module scans **3 forward reading frames (+1, +2, +3) only**.
This is intentional: the primary input sequences are mRNA transcripts
(NCBI accessions prefixed with `NM_`), which are single-stranded and
read in one direction. Reverse strand scanning (`-1, -2, -3`) is
relevant for genomic DNA but would produce misleading results for mRNA.

The algorithm was independently verified against Biopython — all 23
test sequences produced identical ORF counts and positions
(see `tests/verify_orfs.py`).

---

## Tests

```bash
# Verify ORF algorithm against independent Biopython implementation
python tests/verify_orfs.py

# With custom minimum ORF length
python tests/verify_orfs.py --min-len 300

# For a single gene
python tests/verify_orfs.py --gene brca1
```

---

## Future development

The following extensions are planned or possible:

### Analysis extensions
- **Reverse strand ORF scanning** — extend `orf_analyzer.py` with a
  `both_strands=True` parameter and `reverse_complement()` helper for
  analysis of genomic DNA sequences (prefixed `NC_`, `CM_`). The
  scaffolding is documented in `app/src/orf_analyzer.py`.
- **Six-frame translation** — full six-frame ORF analysis matching
  NCBI ORFfinder output
- **Sequence alignment** — pairwise and multiple sequence alignment
  using Biopython `pairwise2` or `Bio.Align`
- **Codon usage analysis** — codon frequency tables per gene

### Data sources
- **Ensembl integration** — download sequences via Ensembl REST API
  as an alternative to NCBI
- **UniProt integration** — link identified ORFs to protein records

### Input/output
- **XLSX support** — load Excel files as an additional input format
- **PDF report export** — export the analysis report as PDF
  in addition to Markdown
- **Report customisation** — user-selectable sections and plot styles

### Infrastructure
- **Database backend** — store cleaned datasets in SQLite for
  faster repeated analysis
- **Extended test suite** — unit tests for all analysis modules
  using pytest

---

## Data sources

- **NCBI Nucleotide** — primary source, downloaded via Biopython Entrez API
- **Custom files** — any FASTA, CSV or TSV file placed in `source/`

---

## Requirements

```
matplotlib>=3.7
biopython>=1.83
pandas>=2.0
numpy>=1.26
scipy>=1.11
customtkinter>=5.2.2
```

---

## Repository

Maintained on GitHub with commits after each development step.
Run `git log --oneline` to see the full development history.