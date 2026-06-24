from api.conversation_context import build_chat_context, context_to_text


def test_build_chat_context_keeps_recent_messages_without_duplication() -> None:
    messages = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "reply one"},
        {"role": "user", "content": "second"},
        {"role": "assistant", "content": "reply two"},
        {"role": "user", "content": "latest"},
    ]

    context = build_chat_context(messages, "latest", max_messages=4)

    assert context == [
        {"role": "assistant", "content": "reply one"},
        {"role": "user", "content": "second"},
        {"role": "assistant", "content": "reply two"},
        {"role": "user", "content": "latest"},
    ]
    assert context.count({"role": "user", "content": "latest"}) == 1


def test_build_chat_context_appends_latest_prompt_when_missing() -> None:
    context = build_chat_context([{"role": "assistant", "content": "hello"}], "new question", max_messages=5)
    assert context[-1] == {"role": "user", "content": "new question"}


def test_context_to_text_renders_roles() -> None:
    text = context_to_text([
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ])
    assert "USER: hello" in text
    assert "ASSISTANT: hi" in text
