from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


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
            chart_paths=[Path("issue_counts.png"), Path("brightness_distribution.png")],
            rows=[
                {
                    "filename": "样例.png",
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

        self.assertIn("样例.png", html)
        self.assertIn("原图预览", html)
        self.assertIn("/preview/demo123/样例.png", html)
        self.assertIn("正常", html)
        self.assertIn("亮度正常 · 120.5", html)
        self.assertIn("对比度正常 · 66.2", html)
        self.assertIn("清晰 · 445.8", html)
        self.assertIn("噪声正常 · 4.5", html)
        self.assertIn("高分辨率 · 8256x5504", html)
        self.assertIn("无明显问题", html)
        self.assertNotIn(">ok<", html)
        self.assertIn("/download/demo123/quality_results.csv", html)
        self.assertIn("/download/demo123/report.md", html)
        self.assertIn("/download/demo123/issue_counts.png", html)
        self.assertIn("<table", html)
        self.assertIn("font-size: 28px", html)
        self.assertIn("grid-template-columns: 1fr", html)

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

        self.assertIn("偏暗 · 28.2", html)
        self.assertIn("对比度偏低 · 12.4", html)
        self.assertIn("偏模糊 · 20.0", html)
        self.assertIn("噪声偏高 · 28.0", html)
        self.assertIn("分辨率偏低 · 40x40", html)
        self.assertIn("过暗；对比度偏低；模糊；噪声偏高；分辨率偏低", html)


if __name__ == "__main__":
    unittest.main()
