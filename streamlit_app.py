"""
Shoreline access × ethnicity vs ACS county benchmarks (2024).
Bay Area counties: walk / bike / drive vs ACS baseline.
Run: streamlit run streamlit_app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from acs_benchmarks import (
    benchmarks_for_chart,
    extract_hispanic_race_block,
    load_acs_county_csv,
    total_population,
)
from shoreline_compare import (
    compare_to_acs,
    load_shoreline_csv,
    served_percentages,
    shoreline_long_from_dataframe,
)

BASE = Path(__file__).resolve().parent
DATASETS = BASE / "Datasets"


def _data_dir() -> Path:
    """Use `Datasets/` when files live there (local); else repo root (flat GitHub uploads)."""
    if (DATASETS / "Alameda_county_demographics.csv").exists():
        return DATASETS
    return BASE


# Resolved once at import so paths match the layout Streamlit Cloud actually checked out.
_DATA = _data_dir()

# County label → ACS profile CSV (2024 Estimate column), same layout as Alameda/Napa.
COUNTY_ACS_FILES: tuple[tuple[str, Path], ...] = (
    ("Alameda", _DATA / "Alameda_county_demographics.csv"),
    ("Contra Costa", _DATA / "Contra_costa_county_demographics.csv"),
    ("Marin", _DATA / "Marin_county_demographics.csv"),
    ("Napa", _DATA / "Napa_county_demographics.csv"),
    ("San Francisco", _DATA / "SF_county_demographics.csv"),
    ("San Mateo", _DATA / "San_mateo_county_demographics.csv"),
    ("Santa Clara", _DATA / "Santa_clara_county_demographics.csv"),
    ("Solano", _DATA / "Solano_county_demographics.csv"),
    ("Sonoma", _DATA / "Sonoma_county_demographics.csv"),
)

COUNTIES: tuple[str, ...] = tuple(c for c, _ in COUNTY_ACS_FILES)

SHORELINE_CANDIDATES = [
    _DATA / "shoreline_access_data.csv",
    _DATA / "Shoreline_Access_Data.csv",
    _DATA / "shorelines_access_dataset.csv",
]
SHORELINE_DEFAULT_NAME = "shoreline_access_data.csv"
SHORELINE_EXAMPLE = _DATA / "shorelines_access_dataset.example.csv"

ACCESS_MODES: list[tuple[str, str]] = [
    ("walk", "Walk"),
    ("bike", "Bike"),
    ("drive", "Drive"),
]


def _resolve_shoreline_csv() -> Path | None:
    for p in SHORELINE_CANDIDATES:
        if p.exists():
            return p
    return None


@st.cache_data
def load_all_acs_benchmarks() -> tuple[pd.DataFrame, dict[str, float], dict[str, str]]:
    """Load every county ACS profile and stack ethnicity benchmarks."""
    parts: list[pd.DataFrame] = []
    pops: dict[str, float] = {}
    sources: dict[str, str] = {}
    for county, path in COUNTY_ACS_FILES:
        if not path.exists():
            raise FileNotFoundError(str(path))
        df = load_acs_county_csv(path)
        pop = total_population(df) or 0.0
        pops[county] = pop
        sources[county] = path.name
        bench = benchmarks_for_chart(extract_hispanic_race_block(df), pop)
        bench = bench.assign(county=county)
        parts.append(bench)
    long_df = pd.concat(parts, ignore_index=True)
    return long_df, pops, sources


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

AXIS_LABELS_SHORT: dict[str, str] = {
    "Hispanic or Latino (any race)": "Hispanic / Latino",
    "NH White alone": "White",
    "NH Black alone": "Black",
    "NH AIAN alone": "Am. Indian / Alaska Nat.",
    "NH Asian alone": "Asian",
    "NH NHPI alone": "Pacific Islander",
    "NH Some other race alone": "Some other race",
    "NH Two or more races": "Multiracial",
}


def _category_display_df(df: pd.DataFrame) -> pd.DataFrame:
    """Replace internal ACS `category` labels with short chart/table names."""
    out = df.copy()
    if "category" in out.columns:
        out["category"] = out["category"].map(
            lambda c: AXIS_LABELS_SHORT.get(str(c), c)
        )
    return out


MODE_BAR_COLORS: dict[str, str] = {
    "acs": "#636EFA",
    "walk": "#EF553B",
    "bike": "#00CC96",
    "drive": "#AB63FA",
}


def fig_acs_vs_all_modes(
    by_mode: dict[str, pd.DataFrame],
    county: str,
) -> go.Figure:
    """One grouped chart: ACS + shoreline for Walk, Bike, Drive (easy cross-mode read)."""
    template = "plotly_dark"
    xlabs = [AXIS_LABELS_SHORT[c] for c in COMPOSITION_CATEGORIES]

    d_walk = by_mode["walk"]
    d_acs = d_walk[d_walk["county"] == county].set_index("category").reindex(
        COMPOSITION_CATEGORIES
    )
    acs = d_acs["acs_pct"].values

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="County (ACS 2024)",
            x=xlabs,
            y=acs,
            marker_color=MODE_BAR_COLORS["acs"],
            hovertemplate=(
                "<b>%{customdata}</b><br>County: %{y:.1f}%<extra></extra>"
            ),
            customdata=xlabs,
        )
    )
    for mode_key, mode_display in ACCESS_MODES:
        d = by_mode[mode_key][by_mode[mode_key]["county"] == county].set_index(
            "category"
        ).reindex(COMPOSITION_CATEGORIES)
        sh = pd.to_numeric(d["shore_pct"], errors="coerce").fillna(0.0).values
        fig.add_trace(
            go.Bar(
                name=f"Served — {mode_display}",
                x=xlabs,
                y=sh,
                marker_color=MODE_BAR_COLORS[mode_key],
                hovertemplate=(
                    "<b>%{customdata}</b><br>"
                    + mode_display
                    + ": %{y:.1f}%<extra></extra>"
                ),
                customdata=xlabs,
            )
        )

    fig.update_layout(
        title=f"{county} — population mix: county vs. shoreline access",
        barmode="group",
        bargap=0.22,
        bargroupgap=0.06,
        yaxis_title="Share of population (%)",
        height=540,
        template=template,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.22,
            xanchor="center",
            x=0.5,
        ),
        xaxis_tickangle=-32,
        margin=dict(t=56, b=180, l=56, r=24),
    )
    return fig


def fig_gap_all_modes(
    by_mode: dict[str, pd.DataFrame],
    county: str,
) -> go.Figure:
    """Grouped bars: shoreline % minus ACS % (percentage points) for Walk, Bike, Drive."""
    template = "plotly_dark"
    xlabs = [AXIS_LABELS_SHORT[c] for c in COMPOSITION_CATEGORIES]

    fig = go.Figure()
    for mode_key, mode_display in ACCESS_MODES:
        d = by_mode[mode_key][by_mode[mode_key]["county"] == county].set_index(
            "category"
        ).reindex(COMPOSITION_CATEGORIES)
        gaps = pd.to_numeric(d["gap_pp"], errors="coerce").fillna(0.0).values
        fig.add_trace(
            go.Bar(
                name=f"{mode_display}",
                x=xlabs,
                y=gaps,
                marker_color=MODE_BAR_COLORS[mode_key],
                hovertemplate=(
                    "<b>%{customdata}</b><br>"
                    + mode_display
                    + ": %{y:+.1f} pts<extra></extra>"
                ),
                customdata=xlabs,
            )
        )

    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="rgba(255,255,255,0.45)",
        line_width=1,
    )

    fig.update_layout(
        title=f"{county} — how served mix differs from county (pts)",
        barmode="group",
        bargap=0.22,
        bargroupgap=0.06,
        yaxis_title="Points vs. county mix",
        height=480,
        template=template,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5,
        ),
        xaxis_tickangle=-32,
        margin=dict(t=48, b=160, l=52, r=20),
    )
    return fig


def compare_all_modes(
    long_acs: pd.DataFrame, raw_shore: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for mode_key, _ in ACCESS_MODES:
        long_cnt = shoreline_long_from_dataframe(raw_shore, access_mode=mode_key)
        shore_pct = served_percentages(long_cnt)
        out[mode_key] = compare_to_acs(long_acs, shore_pct)
    return out


def _county_slug(name: str) -> str:
    return name.lower().replace(" ", "_")


def _modes_with_zero_white_residual(
    by_mode: dict[str, pd.DataFrame], county: str
) -> list[str]:
    """Modes where White (residual) shoreline count is 0 after pooling."""
    out: list[str] = []
    for mode_key, mode_display in ACCESS_MODES:
        sub = by_mode[mode_key]
        row = sub[
            (sub["county"] == county) & (sub["category"] == "NH White alone")
        ]
        if row.empty:
            continue
        sc = float(pd.to_numeric(row["shore_count"], errors="coerce").fillna(0).iloc[0])
        if sc <= 0:
            out.append(mode_display)
    return out


def main() -> None:
    st.set_page_config(
        page_title="Shoreline equity — Bay Area",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("Shoreline access & population mix")
    st.markdown(
        "Compare **2024 county** demographics (American Community Survey) to **who sits in shoreline "
        "access buffers** by **walk**, **bike**, and **drive**. Nine Bay Area counties."
    )

    missing_acs = [(c, p) for c, p in COUNTY_ACS_FILES if not p.exists()]
    if missing_acs:
        lines = "\n".join(f"- **{c}** → `{p.name}`" for c, p in missing_acs)
        st.error(f"Missing ACS county CSV(s) in `{_DATA}`:\n\n{lines}")
        return

    try:
        long_df, pops, sources = load_all_acs_benchmarks()
    except Exception as err:
        st.error(f"Could not load ACS county profiles: {err}")
        return

    selected_county = st.sidebar.selectbox(
        "County",
        options=list(COUNTIES),
        index=0,
        help="Charts below use this county. Gap chart uses the same selection.",
    )

    st.sidebar.markdown("##### Inputs")
    st.sidebar.caption(f"Shoreline CSV (auto): `{SHORELINE_DEFAULT_NAME}` or `Shoreline_Access_Data.csv`")
    with st.sidebar.expander("ACS files per county"):
        for c in COUNTIES:
            st.caption(f"{c} — `{sources[c]}`")

    shore_path = _resolve_shoreline_csv()
    raw_shore: pd.DataFrame | None = None
    shore_label = ""
    if shore_path is not None:
        raw_shore = load_shoreline_csv(shore_path)
        shore_label = shore_path.name

    if raw_shore is None:
        st.error(
            f"Missing shoreline CSV. Add **`{SHORELINE_DEFAULT_NAME}`** or **`Shoreline_Access_Data.csv`** "
            f"to `{_DATA}` (or a `Datasets` subfolder with the same files)."
        )
        st.subheader("ACS 2024 benchmarks (reference table)")
        ref = long_df[long_df["category"].isin(COMPOSITION_CATEGORIES)]
        ref_pv = ref.pivot(index="category", columns="county", values=["pct", "estimate"])
        ref_pv.index = ref_pv.index.map(lambda c: AXIS_LABELS_SHORT.get(c, c))
        st.dataframe(ref_pv, use_container_width=True)
        st.download_button(
            label="Download ACS benchmark CSV (all counties)",
            data=_category_display_df(long_df).to_csv(index=False).encode("utf-8"),
            file_name="acs_bay_area_county_ethnicity_benchmarks_2024.csv",
            mime="text/csv",
        )
        return

    top_m1, top_m2, top_m3 = st.columns([1.1, 1.1, 1.4])
    with top_m1:
        st.metric("County selected", selected_county)
    with top_m2:
        st.metric("County population (ACS 2024)", f"{pops[selected_county]:,.0f}")
    with top_m3:
        st.caption("**Shoreline data**")
        st.caption(f"`{shore_label}`")

    if "SUM_Estimated_Latino_Population" in raw_shore.columns:
        with st.expander("How shoreline numbers are built (read once)", expanded=False):
            st.markdown(
                """
- Rows are **access point × travel mode**; values are **summed** across rows, so people near many points can be **counted more than once**.
- **Served %** is the **mix** within that pooled total for each county and mode (walk / bike / drive).
- **White** is what’s **left over** after subtracting Hispanic/Latino and the other race group columns from the file’s **total population** field. If those pieces **add up to more than the total** after summing (common when pooling many buffers), that remainder is **set to zero**—so you may see **no White bar** for some counties/modes even though the county benchmark shows a large White share. That’s a **data-consistency** issue in the summed columns, not a chart bug.
"""
            )

    st.divider()

    try:
        by_mode = compare_all_modes(long_df, raw_shore)
    except ValueError as err:
        st.error(f"Could not parse shoreline file: {err}")
        return

    if any(m["shore_pct"].isna().any() for m in by_mode.values()):
        st.warning(
            "Some county × group cells have no shoreline estimate for a mode; those bars show **0%**."
        )

    zero_white_modes = _modes_with_zero_white_residual(by_mode, selected_county)
    if zero_white_modes:
        st.warning(
            f"**{selected_county}:** shoreline **White** share is **0%** for **{', '.join(zero_white_modes)}** "
            "because summed race/ethnicity columns exceed the summed total-population field (remainder capped at zero). "
            "Often shows up on **Bike** or **Drive** before **Walk**."
        )

    st.markdown(f"### 1 · {selected_county} — county vs. served mix")
    st.caption(
        "Blue = whole-county share (ACS 2024). Orange / green / purple = share within the **served pool** for that mode only."
    )
    st.plotly_chart(
        fig_acs_vs_all_modes(by_mode, selected_county),
        use_container_width=True,
    )

    st.divider()
    st.markdown(f"### 2 · {selected_county} — difference from county mix")
    st.caption(
        "Each bar: **served % minus county %** (percentage points). Above zero = larger share near shoreline than in the county overall."
    )
    st.plotly_chart(
        fig_gap_all_modes(by_mode, selected_county),
        use_container_width=True,
    )

    st.divider()
    st.markdown("### 3 · Table & downloads")
    rows = []
    for mode_key, mode_display in ACCESS_MODES:
        df = by_mode[mode_key].copy()
        df["access_mode"] = mode_display
        rows.append(df)
    combined = pd.concat(rows, ignore_index=True)
    combined_county = combined[combined["county"] == selected_county]
    st.dataframe(_category_display_df(combined_county), use_container_width=True, height=320)

    c_dl1, c_dl2 = st.columns(2)
    with c_dl1:
        st.download_button(
            label=f"Download ACS vs shoreline ({selected_county}, all modes)",
            data=_category_display_df(combined_county).to_csv(index=False).encode("utf-8"),
            file_name=f"acs_vs_shoreline_{_county_slug(selected_county)}_walk_bike_drive.csv",
            mime="text/csv",
        )
    with c_dl2:
        st.download_button(
            label="Download ACS vs shoreline (all counties, all modes)",
            data=_category_display_df(combined).to_csv(index=False).encode("utf-8"),
            file_name="acs_vs_shoreline_all_counties_walk_bike_drive.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
