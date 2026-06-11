# BioSeq Explorer — Analysis Report

**Generated:** 2026-06-11 13:12  
**Dataset:** `C:\Users\ewary\PycharmProjects\bioseq_explorer\results\tables\clean_dataset_C.csv`  
**HUBA report:** loaded  

---

## 1. Dataset Summary

| Parameter | Value |
|-----------|-------|
| Total sequences | 6 |
| Gene sources | 2 |
| Flagged sequences | 3 |

## 2. Quality Control — Summary Statistics

| Metric | Mean | Median | Std | Min | Max | Q25 | Q75 |
|--------|------|--------|-----|-----|-----|-----|-----|
| GC content | 30.35% | 30.36% | 7.00% | 23.59% | 38.02% | 23.91% | 36.11% |
| N content | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| Length (bp) | 627249.5 | 550466.0 | 696934.5 | 7022.0 | 1554651.0 | 11873.0 | 1089029.0 |

## 3. Per-Gene Statistics

| Gene / Source | Mean GC% | Mean N% | Mean Length (bp) |
|---------------|----------|---------|-----------------|
| brca1_sequences.fasta | 36.69% | 0.000% | 10262.7 |
| brca2_sequences.fasta | 24.02% | 0.000% | 1244236.3 |

## 4. Visualizations

### GC Content Distribution

![GC Content Distribution](report_plots/gc_distribution.png)

### GC Content by Gene

![GC Content by Gene](report_plots/gc_boxplot.png)

### Sequence Length Distribution

![Sequence Length Distribution](report_plots/length_distribution.png)

### GC% vs. Sequence Length

![GC% vs. Sequence Length](report_plots/gc_vs_length.png)

### N Content Distribution

![N Content Distribution](report_plots/n_content.png)

### Correlation Matrix

![Correlation Matrix](report_plots/correlation_matrix.png)

## 5. Statistical Test Results

_No tests were run._

