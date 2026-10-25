"""Fixed tabular contracts and repository-wide validation."""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path
from typing import Iterable

import yaml


OUTPUT_SCHEMAS: dict[tuple[str, ...], tuple[str, ...]] = {
    ("t0", "table_s1.tsv"): (
        "dataset", "cancer", "gene", "contrast", "effect", "ci_lo", "ci_hi",
        "p", "q_bh", "robust_p", "loo_sign_stable", "n_patients", "n_endo",
        "pct_endo", "proxy_note",
    ),
    ("t0", "table_s2.tsv"): (
        "dataset", "cancer", "gene", "contrast", "effect", "ci_lo", "ci_hi",
        "p", "q_bh", "robust_p", "loo_sign_stable", "n_patients", "n_endo",
        "pct_endo", "proxy_note",
    ),
    ("t1", "assoc.tsv"): (
        "cancer", "score_type", "immune_cell", "method", "rho", "p",
        "partial_rho_adj_myeloid_endo", "delta_r", "boot_lo", "boot_hi",
    ),
    ("t1", "scores.tsv"): (
        "sample", "score_type", "method", "score", "n_genes_used",
    ),
    ("t2", "spot_stats.tsv"): (
        "sample", "cancer", "region", "celltype", "prop_mean", "moran_i", "p",
    ),
    ("t2", "distance_stats.tsv"): (
        "sample", "cancer", "region", "immune_cell", "metric", "effect",
        "p", "permutation_p", "n_permutations", "n_spots",
    ),
    ("t3", "cohort_effects.tsv"): (
        "cohort", "cancer", "drug", "endpoint", "score", "effect_scale",
        "score_unit", "n", "effect", "se", "response_definition",
    ),
    ("t3", "cohort_strata.tsv"): (
        "cohort", "cancer", "source", "proxy_method", "proxy_value", "stratum",
        "cutoff",
    ),
    ("t3", "meta.tsv"): (
        "cancer", "drug", "endpoint", "score", "effect_scale", "estimator",
        "n_cohorts", "effect", "se", "i2", "tau2", "p", "loo_stable",
    ),
    ("t3", "meta_stratified.tsv"): (
        "score", "effect_scale", "stratum", "endpoint", "estimator",
        "n_cohorts", "effect", "se", "i2", "tau2", "p", "loo_stable",
    ),
    ("t4", "partial_corr.tsv"): (
        "cancer", "score", "death_program", "partial_rho", "p", "covars",
    ),
    ("t4", "immune_assoc.tsv"): (
        "cancer", "score", "immune_cell", "partial_rho", "p", "covars",
    ),
}

CONFIG_SCHEMAS: dict[str, tuple[str, ...]] = {
    "config/datasets.tsv": (
        "dataset", "cancer", "n_patients", "proxy_malignant", "n_endo",
        "pct_endo", "source", "notes",
    ),
    "config/cancer_map.tsv": ("cancer", "tcga_code", "tisch2_dataset"),
    "config/ici_cohorts.tsv": (
        "cohort", "cancer", "drug", "endpoint", "response_definition", "source",
        "license",
    ),
    "config/downloads.tsv": (
        "asset", "category", "source_or_accession", "raw_subdir",
        "estimated_gb_min", "estimated_gb_max", "status", "notes",
    ),
}

MISSING_TOKENS = {"", "na", "n/a", "nan", "null", "none"}


def validate_tsv(path: Path, expected: Iterable[str]) -> list[str]:
    """Return contract violations for a TSV, requiring exact header names/order."""
    expected_columns = tuple(expected)
    if not path.is_file():
        return [f"missing file: {path}"]
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            header = next(csv.reader(handle, delimiter="\t"), None)
    except (OSError, UnicodeError, csv.Error) as exc:
        return [f"cannot read {path}: {exc}"]

    if header is None:
        return [f"empty file: {path}"]
    if len(header) != len(set(header)):
        return [f"duplicate columns in {path}: {header}"]
    if tuple(header) != expected_columns:
        return [f"wrong columns in {path}: expected {expected_columns}, got {tuple(header)}"]
    return []


def _validation_settings(root: Path) -> tuple[int, float]:
    config_path = root / "config" / "params.yaml"
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        validation = config.get("validation", {})
        min_rows = int(validation.get("min_result_rows", 1))
        max_nan_fraction = float(validation.get("max_nan_fraction", 0.05))
    except (OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        raise ValueError(f"cannot read validation settings from {config_path}: {exc}") from exc
    if min_rows < 1:
        raise ValueError("validation.min_result_rows must be at least 1")
    if not 0 <= max_nan_fraction <= 1 or not math.isfinite(max_nan_fraction):
        raise ValueError("validation.max_nan_fraction must be between 0 and 1")
    return min_rows, max_nan_fraction


def _check_result_quality(path: Path, min_rows: int, max_nan_fraction: float) -> tuple[list[str], str]:
    errors: list[str] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, delimiter="\t")
            header = next(reader, None)
            if header is None:
                return [f"empty file: {path}"], "rows=0 missing=0/0 (0.0%)"
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        return [f"cannot inspect {path}: {exc}"], "quality unavailable"

    row_count = len(rows)
    malformed_rows = [index + 2 for index, row in enumerate(rows) if len(row) != len(header)]
    if malformed_rows:
        errors.append(
            f"row width does not match header in {path}: data lines {malformed_rows[:10]}"
        )
    if row_count < min_rows:
        errors.append(f"too few data rows in {path}: expected at least {min_rows}, got {row_count}")
    cell_count = len(header) * row_count
    missing_count = sum(
        1
        for row in rows
        for value in (row + [""] * max(0, len(header) - len(row)))[:len(header)]
        if value.strip().lower() in MISSING_TOKENS
    )
    missing_fraction = missing_count / cell_count if cell_count else 0.0
    if missing_fraction > max_nan_fraction:
        errors.append(
            f"missing-value fraction exceeds limit in {path}: "
            f"{missing_fraction:.1%} > {max_nan_fraction:.1%}"
        )
    detail = f"rows={row_count} missing={missing_count}/{cell_count} ({missing_fraction:.1%})"
    return errors, detail


def validate_repository(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    reports: list[str] = []
    for relative, columns in CONFIG_SCHEMAS.items():
        errors.extend(validate_tsv(root / relative, columns))

    try:
        min_rows, max_nan_fraction = _validation_settings(root)
    except ValueError as exc:
        return [str(exc)], reports

    results_root = root / "results"
    if results_root.exists():
        for path in sorted(results_root.rglob("*.tsv")):
            relative_parts = path.relative_to(results_root).parts
            expected = next(
                (columns for suffix, columns in OUTPUT_SCHEMAS.items()
                 if len(relative_parts) >= len(suffix)
                 and relative_parts[-len(suffix):] == suffix),
                None,
            )
            if expected is None:
                errors.append(f"unregistered TSV output under results/: {path.relative_to(root)}")
                continue
            schema_errors = validate_tsv(path, expected)
            errors.extend(schema_errors)
            if not schema_errors:
                quality_errors, detail = _check_result_quality(path, min_rows, max_nan_fraction)
                reports.append(f"{path.relative_to(root)}: {detail}")
                errors.extend(quality_errors)

    return errors, reports


def main() -> int:
    root = Path.cwd()
    errors, reports = validate_repository(root)
    for report in reports:
        print(report)
    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Manifest headers, result schemas, row counts, and missing-value limits are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
