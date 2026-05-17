import json
import urllib.parse
import urllib.request


API_BASE = "https://open.feishu.cn/open-apis"


def _request_json(req: urllib.request.Request) -> dict:
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_json(url: str, payload: dict, token: str | None = None) -> dict:
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    return _request_json(req)


def _get_json(url: str, token: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    return _request_json(req)


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    data = _post_json(
        f"{API_BASE}/auth/v3/tenant_access_token/internal",
        {"app_id": app_id, "app_secret": app_secret},
    )
    if data.get("code") != 0:
        raise RuntimeError(f"Failed to get tenant_access_token: {data}")
    return data["tenant_access_token"]


def list_chats(token: str) -> list[dict]:
    params = urllib.parse.urlencode({"page_size": 100})
    data = _get_json(f"{API_BASE}/im/v1/chats?{params}", token)
    if data.get("code") != 0:
        raise RuntimeError(f"Failed to list chats: {data}")
    return data.get("data", {}).get("items", [])


def send_interactive_card(token: str, chat_id: str, title: str, markdown: str) -> None:
    params = urllib.parse.urlencode({"receive_id_type": "chat_id"})
    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "blue",
            "title": {"tag": "plain_text", "content": title},
        },
        "elements": [
            {
                "tag": "markdown",
                "content": markdown[:12000],
            }
        ],
    }
    payload = {
        "receive_id": chat_id,
        "msg_type": "interactive",
        "content": json.dumps(card, ensure_ascii=False),
    }
    data = _post_json(f"{API_BASE}/im/v1/messages?{params}", payload, token)
    if data.get("code") != 0:
        raise RuntimeError(f"Failed to send Feishu message: {data}")
