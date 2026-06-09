# BioSeq Explorer

A bioinformatics platform for integration, standardisation and analysis
of disease-associated gene sequences.

BioSeq Explorer consists of two components:
- **HUBA** — a terminal-based data preparation pipeline (ETL)
- **BioSeq Explorer App** — a GUI-based analytical tool (in development)

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
├── source/                   ← input files (FASTA, CSV, TSV)
├── results/
│   ├── tables/               ← CSV output files
│   ├── plots/                ← PNG charts
│   └── REPORT.md             ← auto-generated pipeline report
├── src/
│   ├── load_data.py          ← file loader (FASTA, CSV, TSV)
│   ├── cleaner.py            ← sequence validation and filtering
│   ├── integrator.py         ← standardisation and CSV export
│   ├── pipeline.py           ← orchestrator (connects all modules)
│   └── stats.py              ← statistics, plots, CSV utilities
├── main.py                   ← HUBA entry point
├── fetch_ncbi.py             ← download sequences from NCBI
├── generate_test_data.py     ← generate CSV/TSV test files
├── config.py                 ← all paths and parameters
└── requirements.txt
```

## Installation

**Requirements:** Python 3.11+

```bash
pip install -r requirements.txt
```

---

## HUBA — quick start

### 1. Download sequences from NCBI

```bash
python fetch_ncbi.py
```

Downloads FASTA sequences for BRCA1, BRCA2, TP53, CHEK2 and PALB2
into `source/`. Skips files that already exist.

To re-download a gene, delete its file from `source/` and run again.

### 2. (Optional) Generate CSV and TSV test files

```bash
python generate_test_data.py
```

Creates 6 test files in `source/` simulating data from different
laboratories with varying column naming conventions.

### 3. Run the pipeline

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

---

## Filter variants

HUBA supports three filtering variants defined in `config.py`:

| Variant | `min_len` | `max_n_pct` | Use case |
|---------|-----------|-------------|----------|
| A | 10 bp | 50% | Lenient — exploration and initial review |
| B | 20 bp | 20% | Standard — typical analysis |
| C | 50 bp | 5% | Strict — high-quality sequences, clinical use |

You can add your own variant by editing `VARIANTS` in `config.py`:

```python
VARIANTS = {
    ...
    "D": {
        "min_len": 100,
        "max_n_pct": 0.01,
    },
}
```

---

## Supported input formats

HUBA automatically detects and loads:

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

---

## Output files

After running the pipeline, the following files are generated:

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

## Sequence validation rules

HUBA applies four rejection rules in order:

1. **EMPTY_SEQUENCE** — sequence is empty
2. **INVALID_CHARACTERS** — sequence contains characters other than A, T, G, C, N
3. **TOO_SHORT** — sequence length is below `min_len`
4. **HIGH_N** — proportion of N bases exceeds `max_n_pct`

---

## Data sources

- **NCBI Nucleotide** — primary source, downloaded via Biopython Entrez API
- **Custom files** — any FASTA, CSV or TSV file placed in `source/`

---

## Future development

The following extensions are planned or possible:

- **Ensembl integration** — download sequences via Ensembl REST API
  as an alternative to NCBI
- **XLSX support** — load Excel files as an additional input format
- **Database backend** — store cleaned datasets in SQLite for
  faster repeated analysis
- **Extended analysis** — ORF detection, motif search, sequence
  alignment using Biopython
- **BioSeq Explorer App** — GUI-based analytical tool for interactive
  exploration of cleaned datasets (in development)

---

## Requirements

```
matplotlib>=3.7
biopython>=1.83
pandas>=2.0
numpy>=1.26
scipy>=1.11
```

---

## Repository

Maintained on GitHub with commits after each development step.
Run `git log --oneline` to see the full development history.