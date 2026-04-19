# Reproducibility

## Environment

- Python 3.11+
- Dependencies in `config/requirements.txt`

## Required local inputs

Place source materials under `data/raw/source_repo_snapshot/` from the project archive.
Raw data are intentionally ignored in git.

## Pipeline execution

Run full preparation:

```bash
python scripts/pipeline/run_all.py
```

This also runs `scripts/pipeline/build_manuscript_tables.py`, `build_sample_characteristics.py`, `extract_influence_counts.py`, `build_figures.py`, and `build_theme_wordclouds.py`, writing tables to `results/tables/` (including `top15_bands.csv`, `top15_vocalists.csv`, theme-count comparisons, and demographics summaries) and figures to `manuscript/figures/`.

Run stage-specific:

```bash
python scripts/stage1/complete_stage1_coding.py
python scripts/stage2/process_qualtrics.py
```

## Determinism and provenance

- Scripts write outputs with fixed filenames to `data/processed/`.
- Reports include record counts and timestamp.
- Assisted coding rows are labeled in `CodingSource`.

## Validation checks

- Stage 1 must include 18 unique participants (`A`-`R`).
- Qualtrics output must not contain restricted columns (`IPAddress`, `RecipientEmail`, geolocation fields).
- Manuscript tables are generated from files in `results/tables/`.
- Bar chart, Q44 heatmap, and wordcloud PNGs are produced under `manuscript/figures/` for the LaTeX manuscript.