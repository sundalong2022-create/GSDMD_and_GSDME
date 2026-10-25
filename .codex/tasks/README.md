# Task package index

Each package is a sequence of single-script sessions. The package files define prerequisites, output contracts, scientific acceptance, and downgrade rules. No package is started automatically; open the next script only after its inputs and the preceding acceptance check are present.

| Package | Session order | Status |
| --- | --- | --- |
| T0 | 01_make_table_s1.py -> 02_plot_fig1_3.py | blocked until frozen CSV inputs are placed in data/raw/ |
| T1 | 01_build_scores.py -> 02_deconvolve.py -> 03_partial_corr.py | highest priority after T0 inputs |
| T2 | 01_qc_cluster.py -> 02_deconv_RCTD.R -> 03_spatial_stats.py -> 04_immune_distance.py | starts after selected Visium samples and reference are present |
| T3 | 01_harmonize.py -> 02_meta.py -> 03_stratify.py | can start with six public cohorts |
| T4 | 01_death_scores.py -> 02_partial_corr.py | starts after T1 scores and gene sets |
| T5 | app.py -> export_zenodo.py -> manuscript automation | starts after stable figures and tables |

Canonical output paths in the contracts are relative to the explicit --outdir. For a canonical package run, pass --outdir results/tX; otherwise use a run-scoped directory and record its path in the session report.
