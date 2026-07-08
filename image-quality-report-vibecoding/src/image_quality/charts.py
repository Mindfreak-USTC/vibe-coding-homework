from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


LABELS = {
    "good": "正常",
    "too_dark": "过暗",
    "overexposed": "过曝",
    "blurry": "模糊",
    "low_contrast": "对比度偏低",
    "high_noise": "噪声偏高",
    "low_resolution": "分辨率偏低",
    "skipped": "跳过",
    "error": "错误",
}


def _font(size: int = 30) -> ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def _canvas(title: str, width: int = 1400, height: int = 860) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((48, 36), title, fill="black", font=_font(44))
    return image, draw


def save_bar_chart(counts: dict[str, int], output_path: Path, title: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image, draw = _canvas(title)
    width, height = image.size
    left, top, right, bottom = 110, 140, width - 70, height - 110
    label_font = _font(30)
    value_font = _font(30)
    draw.rectangle((left, top, right, bottom), outline="#333333", width=3)

    if not counts:
        draw.text((left + 28, top + 40), "无数据", fill="black", font=label_font)
        image.save(output_path)
        return

    items = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    max_count = max(value for _, value in items) or 1
    bar_gap = 22
    bar_height = max(38, int((bottom - top - bar_gap * (len(items) + 1)) / max(len(items), 1)))

    for index, (label, value) in enumerate(items):
        y = top + bar_gap + index * (bar_height + bar_gap)
        bar_width = int((right - left - 360) * value / max_count)
        draw.text((left + 12, y + 2), LABELS.get(label, label)[:16], fill="black", font=label_font)
        draw.rectangle((left + 300, y, left + 300 + bar_width, y + bar_height), fill="#4c78a8")
        draw.text((left + 318 + bar_width, y + 4), str(value), fill="black", font=value_font)

    image.save(output_path)


def save_histogram(values: Iterable[float], output_path: Path, title: str, bins: int = 10) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    values = [float(v) for v in values]
    image, draw = _canvas(title)
    width, height = image.size
    left, top, right, bottom = 110, 140, width - 70, height - 130
    label_font = _font(26)
    draw.rectangle((left, top, right, bottom), outline="#333333", width=3)

    if not values:
        draw.text((left + 28, top + 40), "无数据", fill="black", font=label_font)
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
    bar_gap = 10
    bar_width = int((right - left - bar_gap * (bins + 1)) / bins)
    for index, count in enumerate(bucket_counts):
        x1 = left + bar_gap + index * (bar_width + bar_gap)
        x2 = x1 + bar_width
        bar_top = bottom - int((bottom - top - 30) * count / max_count)
        draw.rectangle((x1, bar_top, x2, bottom), fill="#59a14f")
        label = f"{min_value + step * index:.0f}"
        draw.text((x1, bottom + 16), label, fill="black", font=label_font)

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
