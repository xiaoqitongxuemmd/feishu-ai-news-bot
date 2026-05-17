from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import html
import urllib.parse

import feedparser


@dataclass(frozen=True)
class NewsItem:
    section: str
    title: str
    link: str
    source: str
    published: str
    summary: str


@dataclass(frozen=True)
class FeedQuery:
    section: str
    query: str
    hl: str
    gl: str
    ceid: str


FEED_QUERIES = [
    FeedQuery("Important Domestic News", "__TOP_STORIES__", "zh-CN", "CN", "CN:zh-Hans"),
    FeedQuery("Important Domestic News", "China breaking news politics economy society", "zh-CN", "CN", "CN:zh-Hans"),
    FeedQuery("Important Domestic News", "China finance technology policy market news", "zh-CN", "CN", "CN:zh-Hans"),
    FeedQuery("Important Global News", "__TOP_STORIES__", "en-US", "US", "US:en"),
    FeedQuery("Important Global News", "world breaking news politics economy technology", "en-US", "US", "US:en"),
    FeedQuery("Important Global News", "global markets geopolitics business technology news", "en-US", "US", "US:en"),
    FeedQuery("Market News", "A-share Hong Kong US stocks market index investors", "zh-CN", "CN", "CN:zh-Hans"),
    FeedQuery("Market News", "A股 港股 美股 行情 指数 投资者", "zh-CN", "CN", "CN:zh-Hans"),
    FeedQuery("Market News", "US stocks Hong Kong stocks China A-shares market today", "en-US", "US", "US:en"),
    FeedQuery("Domestic AI", "China artificial intelligence large language model", "zh-CN", "CN", "CN:zh-Hans"),
    FeedQuery("Domestic AI", "China AI chip computing power policy funding", "zh-CN", "CN", "CN:zh-Hans"),
    FeedQuery("Domestic AI", "Baidu Alibaba Tencent ByteDance AI model", "zh-CN", "CN", "CN:zh-Hans"),
    FeedQuery("Global AI", "OpenAI Google Anthropic Meta NVIDIA AI", "en-US", "US", "US:en"),
    FeedQuery("Global AI", "generative AI model launch funding regulation", "en-US", "US", "US:en"),
    FeedQuery("Global AI", "AI chip cloud model startup funding", "en-US", "US", "US:en"),
    FeedQuery("Domestic Autonomous Driving", "China autonomous driving robotaxi NOA ADAS", "zh-CN", "CN", "CN:zh-Hans"),
    FeedQuery("Domestic Autonomous Driving", "China intelligent driving lidar EV automaker", "zh-CN", "CN", "CN:zh-Hans"),
    FeedQuery("Domestic Autonomous Driving", "Baidu Apollo Pony.ai WeRide Momenta autonomous driving", "zh-CN", "CN", "CN:zh-Hans"),
    FeedQuery("Global Autonomous Driving", "Tesla FSD Waymo Cruise Zoox robotaxi", "en-US", "US", "US:en"),
    FeedQuery("Global Autonomous Driving", "autonomous driving ADAS robotaxi regulation", "en-US", "US", "US:en"),
    FeedQuery("Global Autonomous Driving", "Mobileye NVIDIA Drive Qualcomm autonomous vehicle", "en-US", "US", "US:en"),
]


SECTION_ORDER = [
    "Important Domestic News",
    "Important Global News",
    "Market News",
    "Domestic AI",
    "Global AI",
    "Domestic Autonomous Driving",
    "Global Autonomous Driving",
]


def _google_news_rss(feed_query: FeedQuery) -> str:
    if feed_query.query == "__TOP_STORIES__":
        params = urllib.parse.urlencode(
            {
                "hl": feed_query.hl,
                "gl": feed_query.gl,
                "ceid": feed_query.ceid,
            }
        )
        return f"https://news.google.com/rss?{params}"
    params = urllib.parse.urlencode(
        {
            "q": feed_query.query,
            "hl": feed_query.hl,
            "gl": feed_query.gl,
            "ceid": feed_query.ceid,
        }
    )
    return f"https://news.google.com/rss/search?{params}"


def _parse_time(entry) -> datetime | None:
    raw = entry.get("published") or entry.get("updated")
    if not raw:
        return None
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(html.unescape(value).split())


def _entry_to_item(section: str, entry, published_dt: datetime) -> NewsItem:
    return NewsItem(
        section=section,
        title=_clean_text(entry.get("title")),
        link=entry.get("link", ""),
        source=_clean_text(entry.get("source", {}).get("title", "Google News")),
        published=published_dt.isoformat(),
        summary=_clean_text(entry.get("summary")),
    )


def fetch_news(lookback_hours: int, max_items: int) -> list[NewsItem]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    per_section = max(2, max_items // len(SECTION_ORDER))
    seen_links: set[str] = set()
    by_section: dict[str, list[NewsItem]] = {section: [] for section in SECTION_ORDER}

    for feed_query in FEED_QUERIES:
        feed = feedparser.parse(_google_news_rss(feed_query))
        for entry in feed.entries:
            link = entry.get("link", "")
            if not link or link in seen_links:
                continue
            published_dt = _parse_time(entry)
            if not published_dt or published_dt < cutoff:
                continue
            seen_links.add(link)
            by_section[feed_query.section].append(_entry_to_item(feed_query.section, entry, published_dt))

    items: list[NewsItem] = []
    for section in SECTION_ORDER:
        items.extend(by_section[section][:per_section])

    return items[:max_items]
