from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from wordcloud import STOPWORDS, WordCloud


# --- Manual extras (beyond wordcloud.STOPWORDS) --------------------------------
# NOTE: wordcloud.STOPWORDS already covers many function words (a, the, is, was, were, …).

EXTRA_STOP: set[str] = {
    # Tokenizer / contraction debris (incl. possessive splits)
    "s",
    "d",
    "t",
    "m",
    "re",
    "ve",
    "ll",
    "nt",
    "em",
    "im",
    "ive",
    "youre",
    "theyre",
    "dont",
    "didn",
    "doesn",
    "isn",
    "wasn",
    "weren",
    "wouldn",
    "couldn",
    "shouldn",
    "haven",
    "hasn",
    "hadn",
    "ain",
    "youd",
    "youdve",
    "youll",
    "youve",
    "theyll",
    "theyve",
    "weve",
    "thats",
    "heres",
    "theres",
    "wheres",
    "whats",
    "whos",
    "hows",
    "lets",
    "cmon",
    "gonna",
    "wanna",
    "gotta",
    "kinda",
    "sorta",
    "hafta",
    "oughta",
    "dunno",
    "yeah",
    "yep",
    "nope",
    "uh",
    "um",
    "hmm",
    "ok",
    "okay",
    # Discourse fillers
    "like",
    "just",
    "well",
    "thing",
    "things",
    "stuff",
    "bit",
    "bits",
    "lot",
    "lots",
    "sort",
    "sorts",
    "kind",
    "couple",
    "whatever",
    "whichever",
    "however",
    "somewhere",
    "anywhere",
    "everywhere",
    "nowhere",
    "somehow",
    "anyhow",
    "anyway",
    "anyways",
    "else",
    "elsewhere",
    # Connectors (often noise in clouds)
    "therefore",
    "thus",
    "hence",
    "nevertheless",
    "nonetheless",
    "meanwhile",
    "afterwards",
    "afterward",
    "beforehand",
    "likewise",
    "otherwise",
    # Indefinites / pronouns (high frequency in interviews)
    "anything",
    "everything",
    "nothing",
    "something",
    "someone",
    "anyone",
    "everyone",
    "anybody",
    "everybody",
    "nobody",
    "somebody",
    "somewhat",
    "anytime",
    "sometime",
    "sometimes",
    "i",
    "id",
    "ill",
    "me",
    "myself",
    "we",
    "us",
    "our",
    "ourselves",
    "you",
    "your",
    "yourself",
    "yourselves",
    "he",
    "him",
    "himself",
    "she",
    "her",
    "herself",
    "they",
    "them",
    "themselves",
    "it",
    "itself",
    # Intensifiers / non-ly adverbs
    "very",
    "quite",
    "rather",
    "too",
    "also",
    "almost",
    "nearly",
    "even",
    "still",
    "yet",
    "already",
    "ever",
    "never",
    "always",
    "often",
    "seldom",
    "usually",
    "maybe",
    "perhaps",
    "probably",
    "certainly",
    "definitely",
    "absolutely",
    "totally",
    "pretty",
    "much",
    "more",
    "most",
    "less",
    "least",
    "either",
    "neither",
    "instead",
    "especially",
    "particularly",
    "generally",
    "basically",
    "literally",
    "actually",
    "honestly",
    "frankly",
    "hopefully",
    "supposedly",
    "accordingly",
    # Meta / motion / interview scaffolding verbs (not production vocabulary)
    "going",
    "gon",
    "go",
    "goes",
    "gone",
    "went",
    "get",
    "gets",
    "got",
    "getting",
    "gotten",
    "come",
    "comes",
    "came",
    "coming",
    "make",
    "makes",
    "made",
    "making",
    "take",
    "takes",
    "took",
    "taking",
    "want",
    "wants",
    "wanted",
    "wanting",
    "need",
    "needs",
    "needed",
    "needing",
    "think",
    "thinks",
    "thought",
    "thinking",
    "know",
    "knows",
    "knew",
    "knowing",
    "say",
    "says",
    "said",
    "saying",
    "tell",
    "tells",
    "told",
    "telling",
    "ask",
    "asks",
    "asked",
    "asking",
    "look",
    "looks",
    "looked",
    "looking",
    "seem",
    "seems",
    "seemed",
    "seeming",
    "try",
    "tries",
    "tried",
    "trying",
    "put",
    "puts",
    "putting",
    "mean",
    "means",
    "meant",
    "meaning",
    "let",
    "lets",
    "letting",
    "guess",
    "guesses",
    "guessed",
    "guessing",
    "suppose",
    "supposes",
    "supposed",
    "supposing",
    "figure",
    "figures",
    "figured",
    "figuring",
    "believe",
    "believes",
    "believed",
    "believing",
    "remember",
    "remembers",
    "remembered",
    "remembering",
    "understand",
    "understands",
    "understood",
    "understanding",
    "agree",
    "agrees",
    "agreed",
    "agreeing",
    "happen",
    "happens",
    "happened",
    "happening",
    "talk",
    "talks",
    "talked",
    "talking",
}

# Common -ly adverbs only (explicit list avoids killing words like "family", "Italy").
# Keep thematic adverbs like "vocally" / "musically" visible.
LY_ADVERB_STOPS: frozenset[str] = frozenset(
    {
        "really",
        "actually",
        "literally",
        "basically",
        "probably",
        "possibly",
        "definitely",
        "certainly",
        "surely",
        "absolutely",
        "totally",
        "completely",
        "entirely",
        "fully",
        "partially",
        "especially",
        "particularly",
        "specifically",
        "generally",
        "normally",
        "typically",
        "usually",
        "commonly",
        "frequently",
        "infrequently",
        "rarely",
        "constantly",
        "continuously",
        "repeatedly",
        "occasionally",
        "eventually",
        "finally",
        "initially",
        "originally",
        "previously",
        "currently",
        "recently",
        "formerly",
        "presently",
        "suddenly",
        "immediately",
        "eventually",
        "hopefully",
        "thankfully",
        "fortunately",
        "unfortunately",
        "luckily",
        "unluckily",
        "honestly",
        "frankly",
        "seriously",
        "supposedly",
        "reportedly",
        "allegedly",
        "presumably",
        "ostensibly",
        "evidently",
        "apparently",
        "seemingly",
        "admittedly",
        "undoubtedly",
        "doubtlessly",
        "regrettably",
        "obviously",
        "clearly",
        "plainly",
        "simply",
        "merely",
        "purely",
        "mainly",
        "chiefly",
        "partly",
        "largely",
        "mostly",
        "widely",
        "narrowly",
        "broadly",
        "closely",
        "deeply",
        "highly",
        "strongly",
        "weakly",
        "quickly",
        "slowly",
        "rapidly",
        "gradually",
        "directly",
        "indirectly",
        "easily",
        "hardly",
        "barely",
        "scarcely",
        "roughly",
        "approximately",
        "exactly",
        "precisely",
        "truly",
        "badly",
        "sadly",
        "happily",
        "angrily",
        "oddly",
        "strangely",
        "weirdly",
        "likely",
        "unlikely",
        "personally",
        "physically",
        "mentally",
        "emotionally",
        "socially",
        "politically",
        "economically",
        "technically",
        "theoretically",
        "practically",
        "historically",
        "traditionally",
        "naturally",
        "artificially",
        "automatically",
        "manually",
        "globally",
        "locally",
        "internally",
        "externally",
        "publicly",
        "privately",
        "officially",
        "unofficially",
        "formally",
        "informally",
        "strictly",
        "loosely",
        "tightly",
        "firmly",
        "gently",
        "lightly",
        "heavily",
        "safely",
        "carefully",
        "carelessly",
        "successfully",
        "unsuccessfully",
        "effectively",
        "ineffectively",
        "actively",
        "passively",
        "positively",
        "negatively",
        "relatively",
        "comparatively",
        "similarly",
        "differently",
        "identically",
        "uniquely",
        "regularly",
        "irregularly",
        "abnormally",
        "severely",
        "mildly",
        "wildly",
        "calmly",
        "madly",
        "incredibly",
        "extremely",
        "utterly",
        "thoroughly",
        "wholly",
        "wrongly",
        "rightly",
        "correctly",
        "incorrectly",
        "properly",
        "improperly",
        "squarely",
        "roundly",
        "openly",
        "secretly",
        "secondly",
        "thirdly",
        "fourthly",
        "fifthly",
        "firstly",
        "lastly",
        "additionally",
        "similarly",
        "accordingly",
        "consequently",
        "daily",
        "weekly",
        "monthly",
        "yearly",
        "hourly",
        "nightly",
        "overly",
        "only",
        "early",
        "badly",
        "awfully",
        "terribly",
        "horribly",
        "fairly",
        "namely",
        "chiefly",
        "greatly",
        "newly",
        "reportedly",
        "supposedly",
        "hopefully",
        "thankfully",
        "interestingly",
        "surprisingly",
        "undoubtedly",
        "purportedly",
    }
)

assert all(w.endswith("ly") for w in LY_ADVERB_STOPS), "LY_ADVERB_STOPS must be -ly words only"

TOKEN_RE = re.compile(r"\b[\w']+\b", re.UNICODE)


def _normalize_apostrophes(s: str) -> str:
    return s.replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')


def _strip_possessive_suffix(token: str) -> str:
    t = token.lower()
    if t.endswith("'s"):
        t = t[:-2]
    return t


def _filter_token(t: str, stop: set[str]) -> str | None:
    if not t:
        return None
    raw = t
    t = _strip_possessive_suffix(t.strip("'\""))
    if not t:
        return None
    if t.isdigit():
        return None
    if len(t) == 1:
        return None
    if t in {"s", "d", "t", "m", "re", "ve", "ll"}:
        return None
    if t in stop:
        return None
    if raw[0].isdigit():
        return raw.lower()
    return t


def preprocess_for_wordcloud(text: str, stop: set[str]) -> str:
    """Normalize punctuation, split possessives, drop stopwords, return space-joined tokens."""
    text = _normalize_apostrophes(text)
    text = re.sub(r"[^\w\s']", " ", text)
    out: list[str] = []
    for m in TOKEN_RE.finditer(text):
        tok = m.group(0)
        ft = _filter_token(tok, stop)
        if ft:
            out.append(ft)
    return " ".join(out)


def _text_blob(series: pd.Series, stop: set[str]) -> str:
    parts: list[str] = []
    for x in series.astype(str):
        parts.append(preprocess_for_wordcloud(x, stop))
    return " ".join(parts)


def _wordcloud(
    text: str,
    stop: set[str],
    *,
    width: int,
    height: int,
    max_words: int = 110,
) -> WordCloud:
    """Shared WordCloud settings: larger min/max font sizes improve legibility in print."""
    return WordCloud(
        width=width,
        height=height,
        background_color="white",
        stopwords=stop,
        colormap="viridis",
        max_words=max_words,
        min_font_size=10,
        max_font_size=200,
        relative_scaling=0.45,
        regexp=r"\w[\w']+",
    ).generate(text)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    fig_dir = root / "manuscript" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    stop = set(STOPWORDS) | EXTRA_STOP | set(LY_ADVERB_STOPS)

    for p in fig_dir.glob("wordcloud_*.png"):
        p.unlink(missing_ok=True)

    df = pd.read_csv(root / "data" / "processed" / "stage1_segments_18.csv")

    # Standalone PNGs: high resolution for possible reuse outside the montage
    standalone_w, standalone_h = 1400, 900

    def make_cloud(text: str, out_name: str) -> None:
        if len(text.strip()) < 80:
            return
        wc = _wordcloud(text, stop, width=standalone_w, height=standalone_h, max_words=120)
        plt.figure(figsize=(14, 9))
        plt.imshow(wc, interpolation="bilinear")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(fig_dir / out_name, dpi=200, bbox_inches="tight")
        plt.close()

    make_cloud(_text_blob(df["Quote"], stop), "wordcloud_stage1_all.png")

    large_themes = df.groupby("Theme").size().sort_values(ascending=False)
    theme_jobs: list[tuple[str, str]] = []
    for theme, n in large_themes.items():
        if n < 40:
            continue
        safe = re.sub(r"[^a-zA-Z0-9]+", "_", str(theme)).strip("_").lower()[:60]
        fname = f"wordcloud_theme_{safe}.png"
        make_cloud(_text_blob(df[df["Theme"] == theme]["Quote"], stop), fname)
        theme_jobs.append((str(theme), fname))

    # Montage: 3 rows x 2 columns on one portrait-style page; regenerate clouds per
    # panel so words stay sharp (no upscaling small raster PNGs).
    if len(theme_jobs) >= 6:
        montage_w, montage_h = 1250, 980
        fig, axes = plt.subplots(3, 2, figsize=(11.5, 14))
        for ax, (theme_name, _) in zip(axes.flat, theme_jobs[:6]):
            blob = _text_blob(df[df["Theme"] == theme_name]["Quote"], stop)
            wc = _wordcloud(blob, stop, width=montage_w, height=montage_h, max_words=95)
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            ax.set_title(theme_name, fontsize=11, pad=6)
        plt.tight_layout(h_pad=1.0, w_pad=0.8)
        plt.savefig(fig_dir / "wordcloud_themes_montage.png", dpi=200, bbox_inches="tight")
        plt.close()

    print("Wrote wordcloud PNGs under manuscript/figures/")


if __name__ == "__main__":
    main()
