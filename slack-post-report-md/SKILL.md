---
name: slack-post-report-md
description: Generate daily, weekly, or monthly Markdown reports from your own Slack posts by using the bundled Python Slack collector and a Markdown renderer. Use when Codex needs to turn your Slack activity into a `.md` daily report, weekly report, monthly report, or date-specific status summary inside this project.
---

# Slack Post Report Md

Use this skill to produce project-local Markdown reports from your own Slack posts.

Keep the workflow simple:

1. Confirm that project root `.env` contains `SLACK_TOKEN=...` or that `SLACK_TOKEN` is set in the shell environment.
2. Run the bundled collector script to fetch grouped Slack posts as JSON.
3. Run the bundled Markdown renderer to create a readable daily, weekly, or monthly report.
4. Save the output as a `.md` file in the project directory the user wants.

## Project-Local Layout

- Use the scripts in this skill folder, not a global install.
- Treat `scripts/slack_my_posts_grouped.py` as the source of truth for Slack collection.
- Treat `scripts/generate_report_md.py` as the preferred entrypoint for Markdown output.

Resolve paths relative to the skill directory:

```bash
SKILL_DIR="/path/to/slack-post-report-md"
python3 "$SKILL_DIR/scripts/generate_report_md.py" today
```

## Commands

Collect grouped posts as JSON:

```bash
python3 ./scripts/slack_my_posts_grouped.py today --format json
python3 ./scripts/slack_my_posts_grouped.py last-week --format json
python3 ./scripts/slack_my_posts_grouped.py this-month --format json
python3 ./scripts/slack_my_posts_grouped.py date 2026-04-09 --format json
```

Generate Markdown directly:

```bash
python3 ./scripts/generate_report_md.py today
python3 ./scripts/generate_report_md.py this-week --output reports/weekly.md
python3 ./scripts/generate_report_md.py last-month --output reports/monthly.md
python3 ./scripts/generate_report_md.py date 2026-04-09 --title "2026-04-09 日報"
```

## Modes

- `today`: today's posts in JST
- `yesterday`: yesterday's posts in JST
- `day-before-yesterday`: the day before yesterday in JST
- `this-week`: from Monday 00:00 JST to now
- `last-week`: previous Monday 00:00 JST to Sunday 23:59:59 JST
- `this-month`: from the first day of the current month 00:00 JST to now
- `last-month`: from the first day of the previous month 00:00 JST to the last day of that month 23:59:59 JST
- `date YYYY-MM-DD`: one specific JST date

## Output Rules

- Start with an H1 title.
- Include the target period and a generated timestamp in JST.
- Group messages by channel.
- Preserve message text as readable block quotes.
- Include permalinks unless the user explicitly asks to omit them.
- If there are no posts, still emit a valid Markdown file with a short no-posts note.

## Environment Checks

Before running collection:

- Verify `python3` is available.
- Verify project root `.env` contains `SLACK_TOKEN=...`, or `SLACK_TOKEN` is available in the shell environment.

If the user asks for a report and no filename is specified, choose a clear local filename such as:

- `daily-report-YYYY-MM-DD.md`
- `weekly-report-YYYY-MM-DD-to-YYYY-MM-DD.md`
- `monthly-report-YYYY-MM-DD-to-YYYY-MM-DD.md`

## Resources

### scripts/

- `slack_my_posts_grouped.py`: collect your own Slack posts and group them by channel as JSON or YAML
- `generate_report_md.py`: render grouped JSON into Markdown
