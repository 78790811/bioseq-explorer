# app/src/orf_analyzer.py
# ORF (Open Reading Frame) identification functions for BioSeq Explorer.
# Finds all ORFs in DNA sequences, computes their lengths and positions,
# and summarizes results per gene group.
#
# An ORF is defined as a sequence starting with ATG and ending with
# a stop codon (TAA, TAG, TGA) in the same reading frame.

from __future__ import annotations

import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Standard start codon
START_CODON = "ATG"

# Standard stop codons
STOP_CODONS = frozenset({"TAA", "TAG", "TGA"})

# Number of reading frames to scan
N_FRAMES = 3

# ---------------------------------------------------------------------------
# Single-sequence ORF finder
# ---------------------------------------------------------------------------

def find_orfs(
    sequence: str,
    min_length: int = 100,
) -> list[dict]:
    """Find all ORFs in a single DNA sequence across 3 reading frames.

    Scans all three forward reading frames (+1, +2, +3).
    An ORF starts at the first ATG and ends at the first in-frame stop codon.
    After a stop codon is found, scanning continues from the next codon
    in the same frame — nested ORFs within a larger ORF are not reported.
    Only ORFs with length >= min_length are reported.

    Args:
        sequence:   DNA sequence string (case-insensitive).
        min_length: Minimum ORF length in base pairs to report (default 100).

    Returns:
        List of dicts, each representing one ORF with keys:
            frame     : int, reading frame (1, 2 or 3)
            start     : int, 1-based start position of ATG
            end       : int, 1-based end position (last base of stop codon)
            length    : int, ORF length in base pairs
            sequence  : str, ORF nucleotide sequence
    """
    sequence = sequence.upper()
    seq_len = len(sequence)
    orfs = []

    for frame in range(N_FRAMES):
        # Walk through the sequence codon by codon in this frame
        i = frame
        in_orf = False
        orf_start = 0

        while i + 3 <= seq_len:
            codon = sequence[i:i + 3]

            if not in_orf:
                # Looking for a start codon
                if codon == START_CODON:
                    in_orf = True
                    orf_start = i
            else:
                # Inside an ORF — looking for a stop codon
                if codon in STOP_CODONS:
                    end = i + 3          # Include the stop codon
                    orf_len = end - orf_start
                    if orf_len >= min_length:
                        orfs.append({
                            "frame":    frame + 1,
                            "start":    orf_start + 1,   # Convert to 1-based
                            "end":      end,
                            "length":   orf_len,
                            "sequence": sequence[orf_start:end],
                        })
                    in_orf = False  # Reset — look for next ATG

            i += 3  # Always advance by one codon in this frame

    # Sort by length descending
    orfs.sort(key=lambda o: o["length"], reverse=True)
    return orfs


# ---------------------------------------------------------------------------
# DataFrame-level ORF analysis
# ---------------------------------------------------------------------------

def run_orf_analysis(
    df: pd.DataFrame,
    min_length: int = 100,
) -> pd.DataFrame:
    """Run ORF analysis on all sequences in a DataFrame.

    For each sequence, finds all ORFs and records the count and
    the longest ORF length.

    Args:
        df:         DataFrame with 'id', 'sequence', '_source' columns.
        min_length: Minimum ORF length to report (default 100 bp).

    Returns:
        DataFrame with columns:
            id            : sequence identifier
            _source       : gene/source file
            n_orfs        : total number of ORFs found
            longest_orf   : length of the longest ORF in bp (0 if none)
            mean_orf_len  : mean ORF length (0.0 if none)
        Raises ValueError if required columns are missing.
    """
    required = {"id", "sequence"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    rows = []
    for _, record in df.iterrows():
        # str() guards against non-string values (e.g. NaN from blank
        # CSV cells) — intentional, mirrors analyzer.py's approach.
        orfs = find_orfs(str(record["sequence"]), min_length=min_length)
        n = len(orfs)
        longest = max((o["length"] for o in orfs), default=0)
        mean_len = round(sum(o["length"] for o in orfs) / n, 1) if n > 0 else 0.0

        rows.append({
            "id":           record["id"],
            "_source":      record.get("_source", "unknown"),
            "n_orfs":       n,
            "longest_orf":  longest,
            "mean_orf_len": mean_len,
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Per-gene summary
# ---------------------------------------------------------------------------

def summarize_by_gene(
    orf_df: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize ORF results per gene/source.

    Args:
        orf_df: DataFrame produced by run_orf_analysis().

    Returns:
        DataFrame with columns:
            Gene / Source      : gene name
            Total ORFs         : sum of all ORFs across sequences
            Mean ORFs/sequence : mean ORF count per sequence
            Mean longest ORF   : mean of the longest ORF per sequence (bp)
            Max ORF length     : longest ORF found in this gene (bp)
        Sorted by Total ORFs descending.
    """
    if orf_df.empty or "_source" not in orf_df.columns:
        return pd.DataFrame()

    rows = []
    for source, group in orf_df.groupby("_source"):
        label = (source.replace("_sequences.fasta", "")
                       .replace(".fasta", "")
                       .replace(".csv", "")
                       .replace(".tsv", ""))
        rows.append({
            "Gene / Source":       label,
            "Total ORFs":          int(group["n_orfs"].sum()),
            "Mean ORFs/sequence":  round(group["n_orfs"].mean(), 2),
            "Mean longest ORF":    round(group["longest_orf"].mean(), 1),
            "Max ORF length (bp)": int(group["longest_orf"].max()),
        })

    result = pd.DataFrame(rows)
    return result.sort_values("Total ORFs", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Detailed ORF list for a single sequence
# ---------------------------------------------------------------------------

def get_sequence_orfs(
    df: pd.DataFrame,
    seq_id: str,
    min_length: int = 100,
) -> list[dict]:
    """Get the full list of ORFs for a specific sequence ID.

    Used when the user clicks a row to see all ORFs in that sequence.

    Args:
        df:         DataFrame with 'id' and 'sequence' columns.
        seq_id:     The sequence ID to look up.
        min_length: Minimum ORF length to report.

    Returns:
        List of ORF dicts (see find_orfs()), or empty list if ID not found.
    """
    matches = df[df["id"] == seq_id]
    if matches.empty:
        return []
    sequence = str(matches.iloc[0]["sequence"])
    return find_orfs(sequence, min_length=min_length)