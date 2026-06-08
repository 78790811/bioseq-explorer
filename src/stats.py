# stats.py
# Statistical helper functions for BioSeq Explorer.
# Provides sequence statistics, CSV export utilities
# and variant comparison reporting.
# Used by main.py and pipeline.py.

from __future__ import annotations
import csv
from pathlib import Path


# ---------------------------------------------------------------------------
# Sequence statistics
# ---------------------------------------------------------------------------

def gc_content(seq: str) -> float:
    """Calculate GC content as a fraction (0.0 to 1.0).

    GC content is the proportion of G and C bases in the sequence.
    Returns 0.0 if the sequence is empty.
    """
    # Guard against empty sequence to avoid division by zero
    if not seq:
        return 0.0

    # Count G and C bases divided by total length
    return (seq.count("G") + seq.count("C")) / len(seq)


def n_content(seq: str) -> float:
    """Calculate N content as a fraction (0.0 to 1.0).

    N content is the proportion of unknown bases in the sequence.
    Returns 0.0 if the sequence is empty.
    """
    # Guard against empty sequence to avoid division by zero
    if not seq:
        return 0.0

    # Count N bases divided by total length
    return seq.count("N") / len(seq)


# ---------------------------------------------------------------------------
# Input statistics
# ---------------------------------------------------------------------------

def compute_input_stats(records: list[dict]) -> list[dict]:
    """Compute per-sequence statistics for a list of records.

    For each record calculates: length, GC% and N%.
    Used to generate input_stats.csv before filtering.

    Args:
        records: list of sequence records from load_data.py

    Returns:
        list of dicts with columns: id, source, length, gc_pct, n_pct
    """
    rows = []
    for r in records:
        seq = r["sequence"]
        row = {
            "id": r["id"],
            "source": r.get("_source", ""),
            "length": len(seq),
            # Multiply by 100 and round to 1 decimal for percentage display
            "gc_pct": round(gc_content(seq) * 100, 1),
            "n_pct": round(n_content(seq) * 100, 1),
        }
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# CSV export utility
# ---------------------------------------------------------------------------

def save_csv(rows: list[dict], path: Path) -> None:
    """Save a list of dicts to a CSV file.

    Creates parent directories automatically.
    Does nothing if the rows list is empty.

    Args:
        rows: list of dicts — all dicts must have the same keys
        path: full path to the output CSV file
    """
    # Do not create an empty file
    if not rows:
        return

    # Create parent directories if they do not exist
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open(mode="w", encoding="utf-8", newline="") as f:
        # Use keys from the first row as column headers
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------------------
# Variant comparison
# ---------------------------------------------------------------------------

def save_param_compare(
    results_by_variant: dict,
    out_path: Path,
) -> None:
    """Save a comparison table of results across all variants to CSV.

    Each row represents one variant with its parameters and counts.

    Args:
        results_by_variant: dict keyed by variant label (e.g. "A", "B", "C")
                            each value is a dict with keys:
                            params, total, accepted, rejected
        out_path: full path to the output CSV file
    """
    rows = []
    for variant, data in results_by_variant.items():
        rows.append({
            "variant": variant,
            "min_len": data["params"]["min_len"],
            "max_n_pct": data["params"]["max_n_pct"],
            "total_input": data["total"],
            "accepted": data["accepted"],
            "rejected": data["rejected"],
            # Calculate acceptance rate as percentage
            "accepted_pct": round(
                data["accepted"] / data["total"] * 100, 1
            ) if data["total"] else 0,
        })

    # Reuse save_csv utility to write the comparison table
    save_csv(rows, out_path)