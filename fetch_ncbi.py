# fetch_ncbi.py
# Script for downloading gene sequences from NCBI using Biopython Entrez API.
# Saves sequences to the source/ directory for processing by HUBA.
#
# Usage:
#   python fetch_ncbi.py --list
#   python fetch_ncbi.py --genes BRCA1 TP53
#   python fetch_ncbi.py --genes EGFR --max 5
#   python fetch_ncbi.py --genes BRCA1 --force

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from Bio import Entrez, SeqIO


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

Entrez.email = "ewa.rydzek@gmail.com"

OUTPUT_DIR = Path("source")

DEFAULT_MAX_RECORDS = 3


# ---------------------------------------------------------------------------
# Download function
# ---------------------------------------------------------------------------

def fetch_gene_sequences(
    gene_symbol: str,
    output_dir: Path,
    max_records: int,
    force: bool = False,
) -> int:
    """Search NCBI nucleotide database and download sequences as FASTA.

    Checks if file already exists before downloading.
    Skips download if file exists and force=False.

    Args:
        gene_symbol: Gene symbol used for search and output filename.
        output_dir:  Directory where the FASTA file will be saved.
        max_records: Maximum number of sequences to download.
        force:       If True, re-download even if file already exists.

    Returns:
        Number of sequences downloaded, or 0 if skipped or failed.
    """
    output_path = output_dir / f"{gene_symbol.lower()}_sequences.fasta"
    query = f"{gene_symbol.upper()} Homo sapiens mRNA"

    # --- Check if file already exists ---
    if output_path.exists() and not force:
        size_kb = output_path.stat().st_size // 1024
        modified = datetime.fromtimestamp(
            output_path.stat().st_mtime
        ).strftime("%Y-%m-%d %H:%M")
        print(f"\n  {gene_symbol.upper()}: already downloaded — skipping.")
        print(f"    File:     {output_path}")
        print(f"    Size:     {size_kb} KB")
        print(f"    Downloaded: {modified}")
        print(f"    Use --force to re-download.")
        return 0

    if output_path.exists() and force:
        print(f"\n  {gene_symbol.upper()}: re-downloading (--force).")
    else:
        print(f"\n  {gene_symbol.upper()}: downloading...")

    print(f"    Query: {query}")

    # --- Search NCBI ---
    try:
        search_handle = Entrez.esearch(
            db="nucleotide",
            term=query,
            retmax=max_records,
            usehistory="y",
        )
        search_results = Entrez.read(search_handle)
        search_handle.close()
    except Exception as e:
        print(f"    ERROR: NCBI search failed: {e}")
        return 0

    id_list = search_results["IdList"]
    print(f"    Found: {len(id_list)} record(s) on NCBI")

    if not id_list:
        print(f"    WARNING: No sequences found for {gene_symbol.upper()}")
        return 0

    # --- Fetch sequences ---
    try:
        fetch_handle = Entrez.efetch(
            db="nucleotide",
            id=id_list,
            rettype="fasta",
            retmode="text",
        )
        records = list(SeqIO.parse(fetch_handle, "fasta"))
        fetch_handle.close()
    except Exception as e:
        print(f"    ERROR: Download failed: {e}")
        return 0

    if not records:
        print(f"    WARNING: No sequences parsed for {gene_symbol.upper()}")
        return 0

    # --- Save to file ---
    SeqIO.write(records, output_path, "fasta")
    print(f"    Saved: {output_path} ({len(records)} sequences)")
    return len(records)


# ---------------------------------------------------------------------------
# List downloaded files
# ---------------------------------------------------------------------------

def list_downloaded(output_dir: Path) -> None:
    """Display all FASTA files already downloaded to source/.

    Args:
        output_dir: Directory to scan for FASTA files.

    Returns:
        None
    """
    fasta_files = sorted(
        list(output_dir.glob("*.fasta")) + list(output_dir.glob("*.fa"))
    )

    print(f"\nSequence files in {output_dir}/:\n")

    if not fasta_files:
        print("  No FASTA files found.")
        print(f"  Use: python fetch_ncbi.py --genes BRCA1 TP53")
        return

    print(f"  {'File':<40} {'Size':>8}  {'Downloaded':<16}  Sequences")
    print(f"  {'-'*40} {'-'*8}  {'-'*16}  ---------")

    for path in fasta_files:
        size_kb = path.stat().st_size // 1024
        modified = datetime.fromtimestamp(
            path.stat().st_mtime
        ).strftime("%Y-%m-%d %H:%M")
        try:
            n_seqs = sum(1 for _ in SeqIO.parse(str(path), "fasta"))
        except Exception:
            n_seqs = "?"
        print(f"  {path.name:<40} {size_kb:>6} KB  {modified:<16}  {n_seqs}")

    print(f"\n  Total: {len(fasta_files)} file(s)")
    print(f"\n  To re-download a file: python fetch_ncbi.py --genes GENE --force")


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="python fetch_ncbi.py",
        description="Download gene sequences from NCBI for BioSeq Explorer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fetch_ncbi.py --list
      Show all FASTA files already downloaded to source/

  python fetch_ncbi.py --genes BRCA1 TP53 EGFR
      Download BRCA1, TP53 and EGFR (skips if already exists)

  python fetch_ncbi.py --genes BRCA1 --max 5
      Download up to 5 sequences for BRCA1

  python fetch_ncbi.py --genes BRCA1 --force
      Re-download BRCA1 even if file already exists
        """,
    )

    parser.add_argument(
        "--genes",
        nargs="+",
        metavar="GENE",
        help="Gene symbol(s) to download (e.g. BRCA1 TP53 EGFR).",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=DEFAULT_MAX_RECORDS,
        metavar="N",
        help=f"Maximum sequences per gene (default: {DEFAULT_MAX_RECORDS})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download files even if they already exist in source/",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all FASTA files already downloaded to source/, then exit.",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Main entry point — parse arguments and run appropriate action."""
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("BioSeq Explorer — NCBI sequence downloader")
    print("=" * 60)

    # --list: show downloaded files and exit
    if args.list:
        list_downloaded(OUTPUT_DIR)
        print()
        return

    # --genes required if not --list
    if not args.genes:
        print("\nERROR: please specify genes to download.")
        print("  python fetch_ncbi.py --genes BRCA1 TP53")
        print("  python fetch_ncbi.py --list")
        return

    genes = [g.upper() for g in args.genes]
    print(f"\nGenes to download: {', '.join(genes)}")
    print(f"Max sequences per gene: {args.max}")
    if args.force:
        print("Mode: force re-download (--force)")

    total_downloaded = 0
    skipped = 0

    for gene in genes:
        count = fetch_gene_sequences(
            gene_symbol=gene,
            output_dir=OUTPUT_DIR,
            max_records=args.max,
            force=args.force,
        )
        if count > 0:
            total_downloaded += count
        else:
            skipped += 1

    print("\n" + "=" * 60)
    print(f"Done.")
    print(f"  Downloaded:              {total_downloaded} sequence(s)")
    print(f"  Skipped (already exist): {skipped} gene(s)")
    print(f"  Files saved to:          {OUTPUT_DIR}/")
    if total_downloaded > 0:
        print(f"\nNext step: python main.py --all")
    print("=" * 60)


if __name__ == "__main__":
    main()