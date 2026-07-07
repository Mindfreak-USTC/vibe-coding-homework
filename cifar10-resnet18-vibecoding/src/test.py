from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from dataset import build_data_loaders
from evaluate import evaluate
from model import build_model
from reports import generate_experiment_report
from utils import ensure_dir, load_config, project_path, resolve_device, save_json, set_seed
from visualization import save_confusion_matrix


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate a trained CIFAR-10 checkpoint.")
    parser.add_argument("--config", default="configs/default.yaml", type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--offline-smoke", action="store_true", help="Use TorchVision FakeData for pipeline verification.")
    return parser


def _load_checkpoint(model, checkpoint_path: Path, device: str) -> dict[str, Any]:
    import torch

    checkpoint_path = project_path(checkpoint_path)
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location=device)
    state_dict = checkpoint.get("model_state_dict", checkpoint)
    model.load_state_dict(state_dict)
    return checkpoint if isinstance(checkpoint, dict) else {}


def main() -> int:
    import torch.nn as nn

    args = build_parser().parse_args()
    config = load_config(args.config)
    if args.offline_smoke:
        config.setdefault("dataset", {})["fake_data"] = True
        config.setdefault("dataset", {})["fake_test_size"] = 32
        config.setdefault("dataset", {})["batch_size"] = 32
        config.setdefault("dataset", {})["num_workers"] = 0
    set_seed(int(config.get("seed", 42)))
    device = resolve_device(str(config.get("device", "auto")))

    loaders = build_data_loaders(config)
    model = build_model(config).to(device)
    _load_checkpoint(model, args.checkpoint, device)
    criterion = nn.CrossEntropyLoss()

    metrics = evaluate(
        model,
        loaders["test"],
        criterion,
        device,
        num_classes=int(config.get("model", {}).get("num_classes", 10)),
    )
    class_names = loaders["classes"]
    per_class = {
        class_name: metrics["per_class_accuracy"][index]
        for index, class_name in enumerate(class_names)
    }
    outputs_dir = ensure_dir(project_path(config.get("outputs", {}).get("dir", "./outputs")))
    confusion_path = outputs_dir / "confusion_matrix.png"
    save_confusion_matrix(metrics["confusion_matrix"], class_names, confusion_path)

    test_metrics = {
        "dataset_name": "TorchVision FakeData (offline smoke)" if config.get("dataset", {}).get("fake_data") else "CIFAR-10",
        "test_loss": metrics["loss"],
        "test_accuracy": metrics["accuracy"],
        "per_class_accuracy": per_class,
        "confusion_matrix_path": str(confusion_path),
        "samples": metrics["samples"],
    }
    metrics_path = outputs_dir / "test_metrics.json"
    save_json(test_metrics, metrics_path)

    history_path = outputs_dir / "history.json"
    if not history_path.exists():
        save_json({"epochs": []}, history_path)
    generate_experiment_report(history_path, metrics_path, outputs_dir / "report.md")

    print(f"Test accuracy: {metrics['accuracy']:.4f}")
    for class_name, accuracy in per_class.items():
        print(f"{class_name}: {accuracy:.4f}")
    print(f"Metrics: {metrics_path}")
    print(f"Confusion matrix: {confusion_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
