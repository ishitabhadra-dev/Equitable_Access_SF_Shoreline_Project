"""
Static copy for the shoreline equity microsite.
Edit text here only; layout lives in streamlit_app.py.
"""

from __future__ import annotations

from typing import TypedDict


class FindingCard(TypedDict):
    title: str
    bullets: tuple[str, ...]
    takeaway: str


class CountyExample(TypedDict):
    caption: str
    takeaway_title: str
    takeaway_body: str


class PolicyCard(TypedDict):
    title: str
    text: str


# --- Hero ---
HERO_TITLE = "Equitable Access to the San Francisco Bay Shoreline"
HERO_SUBTITLE = (
    "How shoreline access varies across Bay Area counties, racial and ethnic groups, "
    "and transportation modes"
)
HERO_INTRO = (
    "This project examines whether public access to the San Francisco Bay shoreline is "
    "distributed equitably across communities. By comparing county population share with "
    "the share of shoreline access serving different racial and ethnic groups, this tool "
    "highlights where access appears proportional, expanded, or limited. The analysis "
    "focuses on environmental equity, mobility, and regional variation across the Bay Area."
)
HERO_BULLETS: tuple[str, ...] = (
    "Walk, bike, and drive access",
    "County-level comparisons",
    "Equity-focused interpretation",
)

# One short block between hero and headline findings (presentation-friendly)
STUDY_SUMMARY = (
    "This summary compares American Community Survey (ACS) 2024 county population shares to the "
    "racial and ethnic composition of populations represented in modeled shoreline access buffers, "
    "by walk, bike, and drive, across nine Bay Area shoreline counties. Interactive charts below "
    "support the headline findings."
)

# --- Key findings (exact wording from brief) ---
KEY_FINDINGS: tuple[FindingCard, ...] = (
    {
        "title": "White populations underrepresented",
        "bullets": (
            "Lower shoreline access than population share in several diverse counties",
            "Alameda County: 26% White in county vs about 10–11% in Bike/Drive access",
            "Solano County: 31% in county vs about 8–9% in Bike/Drive access",
            "Santa Clara County: 25% in county vs about 2% in Walk access",
        ),
        "takeaway": (
            "This suggests shoreline access is shaped more by spatial distribution and "
            "infrastructure than by overall county population share."
        ),
    },
    {
        "title": "Hispanic/Latino access often expands with mobility",
        "bullets": (
            "Higher access than population share in multiple counties under Bike/Drive views",
            "Contra Costa County: 28% in county vs about 39% in Bike/Drive access",
            "Napa County: 37% in county vs about 43% in Bike access",
            "Solano County: 31% in county vs about 32% in Bike access",
        ),
        "takeaway": (
            "Transportation options appear to substantially expand shoreline access for "
            "Hispanic/Latino communities in some counties."
        ),
    },
    {
        "title": "Asian populations show relatively proportional access",
        "bullets": (
            "Generally aligned with or slightly above county population share",
            "Santa Clara County: about 42% in county vs about 42–43% across modes",
            "San Mateo County: 32% in county vs about 37% in Walk access",
        ),
        "takeaway": (
            "In some parts of the South Bay and Peninsula, Asian populations appear to "
            "experience relatively balanced shoreline access."
        ),
    },
    {
        "title": "Black populations remain unevenly served",
        "bullets": (
            "Lower or only slightly improved access across modes",
            "Alameda County: 9% in county vs about 12–14% in Bike/Drive access",
            "Contra Costa County: 7% in county with uneven gains across modes",
            "Representation remains inconsistent across counties",
        ),
        "takeaway": (
            "Even where access improves slightly, disparities remain uneven and persistent."
        ),
    },
    {
        "title": "Walking access shows the largest gaps",
        "bullets": (
            "Walk access shows the biggest deviations from county population share",
            "Santa Clara County is the strongest example: White population drops from about "
            "25% in county to about 2% in Walk access",
            "Contra Costa and San Mateo also show uneven Walk distributions across groups",
            "Bike and Drive access tend to smooth out some of these differences",
        ),
        "takeaway": (
            "Mobility strongly shapes access, and Walk access is the most unequal mode in "
            "this analysis."
        ),
    },
    {
        "title": "Equity gaps persist overall",
        "bullets": (
            "Patterns vary by county and transportation mode",
            "Increased access in some settings does not translate to consistent equity",
            "Proximity alone does not ensure meaningful or reliable access",
        ),
        "takeaway": (
            "Modeled access should not be interpreted as full equity without considering "
            "quality, safety, and usability."
        ),
    },
)

# --- County examples ---
COUNTY_EXAMPLES_INTRO = (
    "County-level patterns show that shoreline access is not distributed the same way "
    "across the Bay Area. The strongest examples below illustrate how access changes by "
    "county, group, and transportation mode."
)

FEATURED_COUNTIES_DEFAULT: tuple[str, ...] = ("Alameda", "Contra Costa", "Santa Clara")

COUNTY_NARRATIVES: dict[str, CountyExample] = {
    "Alameda": {
        "caption": (
            "In Alameda County, White populations appear substantially underrepresented in "
            "shoreline access relative to their county population share, while Black "
            "populations show only modest improvement under Bike and Drive access."
        ),
        "takeaway_title": "Key takeaway",
        "takeaway_body": (
            "Access patterns in Alameda suggest that shoreline proximity alone does not "
            "produce equitable access across groups."
        ),
    },
    "Contra Costa": {
        "caption": (
            "In Contra Costa County, Hispanic/Latino populations show a major increase in "
            "Bike and Drive access relative to county population share, while Black "
            "representation remains uneven across modes."
        ),
        "takeaway_title": "Key takeaway",
        "takeaway_body": (
            "Transportation mode plays a major role in determining who can realistically "
            "benefit from shoreline access."
        ),
    },
    "Santa Clara": {
        "caption": (
            "In Santa Clara County, Asian populations appear close to proportional across "
            "access modes, while White populations show one of the sharpest declines in "
            "Walk access."
        ),
        "takeaway_title": "Key takeaway",
        "takeaway_body": (
            "Santa Clara highlights how sharply Walk-based access can diverge from county "
            "demographic patterns."
        ),
    },
}

# Generic caption for counties without bespoke narrative text
COUNTY_GENERIC_CAPTION = (
    "County population share (ACS 2024) compared to the mix of population represented in "
    "modeled shoreline access buffers, by walk, bike, and drive."
)

# --- Transportation mode ---
TRANSPORT_SECTION_TITLE = "Why Transportation Mode Matters"
TRANSPORT_INTRO = (
    "Transportation strongly shapes shoreline access. Walking access tends to produce the "
    "largest disparities, while Bike and Drive access expand who can realistically reach "
    "shoreline amenities. This means that access is not just about distance to the "
    "shoreline, but also about mobility infrastructure and connectivity."
)
TRANSPORT_INTERPRETATION = (
    "Across counties, Walk access often shows the largest gaps between county population "
    "share and served share. In contrast, Bike and Drive access tend to broaden access and "
    "reduce some of the sharpest disparities. This pattern is especially visible in "
    "counties such as Santa Clara, Napa, and Contra Costa."
)

# Callouts per mode tab (short labels near charts)
MODE_CALLOUTS: dict[str, str] = {
    "walk": "Largest walk gap",
    "bike": "Bike access expands reach",
    "drive": "Uneven across modes",
}

# --- Why this matters ---
WHY_MATTERS_TITLE = "Why This Matters"
WHY_MATTERS_BODY = (
    "Shoreline access is a public good, but proximity alone does not guarantee meaningful "
    "access. Transportation, infrastructure, and land use decisions shape which "
    "communities can actually reach and benefit from shoreline spaces. Understanding these "
    "patterns can help identify where future public investment should be directed to improve "
    "access more equitably across the Bay Area."
)

# --- Policy ---
POLICY_SECTION_TITLE = "Policy Implications for the Bay Area"
POLICY_CARDS: tuple[PolicyCard, ...] = (
    {
        "title": "Prioritize walkable access",
        "text": (
            "Walking access shows the largest equity gaps across counties. Future shoreline "
            "investments should prioritize sidewalks, crossings, and safe pedestrian routes "
            "connecting underserved neighborhoods to access points."
        ),
    },
    {
        "title": "Expand multimodal connections",
        "text": (
            "Because Bike and Drive access often broaden shoreline reach, regional planning "
            "should improve bike infrastructure, transit access, and multimodal connectivity "
            "to shoreline areas."
        ),
    },
    {
        "title": "Target persistently underserved communities",
        "text": (
            "Black populations remain unevenly served across counties and modes. "
            "Equity-focused planning should direct resources toward communities with "
            "persistent access gaps rather than assuming proximity alone is sufficient."
        ),
    },
    {
        "title": "Measure quality, not just proximity",
        "text": (
            "Being near a shoreline access point does not always mean access is meaningful. "
            "Future work should incorporate trail quality, maintenance, safety, and usability "
            "into shoreline equity planning."
        ),
    },
)
POLICY_CLOSING = (
    "For the Bay Area, equitable shoreline planning means improving not only where access "
    "points exist, but whether communities can realistically, safely, and consistently use them."
)

# --- Limitations ---
LIMITATIONS_TITLE = "Limitations"
LIMITATIONS_BULLETS: tuple[str, ...] = (
    "This analysis measures modeled access, not necessarily quality, safety, comfort, or cultural relevance.",
    "Being near a shoreline access point does not always mean that access is easy or meaningful.",
    "Some observed patterns may reflect broader housing, land use, and infrastructure patterns rather than shoreline planning alone.",
    "Future work should connect demographic access patterns to Bay Trail condition, maintenance, and community vulnerability.",
)

# --- Methodology expander (technical; unchanged substance) ---
METHODOLOGY_EXPANDER_TITLE = "How shoreline numbers are built (technical notes)"
