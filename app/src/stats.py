# app/src/stats.py
# Statistical analysis functions for BioSeq Explorer.
# Provides t-test, ANOVA, Mann-Whitney U test and correlation matrix
# for QC metrics (GC%, N%, length) grouped by gene/_source.
#
# All functions accept a pandas DataFrame produced by analyzer.run_quality_analysis()
# and return a dict or DataFrame with results — no side effects.

from __future__ import annotations

import pandas as pd
from scipy import stats as scipy_stats

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Minimum number of sequences per group required to run a test
MIN_GROUP_SIZE = 3

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_groups(
    qc_df: pd.DataFrame,
    metric: str,
) -> dict[str, pd.Series]:
    """Split a metric column into groups by '_source'.

    Args:
        qc_df:  DataFrame with QC metrics and '_source' column.
        metric: Column name to extract (e.g. 'gc_content').

    Returns:
        Dict mapping source name to Series of metric values.
        Only groups with at least MIN_GROUP_SIZE values are included.
    """
    if "_source" not in qc_df.columns:
        return {}

    groups = {}
    for source, group_df in qc_df.groupby("_source"):
        values = group_df[metric].dropna()
        if len(values) >= MIN_GROUP_SIZE:
            groups[source] = values
    return groups


# ---------------------------------------------------------------------------
# Individual statistical tests
# ---------------------------------------------------------------------------

def run_ttest(
    qc_df: pd.DataFrame,
    metric: str,
    group_a: str,
    group_b: str,
) -> dict:
    """Run an independent samples t-test between two gene groups.

    Tests whether the means of a QC metric differ significantly
    between two selected genes/sources.

    Args:
        qc_df:   DataFrame with QC metrics and '_source' column.
        metric:  Metric to compare ('gc_content', 'n_content', 'length').
        group_a: '_source' value for the first group.
        group_b: '_source' value for the second group.

    Returns:
        Dict with keys:
            test       : str, test name
            metric     : str, metric name
            group_a    : str
            group_b    : str
            mean_a     : float
            mean_b     : float
            statistic  : float, t-statistic
            p_value    : float
            significant: bool, True if p_value < 0.05
            note       : str, plain-language interpretation
    """
    groups = _get_groups(qc_df, metric)

    if group_a not in groups or group_b not in groups:
        return {"error": f"Group '{group_a}' or '{group_b}' not found or too small."}

    a_vals = groups[group_a]
    b_vals = groups[group_b]

    stat, p = scipy_stats.ttest_ind(a_vals, b_vals, equal_var=False)

    significant = bool(p < 0.05)
    note = (
        f"Significant difference between {group_a} and {group_b} (p={p:.4f})."
        if significant
        else f"No significant difference between {group_a} and {group_b} (p={p:.4f})."
    )

    return {
        "test":        "Independent t-test (Welch)",
        "metric":      metric,
        "group_a":     group_a,
        "group_b":     group_b,
        "mean_a":      round(float(a_vals.mean()), 6),
        "mean_b":      round(float(b_vals.mean()), 6),
        "n_a":         len(a_vals),
        "n_b":         len(b_vals),
        "statistic":   round(float(stat), 6),
        "p_value":     round(float(p), 6),
        "significant": significant,
        "note":        note,
    }


def run_anova(
    qc_df: pd.DataFrame,
    metric: str,
) -> dict:
    """Run a one-way ANOVA across all gene groups for a given metric.

    Tests whether the means of a QC metric differ significantly
    across all genes/sources simultaneously.

    Args:
        qc_df:  DataFrame with QC metrics and '_source' column.
        metric: Metric to compare ('gc_content', 'n_content', 'length').

    Returns:
        Dict with keys:
            test       : str, test name
            metric     : str
            groups     : list of group names included
            f_statistic: float
            p_value    : float
            significant: bool
            note       : str
    """
    groups = _get_groups(qc_df, metric)

    if len(groups) < 2:
        return {"error": "ANOVA requires at least 2 groups with enough sequences."}

    group_values = list(groups.values())
    f_stat, p = scipy_stats.f_oneway(*group_values)

    significant = bool(p < 0.05)
    note = (
        f"Significant difference across groups (p={p:.4f}). "
        "Consider pairwise t-tests to identify which groups differ."
        if significant
        else f"No significant difference across groups (p={p:.4f})."
    )

    return {
        "test":        "One-way ANOVA",
        "metric":      metric,
        "groups":      list(groups.keys()),
        "n_groups":    len(groups),
        "f_statistic": round(float(f_stat), 6),
        "p_value":     round(float(p), 6),
        "significant": significant,
        "note":        note,
    }


def run_mannwhitney(
    qc_df: pd.DataFrame,
    metric: str,
    group_a: str,
    group_b: str,
) -> dict:
    """Run a Mann-Whitney U test between two gene groups.

    Non-parametric alternative to t-test. Does not assume normal distribution.
    Useful when sequence counts per gene are small.

    Args:
        qc_df:   DataFrame with QC metrics and '_source' column.
        metric:  Metric to compare ('gc_content', 'n_content', 'length').
        group_a: '_source' value for the first group.
        group_b: '_source' value for the second group.

    Returns:
        Dict with keys:
            test       : str, test name
            metric     : str
            group_a    : str
            group_b    : str
            median_a   : float
            median_b   : float
            statistic  : float, U statistic
            p_value    : float
            significant: bool
            note       : str
    """
    groups = _get_groups(qc_df, metric)

    if group_a not in groups or group_b not in groups:
        return {"error": f"Group '{group_a}' or '{group_b}' not found or too small."}

    a_vals = groups[group_a]
    b_vals = groups[group_b]

    stat, p = scipy_stats.mannwhitneyu(a_vals, b_vals, alternative="two-sided")

    significant = bool(p < 0.05)
    note = (
        f"Significant difference between {group_a} and {group_b} (p={p:.4f})."
        if significant
        else f"No significant difference between {group_a} and {group_b} (p={p:.4f})."
    )

    return {
        "test":        "Mann-Whitney U",
        "metric":      metric,
        "group_a":     group_a,
        "group_b":     group_b,
        "median_a":    round(float(a_vals.median()), 6),
        "median_b":    round(float(b_vals.median()), 6),
        "n_a":         len(a_vals),
        "n_b":         len(b_vals),
        "statistic":   round(float(stat), 6),
        "p_value":     round(float(p), 6),
        "significant": significant,
        "note":        note,
    }


# ---------------------------------------------------------------------------
# Correlation matrix
# ---------------------------------------------------------------------------

def compute_correlation_matrix(
    qc_df: pd.DataFrame,
    method: str = "pearson",
) -> pd.DataFrame:
    """Compute correlation matrix for QC metrics.

    Calculates pairwise correlations between gc_content, n_content and length.

    Args:
        qc_df:  DataFrame with QC metrics.
        method: Correlation method — 'pearson' or 'spearman'.

    Returns:
        Symmetric DataFrame with correlation coefficients.
        Raises ValueError if required columns are missing.
    """
    required = {"gc_content", "n_content", "length"}
    missing = required - set(qc_df.columns)
    if missing:
        raise ValueError(
            f"Missing columns for correlation: {missing}. "
            "Run analyzer.run_quality_analysis() first."
        )

    metrics_df = qc_df[["gc_content", "n_content", "length"]].copy()
    metrics_df.columns = ["GC content", "N content", "Length (bp)"]

    return metrics_df.corr(method=method).round(4)


# ---------------------------------------------------------------------------
# Results formatting helpers
# ---------------------------------------------------------------------------

def result_to_dataframe(result: dict) -> pd.DataFrame:
    """Convert a single test result dict to a two-column DataFrame for display.

    Args:
        result: Dict returned by run_ttest(), run_anova() or run_mannwhitney().

    Returns:
        DataFrame with columns ['Parameter', 'Value'] for display in Treeview.
    """
    if "error" in result:
        return pd.DataFrame([{"Parameter": "Error", "Value": result["error"]}])

    rows = []
    for key, value in result.items():
        if key == "groups":
            value = ", ".join(value)
        elif isinstance(value, bool):
            value = "Yes" if value else "No"
        elif isinstance(value, float):
            value = f"{value:.6f}"
        rows.append({"Parameter": key.replace("_", " ").title(), "Value": str(value)})

    return pd.DataFrame(rows)