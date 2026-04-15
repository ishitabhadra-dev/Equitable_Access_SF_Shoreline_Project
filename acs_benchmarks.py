"""Parse ACS county profile-style CSV exports (FactFinder / data.census.gov format)."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


def _norm_label(s: str) -> str:
    s = str(s).replace("\xa0", " ").strip()
    while "  " in s:
        s = s.replace("  ", " ")
    return s


def _parse_count(s: str) -> float | None:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    t = str(s).strip()
    if t in ("(X)", "N", "*****", "", "nan"):
        return None
    t = t.replace(",", "")
    if re.fullmatch(r"-+", t):
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _parse_pct(s: str) -> float | None:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    t = str(s).strip()
    if t in ("(X)", "N", "*****", "", "nan"):
        return None
    t = t.replace("%", "").strip()
    try:
        return float(t)
    except ValueError:
        return None


def _parse_pct_moe(s: str) -> float | None:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    t = str(s).strip()
    if t in ("(X)", "N", "*****", "", "nan"):
        return None
    t = t.replace("±", "").replace("%", "").strip()
    try:
        return float(t)
    except ValueError:
        return None


def _parse_typed_cell(s: str) -> tuple[float | None, float | None]:
    """Return (pct, count) — exactly one is usually set; percents contain '%'."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None, None
    t = str(s).strip()
    if t in ("(X)", "N", "*****", "", "nan"):
        return None, None
    if "%" in t:
        return _parse_pct(s), None
    c = _parse_count(s)
    return None, c


def load_acs_county_csv(path: str | Path) -> pd.DataFrame:
    """
    Return long-form table: label_norm, estimate, estimate_moe, pct, pct_moe.

    Supports (a) multi-year profile CSVs with a single ``!!2024 Estimate`` column
    (percents and counts mixed), or (b) classic FactFinder columns with separate
    percent and estimate fields.
    """
    path = Path(path)
    raw = pd.read_csv(path, dtype=str)
    if raw.empty:
        return pd.DataFrame(
            columns=["label_norm", "estimate", "estimate_moe", "pct", "pct_moe"]
        )

    label_col = raw.columns[0]
    cols = list(raw.columns)
    y24 = [
        c
        for c in cols
        if "2024 Estimate" in c and "2024 -" not in c and "Statistical" not in c
    ]
    if y24:
        data_col = y24[0]
        pc: list[float | None] = []
        ec: list[float | None] = []
        for v in raw[data_col]:
            p, e = _parse_typed_cell(v)
            pc.append(p)
            ec.append(e)
        n = len(raw)
        return pd.DataFrame(
            {
                "label_norm": raw[label_col].map(_norm_label),
                "estimate": ec,
                "estimate_moe": [pd.NA] * n,
                "pct": pc,
                "pct_moe": [pd.NA] * n,
            }
        )

    est_col = next(c for c in cols if "Estimate" in c and "Margin" not in c)
    moe_col = next(c for c in cols if "Margin of Error" in c and "Percent" not in c)
    pct_col = next(
        c for c in cols if c.endswith("!!Percent") or c.endswith(",Percent")
    )
    if pct_col not in raw.columns:
        pct_col = [c for c in cols if "Percent" in c and "Margin" not in c][-2]
    pct_moe_col = next(c for c in cols if "Percent Margin of Error" in c)

    return pd.DataFrame(
        {
            "label_norm": raw[label_col].map(_norm_label),
            "estimate": raw[est_col].map(_parse_count),
            "estimate_moe": raw[moe_col].map(_parse_pct_moe),
            "pct": raw[pct_col].map(_parse_pct),
            "pct_moe": raw[pct_moe_col].map(_parse_pct_moe),
        }
    )


def extract_hispanic_race_block(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rows under 'HISPANIC OR LATINO AND RACE' through before 'Total housing units'.
    Percentages are share of total population.
    """
    labels = df["label_norm"].tolist()
    try:
        start = labels.index("HISPANIC OR LATINO AND RACE")
    except ValueError:
        return pd.DataFrame()

    end = len(labels)
    for i in range(start + 1, len(labels)):
        if labels[i] == "Total housing units":
            end = i
            break

    block = df.iloc[start + 1 : end].copy()
    block = block[block["label_norm"] != "Total population"]
    block = block.dropna(subset=["label_norm"])
    return block


def benchmarks_for_chart(
    block: pd.DataFrame, total_pop: float | None = None
) -> pd.DataFrame:
    """Pick headline rows for ethnicity / Latino origin comparison."""
    want_display = {
        "Hispanic or Latino (of any race)": "Hispanic or Latino (any race)",
        "Not Hispanic or Latino": "Not Hispanic or Latino",
        "White alone": "NH White alone",
        "Black or African American alone": "NH Black alone",
        "American Indian and Alaska Native alone": "NH AIAN alone",
        "Asian alone": "NH Asian alone",
        "Native Hawaiian and Other Pacific Islander alone": "NH NHPI alone",
        "Some Other Race alone": "NH Some other race alone",
        "Two or More Races": "NH Two or more races",
    }
    rows = []
    seen_nh = False
    for _, r in block.iterrows():
        lab = r["label_norm"]
        if lab == "Not Hispanic or Latino":
            seen_nh = True
        if lab not in want_display:
            continue
        disp = want_display[lab]
        if lab == "White alone" and not seen_nh:
            continue
        pct = r["pct"]
        est = r["estimate"]
        if (
            total_pop
            and (est is None or (isinstance(est, float) and pd.isna(est)))
            and pct is not None
            and not pd.isna(pct)
        ):
            est = round(float(total_pop) * float(pct) / 100.0)
        rows.append(
            {
                "category": disp,
                "pct": pct,
                "pct_moe": r["pct_moe"],
                "estimate": est,
            }
        )
    return pd.DataFrame(rows)


def total_population(df: pd.DataFrame) -> float | None:
    """First 'Total population' under SEX AND AGE (count, not percent)."""
    labels = df["label_norm"].tolist()
    for i, lab in enumerate(labels):
        if lab == "SEX AND AGE":
            for j in range(i + 1, min(i + 6, len(labels))):
                if labels[j] == "Total population":
                    v = df.iloc[j]["estimate"]
                    return float(v) if v is not None and not pd.isna(v) else None
    return None
