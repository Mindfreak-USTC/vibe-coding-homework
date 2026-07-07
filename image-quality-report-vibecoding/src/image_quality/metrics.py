from __future__ import annotations

from typing import Any

import numpy as np
from PIL import Image


def _gray_array(image: Image.Image) -> np.ndarray:
    rgb = image.convert("RGB")
    arr = np.asarray(rgb, dtype=np.float32)
    return 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]


def _laplacian_variance(gray: np.ndarray) -> float:
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return 0.0
    center = gray[1:-1, 1:-1]
    laplace = (
        gray[:-2, 1:-1]
        + gray[2:, 1:-1]
        + gray[1:-1, :-2]
        + gray[1:-1, 2:]
        - 4.0 * center
    )
    return float(np.var(laplace))


def _noise_estimate(gray: np.ndarray) -> float:
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return 0.0
    local_mean = (
        gray[:-2, :-2]
        + gray[:-2, 1:-1]
        + gray[:-2, 2:]
        + gray[1:-1, :-2]
        + gray[1:-1, 1:-1]
        + gray[1:-1, 2:]
        + gray[2:, :-2]
        + gray[2:, 1:-1]
        + gray[2:, 2:]
    ) / 9.0
    residual = gray[1:-1, 1:-1] - local_mean
    return float(np.std(residual))


def compute_quality_metrics(image: Image.Image) -> dict[str, Any]:
    """Compute deterministic quality metrics for one image.

    Metrics are intentionally simple and CPU friendly so the homework can run
    on ordinary laptops without OpenCV or GPU dependencies.
    """

    gray = _gray_array(image)
    width, height = image.size
    return {
        "width": int(width),
        "height": int(height),
        "megapixels": round((width * height) / 1_000_000, 4),
        "brightness": round(float(np.mean(gray)), 4),
        "contrast": round(float(np.std(gray)), 4),
        "sharpness": round(_laplacian_variance(gray), 4),
        "noise": round(_noise_estimate(gray), 4),
    }

