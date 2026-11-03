"""Filtro de viñeta: oscurece los bordes con un degradado radial."""

from __future__ import annotations

from functools import lru_cache

from PIL import Image


@lru_cache(maxsize=32)
def _vignette_mask(size: tuple[int, int], strength: float) -> Image.Image:
    """Máscara "L": 0 en el centro (sin cambio) y ``255 * strength`` en las esquinas.

    Parte de ``Image.radial_gradient`` (valor = distancia al centro) y aplica una
    curva cuadrática para que el centro quede limpio y la caída hacia los bordes
    sea suave. No se debe modificar la imagen devuelta: está en caché.
    """
    gradient = Image.radial_gradient("L")
    max_dist = gradient.getextrema()[1]  # distancia a la esquina (~181)
    lut = [round(min(1.0, v / max_dist) ** 2 * 255 * strength) for v in range(256)]
    return gradient.point(lut).resize(size, Image.Resampling.BICUBIC)


def apply_vignette(img: Image.Image, strength: float) -> Image.Image:
    """Devuelve una copia de ``img`` con los bordes oscurecidos.

    ``strength`` va de 0 (sin efecto) a 1 (esquinas negras). En imágenes RGBA
    solo se oscurecen los colores; el canal alfa se conserva intacto.
    """
    if not 0.0 <= strength <= 1.0:
        raise ValueError(f"strength debe estar entre 0 y 1 (recibido: {strength})")
    if strength == 0:
        return img.copy()

    mask = _vignette_mask(img.size, strength)
    rgb = img.convert("RGB")
    black = Image.new("RGB", img.size, (0, 0, 0))
    darkened = Image.composite(black, rgb, mask)

    if img.mode == "RGBA":
        darkened.putalpha(img.getchannel("A"))
    return darkened
