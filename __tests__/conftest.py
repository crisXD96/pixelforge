from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def make_image(tmp_path):
    """Crea una imagen sintética en disco y devuelve su ruta."""

    def _make(
        name: str,
        size: tuple[int, int] = (1200, 800),
        mode: str = "RGB",
        color=(200, 120, 40),
        folder: Path | None = None,
        **save_kwargs,
    ) -> Path:
        folder = folder or tmp_path / "input"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / name
        Image.new(mode, size, color).save(path, **save_kwargs)
        return path

    return _make


@pytest.fixture
def make_corrupt(tmp_path):
    def _make(name: str = "rota.jpg", folder: Path | None = None) -> Path:
        folder = folder or tmp_path / "input"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / name
        path.write_bytes(b"esto no es una imagen")
        return path

    return _make
