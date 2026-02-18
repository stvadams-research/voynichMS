"""
Format-agnostic image-to-token control streams.

These controls decode images to pixels and serialize visual information into
symbol streams. They test the concept "manuscript as encoded image" without
assuming a specific file format (PNG/JPG/GIF).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


@dataclass
class ImageStreamConfig:
    image_glob: str = "data/raw/scans/jpg/folios_1000/*.jpg"
    max_images: int = 24
    resize_width: int = 256
    quant_levels: int = 16
    target_tokens: int = 230000
    random_state: int = 42
    symbol_alphabet: tuple[str, ...] | None = None


class ImageStreamControlBuilder:
    """Builds multiple image-derived token controls from local image files."""

    def __init__(self, config: ImageStreamConfig | None = None):
        self.config = config or ImageStreamConfig()
        self._rng = np.random.default_rng(self.config.random_state)

    def build_controls(self) -> dict[str, Any]:
        files = self._select_image_files()
        if not files:
            return {"status": "insufficient_data", "reason": "no_images_found", "controls": {}}

        pixel_arrays = []
        per_image_meta = []
        for path in files:
            arr = self._load_grayscale_resized(path)
            pixel_arrays.append(arr)
            per_image_meta.append(
                {
                    "file": str(path),
                    "height": int(arr.shape[0]),
                    "width": int(arr.shape[1]),
                }
            )

        raster = self._quantized_raster_tokens(pixel_arrays)
        snake = self._quantized_snake_tokens(pixel_arrays)
        grad = self._quantized_gradient_tokens(pixel_arrays)

        controls = {
            "image_raster_q16": self._to_target_length(raster),
            "image_snake_q16": self._to_target_length(snake),
            "image_gradient_q16": self._to_target_length(grad),
        }

        return {
            "status": "ok",
            "config": self._config_dict(),
            "source_image_count": len(files),
            "source_images": per_image_meta,
            "controls": controls,
        }

    def _select_image_files(self) -> list[Path]:
        paths = sorted(Path().glob(self.config.image_glob))
        if not paths:
            return []
        if len(paths) <= self.config.max_images:
            return paths

        idx = np.linspace(0, len(paths) - 1, self.config.max_images, dtype=int)
        return [paths[i] for i in idx]

    def _load_grayscale_resized(self, path: Path) -> np.ndarray:
        with Image.open(path) as img:
            gray = img.convert("L")
            w, h = gray.size
            target_w = max(32, self.config.resize_width)
            target_h = max(8, int(round(h * target_w / max(1, w))))
            resized = gray.resize((target_w, target_h), Image.Resampling.BILINEAR)
            return np.asarray(resized, dtype=np.uint8)

    def _quantized_raster_tokens(self, arrays: list[np.ndarray]) -> list[str]:
        out: list[str] = []
        for arr in arrays:
            q = self._quantize(arr)
            out.extend(self._bins_to_tokens(q.ravel()))
        return out

    def _quantized_snake_tokens(self, arrays: list[np.ndarray]) -> list[str]:
        out: list[str] = []
        for arr in arrays:
            q = self._quantize(arr)
            for i, row in enumerate(q):
                values = row if i % 2 == 0 else row[::-1]
                out.extend(self._bins_to_tokens(values))
        return out

    def _quantized_gradient_tokens(self, arrays: list[np.ndarray]) -> list[str]:
        out: list[str] = []
        for arr in arrays:
            arr_f = arr.astype(np.int16)
            dx = np.abs(arr_f[:, 1:] - arr_f[:, :-1])
            dy = np.abs(arr_f[1:, :] - arr_f[:-1, :])
            gx = np.pad(dx, ((0, 0), (0, 1)), mode="edge")
            gy = np.pad(dy, ((0, 1), (0, 0)), mode="edge")
            mag = np.clip(gx + gy, 0, 255).astype(np.uint8)
            q = self._quantize(mag)
            out.extend(self._bins_to_tokens(q.ravel()))
        return out

    def _quantize(self, arr: np.ndarray) -> np.ndarray:
        levels = max(2, self.config.quant_levels)
        return (arr.astype(np.uint16) * levels // 256).astype(np.uint8)

    def _bins_to_tokens(self, bins: np.ndarray) -> list[str]:
        alphabet = self.config.symbol_alphabet
        if alphabet and len(alphabet) >= max(2, self.config.quant_levels):
            return [alphabet[int(v)] for v in bins]
        return [f"q{int(v)}" for v in bins]

    def _to_target_length(self, tokens: list[str]) -> list[str]:
        target = self.config.target_tokens
        if target <= 0:
            return tokens
        if not tokens:
            return []
        if len(tokens) >= target:
            return tokens[:target]
        repeat = (target // len(tokens)) + 1
        return (tokens * repeat)[:target]

    def _config_dict(self) -> dict[str, Any]:
        return {
            "image_glob": self.config.image_glob,
            "max_images": self.config.max_images,
            "resize_width": self.config.resize_width,
            "quant_levels": self.config.quant_levels,
            "target_tokens": self.config.target_tokens,
            "random_state": self.config.random_state,
            "symbol_alphabet_size": len(self.config.symbol_alphabet or ()),
        }
