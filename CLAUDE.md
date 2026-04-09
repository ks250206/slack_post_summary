# slack_post_summary

This repository contains a project-local Slack reporting workflow.

## Primary paths

- `./slack-post-report-md/scripts/slack_my_posts_grouped.py`
- `./slack-post-report-md/scripts/generate_report_md.py`

## Expectations

- Prefer the bundled project-local scripts over any global install.
- Generate reports in Markdown unless the user explicitly asks for JSON or YAML.
- Respect JST-based periods used by the bundled Python collector.
- Keep outputs inside this repository when the user asks to save files.
- Read `SLACK_TOKEN` from project root `.env` by default. If the shell environment already has `SLACK_TOKEN`, prefer that value.

## Common commands

```bash
python3 ./slack-post-report-md/scripts/generate_report_md.py today
python3 ./slack-post-report-md/scripts/generate_report_md.py this-week --output reports/weekly.md
```
