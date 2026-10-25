# GSDM compartment atlas

Analysis scaffold for the pan-cancer study of GSDMD/GSDME cell-of-origin, family-level pyroptosis scores, spatial context, and immunotherapy associations.

## Status

This repository is the project skeleton and data-contract layer. The workspace supplied for initialization contained no existing CSVs, figures, or reports, so cohort values have not been fabricated. The input manifests currently contain headers only. Populate them from the frozen source tables before running analyses.

## Layout

- config/: cohort manifests and analysis parameters.
- data/raw/: immutable source data. Keep original downloads here; scripts must never write to this directory.
- data/interim/ and data/processed/: reproducible intermediate and processed data.
- src/common/: shared I/O, statistics, plotting, logging, and fixed table schemas.
- src/t0_freeze/ through src/t5_resource/: analysis-stage packages.
- results/<run_id>/: outputs from a single run, separated by stage.
- figures/, logs/, tests/, and manuscript/: figures, logs, tests, and writing files.

## Environment and validation

Create the conda environment with conda env create -f environment.yml, then activate gsdm-compartment. Install immunedeconv in that environment before the bulk stage with R -e 'remotes::install_github("omnideconv/immunedeconv")'; use its quantiseq, epic, and mcp-counter methods. CIBERSORTx is optional revalidation only and is disabled by default, so no token is required for the main workflow.

Every stage entry point accepts --outdir, --seed, and --config; for example, make t1 OUTDIR=results/bulk_seed42 SEED=42. Logs are written to logs/pipeline_t1.log. Run make storage-check before downloading. It reports free disk space and refuses an aggregate capacity pass while any planned asset lacks a size estimate; reserve at least 5 GiB for unpacking and intermediates.

make t0, make t1, make t2, make t3, make t4, and make all reserve the ordered workflow entry points. They currently stop with an explicit scaffold status until the corresponding source data and stage implementations are added; make verify is available now.

## Data contracts

The required output columns and order are defined once in src/common/schema.py. Stage outputs must use tab-separated files with those exact headers:

| Output | Contract |
| --- | --- |
| t0/table_s1.tsv | dataset, cancer, gene, contrast, effect, ci_lo, ci_hi, p, q_bh, robust_p, loo_sign_stable, n_patients, n_endo, pct_endo, proxy_note |
| t0/table_s2.tsv | Same columns as S1, containing the sensitivity-analysis subset |
| t1/scores.tsv | sample, score_type, method, score, n_genes_used |
| t1/assoc.tsv | cancer, score_type, immune_cell, method, rho, p, partial_rho_adj_myeloid_endo, delta_r, boot_lo, boot_hi |
| t2/spot_stats.tsv | sample, cancer, region, celltype, prop_mean, moran_i, p |
| t2/distance_stats.tsv | sample, cancer, region, immune_cell, metric, effect, p, permutation_p, n_permutations, n_spots |
| t3/cohort_effects.tsv | cohort, cancer, drug, endpoint, score, effect_scale, score_unit, n, effect, se, response_definition |
| t3/cohort_strata.tsv | cohort, cancer, source, proxy_method, proxy_value, stratum, cutoff |
| t3/meta.tsv | cancer, drug, endpoint, score, effect_scale, estimator, n_cohorts, effect, se, i2, tau2, p, loo_stable |
| t3/meta_stratified.tsv | score, effect_scale, stratum, endpoint, estimator, n_cohorts, effect, se, i2, tau2, p, loo_stable |
| t4/partial_corr.tsv | cancer, score, death_program, partial_rho, p, covars |
| t4/immune_assoc.tsv | cancer, score, immune_cell, partial_rho, p, covars |

make verify runs pytest, checks every matching table found under results/ against its exact schema, and rejects generated tables with zero rows or more than the configured missing-value fraction (default 5%). It does not require result files to exist yet. Raw inputs are read-only; downloads belong in data/raw and processed copies in data/interim or data/processed.

The family-score method and its gene-level transformations are declared in config/params.yaml as provisional defaults. Freeze them before analysis and record any change with the run configuration.
