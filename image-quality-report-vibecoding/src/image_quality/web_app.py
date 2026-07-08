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

from .analyzer import AnalysisSummary, analyze_folder

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_ROOT = PROJECT_ROOT / "web_runs"
PREVIEW_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}
DOWNLOADABLE_FILES = {
    "quality_results.csv",
    "report.md",
    "issue_counts.png",
    "brightness_distribution.png",
    "sharpness_distribution.png",
}
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
    "high_noise": "噪声偏高",
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
        label = "噪声偏高" if value > 22 else "噪声正常"
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
        return f"{value:.1f}", ("噪声偏高" if value > 22 else "噪声正常"), ("warn" if value > 22 else "ok")
    return f"{value:.1f}", "正常", "ok"


def _resolution_conclusion(row: dict[str, object]) -> str:
    width = _to_int(row.get("width"))
    height = _to_int(row.get("height"))
    if width is None or height is None:
        return "未检测"
    label = "分辨率偏低" if width < 64 or height < 64 else "高分辨率"
    return f"{label} · {width}x{height}"


def _resolution_parts(row: dict[str, object]) -> tuple[str, str, str]:
    width = _to_int(row.get("width"))
    height = _to_int(row.get("height"))
    if width is None or height is None:
        return "未检测", "未检测", "warn"
    value_text = f"{width}x{height}"
    if width < 64 or height < 64:
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


def _content_disposition(filename: str) -> str:
    fallback = "".join(char if char.isascii() and char not in '"\\\r\n' else "_" for char in filename)
    fallback = fallback.strip(" .") or "file"
    encoded = quote(filename, safe="")
    return f'inline; filename="{fallback}"; filename*=UTF-8\'\'{encoded}'


def _base_page(title: str, body: str) -> str:
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
      grid-template-columns: repeat(4, minmax(92px, 1fr));
      gap: 12px;
      margin: 24px 0 0;
      max-width: 760px;
    }}
    .hero-stats .stat {{
      min-height: 88px;
      padding: 14px 16px;
    }}
    .hero-stats .stat strong {{ font-size: 30px; }}
    .hero-stats .stat span {{ font-size: 15px; }}
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
      border: 2px solid var(--line);
      background: white;
      padding: 14px;
      box-shadow: 6px 6px 0 rgba(20, 20, 20, .18);
    }}
    .preview-card img {{
      display: block;
      width: 100%;
      height: 260px;
      object-fit: contain;
      background: #f8fafc;
      border: 1px solid #cbd5e1;
    }}
    .preview-card figcaption {{
      margin-top: 12px;
      font-size: 22px;
      font-weight: 700;
      line-height: 1.45;
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
      white-space: nowrap;
    }}
    .issue-line {{
      margin: 0 0 18px;
      color: var(--ink);
      font-size: 21px;
      font-weight: 700;
      line-height: 1.45;
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
      font-size: 20px;
      font-weight: 700;
    }}
    .chart-explainer {{
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.55;
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
<body>
  <main>
    {body}
  </main>
</body>
</html>"""


def render_upload_page(message: str = "") -> str:
    notice = f'<p class="hint">{escape(message)}</p>' if message else ""
    body = f"""
<section class="hero">
  <div>
    <h1>图像质量检测与自动报告系统</h1>
    <p>上传 JPG、PNG 或 BMP 图片后，系统会计算亮度、对比度、清晰度、噪声和分辨率，并自动生成 CSV、Markdown 报告和统计图。</p>
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
    return _base_page("图像质量检测与自动报告系统", body)


def render_results_page(summary: AnalysisSummary, session_id: str) -> str:
    metric_sections = []
    preview_cards = []
    for row in summary.rows:
        status = str(row.get("status", ""))
        filename = str(row.get("filename", ""))
        status_label = _status_label(status)
        issue_text = _issue_text(row.get("issues", []))
        if status == "ok":
            preview_cards.append(
                '<figure class="preview-card">'
                f'<img src="/preview/{_url_part(session_id)}/{_url_part(filename)}" alt="原图预览：{escape(filename)}">'
                f"<figcaption>{escape(filename)}<br>{escape(status_label)} · {escape(issue_text)}</figcaption>"
                "</figure>"
            )
        metric_cards = []
        for label, metric in (
            ("亮度", "brightness"),
            ("对比度", "contrast"),
            ("清晰度", "sharpness"),
            ("噪声", "noise"),
        ):
            value_text, verdict, tone = _metric_parts(metric, row)
            metric_cards.append(_metric_card(label, value_text, verdict, tone))
        resolution_value, resolution_verdict, resolution_tone = _resolution_parts(row)
        metric_cards.append(_metric_card("分辨率", resolution_value, resolution_verdict, resolution_tone))
        status_class = f"status-{escape(status)}"
        metric_sections.append(
            '<article class="file-result">'
            '<div class="file-meta">'
            f'<h3 class="file-name">{escape(filename)}</h3>'
            f'<span class="status-pill {status_class}">{escape(status_label)}</span>'
            "</div>"
            f'<p class="issue-line">问题：{escape(issue_text)}</p>'
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
      <p>已生成每张图片的质量指标、问题标签、CSV 汇总、Markdown 报告和统计图。</p>
      <div class="toolbar">
        <a class="button" href="/">继续上传</a>
        <a class="button" href="/download/{escape(session_id)}/quality_results.csv">下载 CSV</a>
        <a class="button" href="/download/{escape(session_id)}/report.md">下载报告</a>
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
  <div class="panel">
    <h2>质量指标</h2>
    {metric_body}
    <p class="metric-note">数据说明：亮度和对比度来自 0-255 灰度统计；清晰度和噪声是算法相对强度，无物理单位；分辨率单位为像素。</p>
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
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Content-Disposition", _content_disposition(path.name))
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
