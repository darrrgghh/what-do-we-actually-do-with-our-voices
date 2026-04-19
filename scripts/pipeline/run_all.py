from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd


def run_script(path: Path) -> None:
    result = subprocess.run([sys.executable, str(path)], check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Failed: {path}")


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]

    run_script(project_root / "scripts" / "stage1" / "complete_stage1_coding.py")
    run_script(project_root / "scripts" / "stage2" / "process_qualtrics.py")
    run_script(project_root / "scripts" / "pipeline" / "build_manuscript_tables.py")
    run_script(project_root / "scripts" / "pipeline" / "extract_influence_counts.py")
    run_script(project_root / "scripts" / "pipeline" / "build_figures.py")
    run_script(project_root / "scripts" / "pipeline" / "build_theme_wordclouds.py")

    processed = project_root / "data" / "processed"
    results_tables = project_root / "results" / "tables"
    results_reports = project_root / "results" / "reports"
    results_tables.mkdir(parents=True, exist_ok=True)
    results_reports.mkdir(parents=True, exist_ok=True)

    stage1 = pd.read_csv(processed / "stage1_segments_18.csv")
    stage2 = pd.read_csv(processed / "stage2_text_segments.csv")

    stage1_theme = stage1.groupby("Theme", as_index=False).size().rename(columns={"size": "Stage1Count"})
    stage2_theme = stage2.groupby("Theme", as_index=False).size().rename(columns={"size": "Stage2Count"})
    theme_compare = stage1_theme.merge(stage2_theme, on="Theme", how="outer").fillna(0)
    theme_compare["Stage1Count"] = theme_compare["Stage1Count"].astype(int)
    theme_compare["Stage2Count"] = theme_compare["Stage2Count"].astype(int)
    theme_compare["Total"] = theme_compare["Stage1Count"] + theme_compare["Stage2Count"]
    theme_compare = theme_compare.sort_values("Total", ascending=False)

    stage1_code = (
        stage1.groupby(["Theme", "PrimaryCode"], as_index=False)
        .size()
        .rename(columns={"size": "Count"})
        .sort_values(["Theme", "Count"], ascending=[True, False])
    )
    stage2_code = (
        stage2.groupby(["Theme", "PrimaryCode"], as_index=False)
        .size()
        .rename(columns={"size": "Count"})
        .sort_values(["Theme", "Count"], ascending=[True, False])
    )

    theme_compare.to_csv(results_tables / "theme_counts_stage1_stage2.csv", index=False)
    stage1_code.to_csv(results_tables / "stage1_primarycode_counts.csv", index=False)
    stage2_code.to_csv(results_tables / "stage2_primarycode_counts.csv", index=False)

    sample_overview = pd.DataFrame(
        [
            {"metric": "stage1_participants", "value": stage1["Vocalist"].nunique()},
            {"metric": "stage1_segments", "value": len(stage1)},
            {"metric": "stage2_respondents", "value": stage2["RespondentID"].nunique()},
            {"metric": "stage2_segments", "value": len(stage2)},
        ]
    )
    sample_overview.to_csv(results_reports / "sample_overview.csv", index=False)
    print("Pipeline finished successfully.")


if __name__ == "__main__":
    main()

