from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


IDENTIFIER_COLUMNS = {
    "StartDate",
    "EndDate",
    "Status",
    "IPAddress",
    "ResponseId",
    "RecipientLastName",
    "RecipientFirstName",
    "RecipientEmail",
    "ExternalReference",
    "LocationLatitude",
    "LocationLongitude",
    "DistributionChannel",
    "UserLanguage",
}

# Map extracted Qualtrics Q-key (see extract_q_key) to Stage-1-aligned theme labels.
THEME_BY_Q_KEY: dict[str, str] = {
    # Screening / demographics (do not mix with substantive interview themes in comparisons)
    "Q1": "Demographics",
    "Q2": "Demographics",
    "Q3": "Demographics",
    "Q4": "Demographics",
    "Q5": "Demographics",
    "Q6": "Demographics",
    "Q7": "Demographics",
    # Musical taste / influence
    "Q8": "Musical Taste & Influence",
    "Q9": "Musical Taste & Influence",
    "Q10": "Musical Taste & Influence",
    "Q10_9": "Musical Taste & Influence",
    "Q10A": "Musical Taste & Influence",
    "Q39": "Musical Taste & Influence",
    # Background / scene / instruments / bands
    "Q11": "Musical Background",
    "Q12": "Musical Background",
    "Q13": "Musical Background",
    "Q14": "Musical Background",
    "Q15": "Musical Background",
    "Q19": "Musical Background",
    "Q20": "Musical Background",
    "Q20A": "Musical Background",
    "Q20B": "Musical Background",
    "Q20C": "Musical Background",
    "Q22": "Musical Background",
    "Q22A": "Musical Background",
    "Q22B": "Musical Background",
    "Q22C": "Musical Background",
    "Q23": "Musical Background",
    "Q25": "Musical Background",
    "Q25A": "Musical Background",
    "Q32": "Musical Background",
    # Education / training (aligned with Stage 1 Education theme)
    "Q16": "Education",
    "Q33": "Education",
    # Technique / style
    "Q34": "Vocal Technique & Style",
    "Q34_6": "Vocal Technique & Style",
    "Q34A": "Vocal Technique & Style",
    "Q34B": "Vocal Technique & Style",
    "Q34C": "Vocal Technique & Style",
    "Q38": "Vocal Technique & Style",
    "Q40": "Vocal Technique & Style",
    "Q41": "Vocal Technique & Style",
    "Q42": "Vocal Technique & Style",
    # Health
    "Q35": "Vocal Health",
    "Q36": "Vocal Health",
    "Q37": "Vocal Health",
    "Q37A": "Vocal Health",
    # Perception / class block
    "Q43": "Perception & Intelligibility",
    "Q43A": "Perception & Intelligibility",
    "Q44_1": "Perception & Intelligibility",
    "Q44_2": "Perception & Intelligibility",
    "Q44_3": "Perception & Intelligibility",
    "Q44_4": "Perception & Intelligibility",
    "Q44_5": "Perception & Intelligibility",
    "Q44_6": "Perception & Intelligibility",
    "Q44_7": "Perception & Intelligibility",
    "Q44_8": "Perception & Intelligibility",
    "Q44_9": "Perception & Intelligibility",
    "Q44_10": "Perception & Intelligibility",
    "Q44_11": "Perception & Intelligibility",
    "Q44_12": "Perception & Intelligibility",
    "Q45_1": "Perception & Intelligibility",
    "Q45_2": "Perception & Intelligibility",
    "Q45_3": "Perception & Intelligibility",
    "Q46": "Perception & Intelligibility",
    # History
    "Q47": "Historical Perspective",
    "Q48": "Historical Perspective",
    "Q49": "Historical Perspective",
    # Women in metal block
    "Q53": "Women in Metal",
    "Q54": "Women in Metal",
    "Q55": "Women in Metal",
    "Q56": "Women in Metal",
    # Open reflection / misc
    "Q50": "Other",
    "Q51": "Other",
    "Q52": "Other",
    "Q57": "Other",
    "Q58": "Other",
    "Q59": "Other",
    "Q60": "Other",
}


def extract_q_key(col: str) -> str:
    """Normalize Qualtrics column name to a stable Q-key (Q8, Q10A, Q44_1, …)."""
    col = col.replace("\xa0", " ").strip()
    m = re.match(r"^(Q\d+_\d+)", col)
    if m:
        return m.group(1)
    m = re.match(r"^(Q\d+[A-Z]?)(?=[\s_]|$)", col)
    if m:
        return m.group(1)
    m = re.match(r"^(Q\d+)", col)
    if m:
        return m.group(1)
    return col


def theme_for_column(col: str) -> str:
    qk = extract_q_key(col)
    return THEME_BY_Q_KEY.get(qk, "Other")


def load_paths(project_root: Path) -> dict:
    with (project_root / "config" / "project_paths.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize(text: str) -> str:
    return (
        str(text)
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\ufeff", "")
        .strip()
    )


def assign_codes(text: str, theme: str) -> tuple[str, str]:
    t = text.lower()
    rules = [
        ("false cord|false chord", "FALSE_CORD"),
        ("fry", "FRY_TECHNIQUE"),
        ("growl|guttural", "GROWL_TECHNIQUE"),
        ("scream|shout", "SCREAMING_TECHNIQUE"),
        ("warm|rest|hydr|pain|injur|strain", "VOCAL_HEALTH"),
        ("lyrics|understand|message|intelligib", "INTELLIGIBILITY_IMPORTANT"),
        ("rhythm|timing|melody|pitch", "MELODY_IMPORTANT"),
        ("influence|favorite|band|genre", "BAND_INFLUENCE"),
        ("woman|female|gender|misog", "GENDER_UNDERRREPRESENTATION"),
    ]
    found = [code for pattern, code in rules if re.search(pattern, t)]
    if not found:
        fallback = {
            "Perception & Intelligibility": "EXTREME_VOCALS_DEFINITION",
            "Women in Metal": "GENDER_UNDERRREPRESENTATION",
            "Vocal Health": "VOCAL_HEALTH",
            "Vocal Technique & Style": "SCREAMING_TECHNIQUE",
            "Education": "ONLINE_LEARNING",
            "Demographics": "SURVEY_CONTEXT_NOTE",
        }.get(theme, "MUSIC_AS_EXPRESSION")
        found = [fallback]
    primary = found[0]
    return "; ".join(dict.fromkeys(found)), primary


def split_text_units(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+|\n+", normalize(text))
    out = [c.strip() for c in chunks if len(c.strip()) >= 25]
    return out[:6]


def normalize_perceptual_class_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Map legacy survey strings to current manuscript terminology (perceptual class labels)."""
    out = df.copy()
    old, new = "Hybrid/Shout-like", "Hybrid/Yell-like"
    for col in out.columns:
        s = out[col]
        if s.dtype == object or pd.api.types.is_string_dtype(s):
            out[col] = s.map(lambda x: x.replace(old, new) if isinstance(x, str) else x)
    return out


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    paths = load_paths(project_root)
    processed_dir = project_root / paths["processed_dir"]
    processed_dir.mkdir(parents=True, exist_ok=True)

    qualtrics_path = project_root / paths["qualtrics_input"]
    df = pd.read_csv(qualtrics_path, header=0, skiprows=[1, 2], encoding="utf-8")
    df.columns = [normalize(c) for c in df.columns]

    keep_cols = [c for c in df.columns if c not in IDENTIFIER_COLUMNS]
    deid = df[keep_cols].copy()
    deid.insert(0, "RespondentID", [f"QX_{i:03d}" for i in range(1, len(deid) + 1)])
    deid = normalize_perceptual_class_labels(deid)
    deid.to_csv(processed_dir / "qualtrics_deidentified.csv", index=False, encoding="utf-8")

    text_records = []
    for _, row in deid.iterrows():
        rid = row["RespondentID"]
        for col in deid.columns:
            if not col.startswith("Q"):
                continue
            val = row[col]
            if pd.isna(val):
                continue
            val_norm = normalize(val)
            if not val_norm or val_norm.lower() == "nan":
                continue
            if len(val_norm) < 20:
                continue

            theme = theme_for_column(col)
            for seg in split_text_units(val_norm):
                codes, primary = assign_codes(seg, theme)
                text_records.append(
                    {
                        "RespondentID": rid,
                        "QuestionCode": col,
                        "QKey": extract_q_key(col),
                        "Theme": theme,
                        "Quote": seg,
                        "Codes": codes,
                        "PrimaryCode": primary,
                    }
                )

    segments = pd.DataFrame(text_records).drop_duplicates()
    segments.to_csv(processed_dir / "stage2_text_segments.csv", index=False, encoding="utf-8")

    overview = pd.DataFrame(
        [
            {"metric": "qualtrics_rows_total", "value": len(df)},
            {"metric": "qualtrics_rows_finished", "value": int(pd.to_numeric(df.get("Finished"), errors="coerce").eq(1).sum())},
            {"metric": "qualtrics_deidentified_rows", "value": len(deid)},
            {"metric": "stage2_text_segments", "value": len(segments)},
            {"metric": "stage2_respondents_with_text", "value": int(segments["RespondentID"].nunique() if not segments.empty else 0)},
        ]
    )
    overview.to_csv(processed_dir / "stage2_summary.csv", index=False)

    print("Wrote de-identified Qualtrics and coded text segments.")


if __name__ == "__main__":
    main()
