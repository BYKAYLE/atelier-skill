"""Visual diff via Pillow.

First run of a given combination creates a baseline. Subsequent runs compare
pixel-wise and emit a ratio and optional diff image.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageChops
except ImportError:  # Pillow not installed
    Image = None
    ImageChops = None


def compare(
    screenshot: Path,
    baseline_path: Path,
    diff_out: Path | None = None,
    ignore_regions: list[tuple[int, int, int, int]] | None = None,
) -> dict[str, Any]:
    """Compare screenshot to baseline.

    Returns a dict with:
        baseline: "created" | "compared" | "missing"
        ratio: float in [0, 1], fraction of pixels differing beyond threshold
        baseline_path: str
        diff_path: str | None
    """
    if Image is None:
        return {"baseline": "missing", "error": "Pillow not installed", "ratio": None}

    if not screenshot.exists():
        return {"baseline": "missing", "error": "screenshot missing", "ratio": None}

    if not baseline_path.exists():
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        Image.open(screenshot).save(baseline_path)
        return {
            "baseline": "created",
            "ratio": 0.0,
            "baseline_path": str(baseline_path),
            "diff_path": None,
        }

    a = Image.open(baseline_path).convert("RGB")
    b = Image.open(screenshot).convert("RGB")
    if a.size != b.size:
        # resize b to a for comparability; record this
        b = b.resize(a.size)

    if ignore_regions:
        a = _mask(a, ignore_regions)
        b = _mask(b, ignore_regions)

    diff = ImageChops.difference(a, b)
    # A pixel counts as "changed" if max channel delta > 15 (suppresses antialiasing jitter).
    bbox_px = 0
    total_px = a.width * a.height
    for px in diff.getdata():
        if max(px) > 15:
            bbox_px += 1
    ratio = bbox_px / total_px if total_px else 0.0

    diff_path_str: str | None = None
    if diff_out is not None and ratio > 0:
        diff_out.parent.mkdir(parents=True, exist_ok=True)
        # Amplify the diff for human viewing.
        amplified = diff.point(lambda v: min(255, v * 4))
        amplified.save(diff_out)
        diff_path_str = str(diff_out)

    return {
        "baseline": "compared",
        "ratio": ratio,
        "baseline_path": str(baseline_path),
        "diff_path": diff_path_str,
    }


def _mask(img, regions):
    from PIL import ImageDraw  # lazy: Pillow already imported above
    copy = img.copy()
    draw = ImageDraw.Draw(copy)
    for (x, y, w, h) in regions:
        draw.rectangle([x, y, x + w, y + h], fill=(128, 128, 128))
    return copy
