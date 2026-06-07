"""
Projekt A — Analiza sekwencji biologicznych (FASTA)
Uruchomienie:  py main.py --variant A
               py main.py --variant B
               py main.py --all
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

if not Path("config.py").exists():
    print("BŁĄD: Uruchom skrypt z katalogu projekt_A_bio/")
    print("  W PyCharm: File → Open → wybierz folder projekt_A_bio (nie warsztaty-projekty)")
    sys.exit(1)

import matplotlib
matplotlib.use("Agg")  # zapis do pliku, bez okna GUI
import matplotlib.pyplot as plt

import config
from src.load_data import load_all_fastas
from src.stats import compute_input_stats, save_csv
from src.pipeline import filter_sequences, save_param_compare


def run_variant(variant: str, records: list[dict], results_dir: Path) -> dict:
    params = config.VARIANTS[variant]
    print(f"\n  [Wariant {variant}] min_len={params['min_len']}, max_n_pct={params['max_n_pct']}")

    accepted, rejected = filter_sequences(records, **params)

    # Statystyki po filtrze
    after_stats = compute_input_stats(accepted)
    save_csv(after_stats, results_dir / "tables" / f"after_filter_{variant}.csv")

    # Raport odrzuconych
    reject_rows = [{"id": r["id"], "reason": r["reason"]} for r in rejected]
    save_csv(reject_rows, results_dir / "tables" / f"rejected_{variant}.csv")

    print(f"    accepted: {len(accepted)}/{len(records)}, rejected: {len(rejected)}")
    return {
        "params": params,
        "total": len(records),
        "accepted": len(accepted),
        "rejected": len(rejected),
    }


def make_plots(records: list[dict], results_by_variant: dict, results_dir: Path) -> None:
    plots_dir = results_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    # Wykres 1: rozkład długości sekwencji (wejście)
    lengths = [len(r["sequence"]) for r in records]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(range(len(lengths)), sorted(lengths), color="steelblue")
    ax.set_title("Długości sekwencji — dane wejściowe")
    ax.set_xlabel("Sekwencja (posortowane)")
    ax.set_ylabel("Długość (bp)")
    for i, v in enumerate(sorted(lengths)):
        ax.text(i, v + 0.3, str(v), ha="center", fontsize=9)
    plt.tight_layout()
    fig.savefig(plots_dir / "input_lengths.png", dpi=100)
    plt.close(fig)
    print("  Wykres: results/plots/input_lengths.png")

    # Wykres 2: porównanie wariantów (ile sekwencji przeszło filtr)
    variants = list(results_by_variant.keys())
    accepted = [results_by_variant[v]["accepted"] for v in variants]
    rejected = [results_by_variant[v]["rejected"] for v in variants]

    fig, ax = plt.subplots(figsize=(6, 4))
    x = range(len(variants))
    ax.bar(x, accepted, label="Przyjęte", color="steelblue")
    ax.bar(x, rejected, bottom=accepted, label="Odrzucone", color="tomato")
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"Wariant {v}" for v in variants])
    ax.set_ylabel("Liczba sekwencji")
    ax.set_title("Porównanie wariantów filtra")
    ax.legend()
    plt.tight_layout()
    fig.savefig(plots_dir / "param_compare.png", dpi=100)
    plt.close(fig)
    print("  Wykres: results/plots/param_compare.png")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline analizy sekwencji FASTA")
    parser.add_argument("--variant", choices=list(config.VARIANTS.keys()), help="Uruchom jeden wariant")  # dodaj nowy wariant w config.py
    parser.add_argument("--all", action="store_true", help="Uruchom oba warianty")
    parser.add_argument("--dry-run", action="store_true", help="Wczytaj dane i pokaż statystyki — bez filtrowania i zapisu")
    args = parser.parse_args()

    if not args.variant and not args.all and not args.dry_run:
        parser.print_help()
        sys.exit(1)

    results_dir = config.RESULTS_DIR
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "tables").mkdir(exist_ok=True)
    (results_dir / "plots").mkdir(exist_ok=True)

    # --- Krok 1: Wczytaj dane ---
    print(f"\nWczytywanie plików z: {config.SOURCE_DIR}")
    records, file_profile = load_all_fastas(config.SOURCE_DIR)
    print(f"  Łącznie sekwencji: {len(records)}")

    save_csv(file_profile, results_dir / "tables" / "file_profile.csv")
    print("  Zapisano: results/tables/file_profile.csv")

    if args.dry_run:
        print("\n[--dry-run] Zatrzymano przed filtrowaniem. Dane wczytane poprawnie.")
        print(f"  Pliki: {len(file_profile)}, sekwencji łącznie: {len(records)}")
        return

    # --- Krok 2: Statystyki wejścia ---
    input_stats = compute_input_stats(records)
    save_csv(input_stats, results_dir / "tables" / "input_stats.csv")
    print("  Zapisano: results/tables/input_stats.csv")
    for row in input_stats:
        print(f"    {row['id']:20s}  len={row['length']:4d}  GC={row['gc_pct']:5.1f}%  N={row['n_pct']:5.1f}%")

    # --- Krok 3: Uruchom wariant(y) ---
    to_run = ["A", "B"] if args.all else [args.variant]
    results_by_variant = {}
    for v in to_run:
        results_by_variant[v] = run_variant(v, records, results_dir)

    # --- Krok 4: Porównanie wariantów ---
    if len(results_by_variant) > 1:
        save_param_compare(results_by_variant, results_dir / "tables" / "param_compare.csv")
        print("\n  Zapisano: results/tables/param_compare.csv")

    # --- Krok 5: Wykresy ---
    make_plots(records, results_by_variant, results_dir)

    # --- Raport końcowy ---
    report = results_dir / "REPORT.md"
    lines = ["# REPORT — Projekt A: Sekwencje biologiczne", ""]
    lines += [f"Katalog wejściowy: {config.SOURCE_DIR}",
              f"Pliki FASTA: {len(file_profile)}", f"Sekwencji łącznie: {len(records)}", ""]
    for v, d in results_by_variant.items():
        lines.append(f"## Wariant {v}  (min_len={d['params']['min_len']}, max_n_pct={d['params']['max_n_pct']})")
        lines.append(f"- Przyjęte: {d['accepted']}/{d['total']}")
        lines.append(f"- Odrzucone: {d['rejected']}/{d['total']}")
        lines.append("")
    lines += ["## Artefakty", "- results/tables/file_profile.csv",
              "- results/tables/input_stats.csv",
              "- results/tables/after_filter_*.csv", "- results/tables/param_compare.csv",
              "- results/plots/input_lengths.png", "- results/plots/param_compare.png"]
    report.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  Zapisano: results/REPORT.md")
    print("\nGotowe. Sprawdź katalog results/")


if __name__ == "__main__":
    main()
