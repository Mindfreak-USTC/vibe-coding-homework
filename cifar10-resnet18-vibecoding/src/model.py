from __future__ import annotations

from typing import Any


def build_model(config: dict[str, Any]):
    try:
        import torch.nn as nn
        from torchvision import models
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "PyTorch/TorchVision is required. Install project dependencies with "
            "`pip install -r requirements.txt` before building the model."
        ) from error

    model_cfg = config.get("model", {})
    pretrained = bool(model_cfg.get("pretrained", False))
    weights = models.ResNet18_Weights.DEFAULT if pretrained else None
    model = models.resnet18(weights=weights)
    num_classes = int(model_cfg.get("num_classes", 10))
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model

