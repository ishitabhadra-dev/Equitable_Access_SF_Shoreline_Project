"""
Reusable HTML/CSS blocks and copy for the public-facing presentation layer.
Edit strings and numbers here to tune demo messaging without touching chart logic.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# At a Glance — short headline stats (edit freely)
# ---------------------------------------------------------------------------
AT_A_GLANCE_INTRO = (
    "A quick read before the detailed findings: what this tool compares, and why walk, "
    "bike, and drive views matter."
)

# Each block: title, optional big_stat, body HTML or plain text, optional footnote
AT_A_GLANCE_BLOCKS: tuple[dict[str, str], ...] = (
    {
        "title": "What we compare",
        "stat": "9",
        "stat_label": "counties",
        "body": (
            "County population mix from the <strong>2024 American Community Survey</strong> "
            "side by side with who appears in <strong>modeled shoreline access buffers</strong>, "
            "for <strong>walk</strong>, <strong>bike</strong>, and <strong>drive</strong>."
        ),
    },
    {
        "title": "Walk often departs most from county share",
        "stat": "",
        "stat_label": "",
        "body": "",  # filled by icon row in renderer
        "use_walk_icons": "true",
    },
    {
        "title": "Three ways people reach the shore",
        "stat": "3",
        "stat_label": "modes",
        "body": (
            "<div style='display:flex;gap:10px;flex-wrap:wrap;margin-top:6px;'>"
            "<span style='background:#0f766e;color:#fff;padding:4px 12px;border-radius:4px;font-weight:600;font-size:0.95rem;'>Walk</span>"
            "<span style='background:#0e7490;color:#fff;padding:4px 12px;border-radius:4px;font-weight:600;font-size:0.95rem;'>Bike</span>"
            "<span style='background:#475569;color:#fff;padding:4px 12px;border-radius:4px;font-weight:600;font-size:0.95rem;'>Drive</span>"
            "</div><p style='margin:10px 0 0 0;color:#334155;font-size:0.95rem;line-height:1.5;'>"
            "Same shoreline points, different travel assumptions — so served populations can look different by mode.</p>"
        ),
    },
    {
        "title": "Built for policy conversations",
        "stat": "2024",
        "stat_label": "ACS year",
        "body": (
            "Use the sections below to move from <strong>headline patterns</strong> to "
            "<strong>county examples</strong> and full charts. Numbers are illustrative of "
            "regional equity questions, not site-level design standards."
        ),
    },
)

# Icon row: NYC-style “7 in 10” — here 7 of 10 slots emphasize “walk widens gaps” story
WALK_ICON_ROW_HEADLINE = "7 of 10"
WALK_ICON_ROW_SUB = (
    "Illustrative graphic: in most highlighted comparisons, <strong>walk</strong> access "
    "shows the <strong>largest spread</strong> from whole-county population share — "
    "see Key Findings and charts below."
)
WALK_ICON_FILLED = 7
WALK_ICON_TOTAL = 10

# ---------------------------------------------------------------------------
# Quick Visual Takeaways — large type + mini visuals (edit numbers to match your brief)
# ---------------------------------------------------------------------------
QUICK_TAKEAWAYS_INTRO = (
    "Four patterns to hold in mind before reading the full charts. "
    "(Percentages reflect the study narrative; confirm in charts for your selected county.)"
)

QUICK_TAKEAWAY_BLOCKS: tuple[dict[str, str], ...] = (
    {
        "heading": "White populations underrepresented",
        "big": "26% → ~11%",
        "sub": "Example: Alameda County — county White share vs. approximate Bike/Drive served mix.",
        "visual": "compare",  # renderer draws side-by-side bars
        "left_label": "County",
        "left_val": 26,
        "right_label": "Bike/Drive served",
        "right_val": 11,
        "sentence": (
            "In several diverse counties, White population share in modeled shoreline pools "
            "runs well below county population share."
        ),
    },
    {
        "heading": "Hispanic/Latino access often rises with mobility",
        "big": "+11 pts",
        "sub": "Example: Contra Costa — county share to approximate Bike/Drive served mix.",
        "visual": "arrow",
        "from_val": "28%",
        "to_val": "39%",
        "sentence": (
            "Bike and Drive views often broaden who appears in served populations relative to Walk."
        ),
    },
    {
        "heading": "Walk access shows the largest disparities",
        "big": "25% → 2%",
        "sub": "Example: Santa Clara — White county share vs. approximate Walk served share.",
        "visual": "compare",
        "left_label": "County",
        "left_val": 25,
        "right_label": "Walk served",
        "right_val": 2,
        "sentence": (
            "Walking assumptions surface the sharpest gaps for some groups — mobility matters as much as distance."
        ),
    },
    {
        "heading": "Access depends on mobility, not just proximity",
        "big": "3 modes",
        "sub": "Walk · Bike · Drive",
        "visual": "modes",
        "sentence": (
            "If served mix changes when you switch modes, infrastructure and connectivity — not only nearness to water — are shaping outcomes."
        ),
    },
)

# ---------------------------------------------------------------------------
# Transportation section — three mode cards (above full charts)
# ---------------------------------------------------------------------------
MODE_SUMMARY_CARDS: tuple[dict[str, str], ...] = (
    {
        "mode": "Walk",
        "color": "#0f766e",
        "headline": "Largest disparities",
        "text": (
            "Walking buffers often produce the biggest gaps between county population share "
            "and who is counted as served."
        ),
    },
    {
        "mode": "Bike",
        "color": "#0e7490",
        "headline": "Expands reach",
        "text": (
            "Bike access assumptions typically widen who can reach shoreline amenities on paper."
        ),
    },
    {
        "mode": "Drive",
        "color": "#475569",
        "headline": "Broadens access — not equity",
        "text": (
            "Drive extends geographic reach for many groups but does not, by itself, guarantee fair or safe use."
        ),
    },
)


def html_people_icon_row(filled: int, total: int, *, fill_color: str, empty_color: str) -> str:
    """NYC-style row of simple 'person' blocks (filled vs empty)."""
    parts: list[str] = []
    for i in range(total):
        c = fill_color if i < filled else empty_color
        parts.append(
            f'<span class="picon" style="background:{c};" title="{i+1}/{total}"></span>'
        )
    return (
        '<div class="picon-row" style="display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:12px 0;">'
        + "".join(parts)
        + "</div>"
    )


def html_at_a_glance_grid(blocks: tuple[dict[str, str], ...], walk_icon_html: str) -> str:
    """Four-panel grid for At a Glance section."""
    cells = []
    for b in blocks:
        if b.get("use_walk_icons") == "true":
            inner = (
                f'<p class="ag-stat" style="font-size:1.75rem;font-weight:700;color:#1e40af;margin:0 0 4px 0;">'
                f"{WALK_ICON_ROW_HEADLINE}</p>"
                f"<p style='margin:0 0 8px 0;color:#334155;font-size:0.92rem;'>groups / views where walk shows the widest spread</p>"
                f"{walk_icon_html}"
                f"<p style='margin:8px 0 0 0;font-size:0.88rem;color:#475569;line-height:1.45;'>{WALK_ICON_ROW_SUB}</p>"
            )
        else:
            stat_html = ""
            if b.get("stat"):
                stat_html = (
                    f'<p class="ag-stat" style="font-size:2.1rem;font-weight:700;color:#0f172a;margin:0;line-height:1;">'
                    f'{b["stat"]}'
                    f'<span style="font-size:0.95rem;font-weight:600;color:#64748b;margin-left:6px;">{b.get("stat_label", "")}</span></p>'
                )
            inner = stat_html + f'<p style="margin:10px 0 0 0;color:#334155;font-size:0.98rem;line-height:1.55;">{b["body"]}</p>'

        cells.append(
            f"""
<div class="ag-cell">
  <p class="ag-title">{b["title"]}</p>
  {inner}
</div>
            """
        )
    return (
        '<div class="ag-grid">'
        + "".join(cells)
        + "</div>"
    )


def html_quick_takeaway_block(block: dict[str, str]) -> str:
    """One takeaway card with heading, big stat, mini visual, sentence."""
    vis = block.get("visual", "")
    mini = ""
    if vis == "compare":
        lw, rw = float(block["left_val"]), float(block["right_val"])
        maxv = max(lw, rw, 1)
        lw_pct = min(100, 100 * lw / maxv)
        rw_pct = min(100, 100 * rw / maxv)
        mini = f"""
<div style="margin:12px 0;display:flex;gap:14px;align-items:flex-end;">
  <div style="flex:1;">
    <div style="font-size:0.8rem;font-weight:600;color:#0f172a;margin-bottom:4px;">{block["left_label"]}</div>
    <div style="height:72px;background:#e2e8f0;border-radius:4px;position:relative;">
      <div style="position:absolute;bottom:0;left:0;right:0;height:{lw_pct:.1f}%;background:#334155;border-radius:4px;"></div>
    </div>
    <div style="font-size:1.35rem;font-weight:700;color:#0f172a;margin-top:6px;">{lw:.0f}%</div>
  </div>
  <div style="flex:1;">
    <div style="font-size:0.8rem;font-weight:600;color:#0f172a;margin-bottom:4px;">{block["right_label"]}</div>
    <div style="height:72px;background:#e2e8f0;border-radius:4px;position:relative;">
      <div style="position:absolute;bottom:0;left:0;right:0;height:{rw_pct:.1f}%;background:#0f766e;border-radius:4px;"></div>
    </div>
    <div style="font-size:1.35rem;font-weight:700;color:#0f172a;margin-top:6px;">{rw:.0f}%</div>
  </div>
</div>
        """
    elif vis == "arrow":
        mini = f"""
<div style="margin:14px 0;display:flex;align-items:center;gap:12px;font-size:1.25rem;font-weight:700;color:#0f172a;">
  <span style="background:#f1f5f9;padding:8px 14px;border-radius:4px;border:1px solid #cbd5e1;">{block["from_val"]}</span>
  <span style="color:#0f766e;font-size:1.5rem;">→</span>
  <span style="background:#ecfdf5;padding:8px 14px;border-radius:4px;border:1px solid #6ee7b7;">{block["to_val"]}</span>
</div>
        """
    elif vis == "modes":
        mini = """
<div style="margin:12px 0;height:14px;border-radius:8px;overflow:hidden;display:flex;">
  <div style="flex:1;background:#0f766e;"></div>
  <div style="flex:1;background:#0e7490;"></div>
  <div style="flex:1;background:#475569;"></div>
</div>
<p style="margin:4px 0 0 0;font-size:0.78rem;color:#64748b;text-align:center;">Walk · Bike · Drive</p>
        """

    return f"""
<div class="qt-card">
  <p class="qt-heading">{block["heading"]}</p>
  <p class="qt-big">{block["big"]}</p>
  <p class="qt-sub">{block["sub"]}</p>
  {mini}
  <p class="qt-sentence">{block["sentence"]}</p>
</div>
    """


def html_mode_summary_cards(cards: tuple[dict[str, str], ...]) -> str:
    """Three columns: Walk / Bike / Drive summary for transport section."""
    cols = []
    for c in cards:
        cols.append(
            f"""
<div class="mode-sum-card" style="border-top:4px solid {c["color"]};">
  <p style="margin:0;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:#64748b;">{c["mode"]}</p>
  <p style="margin:8px 0 6px 0;font-size:1.05rem;font-weight:700;color:#0f172a;">{c["headline"]}</p>
  <p style="margin:0;font-size:0.92rem;color:#475569;line-height:1.5;">{c["text"]}</p>
</div>
            """
        )
    return '<div class="mode-sum-grid">' + "".join(cols) + "</div>"


def quick_takeaways_grid_html() -> str:
    """All Quick Visual Takeaway cards in one 2×2 grid."""
    parts = [html_quick_takeaway_block(dict(b)) for b in QUICK_TAKEAWAY_BLOCKS]
    return '<div class="qt-grid">' + "".join(parts) + "</div>"
