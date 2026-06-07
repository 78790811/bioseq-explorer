from pathlib import Path

SOURCE_DIR = Path("source")
RESULTS_DIR = Path("results")

# --- Parametr: minimalna długość sekwencji ---
# Wariant A — łagodny filtr (zostają prawie wszystkie sekwencje)
# Wariant B — ostry filtr (odrzuca krótkie i niepełne)
VARIANTS = {
    "A": {"min_len": 10, "max_n_pct": 0.5},
    "B": {"min_len": 20, "max_n_pct": 0.2},
}
