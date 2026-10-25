"""Path helpers that keep raw inputs immutable and outputs run-scoped."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Iterable, Mapping


class PathPolicyError(ValueError):
    """Raised when a path violates the repository's data-write policy."""


def raw_input_path(project_root: Path, relative_path: str) -> Path:
    """Resolve an existing source file under data/raw without creating anything."""
    raw_root = (project_root / "data" / "raw").resolve()
    candidate = (raw_root / relative_path).resolve()
    if not candidate.is_relative_to(raw_root):
        raise PathPolicyError("raw input path must stay inside data/raw")
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def result_path(project_root: Path, run_id: str, relative_path: str) -> Path:
    """Resolve an output under results/<run_id> and reject path traversal."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", run_id):
        raise PathPolicyError("run_id may contain only letters, digits, dot, underscore, and hyphen")
    results_root = (project_root / "results" / run_id).resolve()
    candidate = (results_root / relative_path).resolve()
    if not candidate.is_relative_to(results_root):
        raise PathPolicyError("result path must stay inside its run directory")
    return candidate


def write_tsv(
    path: Path,
    rows: Iterable[Mapping[str, object]],
    columns: Iterable[str],
) -> None:
    """Write a TSV. Callers should obtain path from result_path()."""
    fieldnames = tuple(columns)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
