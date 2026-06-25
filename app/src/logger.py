# logger.py
# Centralized logging module for BioSeq Explorer.
# Writes timestamped log entries to a file and optionally updates
# a status bar widget in the GUI, so the user always sees the most
# recent action without digging through a terminal.

from __future__ import annotations

from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LOG_FILENAME = "bioseq.log"

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

# Reference to the status bar CTkLabel, set once at app startup via
# register_status_bar(). Kept as a module-level variable so any part
# of the app can call log_action() without passing the widget around.
_status_bar_label = None
_log_file_path: Path | None = None


def init_logger(project_root: Path) -> None:
    """Initialize the logger with the project root directory.

    Must be called once at application startup, before any log_action()
    calls, so the log file path is known.

    Args:
        project_root: Path to the project root directory.

    Returns:
        None
    """
    global _log_file_path
    _log_file_path = project_root / LOG_FILENAME


def register_status_bar(label_widget) -> None:
    """Register the GUI status bar widget to receive live updates.

    Args:
        label_widget: A CTkLabel (or similar) widget with a .configure()
                      method accepting a 'text' keyword argument.

    Returns:
        None
    """
    global _status_bar_label
    _status_bar_label = label_widget


def log_action(message: str, level: str = "info") -> None:
    """Log an action: write to the log file and update the status bar.

    Args:
        message: Human-readable description of the action or error.
        level:   Severity level — 'info', 'warning', or 'error'.
                 Affects status bar color and the log file tag.

    Returns:
        None
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    level_tag = level.upper().ljust(7)

    # --- Write to log file ---
    if _log_file_path is not None:
        try:
            with _log_file_path.open("a", encoding="utf-8") as f:
                f.write(f"{timestamp} | {level_tag} | {message}\n")
        except Exception:
            pass  # Never let logging itself crash the app

    # --- Update status bar ---
    if _status_bar_label is not None:
        colors = {
            "info":    "#2CA02C",
            "warning": "#E05A2B",
            "error":   "#DC2626",
        }
        icons = {
            "info":    "✓",
            "warning": "⚠",
            "error":   "✗",
        }
        color = colors.get(level, "#374151")
        icon = icons.get(level, "•")
        try:
            _status_bar_label.configure(
                text=f"{icon}  {message}",
                text_color=color,
            )
        except Exception:
            pass  # Widget may not exist yet during early startup