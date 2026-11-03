"""Generación de thumbnails cuadrados."""

from __future__ import annotations

from PIL import Image, ImageOps


def make_thumbnail(img: Image.Image, size: int) -> Image.Image:
    """Recorta al centro y redimensiona a exactamente ``size`` x ``size``.

    Las imágenes más pequeñas que ``size`` se amplían para que la galería
    tenga una cuadrícula uniforme. Conserva el modo (RGB/RGBA) de entrada.
    """
    return ImageOps.fit(
        img,
        (size, size),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )


def fit_within(img: Image.Image, max_size: int) -> Image.Image:
    """Reduce ``img`` para que su lado mayor sea ≤ ``max_size``, sin recortar.

    Mantiene la proporción y nunca amplía: si ya cabe, devuelve una copia.
    """
    out = img.copy()
    out.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    return out
