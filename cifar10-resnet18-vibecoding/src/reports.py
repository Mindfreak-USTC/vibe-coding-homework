from __future__ import annotations

import os
from pathlib import Path

from utils import load_json


def _last_epoch(history: dict) -> dict:
    epochs = history.get("epochs", [])
    if not epochs:
        return {}
    return epochs[-1]


def _trend_analysis(history: dict) -> str:
    epochs = history.get("epochs", [])
    if len(epochs) < 2:
        return "当前记录不足两个 epoch，只能确认流程是否跑通，不能可靠判断收敛趋势。"
    first, last = epochs[0], epochs[-1]
    if last.get("train_loss", 0) < first.get("train_loss", 0):
        return "训练 loss 下降，模型具备正常收敛迹象。"
    return "训练 loss 未明显下降，建议增加 epoch、检查学习率或数据预处理。"


def _overfit_analysis(history: dict) -> str:
    last = _last_epoch(history)
    train_acc = float(last.get("train_accuracy", 0.0) or 0.0)
    val_acc = float(last.get("val_accuracy", 0.0) or 0.0)
    gap = train_acc - val_acc
    if gap > 0.15:
        return f"是否出现明显过拟合：可能存在。最终 train/val accuracy 差值为 {gap:.4f}。"
    return f"是否出现明显过拟合：未见明显迹象。最终 train/val accuracy 差值为 {gap:.4f}。"


def _save_training_curves(history: dict, output_path: Path) -> bool:
    epochs = history.get("epochs", [])
    if not epochs:
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cache_dir = output_path.parent / ".matplotlib"
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache_dir))

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x_values = [int(row.get("epoch", index + 1)) for index, row in enumerate(epochs)]
    train_loss = [float(row.get("train_loss", 0.0) or 0.0) for row in epochs]
    val_loss = [float(row.get("val_loss", 0.0) or 0.0) for row in epochs]
    train_acc = [float(row.get("train_accuracy", 0.0) or 0.0) for row in epochs]
    val_acc = [float(row.get("val_accuracy", 0.0) or 0.0) for row in epochs]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].plot(x_values, train_loss, marker="o", label="train loss")
    axes[0].plot(x_values, val_loss, marker="o", label="validation loss")
    axes[0].set_title("Loss curves")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].plot(x_values, train_acc, marker="o", label="train accuracy")
    axes[1].plot(x_values, val_acc, marker="o", label="validation accuracy")
    axes[1].set_title("Accuracy curves")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Accuracy")
    axes[1].set_ylim(0.0, 1.0)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return True


def generate_experiment_report(
    history_path: str | Path,
    metrics_path: str | Path,
    report_path: str | Path,
) -> None:
    history = load_json(history_path)
    metrics = load_json(metrics_path)
    last = _last_epoch(history)
    per_class = metrics.get("per_class_accuracy", {})
    dataset_name = metrics.get("dataset_name") or history.get("dataset_name") or "CIFAR-10"
    report_path = Path(report_path)
    curves_path = report_path.parent / "training_curves.png"
    has_curves = _save_training_curves(history, curves_path)

    lines = [
        "# CIFAR-10 ResNet-18 实验报告",
        "",
        "## 实验配置摘要",
        "- 模型: ResNet-18",
        f"- 数据集: {dataset_name}",
        "- 日志: TensorBoard",
        "",
        "## 训练与验证结果",
        f"- 最终训练 loss: {float(last.get('train_loss', 0.0) or 0.0):.4f}",
        f"- 最终训练 accuracy: {float(last.get('train_accuracy', 0.0) or 0.0):.4f}",
        f"- 最终验证 loss: {float(last.get('val_loss', 0.0) or 0.0):.4f}",
        f"- 最终验证 accuracy: {float(last.get('val_accuracy', 0.0) or 0.0):.4f}",
        "",
        "## 训练曲线",
    ]
    if has_curves:
        lines.append(f"![training curves]({curves_path.name})")
    else:
        lines.append("当前没有 epoch 历史记录，无法生成训练曲线。")
    lines.extend(
        [
            "",
        "## 测试结果",
        f"- 测试集整体准确率: {float(metrics.get('test_accuracy', 0.0) or 0.0):.4f}",
        f"- 混淆矩阵: {metrics.get('confusion_matrix_path', 'outputs/confusion_matrix.png')}",
        "",
        "## 每类准确率",
        ]
    )
    if "FakeData" in str(dataset_name):
        lines.extend(
            [
                "",
                "> 注意：本报告来自离线 smoke 模式，用于验证训练、测试、checkpoint、日志和报告链路；真实 CIFAR-10 指标需在数据集下载完成后重新运行完整训练。",
            ]
        )
    for class_name, accuracy in per_class.items():
        lines.append(f"- {class_name}: {float(accuracy):.4f}")

    lines.extend(
        [
            "",
            "## 实验分析",
            f"- 模型是否正常收敛: {_trend_analysis(history)}",
            f"- {_overfit_analysis(history)}",
            "- 哪些类别容易被混淆: 需要结合 `outputs/confusion_matrix.png` 观察非对角线高值。",
            "- 后续改进方向: 增加训练轮数、加入学习率调度、尝试更强数据增强、比较 MobileNetV2 或 SimpleCNN。",
        ]
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
