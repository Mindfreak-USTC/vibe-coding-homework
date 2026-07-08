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


if __name__ == "__main__":
    unittest.main()
