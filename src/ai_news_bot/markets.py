from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import urllib.parse
import urllib.request


@dataclass(frozen=True)
class MarketQuote:
    region: str
    name: str
    symbol: str
    currency: str
    latest: float
    previous: float
    change: float
    change_percent: float
    latest_time: str
    source: str = "Yahoo Finance"


MARKET_SYMBOLS = [
    ("A-share", "SSE Composite", "000001.SS"),
    ("A-share", "SZSE Component", "399001.SZ"),
    ("A-share", "CSI 300", "000300.SS"),
    ("Hong Kong", "Hang Seng Index", "^HSI"),
    ("Hong Kong", "Hang Seng China Enterprises", "^HSCE"),
    ("US", "S&P 500", "^GSPC"),
    ("US", "Nasdaq Composite", "^IXIC"),
    ("US", "Dow Jones Industrial Average", "^DJI"),
]


def _chart_url(symbol: str) -> str:
    encoded = urllib.parse.quote(symbol, safe="")
    return f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?range=1d&interval=5m"


def _fetch_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 feishu-ai-news-bot/0.1",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _parse_quote(region: str, name: str, symbol: str, data: dict) -> MarketQuote | None:
    result = data.get("chart", {}).get("result") or []
    if not result:
        return None
    chart = result[0]
    timestamps = chart.get("timestamp") or []
    quote = (chart.get("indicators", {}).get("quote") or [{}])[0]
    closes = quote.get("close") or []
    meta = chart.get("meta", {})

    points = [(ts, close) for ts, close in zip(timestamps, closes) if close is not None]
    if len(points) < 2:
        return None

    previous = float(points[0][1])
    latest_ts, latest_value = points[-1]
    latest = float(latest_value)
    change = latest - previous
    change_percent = (change / previous * 100) if previous else 0.0
    latest_time = datetime.fromtimestamp(latest_ts, tz=timezone.utc).isoformat()

    return MarketQuote(
        region=region,
        name=name,
        symbol=symbol,
        currency=meta.get("currency", ""),
        latest=latest,
        previous=previous,
        change=change,
        change_percent=change_percent,
        latest_time=latest_time,
    )


def fetch_market_quotes(lookback_hours: int = 24) -> list[MarketQuote]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    quotes: list[MarketQuote] = []
    for region, name, symbol in MARKET_SYMBOLS:
        try:
            data = _fetch_json(_chart_url(symbol))
            quote = _parse_quote(region, name, symbol, data)
        except Exception:
            quote = None
        if quote and datetime.fromisoformat(quote.latest_time) >= cutoff:
            quotes.append(quote)
    return quotes
