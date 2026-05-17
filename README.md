# Feishu News and Markets Bot

Daily Feishu bot for important news, AI/autonomous driving industry news, and A/H/US market analysis.

## Features

- Fetches important domestic/global news from the last 24 hours.
- Fetches domestic/global AI and autonomous driving industry news from the last 24 hours.
- Fetches A-share, Hong Kong, and US index market data only when the quote data is within the last 24 hours.
- Uses DeepSeek or OpenAI to create a Chinese brief with summaries and impact notes.
- Sends a Feishu interactive message card.
- Supports local runs and GitHub Actions scheduled runs.

## Project layout

```text
.
|-- .env.example
|-- .github/workflows/daily.yml
|-- pyproject.toml
|-- requirements.txt
|-- src/ai_news_bot/
|   |-- config.py
|   |-- feishu.py
|   |-- main.py
|   |-- markets.py
|   |-- news.py
|   `-- summarize.py
`-- tools/list_feishu_chats.py
```

## 1. Local setup

```powershell
cd E:\Project\feishu-ai-news-bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

## 2. Configure Feishu

```powershell
$env:FEISHU_APP_ID = "cli_xxx"
$env:FEISHU_APP_SECRET = "your_feishu_app_secret"
```

Get the target group chat ID:

```powershell
python .\tools\list_feishu_chats.py
```

Then set the target group:

```powershell
$env:FEISHU_CHAT_ID = "oc_xxx"
```

## 3. Configure DeepSeek

DeepSeek is the default recommended provider for this project.

```powershell
$env:LLM_PROVIDER = "deepseek"
$env:DEEPSEEK_API_KEY = "your_deepseek_api_key"
$env:DEEPSEEK_MODEL = "deepseek-chat"
```

The official DeepSeek API is OpenAI-compatible. This project uses:

```text
https://api.deepseek.com/chat/completions
```

## 4. Send one brief

```powershell
python -m ai_news_bot.main
```

## 5. Optional OpenAI configuration

```powershell
$env:LLM_PROVIDER = "openai"
$env:OPENAI_API_KEY = "your_openai_api_key"
$env:OPENAI_MODEL = "gpt-4.1-mini"
```

## 6. GitHub Actions deployment

After pushing this project to GitHub, add these secrets under `Settings -> Secrets and variables -> Actions`:

```text
FEISHU_APP_ID
FEISHU_APP_SECRET
FEISHU_CHAT_ID
LLM_PROVIDER
DEEPSEEK_API_KEY
DEEPSEEK_MODEL
```

`.github/workflows/daily.yml` runs at UTC 01:00, which is 09:00 in Asia/Shanghai.

## Notes

The current source layer uses RSS, Google News search feeds, and Yahoo Finance chart data. If markets are closed and the latest index data is older than 24 hours, the bot will not use stale quote data. The generated market section is general analysis, not personalized financial advice. For long-term stable use, extend it with internal feeds, a news API, RSSHub, exchange data providers, or paid media subscriptions.
