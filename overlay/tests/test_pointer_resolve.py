from dataclasses import dataclass

from overlay.pointer_resolve import boxes_for, resolve
from overlay.screenshot import Shot


@dataclass
class FakeBox:
    text: str
    center: tuple[int, int]


def test_ocr_match_wins_over_coords():
    boxes = [FakeBox("Save", (500, 300)), FakeBox("Cancel", (600, 300))]
    shot = Shot(image=None, scale=0.5, origin=(0, 0))
    assert resolve("save", coords=(10, 10), boxes=boxes, shot=shot) == (500, 300)


def test_coords_fallback_when_no_ocr_match():
    shot = Shot(image=None, scale=0.5, origin=(0, 0))
    assert resolve("nonexistent", coords=(10, 10), boxes=[], shot=shot) == (20, 20)


def test_none_when_nothing():
    shot = Shot(image=None, scale=1.0, origin=(0, 0))
    assert resolve(None, coords=None, boxes=[], shot=shot) is None


def test_resolve_clamps_off_screen_coords(monkeypatch):
    monkeypatch.setattr("overlay.screenshot.desktop_bounds", lambda: (0, 0, 1919, 1079))
    shot = Shot(image=None, scale=1.0, origin=(0, 0))
    assert resolve("nonexistent", coords=(-100, 5000), boxes=[], shot=shot) == (0, 1079)


def test_resolve_clamps_ocr_center(monkeypatch):
    monkeypatch.setattr("overlay.screenshot.desktop_bounds", lambda: (0, 0, 1919, 1079))
    boxes = [FakeBox("Save", (-50, 3000))]
    shot = Shot(image=None, scale=1.0, origin=(0, 0))
    assert resolve("save", coords=None, boxes=boxes, shot=shot) == (0, 1079)


def test_whole_word_beats_longer_substring():
    # "troy" must hit the Troy-LL tab, not "troylazaro09" (old code took longest).
    boxes = [
        FakeBox("Inbox - troylazaro09@gmail.com", (3400, 115)),
        FakeBox("Troy-LL (Troy)", (3090, 18)),
    ]
    shot = Shot(image=None, scale=1.0, origin=(0, 0))
    assert resolve("troy-ll", coords=None, boxes=boxes, shot=shot) == (3090, 18)


def test_exact_label_beats_reply_bubble():
    boxes = [
        FakeBox("Here's Cursor Settings.", (890, 230)),
        FakeBox("Cursor Settings", (800, 129)),
    ]
    shot = Shot(image=None, scale=1.0, origin=(0, 0))
    assert resolve("cursor settings", coords=None, boxes=boxes, shot=shot) == (800, 129)


def test_no_match_falls_back_to_coords():
    # OCR truncated the tab to "@gma" — "gmail" appears nowhere. Prefer the
    # model's coords over pointing at an unrelated line.
    boxes = [FakeBox("Inbox - troylazaro09@gma", (3400, 115))]
    shot = Shot(image=None, scale=1.0, origin=(0, 0))
    assert resolve("gmail", coords=(10, 10), boxes=boxes, shot=shot) == (10, 10)


def test_boxes_for_maps_ocr_to_screen_centers(monkeypatch):
    def fake_ocr(_img):
        return [("Save", 100, 40, 20, 10)]

    monkeypatch.setattr("overlay.pointer_resolve.ocr_boxes", fake_ocr)
    shot = Shot(image=object(), scale=0.5, origin=(-1920, 0))
    boxes = boxes_for(shot)
    assert len(boxes) == 1
    assert boxes[0].text == "Save"
    assert boxes[0].center == (-1700, 90)
