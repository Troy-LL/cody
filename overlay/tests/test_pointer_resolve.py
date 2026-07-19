from dataclasses import dataclass

from overlay.pointer_resolve import boxes_for, resolve
from overlay.screenshot import Shot


@dataclass
class FakeBox:
    text: str
    center: tuple[int, int]


def test_ocr_snaps_when_near_model_coords():
    # model (10,10) @0.5 → (20,20); OCR Save nearby → snap to OCR
    boxes = [FakeBox("Save", (22, 24)), FakeBox("Cancel", (600, 300))]
    shot = Shot(image=None, scale=0.5, origin=(0, 0))
    assert resolve("save", coords=(10, 10), boxes=boxes, shot=shot) == (22, 24)


def test_model_coords_win_when_ocr_far():
    # Far OCR must not steal the model guess (wrong-label bug).
    boxes = [FakeBox("Save", (500, 300))]
    shot = Shot(image=None, scale=0.5, origin=(0, 0))
    assert resolve("save", coords=(10, 10), boxes=boxes, shot=shot) == (20, 20)


def test_coords_fallback_when_no_ocr_match():
    shot = Shot(image=None, scale=0.5, origin=(0, 0))
    assert resolve("nonexistent", coords=(10, 10), boxes=[], shot=shot) == (20, 20)


def test_ocr_exact_without_coords():
    boxes = [FakeBox("Save", (500, 300))]
    shot = Shot(image=None, scale=1.0, origin=(0, 0))
    assert resolve("save", coords=None, boxes=boxes, shot=shot) == (500, 300)


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


def test_strips_icon_noise_for_ocr_snap():
    boxes = [FakeBox("Notion", (30, 40))]
    shot = Shot(image=None, scale=1.0, origin=(0, 0))
    assert resolve("my Notion icon", coords=(28, 38), boxes=boxes, shot=shot) == (30, 40)


def test_boxes_for_maps_ocr_to_screen_centers(monkeypatch):
    def fake_ocr(_img):
        return [("Save", 100, 40, 20, 10)]

    monkeypatch.setattr("overlay.pointer_resolve.ocr_boxes", fake_ocr)
    shot = Shot(image=object(), scale=0.5, origin=(-1920, 0))
    boxes = boxes_for(shot)
    assert len(boxes) == 1
    assert boxes[0].text == "Save"
    assert boxes[0].center == (-1700, 90)
