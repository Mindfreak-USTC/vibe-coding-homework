from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from .charts import issue_counts_from_rows, save_bar_chart, save_metric_chart
from .metrics import compute_quality_metrics
from .report import generate_markdown_report

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}


@dataclass
class AnalysisSummary:
    total_files: int
    valid_images: int
    skipped_files: int
    error_files: int
    csv_path: Path
    report_path: Path
    chart_paths: list[Path]
    rows: list[dict[str, Any]]


def classify_issues(
    metrics: dict[str, Any],
    *,
    dark_threshold: float = 45.0,
    bright_threshold: float = 215.0,
    low_contrast_threshold: float = 25.0,
    blur_threshold: float = 80.0,
    noise_threshold: float = 22.0,
    min_width: int = 64,
    min_height: int = 64,
) -> list[str]:
    issues: list[str] = []
    if metrics["brightness"] < dark_threshold:
        issues.append("too_dark")
    if metrics["brightness"] > bright_threshold:
        issues.append("overexposed")
    if metrics["sharpness"] < blur_threshold:
        issues.append("blurry")
    if metrics["contrast"] < low_contrast_threshold:
        issues.append("low_contrast")
    if metrics["noise"] > noise_threshold:
        issues.append("high_noise")
    if metrics["width"] < min_width or metrics["height"] < min_height:
        issues.append("low_resolution")
    return issues


def analyze_image(path: Path, **thresholds: Any) -> dict[str, Any]:
    path = Path(path)
    with Image.open(path) as image:
        image.load()
        metrics = compute_quality_metrics(image)
    issues = classify_issues(metrics, **thresholds)
    return {
        "filename": path.name,
        "path": str(path),
        "status": "ok",
        **metrics,
        "issues": issues,
        "error": "",
    }


def _row_for_skipped(path: Path) -> dict[str, Any]:
    return {
        "filename": path.name,
        "path": str(path),
        "status": "skipped",
        "width": "",
        "height": "",
        "megapixels": "",
        "brightness": "",
        "contrast": "",
        "sharpness": "",
        "noise": "",
        "issues": [],
        "error": "unsupported file type",
    }


def _row_for_error(path: Path, error: Exception) -> dict[str, Any]:
    return {
        "filename": path.name,
        "path": str(path),
        "status": "error",
        "width": "",
        "height": "",
        "megapixels": "",
        "brightness": "",
        "contrast": "",
        "sharpness": "",
        "noise": "",
        "issues": [],
        "error": str(error),
    }


def _write_csv(rows: list[dict[str, Any]], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "filename",
        "path",
        "status",
        "width",
        "height",
        "megapixels",
        "brightness",
        "contrast",
        "sharpness",
        "noise",
        "issues",
        "error",
    ]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            serialized = dict(row)
            issues = serialized.get("issues", [])
            if isinstance(issues, list):
                serialized["issues"] = ";".join(str(issue) for issue in issues)
            writer.writerow({field: serialized.get(field, "") for field in fieldnames})


def analyze_folder(input_dir: Path, output_dir: Path, **thresholds: Any) -> AnalysisSummary:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for path in sorted((p for p in input_dir.iterdir() if p.is_file()), key=lambda p: p.name.lower()):
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            rows.append(_row_for_skipped(path))
            continue
        try:
            rows.append(analyze_image(path, **thresholds))
        except (UnidentifiedImageError, OSError, ValueError) as error:
            rows.append(_row_for_error(path, error))

    csv_path = output_dir / "quality_results.csv"
    _write_csv(rows, csv_path)

    valid_rows = [row for row in rows if row.get("status") == "ok"]
    issue_chart = output_dir / "issue_counts.png"
    brightness_chart = output_dir / "brightness_distribution.png"
    sharpness_chart = output_dir / "sharpness_distribution.png"
    save_bar_chart(issue_counts_from_rows(rows), issue_chart, "问题数量统计图")
    save_metric_chart(
        valid_rows,
        brightness_chart,
        metric="brightness",
        metric_label="亮度",
        title="亮度指标图",
        unit="",
        normal_min=45.0,
        normal_max=215.0,
    )
    save_metric_chart(
        valid_rows,
        sharpness_chart,
        metric="sharpness",
        metric_label="清晰度",
        title="清晰度指标图",
        unit="",
        good_above=80.0,
    )

    report_path = output_dir / "report.md"
    chart_paths = [issue_chart, brightness_chart, sharpness_chart]
    generate_markdown_report(rows, report_path, chart_paths)

    return AnalysisSummary(
        total_files=len(rows),
        valid_images=len(valid_rows),
        skipped_files=sum(1 for row in rows if row.get("status") == "skipped"),
        error_files=sum(1 for row in rows if row.get("status") == "error"),
        csv_path=csv_path,
        report_path=report_path,
        chart_paths=chart_paths,
        rows=rows,
    )
