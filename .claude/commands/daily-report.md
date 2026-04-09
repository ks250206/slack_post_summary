---
description: Generate a daily Markdown report from your own Slack posts in this project.
argument-hint: "[today|yesterday|day-before-yesterday|date YYYY-MM-DD] [--output path] [--title \"...\"] [--no-links]"
---

Generate a daily Slack Markdown report with this project's bundled scripts.

Default to `today` when no period argument is provided.

Accepted period forms:

- `today`
- `yesterday`
- `day-before-yesterday`
- `date YYYY-MM-DD`

Rules:

1. If the user provides no arguments, run `today`.
2. Use `python3 ./slack-post-report-md/scripts/generate_report_md.py`.
3. Pass through any additional flags such as `--output`, `--title`, and `--no-links`.
4. If `SLACK_TOKEN` is missing or the Slack API returns an error, stop and report the exact problem.

Examples:

```bash
python3 ./slack-post-report-md/scripts/generate_report_md.py today
python3 ./slack-post-report-md/scripts/generate_report_md.py yesterday --output reports/daily.md
python3 ./slack-post-report-md/scripts/generate_report_md.py date 2026-04-09 --title "2026-04-09 日報"
```

User arguments: `$ARGUMENTS`
