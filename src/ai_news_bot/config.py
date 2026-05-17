from dataclasses import dataclass
import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


if load_dotenv:
    load_dotenv()


@dataclass(frozen=True)
class Settings:
    feishu_app_id: str
    feishu_app_secret: str
    feishu_chat_id: str
    llm_provider: str
    llm_api_key: str
    llm_model: str
    news_lookback_hours: int
    max_news_items: int


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def load_settings() -> Settings:
    llm_provider = (os.environ.get("LLM_PROVIDER") or "openai").lower()
    if llm_provider == "deepseek":
        llm_api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("LLM_API_KEY")
        llm_model = os.environ.get("DEEPSEEK_MODEL") or os.environ.get("LLM_MODEL") or "deepseek-chat"
    elif llm_provider == "openai":
        llm_api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
        llm_model = os.environ.get("OPENAI_MODEL") or os.environ.get("LLM_MODEL") or "gpt-4.1-mini"
    else:
        raise RuntimeError(f"Unsupported LLM_PROVIDER: {llm_provider}")
    if not llm_api_key:
        raise RuntimeError(
            "Missing LLM API key. Set DEEPSEEK_API_KEY for deepseek or OPENAI_API_KEY for openai."
        )

    return Settings(
        feishu_app_id=_require("FEISHU_APP_ID"),
        feishu_app_secret=_require("FEISHU_APP_SECRET"),
        feishu_chat_id=_require("FEISHU_CHAT_ID"),
        llm_provider=llm_provider,
        llm_api_key=llm_api_key,
        llm_model=llm_model,
        news_lookback_hours=int(os.environ.get("NEWS_LOOKBACK_HOURS", "24")),
        max_news_items=int(os.environ.get("MAX_NEWS_ITEMS", "24")),
    )
