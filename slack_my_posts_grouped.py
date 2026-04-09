#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    from zoneinfo import ZoneInfo
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Python 3.9+ with zoneinfo support is required.") from exc


JST = ZoneInfo("Asia/Tokyo")
SLACK_SEARCH_URL = "https://slack.com/api/search.messages"


@dataclass
class Period:
    start_date: str
    end_date: str
    start_epoch: int
    end_epoch: int
    search_after: str
    search_before: str


def find_dotenv(search_roots: list[Path]) -> Path | None:
    seen: set[Path] = set()
    for root in search_roots:
        current = root.resolve()
        for candidate in [current, *current.parents]:
            if candidate in seen:
                continue
            seen.add(candidate)
            dotenv_path = candidate / ".env"
            if dotenv_path.is_file():
                return dotenv_path
    return None


def parse_dotenv(dotenv_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key] = value
    return values


def load_slack_token() -> str:
    if os.environ.get("SLACK_TOKEN"):
        return os.environ["SLACK_TOKEN"]

    dotenv_path = find_dotenv([Path.cwd(), Path(__file__).resolve().parent])
    if dotenv_path is None:
        raise SystemExit("Error: set SLACK_TOKEN or create .env with SLACK_TOKEN=...")

    dotenv_values = parse_dotenv(dotenv_path)
    token = dotenv_values.get("SLACK_TOKEN", "").strip()
    if not token:
        raise SystemExit(f"Error: {dotenv_path} does not contain SLACK_TOKEN")
    return token


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="slack_my_posts_grouped.sh",
        description=(
            "Fetch your own Slack posts, filter them in JST, and group them by channel. "
            "Runs on any OS with Python 3.9+."
        ),
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
        help="Report target period in JST.",
    )
    parser.add_argument("date_value", nargs="?", help="Required when mode is 'date'.")
    parser.add_argument(
        "--format",
        choices=["json", "yaml"],
        default="json",
        help="Output format. Defaults to json.",
    )
    return parser


def parse_args() -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args()
    if args.mode == "date" and not args.date_value:
        parser.error("mode 'date' requires YYYY-MM-DD")
    if args.mode != "date" and args.date_value:
        parser.error("date_value is only valid when mode is 'date'")
    return args


def parse_iso_date(value: str) -> datetime.date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SystemExit(f"Error: invalid date format: {value}") from exc


def start_of_day(day) -> datetime:
    return datetime.combine(day, time(0, 0, 0), JST)


def end_of_day(day) -> datetime:
    return datetime.combine(day, time(23, 59, 59), JST)


def compute_period(mode: str, date_value: str | None) -> Period:
    now = datetime.now(JST)
    today = now.date()
    this_month_start = today.replace(day=1)

    if mode == "today":
        start_day = today
        end_day = today
        start_dt = start_of_day(start_day)
        end_dt = now
    elif mode == "yesterday":
        start_day = today - timedelta(days=1)
        end_day = start_day
        start_dt = start_of_day(start_day)
        end_dt = end_of_day(end_day)
    elif mode == "day-before-yesterday":
        start_day = today - timedelta(days=2)
        end_day = start_day
        start_dt = start_of_day(start_day)
        end_dt = end_of_day(end_day)
    elif mode == "this-week":
        start_day = today - timedelta(days=today.weekday())
        end_day = today
        start_dt = start_of_day(start_day)
        end_dt = now
    elif mode == "last-week":
        this_week_start = today - timedelta(days=today.weekday())
        start_day = this_week_start - timedelta(days=7)
        end_day = this_week_start - timedelta(days=1)
        start_dt = start_of_day(start_day)
        end_dt = end_of_day(end_day)
    elif mode == "this-month":
        start_day = this_month_start
        end_day = today
        start_dt = start_of_day(start_day)
        end_dt = now
    elif mode == "last-month":
        last_month_end = this_month_start - timedelta(days=1)
        start_day = last_month_end.replace(day=1)
        end_day = last_month_end
        start_dt = start_of_day(start_day)
        end_dt = end_of_day(end_day)
    elif mode == "date":
        start_day = parse_iso_date(date_value)
        end_day = start_day
        start_dt = start_of_day(start_day)
        end_dt = end_of_day(end_day)
    else:  # pragma: no cover
        raise SystemExit(f"Error: unknown mode: {mode}")

    return Period(
        start_date=start_day.isoformat(),
        end_date=end_day.isoformat(),
        start_epoch=int(start_dt.timestamp()),
        end_epoch=int(end_dt.timestamp()),
        search_after=(start_day - timedelta(days=1)).isoformat(),
        search_before=(end_day + timedelta(days=1)).isoformat(),
    )


def fetch_search_page(token: str, query_text: str, page: int) -> dict:
    query = urlencode(
        {
            "query": query_text,
            "page": page,
            "count": 100,
            "sort": "timestamp",
            "sort_dir": "desc",
        }
    )
    request = Request(
        f"{SLACK_SEARCH_URL}?{query}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise SystemExit(f"Error: Slack API request failed with HTTP {exc.code}") from exc
    except URLError as exc:
        raise SystemExit(f"Error: failed to reach Slack API: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Error: Slack API returned invalid JSON: {exc}") from exc


def fetch_matches(token: str, period: Period) -> list[dict] | dict:
    query_text = f"from:me after:{period.search_after} before:{period.search_before}"
    first_payload = fetch_search_page(token, query_text, 1)
    if first_payload.get("ok") is not True:
        return first_payload

    messages = first_payload.get("messages", {})
    matches = list(messages.get("matches", []))
    pagination = messages.get("pagination", {})
    total_pages = int(pagination.get("page_count") or pagination.get("pages") or 1)

    for page in range(2, total_pages + 1):
        payload = fetch_search_page(token, query_text, page)
        if payload.get("ok") is not True:
            return payload
        matches.extend(payload.get("messages", {}).get("matches", []))

    return matches


def normalize_message(match: dict, period: Period) -> dict | None:
    ts_raw = str(match.get("ts", "0"))
    ts = int(ts_raw.split(".", 1)[0])
    if ts < period.start_epoch or ts > period.end_epoch:
        return None

    channel = match.get("channel", {}).get("name") or "unknown"
    time_str = datetime.fromtimestamp(ts, JST).strftime("%Y-%m-%d %H:%M:%S")
    return {
        "channel": channel,
        "time": time_str,
        "text": match.get("text", ""),
        "permalink": match.get("permalink", ""),
    }


def group_messages(matches: list[dict], period: Period) -> list[dict]:
    normalized = [
        message
        for message in (normalize_message(match, period) for match in matches)
        if message is not None
    ]
    normalized.sort(key=lambda item: (item["channel"], item["time"]))

    grouped: list[dict] = []
    current_channel = None
    current_posts: list[dict] = []

    for item in normalized:
        if item["channel"] != current_channel:
            if current_channel is not None:
                grouped.append({"channel": current_channel, "posts": current_posts})
            current_channel = item["channel"]
            current_posts = []

        current_posts.append(
            {
                "time": item["time"],
                "text": item["text"],
                "permalink": item["permalink"],
            }
        )

    if current_channel is not None:
        grouped.append({"channel": current_channel, "posts": current_posts})

    return grouped


def to_yaml(data, indent: int = 0) -> str:
    lines: list[str] = []
    pad = " " * indent

    if isinstance(data, list):
        if not data:
            return f"{pad}[]"
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}-")
                lines.append(to_yaml(item, indent + 2))
            else:
                lines.append(f"{pad}- {yaml_scalar(item)}")
        return "\n".join(lines)

    if isinstance(data, dict):
        if not data:
            return f"{pad}{{}}"
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.append(to_yaml(value, indent + 2))
            else:
                lines.append(f"{pad}{key}: {yaml_scalar(value)}")
        return "\n".join(lines)

    return f"{pad}{yaml_scalar(data)}"


def yaml_scalar(value) -> str:
    text = "" if value is None else str(value)
    return json.dumps(text, ensure_ascii=False)


def main() -> None:
    args = parse_args()
    token = load_slack_token()

    period = compute_period(args.mode, args.date_value)
    matches_or_error = fetch_matches(token, period)

    if isinstance(matches_or_error, dict):
        payload = matches_or_error
        output = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        grouped = group_messages(matches_or_error, period)
        if args.format == "json":
            output = json.dumps(grouped, ensure_ascii=False, indent=2)
        else:
            output = to_yaml(grouped)

    sys.stdout.write(output)
    if not output.endswith("\n"):
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
