"""Búsqueda y carga de imágenes de entrada."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from pixelforge.config import SUPPORTED_EXTENSIONS


class ImageLoadError(Exception):
    """La imagen no se pudo abrir o decodificar."""


def find_images(input_dir: Path) -> list[Path]:
    """Devuelve las imágenes JPG/PNG de ``input_dir`` (sin subcarpetas), ordenadas por nombre.

    La extensión se compara sin distinguir mayúsculas. Lanza ``FileNotFoundError``
    si la carpeta no existe.
    """
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de entrada: {input_dir}")
    return sorted(
        (p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS),
        key=lambda p: p.name.lower(),
    )


def _has_transparency(img: Image.Image) -> bool:
    return img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info)


def load_image(path: Path) -> Image.Image:
    """Abre una imagen, aplica la orientación EXIF y la normaliza a RGB o RGBA.

    Conserva el canal alfa solo si la imagen original tiene transparencia.
    Lanza ``ImageLoadError`` si el archivo está corrupto o no es una imagen.
    """
    try:
        with Image.open(path) as img:
            img.load()
            img = ImageOps.exif_transpose(img)
            mode = "RGBA" if _has_transparency(img) else "RGB"
            # convert() siempre devuelve una copia, así el archivo puede cerrarse.
            return img.convert(mode)
    except UnidentifiedImageError as exc:
        # El mensaje de Pillow repite la ruta completa; uno corto es más legible.
        raise ImageLoadError(f"{path.name}: no es una imagen válida o está dañada") from exc
    except (OSError, Image.DecompressionBombError) as exc:
        raise ImageLoadError(f"{path.name}: {exc}") from exc
