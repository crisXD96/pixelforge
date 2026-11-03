import pytest
from PIL import Image

from pixelforge.loader import ImageLoadError, find_images, load_image


def test_find_images_filters_and_sorts(tmp_path, make_image):
    folder = tmp_path / "input"
    make_image("b.PNG", format="PNG")
    make_image("a.jpg")
    make_image("c.JPEG", format="JPEG")
    (folder / "notas.txt").write_text("x")
    (folder / "sub").mkdir()
    make_image("dentro.jpg", folder=folder / "sub")

    names = [p.name for p in find_images(folder)]
    assert names == ["a.jpg", "b.PNG", "c.JPEG"]


def test_find_images_missing_folder(tmp_path):
    with pytest.raises(FileNotFoundError):
        find_images(tmp_path / "no-existe")


def test_load_jpg_is_rgb(make_image):
    img = load_image(make_image("foto.jpg"))
    assert img.mode == "RGB"
    assert img.size == (1200, 800)


def test_load_png_keeps_alpha(make_image):
    img = load_image(make_image("logo.png", mode="RGBA", color=(255, 0, 0, 128)))
    assert img.mode == "RGBA"


def test_load_png_without_alpha_is_rgb(make_image):
    img = load_image(make_image("plano.png"))
    assert img.mode == "RGB"


def test_load_applies_exif_orientation(make_image):
    exif = Image.Exif()
    exif[0x0112] = 6  # rotar 90°: así guardan muchas cámaras de celular
    img = load_image(make_image("celular.jpg", exif=exif))
    assert img.size == (800, 1200)


def test_load_corrupt_raises(make_corrupt):
    with pytest.raises(ImageLoadError):
        load_image(make_corrupt())
