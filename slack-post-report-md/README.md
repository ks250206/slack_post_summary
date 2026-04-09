# slack-post-report-md

このディレクトリ内で完結する、Slack 自分投稿の日報・週報・月報 Markdown 化用 skill です。

プロジェクト全体の概要は [../README.md](/Users/ryojikanno/Downloads/slack_post_summary/README.md) を参照してください。

## できること

- `today` / `yesterday` / `day-before-yesterday` の日報生成
- `this-week` / `last-week` の週報生成
- `this-month` / `last-month` の月報生成
- `date YYYY-MM-DD` の指定日レポート生成
- Slack 投稿をチャンネル単位でまとめて `.md` 出力

## 前提

- `python3`
- project root の `.env` に `SLACK_TOKEN=...`
- Slack API に到達できるネットワーク

Python 3.9 以上を前提にしています。日付計算と Slack 応答の整形は Python で処理するので、macOS 以外でも使えます。
`SLACK_TOKEN` 環境変数がある場合は `.env` よりそちらを優先します。

## Slack Token

この skill は Slack Web API の `search.messages` を使います。Slack 公式ドキュメント上、この API には `search:read` scope を持つ `user token` が必要です。

- token 種別: user token
- 必要 scope: `search:read`
- 推奨設定: project root `.env` に `SLACK_TOKEN=xoxp-...`

参考:

- `search.messages`: https://docs.slack.dev/reference/methods/search.messages
- `search:read`: https://docs.slack.dev/reference/scopes/search.read/

## 構成

- `SKILL.md`: Codex 用 skill 定義
- `agents/openai.yaml`: UI 向け metadata
- `scripts/slack_my_posts_grouped.py`: Slack 検索結果をチャンネル別 JSON/YAML に整形する本体
- `scripts/generate_report_md.py`: JSON を Markdown に変換

リポジトリ全体で残している shell 入口は、project root の `./slack_my_posts_grouped.sh` だけです。

## 使い方

`.env` の例:

```dotenv
SLACK_TOKEN=xoxp-...
```

日報を stdout に出す:

```bash
python3 ./scripts/generate_report_md.py today
```

週報をファイルに保存する:

```bash
python3 ./scripts/generate_report_md.py this-week --output reports/weekly.md
```

月報をファイルに保存する:

```bash
python3 ./scripts/generate_report_md.py this-month --output reports/monthly.md
```

指定日の日報をタイトル付きで保存する:

```bash
python3 ./scripts/generate_report_md.py date 2026-04-09 \
  --title "2026-04-09 日報" \
  --output reports/2026-04-09.md
```

Permalink を除外する:

```bash
python3 ./scripts/generate_report_md.py today --no-links
```

## 補足

- 期間計算は JST ベースです。
- `scripts/slack_my_posts_grouped.py` は `from:me` で Slack 検索します。
- `.env` が無い場合は環境変数 `SLACK_TOKEN` を見に行きます。
- Slack API や token が失敗すると、そのままエラーを返します。
- collector の shell 入口名は `slack_my_posts_grouped.sh` です。
- 月報は `this-month` と `last-month` を使います。
- Markdown では各チャンネル内を日付ごとにまとめ、その下に時刻ごとの投稿を並べます。
