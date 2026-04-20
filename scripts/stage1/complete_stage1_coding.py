from __future__ import annotations
import json
import re
from pathlib import Path
import pandas as pd

def load_paths(project_root: Path) -> dict:
    cfg_path = project_root / "config" / "project_paths.json"
    with cfg_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_quotes(text: str) -> str:
    return (
        text.replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\ufeff", "")
        .strip()
    )


def parse_metadata(lines: list[str], vocalist_id: str) -> dict:
    defaults = {
        "Vocalist": vocalist_id,
        "Gender": "Unknown",
        "Age": pd.NA,
        "InterviewDate": pd.NA,
        "Experience_months": pd.NA,
    }
    for ln in lines[:6]:
        clean = normalize_quotes(ln)
        if not clean:
            continue
        if re.match(rf"^{vocalist_id}\s+", clean):
            parts = re.split(r"\s+", clean)
            if len(parts) >= 5:
                defaults["Gender"] = parts[1]
                defaults["Age"] = pd.to_numeric(parts[2], errors="coerce")
                defaults["InterviewDate"] = parts[3]
                defaults["Experience_months"] = pd.to_numeric(parts[4], errors="coerce")
                return defaults
        age_match = re.search(r"(\d+)\s*y\.?o", clean, flags=re.IGNORECASE)
        if age_match:
            defaults["Age"] = pd.to_numeric(age_match.group(1), errors="coerce")
        if "male" in clean.lower():
            defaults["Gender"] = "Male"
        if "female" in clean.lower():
            defaults["Gender"] = "Female"
    return defaults


THEME_MAP = {
    "musical taste": "Musical Taste & Influence",
    "musical background": "Musical Background",
    "band experience": "Musical Background",
    "vocal training & technique": "Education",
    "vocal style & techniques": "Vocal Technique & Style",
    "vocal style & influences": "Vocal Technique & Style",
    "vocal techniques": "Vocal Technique & Style",
    "perception, technique, intelligibility": "Perception & Intelligibility",
    "perception and intelligibility": "Perception & Intelligibility",
    "melody and rhythm": "Melody & Rhythm",
    "historical perspective": "Historical Perspective",
    "women in metal": "Women in Metal",
    "other": "Other",
}


def map_theme(header: str) -> str | None:
    key = normalize_quotes(header).lower().strip(": ")
    return THEME_MAP.get(key)


KEYWORD_CODE_RULES = [
    (re.compile(r"\bmetalcore|deathcore|death metal|prog|genre|band\b", re.I), "GENRE_PREFERENCE"),
    (re.compile(r"\binfluence|inspired|favorite\b", re.I), "BAND_INFLUENCE"),
    (re.compile(r"\bnon-metal|ambient|indie|pop|jazz|blues\b", re.I), "NON_METAL_TASTE"),
    (re.compile(r"\bguitar|drum|bass|keyboard|instrument\b", re.I), "INSTRUMENTAL_SKILL"),
    (re.compile(r"\bcompose|songwrit|daw|reaper|logic|record\b", re.I), "COMPOSITION_PROCESS"),
    (re.compile(r"\bband|perform|show|live|studio\b", re.I), "LIVE_PERFORMANCE"),
    (re.compile(r"\byoutube|reddit|self-taught|lesson|learn\b", re.I), "ONLINE_LEARNING"),
    (re.compile(r"\bfalse cord|false chord\b", re.I), "FALSE_CORD"),
    (re.compile(r"\bfry\b", re.I), "FRY_TECHNIQUE"),
    (re.compile(r"\bgrowl|guttural\b", re.I), "GROWL_TECHNIQUE"),
    (re.compile(r"\bscream|screaming\b", re.I), "SCREAMING_TECHNIQUE"),
    (re.compile(r"\bwarm|rest|water|honey|healthy|strain|injury\b", re.I), "VOCAL_HEALTH"),
    (re.compile(r"\bintelligib|understand|lyrics|message\b", re.I), "INTELLIGIBILITY_IMPORTANT"),
    (re.compile(r"\bmelody|rhythm|timing|pitch\b", re.I), "MELODY_IMPORTANT"),
    (re.compile(r"\bearly|origin|first time|history\b", re.I), "EARLY_EXAMPLES_SCREAM"),
]


THEME_DEFAULT_PRIMARY = {
    "Musical Taste & Influence": "GENRE_PREFERENCE",
    "Musical Background": "INSTRUMENTAL_SKILL",
    "Education": "ONLINE_LEARNING",
    "Vocal Technique & Style": "SCREAMING_TECHNIQUE",
    "Vocal Health": "VOCAL_HEALTH",
    "Perception & Intelligibility": "INTELLIGIBILITY_IMPORTANT",
    "Melody & Rhythm": "MELODY_IMPORTANT",
    "Historical Perspective": "EARLY_EXAMPLES_SCREAM",
    "Women in Metal": "GENDER_UNDERRREPRESENTATION",
    "Other": "MUSIC_AS_EXPRESSION",
}


def detect_codes(text: str, theme: str) -> list[str]:
    codes: list[str] = []
    for pattern, code in KEYWORD_CODE_RULES:
        if pattern.search(text):
            codes.append(code)
    if not codes:
        fallback = THEME_DEFAULT_PRIMARY.get(theme, "MUSIC_AS_EXPRESSION")
        codes = [fallback]
    return list(dict.fromkeys(codes))


def extract_segments_from_qa(qa_path: Path, vocalist_id: str) -> pd.DataFrame:
    lines = qa_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    metadata = parse_metadata(lines, vocalist_id)
    rows = []
    theme = None
    for ln in lines:
        clean = normalize_quotes(ln)
        if not clean:
            continue
        mapped = map_theme(clean)
        if mapped:
            theme = mapped
            continue
        if clean.endswith("?") or clean.lower().startswith(("how ", "do ", "what ", "why ", "are ")):
            continue
        if theme is None:
            continue
        if len(clean) < 50:
            continue

        codes = detect_codes(clean, theme)
        primary = codes[0]
        rows.append(
            {
                **metadata,
                "Theme": theme,
                "Quote": clean,
                "Codes": "; ".join(codes),
                "PrimaryCode": primary,
                "CodingSource": "assisted_stage1_completion",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    paths = load_paths(project_root)
    segments_in = project_root / paths["stage1_segments_input"]
    codebook_in = project_root / paths["stage1_codebook_input"]
    qa_dir = project_root / paths["stage1_qa_folder"]
    processed_dir = project_root / paths["processed_dir"]
    codebook_out = project_root / paths["codebook_output"]
    processed_dir.mkdir(parents=True, exist_ok=True)
    codebook_out.parent.mkdir(parents=True, exist_ok=True)
    base = pd.read_csv(segments_in)
    base["CodingSource"] = "manual_existing"
    present = set(base["Vocalist"].dropna().astype(str).unique())

    needed = [v for v in ["Q", "R"] if v not in present]
    assisted_parts = []
    for v in needed:
        match = next(qa_dir.glob(f"{v}*.txt"), None)
        if match is None:
            continue
        assisted = extract_segments_from_qa(match, v)
        if not assisted.empty:
            assisted_parts.append(assisted)

    if assisted_parts:
        base = pd.concat([base, *assisted_parts], ignore_index=True)

    # Harmonize types.
    base["Age"] = pd.to_numeric(base["Age"], errors="coerce")
    base["Experience_months"] = pd.to_numeric(base["Experience_months"], errors="coerce")

    out_segments = processed_dir / "stage1_segments_18.csv"
    base.to_csv(out_segments, index=False, encoding="utf-8")

    codebook = pd.read_csv(codebook_in)
    stage2_extensions = pd.DataFrame(
        [
            {
                "Theme": "Qualtrics Extended Topics",
                "Code": "SURVEY_CONTEXT_NOTE",
                "Definition": "Meta-note for broader Qualtrics themes not present in stage-1 interview prompts.",
                "Examples": "Used to track stage-2-specific context in coding exports.",
            }
        ]
    )
    codebook_v2 = pd.concat([codebook, stage2_extensions], ignore_index=True)
    codebook_v2.to_csv(codebook_out, index=False, encoding="utf-8")

    summary = pd.DataFrame(
        [
            {"metric": "stage1_rows_total", "value": len(base)},
            {"metric": "stage1_unique_vocalists", "value": base["Vocalist"].nunique()},
            {"metric": "stage1_assisted_rows", "value": int((base["CodingSource"] == "assisted_stage1_completion").sum())},
        ]
    )
    summary.to_csv(processed_dir / "stage1_completion_summary.csv", index=False)

    print(f"Wrote: {out_segments}")
    print(f"Wrote: {codebook_out}")
    print("Unique vocalists:", sorted(base["Vocalist"].dropna().unique().tolist()))


if __name__ == "__main__":
    main()