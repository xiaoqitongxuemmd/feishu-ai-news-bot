from dataclasses import dataclass
from datetime import datetime, timezone
import json
import time
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

FETCH_ATTEMPTS = 3
FETCH_RETRY_DELAY_SECONDS = 5


def _chart_url(symbol: str) -> str:
    encoded = urllib.parse.quote(symbol, safe="")
    return f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?range=5d&interval=1d"


def _fetch_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 feishu-ai-news-bot/0.1",
            "Accept": "application/json",
        },
    )
    last_error: Exception | None = None
    for attempt in range(1, FETCH_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            last_error = exc
            if attempt < FETCH_ATTEMPTS:
                time.sleep(FETCH_RETRY_DELAY_SECONDS * attempt)
    raise RuntimeError(f"Failed to fetch market data after {FETCH_ATTEMPTS} attempts: {url}") from last_error


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

    previous = float(points[-2][1])
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


def fetch_market_quotes() -> list[MarketQuote]:
    quotes: list[MarketQuote] = []
    for region, name, symbol in MARKET_SYMBOLS:
        try:
            data = _fetch_json(_chart_url(symbol))
            quote = _parse_quote(region, name, symbol, data)
        except Exception as exc:
            print(f"Failed to fetch market quote for {symbol}: {exc}")
            quote = None
        if quote:
            quotes.append(quote)
    return quotes
