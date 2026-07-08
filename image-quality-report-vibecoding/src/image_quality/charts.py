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
    "high_noise": "噪点偏高",
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
    left, top, right, bottom = 110, 165, width - 70, height - 120
    label_font = _font(30)
    value_font = _font(30)
    total_count = sum(counts.values())
    note = "横轴：数量；纵轴：问题类型。"
    if total_count == 1:
        note += " 当前批次只有 1 项统计，所以显示 1 条标记线。"
    draw.text((left, 108), note, fill="#475467", font=label_font)
    draw.rectangle((left, top, right, bottom), outline="#333333", width=3)
    draw.text((right - 100, bottom + 30), "横轴：数量", fill="#475467", font=label_font)

    if not counts:
        draw.text((left + 28, top + 40), "无数据", fill="black", font=label_font)
        image.save(output_path)
        return

    items = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    max_count = max(value for _, value in items) or 1
    track_left = left + 300
    track_right = right - 120

    def x_for_count(value: int) -> int:
        return track_left + int((track_right - track_left) * value / max_count)

    draw.line((track_left, bottom, track_right, bottom), fill="#94a3b8", width=2)
    if max_count <= 6:
        tick_values = list(range(max_count + 1))
    else:
        tick_values = sorted({0, round(max_count * 0.25), round(max_count * 0.5), round(max_count * 0.75), max_count})
    for tick in tick_values:
        tick_x = x_for_count(tick)
        draw.line((tick_x, bottom - 8, tick_x, bottom + 8), fill="#94a3b8", width=2)
        draw.text((tick_x - 10, bottom + 18), str(tick), fill="#475467", font=label_font)

    for index, (label, value) in enumerate(items):
        if len(items) == 1:
            y_center = (top + bottom) // 2
        else:
            y_center = int(top + (bottom - top) * (index + 1) / (len(items) + 1))
        value_x = x_for_count(value)
        draw.text((left + 12, y_center - 18), LABELS.get(label, label)[:16], fill="black", font=label_font)
        draw.line((track_left, y_center, track_right, y_center), fill="#e5e7eb", width=3)
        draw.line((track_left, y_center, value_x, y_center), fill="#4c78a8", width=10)
        draw.ellipse((value_x - 13, y_center - 13, value_x + 13, y_center + 13), fill="#4c78a8")
        value_text = f"{value} 次"
        text_box = draw.textbbox((0, 0), value_text, font=value_font)
        text_width = text_box[2] - text_box[0]
        text_x = min(value_x + 20, right - text_width - 22)
        draw.text((text_x, y_center - 18), value_text, fill="black", font=value_font)

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


def _short_label(value: object, max_chars: int = 18) -> str:
    text = str(value)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "…"


def save_metric_chart(
    rows: Iterable[dict[str, object]],
    output_path: Path,
    *,
    metric: str,
    metric_label: str,
    title: str,
    unit: str,
    normal_min: float | None = None,
    normal_max: float | None = None,
    good_above: float | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    points: list[tuple[str, float, str, str]] = []
    for row in rows:
        if row.get("status") != "ok":
            continue
        try:
            value = float(row.get(metric, ""))
        except (TypeError, ValueError):
            continue
        if normal_min is not None and value < normal_min:
            verdict = "偏低"
            color = "#b45309"
        elif normal_max is not None and value > normal_max:
            verdict = "偏高"
            color = "#b45309"
        elif good_above is not None and value < good_above:
            verdict = "偏低"
            color = "#b45309"
        else:
            verdict = "正常"
            color = "#0f766e"
        points.append((_short_label(row.get("filename", "")), value, verdict, color))

    image, draw = _canvas(title)
    width, height = image.size
    title_font = _font(32)
    label_font = _font(28)
    value_font = _font(30)
    left, top, right, bottom = 120, 190, width - 80, height - 120
    draw.rectangle((left, top, right, bottom), outline="#333333", width=3)

    if normal_min is not None and normal_max is not None:
        note = f"横轴：{metric_label}指标值；纵轴：图片文件名。参考范围：{normal_min:.0f}-{normal_max:.0f}{unit}。单张图片不做分布统计。"
    elif good_above is not None:
        note = f"横轴：{metric_label}相对值；纵轴：图片文件名。参考阈值：≥{good_above:.0f}{unit} 通常更清晰。单张图片不做分布统计。"
    else:
        note = f"横轴：{metric_label}指标值；纵轴：图片文件名。展示每张图片的指标值和结论。"
    draw.text((left, 110), note, fill="#475467", font=label_font)

    if not points:
        draw.text((left + 32, top + 40), "无有效图片数据", fill="black", font=title_font)
        image.save(output_path)
        return

    raw_max_value = max(value for _, value, _, _ in points)
    max_value = raw_max_value
    if normal_max is not None:
        max_value = max(max_value, normal_max * 1.05)
    if good_above is not None:
        max_value = max(good_above * 4, min(max_value, good_above * 20))
    max_value = max(max_value, 1.0)
    label_width = 310
    bar_left = left + label_width
    bar_right = right - 150

    def x_for(value: float) -> int:
        capped = min(value, max_value)
        return bar_left + int((bar_right - bar_left) * capped / max_value)

    if normal_min is not None and normal_max is not None:
        band_left = x_for(normal_min)
        band_right = x_for(normal_max)
        draw.line((band_left, top + 14, band_left, bottom - 14), fill="#16a34a", width=4)
        draw.line((band_right, top + 14, band_right, bottom - 14), fill="#16a34a", width=4)
        draw.text((band_left, bottom + 24), f"{normal_min:.0f}", fill="#166534", font=label_font)
        draw.text((band_right - 28, bottom + 24), f"{normal_max:.0f}", fill="#166534", font=label_font)
    elif good_above is not None:
        threshold_x = x_for(good_above)
        draw.line((threshold_x, top + 14, threshold_x, bottom - 14), fill="#166534", width=4)
        draw.text((threshold_x + 8, top + 18), f"阈值 {good_above:.0f}", fill="#166534", font=label_font)
    draw.line((bar_left, bottom, bar_right, bottom), fill="#94a3b8", width=2)
    draw.text((bar_left - 8, bottom + 24), "0", fill="#475467", font=label_font)
    if normal_max is None or bar_right - x_for(normal_max) > 120:
        draw.text((bar_right - 70, bottom + 24), f"{max_value:.0f}", fill="#475467", font=label_font)

    for index, (label, value, verdict, color) in enumerate(points):
        if len(points) == 1:
            y_center = (top + bottom) // 2
        else:
            y_center = int(top + (bottom - top) * (index + 1) / (len(points) + 1))
        draw.text((left + 18, y_center - 18), label, fill="black", font=label_font)
        x2 = x_for(value)
        draw.line((bar_left, y_center, bar_right, y_center), fill="#e5e7eb", width=3)
        draw.line((bar_left, y_center, x2, y_center), fill=color, width=10)
        draw.ellipse((x2 - 13, y_center - 13, x2 + 13, y_center + 13), fill=color)
        value_text = f"{value:.1f}{unit} · {verdict}"
        text_box = draw.textbbox((0, 0), value_text, font=value_font)
        text_width = text_box[2] - text_box[0]
        text_x = x2 + 18
        if text_x + text_width > right - 24:
            text_x = max(bar_left + 12, x2 - text_width - 18)
        text_y = y_center - 18
        text_height = text_box[3] - text_box[1]
        draw.rectangle((text_x - 6, text_y - 3, text_x + text_width + 6, text_y + text_height + 3), fill="white")
        draw.text((text_x, text_y), value_text, fill="black", font=value_font)

    if raw_max_value > max_value:
        draw.text((bar_right - 220, top - 42), "超出比例尺的高值按满格显示", fill="#667085", font=label_font)

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
