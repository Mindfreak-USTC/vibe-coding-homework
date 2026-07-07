# CIFAR-10 ResNet-18 图像分类训练系统

这是一个基于 vibe coding 完成的 PyTorch 深度学习工程，用于在 CIFAR-10 数据集上训练 ResNet-18，并完成训练、验证、测试、日志记录、模型保存、混淆矩阵和实验报告。

## 功能

- 自动下载或读取 CIFAR-10 数据集。
- 构建 TorchVision ResNet-18，并将分类头改为 10 类。
- 支持 CPU，检测到 GPU 时自动使用 GPU。
- 支持训练集、验证集、测试集流程。
- 每个 epoch 输出训练 loss/accuracy 和验证 loss/accuracy。
- 保存 `best_model.pth`、`last_checkpoint.pth` 和 `final_model.pth`。
- 使用 TensorBoard 记录训练曲线。
- 测试阶段输出整体准确率、每类准确率、混淆矩阵和 JSON 指标。
- 自动生成 Markdown 实验报告。
- 使用配置文件管理参数，并支持常用命令行覆盖。

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

CPU 版 PyTorch 安装可能需要按本机环境选择官方命令。如果上面的安装较慢，可以参考 PyTorch 官网生成的 CPU 安装命令。

## 训练

完整训练：

```powershell
python src/train.py --config configs/default.yaml
```

CPU 快速调试：

```powershell
python src/train.py --config configs/default.yaml --quick-dev-run
```

离线工程链路验收（不下载 CIFAR-10，使用 TorchVision FakeData 验证训练、验证、checkpoint、日志、测试和报告流程）：

```powershell
python src/train.py --config configs/default.yaml --offline-smoke
python src/test.py --config configs/default.yaml --checkpoint checkpoints/best_model.pth --offline-smoke
```

覆盖常用参数：

```powershell
python src/train.py --config configs/default.yaml --epochs 2 --batch-size 64 --learning-rate 0.001
```

## 测试

```powershell
python src/test.py --config configs/default.yaml --checkpoint checkpoints/best_model.pth
```

输出：

- `outputs/test_metrics.json`
- `outputs/confusion_matrix.png`
- `outputs/report.md`

## TensorBoard

```powershell
tensorboard --logdir logs
```

然后在浏览器中打开 TensorBoard 输出的本地地址。

## 轻量验证

当前仓库提供不依赖 PyTorch 的配置和报告测试：

```powershell
python -m unittest discover -s tests -v
python -m compileall src tests
```

完整 CIFAR-10 训练和测试需要先安装 `torch`、`torchvision`、`tensorboard` 和 `matplotlib`。如果外部 CIFAR-10 下载较慢，可先运行 `--offline-smoke` 证明工程链路可用。

## 项目结构

```text
cifar10-resnet18-vibecoding/
├── README.md
├── requirements.txt
├── configs/
│   └── default.yaml
├── data/
│   └── README.md
├── checkpoints/
│   └── README.md
├── logs/
│   └── README.md
├── outputs/
│   └── report.md
├── src/
│   ├── dataset.py
│   ├── evaluate.py
│   ├── logger.py
│   ├── model.py
│   ├── reports.py
│   ├── test.py
│   ├── train.py
│   ├── utils.py
│   └── visualization.py
├── scripts/
└── docs/
    └── vibe_coding_process.md
```

## Git 注意事项

- 不提交 `data/` 中的数据集文件。
- 不提交 `.pth`、`.pt` 模型权重。
- 不提交 TensorBoard 事件文件。
- 保留 README、配置、源码、测试和实验报告。
