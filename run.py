# run.py
# Launcher for BioSeq Explorer.
# Displays a startup window with options to run HUBA pipeline
# or open BioSeq Explorer GUI directly.
#
# Usage:
#   python run.py

from __future__ import annotations
import subprocess
import sys
from pathlib import Path
from datetime import datetime

import customtkinter as ctk


# ---------------------------------------------------------------------------
# Appearance settings
# ---------------------------------------------------------------------------

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_latest_dataset() -> tuple[str, str] | None:
    """Find the most recently modified clean_dataset_*.csv file.

    Returns:
        tuple (filename, modified_time_str) or None if no dataset found
    """
    tables_dir = Path("results") / "tables"
    if not tables_dir.exists():
        return None

    datasets = list(tables_dir.glob("clean_dataset_*.csv"))
    if not datasets:
        return None

    # Find the most recently modified file
    latest = max(datasets, key=lambda p: p.stat().st_mtime)
    modified = datetime.fromtimestamp(latest.stat().st_mtime)
    modified_str = modified.strftime("%Y-%m-%d %H:%M")

    return latest.name, modified_str


# ---------------------------------------------------------------------------
# Launcher window
# ---------------------------------------------------------------------------

class LauncherWindow(ctk.CTk):
    """Main launcher window for BioSeq Explorer."""

    def __init__(self) -> None:
        super().__init__()

        # --- Window setup ---
        self.title("BioSeq Explorer — Launcher")
        self.geometry("420x380")
        self.resizable(False, False)

        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 420) // 2
        y = (self.winfo_screenheight() - 380) // 2
        self.geometry(f"420x380+{x}+{y}")

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the launcher UI."""

        # --- Title ---
        ctk.CTkLabel(
            self,
            text="BioSeq Explorer",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(pady=(30, 4))

        ctk.CTkLabel(
            self,
            text="Bioinformatics platform for disease-associated gene analysis",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=360,
            justify="center",
        ).pack(pady=(0, 24))

        # --- Dataset info ---
        dataset_info = get_latest_dataset()

        if dataset_info:
            name, modified = dataset_info
            info_text = f"Last dataset: {name}\nGenerated: {modified}"
            info_color = "green"
        else:
            info_text = "No dataset found.\nRun HUBA pipeline first."
            info_color = "orange"

        ctk.CTkLabel(
            self,
            text=info_text,
            font=ctk.CTkFont(size=12),
            text_color=info_color,
            justify="center",
        ).pack(pady=(0, 24))

        # --- Buttons ---
        ctk.CTkButton(
            self,
            text="▶  Run HUBA Pipeline",
            width=280,
            height=44,
            font=ctk.CTkFont(size=14),
            command=self._run_huba,
        ).pack(pady=8)

        ctk.CTkButton(
            self,
            text="📊  Open BioSeq Explorer",
            width=280,
            height=44,
            font=ctk.CTkFont(size=14),
            fg_color="green" if dataset_info else "gray",
            hover_color="darkgreen" if dataset_info else "gray",
            command=self._open_explorer,
            state="normal" if dataset_info else "disabled",
        ).pack(pady=8)

        ctk.CTkButton(
            self,
            text="Exit",
            width=280,
            height=36,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            text_color=("gray30", "gray70"),
            hover_color=("gray85", "gray25"),
            command=self.destroy,
        ).pack(pady=(8, 0))

    def _run_huba(self) -> None:
        """Open a terminal window with HUBA help message and command prompt."""
        help_message = (
            "echo."
            " & echo ============================================================"
            " & echo   BioSeq Explorer -- HUBA Pipeline"
            " & echo ============================================================"
            " & echo."
            " & echo Available commands (run from this directory):"
            " & echo."
            " & echo   python main.py --dry-run               Preview files, no filtering"
            " & echo   python main.py --variant A             Lenient  (min_len=10, max_n=50%%)"
            " & echo   python main.py --variant B             Standard (min_len=20, max_n=20%%)"
            " & echo   python main.py --variant C             Strict   (min_len=50, max_n=5%%)"
            " & echo   python main.py --all                   Run all variants A, B, C"
            " & echo   python main.py --select                Choose files interactively"
            " & echo   python main.py --select --variant C    Select files + strict filter"
            " & echo   python main.py --delete                Delete files from source"
            " & echo."
            " & echo   python fetch_ncbi.py                   Download sequences from NCBI"
            " & echo   python generate_test_data.py           Generate test CSV/TSV files"
            " & echo."
            " & echo Type a command above and press Enter."
            " & echo ============================================================"
            " & echo."
        )

        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "cmd", "/k", help_message],
                cwd=Path.cwd(),
                shell=True,
            )
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", "Could not open terminal:\n" + str(e))

        self._refresh()

    def _open_explorer(self) -> None:
        """Launch BioSeq Explorer GUI."""
        self.withdraw()
        subprocess.Popen(
            [sys.executable, "app/main.py"],
            cwd=Path.cwd(),
        )
        self.destroy()

    def _refresh(self) -> None:
        """Refresh the launcher UI to reflect new dataset status."""
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()


# ---------------------------------------------------------------------------
# HUBA runner window
# ---------------------------------------------------------------------------

class HubaRunnerWindow(ctk.CTkToplevel):
    """Window for running HUBA pipeline with mode selection."""

    def __init__(self, parent: ctk.CTk) -> None:
        super().__init__(parent)

        self.title("Run HUBA Pipeline")
        self.geometry("460x670")
        self.resizable(False, False)

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 460) // 2
        y = (self.winfo_screenheight() - 640) // 2
        self.geometry(f"460x670+{x}+{y}")

        # Variant checkboxes state
        self.var_a = ctk.BooleanVar(value=True)
        self.var_b = ctk.BooleanVar(value=True)
        self.var_c = ctk.BooleanVar(value=False)

        # File selection mode (radio buttons)
        self.file_mode = ctk.StringVar(value="all")

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the HUBA runner UI."""

        ctk.CTkLabel(
            self,
            text="Run HUBA Pipeline",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(20, 4))

        ctk.CTkLabel(
            self,
            text="Configure and run the data preparation pipeline:",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(pady=(0, 12))

        # --- Main frame containing both sections ---
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="x", padx=20, pady=(0, 12))

        # --- Section 1: Filter variants ---
        ctk.CTkLabel(
            main_frame,
            text="1.  Select filter variants:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(12, 4))

        variants_frame = ctk.CTkFrame(main_frame)
        variants_frame.pack(fill="x", padx=16, pady=(0, 12))

        variants = [
            (self.var_a, "Variant A",
             "Lenient — min_len=10, max_n=50%"),
            (self.var_b, "Variant B",
             "Standard — min_len=20, max_n=20%"),
            (self.var_c, "Variant C",
             "Strict — min_len=50, max_n=5%"),
        ]

        for var, label, description in variants:
            row = ctk.CTkFrame(variants_frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=3)
            ctk.CTkCheckBox(
                row,
                text=label,
                variable=var,
                font=ctk.CTkFont(size=13),
                width=110,
            ).pack(side="left")
            ctk.CTkLabel(
                row,
                text=description,
                font=ctk.CTkFont(size=11),
                text_color="gray",
            ).pack(side="left", padx=(8, 0), pady=4)

        # --- Section 2: File selection (radio-style) ---
        ctk.CTkLabel(
            main_frame,
            text="2.  Select input files:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(4, 4))

        files_frame = ctk.CTkFrame(main_frame)
        files_frame.pack(fill="x", padx=16, pady=(0, 12))

        # Use radio buttons for mutually exclusive file selection
        self.file_mode = ctk.StringVar(value="all")

        file_options = [
            ("all", "All files",
             "Process all files in source/ directory"),
            ("select", "Select interactively",
             "Choose which files to process (--select)"),
        ]

        for value, label, description in file_options:
            row = ctk.CTkFrame(files_frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=3)
            ctk.CTkRadioButton(
                row,
                text=label,
                variable=self.file_mode,
                value=value,
                font=ctk.CTkFont(size=13),
                width=160,
            ).pack(side="left")
            ctk.CTkLabel(
                row,
                text=description,
                font=ctk.CTkFont(size=11),
                text_color="gray",
            ).pack(side="left", padx=(8, 0), pady=4)

        # --- Status label ---
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=400,
            justify="center",
        )
        self.status_label.pack(pady=(0, 8))

        # --- Action buttons ---
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20)

        # Run Pipeline button
        run_btn_frame = ctk.CTkFrame(btn_frame, fg_color="transparent")
        run_btn_frame.pack(fill="x", pady=(0, 6))

        ctk.CTkButton(
            run_btn_frame,
            text="▶  Run Pipeline",
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._run_selected,
        ).pack(fill="x")

        ctk.CTkLabel(
            run_btn_frame,
            text="Process files with selected variants and options",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack()

        # Load Raw Files button
        dry_btn_frame = ctk.CTkFrame(btn_frame, fg_color="transparent")
        dry_btn_frame.pack(fill="x", pady=(0, 6))

        ctk.CTkButton(
            dry_btn_frame,
            text="⚡  Load Raw Files",
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda: self._run("--dry-run"),
        ).pack(fill="x")

        ctk.CTkLabel(
            dry_btn_frame,
            text="Load and preview files only — no filtering or saving",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack()

        # --- Collapsible "Available commands" panel ---
        self._commands_visible = False
        self._commands_frame = None

        self._toggle_btn = ctk.CTkButton(
            btn_frame,
            text="ℹ️  Available terminal commands  ▸",
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            text_color=("gray30", "gray70"),
            hover_color=("gray85", "gray25"),
            command=self._toggle_commands,
        )
        self._toggle_btn.pack(fill="x", pady=(4, 4))

        # Close button
        ctk.CTkButton(
            btn_frame,
            text="Close",
            height=36,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            text_color=("gray30", "gray70"),
            hover_color=("gray85", "gray25"),
            command=self.destroy,
        ).pack(fill="x", pady=(0, 8))

    def _toggle_commands(self) -> None:
        """Show or hide the available terminal commands panel.

        Args:
            None

        Returns:
            None
        """
        self._commands_visible = not self._commands_visible

        if self._commands_visible:
            self._toggle_btn.configure(
                text="ℹ️  Available terminal commands  ▾"
            )
            self._commands_frame = ctk.CTkFrame(self, fg_color="#F0F4F8")
            self._commands_frame.pack(fill="x", padx=20, pady=(0, 8))

            commands = [
                ("--dry-run",
                 "Preview files only — no filtering or saving"),
                ("--variant A / B / C",
                 "Run a single filter variant"),
                ("--all",
                 "Run all variants (A, B, C) and compare"),
                ("--select",
                 "Choose which files to process interactively"),
                ("--select --variant C",
                 "Select files + apply strict filtering"),
                ("--delete",
                 "Interactively delete files from source/"),
            ]

            ctk.CTkLabel(
                self._commands_frame,
                text="Run from project root:  python main.py <command>",
                font=ctk.CTkFont(size=10, slant="italic"),
                text_color="gray",
                anchor="w",
            ).pack(anchor="w", padx=10, pady=(6, 2))

            for cmd, desc in commands:
                row = ctk.CTkFrame(
                    self._commands_frame, fg_color="transparent"
                )
                row.pack(fill="x", padx=10, pady=1)

                ctk.CTkLabel(
                    row,
                    text=cmd,
                    font=ctk.CTkFont(family="Courier New", size=11,
                                     weight="bold"),
                    text_color=("#1F6AA5", "#4DA6FF"),
                    width=200,
                    anchor="w",
                ).pack(side="left")

                ctk.CTkLabel(
                    row,
                    text=desc,
                    font=ctk.CTkFont(size=11),
                    text_color="gray",
                    anchor="w",
                ).pack(side="left", padx=(8, 0))

            # Extra tools
            ctk.CTkLabel(
                self._commands_frame,
                text="Other useful scripts:",
                font=ctk.CTkFont(size=10, slant="italic"),
                text_color="gray",
                anchor="w",
            ).pack(anchor="w", padx=10, pady=(6, 2))

            extra = [
                ("python fetch_ncbi.py",
                 "Download sequences from NCBI"),
                ("python generate_test_data.py",
                 "Generate CSV/TSV test files"),
            ]
            for cmd, desc in extra:
                row = ctk.CTkFrame(
                    self._commands_frame, fg_color="transparent"
                )
                row.pack(fill="x", padx=10, pady=1)
                ctk.CTkLabel(
                    row,
                    text=cmd,
                    font=ctk.CTkFont(family="Courier New", size=11,
                                     weight="bold"),
                    text_color=("#1F6AA5", "#4DA6FF"),
                    width=200,
                    anchor="w",
                ).pack(side="left")
                ctk.CTkLabel(
                    row,
                    text=desc,
                    font=ctk.CTkFont(size=11),
                    text_color="gray",
                    anchor="w",
                ).pack(side="left", padx=(8, 0))

            ctk.CTkLabel(
                self._commands_frame,
                text="",
                height=4,
            ).pack()

            # Resize window to fit content
            self.geometry("460x820")

        else:
            self._toggle_btn.configure(
                text="ℹ️  Available terminal commands  ▸"
            )
            if self._commands_frame:
                self._commands_frame.destroy()
                self._commands_frame = None
            self.geometry("460x670")

    def _on_file_selection_changed(self) -> None:
        """Ensure at least one file selection option is always checked."""
        if not self.all_files_var.get() and not self.select_files_var.get():
            self.all_files_var.set(True)

    def _run_selected(self) -> None:
        """Build the command based on selected variants and run."""

        # Validate variant selection
        selected = []
        if self.var_a.get():
            selected.append("A")
        if self.var_b.get():
            selected.append("B")
        if self.var_c.get():
            selected.append("C")

        if not selected:
            self.status_label.configure(
                text="Please select at least one variant.",
                text_color="orange",
            )
            return

        # Build variant flag
        if set(selected) == {"A", "B", "C"}:
            variant_flag = "--all"
        elif len(selected) == 1:
            variant_flag = f"--variant {selected[0]}"
        else:
            variant_flag = "--all"

        # Build file flag
        if self.file_mode.get() == "select":
            flag = f"--select {variant_flag}" \
                if variant_flag != "--all" else "--select"
        else:
            flag = variant_flag

        self._run(flag)

    def _run(self, flag: str) -> None:
        """Run HUBA with the given flag in a new terminal window."""
        self.status_label.configure(
            text=f"Running: python main.py {flag}\n"
                 f"Check the new terminal window.",
            text_color="blue",
        )
        self.update()

        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "cmd", "/k",
                 f"{sys.executable} main.py {flag}"],
                cwd=Path.cwd(),
                shell=True,
            )
            self.status_label.configure(
                text="✓ HUBA started in a new terminal window.\n"
                     "When finished, close that window and return here.",
                text_color="green",
            )
        except Exception as e:
            self.status_label.configure(
                text=f"Error starting HUBA: {e}",
                text_color="red",
            )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = LauncherWindow()
    app.mainloop()