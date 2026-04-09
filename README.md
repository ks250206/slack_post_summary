# slack_post_summary

Slack の自分の投稿を取得して、日報・週報用の Markdown にまとめるための小さなプロジェクトです。
Codex と Claude Code で使う skills / commands をこのプロジェクト内で管理しています。

## できること

- 自分の Slack 投稿を JST 基準で抽出
- `today` / `yesterday` / `day-before-yesterday` の日報向け集計
- `this-week` / `last-week` の週報向け集計
- `this-month` / `last-month` の月報向け集計
- `date YYYY-MM-DD` の指定日集計
- チャンネル単位で grouped JSON / YAML を出力
- grouped データから Markdown レポートを生成

## 前提

- `python3` 3.9 以上
- `.env` に `SLACK_TOKEN=...`
- Slack API に到達できるネットワーク

追加の Python ライブラリは不要です。標準ライブラリだけで動きます。

`.env` より環境変数 `SLACK_TOKEN` が優先されます。

## Slack Token

このプロジェクトは Slack Web API の `search.messages` を使います。Slack 公式ドキュメント上、この API には `search:read` scope を持つ `user token` が必要です。bot token 前提ではありません。

必要条件:

- token 種別: user token
- 必要 scope: `search:read`
- `.env` の設定例: `SLACK_TOKEN=xoxp-...`

注意:

- 取得結果は Slack 側の検索仕様に依存します。
- user token での検索結果は Slack UI の検索フィルタ設定の影響を受けます。
- DM や private channel をどこまで検索できるかは、その token に紐づく権限やユーザー同意に依存します。

参考:

- `search.messages`: https://docs.slack.dev/reference/methods/search.messages
- `search:read`: https://docs.slack.dev/reference/scopes/search.read/

## 構成

- [.env.example](/Users/ryojikanno/Downloads/slack_post_summary/.env.example): `.env` テンプレート
- [.gitignore](/Users/ryojikanno/Downloads/slack_post_summary/.gitignore): secrets / cache / report 出力の ignore 設定
- [slack_my_posts_grouped.sh](/Users/ryojikanno/Downloads/slack_post_summary/slack_my_posts_grouped.sh): collector の shell 入口
- [slack_my_posts_grouped.py](/Users/ryojikanno/Downloads/slack_post_summary/slack_my_posts_grouped.py): collector 本体
- [slack-post-report-md/scripts/generate_report_md.py](/Users/ryojikanno/Downloads/slack_post_summary/slack-post-report-md/scripts/generate_report_md.py): Markdown 生成本体
- [slack-post-report-md](/Users/ryojikanno/Downloads/slack_post_summary/slack-post-report-md): Codex skill 一式
- [CLAUDE.md](/Users/ryojikanno/Downloads/slack_post_summary/CLAUDE.md): Claude Code 向け project memory

## 使い方

`.env.example` をコピーして `.env` を用意する:

```bash
cp .env.example .env
```

```dotenv
SLACK_TOKEN=xoxp-...
```

collector を直接使う:

```bash
./slack_my_posts_grouped.sh today --format json
./slack_my_posts_grouped.sh this-week --format yaml
./slack_my_posts_grouped.sh this-month --format json
./slack_my_posts_grouped.sh date 2026-04-09 --format json
```

Markdown レポートを作る:

```bash
python3 ./slack-post-report-md/scripts/generate_report_md.py today
python3 ./slack-post-report-md/scripts/generate_report_md.py this-week --output reports/weekly.md
python3 ./slack-post-report-md/scripts/generate_report_md.py last-month --output reports/monthly.md
python3 ./slack-post-report-md/scripts/generate_report_md.py date 2026-04-09 --title "2026-04-09 日報"
```

## Agent Setup

### Claude Code

このリポジトリでは project-local command をすでに配置済みです。

- [CLAUDE.md](/Users/ryojikanno/Downloads/slack_post_summary/CLAUDE.md)
- [.claude/commands/slack-report.md](/Users/ryojikanno/Downloads/slack_post_summary/.claude/commands/slack-report.md)
- [.claude/commands/daily-report.md](/Users/ryojikanno/Downloads/slack_post_summary/.claude/commands/daily-report.md)
- [.claude/commands/weekly-report.md](/Users/ryojikanno/Downloads/slack_post_summary/.claude/commands/weekly-report.md)
- [.claude/commands/monthly-report.md](/Users/ryojikanno/Downloads/slack_post_summary/.claude/commands/monthly-report.md)

Claude Code では、このリポジトリを開くだけで project-local command が読み込まれます。追加インストールは不要です。

使い方:

```text
/slack-report this-week --output reports/weekly.md
/daily-report today --output reports/daily.md
/weekly-report last-week
/monthly-report this-month --output reports/monthly.md
```

補足:

- `CLAUDE.md` は project memory として自動読込されます。
- project-local custom command は `.claude/commands/*.md` に置きます。
- 現行の Claude Code では custom commands は skills に統合されていますが、`.claude/commands/` も引き続き動作します。

### Codex

このリポジトリ内の skill 本体は次です。

- [slack-post-report-md/SKILL.md](/Users/ryojikanno/Downloads/slack_post_summary/slack-post-report-md/SKILL.md)

ただし、この Codex 環境では project-local skill をこのリポジトリに置いただけでは自動登録されません。自動 discovery させるには `~/.codex/skills` 配下へ配置します。

推奨は symlink です。

```bash
mkdir -p ~/.codex/skills
ln -sfn "$PWD/slack-post-report-md" ~/.codex/skills/slack-post-report-md
```

登録後の使い方:

```text
Use $slack-post-report-md to generate a weekly Markdown report from my Slack posts.
```

補足:

- global に実体を複製したくない場合でも、symlink なら source はこのプロジェクト内のままです。
- `~/.codex/skills/slack-post-report-md` という名前で見えるようにしておくと、Codex 側の skill discovery に乗せやすいです。
- `.env` の自動検出も symlink 前提の方が安全です。skill ディレクトリを `~/.codex/skills` にコピーしてしまうと、project root の `.env` を見つけにくくなります。
- このプロジェクトでは `Path.cwd()` と script 実体の親ディレクトリ側の両方から `.env` を探索しますが、Codex 登録はコピーではなく symlink を推奨します。

## 特定プロジェクトへの登録

### Claude Code で特定プロジェクトだけに登録する

Claude Code は project-local の仕組みがあるので、そのプロジェクトの root に次を置けば十分です。

- `./CLAUDE.md`
- `./.claude/commands/*.md`
- 必要なら `./.claude/skills/<skill-name>/SKILL.md`

このリポジトリではすでにその形になっているので、Claude Code では「この repo を開く」だけで有効です。

別プロジェクトへ移す場合は、少なくとも次をコピーすれば同じ運用にできます。

- `CLAUDE.md`
- `.claude/commands/slack-report.md`
- `.claude/commands/daily-report.md`
- `.claude/commands/weekly-report.md`
- `.claude/commands/monthly-report.md`
- `slack-post-report-md/`

### Codex で特定プロジェクトだけに登録する

この環境の Codex では、repo 内に `SKILL.md` を置いただけでは自動登録されません。実用上は次のどちらかです。

#### 1. 常設 symlink

ひとまず使える状態にしたいだけなら、`~/.codex/skills` に symlink を張ります。

```bash
mkdir -p ~/.codex/skills
ln -sfn "$PWD/slack-post-report-md" ~/.codex/skills/slack-post-report-md
```

この方法は簡単ですが、他プロジェクトでも同じ skill 名が見える前提です。

#### 2. プロジェクトごとに切り替える

特定プロジェクトでだけ有効にしたいなら、そのプロジェクトに入ったときだけ symlink を張る運用にします。

例:

```bash
mkdir -p ~/.codex/skills
ln -sfn "/absolute/path/to/that-project/slack-post-report-md" \
  ~/.codex/skills/slack-post-report-md
```

別プロジェクトへ切り替えるときは、この symlink の向き先を張り替えます。

より厳密に project 単位で切り替えたいなら、direnv や shell function で project enter 時に張り替える運用にすると管理しやすいです。

## 補足

- 期間計算は JST ベースです。
- collector は `from:me` で Slack 検索します。
- Slack API 側のエラーはそのまま返します。
- Claude Code 用の project-local command は `.claude/commands/` にあります。
- 月報は `this-month` と `last-month` を使います。
