from __future__ import annotations
import csv
from pathlib import Path


def gc_content(seq: str) -> float:
    if not seq:
        return 0.0
    return (seq.count("G") + seq.count("C")) / len(seq)


def n_content(seq: str) -> float:
    if not seq:
        return 0.0
    return seq.count("N") / len(seq)


def compute_input_stats(records: list[dict]) -> list[dict]:
    rows = []
    for r in records:
        seq = r["sequence"]
        row = {
            "id": r["id"],
            "source": r.get("_source", ""),
            "length": len(seq),
            "gc_pct": round(gc_content(seq) * 100, 1),
            "n_pct": round(n_content(seq) * 100, 1),
        }
        rows.append(row)
    return rows


def save_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
