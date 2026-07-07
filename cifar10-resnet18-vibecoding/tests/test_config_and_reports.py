from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
import uuid

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


class ConfigAndReportTests(unittest.TestCase):
    def test_load_config_reads_nested_yaml_values(self):
        from utils import load_config

        with ProjectTempDir() as tmp:
            config_path = Path(tmp) / "config.yaml"
            config_path.write_text(
                """
seed: 7
dataset:
  name: CIFAR10
  batch_size: 4
training:
  epochs: 1
  learning_rate: 0.01
logging:
  backend: tensorboard
""".strip(),
                encoding="utf-8",
            )

            config = load_config(config_path)

        self.assertEqual(config["seed"], 7)
        self.assertEqual(config["dataset"]["batch_size"], 4)
        self.assertEqual(config["training"]["learning_rate"], 0.01)
        self.assertEqual(config["logging"]["backend"], "tensorboard")


    def test_experiment_report_contains_metrics_and_next_steps(self):
        from reports import generate_experiment_report

        with ProjectTempDir() as tmp:
            root = Path(tmp)
            history_path = root / "history.json"
            metrics_path = root / "test_metrics.json"
            report_path = root / "report.md"

            history_path.write_text(
                json.dumps(
                    {
                        "epochs": [
                            {"epoch": 1, "train_loss": 2.1, "train_accuracy": 0.22, "val_loss": 2.0, "val_accuracy": 0.25},
                            {"epoch": 2, "train_loss": 1.8, "train_accuracy": 0.34, "val_loss": 1.9, "val_accuracy": 0.31},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            metrics_path.write_text(
                json.dumps(
                    {
                        "test_accuracy": 0.32,
                        "per_class_accuracy": {"airplane": 0.40, "cat": 0.22},
                        "confusion_matrix_path": "outputs/confusion_matrix.png",
                    }
                ),
                encoding="utf-8",
            )

            generate_experiment_report(history_path, metrics_path, report_path)
            report = report_path.read_text(encoding="utf-8")

        self.assertIn("测试集整体准确率", report)
        self.assertIn("0.3200", report)
        self.assertIn("是否出现明显过拟合", report)
        self.assertIn("后续改进方向", report)

    def test_confusion_matrix_uses_project_local_matplotlib_cache(self):
        from visualization import save_confusion_matrix

        old_cache = os.environ.pop("MPLCONFIGDIR", None)
        try:
            with ProjectTempDir() as tmp:
                output_path = Path(tmp) / "charts" / "confusion_matrix.png"
                save_confusion_matrix([[1, 0], [0, 1]], ["a", "b"], output_path)
                self.assertTrue(output_path.exists())
                self.assertIn(str(output_path.parent / ".matplotlib"), os.environ["MPLCONFIGDIR"])
        finally:
            if old_cache is not None:
                os.environ["MPLCONFIGDIR"] = old_cache

    def test_test_script_quick_dev_overrides_disable_multiprocessing(self):
        import argparse
        import test as test_script

        config = {"dataset": {"batch_size": 128, "num_workers": 2}}
        args = argparse.Namespace(quick_dev_run=True, num_workers=None, batch_size=None)

        updated = test_script.apply_overrides(config, args)

        self.assertEqual(updated["dataset"]["num_workers"], 0)
        self.assertEqual(updated["dataset"]["batch_size"], 64)
        self.assertEqual(updated["dataset"]["test_subset_limit"], 256)


if __name__ == "__main__":
    unittest.main()
