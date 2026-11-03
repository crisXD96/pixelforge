"""Watermark de texto semitransparente en la esquina inferior derecha."""

from __future__ import annotations

from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

# Se prueban en orden; Pillow las busca también en la carpeta de fuentes del sistema.
FONT_CANDIDATES = ("DejaVuSans.ttf", "arial.ttf", "Arial.ttf", "Helvetica.ttc")

FONT_RATIO = 0.07     # tamaño de fuente respecto al lado menor de la imagen
MARGIN_RATIO = 0.04   # margen respecto al lado menor
MIN_FONT_SIZE = 8     # tamaño inicial mínimo; se reduce más solo si el texto no cabe
SHADOW_RATIO = 0.5    # opacidad de la sombra respecto a la del texto


@lru_cache(maxsize=32)
def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def _fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, start_size: int):
    """Devuelve la fuente más grande (≤ ``start_size``) con la que ``text`` cabe en ``max_width``.

    Prefiere que el texto quepa aunque quede pequeño antes que recortarlo.
    """
    size = start_size
    while True:
        font = _load_font(size)
        left, _, right, _ = draw.textbbox((0, 0), text, font=font)
        if right - left <= max_width or size <= 1:
            return font
        size -= 1


def apply_watermark(img: Image.Image, text: str, opacity: float) -> Image.Image:
    """Devuelve una copia de ``img`` con ``text`` en blanco semitransparente abajo a la derecha.

    ``opacity`` va de 0 (invisible) a 1 (opaco). El texto escala con la imagen,
    se reduce si no cabe, y lleva una sombra sutil para leerse sobre fondos
    claros. Conserva el modo de entrada (RGB o RGBA).
    """
    if not 0.0 <= opacity <= 1.0:
        raise ValueError(f"opacity debe estar entre 0 y 1 (recibido: {opacity})")
    if opacity == 0 or not text.strip():
        return img.copy()

    width, height = img.size
    short_side = min(width, height)
    margin = max(2, round(short_side * MARGIN_RATIO))
    alpha = round(opacity * 255)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _fit_font(
        draw, text,
        max_width=width - 2 * margin,
        start_size=max(MIN_FONT_SIZE, round(short_side * FONT_RATIO)),
    )

    # Posición tal que el borde derecho/inferior real del texto quede a `margin` del borde.
    _, _, right, bottom = draw.textbbox((0, 0), text, font=font)
    x = width - margin - right
    y = height - margin - bottom
    shadow = max(1, round(font.size / 14)) if hasattr(font, "size") else 1

    draw.text((x + shadow, y + shadow), text, font=font, fill=(0, 0, 0, round(alpha * SHADOW_RATIO)))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, alpha))

    result = Image.alpha_composite(img.convert("RGBA"), overlay)
    return result if img.mode == "RGBA" else result.convert(img.mode)
