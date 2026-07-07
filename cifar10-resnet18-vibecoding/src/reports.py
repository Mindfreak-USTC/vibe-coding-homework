from __future__ import annotations

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
        "## 测试结果",
        f"- 测试集整体准确率: {float(metrics.get('test_accuracy', 0.0) or 0.0):.4f}",
        f"- 混淆矩阵: {metrics.get('confusion_matrix_path', 'outputs/confusion_matrix.png')}",
        "",
        "## 每类准确率",
    ]
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

    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
