"""Play the scripted member conversations in data/conversations.json against the flow.

Each conversation uses its own session_id, so the flow's Message History only sees that
member's earlier turns. Standard library only.
"""

import json
import os
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = os.environ.get("LANGFLOW_URL", f"http://localhost:{os.environ.get('LANGFLOW_PORT', '7860')}")


def post(path: str, body: dict, *, token: str | None = None, api_key: str | None = None) -> dict:
    req = urllib.request.Request(BASE + path, method="POST", data=json.dumps(body).encode())
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if api_key:
        req.add_header("x-api-key", api_key)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def answer_text(result: dict) -> str:
    return result["outputs"][0]["outputs"][0]["results"]["message"]["text"]


def main() -> None:
    flow_id = (HERE / ".flow_id").read_text().strip()
    with urllib.request.urlopen(BASE + "/api/v1/auto_login", timeout=30) as resp:
        token = json.loads(resp.read())["access_token"]
    # The /run endpoint only accepts a Langflow API key (a login token gets 403).
    api_key = post("/api/v1/api_key/", {"name": "gym-demo"}, token=token)["api_key"]

    conversations = json.loads((HERE / "data" / "conversations.json").read_text())
    for convo in conversations:
        print(f"\n=== {convo['member']} (session {convo['session_id']})")
        for message in convo["turns"]:
            result = post(f"/api/v1/run/{flow_id}?stream=false", {
                "input_value": message,
                "input_type": "chat",
                "output_type": "chat",
                "session_id": convo["session_id"],
            }, api_key=api_key)
            print(f"member: {message}\ndesk:   {answer_text(result)}\n")


if __name__ == "__main__":
    main()
