"""
San Francisco Bay shoreline access vs. ACS county benchmarks (2024).
Narrative microsite + interactive charts. Run: streamlit run streamlit_app.py
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
import narrative_content as nc
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


_DATA = _data_dir()

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
MODE_DISPLAY: dict[str, str] = {k: v for k, v in ACCESS_MODES}

# Restrained palette: slate benchmark, muted blue–green modes
CHART_TEMPLATE = "plotly_white"
MODE_BAR_COLORS: dict[str, str] = {
    "acs": "#334155",
    "walk": "#0f766e",
    "bike": "#0e7490",
    "drive": "#475569",
}
CHART_PAPER = "#f4f6f8"
CHART_FONT_COLOR = "#1e293b"


def _chart_layout_kwargs() -> dict:
    """Shared typography for presentation readability."""
    return {
        "font": {"size": 15, "color": CHART_FONT_COLOR},
        "title_font": {"size": 18, "color": CHART_FONT_COLOR},
        "paper_bgcolor": CHART_PAPER,
        "plot_bgcolor": "#ffffff",
    }


@st.cache_data
def load_all_acs_benchmarks() -> tuple[pd.DataFrame, dict[str, float], dict[str, str]]:
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
    out = df.copy()
    if "category" in out.columns:
        out["category"] = out["category"].map(
            lambda c: AXIS_LABELS_SHORT.get(str(c), c)
        )
    return out


def _resolve_shoreline_csv() -> Path | None:
    for p in SHORELINE_CANDIDATES:
        if p.exists():
            return p
    return None


def fig_acs_vs_all_modes(
    by_mode: dict[str, pd.DataFrame],
    county: str,
    *,
    title: str | None = None,
    y_axis_top: float | None = None,
) -> go.Figure:
    """Grouped bars: county ACS + Walk / Bike / Drive served mix."""
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
            hovertemplate="<b>%{customdata}</b><br>County: %{y:.1f}%<extra></extra>",
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
                    f"<b>%{{customdata}}</b><br>{mode_display}: %{{y:.1f}}%<extra></extra>"
                ),
                customdata=xlabs,
            )
        )

    ttl = title or f"{county} — county population share vs. shoreline served mix"
    fig.update_layout(
        title=ttl,
        barmode="group",
        bargap=0.22,
        bargroupgap=0.06,
        yaxis_title="Share of population (%)",
        height=560,
        template=CHART_TEMPLATE,
        legend=dict(orientation="h", yanchor="top", y=-0.2, x=0.5, xanchor="center"),
        xaxis_tickangle=-32,
        margin=dict(t=64, b=170, l=56, r=28),
        yaxis=dict(range=[0, y_axis_top] if y_axis_top else None),
        **_chart_layout_kwargs(),
    )
    return fig


def fig_gap_all_modes(
    by_mode: dict[str, pd.DataFrame],
    county: str,
    *,
    title: str | None = None,
) -> go.Figure:
    """Gaps (served % − county %) for Walk, Bike, Drive."""
    xlabs = [AXIS_LABELS_SHORT[c] for c in COMPOSITION_CATEGORIES]
    fig = go.Figure()
    for mode_key, mode_display in ACCESS_MODES:
        d = by_mode[mode_key][by_mode[mode_key]["county"] == county].set_index(
            "category"
        ).reindex(COMPOSITION_CATEGORIES)
        gaps = pd.to_numeric(d["gap_pp"], errors="coerce").fillna(0.0).values
        fig.add_trace(
            go.Bar(
                name=mode_display,
                x=xlabs,
                y=gaps,
                marker_color=MODE_BAR_COLORS[mode_key],
                hovertemplate=(
                    f"<b>%{{customdata}}</b><br>{mode_display}: %{{y:+.1f}} pts<extra></extra>"
                ),
                customdata=xlabs,
            )
        )

    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="rgba(30,41,59,0.35)",
        line_width=1,
    )

    ttl = title or f"{county} — difference from county mix (percentage points)"
    fig.update_layout(
        title=ttl,
        barmode="group",
        bargap=0.22,
        bargroupgap=0.06,
        yaxis_title="Points vs. county mix",
        height=500,
        template=CHART_TEMPLATE,
        legend=dict(orientation="h", yanchor="top", y=-0.18, x=0.5, xanchor="center"),
        xaxis_tickangle=-32,
        margin=dict(t=60, b=150, l=52, r=24),
        **_chart_layout_kwargs(),
    )
    return fig


def fig_acs_vs_single_mode(
    by_mode: dict[str, pd.DataFrame],
    county: str,
    mode_key: str,
    *,
    title: str | None = None,
) -> go.Figure:
    """County benchmark vs. one transportation mode (cleaner mode-focused view)."""
    mode_display = MODE_DISPLAY[mode_key]
    xlabs = [AXIS_LABELS_SHORT[c] for c in COMPOSITION_CATEGORIES]
    d_mode = by_mode[mode_key]
    d_row = d_mode[d_mode["county"] == county].set_index("category").reindex(
        COMPOSITION_CATEGORIES
    )
    acs = d_row["acs_pct"].values
    sh = pd.to_numeric(d_row["shore_pct"], errors="coerce").fillna(0.0).values

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="County (ACS 2024)",
            x=xlabs,
            y=acs,
            marker_color=MODE_BAR_COLORS["acs"],
            hovertemplate="<b>%{customdata}</b><br>County: %{y:.1f}%<extra></extra>",
            customdata=xlabs,
        )
    )
    fig.add_trace(
        go.Bar(
            name=f"Served — {mode_display}",
            x=xlabs,
            y=sh,
            marker_color=MODE_BAR_COLORS[mode_key],
            hovertemplate=(
                f"<b>%{{customdata}}</b><br>{mode_display} served: %{{y:.1f}}%<extra></extra>"
            ),
            customdata=xlabs,
        )
    )
    ttl = title or f"{county} — county vs. {mode_display.lower()} access served pool"
    fig.update_layout(
        title=ttl,
        barmode="group",
        bargap=0.18,
        bargroupgap=0.08,
        yaxis_title="Share of population (%)",
        height=520,
        template=CHART_TEMPLATE,
        legend=dict(orientation="h", yanchor="top", y=-0.14, x=0.5, xanchor="center"),
        xaxis_tickangle=-32,
        margin=dict(t=60, b=120, l=56, r=28),
        **_chart_layout_kwargs(),
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


# ---------------------------------------------------------------------------
# Layout: global CSS (editorial, minimal)
# ---------------------------------------------------------------------------
def inject_page_styles() -> None:
    st.markdown(
        """
<style>
  /* Main column breathing room */
  .block-container {
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    max-width: 1200px !important;
  }
  .hero-wrap {
    border: 1px solid #cbd5e1;
    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    border-radius: 4px;
    padding: 2.25rem 2rem 2rem 2rem;
    margin-bottom: 2.5rem;
  }
  .hero-title {
    font-size: 1.85rem;
    font-weight: 650;
    letter-spacing: -0.02em;
    color: #0f172a;
    line-height: 1.2;
    margin: 0 0 0.75rem 0;
  }
  .hero-sub {
    font-size: 1.05rem;
    color: #334155;
    line-height: 1.45;
    margin: 0 0 1.25rem 0;
  }
  .hero-intro {
    font-size: 1rem;
    color: #1e293b;
    line-height: 1.6;
    margin: 0 0 1.25rem 0;
  }
  .hero-bullets {
    margin: 0;
    padding-left: 1.2rem;
    color: #334155;
    line-height: 1.7;
    font-size: 0.98rem;
  }
  .section-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #64748b;
    margin-bottom: 0.35rem;
    font-weight: 600;
  }
  .section-title {
    font-size: 1.35rem;
    font-weight: 650;
    color: #0f172a;
    margin: 0 0 0.75rem 0;
    letter-spacing: -0.01em;
  }
  .section-intro {
    color: #334155;
    line-height: 1.65;
    font-size: 1rem;
    margin-bottom: 1.25rem;
  }
  .kf-card {
    border: 1px solid #e2e8f0;
    background: #ffffff;
    border-radius: 4px;
    padding: 1.15rem 1.25rem 1.1rem 1.25rem;
    margin-bottom: 0.85rem;
  }
  .kf-card h4 {
    margin: 0 0 0.65rem 0;
    font-size: 1.02rem;
    font-weight: 600;
    color: #0f172a;
  }
  .kf-card ul {
    margin: 0 0 0.65rem 0;
    padding-left: 1.15rem;
    color: #334155;
    line-height: 1.55;
    font-size: 0.95rem;
  }
  .kf-takeaway {
    font-size: 0.92rem;
    color: #0f766e;
    border-left: 3px solid #0d9488;
    padding-left: 0.75rem;
    margin: 0;
    line-height: 1.5;
  }
  .takeaway-box {
    border: 1px solid #cbd5e1;
    background: #f8fafc;
    border-left: 3px solid #0f766e;
    padding: 0.85rem 1rem;
    border-radius: 4px;
    margin-top: 0.75rem;
  }
  .takeaway-box strong { color: #0f172a; }
  .policy-card {
    border: 1px solid #e2e8f0;
    background: #ffffff;
    border-radius: 4px;
    padding: 1rem 1.05rem;
    height: 100%;
  }
  .policy-card h4 {
    margin: 0 0 0.5rem 0;
    font-size: 0.98rem;
    font-weight: 600;
    color: #0f172a;
  }
  .policy-card p {
    margin: 0;
    font-size: 0.9rem;
    color: #475569;
    line-height: 1.55;
  }
  .limitations-box {
    border: 1px solid #e2e8f0;
    background: #f1f5f9;
    border-radius: 4px;
    padding: 1.25rem 1.35rem;
    margin-top: 2rem;
  }
  .limitations-box h3 {
    margin: 0 0 0.75rem 0;
    font-size: 1.05rem;
    color: #475569;
    font-weight: 600;
  }
  .limitations-box ul {
    margin: 0;
    padding-left: 1.15rem;
    color: #64748b;
    line-height: 1.6;
    font-size: 0.92rem;
  }
  .chart-caption {
    font-size: 0.9rem;
    color: #475569;
    line-height: 1.55;
    margin-top: 0.35rem;
    margin-bottom: 0.15rem;
  }
  .mode-callout {
    font-size: 0.8rem;
    font-weight: 600;
    color: #0f766e;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.25rem;
  }
  div[data-testid="stExpander"] details summary {
    font-weight: 500;
    color: #475569;
  }
</style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    bullets_html = "".join(f"<li>{b}</li>" for b in nc.HERO_BULLETS)
    st.markdown(
        f"""
<div class="hero-wrap">
  <p class="hero-title">{nc.HERO_TITLE}</p>
  <p class="hero-sub">{nc.HERO_SUBTITLE}</p>
  <p class="hero-intro">{nc.HERO_INTRO}</p>
  <ul class="hero-bullets">{bullets_html}</ul>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_study_summary() -> None:
    st.markdown(
        f"""
<div style="max-width:920px;margin:0 0 2rem 0;padding:0 0.15rem;">
  <div class="section-label">Study summary</div>
  <p class="section-intro" style="margin-bottom:0;">{nc.STUDY_SUMMARY}</p>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(label: str, title: str, intro: str | None = None) -> None:
    intro_html = f'<p class="section-intro">{intro}</p>' if intro else ""
    st.markdown(
        f"""
<div class="section-label">{label}</div>
<h2 class="section-title">{title}</h2>
{intro_html}
        """,
        unsafe_allow_html=True,
    )


def render_key_findings() -> None:
    render_section_header("Synthesis", "Key Findings")
    for card in nc.KEY_FINDINGS:
        bullets = "".join(f"<li>{b}</li>" for b in card["bullets"])
        st.markdown(
            f"""
<div class="kf-card">
  <h4>{card["title"]}</h4>
  <ul>{bullets}</ul>
  <p class="kf-takeaway">{card["takeaway"]}</p>
</div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)


def render_county_example_block(county: str, by_mode: dict[str, pd.DataFrame]) -> None:
    narrative = nc.COUNTY_NARRATIVES.get(county)
    caption = narrative["caption"] if narrative else nc.COUNTY_GENERIC_CAPTION
    st.markdown(f'<p class="chart-caption">{caption}</p>', unsafe_allow_html=True)
    st.plotly_chart(
        fig_acs_vs_all_modes(
            by_mode,
            county,
            title=f"{county} — county share vs. shoreline served mix (by mode)",
        ),
        use_container_width=True,
    )
    st.caption(
        "Bars show ACS 2024 county population share (dark) and modeled share within shoreline "
        "access buffers for walk, bike, and drive (teal tones)."
    )
    if narrative:
        st.markdown(
            f"""
<div class="takeaway-box">
  <strong>{narrative["takeaway_title"]}:</strong> {narrative["takeaway_body"]}
</div>
            """,
            unsafe_allow_html=True,
        )


def render_county_examples(by_mode: dict[str, pd.DataFrame]) -> None:
    render_section_header("Evidence", "County examples", nc.COUNTY_EXAMPLES_INTRO)
    tab_names = list(nc.FEATURED_COUNTIES_DEFAULT) + ["More counties"]
    tabs = st.tabs(tab_names)
    for i, county in enumerate(nc.FEATURED_COUNTIES_DEFAULT):
        with tabs[i]:
            render_county_example_block(county, by_mode)
    with tabs[-1]:
        more_options = [c for c in COUNTIES if c not in nc.FEATURED_COUNTIES_DEFAULT]
        pick = st.selectbox(
            "Choose a county",
            options=more_options,
            index=0,
            key="county_more_tab",
            label_visibility="collapsed",
        )
        render_county_example_block(pick, by_mode)
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)


def render_transport_section(by_mode: dict[str, pd.DataFrame]) -> None:
    render_section_header("Methods lens", nc.TRANSPORT_SECTION_TITLE, nc.TRANSPORT_INTRO)
    county_mode = st.selectbox(
        "County for mode comparison",
        options=list(COUNTIES),
        index=list(COUNTIES).index("Santa Clara"),
        key="transport_county_pick",
    )
    mode_tabs = st.tabs(["Walk", "Bike", "Drive"])
    mode_keys = ("walk", "bike", "drive")
    for tab, mkey in zip(mode_tabs, mode_keys):
        with tab:
            st.markdown(
                f'<p class="mode-callout">{nc.MODE_CALLOUTS.get(mkey, "")}</p>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                fig_acs_vs_single_mode(
                    by_mode,
                    county_mode,
                    mkey,
                    title=f"{county_mode} — county vs. {MODE_DISPLAY[mkey].lower()} served pool",
                ),
                use_container_width=True,
            )
            st.caption(
                "Two bars per group: whole-county share and share within the modeled served "
                f"population for **{MODE_DISPLAY[mkey]}** access only."
            )
    st.markdown(
        f'<p class="section-intro" style="margin-top:1.25rem;">{nc.TRANSPORT_INTERPRETATION}</p>',
        unsafe_allow_html=True,
    )
    # One gap chart (all modes) for the selected county — strong cross-mode read without repeating composition
    st.markdown('<p class="section-label" style="margin-top:1.5rem;">Gap view</p>', unsafe_allow_html=True)
    st.markdown(
        f"<h3 class='section-title' style='font-size:1.1rem;'>{county_mode} — all modes vs. county</h3>",
        unsafe_allow_html=True,
    )
    st.caption("Difference in percentage points: positive means larger share in the shoreline pool than county-wide.")
    st.plotly_chart(
        fig_gap_all_modes(
            by_mode,
            county_mode,
            title=f"{county_mode} — served mix minus county mix (walk, bike, drive)",
        ),
        use_container_width=True,
    )
    st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)


def render_why_matters() -> None:
    render_section_header("Implications", nc.WHY_MATTERS_TITLE)
    st.markdown(
        f'<p class="section-intro" style="margin-bottom:0;">{nc.WHY_MATTERS_BODY}</p>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)


def render_policy_implications() -> None:
    render_section_header("Recommendations", nc.POLICY_SECTION_TITLE)
    cols = st.columns(4, gap="medium")
    for col, card in zip(cols, nc.POLICY_CARDS):
        with col:
            st.markdown(
                f"""
<div class="policy-card">
  <h4>{card["title"]}</h4>
  <p>{card["text"]}</p>
</div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown(
        f'<p class="section-intro" style="margin-top:1.25rem;">{nc.POLICY_CLOSING}</p>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)


def render_limitations() -> None:
    bullets = "".join(f"<li>{b}</li>" for b in nc.LIMITATIONS_BULLETS)
    st.markdown(
        f"""
<div class="limitations-box">
  <h3>{nc.LIMITATIONS_TITLE}</h3>
  <ul>{bullets}</ul>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_methodology_expander(raw_shore: pd.DataFrame) -> None:
    if "SUM_Estimated_Latino_Population" not in raw_shore.columns:
        return
    with st.expander(nc.METHODOLOGY_EXPANDER_TITLE, expanded=False):
        st.markdown(
            """
- Rows are **access point × travel mode**; values are **summed** across rows, so people near many points can be **counted more than once**.
- **Served %** is the **mix** within that pooled total for each county and mode (walk / bike / drive).
- **White** is what’s **left over** after subtracting Hispanic/Latino and the other race group columns from the file’s **total population** field. If those pieces **add up to more than the total** after summing (common when pooling many buffers), that remainder is **set to zero**—so you may see **no White bar** for some counties/modes even though the county benchmark shows a large White share. That reflects **inconsistent totals in the pooled sums**, not a chart error.
            """
        )


def render_data_footer(
    by_mode: dict[str, pd.DataFrame],
    pops: dict[str, float],
    sources: dict[str, str],
    shore_label: str,
) -> None:
    with st.expander("Underlying data & downloads", expanded=False):
        st.caption(f"Shoreline source: `{shore_label}`")
        dl_county = st.selectbox("County for CSV export", options=list(COUNTIES), key="dl_county")
        rows = []
        for mode_key, mode_display in ACCESS_MODES:
            df = by_mode[mode_key].copy()
            df["access_mode"] = mode_display
            rows.append(df)
        combined = pd.concat(rows, ignore_index=True)
        combined_county = combined[combined["county"] == dl_county]
        st.dataframe(_category_display_df(combined_county), use_container_width=True, height=280)
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                label=f"Download CSV — {dl_county} (all modes)",
                data=_category_display_df(combined_county).to_csv(index=False).encode("utf-8"),
                file_name=f"acs_vs_shoreline_{_county_slug(dl_county)}_walk_bike_drive.csv",
                mime="text/csv",
            )
        with c2:
            st.download_button(
                label="Download CSV — all counties (all modes)",
                data=_category_display_df(combined).to_csv(index=False).encode("utf-8"),
                file_name="acs_vs_shoreline_all_counties_walk_bike_drive.csv",
                mime="text/csv",
            )
        with st.expander("ACS input filenames"):
            for c in COUNTIES:
                st.caption(f"{c} — `{sources[c]}`  ·  pop {pops[c]:,.0f}")


def main() -> None:
    st.set_page_config(
        page_title="Equitable Bay Shoreline Access",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_page_styles()

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

    shore_path = _resolve_shoreline_csv()
    raw_shore: pd.DataFrame | None = None
    shore_label = ""
    if shore_path is not None:
        raw_shore = load_shoreline_csv(shore_path)
        shore_label = shore_path.name

    if raw_shore is None:
        render_hero()
        render_study_summary()
        st.error(
            f"Missing shoreline CSV. Add **`{SHORELINE_DEFAULT_NAME}`** or **`Shoreline_Access_Data.csv`** "
            f"to `{_DATA}` (or a `Datasets` subfolder with the same files)."
        )
        st.markdown("### ACS 2024 benchmarks (reference)")
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

    try:
        by_mode = compare_all_modes(long_df, raw_shore)
    except ValueError as err:
        render_hero()
        render_study_summary()
        st.error(f"Could not parse shoreline file: {err}")
        return

    render_hero()
    render_study_summary()
    render_key_findings()

    if any(m["shore_pct"].isna().any() for m in by_mode.values()):
        st.info(
            "Some county × group cells have no shoreline estimate for a mode; those bars show **0%**."
        )

    render_county_examples(by_mode)

    # Residual White at 0% (pooled sums) — keep visible but out of the narrative flow
    _dq = []
    for c in COUNTIES:
        zm = _modes_with_zero_white_residual(by_mode, c)
        if zm:
            _dq.append(
                f"**{c}:** modeled **White** share is **0%** for {', '.join(zm)} "
                "(race/ethnicity columns sum above the pooled total; remainder capped at zero)."
            )
    if _dq:
        with st.expander("Data quality notes (modeled White residual)", expanded=False):
            st.markdown("\n\n".join(_dq))

    render_transport_section(by_mode)
    render_why_matters()
    render_policy_implications()
    render_limitations()

    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    render_methodology_expander(raw_shore)
    render_data_footer(by_mode, pops, sources, shore_label)


if __name__ == "__main__":
    main()
