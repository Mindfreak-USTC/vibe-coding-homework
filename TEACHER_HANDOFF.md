# 作业提交入口

这份文件是给老师/助教快速检查用的入口说明。两个 PDF 作业已经按工程项目方式拆分、实现、测试和记录，核心证据都在下面列出。

## 1. 先看哪些文件

- `PROJECT_MANAGEMENT_REPORT.md`：项目管理总结，说明需求对齐、规划、分步执行、问题修正和验证证据。
- `ACCEPTANCE_AUDIT.md`：按两个 PDF 要求逐项映射当前证据，并标明唯一外部阻塞项。
- `SUBMISSION_CHECKLIST.md`：逐项对照两个 PDF 的交付清单。
- `findings.md`：从两个 PDF 中提取出的需求。
- `task_plan.md`：执行计划和任务拆分。
- `progress.md`：执行过程记录。
- `REMOTE_PUSH_INSTRUCTIONS.md`：远程仓库推送说明。

## 2. 两个任务目录

- `cifar10-resnet18-vibecoding/`：CIFAR-10 ResNet-18 图像分类训练系统。
- `image-quality-report-vibecoding/`：图像质量检测与自动报告系统。

## 3. 任务 1 关键结果

目录：`cifar10-resnet18-vibecoding/`

- 训练配置：`configs/default.yaml`
- 训练入口：`src/train.py`
- 测试入口：`src/test.py`
- 模型定义：`src/model.py`
- GitCode 数据准备脚本：`scripts/prepare_gitcode_cifar.ps1`
- 测试指标：`outputs/test_metrics.json`
- 实验报告：`outputs/report.md`
- 训练/验证曲线：`outputs/training_curves.png`
- 混淆矩阵：`outputs/confusion_matrix.png`
- vibe coding 过程记录：`docs/vibe_coding_process.md`

本地已验证老师给出的 GitCode CIFAR-10 数据源可读取，TorchVision 可加载 50,000 张训练图像。quick-dev 训练和测试均已跑通。

常用验收命令：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/prepare_gitcode_cifar.ps1 -Python <python-path>
python src/train.py --config configs/default.yaml --quick-dev-run
python src/test.py --config configs/default.yaml --checkpoint checkpoints/best_model.pth --quick-dev-run
python -m unittest discover -s tests -v
python -m compileall src tests
```

## 4. 任务 2 关键结果

目录：`image-quality-report-vibecoding/`

- 命令行入口：`src/image_quality/cli.py`
- 图像分析：`src/image_quality/analyzer.py`
- 质量指标：`src/image_quality/metrics.py`
- Markdown 报告生成：`src/image_quality/report.py`
- 示例图片：`sample_images/`
- CSV 汇总：`outputs/quality_results.csv`
- Markdown 报告：`outputs/report.md`
- 统计图：`outputs/issue_counts.png`
- 统计图：`outputs/brightness_distribution.png`
- 统计图：`outputs/sharpness_distribution.png`
- vibe coding 过程记录：`docs/vibe_coding_process.md`

常用验收命令：

```powershell
$env:PYTHONPATH="src"
python -m image_quality.cli --input sample_images --output outputs
python -m unittest discover -s tests -v
python -m compileall src tests
```

## 5. 打包交付物

`dist/` 目录中保留了可提交文件：

- `vibe-coding-homework-source.zip`：源码包，不包含 `.git`、CIFAR 数据集、checkpoint、TensorBoard 日志和临时缓存。
- `vibe-coding-homework-history.bundle`：Git 历史包，可还原完整本地提交历史。
- `SHA256SUMS.txt`：源码包和 Git 历史包的 SHA256 校验值。

## 6. 远程仓库说明

本地 Git 仓库已完成提交历史，但当前 `git remote -v` 为空。拿到 GitHub、GitCode 或 Gitee 的空仓库 URL 后，在根目录执行：

```powershell
git remote add origin <你的远程仓库URL>
git push -u origin master
```

如果暂时无法提供远程仓库，`dist/` 中的源码包和 Git bundle 可以作为离线提交材料。
