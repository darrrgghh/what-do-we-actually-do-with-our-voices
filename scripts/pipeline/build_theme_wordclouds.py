from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from wordcloud import STOPWORDS, WordCloud


EXTRA_STOP = {
    "like",
    "just",
    "really",
    "thing",
    "things",
    "something",
    "kind",
    "lot",
    "gonna",
    "wanna",
    "yeah",
    "well",
    "also",
    "maybe",
    "pretty",
    "much",
    "ve",
    "ll",
    "don",
    "didn",
    "doesn",
    "isn",
    "wasn",
    "weren",
}


def _text_blob(series: pd.Series) -> str:
    parts = []
    for x in series.astype(str):
        x = re.sub(r"[^\w\s\-']", " ", x)
        parts.append(x)
    return " ".join(parts)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    fig_dir = root / "manuscript" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(root / "data" / "processed" / "stage1_segments_18.csv")
    stop = set(STOPWORDS) | EXTRA_STOP

    def make_cloud(text: str, out_name: str) -> None:
        if len(text.strip()) < 80:
            return
        wc = WordCloud(
            width=1200,
            height=700,
            background_color="white",
            stopwords=stop,
            colormap="viridis",
            max_words=120,
        ).generate(text)
        plt.figure(figsize=(12, 7))
        plt.imshow(wc, interpolation="bilinear")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(fig_dir / out_name, dpi=200, bbox_inches="tight")
        plt.close()

    make_cloud(_text_blob(df["Quote"]), "wordcloud_stage1_all.png")

    large_themes = df.groupby("Theme").size().sort_values(ascending=False)
    theme_paths: list[Path] = []
    for theme, n in large_themes.items():
        if n < 40:
            continue
        safe = re.sub(r"[^a-zA-Z0-9]+", "_", str(theme)).strip("_").lower()[:60]
        sub = df[df["Theme"] == theme]
        fname = f"wordcloud_theme_{safe}.png"
        make_cloud(_text_blob(sub["Quote"]), fname)
        theme_paths.append(fig_dir / fname)

    if len(theme_paths) >= 6:
        paths = theme_paths[:6]
        fig, axes = plt.subplots(2, 3, figsize=(14, 9))
        for ax, p in zip(axes.flat, paths):
            im = plt.imread(p)
            ax.imshow(im)
            ax.axis("off")
            ax.set_title(
                p.stem.replace("wordcloud_theme_", "").replace("_", " ")[:44],
                fontsize=8,
            )
        plt.tight_layout()
        plt.savefig(fig_dir / "wordcloud_themes_montage.png", dpi=180, bbox_inches="tight")
        plt.close()

    print("Wrote wordcloud PNGs under manuscript/figures/")


if __name__ == "__main__":
    main()
