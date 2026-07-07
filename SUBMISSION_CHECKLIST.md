# 作业提交清单

## 总体

- [x] 两个 PDF 已解析并形成工程计划。
- [x] 根目录包含仓库首页说明：`README.md`。
- [x] 根目录包含 `task_plan.md`、`findings.md`、`progress.md`。
- [x] 根目录包含工程项目管理总结：`PROJECT_MANAGEMENT_REPORT.md`。
- [x] 根目录包含验收审计表：`ACCEPTANCE_AUDIT.md`。
- [x] 根目录包含一键本地验收脚本：`scripts/verify_submission.ps1`。
- [x] 两个任务拆分为独立项目目录。
- [x] 每个项目都有 README、requirements、源码、测试和 vibe coding 过程记录。

## 任务 1：CIFAR-10 ResNet-18 图像分类训练系统

目录：`cifar10-resnet18-vibecoding/`

- [x] `README.md`
- [x] `requirements.txt`
- [x] `.gitignore`
- [x] `configs/default.yaml`
- [x] `src/dataset.py`
- [x] `src/model.py`
- [x] `src/train.py`
- [x] `src/evaluate.py`
- [x] `src/test.py`
- [x] `src/logger.py`
- [x] `src/reports.py`
- [x] `src/visualization.py`
- [x] `scripts/train.sh`
- [x] `scripts/test.sh`
- [x] `scripts/run_tensorboard.sh`
- [x] `docs/vibe_coding_process.md`
- [x] 轻量测试通过：`python -m unittest discover -s tests -v`
- [x] 语法检查通过：`python -m compileall src tests`
- [x] 依赖安装：PyTorch/TorchVision/TensorBoard/Matplotlib 已安装到 Codex bundled Python。
- [x] 使用老师提供的 GitCode 数据源准备 CIFAR-10：浅克隆数据仓库后用 `tar.exe` 解压，TorchVision 可读取 50,000 张训练图像。
- [x] 真实 CIFAR-10 quick-dev 训练：`python src/train.py --config configs/default.yaml --quick-dev-run` 已通过。
- [x] 真实 CIFAR-10 quick-dev 测试：`python src/test.py --config configs/default.yaml --checkpoint checkpoints/best_model.pth --quick-dev-run` 已通过，测试准确率 0.1992，样本数 256。
- [x] 离线 smoke 训练/测试：`--offline-smoke` 已通过，验证训练、验证、checkpoint、TensorBoard、测试、混淆矩阵和报告链路。
- [ ] 远程 Git 仓库链接：需要用户提供或创建远程仓库后推送。

完整验收命令：

```powershell
pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File scripts/prepare_gitcode_cifar.ps1 -Python <python-path>
python src/train.py --config configs/default.yaml --quick-dev-run
python src/test.py --config configs/default.yaml --checkpoint checkpoints/best_model.pth --quick-dev-run
tensorboard --logdir logs
```

当前环境可用的离线工程链路验收命令：

```powershell
python src/train.py --config configs/default.yaml --offline-smoke
python src/test.py --config configs/default.yaml --checkpoint checkpoints/best_model.pth --offline-smoke
```

离线 smoke 已生成：

- `checkpoints/best_model.pth`（本地验证产物，按 `.gitignore` 不提交）
- `logs/events.out.tfevents.*`（本地验证产物，按 `.gitignore` 不提交）
- `outputs/history.json`
- `outputs/training_curves.png`
- `outputs/test_metrics.json`
- `outputs/confusion_matrix.png`
- `outputs/report.md`

真实 CIFAR quick-dev 已生成：

- `outputs/history.json`
- `outputs/training_curves.png`
- `outputs/test_metrics.json`
- `outputs/confusion_matrix.png`
- `outputs/report.md`

## 任务 2：图像质量检测与自动报告系统

目录：`image-quality-report-vibecoding/`

- [x] `README.md`
- [x] `requirements.txt`
- [x] `.gitignore`
- [x] 示例输入图片：`sample_images/`
- [x] CSV 输出：`outputs/quality_results.csv`
- [x] Markdown 报告：`outputs/report.md`
- [x] 可视化图表：`outputs/issue_counts.png`
- [x] 可视化图表：`outputs/brightness_distribution.png`
- [x] 可视化图表：`outputs/sharpness_distribution.png`
- [x] `docs/vibe_coding_process.md`
- [x] 测试通过：`python -m unittest discover -s tests -v`
- [x] 语法检查通过：`python -m compileall src tests`
- [x] CLI 已在 `sample_images/` 上成功运行。

验收命令：

```powershell
$env:PYTHONPATH="src"
python -m image_quality.cli --input sample_images --output outputs
python -m unittest discover -s tests -v
```
