from datetime import datetime
from datetime import timedelta
from datetime import timezone
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError

from .config import load_settings
from .feishu import get_tenant_access_token, send_interactive_card
from .markets import fetch_market_quotes
from .news import fetch_news
from .summarize import build_brief


def shanghai_now() -> datetime:
    try:
        return datetime.now(ZoneInfo("Asia/Shanghai"))
    except ZoneInfoNotFoundError:
        return datetime.now(timezone(timedelta(hours=8)))


def main() -> None:
    settings = load_settings()
    items = fetch_news(settings.news_lookback_hours, settings.max_news_items)
    market_quotes = fetch_market_quotes()
    brief = build_brief(
        settings.llm_provider,
        settings.llm_api_key,
        settings.llm_model,
        items,
        market_quotes,
    )
    print(f"Generated brief length: {len(brief)} characters.")
    token = get_tenant_access_token(settings.feishu_app_id, settings.feishu_app_secret)
    today = shanghai_now().strftime("%Y-%m-%d")
    send_interactive_card(
        token,
        settings.feishu_chat_id,
        f"Daily News & Markets | {today}",
        brief,
    )
    print(f"Sent brief with {len(items)} news items and {len(market_quotes)} market quotes.")


if __name__ == "__main__":
    main()
