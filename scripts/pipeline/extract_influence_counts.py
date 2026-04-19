from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pandas as pd


def _split_names(inner: str) -> list[str]:
    inner = inner.strip()
    if not inner:
        return []
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    for ch in inner:
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch in ",;" and depth == 0:
            chunk = "".join(buf).strip()
            if chunk:
                parts.append(chunk)
            buf = []
        else:
            buf.append(ch)
    chunk = "".join(buf).strip()
    if chunk:
        parts.append(chunk)
    if not parts:
        return [inner]
    return parts


def _normalize(name: str) -> str:
    name = name.strip()
    name = re.sub(r"\s+", " ", name)
    if len(name) > 120:
        name = name[:117] + "..."
    return name


def _balanced_inners(text: str, label: str) -> list[str]:
    out: list[str] = []
    key = label + "("
    i = 0
    while True:
        start = text.find(key, i)
        if start < 0:
            break
        j = start + len(key)
        depth = 1
        buf: list[str] = []
        while j < len(text) and depth:
            c = text[j]
            if c == "(":
                depth += 1
                buf.append(c)
            elif c == ")":
                depth -= 1
                if depth:
                    buf.append(c)
            else:
                buf.append(c)
            j += 1
        out.append("".join(buf))
        i = j
    return out


def extract_from_codes(codes: str) -> tuple[list[str], list[str]]:
    bands: list[str] = []
    vocalists: list[str] = []
    if not isinstance(codes, str) or not codes.strip():
        return bands, vocalists
    for inner in _balanced_inners(codes, "BAND_INFLUENCE"):
        for p in _split_names(inner):
            bands.append(_normalize(p))
    for inner in _balanced_inners(codes, "VOCALIST_INFLUENCE"):
        for p in _split_names(inner):
            vocalists.append(_normalize(p))
    return bands, vocalists


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    df = pd.read_csv(root / "data" / "processed" / "stage1_segments_18.csv")
    all_b: list[str] = []
    all_v: list[str] = []
    for codes in df["Codes"].astype(str):
        b, v = extract_from_codes(codes)
        all_b.extend(b)
        all_v.extend(v)

    def norm_key(s: str) -> str:
        return re.sub(r"\s+", " ", s.strip().lower())

    def merge_counts(raw: list[str]) -> Counter[str]:
        m: dict[str, str] = {}
        c = Counter()
        for x in raw:
            if not x:
                continue
            k = norm_key(x)
            if k not in m:
                m[k] = x
            c[m[k]] += 1
        return c

    top_b = merge_counts(all_b).most_common(15)
    top_v = merge_counts(all_v).most_common(15)

    out = root / "results" / "tables"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(top_b, columns=["Name", "Count"]).to_csv(out / "top15_bands.csv", index=False)
    pd.DataFrame(top_v, columns=["Name", "Count"]).to_csv(out / "top15_vocalists.csv", index=False)
    print("Wrote top15_bands.csv and top15_vocalists.csv")


if __name__ == "__main__":
    main()
