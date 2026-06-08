# main.py
# Entry point for the HUBA data preparation pipeline.
# Orchestrates loading, cleaning, integration and reporting.
#
# Usage:
#   python main.py --variant A
#   python main.py --variant B
#   python main.py --variant C
#   python main.py --all
#   python main.py --dry-run

from __future__ import annotations
import argparse
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Safety check: make sure the script is run from the correct directory
# ---------------------------------------------------------------------------

if not Path("config.py").exists():
    print("ERROR: Run this script from the bioseq_explorer/ directory.")
    print("  In PyCharm: File -> Open -> select bioseq_explorer folder")
    sys.exit(1)

# Use non-interactive matplotlib backend — saves plots to files, no GUI window
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config
from src.load_data import load_all_files
from src.stats import compute_input_stats, save_csv, save_param_compare
from src.pipeline import run_pipeline


# ---------------------------------------------------------------------------
# Plot generator
# ---------------------------------------------------------------------------

def make_plots(
    records: list[dict],
    results_by_variant: dict,
    results_dir: Path,
) -> None:
    """Generate and save diagnostic plots for the pipeline run.

    Plot 1: bar chart of input sequence lengths (before filtering)
    Plot 2: stacked bar chart comparing accepted/rejected per variant

    Args:
        records:             all raw records from load_data
        results_by_variant:  summary dicts keyed by variant label
        results_dir:         base results directory path
    """
    plots_dir = results_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    # --- Plot 1: distribution of input sequence lengths ---
    lengths = [len(r["sequence"]) for r in records]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(range(len(lengths)), sorted(lengths), color="steelblue")
    ax.set_title("Input sequence lengths")
    ax.set_xlabel("Sequence (sorted)")
    ax.set_ylabel("Length (bp)")

    # Add length value label above each bar
    for i, v in enumerate(sorted(lengths)):
        ax.text(i, v + 0.3, str(v), ha="center", fontsize=9)

    plt.tight_layout()
    fig.savefig(plots_dir / "input_lengths.png", dpi=100)
    plt.close(fig)
    print("  Plot saved: results/plots/input_lengths.png")

    # --- Plot 2: accepted vs rejected per variant ---
    variants = list(results_by_variant.keys())
    accepted = [results_by_variant[v]["accepted"] for v in variants]
    rejected = [results_by_variant[v]["rejected"] for v in variants]

    fig, ax = plt.subplots(figsize=(6, 4))
    x = range(len(variants))

    # Stacked bar: accepted on bottom, rejected on top
    ax.bar(x, accepted, label="Accepted", color="steelblue")
    ax.bar(x, rejected, bottom=accepted, label="Rejected", color="tomato")

    ax.set_xticks(list(x))
    ax.set_xticklabels([f"Variant {v}" for v in variants])
    ax.set_ylabel("Number of sequences")
    ax.set_title("Filter comparison by variant")
    ax.legend()
    plt.tight_layout()
    fig.savefig(plots_dir / "param_compare.png", dpi=100)
    plt.close(fig)
    print("  Plot saved: results/plots/param_compare.png")


# ---------------------------------------------------------------------------
# Report generator
# ---------------------------------------------------------------------------

def save_report(
    file_profile: list[dict],
    results_by_variant: dict,
    results_dir: Path,
) -> None:
    """Generate a Markdown summary report of the pipeline run.

    Args:
        file_profile:        list of dicts describing each input file
        results_by_variant:  summary dicts keyed by variant label
        results_dir:         base results directory path
    """
    lines = [
        "# HUBA — Data Preparation Report",
        "",
        f"Input directory: {config.SOURCE_DIR}",
        f"Files loaded: {len(file_profile)}",
        "",
        "## Input files",
        "",
    ]

    # List each input file with format and record count
    for fp in file_profile:
        lines.append(
            f"- `{fp['file']}` "
            f"({fp['format']}, {fp['n_records']} records)"
        )

    lines.append("")

    # Summary section for each variant
    for variant, data in results_by_variant.items():
        lines += [
            f"## Variant {variant} "
            f"(min_len={data['params']['min_len']}, "
            f"max_n_pct={data['params']['max_n_pct']})",
            "",
            f"- Accepted: {data['accepted']}/{data['total']}",
            f"- Rejected: {data['rejected']}/{data['total']}",
            "",
        ]

    # List all generated artefacts
    lines += [
        "## Artefacts",
        "",
        "- results/tables/file_profile.csv",
        "- results/tables/input_stats.csv",
        "- results/tables/clean_dataset_*.csv",
        "- results/tables/rejected_*.csv",
        "- results/tables/param_compare.csv",
        "- results/plots/input_lengths.png",
        "- results/plots/param_compare.png",
    ]

    report_path = results_dir / "REPORT.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  Saved: {report_path}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Parse command-line arguments and run the HUBA pipeline."""

    # --- Argument parser ---
    parser = argparse.ArgumentParser(
        description="HUBA — data preparation pipeline for BioSeq Explorer"
    )
    parser.add_argument(
        "--variant",
        choices=list(config.VARIANTS.keys()),
        help="Run a single variant (A, B or C)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all variants and generate comparison",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load files and show stats — no filtering or saving",
    )
    args = parser.parse_args()

    # Print help if no argument was given
    if not args.variant and not args.all and not args.dry_run:
        parser.print_help()
        sys.exit(1)

    # --- Create results directories ---
    results_dir = config.RESULTS_DIR
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "tables").mkdir(exist_ok=True)
    (results_dir / "plots").mkdir(exist_ok=True)

    # --- Step 1: Load all input files ---
    print(f"\nLoading files from: {config.SOURCE_DIR}")
    records, file_profile = load_all_files(config.SOURCE_DIR)
    print(f"  Total records loaded: {len(records)}")

    # Save file profile summary
    save_csv(file_profile, results_dir / "tables" / "file_profile.csv")
    print("  Saved: results/tables/file_profile.csv")

    # Dry-run stops here — no filtering or saving
    if args.dry_run:
        print("\n[--dry-run] Stopped before filtering. Data loaded OK.")
        print(f"  Files: {len(file_profile)}, "
              f"records: {len(records)}")
        for fp in file_profile:
            print(f"    {fp['file']} ({fp['format']}): "
                  f"{fp['n_records']} records")
        return

    # --- Step 2: Compute and save input statistics ---
    input_stats = compute_input_stats(records)
    save_csv(input_stats, results_dir / "tables" / "input_stats.csv")
    print("  Saved: results/tables/input_stats.csv")

    # Print per-sequence statistics to terminal
    for row in input_stats:
        print(
            f"    {row['id']:20s}  "
            f"len={row['length']:4d}  "
            f"GC={row['gc_pct']:5.1f}%  "
            f"N={row['n_pct']:5.1f}%"
        )

    # --- Step 3: Run variant(s) ---
    to_run = (
        list(config.VARIANTS.keys()) if args.all
        else [args.variant]
    )

    results_by_variant = {}
    for variant in to_run:
        results_by_variant[variant] = run_pipeline(
            records, variant, config.VARIANTS[variant], results_dir
        )

    # --- Step 4: Save variant comparison table ---
    if len(results_by_variant) > 1:
        save_param_compare(
            results_by_variant,
            results_dir / "tables" / "param_compare.csv",
        )
        print("\n  Saved: results/tables/param_compare.csv")

    # --- Step 5: Generate plots ---
    make_plots(records, results_by_variant, results_dir)

    # --- Step 6: Save report ---
    save_report(file_profile, results_by_variant, results_dir)

    print("\nDone. Check the results/ directory.")


if __name__ == "__main__":
    main()