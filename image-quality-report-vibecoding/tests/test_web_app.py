from pathlib import Path
import sys
import unittest
import uuid
from urllib.parse import quote

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
TMP_ROOT = ROOT / "test_runs"
TMP_ROOT.mkdir(exist_ok=True)


class ProjectTempDir:
    def __enter__(self):
        self.path = TMP_ROOT / f"web_{uuid.uuid4().hex}"
        self.path.mkdir(parents=True, exist_ok=False)
        return str(self.path)

    def __exit__(self, exc_type, exc, traceback):
        return False


class WebAppTests(unittest.TestCase):
    def test_safe_upload_name_strips_paths_and_unsafe_chars(self):
        from image_quality.web_app import safe_upload_name

        name = safe_upload_name(r"..\输入目录/中文:?截图.png", fallback="upload.png")

        self.assertEqual(name, "中文__截图.png")
        self.assertNotIn("/", name)
        self.assertNotIn("\\", name)
        self.assertNotIn("..", name)

    def test_upload_page_contains_multi_image_form(self):
        from image_quality.web_app import render_upload_page

        html = render_upload_page()

        self.assertIn('enctype="multipart/form-data"', html)
        self.assertIn('type="file"', html)
        self.assertIn("multiple", html)
        self.assertIn("jpg", html.lower())
        self.assertIn("png", html.lower())
        self.assertIn("bmp", html.lower())
        self.assertIn('<body class="upload-page">', html)
        self.assertIn(".upload-page main {", html)
        self.assertIn('class="hero upload-hero"', html)
        self.assertIn(".upload-hero h1 {", html)
        self.assertIn("text-align: center;", html)
        self.assertIn("white-space: nowrap;", html)
        self.assertIn("min-height: 240px;", html)

    def test_results_page_exposes_metrics_downloads_charts_and_preview(self):
        from image_quality.analyzer import AnalysisSummary
        from image_quality.web_app import render_results_page

        summary = AnalysisSummary(
            total_files=1,
            valid_images=1,
            skipped_files=0,
            error_files=0,
            csv_path=Path("quality_results.csv"),
            report_path=Path("report.md"),
            chart_paths=[
                Path("issue_counts.png"),
                Path("brightness_distribution.png"),
                Path("sharpness_distribution.png"),
            ],
            rows=[
                {
                    "filename": "宏村-白天3.png",
                    "status": "ok",
                    "width": 8256,
                    "height": 5504,
                    "brightness": 120.5,
                    "contrast": 66.2,
                    "sharpness": 445.8,
                    "noise": 4.5,
                    "issues": [],
                    "error": "",
                }
            ],
        )

        html = render_results_page(summary, session_id="demo123")

        preview_path = f"/preview/demo123/{quote('宏村-白天3.png', safe='')}"
        self.assertIn("宏村-白天3.png", html)
        self.assertIn("原图预览", html)
        self.assertIn(preview_path, html)
        self.assertIn("<figcaption>宏村-白天3.png</figcaption>", html)
        self.assertIn("border: 0;", html)
        self.assertIn("box-shadow: none;", html)
        self.assertIn("padding: 0;", html)
        self.assertIn("text-align: center;", html)
        self.assertNotIn("<br>正常", html)
        self.assertIn("正常", html)
        self.assertIn('class="stats hero-stats"', html)
        self.assertIn("grid-template-columns: repeat(2, minmax(160px, 1fr));", html)
        self.assertIn(".hero-stats .stat strong { font-size: 44px; }", html)
        toolbar_index = html.index('class="toolbar"')
        stats_index = html.index('class="stats hero-stats"')
        preview_index = html.index('class="preview-panel"')
        self.assertLess(toolbar_index, stats_index)
        self.assertLess(stats_index, preview_index)
        self.assertIn("质量指标", html)
        self.assertIn('class="panel metrics-panel"', html)
        self.assertIn("margin-top: 32px;", html)
        self.assertIn("preview-panel", html)
        self.assertIn("metric-note", html)
        self.assertIn("亮度和对比度来自 0-255 灰度统计", html)
        self.assertIn("亮度指标图", html)
        self.assertIn("清晰度指标图", html)
        self.assertIn("chart-explainer", html)
        self.assertIn("font-size: 20px;", html)
        self.assertIn("横轴为数量，纵轴为问题类型", html)
        self.assertIn("横轴为亮度值，纵轴为图片文件名", html)
        self.assertIn("横轴为清晰度相对值，纵轴为图片文件名", html)
        self.assertNotIn("亮度分布图", html)
        self.assertNotIn("清晰度分布图", html)
        self.assertNotIn("本次汇总", html)
        self.assertNotIn("问题：", html)
        self.assertNotIn(">ok<", html)
        self.assertIn("/download/demo123/quality_results.csv", html)
        self.assertIn('/download/demo123/report.pdf" download', html)
        self.assertNotIn('/download/demo123/report.md">下载报告', html)
        self.assertNotIn('/download/demo123/report.html', html)
        self.assertIn("/download/demo123/issue_counts.png", html)
        self.assertNotIn("<table", html)
        self.assertRegex(html, r"<span>亮度</span>\s*<strong>120\.5</strong>\s*<em>亮度正常</em>")
        self.assertRegex(html, r"<span>对比度</span>\s*<strong>66\.2</strong>\s*<em>对比度正常</em>")
        self.assertRegex(html, r"<span>清晰度</span>\s*<strong>445\.8</strong>\s*<em>清晰</em>")
        self.assertRegex(html, r"<span>噪点</span>\s*<strong>4\.5</strong>\s*<em>噪点正常</em>")
        self.assertRegex(html, r"<span>分辨率</span>\s*<strong>8256x5504</strong>\s*<em>高分辨率</em>")

    def test_results_page_translates_problem_labels(self):
        from image_quality.analyzer import AnalysisSummary
        from image_quality.web_app import render_results_page

        summary = AnalysisSummary(
            total_files=1,
            valid_images=1,
            skipped_files=0,
            error_files=0,
            csv_path=Path("quality_results.csv"),
            report_path=Path("report.md"),
            chart_paths=[],
            rows=[
                {
                    "filename": "暗图.png",
                    "status": "ok",
                    "width": 40,
                    "height": 40,
                    "brightness": 28.2,
                    "contrast": 12.4,
                    "sharpness": 20.0,
                    "noise": 28.0,
                    "issues": ["too_dark", "low_contrast", "blurry", "high_noise", "low_resolution"],
                    "error": "",
                }
            ],
        )

        html = render_results_page(summary, session_id="demo456")

        self.assertIn('class="status-pill status-warning"', html)
        self.assertIn(">过暗；对比度偏低；模糊；噪点偏高；分辨率偏低</span>", html)
        self.assertNotIn('<span class="status-pill status-ok">正常</span>', html)
        self.assertNotIn("<br>正常 ·", html)
        self.assertIn("<figcaption>暗图.png</figcaption>", html)
        self.assertNotIn("<figcaption>暗图.png<br>", html)
        self.assertNotIn("问题：", html)
        self.assertRegex(html, r"<span>亮度</span>\s*<strong>28\.2</strong>\s*<em>偏暗</em>")
        self.assertRegex(html, r"<span>对比度</span>\s*<strong>12\.4</strong>\s*<em>对比度偏低</em>")
        self.assertRegex(html, r"<span>清晰度</span>\s*<strong>20\.0</strong>\s*<em>偏模糊</em>")
        self.assertRegex(html, r"<span>噪点</span>\s*<strong>28\.0</strong>\s*<em>噪点偏高</em>")
        self.assertRegex(html, r"<span>分辨率</span>\s*<strong>40x40</strong>\s*<em>分辨率偏低</em>")
        self.assertIn("过暗；对比度偏低；模糊；噪点偏高；分辨率偏低", html)

    def test_content_disposition_is_safe_for_chinese_filenames(self):
        from image_quality.web_app import _content_disposition

        header = _content_disposition("宏村-白天3.png")

        header.encode("latin-1")
        self.assertIn("filename*=UTF-8''", header)
        self.assertNotIn("宏村", header)

    def test_downloadable_report_is_pdf_attachment(self):
        from image_quality.analyzer import AnalysisSummary
        from image_quality.web_app import DOWNLOADABLE_FILES, _content_disposition, write_downloadable_pdf_report

        with ProjectTempDir() as tmp:
            root = Path(tmp)
            upload_dir = root / "uploads"
            output_dir = root / "outputs"
            upload_dir.mkdir()
            output_dir.mkdir()
            Image.new("RGB", (12, 12), (120, 160, 200)).save(upload_dir / "样图.png")
            Image.new("RGB", (12, 12), (255, 255, 255)).save(output_dir / "issue_counts.png")

            summary = AnalysisSummary(
                total_files=1,
                valid_images=1,
                skipped_files=0,
                error_files=0,
                csv_path=output_dir / "quality_results.csv",
                report_path=output_dir / "report.md",
                chart_paths=[output_dir / "issue_counts.png"],
                rows=[
                    {
                        "filename": "样图.png",
                        "status": "ok",
                        "width": 1200,
                        "height": 900,
                        "brightness": 120.0,
                        "contrast": 40.0,
                        "sharpness": 180.0,
                        "noise": 2.0,
                        "issues": [],
                        "error": "",
                    }
                ],
            )

            report_path = write_downloadable_pdf_report(summary, upload_dir, output_dir)
            report_bytes = report_path.read_bytes()

        self.assertIn("report.pdf", DOWNLOADABLE_FILES)
        self.assertNotIn("report.html", DOWNLOADABLE_FILES)
        self.assertTrue(report_path.name.endswith(".pdf"))
        self.assertGreater(len(report_bytes), 2000)
        self.assertTrue(report_bytes.startswith(b"%PDF"))
        self.assertTrue(_content_disposition("检测报告.pdf", disposition="attachment").startswith("attachment;"))


if __name__ == "__main__":
    unittest.main()
