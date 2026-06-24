from pathlib import Path


def test_chatgpt_style_ui_markers_exist() -> None:
    html = Path("index.html").read_text(encoding="utf-8")

    for marker in [
        "Ailovanta Chat",
        "Message Ailovanta",
        "How can I help?",
        "conversationList",
        "composer",
        "Enter to send",
        "Shift+Enter",
        "markdownLite",
        "Thinking...",
        "Copy chat",
        "Clear guest data",
        "Model adapter",
        "Fallback: enabled",
        "/ailovanta/v1/chat",
        "/ailovanta/v1/conversations",
        "context_messages_used",
    ]:
        assert marker in html
