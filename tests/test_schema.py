from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.common.io import PathPolicyError, result_path
from src.common.schema import (
    OUTPUT_SCHEMAS,
    _check_result_quality,
    validate_repository,
    validate_tsv,
)


class SchemaTests(unittest.TestCase):
    def test_valid_header_is_accepted(self) -> None:
        columns = next(iter(OUTPUT_SCHEMAS.values()))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "table.tsv"
            path.write_text("\t".join(columns) + "\n", encoding="utf-8")
            self.assertEqual(validate_tsv(path, columns), [])

    def test_wrong_order_is_rejected(self) -> None:
        columns = next(iter(OUTPUT_SCHEMAS.values()))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "table.tsv"
            path.write_text("\t".join(reversed(columns)) + "\n", encoding="utf-8")
            self.assertTrue(validate_tsv(path, columns))

    def test_result_path_rejects_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(PathPolicyError):
                result_path(Path(temporary), "run-1", "../../data/raw/overwrite.tsv")

    def test_quality_check_rejects_zero_data_rows(self) -> None:
        columns = next(iter(OUTPUT_SCHEMAS.values()))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "table.tsv"
            path.write_text("\t".join(columns) + "\n", encoding="utf-8")
            errors, detail = _check_result_quality(path, min_rows=1, max_nan_fraction=0.05)
            self.assertTrue(any("too few data rows" in error for error in errors))
            self.assertIn("rows=0", detail)

    def test_quality_check_rejects_missing_values_and_bad_row_width(self) -> None:
        columns = next(iter(OUTPUT_SCHEMAS.values()))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "table.tsv"
            path.write_text(
                "\t".join(columns) + "\n" +
                "\t".join([""] * len(columns)) + "\n" +
                "short\n",
                encoding="utf-8",
            )
            errors, detail = _check_result_quality(path, min_rows=1, max_nan_fraction=0.05)
            self.assertTrue(any("missing-value fraction" in error for error in errors))
            self.assertTrue(any("row width" in error for error in errors))
            self.assertIn("missing=29/30", detail)

    def test_repository_rejects_unregistered_result_table(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "config").mkdir()
            for relative, columns in {
                "config/datasets.tsv": ("dataset", "cancer", "n_patients", "proxy_malignant", "n_endo", "pct_endo", "source", "notes"),
                "config/cancer_map.tsv": ("cancer", "tcga_code", "tisch2_dataset"),
                "config/ici_cohorts.tsv": ("cohort", "cancer", "drug", "endpoint", "response_definition", "source", "license"),
                "config/downloads.tsv": ("asset", "category", "source_or_accession", "raw_subdir", "estimated_gb_min", "estimated_gb_max", "status", "notes"),
            }.items():
                path = root / relative
                path.write_text("\t".join(columns) + "\n", encoding="utf-8")
            (root / "config" / "params.yaml").write_text(
                "validation:\n  min_result_rows: 1\n  max_nan_fraction: 0.05\n",
                encoding="utf-8",
            )
            rogue = root / "results" / "run1" / "notes.tsv"
            rogue.parent.mkdir(parents=True)
            rogue.write_text("note\nplaceholder\n", encoding="utf-8")
            errors, _reports = validate_repository(root)
            self.assertTrue(any("unregistered TSV" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
