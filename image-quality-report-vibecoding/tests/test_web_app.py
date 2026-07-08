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

    def test_results_page_exposes_metrics_downloads_and_charts(self):
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
                    "width": 128,
                    "height": 96,
                    "brightness": 120.5,
                    "contrast": 30.2,
                    "sharpness": 88.0,
                    "noise": 4.5,
                    "issues": ["low_contrast"],
                    "error": "",
                }
            ],
        )

        html = render_results_page(summary, session_id="demo123")

        self.assertIn("样例.png", html)
        self.assertIn("low_contrast", html)
        self.assertIn("/download/demo123/quality_results.csv", html)
        self.assertIn("/download/demo123/report.md", html)
        self.assertIn("/download/demo123/issue_counts.png", html)
        self.assertIn("<table", html)


if __name__ == "__main__":
    unittest.main()
