from __future__ import annotations

from api.main import conversations, runtime_registry, usage_store
from api.main_owned_checked import app
from api.owned_default import DefaultOwnedChatRequest, default_owned_chat


@app.post("/ailovanta/v1/owned-chat-default")
def ailovanta_owned_chat_default(body: DefaultOwnedChatRequest) -> dict:
    convo = conversations.get_or_create(body.conversation_id, body.user_id, "Owned model chat")
    conversations.add_message(convo["id"], "user", body.prompt, source="user", model_id=body.route_key)
    result = default_owned_chat(
        DefaultOwnedChatRequest(
            prompt=body.prompt,
            user_id=body.user_id,
            conversation_id=convo["id"],
            route_key=body.route_key,
            policy_mode=body.policy_mode,
        ),
        runtime_registry,
    )
    conversations.add_message(convo["id"], "assistant", result["answer"], source=result["source"], model_id=result.get("model_id") or body.route_key)
    if result.get("ok"):
        usage_store.record(body.user_id, "ailovanta.owned_chat_default", 1, result["source"], {"conversation_id": convo["id"], "route_key": body.route_key, "model_id": result.get("model_id"), "version": result.get("version")})
    return {**result, "conversation_id": convo["id"]}
