from __future__ import annotations

from collections import Counter
from pathlib import Path


def generate_markdown_report(
    rows: list[dict[str, object]],
    output_path: Path,
    chart_paths: list[Path],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    total = len(rows)
    valid = sum(1 for row in rows if row.get("status") == "ok")
    skipped = sum(1 for row in rows if row.get("status") == "skipped")
    errors = sum(1 for row in rows if row.get("status") == "error")
    issue_counter: Counter[str] = Counter()
    for row in rows:
        issues = row.get("issues", [])
        if isinstance(issues, str):
            issues = [item for item in issues.split(";") if item]
        issue_counter.update(str(issue) for issue in issues)

    lines = [
        "# 图像质量检测报告",
        "",
        "## 汇总",
        f"- 总文件数: {total}",
        f"- 有效图像数: {valid}",
        f"- 跳过的非图像文件数: {skipped}",
        f"- 损坏或读取失败文件数: {errors}",
        "",
        "## 问题类型统计",
    ]
    if issue_counter:
        for issue, count in sorted(issue_counter.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- {issue}: {count}")
    else:
        lines.append("- 未发现质量问题")

    lines.extend(["", "## 图表"])
    for chart_path in chart_paths:
        lines.append(f"- ![]({chart_path.name})")

    lines.extend(
        [
            "",
            "## 明细预览",
            "| 文件名 | 状态 | 亮度 | 对比度 | 清晰度 | 噪声 | 分辨率 | 问题 |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in rows[:30]:
        issues = row.get("issues", [])
        if isinstance(issues, list):
            issues_text = ";".join(str(issue) for issue in issues)
        else:
            issues_text = str(issues)
        resolution = f"{row.get('width', '')}x{row.get('height', '')}"
        lines.append(
            "| {filename} | {status} | {brightness} | {contrast} | {sharpness} | {noise} | {resolution} | {issues} |".format(
                filename=row.get("filename", ""),
                status=row.get("status", ""),
                brightness=row.get("brightness", ""),
                contrast=row.get("contrast", ""),
                sharpness=row.get("sharpness", ""),
                noise=row.get("noise", ""),
                resolution=resolution,
                issues=issues_text,
            )
        )

    lines.extend(
        [
            "",
            "## 结论",
            "- 过暗、过曝、模糊、低对比度、高噪声和低分辨率由阈值规则自动判断。",
            "- 阈值适合课堂作业和快速巡检；实际生产环境应结合业务样本重新标定。",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

