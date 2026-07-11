#!/usr/bin/env python3
"""
Scholarship Strategy Report Generator
=====================================

Renders a professional, consulting-style 19-page scholarship / study-abroad
report PDF from a structured JSON input.

The agent (using the companion SKILL.md) is responsible for the *intelligence*:
asking the user questions, researching scholarships, comparing the applicant to
past recipients, and writing the narrative. This script is the *layout engine*:
it takes that structured content and produces a polished PDF with tables,
radar charts, bar charts and consistent professional styling.

Usage
-----
    python generate_report.py input.json output.pdf

If no input file is given, a built-in EXAMPLE dataset is rendered so the skill
is testable and serves as a template.

JSON schema (all keys optional; sensible placeholders are used when missing):
    meta:               { title, subtitle, prepared_for, date, universities:[str] }
    toc:                [ { num, title, desc } ]
    executive_summary:  { intro, findings:[str] }
    profile:            { attributes:[ [label,value] ],
                          comparison:{ headers:[], rows:[[]] },
                          strength:{ labels:[], you:[], average:[] } }
    landscape:          { paragraphs:[str], acceptance:{ labels:[], values:[] } }
    value_comparison:   { labels:[], values:[] }
    past_winners:       [ { heading, description, table:{ headers:[], rows:[[]] } } ]
    comparison:         { radar:{ labels:[], you:[], typical:[] },
                          table:{ headers:[], rows:[[]] } }
    combinations:       [ { heading, description, table:{ headers:[], rows:[[]] } } ]
    feasibility:        { tiers:[ { name, text } ], verdict:{ highlights:[str] } }
    roadmap:            { critical:[ {h,t} ], important:[ {h,t} ], nice:[ {h,t} ] }
    timeline:           [ { month, tasks:[str] } ]
    final_verdict:      { bets:[ { label, text } ], conclusion }

Star ratings in table cells are written as text, e.g. "★★★★☆".
"""

import json
import math
import os
import shutil
import sys
import tempfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# --------------------------------------------------------------------------- #
# Palette & typography (professional consulting report)
# --------------------------------------------------------------------------- #
NAVY = colors.HexColor("#1F3864")
NAVY_LIGHT = colors.HexColor("#2E5496")
GRAY = colors.HexColor("#595959")
LIGHT_GRAY = colors.HexColor("#D9D9D9")
ROW_ALT = colors.HexColor("#F2F4F8")
WHITE = colors.white
ACCENT = colors.HexColor("#C00000")

PAGE_W, PAGE_H = letter
MARGIN = 0.9 * inch

FONT = "Helvetica"
FONT_B = "Helvetica-Bold"


def styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("CoverTitle", parent=ss["Title"], fontName=FONT_B,
                          fontSize=30, textColor=NAVY, leading=34, alignment=TA_CENTER, spaceAfter=6))
    ss.add(ParagraphStyle("CoverSub", parent=ss["Normal"], fontName=FONT,
                          fontSize=15, textColor=GRAY, leading=20, alignment=TA_CENTER))
    ss.add(ParagraphStyle("CoverMeta", parent=ss["Normal"], fontName=FONT,
                          fontSize=11, textColor=colors.black, leading=16, alignment=TA_CENTER))
    ss.add(ParagraphStyle("H1", parent=ss["Heading1"], fontName=FONT_B,
                          fontSize=19, textColor=NAVY, spaceBefore=4, spaceAfter=10, leading=23))
    ss.add(ParagraphStyle("H2", parent=ss["Heading2"], fontName=FONT_B,
                          fontSize=14, textColor=NAVY_LIGHT, spaceBefore=8, spaceAfter=6, leading=18))
    ss.add(ParagraphStyle("Body", parent=ss["Normal"], fontName=FONT,
                          fontSize=11, textColor=colors.black, leading=16, alignment=TA_JUSTIFY, spaceAfter=6))
    ss.add(ParagraphStyle("MyBullet", parent=ss["Normal"], fontName=FONT,
                          fontSize=11, textColor=colors.black, leading=16, leftIndent=14, spaceAfter=4, bulletIndent=2))
    ss.add(ParagraphStyle("Cell", parent=ss["Normal"], fontName=FONT,
                          fontSize=9.5, textColor=colors.black, leading=13))
    ss.add(ParagraphStyle("CellH", parent=ss["Normal"], fontName=FONT_B,
                          fontSize=9.5, textColor=WHITE, leading=13))
    ss.add(ParagraphStyle("TOCEntry", parent=ss["Normal"], fontName=FONT,
                          fontSize=12, textColor=colors.black, leading=20))
    ss.add(ParagraphStyle("TOCNum", parent=ss["Normal"], fontName=FONT_B,
                          fontSize=12, textColor=NAVY, leading=20))
    ss.add(ParagraphStyle("VerdictBig", parent=ss["Normal"], fontName=FONT_B,
                          fontSize=16, textColor=ACCENT, alignment=TA_CENTER, leading=20))
    ss.add(ParagraphStyle("Small", parent=ss["Normal"], fontName=FONT,
                          fontSize=9, textColor=GRAY, leading=12))
    return ss


SS = styles()


# --------------------------------------------------------------------------- #
# Chart helpers (matplotlib -> PNG)
# --------------------------------------------------------------------------- #
def _save(fig, path):
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def make_radar(labels, series, path, title=""):
    """series: list of (name, values 0-10, color)."""
    n = len(labels)
    angles = [i / float(n) * 2 * math.pi for i in range(n)]
    angles += angles[:1]
    fig = plt.figure(figsize=(5.2, 5.0))
    ax = plt.subplot(111, polar=True)
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)
    for name, values, color in series:
        vals = values + values[:1]
        ax.plot(angles, vals, color=color, linewidth=2)
        ax.fill(angles, vals, color=color, alpha=0.18)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"], fontsize=7, color="#888888")
    ax.set_ylim(0, 10)
    ax.grid(color="#CCCCCC", linewidth=0.8)
    if title:
        ax.set_title(title, fontsize=12, fontweight="bold", color="#1F3864", pad=14)
    _save(fig, path)


def make_bar(labels, values, path, title="", horizontal=False, color="#2E5496"):
    fig, ax = plt.subplots(figsize=(6.2, 3.4) if not horizontal else (6.2, 3.8))
    if horizontal:
        bars = ax.barh(labels, values, color=color)
        for b, v in zip(bars, values):
            ax.text(v + max(values) * 0.01, b.get_y() + b.get_height() / 2,
                    f"{v}", va="center", fontsize=9, color="#333333")
        ax.invert_yaxis()
    else:
        bars = ax.bar(labels, values, color=color)
        for b, v in zip(bars, values):
            ax.text(b.get_x() + b.get_width() / 2, v + max(values) * 0.01,
                    f"{v}", ha="center", fontsize=9, color="#333333")
    ax.set_title(title, fontsize=12, fontweight="bold", color="#1F3864", pad=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=9)
    plt.tight_layout()
    _save(fig, path)


def make_grouped_bar(labels, groups, path, title=""):
    """groups: list of (name, values, color)."""
    import numpy as np
    n = len(labels)
    x = np.arange(n)
    width = 0.8 / len(groups)
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for i, (name, values, color) in enumerate(groups):
        ax.bar(x + i * width, values, width, label=name, color=color)
    ax.set_xticks(x + width * (len(groups) - 1) / 2)
    ax.set_xticklabels(labels, fontsize=8.5, rotation=15, ha="right")
    ax.set_title(title, fontsize=12, fontweight="bold", color="#1F3864", pad=10)
    ax.legend(fontsize=8, frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    _save(fig, path)


# --------------------------------------------------------------------------- #
# Table helpers
# --------------------------------------------------------------------------- #
def styled_table(headers, rows, col_widths=None, align_left_cols=None):
    data = [[Paragraph(str(h), SS["CellH"]) for h in headers]]
    for r in rows:
        data.append([Paragraph(str(c), SS["Cell"]) for c in r])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), FONT_B),
        ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    t.setStyle(TableStyle(style))
    return t


def two_col_table(rows, label_w=1.7 * inch):
    data = [[Paragraph(str(k), SS["CellH"]), Paragraph(str(v), SS["Cell"])] for k, v in rows]
    t = Table(data, colWidths=[label_w, PAGE_W - 2 * MARGIN - label_w])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), NAVY),
        ("TEXTCOLOR", (0, 0), (0, -1), WHITE),
        ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def section_header(num, title):
    return Paragraph(f'<font color="#1F3864"><b>{num}. {title}</b></font>' if num else f'<b>{title}</b>', SS["H1"])


def bullets(items):
    return [Paragraph(f"&bull;&nbsp;&nbsp;{it}", SS["MyBullet"]) for it in items]


# --------------------------------------------------------------------------- #
# Page furniture
# --------------------------------------------------------------------------- #
def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LIGHT_GRAY)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 0.6 * inch, PAGE_W - MARGIN, 0.6 * inch)
    canvas.setFont(FONT, 8)
    canvas.setFillColor(GRAY)
    canvas.drawString(MARGIN, 0.42 * inch, "Confidential — Scholarship Strategy Report")
    canvas.drawRightString(PAGE_W - MARGIN, 0.42 * inch, f"Page {doc.page}")
    canvas.restoreState()


def _cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 0.35 * inch, PAGE_W, 0.35 * inch, fill=1, stroke=0)
    canvas.rect(0, 0, PAGE_W, 0.35 * inch, fill=1, stroke=0)
    canvas.restoreState()


# --------------------------------------------------------------------------- #
# Defaults / example data
# --------------------------------------------------------------------------- #
def example_data():
    return {
        "meta": {
            "title": "STUDY IN CANADA",
            "subtitle": "COMPREHENSIVE SCHOLARSHIP STRATEGY REPORT",
            "prepared_for": "Alex Morgan",
            "date": "July 2026",
            "universities": ["University of Toronto", "UBC", "McGill University", "University of Waterloo"],
        },
        "toc": [
            {"num": "1", "title": "Executive Summary", "desc": "Overview of findings and strategy"},
            {"num": "2", "title": "Applicant Profile", "desc": "Strengths, attributes and benchmarking"},
            {"num": "3", "title": "Scholarship Landscape", "desc": "Costs, coverage and competition"},
            {"num": "4", "title": "Past Recipient Analysis", "desc": "Benchmark case studies"},
            {"num": "5", "title": "Comparative Analysis", "desc": "You vs the typical winner"},
            {"num": "6", "title": "Funding Combinations", "desc": "10 fully-funded pathways ranked"},
            {"num": "7", "title": "Feasibility Analysis", "desc": "Tier rankings and honest verdict"},
            {"num": "8", "title": "Improvement Roadmap", "desc": "Critical, important, nice-to-have"},
            {"num": "9", "title": "12-Month Timeline", "desc": "Month-by-month action plan"},
            {"num": "10", "title": "Final Verdict", "desc": "Best bets and recommendations"},
        ],
        "executive_summary": {
            "intro": "This report evaluates 10 fully-funded and substantially-funded scholarship pathways for the applicant's "
                     "targeted graduate studies in Canada. Findings combine the applicant's academic and leadership profile with "
                     "current scholarship availability, geopolitical stability of host regions, and benchmark data from past recipients.",
            "findings": [
                "The applicant's research output and leadership positioning place them in the top quartile versus the typical "
                "awardee for mid-tier national scholarships, but below the threshold for the most selective flagship awards.",
                "Full funding is realistically achievable at 4 of the 10 combinations when combined with on-campus assistantships "
                "and external charity sponsors, reducing the net gap to under CAD 8,000 in the strongest case.",
                "Geopolitical and visa conditions in the target country are currently stable, with no advisory-level disruptions "
                "affecting student permit processing for the applicant's nationality.",
                "The single highest-leverage improvement is a peer-reviewed publication or preprint before the October deadline, "
                "which materially shifts tier-1 eligibility.",
            ],
        },
        "profile": {
            "attributes": [
                ["Full Name", "Alex Morgan"],
                ["Nationality", "Indian"],
                ["Current Location", "Bengaluru, India"],
                ["Age", "21"],
                ["Education", "B.Tech, Computer Science (expected 2027)"],
                ["GPA / Percentage", "9.2 CGPA (94%)"],
                ["Test Scores", "IELTS 7.5; SAT 1480"],
                ["Financial Need", "High — family income below national median"],
                ["Part-time Capacity", "Up to 20 hrs/week on-campus"],
            ],
            "comparison": {
                "headers": ["University", "Ranking", "Est. Cost/yr", "Key Requirement", "Notes"],
                "rows": [
                    ["UBC", "#34", "CAD 42k", "85% avg + research", "Strong int'l support"],
                    ["Toronto", "#21", "CAD 48k", "Competitive + IELTS 7", "High cost, high prestige"],
                    ["McGill", "#30", "CAD 40k", "Strong EC + grades", "Bilingual advantage"],
                    ["Waterloo", "#112", "CAD 38k", "Cohort + co-op", "Best ROI via co-op"],
                ],
            },
            "strength": {
                "labels": ["Academics", "Research", "Leadership", "Test Scores", "Extracurricular", "Need"],
                "you": [9, 8, 7, 8, 7, 9],
                "average": [7, 5, 6, 7, 6, 5],
            },
        },
        "landscape": {
            "paragraphs": [
                "International graduate study in Canada carries an average all-in cost of CAD 38,000–52,000 per year including "
                "tuition, housing and living expenses. Fully-funded awards typically cover tuition plus a living stipend, while "
                "partial awards cover 30–70% of tuition and require the applicant to close the remaining gap through assistantships "
                "or personal means.",
                "Competition is intensifying: flagship national awards receive 8–15x more applicants than available slots, whereas "
                "university-specific and sponsor-linked awards show markedly higher conversion rates for well-matched profiles. "
                "Strategic stacking of a partial scholarship with a research assistantship is the most reliable path to full funding.",
                "Geopolitical conditions in Canada remain favourable for international students, with stable permit processing and "
                "no active travel advisories affecting the applicant's nationality. Currency volatility against the home currency "
                "is the primary financial risk and is reflected in the gap analysis below.",
            ],
            "acceptance": {"labels": ["Flagship", "Univ Merit", "Sponsor", "Assistantship", "Charity"],
                           "values": [7, 18, 24, 41, 33]},
        },
        "value_comparison": {"labels": ["Pearson", "Killam", "Waterloo P.", "McGill M.", "Lester B."],
                             "values": [90, 75, 60, 55, 95]},
        "past_winners": [
            {"heading": "Lester B. Pearson Scholars — Cohort Profile",
             "description": "Flagship undergraduate-focused award; winners share exceptional leadership and community impact.",
             "table": {"headers": ["Name", "Background", "Achievement", "Program"],
                       "rows": [
                           ["R. Ahmed", "Public school, rural", "Founded 3 NGOs, 12k beneficiaries", "UBC Sci"],
                           ["M. Chen", "IB 43", "Int'l Olympiad silver", "Toronto Eng"],
                           ["S. Okoro", "Refugee background", "Youth parliament leader", "McGill Arts"],
                       ]}},
            {"heading": "Killam Fellows — Graduate Benchmark",
             "description": "Research-intensive graduate award favouring publications and measurable impact.",
             "table": {"headers": ["Name", "Background", "Achievement", "Program"],
                       "rows": [
                           ["T. Singh", "BTech, 2 papers", "Open-source, 40k users", "Waterloo CS"],
                           ["L. Park", "MSc, 1 patent", "Lab leadership", "Toronto Bio"],
                       ]}},
        ],
        "comparison": {
            "radar": {"labels": ["Academics", "Research", "Leadership", "SAT", "Community", "Olympiads"],
                      "you": [9, 8, 7, 8, 7, 6],
                      "typical": [7, 6, 6, 7, 6, 5]},
            "table": {"headers": ["Dimension", "You", "Typical Winner"],
                      "rows": [
                          ["Academics", "9 / 10", "7 / 10"],
                          ["Research", "8 / 10", "6 / 10"],
                          ["Leadership", "7 / 10", "6 / 10"],
                          ["SAT / Equivalent", "1480", "1380"],
                          ["Community", "7 / 10", "6 / 10"],
                          ["Olympiads", "6 / 10", "5 / 10"],
                      ]},
        },
        "combinations": [
            {"heading": "1 · UBC Int'l Scholar + RA Stack",
             "description": "Flagship merit award stacked with a research assistantship to approach full funding.",
             "table": {"headers": ["#", "Scholarship Stack", "Funding", "Income", "Gap", "Rating"],
                       "rows": [
                           ["1", "UBC Int'l + RA", "CAD 38k", "CAD 10k", "CAD 0", "★★★★★"],
                           ["2", "UBC Int'l only", "CAD 25k", "CAD 4k", "CAD 13k", "★★★★☆"],
                       ]}},
            {"heading": "2 · Toronto Fellowship + Charity Sponsor",
             "description": "Prestige pathway; charity sponsor closes the high-cost gap.",
             "table": {"headers": ["#", "Scholarship Stack", "Funding", "Income", "Gap", "Rating"],
                       "rows": [
                           ["1", "Toronto Fellow + Sponsor", "CAD 44k", "CAD 8k", "CAD 0", "★★★★★"],
                           ["2", "Toronto Fellow only", "CAD 30k", "CAD 6k", "CAD 18k", "★★★☆☆"],
                       ]}},
            {"heading": "3 · McGill Entrance + Needs Bursary",
             "description": "Strong fit for high-need, high-EC profiles.",
             "table": {"headers": ["#", "Scholarship Stack", "Funding", "Income", "Gap", "Rating"],
                       "rows": [
                           ["1", "McGill Entrance + Bursary", "CAD 36k", "CAD 6k", "CAD 0", "★★★★☆"],
                           ["2", "McGill Entrance only", "CAD 22k", "CAD 5k", "CAD 13k", "★★★☆☆"],
                       ]}},
            {"heading": "4 · Waterloo Co-op + Scholarship",
             "description": "Best ROI; co-op earnings materially reduce net cost.",
             "table": {"headers": ["#", "Scholarship Stack", "Funding", "Income", "Gap", "Rating"],
                       "rows": [
                           ["1", "Waterloo Pres + Co-op", "CAD 30k", "CAD 15k", "CAD 0", "★★★★★"],
                           ["2", "Waterloo Pres only", "CAD 18k", "CAD 6k", "CAD 14k", "★★★★☆"],
                       ]}},
            {"heading": "5 · Killam Graduate Fellowship",
             "description": "Research-intensive; requires publications.",
             "table": {"headers": ["#", "Scholarship Stack", "Funding", "Income", "Gap", "Rating"],
                       "rows": [
                           ["1", "Killam + TA", "CAD 40k", "CAD 8k", "CAD 0", "★★★★☆"],
                           ["2", "Killam only", "CAD 32k", "CAD 4k", "CAD 12k", "★★★☆☆"],
                       ]}},
            {"heading": "6 · Government Bilateral Award",
             "description": "Home-government funded; stable but competitive.",
             "table": {"headers": ["#", "Scholarship Stack", "Funding", "Income", "Gap", "Rating"],
                       "rows": [
                           ["1", "Gov Bilateral + RA", "CAD 35k", "CAD 9k", "CAD 0", "★★★★☆"],
                       ]}},
            {"heading": "7 · Private Company Sponsorship",
             "description": "Corporate-linked award with bonding obligation.",
             "table": {"headers": ["#", "Scholarship Stack", "Funding", "Income", "Gap", "Rating"],
                       "rows": [
                           ["1", "Tech Corp Sponsor", "CAD 28k", "CAD 8k", "CAD 6k", "★★★☆☆"],
                       ]}},
            {"heading": "8 · Charity / Foundation Grant",
             "description": "Need-based philanthropic funding.",
             "table": {"headers": ["#", "Scholarship Stack", "Funding", "Income", "Gap", "Rating"],
                       "rows": [
                           ["1", "Foundation Grant + TA", "CAD 30k", "CAD 7k", "CAD 3k", "★★★★☆"],
                       ]}},
            {"heading": "9 · Lester B. Pearson (Stretch)",
             "description": "Most selective; stretch target.",
             "table": {"headers": ["#", "Scholarship Stack", "Funding", "Income", "Gap", "Rating"],
                       "rows": [
                           ["1", "Pearson Full", "CAD 50k", "CAD 6k", "CAD 0", "★★★★★"],
                       ]}},
            {"heading": "10 · Self-Funded + Partial Merit",
             "description": "Safety net if awards fall through.",
             "table": {"headers": ["#", "Scholarship Stack", "Funding", "Income", "Gap", "Rating"],
                       "rows": [
                           ["1", "Partial Merit + Savings", "CAD 15k", "CAD 5k", "CAD 28k", "★★☆☆☆"],
                       ]}},
        ],
        "feasibility": {
            "tiers": [
                {"name": "TIER 1 — Realistic Full Funding",
                 "text": "Combinations 1, 2, 4 and 9 close the funding gap to zero when stacked with assistantships or sponsors. "
                         "These require the applicant's profile to remain on its current trajectory with one additional publication."},
                {"name": "TIER 2 — Strong Partial + Work",
                 "text": "Combinations 3, 5, 6 and 8 cover 70–90% of cost and rely on 15–20 hrs/week of on-campus income. "
                         "Net gaps stay under CAD 8,000."},
                {"name": "TIER 3 — Safety Net",
                 "text": "Combination 10 is the fallback: partial merit plus personal savings. Viable but leaves a meaningful gap "
                         "and should only be activated if Tier 1/2 options are exhausted."},
            ],
            "verdict": {"highlights": [
                "Full funding is achievable at 4 of 10 combinations with disciplined stacking and one preprint by October.",
                "The highest-risk assumption is permit/currency stability; both currently favour the applicant but should be re-checked quarterly.",
            ]},
        },
        "roadmap": {
            "critical": [
                {"h": "Publish or preprint research", "t": "Submit one manuscript to a peer-reviewed venue or arXiv before the October deadline."},
                {"h": "Secure one recommendation early", "t": "Lock in your strongest academic referee by August to avoid bottleneck."},
            ],
            "important": [
                {"h": "Finalise target shortlist", "t": "Confirm 3 primary and 2 stretch universities by end of August."},
                {"h": "Open permit file", "t": "Begin permit documentation in parallel with applications to absorb processing time."},
            ],
            "nice": [
                {"h": "Attend virtual fairs", "t": "Engage admissions sessions to build demonstrated interest."},
                {"h": "Language upskilling", "t": "Minor French exposure strengthens McGill and bilingual narratives."},
            ],
        },
        "timeline": [
            {"month": "July", "tasks": ["Finalise profile document", "Shortlist 10 combinations", "Begin manuscript draft"]},
            {"month": "August", "tasks": ["Secure referees", "Draft personal statements", "Open permit file"]},
            {"month": "September", "tasks": ["Submit manuscripts", "Complete applications", "Apply to charity sponsors"]},
            {"month": "October", "tasks": ["Final deadline submissions", "Follow up on aids", "Interview prep"]},
            {"month": "November", "tasks": ["Interview rounds", "Track outcomes"]},
            {"month": "December", "tasks": ["Receive decisions", "Compare net costs"]},
            {"month": "January", "tasks": ["Accept offer", "Finalise funding stack"]},
            {"month": "February", "tasks": ["Permit submission", "Housing search"]},
            {"month": "March", "tasks": ["Visa approval follow-up", "Travel booking"]},
            {"month": "April", "tasks": ["Pre-departure prep", "On-campus job applications"]},
            {"month": "May", "tasks": ["Arrival logistics", "Orientation"]},
            {"month": "June", "tasks": ["Program start", "RA/TA onboarding"]},
        ],
        "final_verdict": {
            "bets": [
                {"label": "BEST BET", "text": "Combination 4 — Waterloo Co-op + Scholarship: best ROI and reliable full funding via earnings."},
                {"label": "SAFEST BET", "text": "Combination 1 — UBC Int'l Scholar + RA: prestigious and fully fundable with current profile."},
                {"label": "BEST RANKING", "text": "Combination 2 — Toronto Fellowship + Sponsor: maximises institutional prestige."},
                {"label": "BEST SELF-FUNDING", "text": "Combination 10 — Partial Merit + Savings: dependable fallback."},
                {"label": "STRETCH BET", "text": "Combination 9 — Lester B. Pearson: highest reward, lowest probability; apply but do not rely on it."},
            ],
            "conclusion": "With one additional publication and disciplined stacking of assistantships and sponsors, the applicant can "
                          "achieve full or near-full funding at a top Canadian institution. The plan is realistic, time-bound and "
                          "resilient to current geopolitical conditions. Begin immediately — the October deadline is the pivot point.",
        },
    }


# --------------------------------------------------------------------------- #
# Build document
# --------------------------------------------------------------------------- #
def build(data, output_path):
    tmp = tempfile.mkdtemp(prefix="ssr_charts_")
    story = []
    avail_w = PAGE_W - 2 * MARGIN

    meta = data.get("meta", {})
    title = meta.get("title", "SCHOLARSHIP STRATEGY REPORT")
    subtitle = meta.get("subtitle", "COMPREHENSIVE ANALYSIS")
    prepared_for = meta.get("prepared_for", "—")
    date = meta.get("date", "")
    universities = meta.get("universities", [])

    # ---- Page 1: Cover ----
    story.append(Spacer(1, 1.6 * inch))
    story.append(Paragraph(title, SS["CoverTitle"]))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph(subtitle, SS["CoverSub"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="60%", thickness=1.5, color=NAVY, spaceAfter=0.3 * inch, hAlign="CENTER"))
    story.append(Spacer(1, 0.2 * inch))
    for u in universities:
        story.append(Paragraph(u, SS["CoverMeta"]))
        story.append(Spacer(1, 0.06 * inch))
    story.append(Spacer(1, 0.6 * inch))
    story.append(Paragraph(f"<b>Prepared For:</b> {prepared_for}", SS["CoverMeta"]))
    if date:
        story.append(Spacer(1, 0.08 * inch))
        story.append(Paragraph(date, SS["CoverMeta"]))
    story.append(PageBreak())

    # ---- Page 2: Table of Contents ----
    story.append(section_header("", "Table of Contents"))
    story.append(Spacer(1, 0.15 * inch))
    toc = data.get("toc", [])
    toc_rows = []
    for e in toc:
        num = e.get("num", "")
        t = e.get("title", "")
        d = e.get("desc", "")
        toc_rows.append([Paragraph(f"<b>{num}</b>" if num else "", SS["TOCNum"]),
                         Paragraph(f"<b>{t}</b>", SS["TOCEntry"]),
                         Paragraph(d, SS["Small"])])
    tt = Table(toc_rows, colWidths=[0.5 * inch, 2.6 * inch, avail_w - 3.1 * inch])
    tt.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LIGHT_GRAY),
    ]))
    story.append(tt)
    story.append(PageBreak())

    # ---- Page 3: Executive Summary ----
    story.append(section_header("1", "Executive Summary"))
    es = data.get("executive_summary", {})
    if es.get("intro"):
        story.append(Paragraph(es["intro"], SS["Body"]))
    story.append(Paragraph("<b>Key Findings</b>", SS["H2"]))
    for b in bullets(es.get("findings", [])):
        story.append(b)
    story.append(PageBreak())

    # ---- Page 4: Applicant Profile ----
    story.append(section_header("2", "Applicant Profile"))
    prof = data.get("profile", {})
    if prof.get("attributes"):
        story.append(Paragraph("<b>Profile Attributes</b>", SS["H2"]))
        story.append(two_col_table(prof["attributes"]))
        story.append(Spacer(1, 0.18 * inch))
    if prof.get("comparison"):
        c = prof["comparison"]
        story.append(Paragraph("<b>University Comparison</b>", SS["H2"]))
        ncols = len(c["headers"])
        story.append(styled_table(c["headers"], c["rows"], col_widths=[avail_w / ncols] * ncols))
        story.append(Spacer(1, 0.18 * inch))
    if prof.get("strength"):
        s = prof["strength"]
        story.append(Paragraph("Profile Strength vs Average Applicant", SS["H2"]))
        p = os.path.join(tmp, "strength.png")
        make_grouped_bar(s["labels"], [("You", s.get("you", []), "#1F3864"),
                                       ("Average", s.get("average", []), "#B0B7C3")],
                         p, title="Profile Strength (0–10)")
        story.append(Image(p, width=avail_w, height=avail_w * 0.52))
    story.append(PageBreak())

    # ---- Page 5: Scholarship Landscape ----
    story.append(section_header("3", "Scholarship Landscape"))
    land = data.get("landscape", {})
    for para in land.get("paragraphs", []):
        story.append(Paragraph(para, SS["Body"]))
    if land.get("acceptance"):
        a = land["acceptance"]
        story.append(Spacer(1, 0.1 * inch))
        p = os.path.join(tmp, "acceptance.png")
        make_bar(a["labels"], a["values"], p, title="Acceptance Rates by Award Type (%)", color="#2E5496")
        story.append(Image(p, width=avail_w * 0.92, height=avail_w * 0.92 * 0.55, hAlign="CENTER"))
    story.append(PageBreak())

    # ---- Page 6: Scholarship Value Comparison ----
    story.append(section_header("", "Scholarship Value Comparison"))
    vc = data.get("value_comparison", {})
    if vc.get("labels"):
        p = os.path.join(tmp, "value.png")
        make_bar(vc["labels"], vc["values"], p, title="Estimated Award Value (CAD '000)", horizontal=True, color="#1F3864")
        story.append(Image(p, width=avail_w * 0.9, height=avail_w * 0.9 * 0.6, hAlign="CENTER"))
    story.append(PageBreak())

    # ---- Page 7: Past Recipient Analysis ----
    story.append(section_header("4", "Past Recipient Analysis"))
    for pw in data.get("past_winners", []):
        story.append(Paragraph(pw.get("heading", "Case Study"), SS["H2"]))
        if pw.get("description"):
            story.append(Paragraph(pw["description"], SS["Body"]))
        t = pw.get("table", {})
        if t.get("headers"):
            ncols = len(t["headers"])
            cw = [avail_w * w for w in _fit_widths(ncols)]
            story.append(styled_table(t["headers"], t["rows"], col_widths=cw))
        story.append(Spacer(1, 0.2 * inch))
    story.append(PageBreak())

    # ---- Pages 8-9: Comparative Analysis ----
    story.append(section_header("5", "Comparative Analysis"))
    comp = data.get("comparison", {})
    if comp.get("radar"):
        r = comp["radar"]
        p = os.path.join(tmp, "radar.png")
        make_radar(r["labels"], [("You", r.get("you", []), "#1F3864"),
                                 ("Typical Winner", r.get("typical", []), "#C00000")], p,
                   title="You vs Typical Winner")
        story.append(Image(p, width=avail_w * 0.72, height=avail_w * 0.72 * 0.96, hAlign="CENTER"))
        story.append(Spacer(1, 0.12 * inch))
    if comp.get("table"):
        t = comp["table"]
        ncols = len(t["headers"])
        story.append(styled_table(t["headers"], t["rows"], col_widths=[avail_w / ncols] * ncols))
    story.append(PageBreak())

    # ---- Pages 10-?: Funding Combinations (10) ----
    story.append(section_header("6", "Funding Combinations"))
    story.append(Paragraph("Ten fully-funded and substantially-funded pathways, ranked and rated. "
                           "Star ratings reflect net funding reliability after stacking.", SS["Body"]))
    story.append(Spacer(1, 0.1 * inch))
    for combo in data.get("combinations", []):
        block = []
        block.append(Paragraph(combo.get("heading", "Combination"), SS["H2"]))
        if combo.get("description"):
            block.append(Paragraph(combo["description"], SS["Body"]))
        t = combo.get("table", {})
        if t.get("headers"):
            ncols = len(t["headers"])
            cw = [avail_w * w for w in _fit_widths(ncols, [0.5, 0.34, 0.16, 0.16, 0.16, 0.14])]
            block.append(styled_table(t["headers"], t["rows"], col_widths=cw))
        block.append(Spacer(1, 0.18 * inch))
        story.append(KeepTogether(block))
    story.append(PageBreak())

    # ---- Page: Feasibility Analysis ----
    story.append(section_header("7", "Feasibility Analysis"))
    feas = data.get("feasibility", {})
    for tier in feas.get("tiers", []):
        story.append(Paragraph(tier.get("name", "Tier"), SS["H2"]))
        story.append(Paragraph(tier.get("text", ""), SS["Body"]))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph("The Honest Verdict", SS["VerdictBig"]))
    story.append(Spacer(1, 0.1 * inch))
    for i, h in enumerate(feas.get("verdict", {}).get("highlights", []), 1):
        story.append(Paragraph(f"<b>{i}.</b>&nbsp; {h}", SS["MyBullet"]))
    story.append(PageBreak())

    # ---- Page: Improvement Roadmap ----
    story.append(section_header("8", "Improvement Roadmap"))
    rm = data.get("roadmap", {})
    for sec, label in [("critical", "Critical"), ("important", "Important"), ("nice", "Nice to Have")]:
        story.append(Paragraph(label, SS["H2"]))
        for item in rm.get(sec, []):
            story.append(Paragraph(f"&bull;&nbsp; <b>{item.get('h','')}.</b> {item.get('t','')}", SS["MyBullet"]))
        story.append(Spacer(1, 0.08 * inch))
    story.append(PageBreak())

    # ---- Page: Timeline ----
    story.append(section_header("9", "12-Month Timeline"))
    tl = data.get("timeline", [])
    rows = []
    for m in tl:
        tasks = "<br/>".join(f"&#9744; {t}" for t in m.get("tasks", []))
        rows.append([Paragraph(f"<b>{m.get('month','')}</b>", SS["Cell"]),
                     Paragraph(tasks, SS["Cell"])])
    tlt = Table(rows, colWidths=[1.3 * inch, avail_w - 1.3 * inch], repeatRows=1)
    tlt.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, -1), NAVY),
        ("TEXTCOLOR", (0, 0), (0, -1), WHITE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tlt)
    story.append(PageBreak())

    # ---- Page: Final Verdict ----
    story.append(section_header("10", "Final Verdict"))
    fv = data.get("final_verdict", {})
    for bet in fv.get("bets", []):
        story.append(Paragraph(f"<font color='#C00000'><b>{bet.get('label','')}</b></font>", SS["H2"]))
        story.append(Paragraph(bet.get("text", ""), SS["Body"]))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph("Final Verdict", SS["H1"]))
    story.append(Paragraph(fv.get("conclusion", ""), SS["Body"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY))
    story.append(Paragraph("End of report — generated by the Scholarship Strategy Report skill.", SS["Small"]))

    # ---- render ----
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN, bottomMargin=0.9 * inch,
                            title=title, author="Scholarship Strategy Report Skill")
    doc.build(story, onFirstPage=_cover, onLaterPages=_footer)
    shutil.rmtree(tmp, ignore_errors=True)


def _fit_widths(ncols, weights=None):
    if weights and len(weights) == ncols:
        return weights
    base = 1.0 / ncols
    return [base] * ncols


# --------------------------------------------------------------------------- #
def main():
    if len(sys.argv) >= 2 and os.path.exists(sys.argv[1]):
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            data = json.load(f)
        out = sys.argv[2] if len(sys.argv) >= 3 else "scholarship_report.pdf"
    else:
        if len(sys.argv) >= 2:
            out = sys.argv[1]
        else:
            out = "scholarship_report.pdf"
        data = example_data()
        print("No input JSON found — rendering built-in EXAMPLE report.")
    build(data, out)
    print(f"Report written to: {out}")


if __name__ == "__main__":
    main()
