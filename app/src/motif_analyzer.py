# app/src/motif_analyzer.py
# Motif search and analysis functions for BioSeq Explorer.
# Searches for DNA motifs in sequences, counts occurrences,
# records positions and compares results across gene groups.
#
# All functions accept a pandas DataFrame with 'sequence' and '_source' columns.

from __future__ import annotations

import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Valid DNA characters for motif input validation
VALID_MOTIF_CHARS = frozenset("ACGTNacgtn")

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_motif(motif: str) -> tuple[bool, str]:
    """Validate a user-supplied motif string.

    Checks that the motif is non-empty and contains only valid DNA characters.

    Args:
        motif: Motif string to validate.

    Returns:
        Tuple (is_valid, message).
        is_valid is True if the motif is acceptable.
        message is an empty string on success or an error description on failure.
    """
    if not motif or not motif.strip():
        return False, "Motif cannot be empty."
    cleaned = motif.strip().upper()
    invalid = set(cleaned) - VALID_MOTIF_CHARS
    if invalid:
        return False, (
            f"Invalid characters in motif: {', '.join(sorted(invalid))}. "
            f"Only A, C, G, T, N are allowed."
        )
    if len(cleaned) < 2:
        return False, "Motif must be at least 2 characters long."
    return True, ""


# ---------------------------------------------------------------------------
# Per-sequence search
# ---------------------------------------------------------------------------

def find_motif_in_sequence(
    sequence: str,
    motif: str,
) -> list[int]:
    """Find all (overlapping) positions of a motif in a single sequence.

    Uses a sliding window to find overlapping matches.

    Args:
        sequence: DNA sequence string (will be uppercased).
        motif:    Motif to search for (will be uppercased).

    Returns:
        List of 1-based start positions where the motif was found.
        Empty list if motif not found.
    """
    sequence = sequence.upper()
    motif = motif.upper()
    positions = []
    start = 0
    while True:
        pos = sequence.find(motif, start)
        if pos == -1:
            break
        positions.append(pos + 1)  # Convert to 1-based position
        start = pos + 1            # Allow overlapping matches
    return positions


# ---------------------------------------------------------------------------
# DataFrame-level search
# ---------------------------------------------------------------------------

def search_motif(
    df: pd.DataFrame,
    motif: str,
) -> pd.DataFrame:
    """Search for a motif in all sequences and return per-record results.

    Args:
        df:    DataFrame with 'id', 'sequence', '_source' columns.
        motif: DNA motif to search for.

    Returns:
        DataFrame with columns:
            id         : sequence identifier
            _source    : gene/source file
            count      : number of occurrences in this sequence
            positions  : comma-separated list of 1-based positions
        Sorted by _source, then by count descending.
        Raises ValueError if required columns are missing.
    """
    required = {"sequence", "id"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    motif = motif.strip().upper()
    rows = []

    for _, record in df.iterrows():
        # str() guards against non-string values (e.g. NaN from blank
        # CSV cells) — intentional, mirrors analyzer.py's approach.
        positions = find_motif_in_sequence(str(record["sequence"]), motif)
        rows.append({
            "id":        record["id"],
            "_source":   record.get("_source", "unknown"),
            "count":     len(positions),
            "positions": ", ".join(str(p) for p in positions) if positions else "—",
        })

    result = pd.DataFrame(rows)
    return result.sort_values(["_source", "count"], ascending=[True, False])


# ---------------------------------------------------------------------------
# Per-gene summary
# ---------------------------------------------------------------------------

def summarize_by_gene(
    search_df: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize motif search results per gene/source.

    Computes total occurrences, number of sequences containing the motif,
    and mean occurrences per sequence for each gene.

    Args:
        search_df: DataFrame produced by search_motif().

    Returns:
        DataFrame with columns:
            Gene / Source      : source file name
            Total occurrences  : sum of all motif counts
            Sequences with motif: number of sequences where count > 0
            Total sequences    : total sequences for this gene
            Mean per sequence  : mean count across all sequences
        Sorted by Total occurrences descending.
    """
    if search_df.empty:
        return pd.DataFrame()

    rows = []
    for source, group in search_df.groupby("_source"):
        total = int(group["count"].sum())
        with_motif = int((group["count"] > 0).sum())
        n_total = len(group)
        mean_per = round(group["count"].mean(), 3)

        # Shorten source label
        label = (source.replace("_sequences.fasta", "")
                       .replace(".fasta", "")
                       .replace(".csv", "")
                       .replace(".tsv", ""))
        rows.append({
            "Gene / Source":       label,
            "Total occurrences":   total,
            "Sequences with motif": with_motif,
            "Total sequences":     n_total,
            "Mean per sequence":   mean_per,
        })

    result = pd.DataFrame(rows)
    return (
        result
        .sort_values("Total occurrences", ascending=False)
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# Multi-motif comparison
# ---------------------------------------------------------------------------

def compare_motifs(
    df: pd.DataFrame,
    motifs: list[str],
) -> pd.DataFrame:
    """Compare multiple motifs — total occurrences per gene for each motif.

    Useful for comparing predefined motifs side by side.

    Args:
        df:     DataFrame with 'id', 'sequence', '_source' columns.
        motifs: List of motif strings to compare.

    Returns:
        DataFrame with genes as rows and motifs as columns,
        values are total occurrences per gene.
    """
    if not motifs:
        return pd.DataFrame()

    sources = sorted(df["_source"].unique()) if "_source" in df.columns else []
    data = {"Gene / Source": [
        s.replace("_sequences.fasta", "").replace(".fasta", "")
         .replace(".csv", "").replace(".tsv", "")
        for s in sources
    ]}

    for motif in motifs:
        motif_upper = motif.strip().upper()
        counts = []
        for source in sources:
            group = df[df["_source"] == source]
            total = sum(
                len(find_motif_in_sequence(str(seq), motif_upper))
                for seq in group["sequence"]
            )
            counts.append(total)
        data[motif_upper] = counts

    return pd.DataFrame(data)