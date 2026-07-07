from pathlib import Path
import sys
import tempfile
import unittest
import uuid

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
TMP_ROOT = ROOT / "test_runs"
TMP_ROOT.mkdir(exist_ok=True)


class ProjectTempDir:
    def __enter__(self):
        self.path = TMP_ROOT / f"run_{uuid.uuid4().hex}"
        self.path.mkdir(parents=True, exist_ok=False)
        return str(self.path)

    def __exit__(self, exc_type, exc, traceback):
        return False


def save_image(path: Path, array: np.ndarray) -> None:
    Image.fromarray(array.astype(np.uint8), mode="RGB").save(path)


def checkerboard(size: int = 64) -> np.ndarray:
    grid = np.indices((size, size)).sum(axis=0) % 2
    img = (grid * 255).astype(np.uint8)
    return np.stack([img, img, img], axis=2)


class QualityMetricsTests(unittest.TestCase):
    def test_metrics_detect_dark_low_resolution_and_blur(self):
        from image_quality.analyzer import analyze_image

        with ProjectTempDir() as tmp:
            dark_path = Path(tmp) / "过暗样例.png"
            save_image(dark_path, np.full((24, 24, 3), 12, dtype=np.uint8))

            result = analyze_image(dark_path, min_width=64, min_height=64)

        self.assertEqual(result["status"], "ok")
        self.assertLess(result["brightness"], 30)
        self.assertIn("too_dark", result["issues"])
        self.assertIn("low_resolution", result["issues"])

    def test_sharpness_and_noise_metrics_are_ordered(self):
        from image_quality.metrics import compute_quality_metrics

        sharp = checkerboard(64)
        blurred = np.asarray(Image.fromarray(sharp).filter(ImageFilter.GaussianBlur(radius=3)))
        uniform = np.full((64, 64, 3), 120, dtype=np.uint8)
        noisy = np.clip(uniform + np.random.default_rng(42).normal(0, 35, uniform.shape), 0, 255)

        sharp_metrics = compute_quality_metrics(Image.fromarray(sharp))
        blurred_metrics = compute_quality_metrics(Image.fromarray(blurred.astype(np.uint8)))
        uniform_metrics = compute_quality_metrics(Image.fromarray(uniform))
        noisy_metrics = compute_quality_metrics(Image.fromarray(noisy.astype(np.uint8)))

        self.assertGreater(sharp_metrics["sharpness"], blurred_metrics["sharpness"])
        self.assertGreater(noisy_metrics["noise"], uniform_metrics["noise"])

    def test_folder_analysis_handles_chinese_names_non_images_and_corrupt_files(self):
        from image_quality.analyzer import analyze_folder

        with ProjectTempDir() as tmp:
            root = Path(tmp)
            input_dir = root / "输入图片"
            output_dir = root / "outputs"
            input_dir.mkdir()

            save_image(input_dir / "正常图像.png", np.full((96, 96, 3), 128, dtype=np.uint8))
            (input_dir / "说明.txt").write_text("not an image", encoding="utf-8")
            (input_dir / "损坏图片.png").write_bytes(b"not-a-real-png")

            summary = analyze_folder(input_dir, output_dir)

            self.assertEqual(summary.total_files, 3)
            self.assertEqual(summary.valid_images, 1)
            self.assertEqual(summary.skipped_files, 1)
            self.assertEqual(summary.error_files, 1)
            self.assertTrue((output_dir / "quality_results.csv").exists())


if __name__ == "__main__":
    unittest.main()
