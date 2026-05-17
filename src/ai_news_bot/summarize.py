import json
import urllib.error
import urllib.request

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


def _brief_prompt(items: list[NewsItem]) -> str:
    return f"""
You are a technology industry analyst and daily news editor.
Create a Chinese Feishu daily brief from the candidate news below.

Rules:
- Output Chinese markdown only.
- Sections: Daily Domestic News, Daily Global News, Domestic AI, Global AI, Domestic Autonomous Driving, Global Autonomous Driving, Today's Observations.
- Use Chinese section titles in the final answer. Translate them as:
  Daily Domestic News = domestic general news.
  Daily Global News = global general news.
  Domestic AI = domestic AI.
  Global AI = global AI.
  Domestic Autonomous Driving = domestic intelligent/autonomous driving.
  Global Autonomous Driving = global intelligent/autonomous driving.
  Today's Observations = daily observations.
- Daily Domestic News and Daily Global News are strict 24-hour sections. Do not include older items there.
- Each selected news item must include title, source/time, 2-3 sentence summary, why it matters, and link.
- Merge duplicate events and keep the most authoritative source.
- Distinguish confirmed facts from rumors.
- Do not invent facts outside the candidate list.
- Keep the final answer under 3500 Chinese characters.

Candidate news:
{_news_payload(items)}
""".strip()


def _raise_http_error(provider: str, exc: urllib.error.HTTPError) -> None:
    body = exc.read().decode("utf-8", errors="replace")
    raise RuntimeError(f"{provider} API request failed: HTTP {exc.code}: {body}") from exc


def _call_openai(api_key: str, model: str, prompt: str) -> str:
    payload = {
        "model": model,
        "instructions": "Output only Chinese markdown suitable for a Feishu message card.",
        "input": prompt,
        "max_output_tokens": 4000,
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
        "temperature": 0.3,
        "max_tokens": 4000,
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


def build_brief(provider: str, api_key: str, model: str, items: list[NewsItem]) -> str:
    if not items:
        return "No usable news was fetched today. Please check the news sources or network."

    prompt = _brief_prompt(items)
    if provider == "deepseek":
        return _call_deepseek(api_key, model, prompt)
    if provider == "openai":
        return _call_openai(api_key, model, prompt)
    raise RuntimeError(f"Unsupported LLM provider: {provider}")
