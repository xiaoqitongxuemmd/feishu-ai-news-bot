from datetime import datetime
from datetime import timedelta
from datetime import timezone
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError

from .config import load_settings
from .feishu import get_tenant_access_token, send_interactive_card
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
    brief = build_brief(settings.llm_provider, settings.llm_api_key, settings.llm_model, items)
    token = get_tenant_access_token(settings.feishu_app_id, settings.feishu_app_secret)
    today = shanghai_now().strftime("%Y-%m-%d")
    send_interactive_card(
        token,
        settings.feishu_chat_id,
        f"AI News Brief | {today}",
        brief,
    )
    print(f"Sent brief with {len(items)} source items.")


if __name__ == "__main__":
    main()
