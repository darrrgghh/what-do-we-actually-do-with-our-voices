from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    fig_dir = root / "manuscript" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    sns.set_theme(style="whitegrid", context="paper", font_scale=1.05)

    theme_path = root / "results" / "tables" / "stage1_theme_summary.csv"
    if not theme_path.exists():
        s1 = pd.read_csv(root / "data" / "processed" / "stage1_segments_18.csv")
        theme_summary = (
            s1.groupby("Theme", as_index=False)
            .size()
            .rename(columns={"size": "SegmentCount"})
            .sort_values("SegmentCount", ascending=False)
        )
        theme_summary.to_csv(theme_path, index=False)
    else:
        theme_summary = pd.read_csv(theme_path)

    plt.figure(figsize=(8, 5))
    order = theme_summary.sort_values("SegmentCount", ascending=True)
    y = order["Theme"].astype(str)
    x = order["SegmentCount"].astype(float)
    plt.barh(range(len(y)), x[::-1], color="#2c3e50")
    plt.yticks(range(len(y)), y[::-1])
    plt.xlabel("Segment count (Stage 1)")
    plt.tight_layout()
    plt.savefig(fig_dir / "stage1_themes_bar.png", dpi=300, bbox_inches="tight")
    plt.close()

    q44 = pd.read_csv(root / "results" / "tables" / "q44_mapping_counts.csv")
    pivot = q44.pivot(index="Technique", columns="Class", values="Count").fillna(0)
    for c in ["Scream-like", "Growl-like", "Hybrid/Yell-like"]:
        if c not in pivot.columns:
            pivot[c] = 0.0
    pivot = pivot[["Scream-like", "Growl-like", "Hybrid/Yell-like"]]
    plt.figure(figsize=(7, 8))
    ax = sns.heatmap(
        pivot,
        annot=True,
        fmt=".0f",
        cmap="YlOrRd",
        cbar_kws={"label": "Participants (multi-select allowed)"},
        linewidths=0.5,
    )
    ax.set_xlabel("Perceptual class (Q44)")
    ax.set_ylabel("Production technique label")
    plt.tight_layout()
    plt.savefig(fig_dir / "q44_heatmap.png", dpi=300, bbox_inches="tight")
    plt.close()

    print("Wrote stage1_themes_bar.png and q44_heatmap.png")


if __name__ == "__main__":
    main()
