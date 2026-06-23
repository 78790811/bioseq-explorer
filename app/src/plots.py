# app/src/plots.py
# Plot generation functions for BioSeq Explorer.
# All functions return a matplotlib Figure object.
# Figures can be embedded in the GUI (FigureCanvasTkAgg)
# or opened in a standalone matplotlib window with toolbar.
#
# Usage pattern:
#   fig = plot_gc_distribution(qc_df)
#   open_plot_window(fig, title="GC Distribution")

from __future__ import annotations

import tkinter as tk

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Color palette for gene groups (up to 10 distinct genes)
GENE_COLORS = [
    "#1F6AA5", "#E05A2B", "#2CA02C", "#9467BD",
    "#8C564B", "#E377C2", "#7F7F7F", "#BCBD22",
    "#17BECF", "#D62728",
]

# Default figure size for embedded (in-tab) plots
EMBED_FIGSIZE = (5.5, 3.8)

# Default figure size for standalone popup window plots
POPUP_FIGSIZE = (8.0, 5.5)

# DPI for all figures
FIGURE_DPI = 100

# ---------------------------------------------------------------------------
# Standalone plot window
# ---------------------------------------------------------------------------

def open_plot_window(fig: Figure, title: str = "Plot") -> None:
    """Open a matplotlib figure in a standalone Tk window with toolbar.

    The toolbar provides zoom, pan, and save-to-disk functionality.
    The window is independent — closing it does not affect the main app.

    Args:
        fig:   Matplotlib Figure object to display.
        title: Window title string.

    Returns:
        None
    """
    window = tk.Toplevel()
    window.title(title)
    window.geometry("860x620")

    # Center on screen
    window.update_idletasks()
    x = (window.winfo_screenwidth() - 860) // 2
    y = (window.winfo_screenheight() - 620) // 2
    window.geometry(f"860x620+{x}+{y}")

    # Embed figure in the window
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    # Navigation toolbar (zoom, pan, save)
    toolbar_frame = tk.Frame(window)
    toolbar_frame.pack(fill="x")
    toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
    toolbar.update()


# ---------------------------------------------------------------------------
# Embed helper
# ---------------------------------------------------------------------------

def embed_figure(
    fig: Figure,
    parent: tk.Widget,
) -> FigureCanvasTkAgg:
    """Embed a matplotlib Figure into a tkinter parent widget.

    Args:
        fig:    Matplotlib Figure to embed.
        parent: Tkinter widget to embed the figure into.

    Returns:
        FigureCanvasTkAgg instance (needed to call .draw() after updates).
    """
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
    return canvas


# ---------------------------------------------------------------------------
# QC plots
# ---------------------------------------------------------------------------

def plot_gc_distribution(
    qc_df: pd.DataFrame,
    figsize: tuple[float, float] = EMBED_FIGSIZE,
) -> Figure:
    """Plot GC content distribution as a histogram with per-gene overlay.

    Shows overall GC% distribution as a filled histogram.
    Vertical dashed lines mark the 30% and 70% warning thresholds.

    Args:
        qc_df:   DataFrame with 'gc_content' and '_source' columns,
                 produced by analyzer.run_quality_analysis().
        figsize: Figure dimensions (width, height) in inches.

    Returns:
        Matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=FIGURE_DPI)
    fig.patch.set_facecolor("#F5F5F5")
    ax.set_facecolor("#FAFAFA")

    gc_pct = qc_df["gc_content"] * 100

    ax.hist(
        gc_pct,
        bins=30,
        color=GENE_COLORS[0],
        alpha=0.75,
        edgecolor="white",
        linewidth=0.5,
    )

    # Warning threshold lines
    ax.axvline(30, color="#E05A2B", linestyle="--", linewidth=1.2,
               label="30% threshold")
    ax.axvline(70, color="#E05A2B", linestyle="--", linewidth=1.2,
               label="70% threshold")

    ax.set_xlabel("GC content (%)", fontsize=11)
    ax.set_ylabel("Number of sequences", fontsize=11)
    ax.set_title("GC Content Distribution", fontsize=13, fontweight="bold", pad=10)
    ax.legend(fontsize=9)
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))

    fig.tight_layout()
    return fig


def plot_gc_boxplot(
    qc_df: pd.DataFrame,
    figsize: tuple[float, float] = EMBED_FIGSIZE,
) -> Figure:
    """Plot GC content per gene as a grouped boxplot.

    Each box represents one source file (gene).
    Useful for comparing GC% distributions across genes.

    Args:
        qc_df:   DataFrame with 'gc_content' and '_source' columns.
        figsize: Figure dimensions in inches.

    Returns:
        Matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=FIGURE_DPI)
    fig.patch.set_facecolor("#F5F5F5")
    ax.set_facecolor("#FAFAFA")

    if "_source" not in qc_df.columns:
        ax.text(0.5, 0.5, "No '_source' column found.",
                ha="center", va="center", transform=ax.transAxes)
        return fig

    sources = sorted(qc_df["_source"].unique())
    data = [qc_df.loc[qc_df["_source"] == s, "gc_content"] * 100
            for s in sources]

    bp = ax.boxplot(
        data,
        patch_artist=True,
        medianprops=dict(color="white", linewidth=2),
        whiskerprops=dict(linewidth=1.2),
        capprops=dict(linewidth=1.2),
        flierprops=dict(marker="o", markersize=3, alpha=0.5),
    )

    for patch, color in zip(bp["boxes"], GENE_COLORS):
        patch.set_facecolor(color)
        patch.set_alpha(0.8)

    # Shorten source labels (remove path and extension)
    labels = [s.replace("_sequences.fasta", "").replace(".fasta", "")
               .replace(".csv", "").replace(".tsv", "")
               for s in sources]
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=9)
    ax.set_ylabel("GC content (%)", fontsize=11)
    ax.set_title("GC Content by Gene", fontsize=13, fontweight="bold", pad=10)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.axhline(30, color="#E05A2B", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.axhline(70, color="#E05A2B", linestyle="--", linewidth=0.8, alpha=0.6)

    # Y axis: compute bounds directly from actual data min/max across all
    # genes, with a flat padding margin. Using global IQR here was the bug —
    # genes with very different GC% (e.g. brca2 ~24% vs tp53 ~55%) skewed
    # the statistical whisker estimate so far that the lowest box (brca2)
    # was cut off below the computed bottom of the y-axis.
    all_gc = qc_df["gc_content"] * 100
    data_min = all_gc.min()
    data_max = all_gc.max()
    span = max(data_max - data_min, 1.0)  # avoid zero-span edge case
    margin = span * 0.15
    ax.set_ylim(
        bottom=max(0, data_min - margin),
        top=min(100, data_max + margin),
    )

    fig.tight_layout()
    return fig


def plot_length_distribution(
    qc_df: pd.DataFrame,
    figsize: tuple[float, float] = EMBED_FIGSIZE,
) -> Figure:
    """Plot sequence length distribution as a histogram.

    Args:
        qc_df:   DataFrame with 'length' column.
        figsize: Figure dimensions in inches.

    Returns:
        Matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=FIGURE_DPI)
    fig.patch.set_facecolor("#F5F5F5")
    ax.set_facecolor("#FAFAFA")

    ax.hist(
        qc_df["length"],
        bins=30,
        color=GENE_COLORS[2],
        alpha=0.75,
        edgecolor="white",
        linewidth=0.5,
    )

    ax.set_xlabel("Sequence length (bp)", fontsize=11)
    ax.set_ylabel("Number of sequences", fontsize=11)
    ax.set_title("Sequence Length Distribution", fontsize=13,
                 fontweight="bold", pad=10)

    fig.tight_layout()
    return fig


def plot_gc_vs_length(
    qc_df: pd.DataFrame,
    figsize: tuple[float, float] = EMBED_FIGSIZE,
) -> Figure:
    """Plot GC content vs. sequence length as a scatter plot, colored by gene.

    Args:
        qc_df:   DataFrame with 'gc_content', 'length', '_source' columns.
        figsize: Figure dimensions in inches.

    Returns:
        Matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=FIGURE_DPI)
    fig.patch.set_facecolor("#F5F5F5")
    ax.set_facecolor("#FAFAFA")

    if "_source" in qc_df.columns:
        sources = sorted(qc_df["_source"].unique())
        for i, source in enumerate(sources):
            mask = qc_df["_source"] == source
            label = (source.replace("_sequences.fasta", "")
                           .replace(".fasta", "")
                           .replace(".csv", "")
                           .replace(".tsv", ""))
            ax.scatter(
                qc_df.loc[mask, "length"],
                qc_df.loc[mask, "gc_content"] * 100,
                color=GENE_COLORS[i % len(GENE_COLORS)],
                alpha=0.6,
                s=20,
                label=label,
            )
        ax.legend(fontsize=8, markerscale=1.5, title="Gene", title_fontsize=9)
    else:
        ax.scatter(
            qc_df["length"],
            qc_df["gc_content"] * 100,
            color=GENE_COLORS[0],
            alpha=0.6,
            s=20,
        )

    ax.set_xlabel("Sequence length (bp)", fontsize=11)
    ax.set_ylabel("GC content (%)", fontsize=11)
    ax.set_title("GC Content vs. Sequence Length", fontsize=13,
                 fontweight="bold", pad=10)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.axhline(30, color="#E05A2B", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.axhline(70, color="#E05A2B", linestyle="--", linewidth=0.8, alpha=0.5)

    fig.tight_layout()
    return fig


def plot_n_content(
    qc_df: pd.DataFrame,
    figsize: tuple[float, float] = EMBED_FIGSIZE,
) -> Figure:
    """Plot N content distribution as a histogram.

    Args:
        qc_df:   DataFrame with 'n_content' column.
        figsize: Figure dimensions in inches.

    Returns:
        Matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=FIGURE_DPI)
    fig.patch.set_facecolor("#F5F5F5")
    ax.set_facecolor("#FAFAFA")

    n_pct = qc_df["n_content"] * 100

    ax.hist(
        n_pct,
        bins=20,
        color=GENE_COLORS[3],
        alpha=0.75,
        edgecolor="white",
        linewidth=0.5,
    )

    ax.axvline(10, color="#E05A2B", linestyle="--", linewidth=1.2,
               label="10% warning threshold")

    ax.set_xlabel("N content (%)", fontsize=11)
    ax.set_ylabel("Number of sequences", fontsize=11)
    ax.set_title("N Content Distribution", fontsize=13,
                 fontweight="bold", pad=10)
    ax.legend(fontsize=9)
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Motif analysis plots
# ---------------------------------------------------------------------------

def plot_motif_by_gene(
    summary_df: pd.DataFrame,
    motif: str,
    figsize: tuple[float, float] = EMBED_FIGSIZE,
) -> Figure:
    """Plot total motif occurrences per gene as a horizontal bar chart.

    Args:
        summary_df: DataFrame from motif_analyzer.summarize_by_gene(),
                    must have 'Gene / Source' and 'Total occurrences' columns.
        motif:      Motif string (used in the chart title).
        figsize:    Figure dimensions in inches.

    Returns:
        Matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=FIGURE_DPI)
    fig.patch.set_facecolor("#F5F5F5")
    ax.set_facecolor("#FAFAFA")

    if summary_df.empty:
        ax.text(0.5, 0.5, "No results to display.",
                ha="center", va="center", transform=ax.transAxes)
        return fig

    genes = summary_df["Gene / Source"]
    counts = summary_df["Total occurrences"]
    colors = [GENE_COLORS[i % len(GENE_COLORS)] for i in range(len(genes))]

    bars = ax.barh(genes, counts, color=colors, alpha=0.85, edgecolor="white")

    # Add value labels on bars
    for bar, count in zip(bars, counts):
        if count > 0:
            ax.text(
                bar.get_width() + 0.1,
                bar.get_y() + bar.get_height() / 2,
                str(count),
                va="center", ha="left", fontsize=10,
            )

    ax.set_xlabel("Total occurrences", fontsize=11)
    ax.set_title(
        f"Motif '{motif.upper()}' — occurrences by gene",
        fontsize=13, fontweight="bold", pad=10,
    )
    ax.invert_yaxis()  # Top gene = most occurrences

    fig.tight_layout()
    return fig


def plot_motif_comparison(
    compare_df: pd.DataFrame,
    figsize: tuple[float, float] = EMBED_FIGSIZE,
) -> Figure:
    """Plot a grouped bar chart comparing multiple motifs across genes.

    Args:
        compare_df: DataFrame from motif_analyzer.compare_motifs(),
                    genes as rows, motifs as columns.
        figsize:    Figure dimensions in inches.

    Returns:
        Matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=FIGURE_DPI)
    fig.patch.set_facecolor("#F5F5F5")
    ax.set_facecolor("#FAFAFA")

    if compare_df.empty:
        ax.text(0.5, 0.5, "No data to display.",
                ha="center", va="center", transform=ax.transAxes)
        return fig

    motif_cols = [c for c in compare_df.columns if c != "Gene / Source"]
    genes = compare_df["Gene / Source"].tolist()
    n_genes = len(genes)
    n_motifs = len(motif_cols)

    x = np.arange(n_genes)
    bar_width = min(0.8 / n_motifs, 0.25)

    for i, motif in enumerate(motif_cols):
        offset = (i - n_motifs / 2 + 0.5) * bar_width
        ax.bar(
            x + offset,
            compare_df[motif],
            width=bar_width,
            label=motif,
            color=GENE_COLORS[i % len(GENE_COLORS)],
            alpha=0.85,
            edgecolor="white",
        )

    ax.set_xticks(x)
    ax.set_xticklabels(genes, rotation=25, ha="right", fontsize=9)
    ax.set_ylabel("Total occurrences", fontsize=11)
    ax.set_title("Motif comparison across genes", fontsize=13,
                 fontweight="bold", pad=10)
    ax.legend(fontsize=9, title="Motif", title_fontsize=9)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# ORF analysis plots
# ---------------------------------------------------------------------------

def plot_orf_counts_by_gene(
    summary_df: pd.DataFrame,
    figsize: tuple[float, float] = EMBED_FIGSIZE,
) -> Figure:
    """Plot total ORF count per gene as a bar chart.

    Args:
        summary_df: DataFrame from orf_analyzer.summarize_by_gene(),
                    must have 'Gene / Source' and 'Total ORFs' columns.
        figsize:    Figure dimensions in inches.

    Returns:
        Matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=FIGURE_DPI)
    fig.patch.set_facecolor("#F5F5F5")
    ax.set_facecolor("#FAFAFA")

    if summary_df.empty:
        ax.text(0.5, 0.5, "No ORFs found.",
                ha="center", va="center", transform=ax.transAxes)
        return fig

    genes = summary_df["Gene / Source"]
    counts = summary_df["Total ORFs"]
    colors = [GENE_COLORS[i % len(GENE_COLORS)] for i in range(len(genes))]

    bars = ax.bar(genes, counts, color=colors, alpha=0.85, edgecolor="white")

    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.3,
            str(count),
            ha="center", va="bottom", fontsize=10,
        )

    ax.set_xticklabels(genes, rotation=25, ha="right", fontsize=9)
    ax.set_ylabel("Total ORFs", fontsize=11)
    ax.set_title("Total ORFs by gene", fontsize=13, fontweight="bold", pad=10)

    # Y axis: always start at 0, add 15% headroom above max bar
    ax.set_ylim(bottom=0, top=counts.max() * 1.15)

    fig.tight_layout()
    return fig


def plot_orf_length_distribution(
    orf_df: pd.DataFrame,
    figsize: tuple[float, float] = EMBED_FIGSIZE,
) -> Figure:
    """Plot distribution of longest ORF lengths per sequence as a boxplot by gene.

    Args:
        orf_df:  DataFrame from orf_analyzer.run_orf_analysis(),
                 must have 'longest_orf' and '_source' columns.
        figsize: Figure dimensions in inches.

    Returns:
        Matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=FIGURE_DPI)
    fig.patch.set_facecolor("#F5F5F5")
    ax.set_facecolor("#FAFAFA")

    if "_source" not in orf_df.columns or orf_df.empty:
        ax.text(0.5, 0.5, "No data available.",
                ha="center", va="center", transform=ax.transAxes)
        return fig

    sources = sorted(orf_df["_source"].unique())
    data = [
        orf_df.loc[orf_df["_source"] == s, "longest_orf"]
        for s in sources
    ]
    labels = [
        s.replace("_sequences.fasta", "").replace(".fasta", "")
         .replace(".csv", "").replace(".tsv", "")
        for s in sources
    ]

    bp = ax.boxplot(
        data,
        patch_artist=True,
        medianprops=dict(color="white", linewidth=2),
        whiskerprops=dict(linewidth=1.2),
        capprops=dict(linewidth=1.2),
        flierprops=dict(marker="o", markersize=3, alpha=0.5),
    )
    for patch, color in zip(bp["boxes"], GENE_COLORS):
        patch.set_facecolor(color)
        patch.set_alpha(0.8)

    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=9)
    ax.set_ylabel("Longest ORF length (bp)", fontsize=11)
    ax.set_title("Longest ORF length by gene", fontsize=13,
                 fontweight="bold", pad=10)

    fig.tight_layout()
    return fig


def plot_orf_length_histogram(
    orf_df: pd.DataFrame,
    figsize: tuple[float, float] = EMBED_FIGSIZE,
) -> Figure:
    """Plot histogram of all longest ORF lengths across all sequences.

    Args:
        orf_df:  DataFrame from orf_analyzer.run_orf_analysis().
        figsize: Figure dimensions in inches.

    Returns:
        Matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=FIGURE_DPI)
    fig.patch.set_facecolor("#F5F5F5")
    ax.set_facecolor("#FAFAFA")

    lengths = orf_df["longest_orf"][orf_df["longest_orf"] > 0]

    if lengths.empty:
        ax.text(0.5, 0.5, "No ORFs found.",
                ha="center", va="center", transform=ax.transAxes)
        return fig

    ax.hist(
        lengths,
        bins=20,
        color=GENE_COLORS[4],
        alpha=0.75,
        edgecolor="white",
        linewidth=0.5,
    )

    ax.set_xlabel("Longest ORF length (bp)", fontsize=11)
    ax.set_ylabel("Number of sequences", fontsize=11)
    ax.set_title("Distribution of longest ORF lengths", fontsize=13,
                 fontweight="bold", pad=10)

    fig.tight_layout()
    return fig