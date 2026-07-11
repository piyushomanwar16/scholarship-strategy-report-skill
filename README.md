# Scholarship Strategy Report Skill

An opencode/agent **skill** that produces a professional, consulting-style scholarship /
study-abroad strategy report as a polished PDF. The agent gathers the applicant's profile
and preferences through a structured questionnaire, performs the analysis (including
political/geopolitical risk and benchmark comparisons against past recipients), and renders
a 16–19 page report with tables, a radar chart and bar charts.

## What it produces

| Section | Content |
| --- | --- |
| 1 · Cover | Title, subtitle, universities, prepared-for, date |
| 2 · Table of Contents | Numbered chapters with one-line descriptions |
| 3 · Executive Summary | Intro + key findings |
| 4 · Applicant Profile | Attribute table, university comparison, strength bar chart |
| 5 · Scholarship Landscape | Narrative + acceptance-rate bar chart |
| 6 · Scholarship Value Comparison | Horizontal bar chart |
| 7 · Past Recipient Analysis | Benchmark case-study tables |
| 8 · Comparative Analysis | Radar chart (you vs typical winner) + table |
| 9 · Funding Combinations | **Exactly 10** ranked, star-rated award stacks |
| 10 · Feasibility Analysis | Tier rankings + honest verdict |
| 11 · Improvement Roadmap | Critical / Important / Nice-to-have |
| 12 · 12-Month Timeline | Month-by-month checklist |
| 13 · Final Verdict | Best/Safest/Ranking/Self-funding/Stretch bets + conclusion |

## Files

- `SKILL.md` — instructions for the agent (questionnaire, analysis steps, run command).
- `generate_report.py` — the PDF layout engine (reportlab + matplotlib). Accepts a JSON input.
- `INPUT_SCHEMA.md` — full JSON schema reference with examples.
- `example_profile.json` — a complete, runnable example dataset.
- `requirements.txt` — `reportlab`, `matplotlib`.

## Usage

```bash
pip install -r requirements.txt
python generate_report.py example_profile.json demo_report.pdf   # run the example
python generate_report.py profile.json  output.pdf              # real run
```

When invoked by an agent with this skill loaded, the agent will ask the applicant the
questionnaire in `SKILL.md`, research the target country's scholarship landscape and
geopolitical conditions, fill `profile.json` per `INPUT_SCHEMA.md`, and run the generator.

## License

MIT — free for anyone to use and adapt.
