from __future__ import annotations
import csv
from pathlib import Path
from src.stats import gc_content, n_content


def filter_sequences(records: list[dict], min_len: int, max_n_pct: float) -> tuple[list[dict], list[dict]]:
    """
    Filtruje sekwencje według parametrów jakości.
    Zwraca: (accepted, rejected)
    """
    accepted, rejected = [], []

    for r in records:
        seq = r["sequence"]

        # TODO: Uzupełnij warunki odrzucenia sekwencji.
        # Sekwencja powinna być odrzucona gdy:
        #   1. jej długość jest MNIEJSZA niż min_len
        #   2. LUB jej zawartość N (n_content) jest WIĘKSZA niż max_n_pct
        #
        # Funkcja n_content(seq) zwraca ułamek (0.0–1.0), np. 0.25 = 25% N
        # Przykład sprawdzenia długości: len(seq) < min_len
        #
        # Jeśli warunek odrzucenia jest spełniony → dodaj do rejected z kluczem "reason"
        # W przeciwnym razie → dodaj do accepted

        reject = False
        reason = ""

        # --- UZUPEŁNIJ PONIŻEJ ---
        # Warunek 1: odrzuć jeśli sekwencja jest za krótka
        #   if len(seq) < min_len:
        #       reject = True
        #       reason = f"TOO_SHORT (len={len(seq)}, min={min_len})"
        #
        # Warunek 2: odrzuć jeśli za dużo N  (użyj elif, żeby każda seq miała jeden powód)
        #   elif n_content(seq) > max_n_pct:
        #       reject = True
        #       reason = f"HIGH_N (n_pct={n_content(seq):.0%}, max={max_n_pct:.0%})"
        # --- KONIEC UZUPEŁNIENIA ---

        if reject:
            rejected.append({**r, "reason": reason})
        else:
            accepted.append(r)

    return accepted, rejected


def save_param_compare(results_by_variant: dict, out_path: Path) -> None:
    """Zapisuje tabelę porównawczą wyników dla obu wariantów."""
    rows = []
    for variant, data in results_by_variant.items():
        rows.append({
            "variant": variant,
            "min_len": data["params"]["min_len"],
            "max_n_pct": data["params"]["max_n_pct"],
            "total_input": data["total"],
            "accepted": data["accepted"],
            "rejected": data["rejected"],
            "accepted_pct": round(data["accepted"] / data["total"] * 100, 1) if data["total"] else 0,
        })
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
