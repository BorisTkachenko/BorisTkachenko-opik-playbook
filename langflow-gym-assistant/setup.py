"""Create the gym front-desk flow in a running Langflow, headlessly.

It starts from Langflow's own "Memory Chatbot" starter (Chat Input -> Message History ->
Prompt -> Language Model -> Chat Output), writes the gym's facts and rules into the prompt,
points the Language Model at gpt-4o-mini, and saves it as the flow "Gym front desk".
Re-running replaces the earlier copy. Standard library only.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = os.environ.get("LANGFLOW_URL", f"http://localhost:{os.environ.get('LANGFLOW_PORT', '7860')}")
FLOW_NAME = "Gym front desk"
MODEL = "gpt-4o-mini"


def call(method: str, path: str, token: str | None = None, body: dict | None = None) -> dict | list:
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(req, data=data, timeout=60) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else {}


def wait_for_langflow() -> None:
    for _ in range(90):
        try:
            if call("GET", "/health").get("status") == "ok":
                return
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            pass
        time.sleep(2)
    sys.exit(f"Langflow did not come up at {BASE}")


def build_prompt() -> str:
    facts = (HERE / "data" / "gym-facts.md").read_text()
    # Langflow treats {name} as a template variable, so the facts must not contain braces.
    assert "{" not in facts and "}" not in facts
    return (
        "You are the front-desk assistant of Ironwood Community Gym. Answer members' questions "
        "using ONLY the facts below. Quote prices, times and rules exactly as written. If the "
        "facts do not cover a question, say you don't know and suggest asking at the front desk. "
        "Keep answers to two or three sentences.\n\n"
        f"{facts}\n"
        "Conversation so far:\n{context}\n\n"
        "Member: {user_message}\nAssistant:"
    )


def main() -> None:
    wait_for_langflow()
    token = call("GET", "/api/v1/auto_login")["access_token"]

    starters = call("GET", "/api/v1/starter-projects/", token)
    flow = next(p for p in starters if p["name"] == "Memory Chatbot")

    # The Language Model component wants a full "model selection" object, not just a name.
    # Take an OpenAI entry from Langflow's own catalogue as the template and point it at
    # gpt-4o-mini. The catalogue's default OpenAI entries are reasoning models, so clear those
    # flags or Langflow would send reasoning parameters gpt-4o-mini rejects.
    catalogue = call("GET", "/api/v1/model_options/language", token)
    selection = dict(next(o for o in catalogue if o.get("provider") == "OpenAI"))
    selection["name"] = MODEL
    selection["metadata"] = {**selection.get("metadata", {}), "reasoning": False, "reasoning_models": []}

    for node in flow["data"]["nodes"]:
        kind, tpl = node["data"]["type"], node["data"]["node"]["template"]
        if kind in ("Prompt", "Prompt Template"):
            tpl["template"]["value"] = build_prompt()
        elif kind == "LanguageModelComponent":
            tpl["model"]["value"] = [selection]
            tpl["temperature"]["value"] = 0
            # Reference the global variable by name; the key itself never enters the flow.
            tpl["api_key"]["value"] = "OPENAI_API_KEY"
            tpl["api_key"]["load_from_db"] = True
        elif kind == "MemoryComponent":
            tpl["n_messages"]["value"] = 20

    for old in call("GET", "/api/v1/flows/?remove_example_flows=true&get_all=true", token):
        if old.get("name") == FLOW_NAME:
            call("DELETE", f"/api/v1/flows/{old['id']}", token)

    created = call("POST", "/api/v1/flows/", token, {
        "name": FLOW_NAME,
        "description": "Ironwood Community Gym membership and class-schedule assistant",
        "data": flow["data"],
    })
    (HERE / ".flow_id").write_text(created["id"])
    print(f"Created flow '{FLOW_NAME}' ({created['id']}). Langflow UI: {BASE}")


if __name__ == "__main__":
    main()
