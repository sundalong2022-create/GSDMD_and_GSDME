"""Report free disk space and known download requirements before retrieval."""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

from src.common.runner import add_run_arguments, prepare_run


def _known_size_gb(manifest: Path) -> tuple[float, float, int, list[str]]:
    minimum = maximum = 0.0
    known = 0
    unestimated: list[str] = []
    with manifest.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            low, high = row.get("estimated_gb_min", ""), row.get("estimated_gb_max", "")
            if not low or not high:
                if row.get("status", "").lower() in {"planned", "required"}:
                    unestimated.append(row.get("asset", "(unnamed asset)"))
                continue
            minimum += float(low)
            maximum += float(high)
            known += 1
    return minimum, maximum, known, unestimated


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_run_arguments(parser)
    parser.add_argument(
        "--manifest", type=Path, default=Path("config/downloads.tsv"),
        help="download manifest (default: config/downloads.tsv)",
    )
    args = parser.parse_args(argv)
    try:
        outdir, _config, logger = prepare_run(args, script_name="storage_check")
        root = Path.cwd().resolve()
        manifest = (root / args.manifest).resolve() if not args.manifest.is_absolute() else args.manifest.resolve()
        minimum, maximum, known, unestimated = _known_size_gb(manifest)
    except (OSError, ValueError, csv.Error) as exc:
        parser.error(str(exc))

    usage = shutil.disk_usage(root)
    free_gb = usage.free / (1024**3)
    logger.info(
        "storage: free=%.2f GiB, known download range=%.2f-%.2f GiB, known assets=%d",
        free_gb, minimum, maximum, known,
    )
    print(f"free_gib={free_gb:.2f}")
    print(f"known_download_gb={minimum:.2f}-{maximum:.2f} ({known} assets with estimates)")
    print(f"unestimated_planned_assets={len(unestimated)}")
    for asset in unestimated:
        print(f"needs_size_estimate={asset}")
    print(f"manifest={manifest}")
    print(f"run_outdir={outdir}")
    if unestimated:
        print("status=review_required: estimate all planned assets before approving aggregate download capacity")
        return 1
    required_gib = maximum / 1.073741824 + 5
    if free_gb < required_gib:
        print("status=review_required: reserve at least 5 GiB for unpacking and intermediates")
        return 1
    print("status=capacity_ok_for_known_estimates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
