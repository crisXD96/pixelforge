from pathlib import Path

import pytest
from PIL import Image, ImageChops

from pixelforge import pipeline
from pixelforge.cli import main
from pixelforge.config import Config


@pytest.mark.parametrize(
    ("source", "expected"),
    [("foto.jpg", "foto_jpg.jpg"), ("foto.JPEG", "foto_jpeg.jpg"), ("foto.png", "foto_png.png")],
)
def test_output_name_avoids_collisions(source, expected):
    assert pipeline.output_name(Path(source)) == expected


def test_run_processes_valid_and_skips_corrupt(tmp_path, make_image, make_corrupt):
    make_image("a.jpg")
    make_image("b.png", mode="RGBA", color=(0, 0, 255, 100), format="PNG")
    make_corrupt("rota.jpg")
    config = Config(input_dir=tmp_path / "input", output_dir=tmp_path / "output")

    result = pipeline.run(config)

    assert sorted(r.thumb.name for r in result.processed) == ["a_jpg.jpg", "b_png.png"]
    assert [p.name for p, _ in result.skipped] == ["rota.jpg"]
    assert "no es una imagen válida" in result.skipped[0][1]
    assert str(tmp_path) not in result.skipped[0][1]  # mensaje corto, sin ruta completa

    with Image.open(tmp_path / "output" / "thumbs" / "a_jpg.jpg") as img:
        assert img.size == (300, 300) and img.format == "JPEG"
    with Image.open(tmp_path / "output" / "thumbs" / "b_png.png") as img:
        assert img.size == (300, 300) and img.mode == "RGBA"


def test_run_applies_vignette(tmp_path, make_image):
    make_image("gris.png", color=(200, 200, 200), format="PNG")
    pipeline.run(Config(input_dir=tmp_path / "input", output_dir=tmp_path / "output"))

    with Image.open(tmp_path / "output" / "thumbs" / "gris_png.png") as img:
        center = img.getpixel((150, 150))[0]
        corner = img.getpixel((0, 0))[0]
    assert corner < center


def test_run_applies_watermark(tmp_path, make_image):
    make_image("gris.jpg", color=(120, 120, 120))
    outputs = {}
    for opacity in (0.0, 0.8):
        out_dir = tmp_path / f"out_{opacity}"
        pipeline.run(Config(input_dir=tmp_path / "input", output_dir=out_dir, watermark_opacity=opacity))
        outputs[opacity] = Image.open(out_dir / "thumbs" / "gris_jpg.jpg").convert("RGB")

    plain, marked = outputs[0.0], outputs[0.8]
    diff = ImageChops.difference(plain.crop((150, 230, 300, 300)), marked.crop((150, 230, 300, 300)))
    assert diff.getextrema()[0][1] > 60  # el texto se nota abajo a la derecha
    top = ImageChops.difference(plain.crop((0, 0, 300, 150)), marked.crop((0, 0, 300, 150)))
    assert max(hi for _, hi in top.getextrema()) <= 3  # arriba no cambia (salvo ruido JPEG)


def test_run_generates_full_version(tmp_path, make_image):
    make_image("grande.jpg", size=(3200, 2000))
    make_image("chica.png", size=(640, 400), format="PNG")
    result = pipeline.run(Config(input_dir=tmp_path / "input", output_dir=tmp_path / "output"))

    by_name = {r.source.name: r for r in result.processed}
    assert by_name["grande.jpg"].full_size == (1600, 1000)   # reducida, misma proporción
    assert by_name["chica.png"].full_size == (640, 400)      # no se amplía
    with Image.open(tmp_path / "output" / "full" / "grande_jpg.jpg") as img:
        assert img.size == (1600, 1000) and img.format == "JPEG"
    with Image.open(tmp_path / "output" / "full" / "chica_png.png") as img:
        assert img.format == "PNG"


def test_full_version_has_effects(tmp_path, make_image):
    make_image("gris.png", size=(800, 500), color=(120, 120, 120), format="PNG")
    pipeline.run(Config(input_dir=tmp_path / "input", output_dir=tmp_path / "output"))

    with Image.open(tmp_path / "output" / "full" / "gris_png.png") as img:
        center = img.getpixel((400, 150))[0]
        corner = img.getpixel((0, 0))[0]
        text_area = img.crop((500, 400, 800, 500)).convert("L").getextrema()[1]
    assert corner < center          # viñeta
    assert text_area > center + 30  # watermark claro abajo a la derecha


def test_full_size_zero_disables_full(tmp_path, make_image):
    make_image("a.jpg")
    config = Config(input_dir=tmp_path / "input", output_dir=tmp_path / "output", full_max_size=0)
    result = pipeline.run(config)

    assert result.processed[0].full is None
    assert not (tmp_path / "output" / "full").exists()
    assert (tmp_path / "output" / "thumbs" / "a_jpg.jpg").exists()


def test_run_empty_folder(tmp_path):
    (tmp_path / "input").mkdir()
    result = pipeline.run(Config(input_dir=tmp_path / "input", output_dir=tmp_path / "output"))
    assert result.processed == [] and result.skipped == []


def test_cli_exit_codes(tmp_path, make_image, make_corrupt):
    out = str(tmp_path / "output")
    assert main(["--input", str(tmp_path / "no-existe"), "--output", out]) == 1

    make_corrupt("rota.jpg")
    assert main(["--input", str(tmp_path / "input"), "--output", out]) == 1  # todas fallan

    make_image("ok.jpg")
    assert main(["--input", str(tmp_path / "input"), "--output", out]) == 0
