"""Workflow entry point; stage commands are reserved until implementations land."""

from __future__ import annotations

import argparse
import sys

from .common.runner import add_run_arguments, prepare_run


STAGE_NAMES = {
    "t0": "freeze source results and create S1/S2 and Figures 1-3",
    "t1": "TCGA bulk score and immune-association analysis",
    "t2": "Visium deconvolution and spatial analysis",
    "t3": "ICI cohort harmonization and random-effects meta-analysis",
    "t4": "death-program specificity analysis",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one GSDM compartment analysis stage")
    parser.add_argument("stage", choices=tuple(STAGE_NAMES), help="analysis stage to run")
    add_run_arguments(parser)
    args = parser.parse_args(argv)
    stage = args.stage
    try:
        outdir, _config, logger = prepare_run(args, script_name=f"pipeline_{stage}")
    except ValueError as exc:
        parser.error(str(exc))
    logger.warning("%s is scaffold-only: %s", stage, STAGE_NAMES[stage])
    print(
        f"{stage} is scaffold-only ({STAGE_NAMES[stage]}). "
        "Add the frozen input data and implement this stage before running it.",
        file=sys.stderr,
    )
    logger.info("stage stopped before analysis; output directory is %s", outdir)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
