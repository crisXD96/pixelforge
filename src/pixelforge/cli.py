"""Interfaz de línea de comandos de PixelForge."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence

from pixelforge import __version__, pipeline
from pixelforge.gallery import build_gallery
from pixelforge.config import (
    DEFAULT_FULL_SIZE,
    DEFAULT_OPACITY,
    DEFAULT_SIZE,
    DEFAULT_VIGNETTE,
    DEFAULT_WATERMARK,
    Config,
)

logger = logging.getLogger("pixelforge")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pixelforge",
        description="Genera thumbnails con viñeta y watermark, y una galería web responsive.",
    )
    parser.add_argument(
        "--input", type=Path, default=Path("input"),
        help="carpeta con imágenes JPG/PNG (por defecto: input)",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("output"),
        help="carpeta de salida (por defecto: output)",
    )
    parser.add_argument(
        "--size", type=int, default=DEFAULT_SIZE,
        help=f"lado del thumbnail cuadrado en px (por defecto: {DEFAULT_SIZE})",
    )
    parser.add_argument(
        "--full-size", type=int, default=DEFAULT_FULL_SIZE,
        help=f"lado mayor máximo de la versión grande en px; 0 = no generarla "
             f"(por defecto: {DEFAULT_FULL_SIZE})",
    )
    parser.add_argument(
        "--vignette", type=float, default=DEFAULT_VIGNETTE,
        help=f"intensidad de la viñeta, 0-1 (por defecto: {DEFAULT_VIGNETTE})",
    )
    parser.add_argument(
        "--watermark", default=DEFAULT_WATERMARK,
        help="texto del watermark (por defecto: '%(default)s')",
    )
    parser.add_argument(
        "--opacity", type=float, default=DEFAULT_OPACITY,
        help=f"opacidad del watermark, 0-1 (por defecto: {DEFAULT_OPACITY})",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="muestra mensajes de depuración",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def parse_config(argv: Sequence[str] | None = None) -> tuple[Config, bool]:
    """Convierte los argumentos en un ``Config``. Sale con error de uso si son inválidos."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = Config(
            input_dir=args.input,
            output_dir=args.output,
            size=args.size,
            vignette_strength=args.vignette,
            watermark_text=args.watermark,
            watermark_opacity=args.opacity,
            full_max_size=args.full_size,
        )
    except ValueError as exc:
        parser.error(str(exc))
    return config, args.verbose


def main(argv: Sequence[str] | None = None) -> int:
    config, verbose = parse_config(argv)
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    logger.debug("Configuración: %s", config)

    try:
        result = pipeline.run(config)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1

    logger.info(
        "Listo: %d procesadas, %d omitidas. Salida en %s",
        len(result.processed), len(result.skipped), config.output_dir,
    )

    if result.processed:
        try:
            index = build_gallery(result.processed, config)
        except OSError as exc:
            logger.error("No se pudo escribir la galería: %s", exc)
            return 1
        logger.info("Galería: %s", index)
    else:
        logger.info("Sin imágenes procesadas: no se genera galería.")

    # Falla solo si había imágenes y ninguna se pudo procesar.
    return 1 if result.skipped and not result.processed else 0


if __name__ == "__main__":
    sys.exit(main())
