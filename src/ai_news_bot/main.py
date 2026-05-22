from datetime import datetime
from datetime import timedelta
from datetime import timezone
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError

from .config import load_settings
from .feishu import get_tenant_access_token, send_interactive_card
from .markets import fetch_market_quotes
from .news import NewsItem
from .news import fetch_news
from .summarize import build_brief_part


NEWS_SECTIONS = {"Important Domestic News", "Important Global News"}
AI_SECTIONS = {"Domestic AI", "Global AI", "Domestic Autonomous Driving", "Global Autonomous Driving"}
MARKET_SECTIONS = {"Market News"}

BRIEF_PARTS = [
    (
        "国内国际新闻",
        "Important News",
        NEWS_SECTIONS,
        False,
        """
Cover Important Domestic News and Important Global News.
Select the most important items.
For each item include title, source/time, concise summary, why it matters, and link.
End with 2-3 concise observations.
""".strip(),
        2200,
    ),
    (
        "AI 与智能驾驶",
        "AI & Autonomous Driving",
        AI_SECTIONS,
        False,
        """
Cover Domestic AI, Global AI, Domestic Autonomous Driving, and Global Autonomous Driving.
Merge duplicates and call out confirmed facts versus rumors.
Explain industry impact, affected companies or themes, and what to monitor next.
End with 2-3 concise observations.
""".strip(),
        2200,
    ),
    (
        "市场分析与投资观察",
        "Markets & Watchlist",
        MARKET_SECTIONS,
        True,
        """
Cover Market News and available A-share, Hong Kong, and US index data.
Explain likely market implications based only on the provided market news and index moves.
Provide cautious, general investment observations such as risk control, watchlist themes, position sizing, and what to monitor next.
Add 3-5 specific A-share watchlist candidates with stock names and stock codes.
For each A-share candidate, include related theme, reason to watch, key risk, and what signal to monitor next.
Do not give personalized financial advice, guaranteed returns, or unconditional buy/sell instructions.
""".strip(),
        2600,
    ),
]


def shanghai_now() -> datetime:
    try:
        return datetime.now(ZoneInfo("Asia/Shanghai"))
    except ZoneInfoNotFoundError:
        return datetime.now(timezone(timedelta(hours=8)))


def _filter_items(items: list[NewsItem], sections: set[str]) -> list[NewsItem]:
    return [item for item in items if item.section in sections]


def main() -> None:
    settings = load_settings()
    items = fetch_news(settings.news_lookback_hours, settings.max_news_items)
    market_quotes = fetch_market_quotes()
    token = get_tenant_access_token(settings.feishu_app_id, settings.feishu_app_secret)
    today = shanghai_now().strftime("%Y-%m-%d")
    for label, title, sections, include_markets, instructions, char_limit in BRIEF_PARTS:
        part_items = _filter_items(items, sections)
        part_quotes = market_quotes if include_markets else []
        brief = build_brief_part(
            settings.llm_provider,
            settings.llm_api_key,
            settings.llm_model,
            label,
            instructions,
            part_items,
            part_quotes,
            char_limit=char_limit,
        )
        print(f"Generated {label} brief length: {len(brief)} characters.")
        send_interactive_card(
            token,
            settings.feishu_chat_id,
            f"{title} | {today}",
            brief,
        )
    print(f"Sent brief with {len(items)} news items and {len(market_quotes)} market quotes.")


if __name__ == "__main__":
    main()
