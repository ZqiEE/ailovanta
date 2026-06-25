from api.owned_default import DefaultOwnedChatRequest, default_owned_chat, split_model_key


class DummyRegistry:
    pass


def test_split_model_key() -> None:
    assert split_model_key("ailovanta-owned:candidate") == ("ailovanta-owned", "candidate")
    assert split_model_key("ailovanta-owned") == ("ailovanta-owned", "candidate")


def test_default_owned_chat_without_route() -> None:
    result = default_owned_chat(DefaultOwnedChatRequest(prompt="hello", route_key="missing/route"), DummyRegistry())
    assert result["ok"] is False
    assert result["source"] == "owned-route-unavailable"
