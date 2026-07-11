# Input Schema (profile.json)

The `generate_report.py` script reads a single JSON object. Every key is **optional**;
when omitted the generator substitutes a sensible placeholder so the report still renders.
Numeric arrays for charts use a 0–10 scale (radar/strength) or whatever unit is noted.

```jsonc
{
  "meta": {
    "title": "STUDY IN CANADA",                     // cover big title
    "subtitle": "COMPREHENSIVE SCHOLARSHIP STRATEGY REPORT",
    "prepared_for": "Alex Morgan",                  // cover "Prepared For"
    "date": "July 2026",
    "universities": ["UBC", "Toronto", "McGill"]     // listed under title on cover
  },

  "toc": [
    { "num": "1", "title": "Executive Summary", "desc": "Overview of findings" }
  ],

  "executive_summary": {
    "intro": "One or two objective paragraphs setting up the analysis.",
    "findings": [
      "Bullet finding 1 (2–4 lines).",
      "Bullet finding 2."
    ]
  },

  "profile": {
    "attributes": [ ["Full Name", "Alex Morgan"], ["Nationality", "Indian"] ],
    "comparison": {
      "headers": ["University", "Ranking", "Est. Cost/yr", "Key Requirement", "Notes"],
      "rows": [ ["UBC", "#34", "CAD 42k", "85% avg", "Strong support"] ]
    },
    "strength": {                                    // grouped bar chart
      "labels": ["Academics", "Research", "Leadership", "Test", "EC", "Need"],
      "you": [9, 8, 7, 8, 7, 9],
      "average": [7, 5, 6, 7, 6, 5]
    }
  },

  "landscape": {
    "paragraphs": ["Paragraph 1 …", "Paragraph 2 …"],
    "acceptance": { "labels": ["Flagship","Univ","Sponsor","RA","Charity"], "values": [7,18,24,41,33] }
  },

  "value_comparison": { "labels": ["Pearson","Killam","Waterloo","McGill","Lester"], "values": [90,75,60,55,95] },

  "past_winners": [
    {
      "heading": "Lester B. Pearson — Cohort Profile",
      "description": "Short context sentence.",
      "table": {
        "headers": ["Name", "Background", "Achievement", "Program"],
        "rows": [ ["R. Ahmed", "Public school", "Founded NGO", "UBC Sci"] ]
      }
    }
  ],

  "comparison": {
    "radar": { "labels": ["Academics","Research","Leadership","SAT","Community","Olympiads"],
               "you": [9,8,7,8,7,6], "typical": [7,6,6,7,6,5] },
    "table": { "headers": ["Dimension","You","Typical Winner"],
               "rows": [ ["Academics","9 / 10","7 / 10"] ] }
  },

  // EXACTLY 10 combinations. Each has a # | Scholarship Stack | Funding | Income | Gap | Rating table.
  "combinations": [
    {
      "heading": "1 · UBC Int'l Scholar + RA Stack",
      "description": "Flagship merit award stacked with a research assistantship.",
      "table": {
        "headers": ["#", "Scholarship Stack", "Funding", "Income", "Gap", "Rating"],
        "rows": [ ["1", "UBC Int'l + RA", "CAD 38k", "CAD 10k", "CAD 0", "★★★★★"] ]
      }
    }
  ],

  "feasibility": {
    "tiers": [
      { "name": "TIER 1 — Realistic Full Funding", "text": "Paragraph explaining the tier." }
    ],
    "verdict": { "highlights": ["Numbered honest verdict point 1.", "Point 2."] }
  },

  "roadmap": {
    "critical": [ {"h": "Publish or preprint research", "t": "Submit one manuscript before October."} ],
    "important": [ {"h": "Finalise shortlist", "t": "Confirm 3 primary universities by August."} ],
    "nice": [ {"h": "Attend virtual fairs", "t": "Build demonstrated interest."} ]
  },

  "timeline": [
    { "month": "July", "tasks": ["Finalise profile", "Shortlist 10 combinations"] },
    { "month": "August", "tasks": ["Secure referees", "Draft statements"] }
  ],

  "final_verdict": {
    "bets": [
      { "label": "BEST BET", "text": "Combination 4 — best ROI and reliable full funding." },
      { "label": "SAFEST BET", "text": "Combination 1 — prestigious and fully fundable." }
    ],
    "conclusion": "Motivational closing paragraph."
  }
}
```

## Running

```bash
python generate_report.py profile.json output.pdf     # from your JSON
python generate_report.py output.pdf                  # built-in EXAMPLE report
python generate_report.py                             # EXAMPLE -> scholarship_report.pdf
```

Star glyphs (★ ☆) render with the bundled Helvetica font. If a target system lacks the
glyph, swap to "5/5" style strings in the Rating column.
