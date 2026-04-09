---
description: Generate a Markdown report from your own Slack posts using this project's bundled scripts.
argument-hint: "<today|yesterday|day-before-yesterday|this-week|last-week|this-month|last-month|date YYYY-MM-DD> [--output path] [--title \"...\"] [--no-links]"
---

Generate a project-local Slack Markdown report with the bundled scripts.

Use `python3 ./slack-post-report-md/scripts/generate_report_md.py` from the repository root.

Rules:

1. Preserve the user's arguments exactly: `$ARGUMENTS`
2. If the current working directory is not the repository root, first locate `slack-post-report-md/scripts/generate_report_md.py` in the current repository and use its absolute path.
3. Before running, confirm the script exists.
4. Run the report generator and show the resulting file path when `--output` is present.
5. If `--output` is absent, print the Markdown output in the terminal response.
6. If `SLACK_TOKEN` is missing or the Slack API returns an error, stop and report the exact problem.

Command:

```bash
python3 ./slack-post-report-md/scripts/generate_report_md.py $ARGUMENTS
```
