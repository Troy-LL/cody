from PIL import Image

from overlay.refine import crop_around, map_from_crop
from overlay.screenshot import Shot


def test_crop_around_maps_back():
    img = Image.new("RGB", (200, 200), color=(255, 0, 0))
    shot = Shot(image=img, scale=1.0, origin=(0, 0))
    crop, box = crop_around(shot, 100, 100, pad=0.1)
    left, top, right, bottom = box
    assert (left, top, right, bottom) == (80, 80, 120, 120)
    assert crop.size == (40, 40)
    assert map_from_crop((20, 20), box) == (100.0, 100.0)


def test_crop_around_clamps_to_image_edges():
    img = Image.new("RGB", (200, 200))
    shot = Shot(image=img, scale=1.0, origin=(0, 0))
    _, box = crop_around(shot, 5, 5, pad=0.1)
    assert box[0] == 0 and box[1] == 0
