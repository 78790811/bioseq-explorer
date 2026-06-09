# fetch_ncbi.py
# Script for downloading gene sequences from NCBI using Biopython Entrez API.
# Downloads FASTA sequences for disease-associated genes (BRCA1, BRCA2, etc.)
# and saves them to the source/ directory for processing by HUBA.
#
# Usage:
#   python fetch_ncbi.py

from __future__ import annotations
from pathlib import Path
from Bio import Entrez, SeqIO


# ---------------------------------------------------------------------------
# Configuration — EDIT THIS SECTION
# ---------------------------------------------------------------------------

# Your email address — required by NCBI Entrez API
# Replace the placeholder with your actual email address
Entrez.email = "ewa.rydzek@gmail.com"

# Output directory — where downloaded FASTA files will be saved
OUTPUT_DIR = Path("source")

# Genes to download — NCBI gene symbols for Homo sapiens
# Each entry: (gene_symbol, ncbi_search_query)
GENES = [
    ("BRCA1", "BRCA1[Gene] AND Homo sapiens[Organism] AND mRNA[Filter]"),
    ("BRCA2", "BRCA2[Gene] AND Homo sapiens[Organism] AND mRNA[Filter]"),
    ("TP53",  "TP53[Gene]  AND Homo sapiens[Organism] AND mRNA[Filter]"),
    ("CHEK2", "CHEK2[Gene] AND Homo sapiens[Organism] AND mRNA[Filter]"),
    ("PALB2", "PALB2[Gene] AND Homo sapiens[Organism] AND mRNA[Filter]"),
]

# Maximum number of sequences to download per gene
MAX_RECORDS_PER_GENE = 3


# ---------------------------------------------------------------------------
# Download function
# ---------------------------------------------------------------------------

def fetch_gene_sequences(
    gene_symbol: str,
    query: str,
    output_dir: Path,
    max_records: int,
) -> int:
    """Search NCBI nucleotide database and download sequences as FASTA.

    Args:
        gene_symbol: short gene name used for the output filename
        query:       NCBI Entrez search query string
        output_dir:  directory where the FASTA file will be saved
        max_records: maximum number of sequences to download

    Returns:
        number of sequences successfully downloaded
    """
    print(f"\nSearching NCBI for: {gene_symbol}")
    print(f"  Query: {query}")

    # --- Step 1: Search for matching records ---
    search_handle = Entrez.esearch(
        db="nucleotide",
        term=query,
        retmax=max_records,
    )
    search_results = Entrez.read(search_handle)
    search_handle.close()

    id_list = search_results["IdList"]
    print(f"  Found: {len(id_list)} records")

    if not id_list:
        print(f"  WARNING: No sequences found for {gene_symbol}")
        return 0

    # --- Step 2: Fetch sequences in FASTA format ---
    fetch_handle = Entrez.efetch(
        db="nucleotide",
        id=id_list,
        rettype="fasta",
        retmode="text",
    )

    # --- Step 3: Parse and save to file ---
    output_path = output_dir / f"{gene_symbol.lower()}_sequences.fasta"
    records = list(SeqIO.parse(fetch_handle, "fasta"))
    fetch_handle.close()

    # Save sequences to FASTA file
    SeqIO.write(records, output_path, "fasta")
    print(f"  Saved: {output_path} ({len(records)} sequences)")

    return len(records)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Download sequences for all configured genes from NCBI."""

    # Create output directory if it does not exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("BioSeq Explorer — NCBI sequence downloader")
    print("=" * 60)

    total_downloaded = 0

    for gene_symbol, query in GENES:
        count = fetch_gene_sequences(
            gene_symbol=gene_symbol,
            query=query,
            output_dir=OUTPUT_DIR,
            max_records=MAX_RECORDS_PER_GENE,
        )
        total_downloaded += count

    print("\n" + "=" * 60)
    print(f"Download complete. Total sequences: {total_downloaded}")
    print(f"Files saved to: {OUTPUT_DIR}/")
    print("Next step: run  python main.py --all  to process the data")
    print("=" * 60)


if __name__ == "__main__":
    main()