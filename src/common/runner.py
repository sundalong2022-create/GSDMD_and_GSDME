"""Shared command-line and run setup for analysis scripts."""

from __future__ import annotations

import argparse
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml

from .logging import get_logger


def add_run_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the repository-wide run options to a stage parser.

    Every executable stage accepts the same options so it can be run directly
    or through Make without changing how output locations and randomness are
    configured.
    """
    parser.add_argument(
        "--outdir", type=Path, default=None,
        help="directory for this run's outputs (default: results/<UTC run id>)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="random seed (default: 42)",
    )
    parser.add_argument(
        "--config", type=Path, default=Path("config/params.yaml"),
        help="YAML analysis configuration (default: config/params.yaml)",
    )


def prepare_run(
    args: argparse.Namespace,
    *,
    script_name: str,
    project_root: Path | None = None,
) -> tuple[Path, Mapping[str, Any], Any]:
    """Resolve paths, load YAML, seed Python, and configure file logging."""
    root = (project_root or Path.cwd()).resolve()
    if args.outdir is None:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        outdir = root / "results" / run_id
    else:
        outdir = (root / args.outdir).resolve() if not args.outdir.is_absolute() else args.outdir.resolve()
    config_path = (root / args.config).resolve() if not args.config.is_absolute() else args.config.resolve()
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ValueError(f"cannot read config {config_path}: {exc}") from exc
    if not isinstance(config, Mapping):
        raise ValueError(f"config must contain a YAML mapping: {config_path}")
    outdir.mkdir(parents=True, exist_ok=True)
    random.seed(args.seed)
    try:
        import numpy as np
    except ImportError:
        pass
    else:
        np.random.seed(args.seed)
    logger = get_logger(script_name, root / "logs" / f"{script_name}.log")
    logger.info("run setup: outdir=%s seed=%d config=%s", outdir, args.seed, config_path)
    return outdir, config, logger
