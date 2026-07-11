# Scholarship Strategy Report Skill

[![skills.sh](https://skills.sh/b/piyushomanwar16/scholarship-strategy-report-skill)](https://skills.sh/piyushomanwar16/scholarship-strategy-report-skill)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An AI-agent **skill** that produces a professional, consulting-style scholarship /
study-abroad strategy report as a polished PDF. The agent gathers the applicant's
profile and preferences through a structured questionnaire, performs the analysis
(including **political/geopolitical risk** and benchmark comparisons against past
recipients), and renders a report with tables, a **radar chart** and **bar charts**
using the bundled Python generator.

➡️ **[View a generated sample report (PDF)](example-report.pdf)**

## What it produces

| # | Section | Content |
| --- | --- | --- |
| 1 | Cover | Title, subtitle, universities, prepared-for, date |
| 2 | Table of Contents | Numbered chapters with one-line descriptions |
| 3 | Executive Summary | Intro + key findings |
| 4 | Applicant Profile | Attribute table, university comparison, strength bar chart |
| 5 | Scholarship Landscape | Narrative + acceptance-rate bar chart |
| 6 | Scholarship Value Comparison | Horizontal bar chart |
| 7 | Past Recipient Analysis | Benchmark case-study tables |
| 8 | Comparative Analysis | Radar chart (you vs typical winner) + table |
| 9 | Funding Combinations | **Exactly 10** ranked, star-rated award stacks |
| 10 | Feasibility Analysis | Tier rankings + honest verdict |
| 11 | Improvement Roadmap | Critical / Important / Nice-to-have |
| 12 | 12-Month Timeline | Month-by-month checklist |
| 13 | Final Verdict | Best / Safest / Ranking / Self-funding / Stretch bets + conclusion |

## Install / Use

**Via skills.sh (Vercel) — works with 70+ agents (opencode, Claude Code, Cursor, Codex…):**
```bash
npx skills add piyushomanwar16/scholarship-strategy-report-skill
```

**Via agentskill.sh:**
```bash
npx @agentskill.sh/cli@latest install @piyushomanwar16/scholarship-strategy-report-skill
```
(If not yet indexed, submit the repo at https://agentskill.sh/submit)

**Via ClawHub (OpenClaw):** log in at https://clawhub.ai/import and import the repo
`piyushomanwar16/scholarship-strategy-report-skill`.

**Local / manual:** clone the repo and point your agent at `skills/scholarship-strategy-report/`.

## Run the generator directly

```bash
pip install -r skills/scholarship-strategy-report/requirements.txt
python skills/scholarship-strategy-report/generate_report.py \
       skills/scholarship-strategy-report/example_profile.json demo.pdf
```

When an agent uses the skill, it asks the applicant the questionnaire in `SKILL.md`,
researches the target country's scholarship landscape and geopolitical conditions,
fills `profile.json` per `INPUT_SCHEMA.md`, and runs the generator.

## Files

```
scholarship-strategy-report-skill/
├── skills/scholarship-strategy-report/
│   ├── SKILL.md            # agent instructions + questionnaire + JSON schema
│   ├── generate_report.py  # PDF layout engine (reportlab + matplotlib)
│   ├── INPUT_SCHEMA.md     # full JSON schema reference
│   ├── example_profile.json# complete runnable example
│   └── requirements.txt    # reportlab, matplotlib, numpy
├── example-report.pdf      # generated sample output
├── README.md
└── LICENSE
```

## License

MIT — free for anyone to use and adapt.
