# pipeline.py
# Orchestrator module for the HUBA data preparation pipeline.
# Connects cleaner.py and integrator.py into a single callable step.
# Called by main.py for each configuration variant.

from __future__ import annotations
from pathlib import Path

from src.cleaner import clean_records, cleaning_summary
from src.integrator import save_clean_dataset, save_rejected
from src.stats import compute_input_stats, save_csv


# ---------------------------------------------------------------------------
# Single variant pipeline run
# ---------------------------------------------------------------------------

def run_pipeline(
    records: list[dict],
    variant: str,
    params: dict,
    results_dir: Path,
) -> dict:
    """Run the full cleaning and integration pipeline for one variant.

    Steps:
        1. Clean records using variant parameters (cleaner.py)
        2. Save accepted records to clean_dataset_{variant}.csv
        3. Save per-sequence stats after filtering to after_filter_{variant}.csv
        4. Save rejected records to rejected_{variant}.csv
        5. Return summary dict for reporting

    Args:
        records:     list of raw records from load_data.py
        variant:     variant label, e.g. "A", "B" or "C"
        params:      dict with keys: min_len, max_n_pct (from config.py)
        results_dir: base results directory path

    Returns:
        dict with keys: variant, params, total, accepted, rejected
    """
    print(f"\n  [Variant {variant}] "
          f"min_len={params['min_len']}, "
          f"max_n_pct={params['max_n_pct']}")

    # --- Step 1: clean records ---
    accepted, rejected = clean_records(records, **params)

    # --- Step 2: save clean dataset ---
    clean_path = (
        results_dir / "tables" / f"clean_dataset_{variant}.csv"
    )
    save_clean_dataset(accepted, clean_path)

    # --- Step 3: save per-sequence stats after filtering ---
    after_stats = compute_input_stats(accepted)
    save_csv(
        after_stats,
        results_dir / "tables" / f"after_filter_{variant}.csv",
    )
    print(f"  Saved: results/tables/after_filter_{variant}.csv")

    # --- Step 4: save rejected records for audit ---
    rejected_path = (
        results_dir / "tables" / f"rejected_{variant}.csv"
    )
    save_rejected(rejected, rejected_path)

    # --- Step 5: build and print summary ---
    summary = cleaning_summary(accepted, rejected)
    print(f"    accepted: {summary['accepted']}/{summary['total_input']}")
    print(f"    rejected: {summary['rejected']}/{summary['total_input']}")

    # Print rejection reasons breakdown if any records were rejected
    if summary["rejection_reasons"]:
        for reason, count in summary["rejection_reasons"].items():
            print(f"      - {reason}: {count}")

    return {
        "variant": variant,
        "params": params,
        "total": summary["total_input"],
        "accepted": summary["accepted"],
        "rejected": summary["rejected"],
    }