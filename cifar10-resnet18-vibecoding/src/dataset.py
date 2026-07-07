from __future__ import annotations

from pathlib import Path
from typing import Any

from utils import project_path

CIFAR10_CLASSES = [
    "airplane",
    "automobile",
    "bird",
    "cat",
    "deer",
    "dog",
    "frog",
    "horse",
    "ship",
    "truck",
]


def _load_deps():
    try:
        import torch
        from torch.utils.data import DataLoader, Subset
        from torchvision import datasets, transforms
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "PyTorch/TorchVision is required. Install project dependencies with "
            "`pip install -r requirements.txt` before training or testing."
        ) from error
    return torch, DataLoader, Subset, datasets, transforms


def build_transforms(config: dict[str, Any]):
    _, _, _, _, transforms = _load_deps()
    normalize = transforms.Normalize(
        mean=config["dataset"].get("mean", [0.4914, 0.4822, 0.4465]),
        std=config["dataset"].get("std", [0.2470, 0.2435, 0.2616]),
    )
    train_transform = transforms.Compose(
        [
            transforms.RandomCrop(32, padding=4),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            normalize,
        ]
    )
    eval_transform = transforms.Compose([transforms.ToTensor(), normalize])
    return train_transform, eval_transform


def _split_indices(total: int, val_ratio: float, seed: int) -> tuple[list[int], list[int]]:
    torch, _, _, _, _ = _load_deps()
    generator = torch.Generator().manual_seed(seed)
    indices = torch.randperm(total, generator=generator).tolist()
    val_size = max(1, int(total * val_ratio))
    return indices[val_size:], indices[:val_size]


def build_data_loaders(config: dict[str, Any]) -> dict[str, Any]:
    torch, DataLoader, Subset, datasets, _ = _load_deps()
    train_transform, eval_transform = build_transforms(config)
    dataset_cfg = config["dataset"]
    download = bool(dataset_cfg.get("download", True))
    batch_size = int(dataset_cfg.get("batch_size", 128))
    num_workers = int(dataset_cfg.get("num_workers", 2))
    seed = int(config.get("seed", 42))
    num_classes = int(config.get("model", {}).get("num_classes", 10))

    if bool(dataset_cfg.get("fake_data", False)):
        train_base = datasets.FakeData(
            size=int(dataset_cfg.get("fake_train_size", 128)),
            image_size=(3, 32, 32),
            num_classes=num_classes,
            transform=train_transform,
        )
        val_base = datasets.FakeData(
            size=int(dataset_cfg.get("fake_val_size", 32)),
            image_size=(3, 32, 32),
            num_classes=num_classes,
            transform=eval_transform,
        )
        test_base = datasets.FakeData(
            size=int(dataset_cfg.get("fake_test_size", 32)),
            image_size=(3, 32, 32),
            num_classes=num_classes,
            transform=eval_transform,
        )
        pin_memory = torch.cuda.is_available()
        return {
            "train": DataLoader(train_base, batch_size=batch_size, shuffle=True, num_workers=0, pin_memory=pin_memory),
            "val": DataLoader(val_base, batch_size=batch_size, shuffle=False, num_workers=0, pin_memory=pin_memory),
            "test": DataLoader(test_base, batch_size=batch_size, shuffle=False, num_workers=0, pin_memory=pin_memory),
            "classes": CIFAR10_CLASSES,
        }

    data_dir = project_path(dataset_cfg.get("data_dir", "./data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    val_ratio = float(dataset_cfg.get("val_ratio", 0.1))
    train_base = datasets.CIFAR10(root=data_dir, train=True, transform=train_transform, download=download)
    val_base = datasets.CIFAR10(root=data_dir, train=True, transform=eval_transform, download=False)
    train_indices, val_indices = _split_indices(len(train_base), val_ratio, seed)

    subset_limit = dataset_cfg.get("subset_limit")
    if subset_limit:
        limit = int(subset_limit)
        train_indices = train_indices[:limit]
        val_indices = val_indices[: max(1, min(len(val_indices), limit // 5))]

    test_base = datasets.CIFAR10(root=data_dir, train=False, transform=eval_transform, download=download)
    test_limit = dataset_cfg.get("test_subset_limit")
    if test_limit:
        test_base = Subset(test_base, list(range(min(int(test_limit), len(test_base)))))

    pin_memory = torch.cuda.is_available()
    return {
        "train": DataLoader(
            Subset(train_base, train_indices),
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=pin_memory,
        ),
        "val": DataLoader(
            Subset(val_base, val_indices),
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=pin_memory,
        ),
        "test": DataLoader(
            test_base,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=pin_memory,
        ),
        "classes": CIFAR10_CLASSES,
    }
