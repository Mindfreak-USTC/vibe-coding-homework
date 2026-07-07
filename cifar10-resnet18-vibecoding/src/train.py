from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from dataset import build_data_loaders
from evaluate import evaluate
from logger import create_writer
from model import build_model
from utils import ensure_dir, load_config, project_path, resolve_device, save_json, set_seed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train ResNet-18 on CIFAR-10.")
    parser.add_argument("--config", default="configs/default.yaml", type=Path)
    parser.add_argument("--epochs", type=int, help="Override training epochs.")
    parser.add_argument("--batch-size", type=int, help="Override batch size.")
    parser.add_argument("--learning-rate", type=float, help="Override learning rate.")
    parser.add_argument("--quick-dev-run", action="store_true", help="Use tiny subsets and one epoch for CPU smoke tests.")
    parser.add_argument("--offline-smoke", action="store_true", help="Use TorchVision FakeData to verify the pipeline without downloading CIFAR-10.")
    return parser


def apply_overrides(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    if args.epochs is not None:
        config.setdefault("training", {})["epochs"] = args.epochs
    if args.batch_size is not None:
        config.setdefault("dataset", {})["batch_size"] = args.batch_size
    if args.learning_rate is not None:
        config.setdefault("training", {})["learning_rate"] = args.learning_rate
    if args.quick_dev_run:
        config.setdefault("training", {})["epochs"] = 1
        config.setdefault("dataset", {})["subset_limit"] = 512
        config.setdefault("dataset", {})["test_subset_limit"] = 256
        config.setdefault("dataset", {})["num_workers"] = 0
    if args.offline_smoke:
        config.setdefault("training", {})["epochs"] = 1
        config.setdefault("dataset", {})["fake_data"] = True
        config.setdefault("dataset", {})["fake_train_size"] = 128
        config.setdefault("dataset", {})["fake_val_size"] = 32
        config.setdefault("dataset", {})["fake_test_size"] = 32
        config.setdefault("dataset", {})["batch_size"] = 32
        config.setdefault("dataset", {})["num_workers"] = 0
    return config


def build_optimizer(config: dict[str, Any], model):
    import torch.optim as optim

    training = config.get("training", {})
    lr = float(training.get("learning_rate", 0.001))
    weight_decay = float(training.get("weight_decay", 0.0005))
    optimizer_name = str(training.get("optimizer", "adam")).lower()
    if optimizer_name == "sgd":
        return optim.SGD(model.parameters(), lr=lr, momentum=0.9, weight_decay=weight_decay)
    if optimizer_name == "adamw":
        return optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    return optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)


def train_one_epoch(model, dataloader, criterion, optimizer, device: str) -> dict[str, float]:
    model.train()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0
    for images, targets in dataloader:
        images = images.to(device)
        targets = targets.to(device)
        optimizer.zero_grad(set_to_none=True)
        outputs = model(images)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        preds = outputs.argmax(dim=1)
        batch_size = targets.size(0)
        total_loss += float(loss.item()) * batch_size
        total_correct += int((preds == targets).sum().item())
        total_samples += batch_size
    return {
        "loss": total_loss / max(1, total_samples),
        "accuracy": total_correct / max(1, total_samples),
    }


def save_checkpoint(path: Path, model, optimizer, epoch: int, config: dict[str, Any], best_val_accuracy: float) -> None:
    import torch

    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "config": config,
            "best_val_accuracy": best_val_accuracy,
        },
        path,
    )


def main() -> int:
    import torch
    import torch.nn as nn

    args = build_parser().parse_args()
    config = apply_overrides(load_config(args.config), args)
    set_seed(int(config.get("seed", 42)))
    device = resolve_device(str(config.get("device", "auto")))

    loaders = build_data_loaders(config)
    model = build_model(config).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = build_optimizer(config, model)
    writer = create_writer(config)

    checkpoint_dir = ensure_dir(project_path(config.get("checkpoint", {}).get("save_dir", "./checkpoints")))
    outputs_dir = ensure_dir(project_path(config.get("outputs", {}).get("dir", "./outputs")))
    history: list[dict[str, float]] = []
    best_val_accuracy = -1.0
    epochs = int(config.get("training", {}).get("epochs", 10))

    for epoch in range(1, epochs + 1):
        train_metrics = train_one_epoch(model, loaders["train"], criterion, optimizer, device)
        val_metrics = evaluate(
            model,
            loaders["val"],
            criterion,
            device,
            num_classes=int(config.get("model", {}).get("num_classes", 10)),
        )

        row = {
            "epoch": epoch,
            "train_loss": train_metrics["loss"],
            "train_accuracy": train_metrics["accuracy"],
            "val_loss": val_metrics["loss"],
            "val_accuracy": val_metrics["accuracy"],
        }
        history.append(row)
        writer.add_scalar("loss/train", row["train_loss"], epoch)
        writer.add_scalar("loss/val", row["val_loss"], epoch)
        writer.add_scalar("accuracy/train", row["train_accuracy"], epoch)
        writer.add_scalar("accuracy/val", row["val_accuracy"], epoch)
        writer.add_scalar("learning_rate", optimizer.param_groups[0]["lr"], epoch)

        print(
            "Epoch {epoch}/{epochs} | train loss {train_loss:.4f} acc {train_accuracy:.4f} | "
            "val loss {val_loss:.4f} acc {val_accuracy:.4f}".format(epochs=epochs, **row)
        )
        save_checkpoint(checkpoint_dir / "last_checkpoint.pth", model, optimizer, epoch, config, best_val_accuracy)
        if row["val_accuracy"] > best_val_accuracy:
            best_val_accuracy = row["val_accuracy"]
            save_checkpoint(checkpoint_dir / "best_model.pth", model, optimizer, epoch, config, best_val_accuracy)

    save_checkpoint(checkpoint_dir / "final_model.pth", model, optimizer, epochs, config, best_val_accuracy)
    dataset_name = "TorchVision FakeData (offline smoke)" if config.get("dataset", {}).get("fake_data") else "CIFAR-10"
    save_json(
        {"dataset_name": dataset_name, "epochs": history, "best_val_accuracy": best_val_accuracy},
        outputs_dir / "history.json",
    )
    writer.close()
    print(f"Training complete. Best validation accuracy: {best_val_accuracy:.4f}")
    print(f"Best checkpoint: {checkpoint_dir / 'best_model.pth'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
