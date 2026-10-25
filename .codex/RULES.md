# Codex execution rules

These rules apply to every analysis session in this project.

## Scope and session boundaries

1. One session implements and runs one script. A task package is split into one session per script; do not implement sibling scripts in the same session.
2. Before starting a script, read its package contract in .codex/tasks/TX.md, confirm that its input files exist, and confirm the upstream output schema.
3. If a required input is absent, stop with a clear missing-input report. Do not create mock biological data and do not silently switch to a different cohort.
4. Write tests first, then implement the smallest change that satisfies the tests. Run the script once with an explicit output directory and seed.
5. Run make verify before reporting completion. Scientific acceptance gates (G1, G2, G3, and task-specific row counts) are additional checks and cannot be replaced by make verify.

## Repository and branches

Each script session uses a branch named feat/<task>-<script>, and the branch must pass make verify before merge. The current workspace is not yet a Git repository; initialize Git and create the first branch before opening the first implementation session. Do not claim a branch-based acceptance until that prerequisite is satisfied.

## Data and network

- data/raw/ is immutable. No script may write, delete, unpack over, or normalize files there.
- Large downloads are performed manually and only when the active task needs them. Scripts must not download TCGA, Visium, GEO, ENA, or controlled-access data.
- Store downloaded archives and their checksums/retrieval metadata under data/raw/; write derived data under data/interim/ or data/processed/.
- Controlled-access datasets are optional and must never block the public-cohort workflow.

## Configuration, reproducibility, and logging

- Every executable script accepts --outdir, --seed, and --config; use src.common.runner.add_run_arguments.
- Every run uses an explicit seed and writes logs/<script>.log.
- Analysis parameters belong in config/params.yaml. Do not hard-code QC thresholds, permutation counts, bootstrap counts, score definitions, or gate thresholds in scripts.
- Use the run-scoped output directory supplied by --outdir. Do not write to a fixed result path unless the session explicitly passes that path.

## Contracts and validation

- Output TSV headers and order are defined only in src/common/schema.py.
- Every generated TSV under results/ must be registered in the schema map. Unknown TSVs, zero-row outputs, malformed rows, and missing-value fractions over the configured limit fail validation.
- Keep intermediate cohort-level and diagnostic tables when they are needed to substantiate a gate; do not compress them into a pooled result that cannot be audited.
- Never overwrite an upstream result in place. Use a new run directory or a deliberately named output path.

## Statistical decisions

Freeze score standardization scope, gene-set/version, effect scale, replicate unit, permutation null, and meta-analysis estimator in config/params.yaml before the corresponding script runs. Report the denominator and exclusion rule for every gate. A gate that cannot be computed from the registered output tables is not accepted.

## Scope control

Only modify files inside the active script's source directory, its tests, and the explicitly required contract/config documentation. Do not change unrelated modules or download data as a convenience.
