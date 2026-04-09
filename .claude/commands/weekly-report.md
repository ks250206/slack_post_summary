---
description: Generate a weekly Markdown report from your own Slack posts in this project.
argument-hint: "[this-week|last-week] [--output path] [--title \"...\"] [--no-links]"
---

Generate a weekly Slack Markdown report with this project's bundled scripts.

Default to `this-week` when no period argument is provided.

Accepted period forms:

- `this-week`
- `last-week`

Rules:

1. If the user provides no arguments, run `this-week`.
2. Use `python3 ./slack-post-report-md/scripts/generate_report_md.py`.
3. Pass through any additional flags such as `--output`, `--title`, and `--no-links`.
4. If `SLACK_TOKEN` is missing or the Slack API returns an error, stop and report the exact problem.

Examples:

```bash
python3 ./slack-post-report-md/scripts/generate_report_md.py this-week
python3 ./slack-post-report-md/scripts/generate_report_md.py last-week --output reports/weekly.md
```

User arguments: `$ARGUMENTS`
