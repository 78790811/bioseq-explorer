# app/src/analyzer.py
# Sequence analysis functions for BioSeq Explorer.
# Computes GC content, N content, sequence length and basic statistics
# used in the Quality Control tab.
#
# All functions accept a pandas DataFrame with at least a 'sequence' column
# and return a new DataFrame or a scalar value — no side effects.

from __future__ import annotations

import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Valid DNA base characters (uppercase)
ALLOWED_BASES = frozenset("ACGTN")

# Bases counted as GC
GC_BASES = frozenset("GC")

# ---------------------------------------------------------------------------
# Per-sequence metrics
# ---------------------------------------------------------------------------

def compute_gc_content(sequence: str) -> float:
    """Compute GC content for a single DNA sequence.

    GC content = (count of G + count of C) / total length of sequence.
    Returns 0.0 for empty sequences to avoid division by zero.

    Args:
        sequence: DNA sequence string (case-insensitive).

    Returns:
        GC content as a float in range [0.0, 1.0].
    """
    sequence = sequence.upper()
    total = len(sequence)
    if total == 0:
        return 0.0
    gc_count = sum(1 for base in sequence if base in GC_BASES)
    return gc_count / total


def compute_n_content(sequence: str) -> float:
    """Compute N content (fraction of unknown bases) for a single sequence.

    N content = count of 'N' bases / total length of sequence.
    Returns 0.0 for empty sequences.

    Args:
        sequence: DNA sequence string (case-insensitive).

    Returns:
        N content as a float in range [0.0, 1.0].
    """
    sequence = sequence.upper()
    total = len(sequence)
    if total == 0:
        return 0.0
    return sequence.count("N") / total


def compute_length(sequence: str) -> int:
    """Return the length of a DNA sequence in base pairs.

    Args:
        sequence: DNA sequence string.

    Returns:
        Integer length of the sequence.
    """
    return len(sequence)


# ---------------------------------------------------------------------------
# DataFrame-level analysis
# ---------------------------------------------------------------------------

def run_quality_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Compute QC metrics for all sequences in a DataFrame.

    Adds three new columns to a copy of the input DataFrame:
        - gc_content : float, GC fraction [0.0, 1.0]
        - n_content  : float, N fraction  [0.0, 1.0]
        - length     : int,   sequence length in bp

    Args:
        df: DataFrame with at least a 'sequence' column.

    Returns:
        New DataFrame with the three additional metric columns.
        Raises ValueError if the 'sequence' column is missing, or if any
        row's sequence value isn't a usable string (e.g. an empty CSV
        cell that pandas read in as NaN/float instead of text).
    """
    if "sequence" not in df.columns:
        raise ValueError(
            "Input DataFrame must contain a 'sequence' column."
        )

    result = df.copy()

    # Catch non-string sequence values up front, with a message that
    # names which rows are affected. Without this check, a blank CSV
    # cell becomes a float NaN, and compute_gc_content()'s call to
    # sequence.upper() fails several layers down inside .apply() with
    # a bare "'float' object has no attribute 'upper'" — accurate, but
    # meaningless to anyone reading it without already knowing the cause.
    invalid_mask = ~result["sequence"].apply(lambda v: isinstance(v, str))
    if invalid_mask.any():
        bad_rows = result.loc[invalid_mask]
        count = len(bad_rows)
        if "id" in bad_rows.columns:
            ids = bad_rows["id"].astype(str).head(5).tolist()
            id_list = ", ".join(ids)
            if count > 5:
                id_list += f", and {count - 5} more"
            row_desc = f"rows: {id_list}"
        else:
            row_desc = f"{count} row(s)"
        raise ValueError(
            f"The 'sequence' column contains {count} empty or non-text "
            f"value(s) ({row_desc}). Check the source CSV for blank "
            f"cells in that column and reload the dataset."
        )

    # Apply per-sequence functions to every row
    result["gc_content"] = result["sequence"].apply(compute_gc_content)
    result["n_content"] = result["sequence"].apply(compute_n_content)
    result["length"] = result["sequence"].apply(compute_length)

    return result


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------

def compute_summary_stats(qc_df: pd.DataFrame) -> pd.DataFrame:
    """Compute summary statistics for GC%, N% and length across all sequences.

    Produces a table with one row per metric and columns:
        mean, median, std, min, max, q25, q75

    Args:
        qc_df: DataFrame produced by run_quality_analysis(),
               must contain 'gc_content', 'n_content', 'length' columns.

    Returns:
        DataFrame with summary statistics, indexed by metric name.
        Raises ValueError if required columns are missing.
    """
    required = {"gc_content", "n_content", "length"}
    missing = required - set(qc_df.columns)
    if missing:
        raise ValueError(
            f"Missing columns for summary statistics: {missing}. "
            "Run run_quality_analysis() first."
        )

    metrics = {
        "GC content": qc_df["gc_content"],
        "N content":  qc_df["n_content"],
        "Length (bp)": qc_df["length"],
    }

    rows = []
    for name, series in metrics.items():
        rows.append({
            "Metric":  name,
            "Mean":    round(series.mean(), 4),
            "Median":  round(series.median(), 4),
            "Std":     round(series.std(), 4),
            "Min":     round(series.min(), 4),
            "Max":     round(series.max(), 4),
            "Q25":     round(series.quantile(0.25), 4),
            "Q75":     round(series.quantile(0.75), 4),
        })

    return pd.DataFrame(rows).set_index("Metric")


# ---------------------------------------------------------------------------
# Per-gene group statistics
# ---------------------------------------------------------------------------

def compute_gene_stats(qc_df: pd.DataFrame) -> pd.DataFrame:
    """Compute mean GC%, N% and length grouped by source file (gene).

    Groups sequences by the '_source' column (e.g. brca1_sequences.fasta)
    and computes mean values for each QC metric per group.

    Args:
        qc_df: DataFrame produced by run_quality_analysis(),
               must contain 'gc_content', 'n_content', 'length', '_source'.

    Returns:
        DataFrame grouped by '_source' with mean metric columns.
        Returns empty DataFrame if '_source' column is missing.
    """
    if "_source" not in qc_df.columns:
        return pd.DataFrame()

    grouped = (
        qc_df
        .groupby("_source")[["gc_content", "n_content", "length"]]
        .mean()
        .round(4)
        .reset_index()
    )
    grouped.rename(columns={"_source": "Gene / Source"}, inplace=True)
    return grouped


# ---------------------------------------------------------------------------
# QC flag helpers
# ---------------------------------------------------------------------------

def flag_outliers(
    qc_df: pd.DataFrame,
    gc_low: float = 0.30,
    gc_high: float = 0.70,
    n_warning: float = 0.10,
) -> pd.DataFrame:
    """Add a 'qc_flag' column marking sequences that fall outside QC thresholds.

    Flag values:
        'OK'      — sequence passes all thresholds
        'GC_LOW'  — GC content below gc_low
        'GC_HIGH' — GC content above gc_high
        'HIGH_N'  — N content above n_warning
        Multiple flags are joined with '|' (e.g. 'GC_LOW|HIGH_N')

    Args:
        qc_df:      DataFrame produced by run_quality_analysis().
        gc_low:     Lower GC content threshold (default 0.30).
        gc_high:    Upper GC content threshold (default 0.70).
        n_warning:  N content warning threshold (default 0.10).

    Returns:
        Copy of qc_df with an additional 'qc_flag' column.
    """
    result = qc_df.copy()
    flags = pd.Series([""] * len(result), index=result.index)

    flags = flags.where(
        result["gc_content"] >= gc_low,
        flags + "GC_LOW|",
    )
    flags = flags.where(
        result["gc_content"] <= gc_high,
        flags + "GC_HIGH|",
    )
    flags = flags.where(
        result["n_content"] <= n_warning,
        flags + "HIGH_N|",
    )

    # Strip trailing '|' and replace empty string with 'OK'
    result["qc_flag"] = flags.str.rstrip("|").replace("", "OK")

    return result