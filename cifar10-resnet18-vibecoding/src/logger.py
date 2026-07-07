from __future__ import annotations

from pathlib import Path
from typing import Any

from utils import ensure_dir, project_path


class NullWriter:
    def add_scalar(self, *_args, **_kwargs) -> None:
        return None

    def add_text(self, *_args, **_kwargs) -> None:
        return None

    def close(self) -> None:
        return None


def create_writer(config: dict[str, Any]):
    logging_cfg = config.get("logging", {})
    backend = logging_cfg.get("backend", "tensorboard")
    if backend != "tensorboard":
        print(f"Unsupported logging backend `{backend}`. Falling back to no-op logger.")
        return NullWriter()
    log_dir = ensure_dir(project_path(logging_cfg.get("log_dir", "./logs")))
    try:
        from torch.utils.tensorboard import SummaryWriter
    except ModuleNotFoundError:
        print("TensorBoard is not installed. Install dependencies to enable curve logging.")
        return NullWriter()
    return SummaryWriter(log_dir=str(Path(log_dir)))

