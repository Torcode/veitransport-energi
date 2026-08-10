"""Skjøteregler for salgsstatistikken (D-0002, D-0003).

Reglene fra designporten, håndhevet i kode:
- Gjennomgående begrep er petroleumsmåltallet (inkl. iblandet bio).
- Bilbensin kan settes sammen 1995M01- (03687 -> 11174 -> 13585) med
  segmentmerking; 2020-bruddet gjelder ikke bensin.
- Dieselsum (autodiesel+anleggsdiesel) kan settes sammen 1995M01-2019M12.
- Autodiesel finnes bare fra 2010M01, og SKJØTES ALDRI over 2020M01
  (dokumentert innsamlingsbrudd). Forsøk skal feile med SpliceError.
"""
from __future__ import annotations

import pandas as pd

BREAK_MONTH_AUTODIESEL = "2020M01"


class SpliceError(RuntimeError):
    """Forsøk på en skjøt designporten forbyr."""


def _pivot(df: pd.DataFrame, prod_col: str) -> pd.DataFrame:
    return df.pivot_table(index="Tid", columns=prod_col, values="value", aggfunc="first")


def bensin_series(s03: pd.DataFrame, s11: pd.DataFrame, s13: pd.DataFrame) -> pd.DataFrame:
    """Segmentert bensinserie, petroleumsmåltallet, 1995M01-."""
    a = _pivot(s03, "PetroleumProd")["03"].rename("value").to_frame()
    a["segment"] = "03687"
    b = _pivot(s11, "PetroleumProd")["03"].rename("value").to_frame()
    b["segment"] = "11174"
    c13 = s13[s13["ContentsCode"] == "Petroleum"]
    c = _pivot(c13, "Produkter")["01"].rename("value").to_frame()
    c["segment"] = "13585_petroleum"
    # prioriter nyeste kilde i overlapp
    out = pd.concat([a, b, c])
    out = out[~out.index.duplicated(keep="last")].sort_index()
    out.index.name = "Tid"
    out["serie"] = "bilbensin_petroleum"
    return out.reset_index()


def dieselsum_series(s03: pd.DataFrame, s11: pd.DataFrame) -> pd.DataFrame:
    """Dieselsum (autodiesel+anleggsdiesel) 1995M01-2019M12, segmentert.

    Stoppes ved 2019M12: fra 2020 er nivået ikke sammenlignbart bakover
    (innsamlingskorreksjonen), og dieselsummen videreføres i stedet som egne
    segmenter fra de nyere tabellene.
    """
    a = _pivot(s03, "PetroleumProd")["04"].rename("value").to_frame()
    a["segment"] = "03687_diesel_udelt"
    p11 = _pivot(s11, "PetroleumProd")
    b = (p11["04a"] + p11["04b"]).rename("value").to_frame()
    b["segment"] = "11174_sum_04a_04b"
    out = pd.concat([a, b])
    out = out[~out.index.duplicated(keep="last")].sort_index()
    out = out[out.index < BREAK_MONTH_AUTODIESEL]
    out.index.name = "Tid"
    out["serie"] = "dieselsum_prebrudd"
    return out.reset_index()


def autodiesel_segments(
    s11: pd.DataFrame, s13: pd.DataFrame, *, allow_cross_break: bool = False
) -> pd.DataFrame:
    """Autodiesel som to adskilte segmenter (2010M01-2019M12 og 2020M01-).

    allow_cross_break finnes bare for å kunne demonstrere at vakten virker i
    test; produksjonskode skal aldri sette den.
    """
    if allow_cross_break:
        raise SpliceError(
            "D-0002/D-0003: autodiesel skal ikke settes sammen til én serie over "
            f"{BREAK_MONTH_AUTODIESEL} (dokumentert innsamlingsbrudd 2012-2019)."
        )
    p11 = _pivot(s11, "PetroleumProd")["04b"].rename("value").to_frame()
    pre = p11[p11.index < BREAK_MONTH_AUTODIESEL].copy()
    pre["segment"] = "autodiesel_2010_2019"
    p13 = s13[s13["ContentsCode"] == "Petroleum"]
    post_11 = p11[p11.index >= BREAK_MONTH_AUTODIESEL].copy()
    post_11["segment"] = "autodiesel_2020_"
    post_13 = _pivot(p13, "Produkter")["02a"].rename("value").to_frame()
    post_13["segment"] = "autodiesel_2020_"
    post = pd.concat([post_11, post_13])
    post = post[~post.index.duplicated(keep="last")]
    out = pd.concat([pre, post]).sort_index()
    out.index.name = "Tid"
    out["serie"] = "autodiesel_petroleum_segmentert"
    return out.reset_index()


def overlap_stats(x: pd.Series, y: pd.Series) -> dict[str, float]:
    """Nivå- og vekstavvik i felles måneder (samme mål som i designporten)."""
    common = x.index.intersection(y.index)
    xs, ys = x.loc[common].astype(float), y.loc[common].astype(float)
    d = (ys - xs) / xs * 100
    import numpy as np

    gx, gy = np.diff(np.log(xs.values)), np.diff(np.log(ys.values))
    return {
        "n": int(len(common)),
        "mean_ratio": float((ys / xs).mean()),
        "median_abs_pct_diff": float(d.abs().median()),
        "max_abs_pct_diff": float(d.abs().max()),
        "growth_corr": float(np.corrcoef(gx, gy)[0, 1]),
    }
