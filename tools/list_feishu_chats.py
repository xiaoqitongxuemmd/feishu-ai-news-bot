from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ai_news_bot.config import _require  # noqa: E402
from ai_news_bot.feishu import get_tenant_access_token, list_chats  # noqa: E402


def main() -> None:
    token = get_tenant_access_token(_require("FEISHU_APP_ID"), _require("FEISHU_APP_SECRET"))
    chats = list_chats(token)
    if not chats:
        print("No chats found. Confirm the bot has been added to the target group.")
        return
    for chat in chats:
        print(f"{chat.get('name', '<unnamed>')}\t{chat.get('chat_id')}")


if __name__ == "__main__":
    main()
