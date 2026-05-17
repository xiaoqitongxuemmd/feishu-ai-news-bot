from collections import Counter
from datetime import datetime, timezone

from ai_news_bot.markets import fetch_market_quotes
from ai_news_bot.news import fetch_news


items = fetch_news(24, 30)
counts = Counter(item.section for item in items)
print("total", len(items))
for section in [
    "Important Domestic News",
    "Important Global News",
    "Market News",
    "Domestic AI",
    "Global AI",
    "Domestic Autonomous Driving",
    "Global Autonomous Driving",
]:
    print(section, counts.get(section, 0))

now = datetime.now(timezone.utc)
for item in items:
    if item.section in {"Important Domestic News", "Important Global News"}:
        age = ""
        if item.published:
            published = datetime.fromisoformat(item.published)
            age = f"{(now - published).total_seconds() / 3600:.1f}h"
        print("-", item.section, age, item.title[:100])

print("markets")
for quote in fetch_market_quotes():
    print(
        quote.region,
        quote.name,
        quote.symbol,
        round(quote.latest, 2),
        f"{quote.change_percent:.2f}%",
        quote.latest_time,
    )
