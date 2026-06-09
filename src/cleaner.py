# cleaner.py
# Module responsible for validating and cleaning sequence records.
# Receives raw records from load_data.py and returns accepted/rejected lists.
# Part of the HUBA data preparation pipeline.

from __future__ import annotations


# ---------------------------------------------------------------------------
# Helper functions for sequence validation
# ---------------------------------------------------------------------------

def n_content(sequence: str) -> float:
    """Calculate the N content of a sequence as a fraction (0.0 to 1.0).

    N content is the proportion of unknown bases (N) in the sequence.
    Used as a data quality criterion — too many N bases means poor quality.
    Returns 0.0 if the sequence is empty.
    """
    # Return 0.0 for empty sequences to avoid division by zero
    if not sequence:
        return 0.0

    # Count N bases and divide by total sequence length
    return sequence.count("N") / len(sequence)


# Set of valid DNA characters — defined at module level for efficiency
ALLOWED_BASES = frozenset("ATGCN")


def is_valid_sequence(sequence: str) -> bool:
    """Check if a sequence contains only valid DNA characters.

    Valid characters are: A, T, G, C, N (uppercase).
    Returns False if any other character is found.
    """
    # Check every character against the allowed set
    return all(char in ALLOWED_BASES for char in sequence)


# ---------------------------------------------------------------------------
# Main cleaning function
# ---------------------------------------------------------------------------

def clean_records(
    records: list[dict],
    min_len: int,
    max_n_pct: float,
) -> tuple[list[dict], list[dict]]:
    """Validate and filter sequence records based on quality criteria.

    Rejection rules (applied in order):
        1. Empty sequence
        2. Invalid characters (not A/T/G/C/N)
        3. Sequence too short (length < min_len)
        4. Too many N bases (n_content > max_n_pct)

    Args:
        records:    list of sequence records from load_data.py
        min_len:    minimum accepted sequence length in base pairs
        max_n_pct:  maximum accepted N content as a fraction (0.0-1.0)

    Returns:
        accepted:  list of records that passed all filters
        rejected:  list of records that failed, each with a 'reason' key
    """
    accepted = []
    rejected = []

    for record in records:
        seq = record.get("sequence", "")

        # Initialise rejection flag and reason
        reject = False
        reason = ""

        # --- Rule 1: reject if sequence is empty ---
        if not seq:
            reject = True
            reason = "EMPTY_SEQUENCE"

        # --- Rule 2: reject if sequence contains invalid characters ---
        elif not is_valid_sequence(seq):
            reject = True
            reason = "INVALID_CHARACTERS"

        # --- Rule 3: reject if sequence is too short ---
        elif len(seq) < min_len:
            reject = True
            reason = (
                f"TOO_SHORT "
                f"(len={len(seq)}, min={min_len})"
            )

        # --- Rule 4: reject if N content is too high ---
        elif n_content(seq) > max_n_pct:
            reject = True
            reason = (
                f"HIGH_N "
                f"(n_pct={n_content(seq):.0%}, max={max_n_pct:.0%})"
            )

        # --- Append record to the correct output list ---
        if reject:
            rejected.append({**record, "reason": reason})
        else:
            accepted.append(record)

    return accepted, rejected


# ---------------------------------------------------------------------------
# Summary statistics for cleaning report
# ---------------------------------------------------------------------------

def cleaning_summary(
    accepted: list[dict],
    rejected: list[dict],
) -> dict:
    """Generate a summary dictionary for the cleaning step.

    Returns a dict with total counts and rejection reasons breakdown.
    """
    total = len(accepted) + len(rejected)

    # Count how many records were rejected for each reason
    reasons: dict[str, int] = {}
    for record in rejected:
        # Extract reason prefix only, e.g. "TOO_SHORT" from
        # "TOO_SHORT (len=4, min=20)"
        reason_key = record.get("reason", "UNKNOWN").split("(")[0].strip()
        reasons[reason_key] = reasons.get(reason_key, 0) + 1

    return {
        "total_input": total,
        "accepted": len(accepted),
        "rejected": len(rejected),
        "rejection_reasons": reasons,
    }