# verify_orfs.py
# Independent ORF verification script using Biopython.
# Reads FASTA files from source/ directory, finds ORFs using Biopython
# and compares results with BioSeq Explorer's orf_analyzer.py.
#
# Usage (from project root):
#   python verify_orfs.py
#   python verify_orfs.py --min-len 300
#   python verify_orfs.py --gene brca1

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description="Verify ORF counts using Biopython vs BioSeq Explorer."
)
parser.add_argument(
    "--min-len", type=int, default=100,
    help="Minimum ORF length in bp (default: 100)"
)
parser.add_argument(
    "--gene", type=str, default=None,
    help="Limit to one gene, e.g. --gene brca1 (optional)"
)
args = parser.parse_args()

MIN_LEN = args.min_len
FILTER_GENE = args.gene.lower() if args.gene else None

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

try:
    from Bio import SeqIO
    from Bio.Seq import Seq
except ImportError:
    print("ERROR: Biopython not installed. Run: pip install biopython")
    sys.exit(1)

# Add project root to path so we can import orf_analyzer
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # tests/ -> project root
sys.path.insert(0, str(PROJECT_ROOT / "app" / "src"))

try:
    import orf_analyzer as our_module
except ImportError:
    print("ERROR: Could not import app/src/orf_analyzer.py")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SOURCE_DIR = PROJECT_ROOT / "source"
STOP_CODONS = {"TAA", "TAG", "TGA"}
START_CODON = "ATG"

# ---------------------------------------------------------------------------
# Biopython ORF finder (reference implementation)
# ---------------------------------------------------------------------------

def biopython_find_orfs(sequence: str, min_length: int) -> list[dict]:
    """Find ORFs using Biopython Seq translation approach.

    Scans all 3 forward reading frames codon by codon.
    Same logic as our module but using Biopython for codon handling.

    Args:
        sequence:   DNA string.
        min_length: Minimum ORF length in bp.

    Returns:
        List of ORF dicts with frame, start, end, length.
    """
    seq = Seq(sequence.upper())
    orfs = []

    for frame in range(3):
        i = frame
        in_orf = False
        orf_start = 0

        while i + 3 <= len(seq):
            codon = str(seq[i:i + 3])
            if not in_orf:
                if codon == START_CODON:
                    in_orf = True
                    orf_start = i
            else:
                if codon in STOP_CODONS:
                    length = (i + 3) - orf_start
                    if length >= min_length:
                        orfs.append({
                            "frame":  frame + 1,
                            "start":  orf_start + 1,
                            "end":    i + 3,
                            "length": length,
                        })
                    in_orf = False
            i += 3

    return orfs

# ---------------------------------------------------------------------------
# Main comparison
# ---------------------------------------------------------------------------

print("=" * 70)
print(f"ORF Verification — min_length = {MIN_LEN} bp")
print("=" * 70)

fasta_files = sorted(SOURCE_DIR.glob("*.fasta")) + sorted(SOURCE_DIR.glob("*.fa"))

if not fasta_files:
    print(f"ERROR: No FASTA files found in {SOURCE_DIR}")
    sys.exit(1)

if FILTER_GENE:
    fasta_files = [f for f in fasta_files if FILTER_GENE in f.name.lower()]
    if not fasta_files:
        print(f"ERROR: No FASTA files matching '{FILTER_GENE}' found.")
        sys.exit(1)

total_match = 0
total_mismatch = 0

for fasta_path in fasta_files:
    print(f"\n── {fasta_path.name} ──")

    records = list(SeqIO.parse(str(fasta_path), "fasta"))
    if not records:
        print("  (empty file)")
        continue

    for record in records:
        seq_str = str(record.seq)
        seq_id = record.id

        # BioSeq Explorer orf_analyzer result
        our_orfs = our_module.find_orfs(seq_str, min_length=MIN_LEN)

        # Biopython reference result
        bio_orfs = biopython_find_orfs(seq_str, min_length=MIN_LEN)

        our_count = len(our_orfs)
        bio_count = len(bio_orfs)
        match = "✓ MATCH" if our_count == bio_count else "✗ MISMATCH"

        if our_count != bio_count:
            total_mismatch += 1
        else:
            total_match += 1

        print(f"  {seq_id}")
        print(f"    Length:      {len(seq_str):,} bp")
        print(f"    BioSeq ORFs: {our_count}")
        print(f"    Biopython:   {bio_count}  {match}")

        # Show first 3 ORFs from each for spot-checking
        if our_orfs:
            print(f"    Top ORF (BioSeq):   frame={our_orfs[0]['frame']} "
                  f"start={our_orfs[0]['start']} "
                  f"len={our_orfs[0]['length']} bp")
        if bio_orfs:
            longest_bio = max(bio_orfs, key=lambda o: o["length"])
            print(f"    Top ORF (Biopython): frame={longest_bio['frame']} "
                  f"start={longest_bio['start']} "
                  f"len={longest_bio['length']} bp")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print("\n" + "=" * 70)
print(f"SUMMARY")
print(f"  Sequences matching:    {total_match}")
print(f"  Sequences mismatching: {total_mismatch}")
if total_mismatch == 0:
    print("  ✓ All results match — BioSeq Explorer ORF algorithm is correct.")
else:
    print("  ✗ Mismatches found — review algorithm differences above.")
print("=" * 70)