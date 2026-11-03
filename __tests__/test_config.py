from pathlib import Path

import pytest

from pixelforge.cli import parse_config
from pixelforge.config import Config


def test_defaults():
    config = Config()
    assert config.size == 300
    assert config.watermark_text == "© PixelForge"
    assert config.watermark_alpha == 128
    assert isinstance(config.input_dir, Path)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"size": 0},
        {"full_max_size": -1},
        {"vignette_strength": 1.5},
        {"watermark_opacity": -0.1},
        {"input_dir": "same", "output_dir": "same"},
    ],
)
def test_invalid_values_raise(kwargs):
    with pytest.raises(ValueError):
        Config(**kwargs)


def test_cli_builds_config():
    config, verbose = parse_config(["--size", "200", "--opacity", "0.3", "-v"])
    assert config.size == 200
    assert config.watermark_opacity == 0.3
    assert verbose is True


def test_cli_rejects_invalid_value():
    with pytest.raises(SystemExit) as exc:
        parse_config(["--vignette", "2"])
    assert exc.value.code == 2
