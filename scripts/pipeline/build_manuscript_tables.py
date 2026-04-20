from __future__ import annotations
from pathlib import Path
import pandas as pd

def build_stage1_tables(root: Path) -> None:
    s1 = pd.read_csv(root / "data" / "processed" / "stage1_segments_18.csv")
    s1["PrimaryCodeNorm"] = (
        s1["PrimaryCode"]
        .astype(str)
        .str.strip()
        .replace({"SCREAMINIG_TECHNIQUE": "SCREAMING_TECHNIQUE"})
    )

    theme_summary = (
        s1.groupby("Theme", as_index=False)
        .size()
        .rename(columns={"size": "SegmentCount"})
        .sort_values("SegmentCount", ascending=False)
    )
    theme_summary.to_csv(root / "results" / "tables" / "stage1_theme_summary.csv", index=False)

    code_summary = (
        s1.groupby(["Theme", "PrimaryCodeNorm"], as_index=False)
        .size()
        .rename(columns={"size": "Count"})
        .sort_values(["Theme", "Count"], ascending=[True, False])
    )
    code_summary.to_csv(root / "results" / "tables" / "stage1_primarycode_counts_clean.csv", index=False)


def build_stage2_tables(root: Path) -> None:
    df = pd.read_csv(root / "data" / "processed" / "qualtrics_deidentified.csv")
    flow_rows = [("Qualtrics rows in export", len(df))]
    flow_rows.append(
        (
            "Finished responses (Finished=1)",
            int(pd.to_numeric(df["Finished"], errors="coerce").eq(1).sum()),
        )
    )

    qblock_cols = ["Q43 Perc-Class"] + [f"Q44_{i}" for i in range(1, 13)] + ["Q45_1", "Q45_2", "Q45_3", "Q46"]
    qblock_cols = [c for c in qblock_cols if c in df.columns]
    qblock = df[qblock_cols].fillna("").astype(str)
    any_qblock = qblock.apply(lambda r: any(x.strip() != "" for x in r), axis=1)
    flow_rows.append(("Any response in Q43-Q46 block", int(any_qblock.sum())))
    flow_rows.append(
        (
            "Any response in Q43-Q46 and Finished=1",
            int((any_qblock & pd.to_numeric(df["Finished"], errors="coerce").eq(1)).sum()),
        )
    )

    q44 = df[[f"Q44_{i}" for i in range(1, 13)]].fillna("").astype(str)
    flow_rows.append(("At least one Q44 row answered", int(q44.apply(lambda r: any(x.strip() != "" for x in r), axis=1).sum())))
    q45 = df[["Q45_1", "Q45_2", "Q45_3"]].fillna("").astype(str)
    flow_rows.append(("All three Q45 fields non-empty", int(q45.apply(lambda r: all(x.strip() != "" for x in r), axis=1).sum())))
    q46 = df["Q46"].fillna("").astype(str).str.strip()
    flow_rows.append(("Non-empty Q46 responses", int((q46 != "").sum())))
    pd.DataFrame(flow_rows, columns=["Metric", "Value"]).to_csv(
        root / "results" / "tables" / "stage2_sample_flow.csv",
        index=False,
    )

    q43 = df["Q43 Perc-Class"].fillna("").astype(str).str.strip()
    q43 = q43[q43 != ""]
    q43_map = {"Yes": "Agree", "No": "Disagree", "Not sure": "Uncertain"}
    q43_out = q43.map(lambda x: q43_map.get(x, x)).value_counts().rename_axis("Response").reset_index(name="Count")
    q43_out["Percent"] = (q43_out["Count"] / q43_out["Count"].sum() * 100).round(1)
    q43_out.to_csv(root / "results" / "tables" / "q43_agreement.csv", index=False)

    tech_map = {
        1: "False Cord, low",
        2: "False Cord, mid",
        3: "Fry, low",
        4: "Fry, mid",
        5: "Fry, high",
        6: "Hardcore Scream",
        7: "Guttural",
        8: "Pig squeal",
        9: "Snarl",
        10: "Zombie scream",
        11: "Banshee scream",
        12: "Goblin scream",
    }
    classes = ["Scream-like", "Growl-like", "Hybrid/Yell-like"]
    has_q44 = q44.apply(lambda r: any(x.strip() != "" for x in r), axis=1)
    rows = []
    for i in range(1, 13):
        col = f"Q44_{i}"
        vals = df.loc[has_q44, col].fillna("").astype(str)
        for cl in classes:
            rows.append((tech_map[i], cl, int(vals.str.contains(cl, regex=False).sum())))
    pd.DataFrame(rows, columns=["Technique", "Class", "Count"]).to_csv(
        root / "results" / "tables" / "q44_mapping_counts.csv",
        index=False,
    )

    q46_map = {"Yes, always": "Regularly", "Yes, sometimes": "Sometimes", "Never": "Rarely/Never"}
    q46_out = q46[q46 != ""].map(lambda x: q46_map.get(x, x)).value_counts().rename_axis("Frequency").reset_index(name="Count")
    q46_out["Percent"] = (q46_out["Count"] / q46_out["Count"].sum() * 100).round(1)
    q46_out.to_csv(root / "results" / "tables" / "q46_class_usage.csv", index=False)

    open_map = {
        "Musical Taste & Influence": ["Q9\xa0Metal Subgenres A", "Q10A Non-metal subge", "Q39 Influence"],
        "Musical Background": ["Q13 Instruments A", "Q15 Composing A", "Q19", "Q20A Band A", "Q22A Past Bands A", "Q22B", "Q22C", "Q25A Studio A"],
        "Vocal Technique & Style": ["Q34_6_TEXT", "Q38 Vox-Style", "Q40 Use Techniques_10_TEXT", "Q41 Other Techniques", "Q42 Approach"],
        "Vocal Health": ["Q35 Health routine_2_TEXT", "Q36 Health Routine A", "Q37A"],
        "Perception & Intelligibility": ["Q43A", "Q45_1", "Q45_2", "Q45_3", "Q46"],
        "Historical Perspective": ["Q47", "Q48", "Q49"],
        "Women in Metal": ["Q53", "Q54", "Q55", "Q56"],
        "Other Reflection": ["Q50", "Q51", "Q52", "Q57", "Q58", "Q59", "Q60"],
    }
    cov_rows = []
    for theme, cols in open_map.items():
        cols = [c for c in cols if c in df.columns]
        sub = df[cols].fillna("").astype(str)
        cov_rows.append((theme, int(sub.apply(lambda r: any(x.strip() != "" for x in r), axis=1).sum())))
    pd.DataFrame(cov_rows, columns=["ThemeBlock", "RespondentsWithAnyText"]).sort_values(
        "RespondentsWithAnyText", ascending=False
    ).to_csv(root / "results" / "tables" / "stage2_open_text_theme_coverage.csv", index=False)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_stage1_tables(root)
    build_stage2_tables(root)
    print("Manuscript tables refreshed.")

if __name__ == "__main__":
    main()