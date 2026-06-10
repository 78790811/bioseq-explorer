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
        """Open a new terminal window and run the HUBA pipeline."""
        self.withdraw()

        # Run HUBA in a new terminal window
        huba_window = HubaRunnerWindow(self)
        huba_window.grab_set()
        self.wait_window(huba_window)

        # Refresh launcher after HUBA finishes
        self.deiconify()
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
        self.geometry("420x560")
        self.resizable(False, False)

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 420) // 2
        y = (self.winfo_screenheight() - 560) // 2
        self.geometry(f"420x560+{x}+{y}")

        # Checkboxes state for variants
        self.var_a = ctk.BooleanVar(value=True)
        self.var_b = ctk.BooleanVar(value=True)
        self.var_c = ctk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the HUBA runner UI."""

        ctk.CTkLabel(
            self,
            text="Run HUBA Pipeline",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(24, 4))

        ctk.CTkLabel(
            self,
            text="Select variants and run mode:",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(pady=(0, 16))

        # --- Variant checkboxes ---
        variants_frame = ctk.CTkFrame(self)
        variants_frame.pack(fill="x", padx=24, pady=(0, 16))

        ctk.CTkLabel(
            variants_frame,
            text="Filter variants:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(12, 4))

        variants = [
            (self.var_a, "Variant A", "Lenient  (min_len=10, max_n=50%)"),
            (self.var_b, "Variant B", "Standard (min_len=20, max_n=20%)"),
            (self.var_c, "Variant C", "Strict   (min_len=50, max_n=5%)"),
        ]

        for var, label, description in variants:
            row = ctk.CTkFrame(variants_frame, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=2)

            ctk.CTkCheckBox(
                row,
                text=label,
                variable=var,
                font=ctk.CTkFont(size=13),
                width=120,
            ).pack(side="left")

            ctk.CTkLabel(
                row,
                text=description,
                font=ctk.CTkFont(size=11),
                text_color="gray",
            ).pack(side="left", padx=(8, 0))

        # --- File selection ---
        ctk.CTkLabel(
            self,
            text="File selection:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=24, pady=(0, 4))

        self.select_files_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self,
            text="Select files interactively (--select)",
            variable=self.select_files_var,
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", padx=24, pady=(0, 16))

        # --- Run buttons ---
        ctk.CTkButton(
            self,
            text="▶  Run Pipeline",
            width=280,
            height=44,
            font=ctk.CTkFont(size=14),
            command=self._run_selected,
        ).pack(pady=(0, 8))

        ctk.CTkButton(
            self,
            text="⚡  Dry Run (load only)",
            width=280,
            height=36,
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            border_width=1,
            text_color=("gray30", "gray70"),
            hover_color=("gray85", "gray25"),
            command=lambda: self._run("--dry-run"),
        ).pack(pady=(0, 8))

        # --- Status label ---
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=360,
            justify="center",
        )
        self.status_label.pack(pady=(4, 0))

        # --- Close button ---
        ctk.CTkButton(
            self,
            text="Close",
            width=280,
            height=36,
            fg_color="transparent",
            border_width=1,
            text_color=("gray30", "gray70"),
            hover_color=("gray85", "gray25"),
            command=self.destroy,
        ).pack(pady=(8, 16))

    def _run_selected(self) -> None:
        """Build the command based on selected variants and run."""

        # Collect selected variants
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

        # Build command
        if set(selected) == {"A", "B", "C"}:
            # All three selected — use --all
            flag = "--all"
        elif len(selected) == 1:
            # Single variant
            flag = f"--variant {selected[0]}"
        else:
            # Multiple but not all — run each separately
            # We run --variant for each selected variant
            flag = " ".join(f"--variant {v}" for v in selected)

        # Add --select flag if checked
        if self.select_files_var.get():
            flag = "--select " + flag.split()[0] if len(selected) == 1 \
                else "--select --all"

        self._run(flag)

    def _run(self, flag: str) -> None:
        """Run HUBA with the given flag in a new terminal window."""
        self.status_label.configure(
            text=f"Running HUBA {flag}...\nCheck the terminal window.",
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
                text="HUBA started in a new terminal window.\n"
                     "Close that window when done, then close this.",
                text_color="green",
            )
        except Exception as e:
            self.status_label.configure(
                text=f"Error: {e}",
                text_color="red",
            )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = LauncherWindow()
    app.mainloop()