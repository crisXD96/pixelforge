import pytest
from PIL import Image

from pixelforge.thumbnail import fit_within, make_thumbnail


@pytest.mark.parametrize("size", [(1200, 800), (800, 1200), (300, 300), (120, 90)])
def test_thumbnail_is_exact_square(size):
    thumb = make_thumbnail(Image.new("RGB", size), 300)
    assert thumb.size == (300, 300)


@pytest.mark.parametrize(
    ("size", "expected"),
    [((3200, 2000), (1600, 1000)), ((1000, 3000), (533, 1600)), ((638, 400), (638, 400))],
)
def test_fit_within_keeps_ratio_and_never_upscales(size, expected):
    assert fit_within(Image.new("RGB", size), 1600).size == expected


def test_fit_within_returns_copy():
    img = Image.new("RGB", (100, 100))
    assert fit_within(img, 1600) is not img


def test_thumbnail_keeps_mode():
    assert make_thumbnail(Image.new("RGBA", (500, 400)), 300).mode == "RGBA"


def test_thumbnail_crops_center():
    # Franjas rojo | verde | azul de 300 px: el recorte centrado debe quedar todo verde.
    img = Image.new("RGB", (900, 300))
    img.paste((255, 0, 0), (0, 0, 300, 300))
    img.paste((0, 255, 0), (300, 0, 600, 300))
    img.paste((0, 0, 255), (600, 0, 900, 300))

    thumb = make_thumbnail(img, 300)
    for xy in [(5, 5), (150, 150), (294, 294)]:
        r, g, b = thumb.getpixel(xy)
        assert g > 200 and r < 30 and b < 30, (xy, (r, g, b))
