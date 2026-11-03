import pytest
from PIL import Image, ImageChops

from pixelforge.vignette import apply_vignette

GRAY = (200, 200, 200)


def brightness(img, xy):
    return sum(img.getpixel(xy)[:3]) / 3


@pytest.fixture
def gray():
    return Image.new("RGB", (300, 300), GRAY)


def test_keeps_size_and_mode(gray):
    out = apply_vignette(gray, 0.6)
    assert out.size == gray.size and out.mode == "RGB"


def test_corners_darker_than_center(gray):
    out = apply_vignette(gray, 0.6)
    center = brightness(out, (150, 150))
    assert center == pytest.approx(200, abs=2)  # el centro no se toca
    for corner in [(0, 0), (299, 0), (0, 299), (299, 299)]:
        assert brightness(out, corner) < center * 0.5


def test_radial_falloff(gray):
    out = apply_vignette(gray, 0.6)
    center = brightness(out, (150, 150))
    edge = brightness(out, (150, 0))  # mitad del borde superior
    corner = brightness(out, (0, 0))
    assert center > edge > corner


def test_zero_strength_is_identity(gray):
    out = apply_vignette(gray, 0)
    assert ImageChops.difference(out, gray).getbbox() is None
    assert out is not gray


def test_stronger_means_darker(gray):
    soft = brightness(apply_vignette(gray, 0.3), (0, 0))
    hard = brightness(apply_vignette(gray, 0.9), (0, 0))
    assert hard < soft


def test_rgba_alpha_preserved():
    img = Image.new("RGBA", (200, 200), (200, 200, 200, 90))
    out = apply_vignette(img, 0.8)
    assert out.mode == "RGBA"
    assert out.getchannel("A").getextrema() == (90, 90)
    assert brightness(out, (0, 0)) < brightness(out, (100, 100))


def test_does_not_modify_input(gray):
    original = gray.copy()
    apply_vignette(gray, 0.9)
    assert ImageChops.difference(gray, original).getbbox() is None


@pytest.mark.parametrize("strength", [-0.1, 1.1])
def test_invalid_strength(gray, strength):
    with pytest.raises(ValueError):
        apply_vignette(gray, strength)
