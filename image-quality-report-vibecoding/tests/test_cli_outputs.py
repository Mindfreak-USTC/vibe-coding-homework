from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
import uuid

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TMP_ROOT = ROOT / "test_runs"
TMP_ROOT.mkdir(exist_ok=True)


class ProjectTempDir:
    def __enter__(self):
        self.path = TMP_ROOT / f"run_{uuid.uuid4().hex}"
        self.path.mkdir(parents=True, exist_ok=False)
        return str(self.path)

    def __exit__(self, exc_type, exc, traceback):
        return False


class CliOutputTests(unittest.TestCase):
    def _target_color_ratio(self, image_path: Path, rgb: tuple[int, int, int], tolerance: int = 4) -> float:
        with Image.open(image_path) as image:
            pixels = np.asarray(image.convert("RGB"), dtype=np.int16)
        target = np.array(rgb, dtype=np.int16)
        matches = np.all(np.abs(pixels - target) <= tolerance, axis=2)
        return float(matches.sum() / matches.size)

    def test_cli_generates_csv_report_and_two_charts(self):
        with ProjectTempDir() as tmp:
            root = Path(tmp)
            input_dir = root / "images"
            output_dir = root / "outputs"
            input_dir.mkdir()

            Image.fromarray(np.full((96, 96, 3), 130, dtype=np.uint8)).save(input_dir / "normal.png")
            Image.fromarray(np.full((24, 24, 3), 8, dtype=np.uint8)).save(input_dir / "低亮度.png")

            command = [
                sys.executable,
                "-m",
                "image_quality.cli",
                "--input",
                str(input_dir),
                "--output",
                str(output_dir),
            ]
            env = os.environ.copy()
            env["PYTHONPATH"] = str(ROOT / "src")
            completed = subprocess.run(
                command,
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((output_dir / "quality_results.csv").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue((output_dir / "issue_counts.png").exists())
            self.assertTrue((output_dir / "brightness_distribution.png").exists())
            self.assertTrue((output_dir / "sharpness_distribution.png").exists())
            report = (output_dir / "report.md").read_text(encoding="utf-8")
            self.assertIn("- 模糊:", report)
            self.assertIn("- 对比度偏低:", report)
            self.assertIn("问题数量统计图", report)
            self.assertIn("亮度指标图", report)
            self.assertIn("清晰度指标图", report)
            self.assertIn("| normal.png | 正常 |", report)
            self.assertNotIn("- blurry:", report)
            self.assertNotIn("- low_contrast:", report)
            self.assertNotIn("| ok |", report)
            with Image.open(output_dir / "issue_counts.png") as chart:
                self.assertGreaterEqual(chart.width, 1200)
                self.assertGreaterEqual(chart.height, 720)
            with Image.open(output_dir / "brightness_distribution.png") as chart:
                self.assertGreaterEqual(chart.width, 1200)
                self.assertGreaterEqual(chart.height, 720)
            with Image.open(output_dir / "sharpness_distribution.png") as chart:
                self.assertGreaterEqual(chart.width, 1200)
                self.assertGreaterEqual(chart.height, 720)

    def test_single_image_charts_use_markers_instead_of_large_color_blocks(self):
        from image_quality.charts import save_bar_chart, save_metric_chart

        with ProjectTempDir() as tmp:
            root = Path(tmp)
            issue_chart = root / "issue_counts.png"
            brightness_chart = root / "brightness_distribution.png"

            save_bar_chart({"good": 1}, issue_chart, "问题数量统计图")
            save_metric_chart(
                [
                    {
                        "filename": "单张图片.png",
                        "status": "ok",
                        "brightness": 172.4,
                    }
                ],
                brightness_chart,
                metric="brightness",
                metric_label="亮度",
                title="亮度指标图",
                unit="",
                normal_min=45,
                normal_max=215,
            )

            self.assertLess(self._target_color_ratio(issue_chart, (76, 120, 168)), 0.04)
            self.assertLess(self._target_color_ratio(brightness_chart, (15, 118, 110)), 0.04)


if __name__ == "__main__":
    unittest.main()
