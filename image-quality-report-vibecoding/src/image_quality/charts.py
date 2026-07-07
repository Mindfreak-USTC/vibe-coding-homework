from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


def _font() -> ImageFont.ImageFont:
    return ImageFont.load_default()


def _canvas(title: str, width: int = 900, height: int = 540) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((30, 24), title, fill="black", font=_font())
    return image, draw


def save_bar_chart(counts: dict[str, int], output_path: Path, title: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image, draw = _canvas(title)
    width, height = image.size
    left, top, right, bottom = 80, 90, width - 40, height - 80
    draw.rectangle((left, top, right, bottom), outline="#333333")

    if not counts:
        draw.text((left + 20, top + 30), "No data", fill="black", font=_font())
        image.save(output_path)
        return

    items = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    max_count = max(value for _, value in items) or 1
    bar_gap = 12
    bar_height = max(18, int((bottom - top - bar_gap * (len(items) + 1)) / max(len(items), 1)))

    for index, (label, value) in enumerate(items):
        y = top + bar_gap + index * (bar_height + bar_gap)
        bar_width = int((right - left - 220) * value / max_count)
        draw.text((left + 8, y + 2), label[:26], fill="black", font=_font())
        draw.rectangle((left + 190, y, left + 190 + bar_width, y + bar_height), fill="#4c78a8")
        draw.text((left + 200 + bar_width, y + 2), str(value), fill="black", font=_font())

    image.save(output_path)


def save_histogram(values: Iterable[float], output_path: Path, title: str, bins: int = 10) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    values = [float(v) for v in values]
    image, draw = _canvas(title)
    width, height = image.size
    left, top, right, bottom = 80, 90, width - 40, height - 80
    draw.rectangle((left, top, right, bottom), outline="#333333")

    if not values:
        draw.text((left + 20, top + 30), "No data", fill="black", font=_font())
        image.save(output_path)
        return

    min_value, max_value = min(values), max(values)
    if min_value == max_value:
        max_value = min_value + 1.0
    step = (max_value - min_value) / bins
    bucket_counts = [0 for _ in range(bins)]
    for value in values:
        bucket = min(int((value - min_value) / step), bins - 1)
        bucket_counts[bucket] += 1

    max_count = max(bucket_counts) or 1
    bar_gap = 6
    bar_width = int((right - left - bar_gap * (bins + 1)) / bins)
    for index, count in enumerate(bucket_counts):
        x1 = left + bar_gap + index * (bar_width + bar_gap)
        x2 = x1 + bar_width
        bar_top = bottom - int((bottom - top - 20) * count / max_count)
        draw.rectangle((x1, bar_top, x2, bottom), fill="#59a14f")
        label = f"{min_value + step * index:.0f}"
        draw.text((x1, bottom + 10), label, fill="black", font=_font())

    image.save(output_path)


def issue_counts_from_rows(rows: list[dict[str, object]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        if row.get("status") != "ok":
            counter[str(row.get("status", "error"))] += 1
            continue
        issues = row.get("issues", [])
        if isinstance(issues, str):
            issues = [issue for issue in issues.split(";") if issue]
        if not issues:
            counter["good"] += 1
        else:
            counter.update(str(issue) for issue in issues)
    return dict(counter)

