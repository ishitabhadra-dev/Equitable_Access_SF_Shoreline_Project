"""
Aggregate shoreline / access-served units and compare to ACS county benchmarks.

Supported inputs
----------------
1) **Long** (preferred): columns include county + category + a count column.
   - county: e.g. Alameda, Napa (optional suffix \" County\")
   - category: must match acs_benchmarks chart labels, e.g.
     \"Hispanic or Latino (any race)\", \"NH White alone\", ...
   - count: one of count | population | households | weight | n

2) **Wide**: one row per unit (or pre-aggregated row) with a county column and
   count columns mapped via WIDE_COUNT_COLUMNS (see below).

3) **BCDC shoreline access export** (e.g. ``Shoreline_Access_Data.csv``): columns
   ``County_Name``, ``Service_Type`` (Walk/Bike/Drive), and
   ``SUM_Estimated_*_Population`` totals. NH White is computed as a residual so
   eight groups sum to row ``SUM_Estimated_Total_Population`` (see module doc).

Optional: access_mode column (walk | bike | drive | all) or boolean columns
walk, bike, drive to restrict which rows are included. For BCDC files,
``Service_Type`` is used the same way.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

# Canonical category strings (must match streamlit_app.COMPOSITION_CATEGORIES)
COMPOSITION_CATEGORIES: list[str] = [
    "Hispanic or Latino (any race)",
    "NH White alone",
    "NH Black alone",
    "NH AIAN alone",
    "NH Asian alone",
    "NH NHPI alone",
    "NH Some other race alone",
    "NH Two or more races",
]

# Wide file: map your column names (case-insensitive) -> canonical category
WIDE_COUNT_COLUMNS: dict[str, str] = {
    "hispanic_latino_any": "Hispanic or Latino (any race)",
    "hispanic_any": "Hispanic or Latino (any race)",
    "latino_hispanic": "Hispanic or Latino (any race)",
    "nh_white_alone": "NH White alone",
    "nh_white": "NH White alone",
    "white_nh": "NH White alone",
    "nh_black_alone": "NH Black alone",
    "nh_black": "NH Black alone",
    "black_nh": "NH Black alone",
    "nh_aian_alone": "NH AIAN alone",
    "nh_aian": "NH AIAN alone",
    "aian_nh": "NH AIAN alone",
    "nh_asian_alone": "NH Asian alone",
    "nh_asian": "NH Asian alone",
    "asian_nh": "NH Asian alone",
    "nh_nhpi_alone": "NH NHPI alone",
    "nh_nhpi": "NH NHPI alone",
    "nh_pacific_alone": "NH NHPI alone",
    "nh_some_other_race_alone": "NH Some other race alone",
    "nh_sor_alone": "NH Some other race alone",
    "nh_two_or_more": "NH Two or more races",
    "nh_multiracial": "NH Two or more races",
    "two_or_more_races": "NH Two or more races",
}

COUNT_ALIASES = ("count", "population", "households", "weight", "n", "units", "hh")
COUNTY_ALIASES = ("county", "county_name", "subregion", "geography")

# Must match shoreline `County_Name` and ACS app county labels.
CANONICAL_COUNTIES: tuple[str, ...] = (
    "Alameda",
    "Contra Costa",
    "Marin",
    "Napa",
    "San Francisco",
    "San Mateo",
    "Santa Clara",
    "Solano",
    "Sonoma",
)


def _norm_county(val: object) -> str | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    s = re.sub(r",\s*California$", "", s, flags=re.I)
    s = re.sub(r"\s+county$", "", s, flags=re.I).strip()
    for c in CANONICAL_COUNTIES:
        if s.lower() == c.lower():
            return c
    return None


def _pick_column(df: pd.DataFrame, names: tuple[str, ...]) -> str | None:
    cmap = {c.lower(): c for c in df.columns}
    for n in names:
        if n.lower() in cmap:
            return cmap[n.lower()]
    return None


def _filter_access_mode(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    if mode not in ("all", "walk", "bike", "drive"):
        mode = "all"
    if mode == "all":
        return df
    stype = _pick_column(df, ("service_type",))
    if stype:
        m = df[stype].astype(str).str.strip().str.lower()
        sub = df[m == mode.lower()].copy()
        if len(sub) > 0:
            return sub
    mcol = _pick_column(df, ("access_mode", "mode", "travel_mode"))
    if mcol:
        sub = df[df[mcol].astype(str).str.lower().str.strip() == mode].copy()
        if len(sub) == 0:
            return df
        return sub
    bcol = _pick_column(df, (mode,))
    if bcol and df[bcol].dtype in (bool, "bool"):
        return df[df[bcol] == True].copy()  # noqa: E712
    return df


def _aggregate_bcdc_estimated_population(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sum SUM_Estimated_* columns by county (canonical Bay Area counties only).
    NH White alone = total − Latino − (other race-alone NH sums), floored at 0.
    """
    cty = _pick_column(df, ("County_Name", "COUNTY_NAME"))
    if not cty:
        raise ValueError("BCDC format: missing County_Name.")

    col_total = _pick_column(df, ("SUM_Estimated_Total_Population",))
    col_lat = _pick_column(df, ("SUM_Estimated_Latino_Population",))
    col_blk = _pick_column(df, ("SUM_Estimated_Black_Population",))
    col_aian = _pick_column(df, ("SUM_Estimated_American_Indian_Population",))
    col_asn = _pick_column(df, ("SUM_Estimated_Asian_Population",))
    col_nhpi = _pick_column(df, ("SUM_Estimated_Pacific_Islander_Population",))
    col_sor = _pick_column(df, ("SUM_Estimated_Other_Race_Population",))
    col_tom = _pick_column(df, ("SUM_Estimated_Two_Or_More_Races_Population",))
    req = (col_total, col_lat, col_blk, col_aian, col_asn, col_nhpi, col_sor, col_tom)
    if not all(req):
        raise ValueError(
            "BCDC format: missing one or more SUM_Estimated_* population columns."
        )

    d = df.copy()
    d["_county"] = d[cty].map(_norm_county)
    d = d[d["_county"].notna()]
    if d.empty:
        return pd.DataFrame(columns=["county", "category", "count"])

    sum_cols = list(
        dict.fromkeys(
            [col_total, col_lat, col_blk, col_aian, col_asn, col_nhpi, col_sor, col_tom]
        )
    )
    for c in sum_cols:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0.0)
    g = d.groupby("_county", as_index=False)[sum_cols].sum()

    rows: list[dict[str, object]] = []
    cat_map: list[tuple[str, str]] = [
        ("NH Black alone", col_blk),
        ("NH AIAN alone", col_aian),
        ("NH Asian alone", col_asn),
        ("NH NHPI alone", col_nhpi),
        ("NH Some other race alone", col_sor),
        ("NH Two or more races", col_tom),
    ]
    for _, r in g.iterrows():
        county = str(r["_county"])
        total = float(r[col_total])
        lat = float(r[col_lat])
        blk = float(r[col_blk])
        aian = float(r[col_aian])
        asn = float(r[col_asn])
        nhpi = float(r[col_nhpi])
        sor = float(r[col_sor])
        tom = float(r[col_tom])
        # Residual NH White; floored at 0 when summed race/Hispanic exceeds total (pooled-row inconsistency).
        nh_white = total - lat - blk - aian - asn - nhpi - sor - tom
        nh_white = max(0.0, nh_white)
        rows.append(
            {"county": county, "category": "Hispanic or Latino (any race)", "count": lat}
        )
        rows.append({"county": county, "category": "NH White alone", "count": nh_white})
        for cat, ccol in cat_map:
            rows.append({"county": county, "category": cat, "count": float(r[ccol])})

    out = pd.DataFrame(rows)
    return out.groupby(["county", "category"], as_index=False)["count"].sum()


def shoreline_long_from_dataframe(
    raw: pd.DataFrame,
    access_mode: str = "all",
) -> pd.DataFrame:
    """
    Return columns: county, category, count (sums over rows).
    Raises ValueError if format is not recognized.
    """
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = _filter_access_mode(df, access_mode)

    if _pick_column(df, ("SUM_Estimated_Latino_Population",)) and _pick_column(
        df, ("County_Name",)
    ):
        return _aggregate_bcdc_estimated_population(df)

    cat_col = _pick_column(df, ("category", "group", "ethnicity_category", "race_category"))
    cnt_col = _pick_column(df, COUNT_ALIASES)
    cty_col = _pick_column(df, COUNTY_ALIASES)

    if cat_col and cnt_col and cty_col:
        out = df[[cty_col, cat_col, cnt_col]].copy()
        out.columns = ["county_raw", "category", "count"]
        out["county"] = out["county_raw"].map(_norm_county)
        out = out.dropna(subset=["county"])
        out["count"] = pd.to_numeric(out["count"], errors="coerce").fillna(0)
        agg = out.groupby(["county", "category"], as_index=False)["count"].sum()
        return agg

    # Wide: county + multiple count_* columns
    if not cty_col:
        raise ValueError(
            "Could not find a county column. Expected one of: "
            + ", ".join(COUNTY_ALIASES)
        )
    rows = []
    for std_name, category in WIDE_COUNT_COLUMNS.items():
        col = _pick_column(df, (std_name,))
        if not col:
            continue
        chunk = df[[cty_col, col]].copy()
        chunk.columns = ["county_raw", "count"]
        chunk["county"] = chunk["county_raw"].map(_norm_county)
        chunk["category"] = category
        chunk["count"] = pd.to_numeric(chunk["count"], errors="coerce").fillna(0)
        chunk = chunk.dropna(subset=["county"])
        rows.append(chunk[["county", "category", "count"]])
    if not rows:
        raise ValueError(
            "Wide format: no recognized count columns. "
            "Add long-format columns (county, category, count) or rename columns to match "
            f"WIDE_COUNT_COLUMNS keys, e.g. nh_white_alone, hispanic_latino_any. "
            f"Columns seen: {list(df.columns)}"
        )
    stacked = pd.concat(rows, ignore_index=True)
    return stacked.groupby(["county", "category"], as_index=False)["count"].sum()


def served_percentages(long_counts: pd.DataFrame) -> pd.DataFrame:
    """Add pct_served within each county (composition of served population)."""
    if long_counts.empty:
        return long_counts.assign(pct_served=pd.Series(dtype=float))
    totals = long_counts.groupby("county")["count"].transform("sum")
    out = long_counts.copy()
    out["pct_served"] = 100.0 * out["count"] / totals.replace(0, pd.NA)
    return out


def compare_to_acs(
    acs_long: pd.DataFrame,
    shore_pct: pd.DataFrame,
    categories: list[str] | None = None,
) -> pd.DataFrame:
    """
    acs_long: columns county, category, pct (from benchmarks).
    shore_pct: columns county, category, count, pct_served.
    """
    cats = categories or COMPOSITION_CATEGORIES
    acs = acs_long[acs_long["category"].isin(cats)][["county", "category", "pct"]].copy()
    acs = acs.rename(columns={"pct": "acs_pct"})
    sh = shore_pct[shore_pct["category"].isin(cats)][
        ["county", "category", "count", "pct_served"]
    ].copy()
    sh = sh.rename(columns={"pct_served": "shore_pct", "count": "shore_count"})
    merged = acs.merge(sh, on=["county", "category"], how="outer")
    merged["acs_pct"] = pd.to_numeric(merged["acs_pct"], errors="coerce")
    merged["shore_pct"] = pd.to_numeric(merged["shore_pct"], errors="coerce")
    merged["gap_pp"] = merged["shore_pct"] - merged["acs_pct"]
    merged["category"] = pd.Categorical(
        merged["category"], categories=cats, ordered=True
    )
    return merged.sort_values(["county", "category"])


def load_shoreline_csv(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, low_memory=False)
