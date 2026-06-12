# app/src/report.py
# Report generation module for BioSeq Explorer.
# Generates a Markdown report with embedded PNG plots
# summarising QC metrics, statistical results and dataset info.
#
# The report is saved to results/app_output/ together with
# all plot PNG files referenced in the document.

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Subdirectory inside APP_OUTPUT_DIR where report plots are saved
PLOTS_SUBDIR = "report_plots"

# Report filename
REPORT_FILENAME = "bioseq_report.md"

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ensure_output_dirs(output_dir: Path) -> Path:
    """Create output directory and plots subdirectory if they do not exist.

    Args:
        output_dir: Base output directory (from config.APP_OUTPUT_DIR).

    Returns:
        Path to the plots subdirectory.
    """
    plots_dir = output_dir / PLOTS_SUBDIR
    plots_dir.mkdir(parents=True, exist_ok=True)
    return plots_dir


def _save_figure(fig, path: Path) -> None:
    """Save a matplotlib Figure to a PNG file.

    Args:
        fig:  Matplotlib Figure object.
        path: Full path where the PNG will be saved.

    Returns:
        None
    """
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())


def _format_metric_name(metric: str) -> str:
    """Convert internal metric column name to a human-readable label.

    Args:
        metric: Column name ('gc_content', 'n_content', 'length').

    Returns:
        Human-readable string.
    """
    return {
        "gc_content": "GC content",
        "n_content":  "N content",
        "length":     "Sequence length (bp)",
    }.get(metric, metric)


# ---------------------------------------------------------------------------
# Report sections
# ---------------------------------------------------------------------------

def _section_header(dataset_path: str, huba_report_loaded: bool) -> str:
    """Generate the report header section.

    Args:
        dataset_path:       Path to the loaded dataset file.
        huba_report_loaded: Whether HUBA REPORT.md was loaded.

    Returns:
        Markdown string for the header section.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# BioSeq Explorer — Analysis Report",
        "",
        f"**Generated:** {now}  ",
        f"**Dataset:** `{dataset_path}`  ",
        f"**HUBA report:** {'loaded' if huba_report_loaded else 'not available'}  ",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def _section_dataset_summary(qc_df: pd.DataFrame) -> str:
    """Generate dataset summary section.

    Args:
        qc_df: DataFrame with QC metrics.

    Returns:
        Markdown string for the dataset summary section.
    """
    n_seq = len(qc_df)
    n_sources = qc_df["_source"].nunique() if "_source" in qc_df.columns else "—"
    n_flagged = int((qc_df["qc_flag"] != "OK").sum()) \
        if "qc_flag" in qc_df.columns else "—"

    lines = [
        "## 1. Dataset Summary",
        "",
        f"| Parameter | Value |",
        f"|-----------|-------|",
        f"| Total sequences | {n_seq} |",
        f"| Gene sources | {n_sources} |",
        f"| Flagged sequences | {n_flagged} |",
        "",
    ]
    return "\n".join(lines)


def _section_qc_stats(summary_df: pd.DataFrame) -> str:
    """Generate QC summary statistics section.

    Args:
        summary_df: DataFrame from analyzer.compute_summary_stats().

    Returns:
        Markdown string for the QC statistics section.
    """
    lines = [
        "## 2. Quality Control — Summary Statistics",
        "",
    ]

    # Convert summary DataFrame to Markdown table
    header = "| Metric | Mean | Median | Std | Min | Max | Q25 | Q75 |"
    separator = "|--------|------|--------|-----|-----|-----|-----|-----|"
    lines.append(header)
    lines.append(separator)

    for metric_name, row in summary_df.iterrows():
        # Format GC and N content as percentages, length as integer
        if "content" in metric_name.lower():
            fmt = lambda v: f"{v * 100:.2f}%"
        else:
            fmt = lambda v: f"{v:.1f}"

        lines.append(
            f"| {metric_name} "
            f"| {fmt(row['Mean'])} "
            f"| {fmt(row['Median'])} "
            f"| {fmt(row['Std'])} "
            f"| {fmt(row['Min'])} "
            f"| {fmt(row['Max'])} "
            f"| {fmt(row['Q25'])} "
            f"| {fmt(row['Q75'])} |"
        )

    lines.append("")
    return "\n".join(lines)


def _section_gene_stats(gene_df: pd.DataFrame) -> str:
    """Generate per-gene statistics section.

    Args:
        gene_df: DataFrame from analyzer.compute_gene_stats().

    Returns:
        Markdown string for the per-gene statistics section.
    """
    if gene_df.empty:
        return "## 3. Per-Gene Statistics\n\n_No gene source data available._\n\n"

    lines = [
        "## 3. Per-Gene Statistics",
        "",
        "| Gene / Source | Mean GC% | Mean N% | Mean Length (bp) |",
        "|---------------|----------|---------|-----------------|",
    ]

    for _, row in gene_df.iterrows():
        lines.append(
            f"| {row['Gene / Source']} "
            f"| {row['gc_content'] * 100:.2f}% "
            f"| {row['n_content'] * 100:.3f}% "
            f"| {row['length']:.1f} |"
        )

    lines.append("")
    return "\n".join(lines)


def _section_plots(plot_filenames: list[str]) -> str:
    """Generate plots section with embedded images.

    Args:
        plot_filenames: List of PNG filenames (relative to report location).

    Returns:
        Markdown string embedding all plot images.
    """
    lines = [
        "## 4. Visualizations",
        "",
    ]

    plot_titles = {
        "gc_distribution.png":    "GC Content Distribution",
        "gc_boxplot.png":         "GC Content by Gene",
        "length_distribution.png": "Sequence Length Distribution",
        "gc_vs_length.png":       "GC% vs. Sequence Length",
        "n_content.png":          "N Content Distribution",
        "correlation_matrix.png": "Correlation Matrix",
    }

    for filename in plot_filenames:
        title = plot_titles.get(filename, filename.replace(".png", "").replace("_", " ").title())
        lines.append(f"### {title}")
        lines.append("")
        lines.append(f"![{title}]({PLOTS_SUBDIR}/{filename})")
        lines.append("")

    return "\n".join(lines)


def _section_stat_results(stat_results: list[dict]) -> str:
    """Generate statistical test results section.

    Args:
        stat_results: List of result dicts from stats module tests.

    Returns:
        Markdown string for the statistical results section.
    """
    if not stat_results:
        return "## 5. Statistical Test Results\n\n_No tests were run._\n\n"

    lines = ["## 5. Statistical Test Results", ""]

    for result in stat_results:
        if "error" in result:
            lines.append(f"- **Error:** {result['error']}")
            continue

        test_name = result.get("test", "Unknown test")
        metric = _format_metric_name(result.get("metric", ""))
        p_val = result.get("p_value", "—")
        significant = result.get("significant", False)
        note = result.get("note", "")
        sig_label = "✅ Significant" if significant else "❌ Not significant"

        lines.append(f"**{test_name}** — {metric}")
        lines.append("")
        lines.append(f"- p-value: `{p_val}`")
        lines.append(f"- Result: {sig_label}")
        lines.append(f"- {note}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main report generation function
# ---------------------------------------------------------------------------

def generate_report(
    qc_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    gene_df: pd.DataFrame,
    plots_module,
    output_dir: Path,
    dataset_path: str = "unknown",
    huba_report_loaded: bool = False,
    stat_results: list[dict] | None = None,
    corr_fig=None,
) -> Path:
    """Generate a full Markdown report with plots.

    Saves all PNG plots to output_dir/report_plots/
    and writes the Markdown report to output_dir/bioseq_report.md.

    Args:
        qc_df:              DataFrame with QC metrics (from analyzer).
        summary_df:         Summary stats DataFrame (from analyzer).
        gene_df:            Per-gene stats DataFrame (from analyzer).
        plots_module:       Loaded plots module (app/src/plots.py).
        output_dir:         Directory to save report and plots.
        dataset_path:       String path of the loaded dataset (for header).
        huba_report_loaded: Whether HUBA REPORT.md was loaded.
        stat_results:       List of statistical test result dicts (optional).
        corr_fig:           Correlation heatmap Figure object (optional).

    Returns:
        Path to the generated Markdown report file.
    """
    plots_dir = _ensure_output_dirs(output_dir)

    # --- Generate and save all QC plots ---
    plot_specs = [
        ("gc_distribution.png",    plots_module.plot_gc_distribution),
        ("gc_boxplot.png",         plots_module.plot_gc_boxplot),
        ("length_distribution.png", plots_module.plot_length_distribution),
        ("gc_vs_length.png",       plots_module.plot_gc_vs_length),
        ("n_content.png",          plots_module.plot_n_content),
    ]

    saved_plots = []
    for filename, plot_fn in plot_specs:
        try:
            fig = plot_fn(
                qc_df,
                figsize=(7.0, 4.5),  # Larger size for report
            )
            _save_figure(fig, plots_dir / filename)
            saved_plots.append(filename)
        except Exception:
            pass  # Skip plots that fail — don't abort whole report

    # Save correlation matrix if provided
    if corr_fig is not None:
        try:
            _save_figure(corr_fig, plots_dir / "correlation_matrix.png")
            saved_plots.append("correlation_matrix.png")
        except Exception:
            pass

    # --- Assemble Markdown content ---
    sections = [
        _section_header(dataset_path, huba_report_loaded),
        _section_dataset_summary(qc_df),
        _section_qc_stats(summary_df),
        _section_gene_stats(gene_df),
        _section_plots(saved_plots),
        _section_stat_results(stat_results or []),
    ]

    report_text = "\n".join(sections)

    # --- Write report file ---
    report_path = output_dir / REPORT_FILENAME
    report_path.write_text(report_text, encoding="utf-8")

    return report_path


# ---------------------------------------------------------------------------
# PDF report generation
# ---------------------------------------------------------------------------

def generate_pdf(
    qc_df,
    summary_df,
    gene_df,
    plots_module,
    output_dir,
    dataset_path: str = "unknown",
    huba_report_loaded: bool = False,
    huba_report_text: str = "",
    stat_results=None,
    corr_fig=None,
    orf_df=None,
    include_plots: bool = True,
    plot_selection: dict = None,
):
    """Generate a PDF report with all analyses, statistics and plots.

    Uses reportlab to produce a single self-contained PDF file.
    All plots are embedded directly — no external PNG files needed.

    Args:
        qc_df:              DataFrame with QC metrics.
        summary_df:         Summary stats DataFrame.
        gene_df:            Per-gene stats DataFrame.
        plots_module:       Loaded plots module.
        output_dir:         Directory to save the PDF.
        dataset_path:       Path string of the loaded dataset.
        huba_report_loaded: Whether HUBA REPORT.md was loaded.
        huba_report_text:   Full text of HUBA REPORT.md (optional).
        stat_results:       List of statistical test result dicts.
        corr_fig:           Correlation heatmap Figure (optional).

    Returns:
        Path to the generated PDF file.
    """
    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Image as RLImage, KeepTogether, PageBreak, Paragraph,
        SimpleDocTemplate, Spacer, Table, TableStyle,
    )

    _ensure_output_dirs(output_dir)
    pdf_path = output_dir / "bioseq_report.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path), pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("ReportTitle", parent=styles["Title"],
        fontSize=20, spaceAfter=6,
        textColor=colors.HexColor("#1F6AA5"))
    h1_style = ParagraphStyle("H1", parent=styles["Heading1"],
        fontSize=14, spaceBefore=14, spaceAfter=4,
        textColor=colors.HexColor("#1F6AA5"))
    h2_style = ParagraphStyle("H2", parent=styles["Heading2"],
        fontSize=12, spaceBefore=6, spaceAfter=3,
        textColor=colors.HexColor("#374151"))
    body_style = ParagraphStyle("Body", parent=styles["Normal"],
        fontSize=10, spaceAfter=4, leading=14)
    meta_style = ParagraphStyle("Meta", parent=styles["Normal"],
        fontSize=9, spaceAfter=3, leading=12,
        textColor=colors.HexColor("#6B7280"))
    mono_style = ParagraphStyle("Mono", parent=styles["Code"],
        fontSize=8, spaceAfter=2, leading=12,
        textColor=colors.HexColor("#374151"))

    def make_table_style(header_color="#1F6AA5"):
        return TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor(header_color)),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,0), 9),
            ("FONTSIZE",   (0,1), (-1,-1), 8),
            ("ROWBACKGROUNDS", (0,1), (-1,-1),
             [colors.white, colors.HexColor("#F3F4F6")]),
            ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#D1D5DB")),
            ("ALIGN", (1,0), (-1,-1), "CENTER"),
            ("ALIGN", (0,0), (0,-1), "LEFT"),
            ("TOPPADDING",    (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING",   (0,0), (-1,-1), 6),
            ("ROWBACKGROUNDS", (0,0), (-1,0), [colors.HexColor(header_color)]),
        ])

    def fig_to_image(fig, width_cm=14):
        """Convert matplotlib figure to reportlab Image with correct scaling."""
        # Move legend outside plot area to prevent overlap
        try:
            for ax in fig.get_axes():
                leg = ax.get_legend()
                if leg is not None:
                    leg.set_bbox_to_anchor((1.01, 1))
                    leg.set_loc("upper left")
            fig.tight_layout()
        except Exception:
            pass

        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=96, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        buf.seek(0)
        img = RLImage(buf)
        scale = (width_cm * cm) / img.imageWidth
        img.drawWidth = width_cm * cm
        img.drawHeight = img.imageHeight * scale
        img.hAlign = "CENTER"
        return img

    def plot_block(title, fig, width_cm=14):
        """Wrap plot title + image in KeepTogether so they stay on same page."""
        return KeepTogether([
            Paragraph(title, h2_style),
            fig_to_image(fig, width_cm=width_cm),
            Spacer(1, 0.5*cm),
        ])

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Extract dataset variant from filename (A, B or C)
    import re
    variant_match = re.search(r"clean_dataset_([ABC])", dataset_path)
    variant = f"Variant {variant_match.group(1)}" if variant_match else "Unknown"
    dataset_name = Path(dataset_path).name

    story = []
    section_num = [0]  # mutable counter for dynamic section numbering

    def next_section(title: str) -> str:
        """Return next numbered section title."""
        section_num[0] += 1
        return f"{section_num[0]}. {title}"

    # ── Cover ────────────────────────────────────────────────────────────────
    story.append(Paragraph("BioSeq Explorer", title_style))
    story.append(Paragraph("Analysis Report", styles["Heading2"]))
    story.append(Spacer(1, 0.5*cm))

    cover_data = [
        ["Generated", now],
        ["Dataset", dataset_name],
        ["Filter variant", variant],
        ["HUBA report", "Loaded" if huba_report_loaded else "Not available"],
        ["Total sequences", str(len(qc_df))],
        ["Gene sources",
         str(qc_df["_source"].nunique()) if "_source" in qc_df.columns else "n/a"],
        ["Flagged sequences",
         str(int((qc_df["qc_flag"] != "OK").sum()))
         if "qc_flag" in qc_df.columns else "n/a"],
    ]
    cover_table = Table(cover_data, colWidths=[5*cm, 11*cm])
    cover_table.setStyle(TableStyle([
        ("FONTNAME",   (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 10),
        ("TEXTCOLOR",  (0,0), (0,-1), colors.HexColor("#1F6AA5")),
        ("ROWBACKGROUNDS", (0,0), (-1,-1),
         [colors.white, colors.HexColor("#F3F4F6")]),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("LINEBELOW", (0,-1), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 0.5*cm))

    # ── 1. QC Summary Statistics ─────────────────────────────────────────────
    if summary_df is not None:
     story.append(Paragraph(next_section("Quality Control — Summary Statistics"), h1_style))
    qc_data = [["Metric", "Mean", "Median", "Std", "Min", "Max", "Q25", "Q75"]]
    for metric_name, row in summary_df.iterrows():
        fmt = (lambda v: f"{v*100:.2f}%") if "content" in metric_name.lower()             else (lambda v: f"{v:.1f}")
        qc_data.append([metric_name,
            fmt(row["Mean"]), fmt(row["Median"]), fmt(row["Std"]),
            fmt(row["Min"]),  fmt(row["Max"]),
            fmt(row["Q25"]),  fmt(row["Q75"])])
    t = Table(qc_data, colWidths=[4.5*cm]+[1.9*cm]*7)
    t.setStyle(make_table_style())
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    # ── 2. Per-Gene Statistics ────────────────────────────────────────────────
    if gene_df is not None and not gene_df.empty:
        gene_data = [["Gene / Source", "Mean GC%", "Mean N%", "Mean Length (bp)"]]
        for _, row in gene_df.iterrows():
            gene_data.append([
                str(row["Gene / Source"]),
                f"{row['gc_content']*100:.2f}%",
                f"{row['n_content']*100:.3f}%",
                f"{row['length']:.1f}",
            ])
        t = Table(gene_data, colWidths=[5*cm, 3.5*cm, 3.5*cm, 4*cm])
        t.setStyle(make_table_style())

        # KeepTogether keeps header + table on same page if it fits
        gene_block = [
            Paragraph(next_section("Per-Gene Statistics"), h1_style),
            t,
            Spacer(1, 0.5*cm),
        ]
        # If table has many rows it won't fit — just add normally
        if len(gene_data) <= 12:
            story.append(KeepTogether(gene_block))
        else:
            story.extend(gene_block)

    # ── 3. Statistical Test Results ───────────────────────────────────────────
    if stat_results:
        story.append(Paragraph(next_section("Statistical Test Results"), h1_style))
        for result in stat_results:
            if "error" in result:
                story.append(Paragraph(f"Error: {result['error']}", body_style))
                continue
            test_name = result.get("test", "Unknown test")
            metric = _format_metric_name(result.get("metric", ""))
            p_val = result.get("p_value", "n/a")
            significant = result.get("significant", False)
            note = result.get("note", "")
            sig_label = "Significant" if significant else "Not significant"
            story.append(KeepTogether([
                Paragraph(f"<b>{test_name}</b> — {metric}", h2_style),
                Paragraph(
                    f"p-value: <b>{p_val}</b>   Result: <b>{sig_label}</b>",
                    body_style),
                Paragraph(note, body_style),
                Spacer(1, 0.3*cm),
            ]))
        story.append(Spacer(1, 0.3*cm))

    # ── 4. ORF Analysis Results ──────────────────────────────────────────────
    if orf_df is not None and not orf_df.empty:
        import importlib.util as _ilu2
        story.append(Paragraph(next_section("ORF Analysis Results"), h1_style))

        # Summary stats
        total_orfs = int(orf_df["n_orfs"].sum())
        seqs_with_orfs = int((orf_df["n_orfs"] > 0).sum())
        story.append(Paragraph(
            f"Total ORFs found: <b>{total_orfs}</b> &nbsp;&nbsp; "
            f"Sequences with ORFs: <b>{seqs_with_orfs}</b> / {len(orf_df)}",
            body_style,
        ))
        story.append(Spacer(1, 0.3*cm))

        # Per-gene ORF summary table
        from collections import defaultdict
        gene_orfs = defaultdict(lambda: {"total": 0, "longest": 0, "count": 0})
        for _, row in orf_df.iterrows():
            src = str(row["_source"]).replace("_sequences.fasta","")                 .replace(".fasta","").replace(".csv","").replace(".tsv","")
            gene_orfs[src]["total"] += int(row["n_orfs"])
            gene_orfs[src]["longest"] = max(
                gene_orfs[src]["longest"], int(row["longest_orf"]))
            gene_orfs[src]["count"] += 1

        orf_table_data = [["Gene / Source", "Total ORFs",
                           "Longest ORF (bp)", "Sequences"]]
        for gene, vals in sorted(gene_orfs.items(),
                                 key=lambda x: x[1]["total"], reverse=True):
            orf_table_data.append([
                gene, str(vals["total"]),
                str(vals["longest"]), str(vals["count"]),
            ])

        t = Table(orf_table_data, colWidths=[5*cm, 3.5*cm, 4*cm, 3.5*cm])
        t.setStyle(make_table_style())
        story.append(KeepTogether([t, Spacer(1, 0.5*cm)]))

    # ── 5. Visualizations ─────────────────────────────────────────────────────
    if include_plots:
     story.append(PageBreak())
     story.append(Paragraph(next_section("Visualizations"), h1_style))

    if include_plots:
        sel = plot_selection or {}
        plot_specs = [
            ("plot_gc_dist",   "GC Content Distribution",
             plots_module.plot_gc_distribution),
            ("plot_gc_box",    "GC Content by Gene",
             plots_module.plot_gc_boxplot),
            ("plot_length",    "Sequence Length Distribution",
             plots_module.plot_length_distribution),
            ("plot_gc_length", "GC% vs. Sequence Length",
             plots_module.plot_gc_vs_length),
            ("plot_n",         "N Content Distribution",
             plots_module.plot_n_content),
        ]
        any_plot = False
        for key, plot_title, plot_fn in plot_specs:
            # Include if no selection made (default all) or explicitly selected
            if sel.get(key, True):
                try:
                    fig = plot_fn(qc_df, figsize=(7.0, 3.8))
                    story.append(plot_block(plot_title, fig, width_cm=14))
                    any_plot = True
                except Exception:
                    pass

        if corr_fig is not None and sel.get("plot_corr", True):
            try:
                story.append(plot_block("Correlation Matrix",
                                        corr_fig, width_cm=10))
                any_plot = True
            except Exception:
                pass

    # ── 5. HUBA Pipeline Report (condensed) ───────────────────────────────────
    if huba_report_text:
        story.append(PageBreak())
        story.append(Paragraph(next_section("HUBA Pipeline Report"), h1_style))
        story.append(Paragraph(
            "Data preparation summary generated by HUBA pipeline:",
            body_style))
        story.append(Spacer(1, 0.3*cm))

        # Parse HUBA report — skip duplicate Artefacts sections
        seen_artefacts = False
        skip_artefacts = False
        for line in huba_report_text.splitlines():
            stripped = line.strip()
            if not stripped:
                story.append(Spacer(1, 0.1*cm))
                continue

            # Detect and deduplicate Artefacts sections
            if stripped.lower() == "artefacts" or stripped == "## Artefacts":
                if seen_artefacts:
                    skip_artefacts = True
                    continue
                else:
                    seen_artefacts = True
                    skip_artefacts = False

            if skip_artefacts:
                # Resume after next variant header
                if stripped.startswith("## Variant") or stripped.startswith("Variant"):
                    skip_artefacts = False
                else:
                    continue

            if stripped.startswith("## "):
                story.append(Paragraph(stripped[3:], h2_style))
            elif stripped.startswith("# "):
                story.append(Paragraph(stripped[2:], h1_style))
            else:
                safe = stripped.replace("&","&amp;").replace("<","&lt;")                               .replace(">","&gt;")
                story.append(Paragraph(safe, mono_style))

    doc.build(story)
    return pdf_path