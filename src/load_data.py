from __future__ import annotations
from pathlib import Path


def read_fasta(path: Path) -> list[dict]:
    """Wczytuje plik FASTA. Zwraca listę słowników: id, description, sequence."""
    records = []
    current_id, current_desc, current_seq = None, "", []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if current_id is not None:
                    records.append({
                        "id": current_id,
                        "description": current_desc,
                        "sequence": "".join(current_seq),
                    })
                parts = line[1:].split(" ", 1)
                current_id = parts[0]
                current_desc = parts[1] if len(parts) > 1 else ""
                current_seq = []
            else:
                current_seq.append(line.upper())

    if current_id is not None:
        records.append({
            "id": current_id,
            "description": current_desc,
            "sequence": "".join(current_seq),
        })
    return records


def load_all_fastas(source_dir: Path) -> tuple[list[dict], list[dict]]:
    """Wczytuje wszystkie pliki *.fasta z katalogu. Zwraca (wszystkie rekordy, profil plików)."""
    all_records = []
    file_profile = []

    for path in sorted(source_dir.glob("*.fasta")):
        records = read_fasta(path)
        for r in records:
            r["_source"] = path.name
        all_records.extend(records)
        file_profile.append({
            "file": path.name,
            "n_sequences": len(records),
        })
        print(f"    {path.name}: {len(records)} sekwencji")

    return all_records, file_profile
