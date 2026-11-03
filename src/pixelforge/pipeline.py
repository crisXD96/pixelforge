"""Orquestación del pipeline.

Por cada imagen de entrada genera dos salidas con los mismos efectos:

- ``thumbs/``: thumbnail cuadrado (recorte centrado) → viñeta → watermark.
- ``full/``: versión grande (sin recorte, lado mayor ≤ ``full_max_size``) → viñeta → watermark.

El watermark va después de la viñeta para que el texto no quede oscurecido.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from pixelforge.config import Config
from pixelforge.loader import ImageLoadError, find_images, load_image
from pixelforge.thumbnail import fit_within, make_thumbnail
from pixelforge.vignette import apply_vignette
from pixelforge.watermark import apply_watermark

logger = logging.getLogger(__name__)

THUMBS_SUBDIR = "thumbs"
FULL_SUBDIR = "full"
JPEG_QUALITY = 88


@dataclass(frozen=True)
class ProcessedImage:
    """Salidas generadas para una imagen. Las rutas son absolutas o relativas al cwd."""

    source: Path
    thumb: Path
    full: Path | None          # None si --full-size 0
    full_size: tuple[int, int] | None


@dataclass
class PipelineResult:
    processed: list[ProcessedImage] = field(default_factory=list)
    skipped: list[tuple[Path, str]] = field(default_factory=list)


def output_name(source: Path) -> str:
    """Nombre de salida que evita choques: ``foto.jpg`` → ``foto_jpg.jpg``, ``foto.png`` → ``foto_png.png``.

    PNG se mantiene como PNG (puede tener transparencia); JPG/JPEG salen como ``.jpg``.
    """
    ext = source.suffix.lower().lstrip(".")
    out_ext = "png" if ext == "png" else "jpg"
    return f"{source.stem}_{ext}.{out_ext}"


def save_image(img: Image.Image, dest: Path) -> None:
    if dest.suffix == ".png":
        img.save(dest, format="PNG", optimize=True)
    else:
        img.convert("RGB").save(
            dest, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True
        )


def apply_effects(img: Image.Image, config: Config) -> Image.Image:
    vignetted = apply_vignette(img, config.vignette_strength)
    return apply_watermark(vignetted, config.watermark_text, config.watermark_opacity)


def process_thumbnail(img: Image.Image, config: Config) -> Image.Image:
    return apply_effects(make_thumbnail(img, config.size), config)


def process_full(img: Image.Image, config: Config) -> Image.Image:
    return apply_effects(fit_within(img, config.full_max_size), config)


def _process_one(path: Path, config: Config) -> ProcessedImage:
    img = load_image(path)
    name = output_name(path)

    thumb_path = config.output_dir / THUMBS_SUBDIR / name
    save_image(process_thumbnail(img, config), thumb_path)

    full_path = full_size = None
    if config.full_max_size:
        full = process_full(img, config)
        full_path = config.output_dir / FULL_SUBDIR / name
        save_image(full, full_path)
        full_size = full.size

    return ProcessedImage(source=path, thumb=thumb_path, full=full_path, full_size=full_size)


def run(config: Config) -> PipelineResult:
    """Procesa todas las imágenes de ``config.input_dir``.

    Un archivo que no se puede leer o guardar se registra en ``skipped`` y no
    detiene el resto. Lanza ``FileNotFoundError`` si la carpeta de entrada no existe.
    """
    result = PipelineResult()
    images = find_images(config.input_dir)
    if not images:
        logger.warning("No se encontraron imágenes JPG/PNG en %s", config.input_dir)
        return result

    (config.output_dir / THUMBS_SUBDIR).mkdir(parents=True, exist_ok=True)
    if config.full_max_size:
        (config.output_dir / FULL_SUBDIR).mkdir(parents=True, exist_ok=True)

    for path in images:
        try:
            item = _process_one(path, config)
        except ImageLoadError as exc:
            reason = str(exc)
        except OSError as exc:  # p. ej. disco lleno o sin permisos al guardar
            reason = f"{path.name}: no se pudo guardar ({exc.strerror or exc})"
        else:
            detail = f"{THUMBS_SUBDIR}/{item.thumb.name}"
            if item.full:
                detail += f" + {FULL_SUBDIR}/{item.full.name} {item.full_size[0]}x{item.full_size[1]}"
            logger.info("OK: %s -> %s", path.name, detail)
            result.processed.append(item)
            continue

        logger.warning("Omitida: %s", reason)
        result.skipped.append((path, reason))

    return result
