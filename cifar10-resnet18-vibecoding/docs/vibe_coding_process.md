# Vibe Coding 过程记录

## 第 1 轮：初始需求

我的提示词：

```text
请读取老师提供的 CIFAR-10 PDF 作业要求，生成一个规范的 PyTorch 项目，在 CIFAR-10 上训练 ResNet-18，包含训练、验证、测试、日志、checkpoint、混淆矩阵、实验报告和 Git 管理。
```

AI 输出摘要：

- 确认任务目标是 CIFAR-10 ResNet-18 图像分类训练系统。
- 提取必须交付：README、requirements、配置、训练脚本、测试脚本、TensorBoard 日志、模型保存、测试结果、混淆矩阵、实验报告、vibe coding 过程记录。
- 决定使用 TensorBoard，避免 W&B API Key 写入代码。

## 第 2 轮：工程规划

我的提示词：

```text
请把作业作为工程项目管理，先写任务计划、需求发现、进度记录，再拆成可执行的实现步骤。
```

AI 输出摘要：

- 在根目录创建 `task_plan.md`、`findings.md`、`progress.md`。
- 将 CIFAR-10 和图像质量检测拆成两个独立项目。
- 为 CIFAR 项目设计 `configs/`、`src/`、`tests/`、`outputs/`、`docs/` 结构。

## 第 3 轮：测试先行

我的提示词：

```text
请先生成不依赖 Torch 的轻量测试，验证配置解析和实验报告生成，保证当前环境也能执行基础验证。
```

第一次运行遇到的问题：

```text
No module named pytest
```

我的反馈提示词：

```text
当前环境没有 pytest，请改为标准库 unittest，减少额外依赖。
```

修改结果：

- 测试改为 `unittest`。
- 红灯变为 `No module named utils` 和 `No module named reports`，说明测试已指向待实现模块。

## 第 4 轮：实现配置与报告

我的提示词：

```text
请实现配置读取和实验报告生成。配置优先支持 PyYAML，若环境没有 PyYAML，对简单 YAML 提供 fallback 解析，方便轻量测试。
```

AI 修改摘要：

- 生成 `src/utils.py`。
- 生成 `src/reports.py`。

验证结果：

```text
python -m unittest discover -s tests -v
Ran 2 tests
OK
```

## 第 5 轮：实现训练/验证/测试主流程

我的提示词：

```text
请补齐 PyTorch CIFAR-10 工程：数据加载、ResNet-18、训练循环、验证、测试、TensorBoard、checkpoint、混淆矩阵和 CLI 命令。
```

AI 修改摘要：

- 生成 `dataset.py`、`model.py`、`evaluate.py`、`logger.py`、`visualization.py`、`train.py`、`test.py`。
- 训练脚本保存最佳、最后和最终模型。
- 测试脚本输出测试准确率、每类准确率、混淆矩阵和报告。

当前验证结果：

```text
python -m unittest discover -s tests -v
Ran 2 tests
OK

python -m compileall src tests
语法检查通过
```

## 第 6 轮：环境限制与最终验收

当前环境限制：

- 初始环境未安装 `torch`、`torchvision`、`tensorboard` 和 `matplotlib`，已通过 `pip install -r requirements.txt` 安装。
- 真实 CIFAR-10 下载在当前网络环境中超时，因此新增 `--offline-smoke` 模式，使用 TorchVision FakeData 验证训练、checkpoint、日志、测试和报告链路。

完整验收命令：

```powershell
pip install -r requirements.txt
python src/train.py --config configs/default.yaml --quick-dev-run
python src/test.py --config configs/default.yaml --checkpoint checkpoints/best_model.pth
tensorboard --logdir logs
```

离线 smoke 验收命令：

```powershell
python src/train.py --config configs/default.yaml --offline-smoke
python src/test.py --config configs/default.yaml --checkpoint checkpoints/best_model.pth --offline-smoke
```

离线 smoke 实际结果：

```text
Epoch 1/1 | train loss 2.5188 acc 0.1250 | val loss 2.3110 acc 0.1562
Test accuracy: 0.1562
```

输出文件：

- `outputs/history.json`
- `outputs/test_metrics.json`
- `outputs/confusion_matrix.png`
- `outputs/report.md`
- `logs/events.out.tfevents.*`
- `checkpoints/best_model.pth`

总结：

- 需求越具体，AI 生成的项目结构越完整。
- 明确要求“CPU 可运行、日志、checkpoint、测试、报告、错误处理”后，代码从单脚本变成可验收工程。
- 通过红灯、修复、绿灯记录，可以证明不是只复制代码，而是在用自然语言驱动 AI 迭代完成工程。
