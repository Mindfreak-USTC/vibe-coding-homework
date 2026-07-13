from __future__ import annotations

import argparse
from dataclasses import dataclass
from email.parser import BytesParser
from email.policy import default
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath, PureWindowsPath
import time
from typing import Iterable
from urllib.parse import quote, unquote, urlparse

from .analyzer import (
    DEFAULT_MIN_HEIGHT,
    DEFAULT_MIN_WIDTH,
    DEFAULT_NOISE_THRESHOLD,
    AnalysisSummary,
    analyze_folder,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_ROOT = PROJECT_ROOT / "web_runs"
PREVIEW_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}
DOWNLOADABLE_FILES = {
    "quality_results.csv",
    "report.md",
    "report.pdf",
    "issue_counts.png",
    "brightness_distribution.png",
    "sharpness_distribution.png",
}
ATTACHMENT_DOWNLOADS = {"quality_results.csv", "report.md", "report.pdf"}
STATUS_LABELS = {
    "ok": "正常",
    "skipped": "跳过",
    "error": "错误",
}
ISSUE_LABELS = {
    "too_dark": "过暗",
    "overexposed": "过曝",
    "blurry": "模糊",
    "low_contrast": "对比度偏低",
    "high_noise": "噪点偏高",
    "low_resolution": "分辨率偏低",
}
CHART_LABELS = {
    "issue_counts.png": "问题数量统计图",
    "brightness_distribution.png": "亮度指标图",
    "sharpness_distribution.png": "清晰度指标图",
}
CHART_EXPLAINERS = {
    "issue_counts.png": "横轴为数量，纵轴为问题类型。只有一张图片时，一条标记线表示该状态或问题在本批次出现 1 次。",
    "brightness_distribution.png": "横轴为亮度值，纵轴为图片文件名。两条绿色参考线表示正常亮度范围 45-215。",
    "sharpness_distribution.png": "横轴为清晰度相对值，纵轴为图片文件名。绿色参考线表示清晰度阈值 80。",
}


@dataclass
class UploadedFile:
    filename: str
    content: bytes


def safe_upload_name(filename: str, *, fallback: str = "upload.png") -> str:
    raw = (filename or "").strip()
    raw = PureWindowsPath(PurePosixPath(raw).name).name
    if raw in {"", ".", ".."}:
        raw = fallback
    safe_chars: list[str] = []
    for char in raw:
        if char in '<>:"/\\|?*' or ord(char) < 32:
            safe_chars.append("_")
        else:
            safe_chars.append(char)
    cleaned = "".join(safe_chars).strip(" .")
    return cleaned or fallback


def _issue_text(issues: object) -> str:
    if isinstance(issues, str):
        issue_items = [issue for issue in issues.split(";") if issue]
    elif isinstance(issues, list):
        issue_items = [str(issue) for issue in issues if str(issue)]
    else:
        issue_items = []
    if not issue_items:
        return "无明显问题"
    return "；".join(ISSUE_LABELS.get(issue, issue) for issue in issue_items)


def _format_cell(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.1f}"
    return escape(str(value))


def _status_label(status: object) -> str:
    return STATUS_LABELS.get(str(status), str(status or "未知"))


def _result_badge(status: str, issue_text: str) -> tuple[str, str]:
    if status == "ok" and issue_text != "无明显问题":
        return issue_text, "status-warning"
    return _status_label(status), f"status-{status}"


def _to_float(value: object) -> float | None:
    try:
        if value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: object) -> int | None:
    try:
        if value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _metric_conclusion(metric: str, row: dict[str, object]) -> str:
    value = _to_float(row.get(metric))
    if value is None:
        return "未检测"
    formatted = f"{value:.1f}"
    if metric == "brightness":
        if value < 45:
            label = "偏暗"
        elif value > 215:
            label = "过曝"
        else:
            label = "亮度正常"
    elif metric == "contrast":
        label = "对比度偏低" if value < 25 else "对比度正常"
    elif metric == "sharpness":
        label = "偏模糊" if value < 80 else "清晰"
    elif metric == "noise":
        label = "噪点偏高" if value >= DEFAULT_NOISE_THRESHOLD else "噪点正常"
    else:
        label = "正常"
    return f"{label} · {formatted}"


def _metric_parts(metric: str, row: dict[str, object]) -> tuple[str, str, str]:
    value = _to_float(row.get(metric))
    if value is None:
        return "未检测", "未检测", "warn"
    if metric == "brightness":
        value_text = f"{value:.1f}"
        if value < 45:
            return value_text, "偏暗", "warn"
        if value > 215:
            return value_text, "过曝", "warn"
        return value_text, "亮度正常", "ok"
    if metric == "contrast":
        return f"{value:.1f}", ("对比度偏低" if value < 25 else "对比度正常"), ("warn" if value < 25 else "ok")
    if metric == "sharpness":
        return f"{value:.1f}", ("偏模糊" if value < 80 else "清晰"), ("warn" if value < 80 else "ok")
    if metric == "noise":
        return (
            f"{value:.1f}",
            ("噪点偏高" if value >= DEFAULT_NOISE_THRESHOLD else "噪点正常"),
            ("warn" if value >= DEFAULT_NOISE_THRESHOLD else "ok"),
        )
    return f"{value:.1f}", "正常", "ok"


def _resolution_conclusion(row: dict[str, object]) -> str:
    width = _to_int(row.get("width"))
    height = _to_int(row.get("height"))
    if width is None or height is None:
        return "未检测"
    label = "分辨率偏低" if width < DEFAULT_MIN_WIDTH or height < DEFAULT_MIN_HEIGHT else "高分辨率"
    return f"{label} · {width}x{height}"


def _resolution_parts(row: dict[str, object]) -> tuple[str, str, str]:
    width = _to_int(row.get("width"))
    height = _to_int(row.get("height"))
    if width is None or height is None:
        return "未检测", "未检测", "warn"
    value_text = f"{width}x{height}"
    if width < DEFAULT_MIN_WIDTH or height < DEFAULT_MIN_HEIGHT:
        return value_text, "分辨率偏低", "warn"
    return value_text, "高分辨率", "ok"


def _metric_card(label: str, value: str, verdict: str, tone: str) -> str:
    tone_class = "" if tone == "ok" else f" {tone}"
    return (
        f'<article class="metric-card{tone_class}">'
        f"<span>{escape(label)}</span>"
        f"<strong>{escape(value)}</strong>"
        f"<em>{escape(verdict)}</em>"
        "</article>"
    )


def _chart_label(filename: str) -> str:
    return CHART_LABELS.get(filename, filename)


def _chart_explainer(filename: str) -> str:
    return CHART_EXPLAINERS.get(filename, "展示本批次图像质量统计结果。")


def _url_part(value: object) -> str:
    return quote(str(value), safe="")


def _content_disposition(filename: str, *, disposition: str = "inline") -> str:
    safe_disposition = "attachment" if disposition == "attachment" else "inline"
    fallback = "".join(char if char.isascii() and char not in '"\\\r\n' else "_" for char in filename)
    fallback = fallback.strip(" .") or "file"
    encoded = quote(filename, safe="")
    return f'{safe_disposition}; filename="{fallback}"; filename*=UTF-8\'\'{encoded}'


def _pdf_font(size: int, *, bold: bool = False):
    from PIL import ImageFont

    candidates = [
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/msyhbd.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/simsun.ttc"),
        Path("C:/Windows/Fonts/simsunb.ttf"),
        Path("C:/Windows/Fonts/simkai.ttf"),
        Path("/System/Library/Fonts/PingFang.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    if not bold:
        candidates = [Path("C:/Windows/Fonts/simsun.ttc"), Path("C:/Windows/Fonts/msyh.ttc"), *candidates]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _text_size(draw: object, text: str, font: object) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap_text(draw: object, text: str, font: object, max_width: int, *, max_lines: int | None = None) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        if char == "\n":
            lines.append(current)
            current = ""
            continue
        candidate = current + char
        if not current or _text_size(draw, candidate, font)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = char
        if max_lines and len(lines) >= max_lines:
            break
    if current and (not max_lines or len(lines) < max_lines):
        lines.append(current)
    if max_lines and len(lines) > max_lines:
        return lines[:max_lines]
    return lines


def _draw_wrapped_text(
    draw: object,
    text: str,
    xy: tuple[int, int],
    font: object,
    fill: tuple[int, int, int],
    max_width: int,
    *,
    line_gap: int = 8,
    max_lines: int | None = None,
) -> int:
    x, y = xy
    line_height = _text_size(draw, "国", font)[1] + line_gap
    for line in _wrap_text(draw, text, font, max_width, max_lines=max_lines):
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def _paste_fitted_image(page: object, path: Path, box: tuple[int, int, int, int]) -> None:
    from PIL import Image, ImageOps

    left, top, right, bottom = box
    max_width = max(1, right - left)
    max_height = max(1, bottom - top)
    with Image.open(path) as image:
        fitted = ImageOps.exif_transpose(image).convert("RGB")
        fitted.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        x = left + (max_width - fitted.width) // 2
        y = top + (max_height - fitted.height) // 2
        page.paste(fitted, (x, y))


def write_downloadable_pdf_report(summary: AnalysisSummary, upload_dir: Path, output_dir: Path) -> Path:
    from PIL import Image, ImageDraw

    page_width, page_height = 1240, 1754
    margin = 70
    line = (31, 41, 55)
    paper = (247, 243, 234)
    panel = (255, 253, 247)
    white = (255, 255, 255)
    muted = (102, 112, 133)
    accent = (15, 118, 110)
    good = (22, 101, 52)
    warn = (180, 83, 9)
    bad = (185, 28, 28)

    title_font = _pdf_font(54, bold=True)
    h2_font = _pdf_font(34, bold=True)
    h3_font = _pdf_font(25, bold=True)
    body_font = _pdf_font(20)
    small_font = _pdf_font(17)
    number_font = _pdf_font(34, bold=True)

    pages: list[Image.Image] = []

    def new_page() -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
        page = Image.new("RGB", (page_width, page_height), paper)
        draw = ImageDraw.Draw(page)
        for x in range(0, page_width, 34):
            draw.line((x, 0, x, page_height), fill=(230, 226, 216), width=1)
        for y_grid in range(0, page_height, 34):
            draw.line((0, y_grid, page_width, y_grid), fill=(230, 226, 216), width=1)
        pages.append(page)
        return page, draw, margin

    page, draw, y = new_page()

    def ensure_space(required_height: int) -> None:
        nonlocal page, draw, y
        if y + required_height > page_height - margin:
            page, draw, y = new_page()

    def card(x: int, top: int, width: int, height: int, *, fill: tuple[int, int, int] = white) -> None:
        draw.rectangle((x + 8, top + 8, x + width + 8, top + height + 8), fill=(205, 201, 191))
        draw.rectangle((x, top, x + width, top + height), fill=fill, outline=line, width=3)

    content_width = page_width - margin * 2
    draw.text((margin, y), "图像质量检测报告", font=title_font, fill=(20, 20, 20))
    y += 76
    y = _draw_wrapped_text(
        draw,
        "本报告由网页上传检测生成，包含原图预览、质量指标、问题结论、CSV 对应统计和图表。",
        (margin, y),
        body_font,
        muted,
        content_width,
    )
    y += 18

    stat_items = [
        ("总文件数", str(summary.total_files)),
        ("有效图像", str(summary.valid_images)),
        ("跳过文件", str(summary.skipped_files)),
        ("损坏/错误", str(summary.error_files)),
    ]
    stat_gap = 16
    stat_width = (content_width - stat_gap * 3) // 4
    stat_height = 118
    for index, (label, value) in enumerate(stat_items):
        x = margin + index * (stat_width + stat_gap)
        card(x, y, stat_width, stat_height)
        draw.text((x + 22, y + 18), value, font=number_font, fill=(0, 0, 0))
        draw.text((x + 22, y + 70), label, font=body_font, fill=muted)
    y += stat_height + 34

    valid_rows = [row for row in summary.rows if row.get("status") == "ok"]
    if valid_rows:
        first = valid_rows[0]
        filename = str(first.get("filename", ""))
        image_path = upload_dir / filename
        if image_path.exists():
            preview_height = 520
            ensure_space(preview_height)
            card(margin, y, content_width, preview_height, fill=white)
            draw.text((margin + 24, y + 22), "原图预览", font=h2_font, fill=(0, 0, 0))
            image_box = (margin + 34, y + 84, margin + content_width - 34, y + 410)
            draw.rectangle(image_box, fill=(248, 250, 252), outline=(203, 213, 225), width=2)
            _paste_fitted_image(page, image_path, image_box)
            name_width = _text_size(draw, filename, h3_font)[0]
            draw.text((margin + (content_width - name_width) // 2, y + 430), filename, font=h3_font, fill=(0, 0, 0))
            y += preview_height + 36

    ensure_space(250)
    draw.text((margin, y), "质量指标", font=h2_font, fill=(0, 0, 0))
    y += 52
    for row in summary.rows:
        filename = str(row.get("filename", ""))
        status = str(row.get("status", ""))
        issue_text = _issue_text(row.get("issues", []))
        badge_text, _badge_class = _result_badge(status, issue_text)
        metrics = []
        for label, metric in (("亮度", "brightness"), ("对比度", "contrast"), ("清晰度", "sharpness"), ("噪点", "noise")):
            value, verdict, tone = _metric_parts(metric, row)
            metrics.append((label, value, verdict, tone))
        value, verdict, tone = _resolution_parts(row)
        metrics.append(("分辨率", value, verdict, tone))

        row_height = 238
        ensure_space(row_height + 24)
        card(margin, y, content_width, row_height, fill=panel)
        draw.text((margin + 22, y + 22), filename, font=h3_font, fill=(0, 0, 0))
        badge_color = warn if badge_text != "正常" else good
        badge_width = min(410, max(120, _text_size(draw, badge_text, body_font)[0] + 44))
        badge_x = margin + content_width - badge_width - 22
        draw.rectangle((badge_x, y + 20, badge_x + badge_width, y + 62), fill=(220, 252, 231), outline=line, width=2)
        draw.text((badge_x + 18, y + 29), badge_text, font=body_font, fill=badge_color)

        metric_gap = 14
        metric_width = (content_width - 44 - metric_gap * 4) // 5
        metric_y = y + 88
        for index, (label, value_text, verdict_text, tone_name) in enumerate(metrics):
            x = margin + 22 + index * (metric_width + metric_gap)
            draw.rectangle((x, metric_y, x + metric_width, metric_y + 112), fill=white, outline=line, width=2)
            draw.text((x + 14, metric_y + 14), label, font=small_font, fill=muted)
            draw.text((x + 14, metric_y + 40), value_text, font=h3_font, fill=(0, 0, 0))
            verdict_color = warn if tone_name == "warn" else bad if tone_name == "bad" else good
            draw.text((x + 14, metric_y + 78), verdict_text, font=small_font, fill=verdict_color)
        y += row_height + 26

    note = "数据说明：亮度和对比度来自 0-255 灰度统计；清晰度和噪点是算法相对强度，无物理单位；分辨率单位为像素。"
    ensure_space(78)
    y = _draw_wrapped_text(draw, note, (margin, y), small_font, muted, content_width)
    y += 28

    if summary.chart_paths:
        ensure_space(90)
        draw.text((margin, y), "统计图", font=h2_font, fill=(0, 0, 0))
        y += 54
        for chart_path in summary.chart_paths:
            chart_height = 470
            ensure_space(chart_height + 34)
            card(margin, y, content_width, chart_height, fill=white)
            draw.text((margin + 22, y + 18), _chart_label(chart_path.name), font=h3_font, fill=(0, 0, 0))
            image_box = (margin + 28, y + 64, margin + content_width - 28, y + 350)
            draw.rectangle(image_box, fill=white, outline=(203, 213, 225), width=2)
            if Path(chart_path).exists():
                _paste_fitted_image(page, Path(chart_path), image_box)
            _draw_wrapped_text(
                draw,
                _chart_explainer(chart_path.name),
                (margin + 24, y + 366),
                body_font,
                muted,
                content_width - 48,
                max_lines=3,
            )
            y += chart_height + 30

    report_path = output_dir / "report.pdf"
    if not pages:
        page, draw, y = new_page()
    pages[0].save(report_path, "PDF", resolution=150.0, save_all=True, append_images=pages[1:])
    return report_path


def _base_page(title: str, body: str, *, page_class: str = "") -> str:
    body_class = f' class="{escape(page_class)}"' if page_class else ""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{
      --ink: #141414;
      --muted: #667085;
      --paper: #f7f3ea;
      --panel: #fffdf7;
      --line: #1f2937;
      --accent: #0f766e;
      --accent-strong: #115e59;
      --warn: #b45309;
      --bad: #b91c1c;
      --good: #166534;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: Cambria, "Noto Serif SC", "Microsoft YaHei", serif;
      background:
        linear-gradient(90deg, rgba(15, 118, 110, .08) 1px, transparent 1px),
        linear-gradient(rgba(31, 41, 55, .06) 1px, transparent 1px),
        var(--paper);
      background-size: 34px 34px;
    }}
    main {{
      width: min(1480px, calc(100vw - 32px));
      margin: 28px auto 48px;
    }}
    .upload-page main {{
      min-height: 100vh;
      margin: 0 auto;
      padding: 48px 0 56px;
      display: grid;
      align-items: start;
    }}
    .hero {{
      border: 2px solid var(--line);
      background: var(--panel);
      padding: 34px;
      box-shadow: 10px 10px 0 var(--line);
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(360px, .72fr);
      gap: 28px;
      align-items: stretch;
    }}
    .upload-hero {{
      width: min(1120px, 100%);
      margin: 0 auto;
      grid-template-columns: 1fr;
      gap: 26px;
      text-align: center;
      padding: 44px;
    }}
    .upload-hero h1 {{
      margin-bottom: 18px;
      font-size: clamp(40px, 5vw, 74px);
      white-space: nowrap;
    }}
    .upload-hero p {{
      max-width: 860px;
      margin-left: auto;
      margin-right: auto;
      font-size: 20px;
    }}
    .upload-hero .panel {{
      width: min(760px, 100%);
      margin: 0 auto;
      padding: 34px;
      text-align: left;
    }}
    .upload-hero .panel h2 {{
      text-align: center;
      font-size: 38px;
    }}
    .upload-hero .upload-box {{
      min-height: 240px;
    }}
    .upload-hero input[type="file"] {{
      max-width: 560px;
      font-size: 18px;
    }}
    .upload-hero .toolbar {{
      justify-content: center;
    }}
    .upload-hero button {{
      min-height: 56px;
      padding: 0 34px;
      font-size: 21px;
    }}
    h1 {{
      margin: 0 0 14px;
      font-size: clamp(32px, 5vw, 64px);
      line-height: 1.02;
      letter-spacing: 0;
    }}
    h2 {{
      margin: 0 0 16px;
      font-size: 32px;
    }}
    p {{
      color: var(--muted);
      font-size: 17px;
      line-height: 1.7;
      margin: 0 0 14px;
    }}
    .panel {{
      border: 2px solid var(--line);
      background: white;
      padding: 22px;
      box-shadow: 6px 6px 0 rgba(20, 20, 20, .18);
    }}
    .upload-box {{
      border: 2px dashed var(--accent);
      padding: 22px;
      min-height: 190px;
      display: grid;
      place-items: center;
      text-align: center;
      background: #ecfdf5;
    }}
    input[type="file"] {{
      width: 100%;
      max-width: 360px;
      padding: 14px;
      border: 1px solid #99f6e4;
      background: white;
    }}
    button, .button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 44px;
      padding: 0 18px;
      border: 2px solid var(--line);
      background: var(--accent);
      color: white;
      font-weight: 700;
      text-decoration: none;
      cursor: pointer;
      box-shadow: 4px 4px 0 var(--line);
    }}
    button:hover, .button:hover {{ background: var(--accent-strong); }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 18px;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(4, minmax(120px, 1fr));
      gap: 14px;
      margin: 24px 0;
    }}
    .stat {{
      border: 2px solid var(--line);
      background: white;
      padding: 18px;
    }}
    .stat strong {{
      display: block;
      font-size: 32px;
      line-height: 1;
    }}
    .stat span {{ color: var(--muted); }}
    .hero-stats {{
      grid-template-columns: repeat(2, minmax(160px, 1fr));
      gap: 16px;
      margin: 24px 0 0;
      max-width: 560px;
    }}
    .hero-stats .stat {{
      min-height: 116px;
      padding: 20px 22px;
    }}
    .hero-stats .stat strong {{ font-size: 44px; }}
    .hero-stats .stat span {{ font-size: 19px; }}
    .status-ok {{ color: var(--good); font-weight: 700; }}
    .status-error {{ color: var(--bad); font-weight: 700; }}
    .status-skipped {{ color: var(--warn); font-weight: 700; }}
    .preview-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 18px;
      margin: 24px 0;
    }}
    .preview-panel {{
      border: 2px solid var(--line);
      background: white;
      padding: 20px;
      box-shadow: 6px 6px 0 rgba(20, 20, 20, .18);
    }}
    .preview-panel .preview-grid {{
      grid-template-columns: 1fr;
      margin: 0;
    }}
    .preview-card {{
      margin: 0;
      border: 0;
      background: transparent;
      padding: 0;
      box-shadow: none;
    }}
    .preview-card img {{
      display: block;
      width: 100%;
      height: 260px;
      object-fit: contain;
      background: #f8fafc;
      border: 0;
    }}
    .preview-card figcaption {{
      margin-top: 12px;
      font-size: 22px;
      font-weight: 700;
      line-height: 1.45;
      text-align: center;
      overflow-wrap: anywhere;
    }}
    .file-result {{
      border: 2px solid var(--line);
      background: #fffdf7;
      padding: 22px;
      margin-top: 18px;
    }}
    .file-result:first-of-type {{ margin-top: 0; }}
    .file-meta {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
      margin-bottom: 18px;
    }}
    .file-name {{
      margin: 0;
      font-size: 26px;
      line-height: 1.2;
      font-weight: 800;
    }}
    .status-pill {{
      display: inline-flex;
      align-items: center;
      min-height: 42px;
      padding: 0 16px;
      border: 2px solid var(--line);
      background: #dcfce7;
      color: var(--good);
      font-size: 22px;
      font-weight: 800;
      text-align: center;
      white-space: normal;
      max-width: 64%;
      line-height: 1.35;
    }}
    .status-pill.status-warning {{
      background: #fffbeb;
      color: var(--warn);
    }}
    .status-pill.status-error {{
      background: #fee2e2;
      color: var(--bad);
    }}
    .status-pill.status-skipped {{
      background: #fef3c7;
      color: var(--warn);
    }}
    .metric-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 14px;
    }}
    .metric-card {{
      border: 2px solid var(--line);
      background: white;
      padding: 16px 18px;
      min-height: 142px;
      display: grid;
      grid-template-rows: auto 1fr auto;
      align-items: center;
    }}
    .metric-card span {{
      color: var(--muted);
      font-size: 18px;
      font-weight: 700;
    }}
    .metric-card strong {{
      display: block;
      font-size: 34px;
      line-height: 1.1;
      white-space: nowrap;
    }}
    .metric-card em {{
      color: var(--good);
      font-size: 20px;
      font-style: normal;
      font-weight: 800;
      white-space: nowrap;
    }}
    .metric-card.warn em {{ color: var(--warn); }}
    .metric-card.bad em {{ color: var(--bad); }}
    .metrics-panel {{
      margin-top: 32px;
    }}
    .metric-note {{
      margin: 18px 0 0;
      color: var(--muted);
      font-size: 16px;
      line-height: 1.6;
      text-align: right;
    }}
    .charts {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 18px;
      margin-top: 24px;
    }}
    .chart {{
      margin: 0;
      border: 2px solid var(--line);
      background: white;
      padding: 14px;
      box-shadow: 6px 6px 0 rgba(20, 20, 20, .18);
    }}
    .chart img {{
      display: block;
      width: 100%;
      height: auto;
      max-height: 320px;
      object-fit: contain;
      border: 1px solid #cbd5e1;
      background: white;
    }}
    .chart figcaption {{
      margin-top: 12px;
      font-size: 24px;
      font-weight: 700;
    }}
    .chart-explainer {{
      margin: 10px 0 0;
      color: var(--muted);
      font-size: 20px;
      line-height: 1.6;
    }}
    .hint {{
      padding: 12px 14px;
      background: #fffbeb;
      border-left: 4px solid #f59e0b;
      color: #713f12;
    }}
    @media (max-width: 780px) {{
      .hero {{ grid-template-columns: 1fr; padding: 22px; }}
      .stats {{ grid-template-columns: repeat(2, 1fr); }}
      .metric-grid {{ grid-template-columns: 1fr; }}
      .charts {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body{body_class}>
  <main>
    {body}
  </main>
</body>
</html>"""


def render_upload_page(message: str = "") -> str:
    notice = f'<p class="hint">{escape(message)}</p>' if message else ""
    body = f"""
<section class="hero upload-hero">
  <div>
    <h1>图像质量检测与自动报告系统</h1>
    <p>上传 JPG、PNG 或 BMP 图片后，系统会计算亮度、对比度、清晰度、噪点和分辨率，并自动生成 CSV、PDF 报告和统计图。</p>
    <p>这个页面复用命令行项目的同一套检测逻辑，适合课堂现场演示真实图片输入。</p>
    {notice}
  </div>
  <form class="panel" action="/analyze" method="post" enctype="multipart/form-data">
    <h2>上传图片</h2>
    <div class="upload-box">
      <div>
        <input type="file" name="images" accept=".jpg,.jpeg,.png,.bmp,image/jpeg,image/png,image/bmp" multiple required>
        <p>支持一次选择多张图片。中文文件名会保留，危险路径字符会自动清理。</p>
      </div>
    </div>
    <div class="toolbar">
      <button type="submit">开始检测</button>
    </div>
  </form>
</section>
"""
    return _base_page("图像质量检测与自动报告系统", body, page_class="upload-page")


def render_results_page(summary: AnalysisSummary, session_id: str) -> str:
    metric_sections = []
    preview_cards = []
    for row in summary.rows:
        status = str(row.get("status", ""))
        filename = str(row.get("filename", ""))
        issue_text = _issue_text(row.get("issues", []))
        badge_text, badge_class = _result_badge(status, issue_text)
        if status == "ok":
            preview_cards.append(
                '<figure class="preview-card">'
                f'<img src="/preview/{_url_part(session_id)}/{_url_part(filename)}" alt="原图预览：{escape(filename)}">'
                f"<figcaption>{escape(filename)}</figcaption>"
                "</figure>"
            )
        metric_cards = []
        for label, metric in (
            ("亮度", "brightness"),
            ("对比度", "contrast"),
            ("清晰度", "sharpness"),
            ("噪点", "noise"),
        ):
            value_text, verdict, tone = _metric_parts(metric, row)
            metric_cards.append(_metric_card(label, value_text, verdict, tone))
        resolution_value, resolution_verdict, resolution_tone = _resolution_parts(row)
        metric_cards.append(_metric_card("分辨率", resolution_value, resolution_verdict, resolution_tone))
        metric_sections.append(
            '<article class="file-result">'
            '<div class="file-meta">'
            f'<h3 class="file-name">{escape(filename)}</h3>'
            f'<span class="status-pill {escape(badge_class)}">{escape(badge_text)}</span>'
            "</div>"
            f'<div class="metric-grid">{"".join(metric_cards)}</div>'
            "</article>"
        )
    metric_body = "\n".join(metric_sections)
    previews = "\n".join(preview_cards) or '<p class="hint">本次没有可预览的有效图片。</p>'
    chart_cards = "\n".join(
        f'<figure class="chart"><img src="/download/{_url_part(session_id)}/{_url_part(path.name)}" alt="{escape(_chart_label(path.name))}"><figcaption>{escape(_chart_label(path.name))}</figcaption><p class="chart-explainer">{escape(_chart_explainer(path.name))}</p></figure>'
        for path in summary.chart_paths
    )
    body = f"""
<section>
  <div class="hero">
    <div>
      <h1>检测完成</h1>
      <p>已生成每张图片的质量指标、问题标签、CSV 汇总、PDF 报告和统计图。</p>
      <div class="toolbar">
        <a class="button" href="/">继续上传</a>
        <a class="button" href="/download/{escape(session_id)}/quality_results.csv">下载 CSV</a>
        <a class="button" href="/download/{escape(session_id)}/report.pdf" download>下载报告</a>
      </div>
      <div class="stats hero-stats">
        <div class="stat"><strong>{summary.total_files}</strong><span>总文件数</span></div>
        <div class="stat"><strong>{summary.valid_images}</strong><span>有效图像</span></div>
        <div class="stat"><strong>{summary.skipped_files}</strong><span>跳过文件</span></div>
        <div class="stat"><strong>{summary.error_files}</strong><span>损坏/错误</span></div>
      </div>
    </div>
    <aside class="preview-panel">
      <h2>原图预览</h2>
      <div class="preview-grid">{previews}</div>
    </aside>
  </div>
  <div class="panel metrics-panel">
    <h2>质量指标</h2>
    {metric_body}
    <p class="metric-note">数据说明：亮度和对比度来自 0-255 灰度统计；清晰度和噪点是算法相对强度，无物理单位；分辨率单位为像素。</p>
  </div>
  <div class="charts">{chart_cards}</div>
</section>
"""
    return _base_page("检测结果", body)


def parse_uploaded_files(body: bytes, content_type: str) -> list[UploadedFile]:
    message = BytesParser(policy=default).parsebytes(
        f"Content-Type: {content_type}\nMIME-Version: 1.0\n\n".encode("utf-8") + body
    )
    uploads: list[UploadedFile] = []
    if not message.is_multipart():
        return uploads
    for part in message.iter_parts():
        filename = part.get_filename()
        if not filename:
            continue
        content = part.get_payload(decode=True) or b""
        if not content:
            continue
        uploads.append(UploadedFile(filename=filename, content=content))
    return uploads


def save_uploads(files: Iterable[UploadedFile], upload_dir: Path) -> int:
    upload_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    used: set[str] = set()
    for index, upload in enumerate(files, start=1):
        filename = safe_upload_name(upload.filename, fallback=f"upload_{index}.png")
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        candidate = filename
        duplicate_index = 2
        while candidate.lower() in used or (upload_dir / candidate).exists():
            candidate = f"{stem}_{duplicate_index}{suffix}"
            duplicate_index += 1
        used.add(candidate.lower())
        (upload_dir / candidate).write_bytes(upload.content)
        count += 1
    return count


class ImageQualityWebHandler(BaseHTTPRequestHandler):
    server: "ImageQualityHTTPServer"

    def _send_html(self, html: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content_type = "application/octet-stream"
        if path.suffix.lower() == ".png":
            content_type = "image/png"
        elif path.suffix.lower() in {".jpg", ".jpeg"}:
            content_type = "image/jpeg"
        elif path.suffix.lower() == ".bmp":
            content_type = "image/bmp"
        elif path.suffix.lower() == ".csv":
            content_type = "text/csv; charset=utf-8"
        elif path.suffix.lower() == ".md":
            content_type = "text/markdown; charset=utf-8"
        elif path.suffix.lower() == ".pdf":
            content_type = "application/pdf"
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        disposition = "attachment" if path.name in ATTACHMENT_DOWNLOADS else "inline"
        self.send_header("Content-Disposition", _content_disposition(path.name, disposition=disposition))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self._send_html(render_upload_page())
            return
        parts = PurePosixPath(unquote(parsed.path)).parts
        if len(parts) == 4 and parts[1] == "download":
            session_id = safe_upload_name(parts[2], fallback="")
            filename = safe_upload_name(parts[3], fallback="")
            if filename not in DOWNLOADABLE_FILES:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self._send_file(self.server.run_root / session_id / "outputs" / filename)
            return
        if len(parts) == 4 and parts[1] == "preview":
            session_id = safe_upload_name(parts[2], fallback="")
            filename = safe_upload_name(parts[3], fallback="")
            if Path(filename).suffix.lower() not in PREVIEW_EXTENSIONS:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self._send_file(self.server.run_root / session_id / "uploads" / filename)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/analyze":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content_type = self.headers.get("Content-Type", "")
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0
        uploads = parse_uploaded_files(self.rfile.read(content_length), content_type)
        if not uploads:
            self._send_html(render_upload_page("没有收到可处理的上传文件。"), HTTPStatus.BAD_REQUEST)
            return
        session_id = str(int(time.time() * 1000))
        session_dir = self.server.run_root / session_id
        upload_dir = session_dir / "uploads"
        output_dir = session_dir / "outputs"
        save_uploads(uploads, upload_dir)
        summary = analyze_folder(upload_dir, output_dir)
        write_downloadable_pdf_report(summary, upload_dir, output_dir)
        self._send_html(render_results_page(summary, session_id))

    def log_message(self, format: str, *args: object) -> None:
        print(f"[web] {self.address_string()} - {format % args}")


class ImageQualityHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], run_root: Path):
        super().__init__(server_address, ImageQualityWebHandler)
        self.run_root = Path(run_root)
        self.run_root.mkdir(parents=True, exist_ok=True)


def run_server(host: str = "127.0.0.1", port: int = 7860, run_root: Path = DEFAULT_RUN_ROOT) -> None:
    server = ImageQualityHTTPServer((host, port), run_root)
    print(f"Image quality web UI: http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the image quality upload web UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=7860, type=int)
    parser.add_argument("--run-root", default=DEFAULT_RUN_ROOT, type=Path)
    args = parser.parse_args(argv)
    run_server(args.host, args.port, args.run_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
