# main.py
# Entry point for the HUBA data preparation pipeline.
# Orchestrates loading, cleaning, integration and reporting.
#
# Usage:
#   python main.py --variant A        run single variant (A, B or C)
#   python main.py --variant B
#   python main.py --variant C
#   python main.py --all              run all variants
#   python main.py --dry-run          load files only, no filtering
#   python main.py --select           interactively select files to process
#   python main.py --delete           interactively delete files from source/

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
# Interactive file selector
# ---------------------------------------------------------------------------

def list_source_files(source_dir: Path) -> list[Path]:
    """List all supported files in the source directory.

    Returns a sorted list of Path objects for supported file types.
    """
    supported = {".fasta", ".fa", ".csv", ".tsv"}
    return sorted([
        p for p in source_dir.iterdir()
        if p.suffix.lower() in supported
    ])


def select_files_interactive(
    source_dir: Path,
    mode: str = "process",
) -> list[Path]:
    """Interactively display files and let user select which ones to use.

    Args:
        source_dir: path to the source directory
        mode:       "process" — select files to process
                    "delete"  — select files to delete

    Returns:
        list of selected Path objects
    """
    all_files = list_source_files(source_dir)

    if not all_files:
        print("\nNo supported files found in source/ directory.")
        return []

    # --- Display file list ---
    print("\n" + "=" * 60)
    if mode == "delete":
        print("FILE MANAGER — select files to DELETE from source/")
    else:
        print("FILE SELECTOR — select files to process")
    print("=" * 60)

    for i, path in enumerate(all_files, start=1):
        # Show file size in KB for context
        size_kb = path.stat().st_size / 1024
        print(f"  [{i:2d}] {path.name:<40s} {size_kb:8.1f} KB")

    print("=" * 60)

    if mode == "delete":
        print("Enter numbers to DELETE (e.g. 1 3 5), or 'all', or 'none':")
    else:
        print("Enter numbers to PROCESS (e.g. 1 3 5), or 'all', or 'none':")

    # --- Get user input ---
    while True:
        raw = input("> ").strip().lower()

        if raw == "none":
            print("  No files selected.")
            return []

        if raw == "all":
            print(f"  Selected all {len(all_files)} files.")
            return all_files

        # Parse space-separated numbers
        try:
            indices = [int(x) for x in raw.split()]
            selected = []
            valid = True
            for idx in indices:
                if 1 <= idx <= len(all_files):
                    selected.append(all_files[idx - 1])
                else:
                    print(f"  ERROR: {idx} is out of range "
                          f"(1-{len(all_files)}). Try again.")
                    valid = False
                    break
            if valid:
                print(f"  Selected {len(selected)} file(s).")
                return selected
        except ValueError:
            print("  ERROR: Enter numbers separated by spaces, "
                  "'all', or 'none'. Try again.")


def delete_files_interactive(source_dir: Path) -> None:
    """Interactively select and permanently delete files from source/.

    Asks for confirmation before deleting.
    """
    selected = select_files_interactive(source_dir, mode="delete")

    if not selected:
        return

    # --- Show confirmation ---
    print("\nFiles selected for deletion:")
    for path in selected:
        print(f"  - {path.name}")

    print("\nAre you sure you want to permanently delete these files? (yes/no)")
    confirm = input("> ").strip().lower()

    if confirm != "yes":
        print("  Deletion cancelled.")
        return

    # --- Delete files ---
    deleted = 0
    for path in selected:
        try:
            path.unlink()
            print(f"  Deleted: {path.name}")
            deleted += 1
        except OSError as e:
            print(f"  ERROR deleting {path.name}: {e}")

    print(f"\n  Done. {deleted} file(s) deleted from source/.")

# ---------------------------------------------------------------------------
# Plot generator
# ---------------------------------------------------------------------------

def make_plots(
    records: list[dict],
    results_by_variant: dict,
    results_dir: Path,
) -> None:
    """Generate and save diagnostic plots for the pipeline run.

    Plot 1: bar chart of input sequence lengths (log scale)
    Plot 2: stacked bar chart comparing accepted/rejected per variant
    Plot 3: boxplot of GC% distribution per source file
    Plot 4: scatter plot of GC% vs sequence length

    Args:
        records:             all raw records from load_data
        results_by_variant:  summary dicts keyed by variant label
        results_dir:         base results directory path
    """
    plots_dir = results_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    # --- Plot 1: input sequence lengths (log scale, coloured by source) ---

    # Build list of (length, source) pairs sorted by length
    length_source = sorted(
        [(len(r["sequence"]), r.get("_source", "unknown")) for r in records],
        key=lambda x: x[0],
    )
    sorted_lengths = [ls[0] for ls in length_source]
    sorted_sources = [ls[1] for ls in length_source]

    # Assign a colour per source file
    unique_sources = list(dict.fromkeys(sorted_sources))
    color_map_bar = matplotlib.colormaps.get_cmap("tab10").resampled(len(unique_sources))
    source_to_color = {
        src: color_map_bar(i) for i, src in enumerate(unique_sources)
    }
    bar_colors = [source_to_color[s] for s in sorted_sources]

    # Shorten legend labels
    short_legend = {
        src: src.replace("_sequences.fasta", "").replace(".fasta", "")
        for src in unique_sources
    }

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(range(len(sorted_lengths)), sorted_lengths, color=bar_colors)

    # Use logarithmic scale to handle large range of sequence lengths
    ax.set_yscale("log")
    ax.set_title("Input sequence lengths (log scale, coloured by source)")
    ax.set_xlabel("Sequence index (sorted by length)")
    ax.set_ylabel("Length (bp, log scale)")
    ax.set_xticks([])

    # Add legend for source files
    legend_handles = [
        plt.Rectangle((0, 0), 1, 1,
                      color=source_to_color[src],
                      label=short_legend[src])
        for src in unique_sources
    ]
    ax.legend(handles=legend_handles, bbox_to_anchor=(1.01, 1),
              loc="upper left", fontsize=8)

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

    # Add count labels inside each bar segment
    for i, (acc, rej) in enumerate(zip(accepted, rejected)):
        ax.text(i, acc / 2, str(acc), ha="center", va="center",
                color="white", fontsize=10, fontweight="bold")
        if rej > 0:
            ax.text(i, acc + rej / 2, str(rej), ha="center", va="center",
                    color="white", fontsize=10, fontweight="bold")

    ax.set_xticks(list(x))
    ax.set_xticklabels([f"Variant {v}" for v in variants])
    ax.set_ylabel("Number of sequences")
    ax.set_title("Filter comparison by variant")
    ax.legend()
    plt.tight_layout()
    fig.savefig(plots_dir / "param_compare.png", dpi=100)
    plt.close(fig)
    print("  Plot saved: results/plots/param_compare.png")

    # --- Plot 3: GC% distribution per source file (boxplot) ---
    # Group GC% values by source file
    sources: dict[str, list[float]] = {}
    for r in records:
        src = r.get("_source", "unknown")
        gc = (r["sequence"].count("G") + r["sequence"].count("C")) / len(
            r["sequence"]
        ) * 100 if r["sequence"] else 0.0
        sources.setdefault(src, []).append(gc)

    source_labels = list(sources.keys())
    source_data = [sources[s] for s in source_labels]

    # Shorten labels for readability (remove _sequences.fasta suffix)
    short_labels = [
        s.replace("_sequences.fasta", "").replace(".fasta", "")
        for s in source_labels
    ]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.boxplot(source_data, tick_labels=short_labels, patch_artist=True,
               boxprops=dict(facecolor="steelblue", alpha=0.6))
    ax.set_title("GC% distribution per source file")
    ax.set_xlabel("Source file")
    ax.set_ylabel("GC content (%)")

    # Rotate x labels to avoid overlap
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    fig.savefig(plots_dir / "gc_boxplot.png", dpi=100)
    plt.close(fig)
    print("  Plot saved: results/plots/gc_boxplot.png")

    # --- Plot 4: GC% vs sequence length (scatter plot) ---
    gc_values = []
    len_values = []
    colors_scatter = []

    # Assign a colour per source file for visual grouping
    color_map = matplotlib.colormaps.get_cmap("tab10").resampled(len(sources))
    source_color = {
        src: color_map(i) for i, src in enumerate(source_labels)
    }

    for r in records:
        seq = r["sequence"]
        if not seq:
            continue
        gc = (seq.count("G") + seq.count("C")) / len(seq) * 100
        gc_values.append(gc)
        len_values.append(len(seq))
        colors_scatter.append(source_color[r.get("_source", "unknown")])

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.scatter(len_values, gc_values, c=colors_scatter, alpha=0.7,
               edgecolors="grey", linewidths=0.5, s=60)

    # Use log scale on x axis — sequence lengths span several orders of magnitude
    ax.set_xscale("log")
    ax.set_title("GC content vs sequence length")
    ax.set_xlabel("Sequence length (bp, log scale)")
    ax.set_ylabel("GC content (%)")

    # Add legend for source files
    handles = [
        plt.Line2D([0], [0], marker="o", color="w",
                   markerfacecolor=source_color[src], markersize=8,
                   label=src.replace("_sequences.fasta", "").replace(".fasta", ""))
        for src in source_labels
    ]
    ax.legend(handles=handles, bbox_to_anchor=(1.01, 1), loc="upper left",
              fontsize=8)
    plt.tight_layout()
    fig.savefig(plots_dir / "gc_vs_length_scatter.png", dpi=100)
    plt.close(fig)
    print("  Plot saved: results/plots/gc_vs_length_scatter.png")


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

        # List only artefacts that were actually generated
        artefacts = []

        # Tables — always generated
        artefacts += [
            "- results/tables/file_profile.csv",
            "- results/tables/input_stats.csv",
        ]

        # Variant-specific tables
        for v in results_by_variant:
            artefacts.append(f"- results/tables/clean_dataset_{v}.csv")
            artefacts.append(f"- results/tables/after_filter_{v}.csv")

        # Rejected files — only if any rejections occurred
        for v, data in results_by_variant.items():
            if data["rejected"] > 0:
                artefacts.append(f"- results/tables/rejected_{v}.csv")

        # Param compare — only if more than one variant was run
        if len(results_by_variant) > 1:
            artefacts.append("- results/tables/param_compare.csv")

        # Plots — always generated
        artefacts += [
            "- results/plots/input_lengths.png",
            "- results/plots/param_compare.png",
            "- results/plots/gc_boxplot.png",
            "- results/plots/gc_vs_length_scatter.png",
        ]

        lines += ["## Artefacts", ""] + artefacts

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
    parser.add_argument(
        "--select",
        action="store_true",
        help="Interactively select which files to process",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Interactively select and delete files from source/",
    )
    args = parser.parse_args()

    # Print help if no argument was given
    if not any([
        args.variant, args.all, args.dry_run,
        args.select, args.delete,
    ]):
        parser.print_help()
        sys.exit(1)

    # --- Handle --delete mode ---
    if args.delete:
        delete_files_interactive(config.SOURCE_DIR)
        return

    # --- Handle --select mode: load only chosen files ---
    if args.select:
        selected_files = select_files_interactive(config.SOURCE_DIR)
        if not selected_files:
            print("No files selected. Exiting.")
            return
        print(f"\nProcessing {len(selected_files)} selected file(s)...")

        # --- Create results directories and clean previous results ---
        results_dir = config.RESULTS_DIR
        results_dir.mkdir(parents=True, exist_ok=True)

        tables_dir = results_dir / "tables"
        plots_dir = results_dir / "plots"

        # Remove all CSV files from previous pipeline run
        if tables_dir.exists():
            for old_file in tables_dir.glob("*.csv"):
                old_file.unlink()
                print(f"  Removed old result: {old_file.name}")

        # Remove all PNG plots from previous pipeline run
        if plots_dir.exists():
            for old_file in plots_dir.glob("*.png"):
                old_file.unlink()
                print(f"  Removed old plot: {old_file.name}")

        # Remove old report if exists
        old_report = results_dir / "REPORT.md"
        if old_report.exists():
            old_report.unlink()

        # Recreate directories
        tables_dir.mkdir(exist_ok=True)
        plots_dir.mkdir(exist_ok=True)

        print("  Results directory cleared.")

    # --- Step 1: Load all input files ---
    # In --select mode, load only the files chosen by the user
    if args.select:
        records, file_profile = load_all_files(
            config.SOURCE_DIR,
            selected_files=selected_files,
        )
    else:
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
    # In --select mode without --variant or --all, default to all variants
    if args.all or (args.select and not args.variant):
        to_run = list(config.VARIANTS.keys())
    else:
        to_run = [args.variant]

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