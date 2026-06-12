# app/main.py
# Main entry point for BioSeq Explorer GUI.
# Creates the main application window with a tab-based layout.
# Each tab is a placeholder frame — functionality will be added module by module.
#
# Usage:
#   python app/main.py          (from project root)
#   python main.py              (from app/ directory)

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

# ---------------------------------------------------------------------------
# Path setup — allow running from project root or from app/ directory
# ---------------------------------------------------------------------------

# Add the app/ directory to sys.path so that config can be imported
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# Add project root to sys.path (needed for future imports from src/)
PROJECT_ROOT = APP_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import importlib.util as _ilu

# Always load app/config.py — not the root config.py used by HUBA
_cfg_path = APP_DIR / "config.py"
_spec = _ilu.spec_from_file_location("app_config", _cfg_path)
config = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(config)

# ---------------------------------------------------------------------------
# Appearance settings
# ---------------------------------------------------------------------------

ctk.set_appearance_mode(config.APPEARANCE_MODE)
ctk.set_default_color_theme(config.COLOR_THEME)


# ---------------------------------------------------------------------------
# Helper — Treeview styling
# ---------------------------------------------------------------------------

def apply_treeview_style() -> None:
    """Apply a clean style to all ttk.Treeview widgets.

    Args:
        None

    Returns:
        None
    """
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Treeview",
        rowheight=24,
        font=("Segoe UI", 11),
        borderwidth=0,
    )
    style.configure(
        "Treeview.Heading",
        font=("Segoe UI", 11, "bold"),
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", "#1F6AA5")],
        foreground=[("selected", "white")],
    )


# ---------------------------------------------------------------------------
# Tab: Home
# ---------------------------------------------------------------------------

class HomeTab(ctk.CTkFrame):
    """Home tab — load dataset and display HUBA report summary."""

    def __init__(self, parent: ctk.CTkTabview) -> None:
        super().__init__(parent, fg_color="transparent")

        self.df = None           # Loaded pandas DataFrame
        self.dataset_path = None # Path to the loaded CSV file

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the Home tab layout.

        Args:
            None

        Returns:
            None
        """
        # --- Top bar: load button + dataset info ---
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkButton(
            top_bar,
            text="📂  Load Dataset",
            width=160,
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._load_dataset,
        ).pack(side="left")

        self.dataset_label = ctk.CTkLabel(
            top_bar,
            text="No dataset loaded.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.dataset_label.pack(side="left", padx=(16, 0))

        # --- Main area: two columns ---
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        content.columnconfigure(0, weight=3)  # Table takes more space
        content.columnconfigure(1, weight=2)  # Report panel
        content.rowconfigure(0, weight=1)

        # --- Left column: data table ---
        table_frame = ctk.CTkFrame(content)
        table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            table_frame,
            text="Dataset preview",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(10, 4))

        # Treeview inside a plain tk frame (ttk widget — needs tk parent)
        tree_container = tk.Frame(table_frame, bg="#2b2b2b")
        tree_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.tree = ttk.Treeview(tree_container, show="headings")
        vsb = ttk.Scrollbar(
            tree_container, orient="vertical", command=self.tree.yview
        )
        hsb = ttk.Scrollbar(
            tree_container, orient="horizontal", command=self.tree.xview
        )
        self.tree.configure(
            yscrollcommand=vsb.set, xscrollcommand=hsb.set
        )

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        # Placeholder message in table
        self._show_table_placeholder()

        # --- Right column: HUBA report ---
        report_frame = ctk.CTkFrame(content)
        report_frame.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(
            report_frame,
            text="HUBA pipeline report",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(10, 4))

        self.report_box = ctk.CTkTextbox(
            report_frame,
            font=ctk.CTkFont(family="Courier New", size=11),
            wrap="none",
            state="disabled",
        )
        self.report_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._show_report_placeholder()

    def _show_table_placeholder(self) -> None:
        """Show placeholder text when no dataset is loaded.

        Args:
            None

        Returns:
            None
        """
        # Clear existing columns and insert a single placeholder column
        self.tree["columns"] = ("info",)
        self.tree.heading("info", text="")
        self.tree.column("info", width=400, anchor="center")
        self.tree.delete(*self.tree.get_children())
        self.tree.insert("", "end", values=("Load a dataset to preview data.",))

    def _show_report_placeholder(self) -> None:
        """Show placeholder text in the report panel.

        Args:
            None

        Returns:
            None
        """
        self.report_box.configure(state="normal")
        self.report_box.delete("1.0", "end")
        self.report_box.insert(
            "1.0",
            "No report loaded.\n\nLoad a dataset to display\nthe HUBA pipeline report.",
        )
        self.report_box.configure(state="disabled")

    def _load_dataset(self) -> None:
        """Open file dialog and load a clean_dataset_*.csv file.

        Args:
            None

        Returns:
            None
        """
        import pandas as pd

        # Required columns for BioSeq Explorer analysis
        REQUIRED_COLUMNS = {"id", "sequence", "_source"}

        # File dialog — start in results/tables if it exists
        # Show only clean_dataset_*.csv files by default
        initial_dir = str(
            PROJECT_ROOT / "results" / "tables"
            if (PROJECT_ROOT / "results" / "tables").exists()
            else PROJECT_ROOT
        )

        path = filedialog.askopenfilename(
            title="Select clean dataset — choose a clean_dataset_*.csv file",
            initialdir=initial_dir,
            filetypes=[
                ("Clean datasets", "clean_dataset_*.csv"),
                ("All CSV files", "*.csv"),
                ("All files", "*.*"),
            ],
        )

        if not path:
            return  # User cancelled

        # Warn if selected file does not look like a clean_dataset
        filename = Path(path).name
        if not filename.startswith("clean_dataset_"):
            proceed = messagebox.askyesno(
                "Unexpected file",
                f"The selected file '{filename}' does not appear to be a "
                f"clean_dataset_*.csv file generated by HUBA.\n\n"
                f"BioSeq Explorer requires a file with columns:\n"
                f"  id, sequence, _source\n\n"
                f"If this file is missing these columns, the following tabs\n"
                f"will not work: Quality Control, Statistics, Report.\n\n"
                f"Do you want to continue anyway?",
            )
            if not proceed:
                return

        try:
            self.df = pd.read_csv(path)
            self.dataset_path = Path(path)
        except Exception as e:
            messagebox.showerror("Load error", f"Could not load file:\n{e}")
            return

        # Validate required columns
        missing_cols = REQUIRED_COLUMNS - set(self.df.columns)
        if missing_cols:
            messagebox.showerror(
                "Invalid file",
                f"The file '{filename}' is missing required columns:\n\n"
                f"  {', '.join(sorted(missing_cols))}\n\n"
                f"BioSeq Explorer requires columns: id, sequence, _source.\n\n"
                f"Please load a clean_dataset_*.csv file generated by HUBA\n"
                f"(found in results/tables/).",
            )
            self.df = None
            self.dataset_path = None
            return

        # Update dataset label
        row_count = len(self.df)
        col_count = len(self.df.columns)
        self.dataset_label.configure(
            text=f"{self.dataset_path.name}  —  {row_count} rows, {col_count} columns",
            text_color=("gray10", "gray90"),
        )

        # Populate Treeview
        self._populate_table()

        # Load HUBA report from same results directory
        self._load_report(self.dataset_path.parent.parent / "REPORT.md")

        # Notify other tabs that data has been loaded
        app = self.winfo_toplevel()
        app.on_dataset_loaded(self.df)

        # Pass dataset metadata to ReportTab
        huba_report_path = self.dataset_path.parent.parent / "REPORT.md"
        huba_loaded = huba_report_path.exists()
        huba_text = huba_report_path.read_text(encoding="utf-8")             if huba_loaded else ""
        app.report_tab.set_dataset_info(
            dataset_path=str(self.dataset_path),
            huba_loaded=huba_loaded,
        )
        app.report_tab._huba_report_text = huba_text

    def _populate_table(self) -> None:
        """Fill the Treeview with data from self.df.

        Args:
            None

        Returns:
            None
        """
        # Clear existing data
        self.tree.delete(*self.tree.get_children())

        # Set columns
        columns = list(self.df.columns)
        self.tree["columns"] = columns

        for col in columns:
            self.tree.heading(
                col,
                text=col,
                command=lambda c=col: self._sort_column(c, False),
            )
            # Auto-width: max of header length and first few values
            col_width = max(
                len(str(col)) * 10,
                min(200, max(
                    (len(str(v)) * 8 for v in self.df[col].head(20)),
                    default=80,
                )),
            )
            self.tree.column(col, width=col_width, minwidth=60)

        # Insert rows (limit to 500 for performance)
        display_df = self.df.head(500)
        for _, row in display_df.iterrows():
            self.tree.insert("", "end", values=list(row))

        if len(self.df) > 500:
            self.tree.insert(
                "", "end",
                values=["... (showing first 500 rows)"] + [""] * (len(columns) - 1),
            )

    def _sort_column(self, col: str, reverse: bool) -> None:
        """Sort Treeview rows by the clicked column header.

        Args:
            col:     Column name to sort by.
            reverse: If True, sort descending.

        Returns:
            None
        """
        data = [
            (self.tree.set(child, col), child)
            for child in self.tree.get_children("")
        ]

        try:
            data.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            data.sort(key=lambda t: t[0].lower(), reverse=reverse)

        for index, (_, child) in enumerate(data):
            self.tree.move(child, "", index)

        # Flip sort direction on next click
        self.tree.heading(
            col,
            command=lambda: self._sort_column(col, not reverse),
        )

    def _load_report(self, report_path: Path) -> None:
        """Load and display REPORT.md content in the report panel.

        Args:
            report_path: Path to the REPORT.md file.

        Returns:
            None
        """
        self.report_box.configure(state="normal")
        self.report_box.delete("1.0", "end")

        if report_path.exists():
            text = report_path.read_text(encoding="utf-8")
            self.report_box.insert("1.0", text)
        else:
            self.report_box.insert(
                "1.0",
                f"Report not found:\n{report_path}\n\n"
                "Make sure HUBA has been run and REPORT.md exists.",
            )

        self.report_box.configure(state="disabled")


# ---------------------------------------------------------------------------
# Tab: Quality Control
# ---------------------------------------------------------------------------

class QualityControlTab(ctk.CTkFrame):
    """Quality Control tab — GC%, N%, sequence length analysis."""

    def __init__(self, parent: ctk.CTkTabview) -> None:
        super().__init__(parent, fg_color="transparent")

        self.qc_df = None   # DataFrame with computed QC metrics
        self._figures = {}  # Stores current Figure objects for popup reuse

        self._build_placeholder()

    def _build_placeholder(self) -> None:
        """Show a placeholder until data is loaded.

        Args:
            None

        Returns:
            None
        """
        self._placeholder = ctk.CTkFrame(self, fg_color="transparent")
        self._placeholder.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self._placeholder,
            text="Quality Control",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(40, 8))
        ctk.CTkLabel(
            self._placeholder,
            text="Load a dataset in the Home tab to enable this analysis.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).pack()

    def _show_error(self, message: str) -> None:
        """Replace placeholder with a critical error message.

        Args:
            message: Error description to display.

        Returns:
            None
        """
        for widget in self._placeholder.winfo_children():
            widget.destroy()
        tk.Label(
            self._placeholder,
            text="❌  This tab could not be loaded",
            font=("Segoe UI", 14, "bold"),
            fg="#DC2626",
            bg=self._placeholder.cget("fg_color")[1]
            if isinstance(self._placeholder.cget("fg_color"), (list, tuple))
            else "#F9FAFB",
        ).pack(pady=(40, 8))
        tk.Label(
            self._placeholder,
            text=message,
            font=("Segoe UI", 11),
            fg="#6B7280",
            wraplength=500,
            justify="center",
        ).pack()
        tk.Label(
            self._placeholder,
            text="Please load a clean_dataset_*.csv file from results/tables/",
            font=("Segoe UI", 11),
            fg="#6B7280",
            wraplength=500,
            justify="center",
        ).pack(pady=(8, 0))

    def reset(self) -> None:
        """Reset tab to placeholder state for a new dataset load.

        Args:
            None

        Returns:
            None
        """
        for widget in self.winfo_children():
            widget.destroy()
        self.qc_df = None
        self._figures = {}
        self._build_placeholder()

    def load_data(self, df) -> None:
        """Receive the loaded DataFrame, compute QC metrics and build the UI.

        Args:
            df: pandas DataFrame with sequence data (must have 'sequence' column).

        Returns:
            None
        """
        # Guard: build UI only once
        if self.qc_df is not None:
            return

        import importlib.util as _ilu

        # Load analyzer module from app/src/analyzer.py
        _ana_path = APP_DIR / "src" / "analyzer.py"
        _spec = _ilu.spec_from_file_location("app_analyzer", _ana_path)
        analyzer = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(analyzer)

        # Load plots module from app/src/plots.py
        _plt_path = APP_DIR / "src" / "plots.py"
        _spec2 = _ilu.spec_from_file_location("app_plots", _plt_path)
        plots = _ilu.module_from_spec(_spec2)
        _spec2.loader.exec_module(plots)

        try:
            self.qc_df = analyzer.run_quality_analysis(df)
            self.qc_df = analyzer.flag_outliers(
                self.qc_df,
                gc_low=config.GC_LOW_THRESHOLD,
                gc_high=config.GC_HIGH_THRESHOLD,
                n_warning=config.N_WARNING_THRESHOLD,
            )
        except Exception as e:
            self._show_error(str(e))
            return

        # Remove placeholder and build full UI
        self._placeholder.destroy()
        self._build_ui(plots, analyzer)

    def _build_ui(self, plots, analyzer) -> None:
        """Build the full Quality Control UI with table and plots.

        Args:
            plots:    Loaded plots module (app/src/plots.py).
            analyzer: Loaded analyzer module (app/src/analyzer.py).

        Returns:
            None
        """
        # --- Summary stats bar at the top ---
        summary = analyzer.compute_summary_stats(self.qc_df)

        stats_bar = ctk.CTkFrame(self, height=52)
        stats_bar.pack(fill="x", padx=16, pady=(12, 0))
        stats_bar.pack_propagate(False)

        stat_items = [
            ("Sequences", str(len(self.qc_df))),
            ("Mean GC%", f"{summary.loc['GC content', 'Mean'] * 100:.1f}%"),
            ("Mean N%",  f"{summary.loc['N content', 'Mean'] * 100:.2f}%"),
            ("Mean length", f"{summary.loc['Length (bp)', 'Mean']:.0f} bp"),
            ("Flagged", str((self.qc_df["qc_flag"] != "OK").sum())),
        ]

        for label, value in stat_items:
            box = ctk.CTkFrame(stats_bar, fg_color="transparent")
            box.pack(side="left", padx=20, pady=6)
            ctk.CTkLabel(
                box, text=value,
                font=ctk.CTkFont(size=15, weight="bold"),
            ).pack()
            ctk.CTkLabel(
                box, text=label,
                font=ctk.CTkFont(size=10),
                text_color="gray",
            ).pack()

        # --- Main area: left = table, right = plots ---
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=(8, 16))
        content.columnconfigure(0, weight=2)
        content.columnconfigure(1, weight=3)
        content.rowconfigure(0, weight=1)

        # --- Left: QC metrics table ---
        table_frame = ctk.CTkFrame(content)
        table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            table_frame,
            text="Sequence metrics",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(10, 4))

        tree_container = tk.Frame(table_frame)
        tree_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        cols = ["id", "length", "gc_content", "n_content", "qc_flag"]
        self.qc_tree = ttk.Treeview(
            tree_container, columns=cols, show="headings"
        )

        headers = {
            "id": "ID",
            "length": "Length (bp)",
            "gc_content": "GC%",
            "n_content": "N%",
            "qc_flag": "Flag",
        }
        widths = {"id": 130, "length": 80, "gc_content": 70,
                  "n_content": 60, "qc_flag": 80}

        for col in cols:
            self.qc_tree.heading(
                col, text=headers[col],
                command=lambda c=col: self._sort_qc(c, False),
            )
            self.qc_tree.column(col, width=widths[col], minwidth=50)

        vsb = ttk.Scrollbar(
            tree_container, orient="vertical", command=self.qc_tree.yview
        )
        self.qc_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.qc_tree.pack(fill="both", expand=True)

        # Populate rows
        for _, row in self.qc_df.iterrows():
            flag = row.get("qc_flag", "OK")
            tag = "flagged" if flag != "OK" else "ok"
            self.qc_tree.insert(
                "", "end",
                values=[
                    row["id"],
                    int(row["length"]),
                    f"{row['gc_content'] * 100:.1f}%",
                    f"{row['n_content'] * 100:.2f}%",
                    flag,
                ],
                tags=(tag,),
            )

        # Tag colors: flagged rows in light orange
        self.qc_tree.tag_configure("flagged", background="#FFF3E0")
        self.qc_tree.tag_configure("ok", background="")

        # --- Right: plots panel ---
        plots_frame = ctk.CTkFrame(content)
        plots_frame.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(
            plots_frame,
            text="Visualizations",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(10, 4))

        # Scrollable area for plot thumbnails + buttons
        scroll = ctk.CTkScrollableFrame(plots_frame)
        scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        plot_specs = [
            ("GC Content Distribution",  plots.plot_gc_distribution),
            ("GC Content by Gene",        plots.plot_gc_boxplot),
            ("Sequence Length Distribution", plots.plot_length_distribution),
            ("GC% vs. Length",            plots.plot_gc_vs_length),
            ("N Content Distribution",    plots.plot_n_content),
        ]

        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        for title, plot_fn in plot_specs:
            card = ctk.CTkFrame(scroll)
            card.pack(fill="x", pady=(0, 10))

            ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w",
            ).pack(anchor="w", padx=10, pady=(8, 4))

            # Generate figure and embed thumbnail
            fig = plot_fn(self.qc_df)
            self._figures[title] = fig

            thumb_frame = tk.Frame(card)
            thumb_frame.pack(fill="x", padx=10)

            canvas = FigureCanvasTkAgg(fig, master=thumb_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x")

            # "Open in window" button
            ctk.CTkButton(
                card,
                text="⤢  Open in window",
                height=28,
                width=160,
                font=ctk.CTkFont(size=11),
                fg_color="transparent",
                border_width=1,
                text_color=("gray20", "gray80"),
                hover_color=("gray85", "gray25"),
                command=lambda t=title: plots.open_plot_window(
                    self._figures[t], title=t
                ),
            ).pack(anchor="e", padx=10, pady=(4, 8))

    def _sort_qc(self, col: str, reverse: bool) -> None:
        """Sort QC Treeview by clicked column header.

        Args:
            col:     Column name to sort by.
            reverse: Sort direction.

        Returns:
            None
        """
        data = [
            (self.qc_tree.set(child, col), child)
            for child in self.qc_tree.get_children("")
        ]
        try:
            data.sort(key=lambda t: float(t[0].rstrip("%")), reverse=reverse)
        except ValueError:
            data.sort(key=lambda t: t[0].lower(), reverse=reverse)

        for index, (_, child) in enumerate(data):
            self.qc_tree.move(child, "", index)

        self.qc_tree.heading(
            col, command=lambda: self._sort_qc(col, not reverse)
        )


# ---------------------------------------------------------------------------
# Tab: Motif Analysis
# ---------------------------------------------------------------------------

class MotifAnalysisTab(ctk.CTkFrame):
    """Motif Analysis tab — predefined and custom motif search."""

    def __init__(self, parent: ctk.CTkTabview) -> None:
        super().__init__(parent, fg_color="transparent")

        self.df = None
        self._motif_module = None
        self._plots = None
        self._current_fig = None   # Current bar chart figure

        self._placeholder = ctk.CTkFrame(self, fg_color="transparent")
        self._placeholder.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self._placeholder,
            text="Motif Analysis",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(40, 8))
        ctk.CTkLabel(
            self._placeholder,
            text="Load a dataset in the Home tab to enable this analysis.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).pack()

    def reset(self) -> None:
        """Reset tab to placeholder state for a new dataset load.

        Args:
            None

        Returns:
            None
        """
        for widget in self.winfo_children():
            widget.destroy()
        self.df = None
        self._motif_module = None
        self._plots = None
        self._current_fig = None
        self._placeholder = ctk.CTkFrame(self, fg_color="transparent")
        self._placeholder.pack(fill="both", expand=True)
        ctk.CTkLabel(self._placeholder, text="Motif Analysis",
            font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(40, 8))
        ctk.CTkLabel(self._placeholder,
            text="Load a dataset in the Home tab to enable this analysis.",
            font=ctk.CTkFont(size=13), text_color="gray").pack()

    def load_data(self, df) -> None:
        """Receive DataFrame and build the Motif Analysis UI.

        Args:
            df: pandas DataFrame with sequence data.

        Returns:
            None
        """
        if self.df is not None:
            self.df = df
            return

        import importlib.util as _ilu

        self.df = df

        # Load motif_analyzer module
        _path = APP_DIR / "src" / "motif_analyzer.py"
        _spec = _ilu.spec_from_file_location("motif_analyzer", _path)
        self._motif_module = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(self._motif_module)

        # Load plots module
        _plt_path = APP_DIR / "src" / "plots.py"
        _spec2 = _ilu.spec_from_file_location("plots", _plt_path)
        self._plots = _ilu.module_from_spec(_spec2)
        _spec2.loader.exec_module(self._plots)

        self._placeholder.destroy()
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the full Motif Analysis UI.

        Args:
            None

        Returns:
            None
        """
        # --- Main layout: left = controls + results table, right = plot ---
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=16)
        content.columnconfigure(0, weight=2)
        content.columnconfigure(1, weight=3)
        content.rowconfigure(0, weight=1)

        # ── LEFT PANEL ──────────────────────────────────────────────────────
        left = ctk.CTkFrame(content)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            left,
            text="Motif search",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(10, 8))

        # --- Predefined motif selector ---
        ctk.CTkLabel(
            left,
            text="Predefined motifs:",
            font=ctk.CTkFont(size=12),
            anchor="w",
        ).pack(anchor="w", padx=12)

        motif_names = list(config.PREDEFINED_MOTIFS.keys())
        self.predefined_var = ctk.StringVar(value=motif_names[0])
        self.predefined_menu = ctk.CTkOptionMenu(
            left,
            variable=self.predefined_var,
            values=motif_names,
            width=300,
            font=ctk.CTkFont(size=11),
            command=self._on_predefined_selected,
        )
        self.predefined_menu.pack(fill="x", padx=12, pady=(4, 8))

        # Separator label
        ctk.CTkLabel(
            left,
            text="— or enter a custom motif —",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(pady=(0, 4))

        # --- Custom motif entry ---
        ctk.CTkLabel(
            left,
            text="Custom motif (A/C/G/T/N only):",
            font=ctk.CTkFont(size=12),
            anchor="w",
        ).pack(anchor="w", padx=12)

        entry_row = ctk.CTkFrame(left, fg_color="transparent")
        entry_row.pack(fill="x", padx=12, pady=(4, 4))

        self.custom_motif_var = ctk.StringVar()
        self.custom_entry = ctk.CTkEntry(
            entry_row,
            textvariable=self.custom_motif_var,
            placeholder_text="e.g. GAATTC",
            font=ctk.CTkFont(size=12),
            width=200,
        )
        self.custom_entry.pack(side="left")
        # Bind Enter key to run search
        self.custom_entry.bind("<Return>", lambda _: self._run_search())

        # Validation label
        self.validation_label = ctk.CTkLabel(
            left,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="red",
            anchor="w",
        )
        self.validation_label.pack(anchor="w", padx=12, pady=(0, 4))

        # --- Search button ---
        ctk.CTkButton(
            left,
            text="🔍  Search",
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._run_search,
        ).pack(fill="x", padx=12, pady=(4, 8))

        # --- Active motif label ---
        self.active_motif_label = ctk.CTkLabel(
            left,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#1F6AA5", "#4DA6FF"),
            anchor="w",
        )
        self.active_motif_label.pack(anchor="w", padx=12, pady=(0, 8))

        # --- Per-gene summary table ---
        ctk.CTkLabel(
            left,
            text="Results by gene:",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(0, 4))

        summary_container = tk.Frame(left)
        summary_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        summary_cols = [
            "Gene / Source", "Total occurrences",
            "Sequences with motif", "Total sequences", "Mean per sequence",
        ]
        self.summary_tree = ttk.Treeview(
            summary_container, columns=summary_cols, show="headings", height=8,
        )
        col_widths = {
            "Gene / Source": 130,
            "Total occurrences": 100,
            "Sequences with motif": 120,
            "Total sequences": 100,
            "Mean per sequence": 110,
        }
        for col in summary_cols:
            self.summary_tree.heading(col, text=col)
            self.summary_tree.column(
                col, width=col_widths.get(col, 100), minwidth=60, anchor="center"
            )

        vsb = ttk.Scrollbar(
            summary_container, orient="vertical", command=self.summary_tree.yview
        )
        self.summary_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.summary_tree.pack(fill="both", expand=True)

        # ── RIGHT PANEL ──────────────────────────────────────────────────────
        right = ctk.CTkFrame(content)
        right.grid(row=0, column=1, sticky="nsew")

        right_header = ctk.CTkFrame(right, fg_color="transparent")
        right_header.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            right_header,
            text="Occurrences by gene",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(side="left")

        ctk.CTkButton(
            right_header,
            text="⤢  Open in window",
            height=28,
            width=150,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=self._open_plot_window,
        ).pack(side="right")

        # Plot area
        self.plot_frame = tk.Frame(right)
        self.plot_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        # Per-sequence detail table below plot
        ctk.CTkLabel(
            right,
            text="Per-sequence detail:",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(4, 4))

        detail_container = tk.Frame(right)
        detail_container.pack(fill="x", padx=12, pady=(0, 12))

        detail_cols = ["id", "_source", "count", "positions"]
        self.detail_tree = ttk.Treeview(
            detail_container, columns=detail_cols, show="headings", height=6,
        )
        detail_widths = {"id": 140, "_source": 160, "count": 60, "positions": 200}
        detail_headers = {
            "id": "ID", "_source": "Gene / Source",
            "count": "Count", "positions": "Positions (1-based)",
        }
        for col in detail_cols:
            self.detail_tree.heading(col, text=detail_headers[col])
            self.detail_tree.column(
                col, width=detail_widths.get(col, 100), minwidth=50
            )

        hsb = ttk.Scrollbar(
            detail_container, orient="horizontal", command=self.detail_tree.xview
        )
        vsb2 = ttk.Scrollbar(
            detail_container, orient="vertical", command=self.detail_tree.yview
        )
        self.detail_tree.configure(
            xscrollcommand=hsb.set, yscrollcommand=vsb2.set
        )
        vsb2.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.detail_tree.pack(fill="both", expand=True)

        # Run initial search with first predefined motif
        self._on_predefined_selected(motif_names[0])

    def _on_predefined_selected(self, name: str) -> None:
        """Set the custom entry to the selected predefined motif sequence.

        Args:
            name: Display name of the selected predefined motif.

        Returns:
            None
        """
        motif_seq = config.PREDEFINED_MOTIFS.get(name, "")
        self.custom_motif_var.set(motif_seq)
        self.validation_label.configure(text="")

    def _run_search(self) -> None:
        """Validate the motif and run the search.

        Args:
            None

        Returns:
            None
        """
        motif = self.custom_motif_var.get().strip()

        # Validate
        valid, msg = self._motif_module.validate_motif(motif)
        if not valid:
            self.validation_label.configure(text=msg)
            return

        self.validation_label.configure(text="")
        motif = motif.upper()

        # Run search
        try:
            search_df = self._motif_module.search_motif(self.df, motif)
            summary_df = self._motif_module.summarize_by_gene(search_df)
        except Exception as e:
            messagebox.showerror("Motif Search Error", f"Search failed:\n{e}")
            return

        total = int(search_df["count"].sum())
        self.active_motif_label.configure(
            text=f"Motif: {motif}   |   Total occurrences: {total}"
        )

        # Populate summary table
        self.summary_tree.delete(*self.summary_tree.get_children())
        for _, row in summary_df.iterrows():
            self.summary_tree.insert("", "end", values=list(row))

        # Populate detail table
        self.detail_tree.delete(*self.detail_tree.get_children())
        for _, row in search_df.iterrows():
            tag = "found" if row["count"] > 0 else "notfound"
            self.detail_tree.insert(
                "", "end",
                values=[row["id"], row["_source"], row["count"], row["positions"]],
                tags=(tag,),
            )
        self.detail_tree.tag_configure("found", background="#E8F5E9")
        self.detail_tree.tag_configure("notfound", background="")

        # Update plot
        self._update_plot(summary_df, motif)

    def _update_plot(self, summary_df, motif: str) -> None:
        """Regenerate and embed the occurrences bar chart.

        Args:
            summary_df: Per-gene summary DataFrame.
            motif:      Motif string for chart title.

        Returns:
            None
        """
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        self._current_fig = self._plots.plot_motif_by_gene(summary_df, motif)
        canvas = FigureCanvasTkAgg(self._current_fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _open_plot_window(self) -> None:
        """Open the current motif plot in a standalone window.

        Args:
            None

        Returns:
            None
        """
        if self._current_fig is not None:
            motif = self.custom_motif_var.get().strip().upper()
            self._plots.open_plot_window(
                self._current_fig,
                title=f"Motif '{motif}' — occurrences by gene",
            )
        else:
            messagebox.showinfo("No plot", "Run a search first.")


# ---------------------------------------------------------------------------
# Tab: ORF Analysis
# ---------------------------------------------------------------------------

class ORFAnalysisTab(ctk.CTkFrame):
    """ORF Analysis tab — open reading frame identification."""

    def __init__(self, parent: ctk.CTkTabview) -> None:
        super().__init__(parent, fg_color="transparent")

        self.df = None
        self.orf_df = None
        self._orf_module = None
        self._plots = None
        self._current_figs = {}   # Stores current figures for popup reuse

        self._placeholder = ctk.CTkFrame(self, fg_color="transparent")
        self._placeholder.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self._placeholder,
            text="ORF Analysis",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(40, 8))
        ctk.CTkLabel(
            self._placeholder,
            text="Load a dataset in the Home tab to enable this analysis.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).pack()

    def reset(self) -> None:
        """Reset tab to placeholder state for a new dataset load.

        Args:
            None

        Returns:
            None
        """
        for widget in self.winfo_children():
            widget.destroy()
        self.df = None
        self.orf_df = None
        self._orf_module = None
        self._plots = None
        self._current_figs = {}
        self._placeholder = ctk.CTkFrame(self, fg_color="transparent")
        self._placeholder.pack(fill="both", expand=True)
        ctk.CTkLabel(self._placeholder, text="ORF Analysis",
            font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(40, 8))
        ctk.CTkLabel(self._placeholder,
            text="Load a dataset in the Home tab to enable this analysis.",
            font=ctk.CTkFont(size=13), text_color="gray").pack()

    def load_data(self, df) -> None:
        """Receive DataFrame and build the ORF Analysis UI.

        Args:
            df: pandas DataFrame with sequence data.

        Returns:
            None
        """
        if self.df is not None:
            self.df = df
            return

        import importlib.util as _ilu

        self.df = df

        # Load orf_analyzer module
        _path = APP_DIR / "src" / "orf_analyzer.py"
        _spec = _ilu.spec_from_file_location("orf_analyzer", _path)
        self._orf_module = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(self._orf_module)

        # Load plots module
        _plt_path = APP_DIR / "src" / "plots.py"
        _spec2 = _ilu.spec_from_file_location("plots", _plt_path)
        self._plots = _ilu.module_from_spec(_spec2)
        _spec2.loader.exec_module(self._plots)

        self._placeholder.destroy()
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the full ORF Analysis UI.

        Args:
            None

        Returns:
            None
        """
        # --- Top controls bar ---
        controls = ctk.CTkFrame(self)
        controls.pack(fill="x", padx=16, pady=(12, 8))

        ctk.CTkLabel(
            controls,
            text="Minimum ORF length (bp):",
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(12, 8), pady=8)

        self.min_len_var = ctk.StringVar(
            value=str(config.ORF_MIN_LENGTH)
        )
        ctk.CTkEntry(
            controls,
            textvariable=self.min_len_var,
            width=80,
            font=ctk.CTkFont(size=12),
        ).pack(side="left", pady=8)

        ctk.CTkButton(
            controls,
            text="▶  Run ORF Analysis",
            height=36,
            width=180,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._run_analysis,
        ).pack(side="left", padx=(16, 0), pady=8)

        self.status_label = ctk.CTkLabel(
            controls,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.status_label.pack(side="left", padx=(16, 0), pady=8)

        # --- Main layout: left = summary table, right = plots ---
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        content.columnconfigure(0, weight=2)
        content.columnconfigure(1, weight=3)
        content.rowconfigure(0, weight=1)

        # ── LEFT: summary table + per-sequence table ─────────────────────
        left = ctk.CTkFrame(content)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            left,
            text="Summary by gene",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(10, 4))

        summary_container = tk.Frame(left)
        summary_container.pack(fill="x", padx=12, pady=(0, 8))

        summary_cols = [
            "Gene / Source", "Total ORFs",
            "Mean ORFs/sequence", "Mean longest ORF", "Max ORF length (bp)",
        ]
        self.summary_tree = ttk.Treeview(
            summary_container, columns=summary_cols,
            show="headings", height=7,
        )
        col_widths = {
            "Gene / Source": 120,
            "Total ORFs": 80,
            "Mean ORFs/sequence": 110,
            "Mean longest ORF": 110,
            "Max ORF length (bp)": 120,
        }
        for col in summary_cols:
            self.summary_tree.heading(col, text=col)
            self.summary_tree.column(
                col, width=col_widths.get(col, 100),
                minwidth=60, anchor="center",
            )

        vsb = ttk.Scrollbar(
            summary_container, orient="vertical",
            command=self.summary_tree.yview,
        )
        self.summary_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.summary_tree.pack(fill="x", expand=False)

        # Per-sequence table
        ctk.CTkLabel(
            left,
            text="Per-sequence results",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(4, 4))

        ctk.CTkLabel(
            left,
            text="Double-click a row to see all ORFs for that sequence.",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(0, 4))

        detail_container = tk.Frame(left)
        detail_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        detail_cols = ["id", "_source", "n_orfs", "longest_orf", "mean_orf_len"]
        detail_headers = {
            "id": "ID", "_source": "Gene / Source",
            "n_orfs": "ORFs", "longest_orf": "Longest (bp)",
            "mean_orf_len": "Mean (bp)",
        }
        detail_widths = {
            "id": 140, "_source": 140,
            "n_orfs": 50, "longest_orf": 90, "mean_orf_len": 80,
        }
        self.detail_tree = ttk.Treeview(
            detail_container, columns=detail_cols, show="headings",
        )
        for col in detail_cols:
            self.detail_tree.heading(col, text=detail_headers[col])
            self.detail_tree.column(
                col, width=detail_widths.get(col, 80),
                minwidth=50, anchor="center",
            )

        vsb2 = ttk.Scrollbar(
            detail_container, orient="vertical",
            command=self.detail_tree.yview,
        )
        self.detail_tree.configure(yscrollcommand=vsb2.set)
        vsb2.pack(side="right", fill="y")
        self.detail_tree.pack(fill="both", expand=True)

        # Double-click to show full ORF list for a sequence
        self.detail_tree.bind("<Double-1>", self._on_row_double_click)

        # ── RIGHT: plots ─────────────────────────────────────────────────
        right = ctk.CTkFrame(content)
        right.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(
            right,
            text="Visualizations",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(10, 4))

        self.plots_scroll = ctk.CTkScrollableFrame(right)
        self.plots_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Placeholder message until analysis is run
        self._plots_placeholder = ctk.CTkLabel(
            self.plots_scroll,
            text="Click 'Run ORF Analysis' to generate plots.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self._plots_placeholder.pack(pady=40)

    def _run_analysis(self) -> None:
        """Run ORF analysis with current min_length setting.

        Args:
            None

        Returns:
            None
        """
        try:
            min_len = int(self.min_len_var.get())
        except ValueError:
            messagebox.showerror(
                "Invalid input", "Minimum ORF length must be an integer."
            )
            return

        self.status_label.configure(
            text="Running ORF analysis...", text_color="gray"
        )
        self.update()

        try:
            self.orf_df = self._orf_module.run_orf_analysis(
                self.df, min_length=min_len
            )
            summary_df = self._orf_module.summarize_by_gene(self.orf_df)
        except Exception as e:
            messagebox.showerror("ORF Error", f"Analysis failed:\n{e}")
            self.status_label.configure(text="Error.", text_color="red")
            return

        total_orfs = int(self.orf_df["n_orfs"].sum())
        self.status_label.configure(
            text=f"✓ Done — {total_orfs} ORFs found (min {min_len} bp)",
            text_color="green" if total_orfs > 0 else "orange",
        )

        if total_orfs == 0:
            self.status_label.configure(
                text=f"⚠  0 ORFs found (min {min_len} bp) — "
                     f"sequences may be too short or file may not contain valid DNA.",
                text_color="orange",
            )

        # Populate summary table
        self.summary_tree.delete(*self.summary_tree.get_children())
        for _, row in summary_df.iterrows():
            self.summary_tree.insert("", "end", values=list(row))

        # Populate per-sequence table
        self.detail_tree.delete(*self.detail_tree.get_children())
        for _, row in self.orf_df.iterrows():
            tag = "has_orfs" if row["n_orfs"] > 0 else "no_orfs"
            self.detail_tree.insert(
                "", "end",
                values=[
                    row["id"], row["_source"],
                    row["n_orfs"], row["longest_orf"], row["mean_orf_len"],
                ],
                tags=(tag,),
            )
        self.detail_tree.tag_configure("has_orfs", background="#E8F5E9")
        self.detail_tree.tag_configure("no_orfs", background="")

        # Update plots
        self._update_plots(summary_df)

    def _update_plots(self, summary_df) -> None:
        """Regenerate and embed ORF plots.

        Args:
            summary_df: Per-gene summary DataFrame.

        Returns:
            None
        """
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        # Clear existing content
        for widget in self.plots_scroll.winfo_children():
            widget.destroy()
        self._current_figs = {}

        plot_specs = [
            ("Total ORFs by gene",              "counts",
             lambda: self._plots.plot_orf_counts_by_gene(summary_df)),
            ("Longest ORF length by gene",       "boxplot",
             lambda: self._plots.plot_orf_length_distribution(self.orf_df)),
            ("Distribution of longest ORF lengths", "histogram",
             lambda: self._plots.plot_orf_length_histogram(self.orf_df)),
        ]

        for title, key, plot_fn in plot_specs:
            card = ctk.CTkFrame(self.plots_scroll)
            card.pack(fill="x", pady=(0, 10))

            ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w",
            ).pack(anchor="w", padx=10, pady=(8, 4))

            fig = plot_fn()
            self._current_figs[key] = fig

            thumb_frame = tk.Frame(card)
            thumb_frame.pack(fill="x", padx=10)
            canvas = FigureCanvasTkAgg(fig, master=thumb_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x")

            ctk.CTkButton(
                card,
                text="⤢  Open in window",
                height=28,
                width=160,
                font=ctk.CTkFont(size=11),
                fg_color="transparent",
                border_width=1,
                text_color=("gray20", "gray80"),
                hover_color=("gray85", "gray25"),
                command=lambda t=title, k=key: self._plots.open_plot_window(
                    self._current_figs[k], title=t
                ),
            ).pack(anchor="e", padx=10, pady=(4, 8))

    def _on_row_double_click(self, event) -> None:
        """Open a popup with all ORFs for the double-clicked sequence.

        Args:
            event: Tkinter event object.

        Returns:
            None
        """
        selected = self.detail_tree.selection()
        if not selected:
            return

        values = self.detail_tree.item(selected[0], "values")
        seq_id = values[0]

        try:
            min_len = int(self.min_len_var.get())
        except ValueError:
            min_len = config.ORF_MIN_LENGTH

        orfs = self._orf_module.get_sequence_orfs(self.df, seq_id, min_len)
        self._show_orf_popup(seq_id, orfs)

    def _show_orf_popup(self, seq_id: str, orfs: list[dict]) -> None:
        """Show a popup window with all ORFs for a sequence.

        Args:
            seq_id: Sequence identifier.
            orfs:   List of ORF dicts from orf_analyzer.find_orfs().

        Returns:
            None
        """
        popup = tk.Toplevel(self)
        popup.title(f"ORFs — {seq_id}")
        popup.geometry("720x440")

        # Center on screen
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() - 720) // 2
        y = (popup.winfo_screenheight() - 440) // 2
        popup.geometry(f"720x440+{x}+{y}")

        header = tk.Frame(popup)
        header.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(
            header,
            text=f"Sequence: {seq_id}",
            font=("Segoe UI", 12, "bold"),
        ).pack(side="left")
        tk.Label(
            header,
            text=f"  —  {len(orfs)} ORF(s) found",
            font=("Segoe UI", 11),
            fg="gray",
        ).pack(side="left")

        # ORF table
        container = tk.Frame(popup)
        container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        cols = ["frame", "start", "end", "length", "sequence"]
        headers = {
            "frame": "Frame", "start": "Start", "end": "End",
            "length": "Length (bp)", "sequence": "Sequence (preview)",
        }
        widths = {
            "frame": 55, "start": 70, "end": 70,
            "length": 90, "sequence": 340,
        }

        tree = ttk.Treeview(container, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=headers[col])
            tree.column(col, width=widths[col], minwidth=50, anchor="center")

        vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        if orfs:
            for orf in orfs:
                preview = orf["sequence"][:40] + "..." \
                    if len(orf["sequence"]) > 40 else orf["sequence"]
                tree.insert("", "end", values=[
                    f"+{orf['frame']}",
                    orf["start"],
                    orf["end"],
                    orf["length"],
                    preview,
                ])
        else:
            tree.insert("", "end", values=["—", "—", "—", "—",
                                           "No ORFs found for this sequence."])

        tk.Button(
            popup, text="Close", command=popup.destroy,
            font=("Segoe UI", 11), width=12,
        ).pack(pady=(0, 12))


# ---------------------------------------------------------------------------
# Tab: Statistics
# ---------------------------------------------------------------------------

class StatisticsTab(ctk.CTkFrame):
    """Statistics tab — statistical tests and correlation matrix."""

    def __init__(self, parent: ctk.CTkTabview) -> None:
        super().__init__(parent, fg_color="transparent")

        self.qc_df = None
        self._stats = None
        self._plots = None
        self._last_results = []

        self._placeholder = ctk.CTkFrame(self, fg_color="transparent")
        self._placeholder.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self._placeholder,
            text="Statistics",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(40, 8))
        ctk.CTkLabel(
            self._placeholder,
            text="Load a dataset in the Home tab to enable this analysis.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).pack()


    def _show_error(self, message: str) -> None:
        """Replace placeholder with a critical error message.

        Args:
            message: Error description to display.

        Returns:
            None
        """
        for widget in self._placeholder.winfo_children():
            widget.destroy()
        tk.Label(
            self._placeholder,
            text="❌  This tab could not be loaded",
            font=("Segoe UI", 14, "bold"),
            fg="#DC2626",
        ).pack(pady=(40, 8))
        tk.Label(
            self._placeholder,
            text=message,
            font=("Segoe UI", 11),
            fg="#6B7280",
            wraplength=500,
            justify="center",
        ).pack()
        tk.Label(
            self._placeholder,
            text="Please load a clean_dataset_*.csv file from results/tables/",
            font=("Segoe UI", 11),
            fg="#6B7280",
            wraplength=500,
            justify="center",
        ).pack(pady=(8, 0))
    def reset(self) -> None:
        """Reset tab to placeholder state for a new dataset load.

        Args:
            None

        Returns:
            None
        """
        for widget in self.winfo_children():
            widget.destroy()
        self.qc_df = None
        self._stats = None
        self._plots = None
        self._last_results = []
        self._placeholder = ctk.CTkFrame(self, fg_color="transparent")
        self._placeholder.pack(fill="both", expand=True)
        ctk.CTkLabel(self._placeholder, text="Statistics",
            font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(40, 8))
        ctk.CTkLabel(self._placeholder,
            text="Load a dataset in the Home tab to enable this analysis.",
            font=ctk.CTkFont(size=13), text_color="gray").pack()

    def load_data(self, df) -> None:
        """Receive DataFrame, compute QC metrics and build the Statistics UI.

        Args:
            df: pandas DataFrame with sequence data.

        Returns:
            None
        """
        # Guard: build UI only once
        if self.qc_df is not None:
            return

        import importlib.util as _ilu

        # Load analyzer to get QC metrics
        _ana_path = APP_DIR / "src" / "analyzer.py"
        _spec = _ilu.spec_from_file_location("app_analyzer", _ana_path)
        analyzer = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(analyzer)

        # Load stats module
        _st_path = APP_DIR / "src" / "stats.py"
        _spec2 = _ilu.spec_from_file_location("app_stats", _st_path)
        self._stats = _ilu.module_from_spec(_spec2)
        _spec2.loader.exec_module(self._stats)

        # Load plots module (for correlation heatmap)
        _plt_path = APP_DIR / "src" / "plots.py"
        _spec3 = _ilu.spec_from_file_location("plots", _plt_path)
        self._plots = _ilu.module_from_spec(_spec3)
        _spec3.loader.exec_module(self._plots)

        try:
            self.qc_df = analyzer.run_quality_analysis(df)
        except Exception as e:
            self._show_error(str(e))
            return

        self._placeholder.destroy()
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the full Statistics UI.

        Args:
            None

        Returns:
            None
        """
        # --- Main layout: left = controls + results, right = correlation ---
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=16)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        # ── LEFT PANEL ──────────────────────────────────────────────────────
        left = ctk.CTkFrame(content)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            left,
            text="Statistical tests",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(10, 8))

        # --- Controls ---
        controls = ctk.CTkFrame(left, fg_color="transparent")
        controls.pack(fill="x", padx=12)

        # Metric selector
        metric_row = ctk.CTkFrame(controls, fg_color="transparent")
        metric_row.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(
            metric_row, text="Metric:", width=80,
            font=ctk.CTkFont(size=12),
        ).pack(side="left")
        self.metric_var = ctk.StringVar(value="gc_content")
        ctk.CTkOptionMenu(
            metric_row,
            variable=self.metric_var,
            values=["gc_content", "n_content", "length"],
            width=180,
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(8, 0))

        # Test selector
        test_row = ctk.CTkFrame(controls, fg_color="transparent")
        test_row.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(
            test_row, text="Test:", width=80,
            font=ctk.CTkFont(size=12),
        ).pack(side="left")
        self.test_var = ctk.StringVar(value="ANOVA")
        self.test_menu = ctk.CTkOptionMenu(
            test_row,
            variable=self.test_var,
            values=["ANOVA", "t-test", "Mann-Whitney U"],
            width=180,
            font=ctk.CTkFont(size=12),
            command=self._on_test_changed,
        )
        self.test_menu.pack(side="left", padx=(8, 0))

        # Group selectors (shown only for t-test and Mann-Whitney)
        self.group_frame = ctk.CTkFrame(controls, fg_color="transparent")
        self.group_frame.pack(fill="x")

        sources = sorted(self.qc_df["_source"].unique()) \
            if "_source" in self.qc_df.columns else []

        group_a_row = ctk.CTkFrame(self.group_frame, fg_color="transparent")
        group_a_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(
            group_a_row, text="Group A:", width=80,
            font=ctk.CTkFont(size=12),
        ).pack(side="left")
        self.group_a_var = ctk.StringVar(
            value=sources[0] if sources else ""
        )
        self.group_a_menu = ctk.CTkOptionMenu(
            group_a_row,
            variable=self.group_a_var,
            values=sources if sources else ["—"],
            width=220,
            font=ctk.CTkFont(size=11),
        )
        self.group_a_menu.pack(side="left", padx=(8, 0))

        group_b_row = ctk.CTkFrame(self.group_frame, fg_color="transparent")
        group_b_row.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(
            group_b_row, text="Group B:", width=80,
            font=ctk.CTkFont(size=12),
        ).pack(side="left")
        self.group_b_var = ctk.StringVar(
            value=sources[1] if len(sources) > 1 else ""
        )
        self.group_b_menu = ctk.CTkOptionMenu(
            group_b_row,
            variable=self.group_b_var,
            values=sources if sources else ["—"],
            width=220,
            font=ctk.CTkFont(size=11),
        )
        self.group_b_menu.pack(side="left", padx=(8, 0))

        # Hide group selectors for ANOVA (default)
        self.group_frame.pack_forget()

        # Run button
        ctk.CTkButton(
            left,
            text="▶  Run Test",
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._run_test,
        ).pack(fill="x", padx=12, pady=(8, 4))

        # Result interpretation label
        self.result_label = ctk.CTkLabel(
            left,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=420,
            justify="left",
        )
        self.result_label.pack(anchor="w", padx=12, pady=(4, 8))

        # Results Treeview
        ctk.CTkLabel(
            left,
            text="Test results",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(0, 4))

        tree_container = tk.Frame(left)
        tree_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.result_tree = ttk.Treeview(
            tree_container,
            columns=["Parameter", "Value"],
            show="headings",
            height=10,
        )
        self.result_tree.heading("Parameter", text="Parameter")
        self.result_tree.heading("Value", text="Value")
        self.result_tree.column("Parameter", width=180, minwidth=120)
        self.result_tree.column("Value", width=260, minwidth=120)

        vsb = ttk.Scrollbar(
            tree_container, orient="vertical", command=self.result_tree.yview
        )
        self.result_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.result_tree.pack(fill="both", expand=True)

        # ── RIGHT PANEL: Correlation matrix ─────────────────────────────────
        right = ctk.CTkFrame(content)
        right.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(
            right,
            text="Correlation matrix",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(10, 4))

        # Method toggle
        method_row = ctk.CTkFrame(right, fg_color="transparent")
        method_row.pack(fill="x", padx=12, pady=(0, 6))
        ctk.CTkLabel(
            method_row, text="Method:",
            font=ctk.CTkFont(size=12),
        ).pack(side="left")
        self.corr_method_var = ctk.StringVar(value="pearson")
        ctk.CTkOptionMenu(
            method_row,
            variable=self.corr_method_var,
            values=["pearson", "spearman"],
            width=140,
            font=ctk.CTkFont(size=12),
            command=lambda _: self._update_correlation(),
        ).pack(side="left", padx=(8, 0))

        # Correlation heatmap area
        self.corr_frame = tk.Frame(right)
        self.corr_frame.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        ctk.CTkButton(
            right,
            text="⤢  Open in window",
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=self._open_corr_window,
        ).pack(anchor="e", padx=12, pady=(0, 8))

        # Draw initial correlation heatmap
        self._corr_fig = None
        self._update_correlation()

    def _on_test_changed(self, value: str) -> None:
        """Show or hide group selectors depending on selected test.

        Args:
            value: Selected test name.

        Returns:
            None
        """
        if value == "ANOVA":
            self.group_frame.pack_forget()
        else:
            self.group_frame.pack(fill="x")

    def _run_test(self) -> None:
        """Run the selected statistical test and display results.

        Args:
            None

        Returns:
            None
        """
        metric = self.metric_var.get()
        test = self.test_var.get()

        if test == "ANOVA":
            result = self._stats.run_anova(self.qc_df, metric)
        elif test == "t-test":
            result = self._stats.run_ttest(
                self.qc_df, metric,
                self.group_a_var.get(), self.group_b_var.get(),
            )
        else:  # Mann-Whitney U
            result = self._stats.run_mannwhitney(
                self.qc_df, metric,
                self.group_a_var.get(), self.group_b_var.get(),
            )

        # Store result for ReportTab
        if "error" not in result:
            self._last_results = [result]

        # Show interpretation
        if "error" in result:
            self.result_label.configure(
                text=result["error"], text_color="red"
            )
        else:
            color = "#2CA02C" if result.get("significant") else "#E05A2B"
            self.result_label.configure(
                text=result.get("note", ""), text_color=color
            )

        # Populate results Treeview
        result_df = self._stats.result_to_dataframe(result)
        self.result_tree.delete(*self.result_tree.get_children())
        for _, row in result_df.iterrows():
            self.result_tree.insert(
                "", "end", values=[row["Parameter"], row["Value"]]
            )

    def _update_correlation(self) -> None:
        """Recompute and redraw the correlation heatmap.

        Args:
            None

        Returns:
            None
        """
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        method = self.corr_method_var.get()
        corr_matrix = self._stats.compute_correlation_matrix(
            self.qc_df, method=method
        )

        # Build heatmap figure
        fig, ax = plt.subplots(figsize=(4.0, 3.2), dpi=100)
        fig.patch.set_facecolor("#F5F5F5")

        im = ax.imshow(corr_matrix.values, cmap="coolwarm", vmin=-1, vmax=1)
        fig.colorbar(im, ax=ax, shrink=0.8)

        labels = list(corr_matrix.columns)
        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=9, rotation=20, ha="right")
        ax.set_yticklabels(labels, fontsize=9)

        # Annotate cells with correlation values
        for i in range(len(labels)):
            for j in range(len(labels)):
                ax.text(
                    j, i,
                    f"{corr_matrix.values[i, j]:.2f}",
                    ha="center", va="center",
                    fontsize=10, fontweight="bold",
                    color="white" if abs(corr_matrix.values[i, j]) > 0.5
                    else "black",
                )

        ax.set_title(
            f"Correlation matrix ({method.capitalize()})",
            fontsize=11, fontweight="bold", pad=8,
        )
        fig.tight_layout()

        self._corr_fig = fig

        # Clear previous canvas and embed new one
        for widget in self.corr_frame.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=self.corr_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _open_corr_window(self) -> None:
        """Open the correlation heatmap in a standalone window.

        Args:
            None

        Returns:
            None
        """
        if self._corr_fig is not None:
            self._plots.open_plot_window(
                self._corr_fig,
                title=f"Correlation Matrix ({self.corr_method_var.get().capitalize()})",
            )


# ---------------------------------------------------------------------------
# Tab: Report
# ---------------------------------------------------------------------------

class ReportTab(ctk.CTkFrame):
    """Report tab — generate and export analysis report."""

    def __init__(self, parent: ctk.CTkTabview) -> None:
        super().__init__(parent, fg_color="transparent")

        self.qc_df = None
        self.summary_df = None
        self.gene_df = None
        self.dataset_path = ""
        self.huba_report_loaded = False
        self._report_module = None
        self._analyzer = None
        self._plots = None
        self._stats = None
        self._corr_fig = None       # Injected from StatisticsTab if available
        self._stat_results = []     # Injected from StatisticsTab if available
        self._huba_report_text = "" # HUBA REPORT.md text for PDF export

        self._placeholder = ctk.CTkFrame(self, fg_color="transparent")
        self._placeholder.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self._placeholder,
            text="Report",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(40, 8))
        ctk.CTkLabel(
            self._placeholder,
            text="Load a dataset in the Home tab to enable report generation.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).pack()


    def _show_error(self, message: str) -> None:
        """Replace placeholder with a critical error message.

        Args:
            message: Error description to display.

        Returns:
            None
        """
        for widget in self._placeholder.winfo_children():
            widget.destroy()
        tk.Label(
            self._placeholder,
            text="❌  This tab could not be loaded",
            font=("Segoe UI", 14, "bold"),
            fg="#DC2626",
        ).pack(pady=(40, 8))
        tk.Label(
            self._placeholder,
            text=message,
            font=("Segoe UI", 11),
            fg="#6B7280",
            wraplength=500,
            justify="center",
        ).pack()
        tk.Label(
            self._placeholder,
            text="Please load a clean_dataset_*.csv file from results/tables/",
            font=("Segoe UI", 11),
            fg="#6B7280",
            wraplength=500,
            justify="center",
        ).pack(pady=(8, 0))
    def reset(self) -> None:
        """Reset tab to placeholder state for a new dataset load.

        Args:
            None

        Returns:
            None
        """
        for widget in self.winfo_children():
            widget.destroy()
        self.qc_df = None
        self.summary_df = None
        self.gene_df = None
        self.dataset_path = ""
        self.huba_report_loaded = False
        self._report_module = None
        self._analyzer = None
        self._plots = None
        self._stats = None
        self._corr_fig = None
        self._stat_results = []
        self._placeholder = ctk.CTkFrame(self, fg_color="transparent")
        self._placeholder.pack(fill="both", expand=True)
        ctk.CTkLabel(self._placeholder, text="Report",
            font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(40, 8))
        ctk.CTkLabel(self._placeholder,
            text="Load a dataset in the Home tab to enable report generation.",
            font=ctk.CTkFont(size=13), text_color="gray").pack()

    def load_data(self, df) -> None:
        """Receive DataFrame, prepare data and build the Report UI.

        Args:
            df: pandas DataFrame with sequence data.

        Returns:
            None
        """
        # Guard: build UI only once
        if self.qc_df is not None:
            return

        import importlib.util as _ilu

        # Load required modules
        for mod_name, rel_path, attr in [
            ("app_analyzer", "src/analyzer.py", "_analyzer"),
            ("app_plots",    "src/plots.py",    "_plots"),
            ("app_stats",    "src/stats.py",    "_stats"),
            ("app_report",   "src/report.py",   "_report_module"),
        ]:
            path = APP_DIR / rel_path
            spec = _ilu.spec_from_file_location(mod_name, path)
            mod = _ilu.module_from_spec(spec)
            spec.loader.exec_module(mod)
            setattr(self, attr, mod)

        try:
            self.qc_df = self._analyzer.run_quality_analysis(df)
            self.qc_df = self._analyzer.flag_outliers(
                self.qc_df,
                gc_low=config.GC_LOW_THRESHOLD,
                gc_high=config.GC_HIGH_THRESHOLD,
                n_warning=config.N_WARNING_THRESHOLD,
            )
            self.summary_df = self._analyzer.compute_summary_stats(self.qc_df)
            self.gene_df = self._analyzer.compute_gene_stats(self.qc_df)
        except Exception as e:
            self._show_error(str(e))
            return

        self._placeholder.destroy()
        self._build_ui()

    def set_dataset_info(self, dataset_path: str, huba_loaded: bool) -> None:
        """Set dataset metadata for use in the report header.

        Called by HomeTab after loading a dataset.

        Args:
            dataset_path: Path string of the loaded CSV file.
            huba_loaded:  Whether HUBA REPORT.md was loaded.

        Returns:
            None
        """
        self.dataset_path = dataset_path
        self.huba_report_loaded = huba_loaded

    def _build_ui(self) -> None:
        """Build the full Report tab UI.

        Args:
            None

        Returns:
            None
        """
        # --- Top: generate button + status ---
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            top,
            text="Generate Report",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")

        self.status_label = ctk.CTkLabel(
            top,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.status_label.pack(side="left", padx=(16, 0))

        # --- Options frame ---
        options = ctk.CTkFrame(self)
        options.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(
            options,
            text="Output directory:",
            font=ctk.CTkFont(size=12),
        ).grid(row=0, column=0, padx=(12, 8), pady=10, sticky="w")

        self.output_dir_var = ctk.StringVar(
            value=str(PROJECT_ROOT / "results" / "app_output")
        )
        ctk.CTkEntry(
            options,
            textvariable=self.output_dir_var,
            width=380,
            font=ctk.CTkFont(size=11),
        ).grid(row=0, column=1, padx=(0, 8), pady=10)

        ctk.CTkButton(
            options,
            text="Browse",
            width=80,
            height=30,
            font=ctk.CTkFont(size=11),
            command=self._browse_output_dir,
        ).grid(row=0, column=2, padx=(0, 12), pady=10)

        # Include stat results checkbox
        self.include_stats_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options,
            text="Include statistical test results (if any were run in Statistics tab)",
            variable=self.include_stats_var,
            font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, columnspan=3, padx=12, pady=(0, 10), sticky="w")

        # --- Generate buttons ---
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 8))
        btn_row.columnconfigure(0, weight=1)
        btn_row.columnconfigure(1, weight=1)

        ctk.CTkButton(
            btn_row,
            text="📄  Generate Markdown",
            height=44,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._generate,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkButton(
            btn_row,
            text="📑  Generate PDF",
            height=44,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2CA02C",
            hover_color="#1a7a1a",
            command=self._generate_pdf,
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        # --- Preview area ---
        ctk.CTkLabel(
            self,
            text="Report preview",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(anchor="w", padx=16, pady=(4, 4))

        self.preview_box = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Courier New", size=11),
            wrap="none",
            state="disabled",
        )
        self.preview_box.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self._show_preview_placeholder()

    def _generate_pdf(self) -> None:
        """Show section selector dialog then generate PDF report.

        Args:
            None

        Returns:
            None
        """
        # Get live references from sibling tabs
        app = self.winfo_toplevel()
        stats_tab = getattr(app, "stats_tab", None)
        orf_tab   = getattr(app, "orf_tab", None)

        stat_results = getattr(stats_tab, "_last_results", [])             if stats_tab else []
        corr_fig = getattr(stats_tab, "_corr_fig", None)             if stats_tab else None
        orf_df = getattr(orf_tab, "orf_df", None)             if orf_tab else None

        # Show section selector dialog
        selections = self._show_pdf_section_dialog(
            has_stats=bool(stat_results),
            has_corr=corr_fig is not None,
            has_orf=orf_df is not None,
        )
        if selections is None:
            return  # User cancelled

        output_dir = Path(self.output_dir_var.get())
        self.status_label.configure(
            text="Generating PDF...", text_color="gray"
        )
        self.update()

        try:
            pdf_path = self._report_module.generate_pdf(
                qc_df=self.qc_df,
                summary_df=self.summary_df if selections["qc_stats"] else None,
                gene_df=self.gene_df if selections["gene_stats"] else None,
                plots_module=self._plots,
                output_dir=output_dir,
                dataset_path=self.dataset_path,
                huba_report_loaded=self.huba_report_loaded,
                huba_report_text=self._huba_report_text
                    if selections["huba_report"] else "",
                stat_results=stat_results if selections["stat_results"] else [],
                corr_fig=corr_fig if selections["correlation"] else None,
                orf_df=orf_df if selections["orf"] else None,
                include_plots=selections["plots"],
            )
        except Exception as e:
            self.status_label.configure(text=f"PDF error: {e}", text_color="red")
            messagebox.showerror("PDF Error", f"Could not generate PDF:\n{e}")
            return

        self.status_label.configure(
            text=f"✓ PDF saved to: {pdf_path}", text_color="green"
        )
        messagebox.showinfo(
            "PDF generated",
            f"PDF report saved successfully:\n{pdf_path}",
        )

    def _show_pdf_section_dialog(
        self,
        has_stats: bool,
        has_corr: bool,
        has_orf: bool,
    ) -> dict | None:
        """Show a dialog for the user to select which sections to include in PDF.

        Args:
            has_stats: Whether statistical test results are available.
            has_corr:  Whether correlation matrix is available.
            has_orf:   Whether ORF analysis results are available.

        Returns:
            Dict of section keys → bool, or None if user cancelled.
        """
        result = {"cancelled": True}

        dialog = tk.Toplevel(self)
        dialog.title("Generate PDF — Select sections")
        dialog.resizable(False, False)

        # Center relative to parent window
        self.winfo_toplevel().update_idletasks()
        px = self.winfo_toplevel().winfo_x()
        py = self.winfo_toplevel().winfo_y()
        pw = self.winfo_toplevel().winfo_width()
        ph = self.winfo_toplevel().winfo_height()
        dialog.update_idletasks()
        dw, dh = 420, 500
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        dialog.geometry(f"{dw}x{dh}+{x}+{y}")

        tk.Label(
            dialog,
            text="📑  Select sections to include in PDF",
            font=("Segoe UI", 13, "bold"),
            fg="#1F6AA5",
        ).pack(anchor="w", padx=20, pady=(16, 8))

        tk.Label(
            dialog,
            text="Greyed out sections have no data available.",
            font=("Segoe UI", 9),
            fg="gray",
        ).pack(anchor="w", padx=20, pady=(0, 8))

        frame = tk.Frame(dialog, relief="flat", bd=1,
                         bg="#F9FAFB", padx=12, pady=8)
        frame.pack(fill="x", padx=20)

        # Section definitions: (key, label, always_available)
        sections = [
            ("cover",       "Cover page (dataset info)",        True),
            ("qc_stats",    "Quality Control statistics",       True),
            ("gene_stats",  "Per-gene statistics",              True),
            ("plots",       "QC Visualizations (all plots)",    True),
            ("stat_results","Statistical test results",         has_stats),
            ("correlation", "Correlation matrix",               has_corr),
            ("orf",         "ORF Analysis results",             has_orf),
            ("huba_report", "HUBA Pipeline Report",             True),
        ]

        vars_ = {}
        for key, label, available in sections:
            var = tk.BooleanVar(value=available)
            vars_[key] = var
            cb = tk.Checkbutton(
                frame,
                text=label,
                variable=var,
                font=("Segoe UI", 11),
                bg="#F9FAFB",
                state="normal" if available else "disabled",
                fg="black" if available else "gray",
                anchor="w",
            )
            cb.pack(fill="x", pady=2)

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=(16, 12))

        def on_generate():
            result["cancelled"] = False
            result.update({k: v.get() for k, v in vars_.items()})
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        tk.Button(
            btn_frame, text="Cancel", width=10,
            font=("Segoe UI", 11), command=on_cancel,
        ).pack(side="left", padx=8)

        tk.Button(
            btn_frame, text="Generate PDF", width=14,
            font=("Segoe UI", 11, "bold"),
            bg="#1F6AA5", fg="white",
            command=on_generate,
        ).pack(side="left", padx=8)

        dialog.grab_set()
        self.wait_window(dialog)

        if result.get("cancelled", True):
            return None
        return result

    def _browse_output_dir(self) -> None:
        """Open directory dialog to choose report output location.

        Args:
            None

        Returns:
            None
        """
        from tkinter import filedialog
        path = filedialog.askdirectory(
            title="Select output directory",
            initialdir=self.output_dir_var.get(),
        )
        if path:
            self.output_dir_var.set(path)

    def _show_preview_placeholder(self) -> None:
        """Show placeholder text in the preview box.

        Args:
            None

        Returns:
            None
        """
        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        self.preview_box.insert(
            "1.0",
            "Click 'Generate Report' to create the report.\n\n"
            "The report will be saved as:\n"
            f"  <output_dir>/bioseq_report.md\n\n"
            "All plots will be saved as PNG files in:\n"
            f"  <output_dir>/report_plots/",
        )
        self.preview_box.configure(state="disabled")

    def _generate(self) -> None:
        """Generate the report and display a preview.

        Args:
            None

        Returns:
            None
        """
        output_dir = Path(self.output_dir_var.get())

        # Collect stat results from Statistics tab if requested
        stat_results = []
        if self.include_stats_var.get():
            stat_results = self._stat_results

        # Get correlation figure from Statistics tab if available
        corr_fig = self._corr_fig

        self.status_label.configure(
            text="Generating report...", text_color="gray"
        )
        self.update()

        try:
            report_path = self._report_module.generate_report(
                qc_df=self.qc_df,
                summary_df=self.summary_df,
                gene_df=self.gene_df,
                plots_module=self._plots,
                output_dir=output_dir,
                dataset_path=self.dataset_path,
                huba_report_loaded=self.huba_report_loaded,
                stat_results=stat_results,
                corr_fig=corr_fig,
            )
        except Exception as e:
            self.status_label.configure(
                text=f"Error: {e}", text_color="red"
            )
            messagebox.showerror("Report Error", f"Could not generate report:\n{e}")
            return

        self.status_label.configure(
            text=f"✓ Saved to: {report_path}",
            text_color="green",
        )

        # Show preview of generated report
        try:
            content = report_path.read_text(encoding="utf-8")
            self.preview_box.configure(state="normal")
            self.preview_box.delete("1.0", "end")
            self.preview_box.insert("1.0", content)
            self.preview_box.configure(state="disabled")
        except Exception:
            pass

        messagebox.showinfo(
            "Report generated",
            f"Report saved successfully:\n{report_path}\n\n"
            f"Plots saved to:\n{output_dir / 'report_plots'}",
        )


# ---------------------------------------------------------------------------
# Main application window
# ---------------------------------------------------------------------------

class BioSeqExplorerApp(ctk.CTk):
    """Main BioSeq Explorer application window."""

    def __init__(self) -> None:
        super().__init__()

        # --- Window setup ---
        self.title(config.APP_TITLE)
        self.geometry(
            f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}"
        )
        self.minsize(config.MIN_WINDOW_WIDTH, config.MIN_WINDOW_HEIGHT)

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - config.WINDOW_WIDTH) // 2
        y = (self.winfo_screenheight() - config.WINDOW_HEIGHT) // 2
        self.geometry(
            f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}+{x}+{y}"
        )

        # Apply Treeview styling before building UI
        apply_treeview_style()

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the main window layout with tab navigation.

        Args:
            None

        Returns:
            None
        """
        # --- Header bar ---
        header = ctk.CTkFrame(self, height=48, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="BioSeq Explorer",
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w",
        ).pack(side="left", padx=20, pady=8)

        ctk.CTkLabel(
            header,
            text="Bioinformatics analysis platform",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
        ).pack(side="left", padx=(0, 20), pady=8)

        # --- Tab view ---
        self.tabs = ctk.CTkTabview(
            self,
            anchor="nw",
        )
        self.tabs.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        # Create all tabs
        tab_names = [
            "🏠  Home",
            "🔬  Quality Control",
            "🔍  Motif Analysis",
            "🧬  ORF Analysis",
            "📊  Statistics",
            "📄  Report",
        ]
        for name in tab_names:
            self.tabs.add(name)

        # Instantiate tab content frames
        self.home_tab = HomeTab(self.tabs.tab("🏠  Home"))
        self.home_tab.pack(fill="both", expand=True)

        self.qc_tab = QualityControlTab(self.tabs.tab("🔬  Quality Control"))
        self.qc_tab.pack(fill="both", expand=True)

        self.motif_tab = MotifAnalysisTab(self.tabs.tab("🔍  Motif Analysis"))
        self.motif_tab.pack(fill="both", expand=True)

        self.orf_tab = ORFAnalysisTab(self.tabs.tab("🧬  ORF Analysis"))
        self.orf_tab.pack(fill="both", expand=True)

        self.stats_tab = StatisticsTab(self.tabs.tab("📊  Statistics"))
        self.stats_tab.pack(fill="both", expand=True)

        self.report_tab = ReportTab(self.tabs.tab("📄  Report"))
        self.report_tab.pack(fill="both", expand=True)

        # Set default tab
        self.tabs.set("🏠  Home")

    def on_dataset_loaded(self, df) -> None:
        """Propagate the loaded DataFrame to all analysis tabs.

        Called by HomeTab after a dataset is successfully loaded.
        Resets all tabs first to clear any previous dataset state.

        Args:
            df: pandas DataFrame with sequence data.

        Returns:
            None
        """
        # Reset all tabs to clear previous dataset
        for tab in [
            self.qc_tab, self.motif_tab, self.orf_tab,
            self.stats_tab, self.report_tab,
        ]:
            tab.reset()

        # Load new data into each tab
        self.qc_tab.load_data(df)
        self.motif_tab.load_data(df)
        self.orf_tab.load_data(df)
        self.stats_tab.load_data(df)
        self.report_tab.load_data(df)

        # Share correlation figure and stat results with ReportTab
        self.report_tab._corr_fig = getattr(self.stats_tab, "_corr_fig", None)
        self.report_tab._stat_results = getattr(self.stats_tab, "_last_results", [])




# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = BioSeqExplorerApp()
    app.mainloop()