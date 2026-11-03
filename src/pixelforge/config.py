"""Parámetros del pipeline y su validación."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png"})

DEFAULT_SIZE = 300
DEFAULT_VIGNETTE = 0.6
DEFAULT_WATERMARK = "© PixelForge"
DEFAULT_OPACITY = 0.5
DEFAULT_FULL_SIZE = 1600


@dataclass(frozen=True)
class Config:
    """Configuración inmutable de una ejecución del pipeline.

    Lanza ``ValueError`` si algún parámetro está fuera de rango.
    """

    input_dir: Path = Path("input")
    output_dir: Path = Path("output")
    size: int = DEFAULT_SIZE
    vignette_strength: float = DEFAULT_VIGNETTE
    watermark_text: str = DEFAULT_WATERMARK
    watermark_opacity: float = DEFAULT_OPACITY
    full_max_size: int = DEFAULT_FULL_SIZE  # 0 = no generar versión grande

    def __post_init__(self) -> None:
        # Normaliza rutas aunque lleguen como str.
        object.__setattr__(self, "input_dir", Path(self.input_dir))
        object.__setattr__(self, "output_dir", Path(self.output_dir))

        if self.size <= 0:
            raise ValueError(f"size debe ser mayor que 0 (recibido: {self.size})")
        if self.full_max_size < 0:
            raise ValueError(
                f"full_max_size debe ser 0 (desactivado) o mayor (recibido: {self.full_max_size})"
            )
        if not 0.0 <= self.vignette_strength <= 1.0:
            raise ValueError(
                f"vignette_strength debe estar entre 0 y 1 (recibido: {self.vignette_strength})"
            )
        if not 0.0 <= self.watermark_opacity <= 1.0:
            raise ValueError(
                f"watermark_opacity debe estar entre 0 y 1 (recibido: {self.watermark_opacity})"
            )
        if self.input_dir.resolve() == self.output_dir.resolve():
            raise ValueError("input_dir y output_dir no pueden ser la misma carpeta")

    @property
    def watermark_alpha(self) -> int:
        """Opacidad del watermark en escala 0-255, lista para Pillow."""
        return round(self.watermark_opacity * 255)
