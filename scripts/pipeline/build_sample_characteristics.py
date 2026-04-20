from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

def _numeric_age(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.replace(r"[^\d.]", "", regex=True), errors="coerce")

def summarize_stage1(root: Path) -> None:
    seg = pd.read_csv(root / "data" / "processed" / "stage1_segments_18.csv")
    p = seg.drop_duplicates(subset=["Vocalist"]).copy()
    p.to_csv(root / "results" / "tables" / "stage1_participant_level.csv", index=False)
    age = pd.to_numeric(p["Age"], errors="coerce")
    exp = pd.to_numeric(p["Experience_months"], errors="coerce")

    rows = [
        ("N_participants", len(p)),
        ("Age_median", float(np.nanmedian(age)) if age.notna().any() else np.nan),
        ("Age_q25", float(np.nanquantile(age, 0.25)) if age.notna().any() else np.nan),
        ("Age_q75", float(np.nanquantile(age, 0.75)) if age.notna().any() else np.nan),
        ("Age_min", float(np.nanmin(age)) if age.notna().any() else np.nan),
        ("Age_max", float(np.nanmax(age)) if age.notna().any() else np.nan),
        ("Experience_months_median", float(np.nanmedian(exp)) if exp.notna().any() else np.nan),
        ("Experience_months_q25", float(np.nanquantile(exp, 0.25)) if exp.notna().any() else np.nan),
        ("Experience_months_q75", float(np.nanquantile(exp, 0.75)) if exp.notna().any() else np.nan),
    ]
    summary = pd.DataFrame(rows, columns=["Metric", "Value"])
    summary.to_csv(root / "results" / "tables" / "stage1_demographics_summary.csv", index=False)
    gcounts = p["Gender"].fillna("Unknown").value_counts().rename_axis("Gender").reset_index(name="Count")
    gcounts.to_csv(root / "results" / "tables" / "stage1_gender_counts.csv", index=False)

def _stage2_slice(df: pd.DataFrame, finished_only: bool) -> pd.DataFrame:
    if finished_only and "Finished" in df.columns:
        fin = pd.to_numeric(df["Finished"], errors="coerce").eq(1)
        return df.loc[fin].copy()
    return df.copy()

def summarize_stage2(root: Path) -> None:
    q = pd.read_csv(root / "data" / "processed" / "qualtrics_deidentified.csv")
    out_rows: list[dict] = []
    for label, finished_only in [("all_rows", False), ("finished_only", True)]:
        sub = _stage2_slice(q, finished_only)
        age = _numeric_age(sub.get("Q1 Age", pd.Series(dtype=float)))
        n = len(sub)
        def add(metric: str, value: float | int | str) -> None:
            out_rows.append({"Slice": label, "Metric": metric, "Value": value})

        add("N_rows", n)
        add("Age_median", float(np.nanmedian(age)) if age.notna().any() else np.nan)
        add("Age_q25", float(np.nanquantile(age, 0.25)) if age.notna().any() else np.nan)
        add("Age_q75", float(np.nanquantile(age, 0.75)) if age.notna().any() else np.nan)
        add("Age_nonmissing_n", int(age.notna().sum()))

        if "Q2 Gender" in sub.columns:
            g = sub["Q2 Gender"].fillna("").astype(str).str.strip()
            for k, v in g[g != ""].value_counts().items():
                out_rows.append({"Slice": label, "Metric": f"Gender_{k}", "Value": int(v)})

        for col, prefix in [
            ("Q3 Native language", "NativeLanguage"),
            ("Q4 Location", "Location"),
        ]:
            if col not in sub.columns:
                continue
            s = sub[col].fillna("").astype(str).str.strip()
            nonempty = int((s != "").sum())
            add(f"{prefix}_nonempty_n", nonempty)

        for col, prefix in [("Q6", "Q6_entry_nonempty"), ("Q7", "Q7_nonempty")]:
            if col not in sub.columns:
                continue
            s = sub[col].fillna("").astype(str).str.strip()
            add(prefix, int((s != "").sum()))

        if "Q11 Musicianship_1" in sub.columns:
            m = sub["Q11 Musicianship_1"].fillna("").astype(str).str.strip()
            for k, v in m[m != ""].value_counts().items():
                out_rows.append({"Slice": label, "Metric": f"Musicianship_{k}", "Value": int(v)})

    pd.DataFrame(out_rows).to_csv(root / "results" / "tables" / "stage2_demographics_summary.csv", index=False)

    # Side-by-side age comparison Stage1 vs Stage2 finished
    s1 = pd.read_csv(root / "data" / "processed" / "stage1_segments_18.csv")
    p1 = s1.drop_duplicates(subset=["Vocalist"])
    age1 = pd.to_numeric(p1["Age"], errors="coerce")
    qf = _stage2_slice(q, True)
    age2 = _numeric_age(qf.get("Q1 Age", pd.Series(dtype=float)))

    cmp_rows = [
        {
            "Group": "Stage1_interviews",
            "N": len(p1),
            "Age_median": float(np.nanmedian(age1)) if age1.notna().any() else np.nan,
            "Age_q25": float(np.nanquantile(age1, 0.25)) if age1.notna().any() else np.nan,
            "Age_q75": float(np.nanquantile(age1, 0.75)) if age1.notna().any() else np.nan,
        },
        {
            "Group": "Stage2_Qualtrics_finished",
            "N": len(qf),
            "Age_median": float(np.nanmedian(age2)) if age2.notna().any() else np.nan,
            "Age_q25": float(np.nanquantile(age2, 0.25)) if age2.notna().any() else np.nan,
            "Age_q75": float(np.nanquantile(age2, 0.75)) if age2.notna().any() else np.nan,
        },
    ]
    pd.DataFrame(cmp_rows).to_csv(root / "results" / "tables" / "stage1_vs_stage2_age_compare.csv", index=False)

def main() -> None:
    root = Path(__file__).resolve().parents[2]
    (root / "results" / "tables").mkdir(parents=True, exist_ok=True)
    summarize_stage1(root)
    summarize_stage2(root)
    print("Wrote sample characteristic tables under results/tables/")

if __name__ == "__main__":
    main()