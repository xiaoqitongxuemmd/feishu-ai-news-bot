import json
import urllib.error
import urllib.request

from .markets import MarketQuote
from .news import NewsItem


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/chat/completions"


def _news_payload(items: list[NewsItem]) -> str:
    rows = []
    for item in items:
        rows.append(
            {
                "section": item.section,
                "title": item.title,
                "source": item.source,
                "published": item.published,
                "summary": item.summary,
                "link": item.link,
            }
        )
    return json.dumps(rows, ensure_ascii=False, indent=2)


def _market_payload(quotes: list[MarketQuote]) -> str:
    rows = []
    for quote in quotes:
        rows.append(
            {
                "region": quote.region,
                "name": quote.name,
                "symbol": quote.symbol,
                "currency": quote.currency,
                "latest": round(quote.latest, 2),
                "change": round(quote.change, 2),
                "change_percent": round(quote.change_percent, 2),
                "latest_time": quote.latest_time,
                "source": quote.source,
            }
        )
    return json.dumps(rows, ensure_ascii=False, indent=2)


def _brief_prompt(news_items: list[NewsItem], market_quotes: list[MarketQuote]) -> str:
    return f"""
You are a senior news editor and market analyst.
Create a Chinese Feishu daily brief from the candidate news and market data below.

Hard constraints:
- Use only information in the candidate news and market data.
- All candidate news is already filtered to the last 24 hours. Do not introduce older news.
- Market data is filtered to the last 24 hours. If market data is empty, explicitly say there is no usable 24-hour market quote data and do not use stale prices.
- Do not invent facts, prices, policy details, earnings, or company events.
- Output Chinese markdown only.
- Keep the final answer under 4000 Chinese characters.

Required structure:
1. Important domestic and global news
   - Cover Important Domestic News and Important Global News.
   - Select the most important items, each with title, source/time, concise summary, why it matters, and link.
2. Domestic/global AI and autonomous driving industry news
   - Cover Domestic AI, Global AI, Domestic Autonomous Driving, and Global Autonomous Driving.
   - Merge duplicates and call out confirmed facts versus rumors.
3. A-share, Hong Kong, and US markets with investment observations
   - Cover Market News and any available A-share, Hong Kong, and US index data.
   - Explain likely market implications based only on the provided market news and index moves.
   - Provide cautious, general investment suggestions such as risk control, watchlist themes, position sizing, and what to monitor next.
   - Do not give personalized financial advice, guaranteed returns, or unconditional buy/sell instructions.
4. Today's observations
   - Give 3-5 concise cross-market and industry takeaways.

Candidate news:
{_news_payload(news_items)}

Market data:
{_market_payload(market_quotes)}
""".strip()


def _raise_http_error(provider: str, exc: urllib.error.HTTPError) -> None:
    body = exc.read().decode("utf-8", errors="replace")
    raise RuntimeError(f"{provider} API request failed: HTTP {exc.code}: {body}") from exc


def _call_openai(api_key: str, model: str, prompt: str) -> str:
    payload = {
        "model": model,
        "instructions": "Output only Chinese markdown suitable for a Feishu message card.",
        "input": prompt,
        "max_output_tokens": 4500,
    }
    req = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        _raise_http_error("OpenAI", exc)

    text = data.get("output_text")
    if text:
        return text

    parts: list[str] = []
    for output in data.get("output", []):
        for content in output.get("content", []):
            if content.get("type") == "output_text":
                parts.append(content.get("text", ""))
    if parts:
        return "\n".join(parts)
    raise RuntimeError(f"OpenAI response did not contain output text: {data}")


def _call_deepseek(api_key: str, model: str, prompt: str) -> str:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Output only Chinese markdown suitable for a Feishu message card.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.25,
        "max_tokens": 4500,
        "stream": False,
    }
    req = urllib.request.Request(
        DEEPSEEK_CHAT_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        _raise_http_error("DeepSeek", exc)

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"DeepSeek response did not contain output text: {data}") from exc


def build_brief(
    provider: str,
    api_key: str,
    model: str,
    news_items: list[NewsItem],
    market_quotes: list[MarketQuote],
) -> str:
    if not news_items and not market_quotes:
        return "No usable news or market data was fetched today. Please check the sources or network."

    prompt = _brief_prompt(news_items, market_quotes)
    if provider == "deepseek":
        return _call_deepseek(api_key, model, prompt)
    if provider == "openai":
        return _call_openai(api_key, model, prompt)
    raise RuntimeError(f"Unsupported LLM provider: {provider}")
