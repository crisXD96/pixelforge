import pytest
from PIL import Image, ImageChops, ImageStat

from pixelforge.watermark import apply_watermark

TEXT = "© PixelForge"


@pytest.fixture
def gray():
    return Image.new("RGB", (300, 300), (90, 90, 90))


def changed_bbox(a, b):
    return ImageChops.difference(a.convert("RGB"), b.convert("RGB")).getbbox()


def test_keeps_size_and_mode(gray):
    out = apply_watermark(gray, TEXT, 0.5)
    assert out.size == gray.size and out.mode == "RGB"


def test_text_is_bottom_right_and_inside(gray):
    bbox = changed_bbox(gray, apply_watermark(gray, TEXT, 0.5))
    assert bbox is not None
    left, top, right, bottom = bbox
    assert left > 150 and top > 230          # solo en la esquina inferior derecha
    assert right < 300 and bottom < 300      # deja margen, no toca el borde


def test_text_is_lighter_than_background(gray):
    out = apply_watermark(gray, TEXT, 0.8)
    region = out.crop(changed_bbox(gray, out))
    assert ImageStat.Stat(region).extrema[0][1] > 150  # hay píxeles claros (texto blanco)


def test_higher_opacity_is_more_visible(gray):
    def visibility(opacity):
        diff = ImageChops.difference(gray, apply_watermark(gray, TEXT, opacity))
        return sum(ImageStat.Stat(diff).sum)

    assert visibility(0.9) > visibility(0.3) > 0


@pytest.mark.parametrize(("text", "opacity"), [(TEXT, 0), ("", 0.5), ("   ", 0.5)])
def test_no_op_cases(gray, text, opacity):
    assert changed_bbox(gray, apply_watermark(gray, text, opacity)) is None


def test_long_text_fits_small_image():
    img = Image.new("RGB", (100, 100), (90, 90, 90))
    bbox = changed_bbox(img, apply_watermark(img, "© PixelForge — texto muy largo", 0.8))
    assert bbox is not None
    assert bbox[0] > 0 and bbox[2] < 100


def test_rgba_alpha_preserved_outside_text():
    img = Image.new("RGBA", (300, 300), (90, 90, 90, 120))
    out = apply_watermark(img, TEXT, 0.5)
    assert out.mode == "RGBA"
    left, top, _, _ = changed_bbox(img, out)
    untouched = out.getchannel("A").crop((0, 0, 300, top))
    assert untouched.getextrema() == (120, 120)


def test_does_not_modify_input(gray):
    original = gray.copy()
    apply_watermark(gray, TEXT, 1.0)
    assert changed_bbox(gray, original) is None


@pytest.mark.parametrize("opacity", [-0.1, 1.5])
def test_invalid_opacity(gray, opacity):
    with pytest.raises(ValueError):
        apply_watermark(gray, TEXT, opacity)
