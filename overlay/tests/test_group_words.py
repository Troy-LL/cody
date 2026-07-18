from overlay.ocr_targets import group_word_boxes


def test_groups_adjacent_words_on_one_line() -> None:
    words = [
        ("New", 10, 20, 30, 12),
        ("folder", 44, 20, 40, 12),  # small gap after "New"
    ]
    out = group_word_boxes(words)
    assert len(out) == 1
    assert out[0][0] == "New folder"


def test_keeps_far_apart_words_separate() -> None:
    words = [
        ("File", 10, 20, 30, 12),
        ("Edit", 200, 20, 30, 12),  # large gap
    ]
    out = group_word_boxes(words)
    assert [b[0] for b in out] == ["File", "Edit"]


def test_different_lines_stay_separate() -> None:
    words = [
        ("Hello", 10, 20, 40, 12),
        ("world", 10, 50, 40, 12),
    ]
    out = group_word_boxes(words)
    assert [b[0] for b in out] == ["Hello", "world"]
