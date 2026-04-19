# what-do-we-actually-do-with-our-voices

Publication workspace for a two-stage study on extreme metal vocals.

## Scope

This repository is organized for manuscript preparation and reproducible analysis.

- **Stage 1**: 18 one-on-one interviews with vocalists.
- **Stage 2**: Qualtrics dataset with quantitative and open-ended responses.

## Authors

- Alexey Voronin
- Nat Condit-Schultz

## Repository layout

- `data/processed/` - de-identified analysis-ready data
- `data/codebooks/` - codebooks and code mappings
- `scripts/stage1/` - interview coding and stage-1 preparation
- `scripts/stage2/` - Qualtrics cleaning and stage-2 coding
- `scripts/pipeline/` - end-to-end orchestration
- `results/` - generated outputs (tables, figures, reports)
- `manuscript/` - Journal of Voice submission files
- `docs/` - data policy, reproducibility, and methodology notes
- `config/` - project configuration

## Reproducibility quick start

1. Create and activate a Python environment.
2. Install dependencies from `config/requirements.txt`.
3. Place restricted source files under `data/raw/` (not tracked).
4. Run:

```bash
python scripts/pipeline/run_all.py
```

Outputs will be written to `data/processed/` and `results/`.

## Data governance

This workspace contains human-subject materials. Public artifacts must be de-identified.
See:

- `docs/ETHICS_DATA_POLICY.md`
- `docs/DATA_DICTIONARY.md`
- `docs/REPRODUCIBILITY.md`
