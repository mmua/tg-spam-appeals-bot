"""Additional utils tests to improve coverage."""

from appeals_bot.utils import escape_markdown, truncate_text


def test_escape_markdown_all_chars():
    src = "_ * [ ] ( ) ~ ` > # + - = | { } . !"
    escaped = escape_markdown(src)
    assert "\\_" in escaped and "\\*" in escaped and "\\#" in escaped


def test_truncate_text_short_and_long():
    assert truncate_text("short", 10) == "short"
    assert truncate_text("abcdefghijk", 10) == "abcdefg..."


