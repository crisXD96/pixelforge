from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

from pixelforge import pipeline
from pixelforge.cli import main
from pixelforge.config import Config
from pixelforge.gallery import build_gallery, render_html
from pixelforge.pipeline import ProcessedImage


class TagCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags: list[tuple[str, dict]] = []
        self.text: list[str] = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.text.append(data)

    def find(self, tag, **attrs):
        return [a for t, a in self.tags if t == tag and all(a.get(k) == v for k, v in attrs.items())]

    def by_class(self, tag, cls):
        return [a for t, a in self.tags if t == tag and cls in (a.get("class") or "").split()]

    @property
    def all_text(self):
        return " ".join("".join(self.text).split())


def parse(html_text: str) -> TagCollector:
    collector = TagCollector()
    collector.feed(html_text)
    return collector


def item(name: str, full=True, size=(800, 600)) -> ProcessedImage:
    out = pipeline.output_name(Path(name))
    return ProcessedImage(
        source=Path(name),
        thumb=Path("thumbs") / out,
        full=Path("full") / out if full else None,
        full_size=size if full else None,
    )


CONFIG = Config()


def test_one_card_per_image():
    doc = parse(render_html([item("a.jpg"), item("b.png"), item("c.jpeg")], CONFIG))
    assert len(doc.by_class("li", "card")) == 3
    assert len(doc.by_class("div", "lightbox")) == 3
    assert "3 imágenes" in doc.all_text


def test_page_basics():
    html_text = render_html([item("a.jpg")], CONFIG, now=datetime(2026, 11, 3, 10, 30))
    doc = parse(html_text)
    assert html_text.lstrip().lower().startswith("<!doctype html>")
    assert doc.find("html", lang="es")
    assert doc.find("meta", name="viewport")
    assert doc.find("link", rel="stylesheet", href="styles.css")
    text = doc.all_text
    assert "1 imagen" in text and "300 × 300" in text and "03/11/2026 10:30" in text
    assert "Generado con PixelForge" in text
    assert "© PixelForge ·" not in text  # pie sin texto redundante


def test_card_opens_lightbox_with_full_image():
    doc = parse(render_html([item("coche.jpg")], CONFIG))
    (card_link,) = doc.by_class("a", "card-link")
    assert card_link["href"] == "#img-1"

    thumb, full = doc.find("img")
    assert thumb["src"] == "thumbs/coche_jpg.jpg"
    assert (thumb["width"], thumb["height"], thumb["loading"]) == ("300", "300", "lazy")
    assert thumb["alt"] == "coche.jpg"

    (box,) = doc.by_class("div", "lightbox")
    assert box["id"] == "img-1"
    assert full["src"] == "full/coche_jpg.jpg"
    assert (full["width"], full["height"]) == ("800", "600")
    assert full["loading"] == "lazy"  # no se descarga hasta abrir el visor
    (original,) = doc.by_class("a", "lb-original")
    assert original["href"] == "full/coche_jpg.jpg"
    assert "800 × 600" in doc.all_text


def test_lightbox_close_does_not_target_existing_element():
    html_text = render_html([item("a.jpg")], CONFIG)
    doc = parse(html_text)
    (close,) = doc.by_class("a", "lb-close")
    assert close["href"] == "#_"
    assert 'id="_"' not in html_text


def test_single_image_has_no_prev_next():
    doc = parse(render_html([item("a.jpg")], CONFIG))
    assert doc.by_class("a", "lb-prev") == [] and doc.by_class("a", "lb-next") == []


def test_prev_next_wrap_around():
    doc = parse(render_html([item("a.jpg"), item("b.jpg"), item("c.jpg")], CONFIG))
    prevs = [a["href"] for a in doc.by_class("a", "lb-prev")]
    nexts = [a["href"] for a in doc.by_class("a", "lb-next")]
    assert prevs == ["#img-3", "#img-1", "#img-2"]
    assert nexts == ["#img-2", "#img-3", "#img-1"]


def test_without_full_card_is_not_clickable():
    doc = parse(render_html([item("a.jpg", full=False)], CONFIG))
    assert doc.find("a") == []
    assert doc.by_class("div", "lightbox") == []
    assert len(doc.find("img")) == 1


def test_mixed_full_and_no_full_navigation_skips_static():
    doc = parse(render_html([item("a.jpg"), item("b.jpg", full=False), item("c.jpg")], CONFIG))
    assert [a["href"] for a in doc.by_class("a", "card-link")] == ["#img-1", "#img-2"]
    assert [a["href"] for a in doc.by_class("a", "lb-next")] == ["#img-2", "#img-1"]


def test_weird_names_are_escaped():
    name = 'mi <foto> & "amigos" #1.jpg'
    html_text = render_html([item(name)], CONFIG)
    assert "<foto>" not in html_text  # no se inyecta HTML
    doc = parse(html_text)
    thumb, full = doc.find("img")
    assert thumb["alt"] == name
    expected = pipeline.output_name(Path(name))
    assert unquote(thumb["src"]) == "thumbs/" + expected
    assert unquote(full["src"]) == "full/" + expected
    assert " " not in thumb["src"] and "#" not in thumb["src"]


def test_build_writes_files_and_links_exist(tmp_path, make_image):
    make_image("coche.jpg")
    make_image("con espacios & signos.png", format="PNG")
    config = Config(input_dir=tmp_path / "input", output_dir=tmp_path / "output")
    result = pipeline.run(config)

    index = build_gallery(result.processed, config)
    assert index == tmp_path / "output" / "index.html"
    assert (tmp_path / "output" / "styles.css").read_text(encoding="utf-8").strip()

    doc = parse(index.read_text(encoding="utf-8"))
    files = [a["href"] for a in doc.find("a") if not a["href"].startswith("#")]
    files += [i["src"] for i in doc.find("img")]
    assert len(files) == 6  # por imagen: thumb + full en visor + enlace "Abrir original"
    for ref in files:
        assert (tmp_path / "output" / unquote(ref)).is_file(), ref

    ids = {a["id"] for _, a in doc.tags if "id" in a}
    for a in doc.find("a"):
        if a["href"].startswith("#") and a["href"] != "#_":
            assert a["href"][1:] in ids, a["href"]


def test_cli_generates_gallery(tmp_path, make_image):
    make_image("a.jpg")
    out = tmp_path / "output"
    assert main(["--input", str(tmp_path / "input"), "--output", str(out)]) == 0
    assert (out / "index.html").is_file() and (out / "styles.css").is_file()


def test_cli_no_gallery_without_images(tmp_path):
    (tmp_path / "input").mkdir()
    out = tmp_path / "output"
    assert main(["--input", str(tmp_path / "input"), "--output", str(out)]) == 0
    assert not (out / "index.html").exists()
