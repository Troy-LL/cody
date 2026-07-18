from overlay.query_parse import extract_search_phrase, parse_hey_cody, query_terms


def test_hey_cody_wheres_my() -> None:
    assert parse_hey_cody("Hey Cody, where's my Downloads") == "Downloads"
    assert parse_hey_cody("hey cody where is my sort button") == "sort button"
    assert parse_hey_cody("Hey Codey where's my antigravity diagnostics") == "antigravity diagnostics"


def test_wake_only() -> None:
    assert parse_hey_cody("Hey Cody") == ""


def test_non_command() -> None:
    assert parse_hey_cody("what's the weather") is None


def test_extract_and_terms() -> None:
    assert extract_search_phrase("where's my View menu") == "View menu"
    assert "view" in query_terms("View menu")
