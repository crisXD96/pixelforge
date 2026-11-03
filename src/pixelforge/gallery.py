"""Generación de la galería web estática (index.html + styles.css).

Cada tarjeta abre un visor (lightbox) hecho solo con CSS ``:target``; un
script mínimo añade atajos de teclado, pero la página funciona sin JavaScript.
Si una imagen no tiene versión grande (``--full-size 0``), su tarjeta no es
clicable.
"""

from __future__ import annotations

import html
from datetime import datetime
from importlib.resources import files
from pathlib import Path
from string import Template
from typing import Iterable
from urllib.parse import quote

from pixelforge.config import Config
from pixelforge.pipeline import FULL_SUBDIR, THUMBS_SUBDIR, ProcessedImage

INDEX_NAME = "index.html"
CSS_NAME = "styles.css"
TITLE = "Galería PixelForge"
CLOSE_HASH = "#_"  # ancla inexistente: cierra el visor sin saltar al inicio de la página

_TEMPLATES = files("pixelforge") / "templates"


def _url(subdir: str, name: str) -> str:
    """Ruta relativa segura para usar en ``src``/``href`` (espacios, #, & …)."""
    return html.escape(f"{subdir}/{quote(name)}", quote=True)


def _size_label(item: ProcessedImage) -> str:
    return f"{item.full_size[0]} × {item.full_size[1]}" if item.full_size else ""


def _card(item: ProcessedImage, index: int, lightbox_id: str | None, thumb_size: int) -> str:
    title = html.escape(item.source.name)
    size = _size_label(item)
    size_html = f'<span class="card-size">{size}</span>' if size else ""
    img = (
        f'<img src="{_url(THUMBS_SUBDIR, item.thumb.name)}" alt="{title}" '
        f'width="{thumb_size}" height="{thumb_size}" loading="lazy" decoding="async">'
    )
    inner = (
        f'<span class="card-media">{img}'
        + ('<span class="card-zoom" aria-hidden="true">⤢ Ampliar</span>' if lightbox_id else "")
        + "</span>"
        f'<span class="card-body"><span class="card-title" title="{title}">{title}</span>{size_html}</span>'
    )
    if lightbox_id:
        wrapper = f'<a class="card-link" href="#{lightbox_id}" aria-label="Ampliar {title}">{inner}</a>'
    else:
        wrapper = f'<div class="card-link">{inner}</div>'
    return f'      <li class="card" style="--i: {index}">{wrapper}</li>'


def _lightbox(item: ProcessedImage, lightbox_id: str, prev_id: str | None, next_id: str | None) -> str:
    title = html.escape(item.source.name)
    full_url = _url(FULL_SUBDIR, item.full.name)
    width, height = item.full_size
    nav = ""
    if prev_id and next_id:
        nav = (
            f'\n    <a class="lb-btn lb-prev" href="#{prev_id}" aria-label="Imagen anterior">‹</a>'
            f'\n    <a class="lb-btn lb-next" href="#{next_id}" aria-label="Imagen siguiente">›</a>'
        )
    return (
        f'  <div class="lightbox" id="{lightbox_id}" role="dialog" aria-label="{title}">\n'
        f'    <a class="lb-backdrop" href="{CLOSE_HASH}" tabindex="-1" aria-hidden="true"></a>\n'
        '    <figure class="lb-figure">\n'
        f'      <img src="{full_url}" alt="{title}" width="{width}" height="{height}" '
        'loading="lazy" decoding="async">\n'
        f"      <figcaption><span><strong>{title}</strong> · {_size_label(item)}</span>"
        f'<a class="lb-original" href="{full_url}" target="_blank" rel="noopener">Abrir original ↗</a>'
        "</figcaption>\n"
        "    </figure>\n"
        f'    <a class="lb-btn lb-close" href="{CLOSE_HASH}" aria-label="Cerrar">✕</a>{nav}\n'
        "  </div>"
    )


def render_html(items: Iterable[ProcessedImage], config: Config, now: datetime | None = None) -> str:
    """Devuelve el HTML de la galería (no escribe nada a disco)."""
    items = list(items)
    now = now or datetime.now()

    # Solo las imágenes con versión grande abren visor; la navegación da la vuelta.
    zoomable = [i for i, item in enumerate(items) if item.full is not None]
    ids = {i: f"img-{n + 1}" for n, i in enumerate(zoomable)}

    cards = [_card(item, i, ids.get(i), config.size) for i, item in enumerate(items)]
    lightboxes = []
    for n, i in enumerate(zoomable):
        multiple = len(zoomable) > 1
        prev_id = ids[zoomable[n - 1]] if multiple else None
        next_id = ids[zoomable[(n + 1) % len(zoomable)]] if multiple else None
        lightboxes.append(_lightbox(items[i], ids[i], prev_id, next_id))

    template = Template((_TEMPLATES / "gallery.html").read_text(encoding="utf-8"))
    return template.substitute(
        title=html.escape(TITLE),
        count=len(items),
        count_noun="imagen" if len(items) == 1 else "imágenes",
        thumb_size=f"{config.size} × {config.size}",
        generated=now.strftime("%d/%m/%Y %H:%M"),
        cards="\n".join(cards),
        lightboxes="\n".join(lightboxes),
    )


def build_gallery(items: Iterable[ProcessedImage], config: Config) -> Path:
    """Escribe ``index.html`` y ``styles.css`` en ``config.output_dir`` y devuelve la ruta del índice.

    Los enlaces son relativos: la galería se abre directamente desde disco sin servidor.
    """
    config.output_dir.mkdir(parents=True, exist_ok=True)
    index = config.output_dir / INDEX_NAME
    index.write_text(render_html(items, config), encoding="utf-8")
    (config.output_dir / CSS_NAME).write_text(
        (_TEMPLATES / CSS_NAME).read_text(encoding="utf-8"), encoding="utf-8"
    )
    return index
