#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


JST = ZoneInfo("Asia/Tokyo")


@dataclass
class PeriodInfo:
    label: str
    start_date: str
    end_date: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Markdown daily, weekly, or monthly report from grouped Slack posts."
    )
    parser.add_argument(
        "mode",
        choices=[
            "today",
            "yesterday",
            "day-before-yesterday",
            "this-week",
            "last-week",
            "this-month",
            "last-month",
            "date",
        ],
        help="Report target period.",
    )
    parser.add_argument("date_value", nargs="?", help="Required when mode is 'date'.")
    parser.add_argument("--title", help="Override the generated H1 title.")
    parser.add_argument("--output", help="Write Markdown to this file instead of stdout.")
    parser.add_argument(
        "--no-links",
        action="store_true",
        help="Omit Slack permalinks from the Markdown output.",
    )
    parser.add_argument(
        "--source-script",
        default=str(Path(__file__).with_name("slack_my_posts_grouped.py")),
        help="Path to the grouped Slack collector script.",
    )
    args = parser.parse_args()
    if args.mode == "date" and not args.date_value:
        parser.error("mode 'date' requires YYYY-MM-DD")
    if args.mode != "date" and args.date_value:
        parser.error("date_value is only valid when mode is 'date'")
    return args


def compute_period(mode: str, date_value: str | None) -> PeriodInfo:
    now = datetime.now(JST)
    today = now.date()
    this_month_start = today.replace(day=1)

    if mode == "today":
        return PeriodInfo("daily", today.isoformat(), today.isoformat())
    if mode == "yesterday":
        day = today - timedelta(days=1)
        return PeriodInfo("daily", day.isoformat(), day.isoformat())
    if mode == "day-before-yesterday":
        day = today - timedelta(days=2)
        return PeriodInfo("daily", day.isoformat(), day.isoformat())
    if mode == "date":
        return PeriodInfo("daily", date_value, date_value)
    if mode == "this-week":
        start = today - timedelta(days=today.weekday())
        return PeriodInfo("weekly", start.isoformat(), today.isoformat())
    if mode == "last-week":
        this_week_start = today - timedelta(days=today.weekday())
        start = this_week_start - timedelta(days=7)
        end = this_week_start - timedelta(days=1)
        return PeriodInfo("weekly", start.isoformat(), end.isoformat())
    if mode == "this-month":
        return PeriodInfo("monthly", this_month_start.isoformat(), today.isoformat())
    if mode == "last-month":
        last_month_end = this_month_start - timedelta(days=1)
        start = last_month_end.replace(day=1)
        return PeriodInfo("monthly", start.isoformat(), last_month_end.isoformat())
    raise ValueError(f"Unsupported mode: {mode}")


def default_title(mode: str, period: PeriodInfo) -> str:
    if period.label == "daily":
        return f"Slack Daily Report - {period.start_date}"
    if period.label == "monthly":
        return f"Slack Monthly Report - {period.start_date} to {period.end_date}"
    return f"Slack Weekly Report - {period.start_date} to {period.end_date}"


def run_source_script(source_script: str, mode: str, date_value: str | None) -> list[dict]:
    cmd = [source_script, mode]
    if mode == "date":
        cmd.append(date_value)
    cmd.extend(["--format", "json"])

    try:
        completed = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
    except FileNotFoundError as exc:
        raise SystemExit(f"Source script not found: {exc.filename}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip()
        stdout = exc.stdout.strip()
        detail = stderr or stdout or f"exit status {exc.returncode}"
        raise SystemExit(f"Slack collection failed: {detail}") from exc

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Collector returned invalid JSON: {exc}") from exc

    if isinstance(payload, dict):
        error = payload.get("error") or payload.get("warning") or payload
        raise SystemExit(f"Slack API returned an error payload: {error}")
    if not isinstance(payload, list):
        raise SystemExit("Collector returned an unexpected JSON shape.")
    return payload


def blockquote(text: str) -> str:
    lines = text.splitlines() or [""]
    return "\n".join("> " + line if line else ">" for line in lines)


def split_timestamp(timestamp: str) -> tuple[str, str]:
    text = str(timestamp).strip()
    if " " in text:
        date_part, time_part = text.split(" ", 1)
        return date_part, time_part
    return text, text


def render_markdown(
    groups: list[dict], title: str, mode: str, period: PeriodInfo, include_links: bool
) -> str:
    generated_at = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST")
    lines: list[str] = [
        f"# {title}",
        "",
        f"- Mode: `{mode}`",
        f"- Period: `{period.start_date}` to `{period.end_date}` (JST)",
        f"- Generated: `{generated_at}`",
        "",
    ]

    total_posts = sum(len(group.get("posts", [])) for group in groups)
    lines.append(f"- Total posts: `{total_posts}`")
    lines.append("")

    if total_posts == 0:
        lines.append("No Slack posts found for the target period.")
        lines.append("")
        return "\n".join(lines)

    for group in groups:
        channel = group.get("channel") or "unknown"
        posts = group.get("posts", [])
        lines.append(f"## #{channel}")
        lines.append("")
        lines.append(f"Posts in this channel: `{len(posts)}`")
        lines.append("")

        posts_by_date: dict[str, list[dict]] = {}
        for post in posts:
            date_part, _ = split_timestamp(post.get("time", ""))
            posts_by_date.setdefault(date_part, []).append(post)

        for date_part, dated_posts in posts_by_date.items():
            lines.append(f"### {date_part}")
            lines.append("")

            for post in dated_posts:
                _, time_part = split_timestamp(post.get("time", ""))
                lines.append(f"#### {time_part}")
                lines.append("")
                lines.append(blockquote(str(post.get("text", "")).rstrip()))
                lines.append("")
                if include_links and post.get("permalink"):
                    lines.append(f"Permalink: {post['permalink']}")
                    lines.append("")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_output(markdown: str, output_path: str | None) -> None:
    if not output_path:
        sys.stdout.write(markdown)
        return

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(markdown, encoding="utf-8")


def main() -> None:
    args = parse_args()
    period = compute_period(args.mode, args.date_value)
    groups = run_source_script(args.source_script, args.mode, args.date_value)
    title = args.title or default_title(args.mode, period)
    markdown = render_markdown(
        groups=groups,
        title=title,
        mode=args.mode,
        period=period,
        include_links=not args.no_links,
    )
    write_output(markdown, args.output)


if __name__ == "__main__":
    main()
