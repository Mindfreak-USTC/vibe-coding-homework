# Vibe Coding 工程项目管理报告

## 1. 项目目标

本次作业包含两个独立编程任务：

1. 基于 CIFAR-10 的 ResNet-18 图像分类训练系统。
2. 图像质量检测与自动报告系统。

本项目不是把两个脚本一次性生成出来，而是按工程项目管理方式完成：先做需求对齐，再规划大纲，再分步执行，最后回顾需求和验证结果。整个过程通过自然语言驱动大模型生成、修改、解释和完善代码，符合 vibe coding 的核心要求。

## 2. 需求对齐

需求来源是工作区中的两个 PDF：

- `Vibe Coding CIFAR-10 Image Classification.pdf`
- `图像质量检测与自动报告系统.pdf`

需求提取后写入：

- `findings.md`
- `task_plan.md`
- `SUBMISSION_CHECKLIST.md`

### 2.1 CIFAR-10 任务需求映射

| PDF 要求 | 当前实现证据 |
|---|---|
| 自动下载或读取 CIFAR-10 | `scripts/prepare_gitcode_cifar.ps1` 使用老师给的 GitCode 数据仓库准备数据；TorchVision 验证 50,000 张训练图像 |
| ResNet-18 模型 | `cifar10-resnet18-vibecoding/src/model.py` |
| 训练流程 | `cifar10-resnet18-vibecoding/src/train.py` |
| 验证流程 | `cifar10-resnet18-vibecoding/src/evaluate.py` |
| 测试流程 | `cifar10-resnet18-vibecoding/src/test.py` |
| TensorBoard 日志 | `cifar10-resnet18-vibecoding/src/logger.py` 和 `logs/README.md` |
| 保存模型权重 | `checkpoints/README.md`；本地验证生成 `.pth`，但按要求不提交大文件 |
| 测试准确率和每类准确率 | `cifar10-resnet18-vibecoding/outputs/test_metrics.json` |
| 训练/验证 loss 和 accuracy 曲线 | `cifar10-resnet18-vibecoding/outputs/training_curves.png` |
| 混淆矩阵 | `cifar10-resnet18-vibecoding/outputs/confusion_matrix.png` |
| 实验报告 | `cifar10-resnet18-vibecoding/outputs/report.md` |
| vibe coding 过程记录 | `cifar10-resnet18-vibecoding/docs/vibe_coding_process.md` |
| README 和配置文件 | `README.md`、`configs/default.yaml` |
| Git 管理 | 本地 Git 仓库包含 9 次以上有意义提交 |

### 2.2 图像质量任务需求映射

| PDF 要求 | 当前实现证据 |
|---|---|
| 读取 jpg/png/bmp | `image-quality-report-vibecoding/src/image_quality/analyzer.py` |
| 跳过非图像文件 | 单元测试 `test_folder_analysis_handles_chinese_names_non_images_and_corrupt_files` |
| 损坏图像错误提示 | 同上，示例 `sample_images/corrupt.png` |
| 亮度、对比度、清晰度、噪声、分辨率 | `src/image_quality/metrics.py` |
| 判断过暗、过曝、模糊、低对比度、高噪声、低分辨率 | `classify_issues()` |
| CSV 汇总 | `outputs/quality_results.csv` |
| 至少两类统计图 | `outputs/issue_counts.png`、`outputs/brightness_distribution.png`、`outputs/sharpness_distribution.png` |
| Markdown 检测报告 | `outputs/report.md` |
| 命令行运行 | `src/image_quality/cli.py` |
| README | `image-quality-report-vibecoding/README.md` |
| 示例输入图片 | `image-quality-report-vibecoding/sample_images/` |
| vibe coding 过程记录 | `image-quality-report-vibecoding/docs/vibe_coding_process.md` |

## 3. 规划大纲

项目被拆成两个独立工程目录：

```text
cifar10-resnet18-vibecoding/
image-quality-report-vibecoding/
```

根目录保留项目管理文件：

```text
task_plan.md
findings.md
progress.md
SUBMISSION_CHECKLIST.md
REMOTE_PUSH_INSTRUCTIONS.md
```

这种结构避免两个任务的依赖和输出互相污染，也能让每个项目独立运行、测试和提交。

## 4. 分步执行策略

执行过程采用以下顺序：

1. PDF 解析：先提取题目要求，不直接写代码。
2. 项目规划：为两个任务分别设计目录、依赖、命令和验收方法。
3. 测试先行：先写行为测试，让测试暴露缺失模块。
4. 代码生成：通过自然语言要求 AI 生成实现。
5. 错误反馈：把报错原文反馈给 AI，再由 AI 修改。
6. 验证闭环：每个阶段跑测试、语法检查或 smoke test。
7. 需求回顾：用 `SUBMISSION_CHECKLIST.md` 对照 PDF 验收项逐条检查。

## 5. 关键问题与修正

| 问题 | 原因 | 修正 |
|---|---|---|
| 默认 `python` 不可用 | Windows Store 占位程序 | 使用 Codex bundled Python 或在脚本中允许传入 `-Python` |
| 没有 `pytest` | 当前环境未安装 | 改为标准库 `unittest` |
| 测试临时目录权限问题 | Windows 沙箱限制系统 Temp | 改用项目内 `test_runs/` |
| CIFAR 官方下载超时 | 网络不稳定 | 使用老师给的 GitCode 仓库浅克隆 |
| GitCode 文件名是 `.tar.gz` 但内容是 RAR | GitCode 仓库 README 说明需改成 rar 解压 | 使用 Windows `tar.exe` 解压并写入 `prepare_gitcode_cifar.ps1` |
| CIFAR 测试脚本多进程权限错误 | `num_workers=2` 在当前沙箱无法创建 Pipe | 给测试脚本增加 `--quick-dev-run`，强制 `num_workers=0` |
| Matplotlib 写 AppData 缓存失败 | 默认缓存目录不可写 | 设置项目内 `MPLCONFIGDIR` |

## 6. 验证证据

### 6.1 图像质量项目

```powershell
python -m unittest discover -s tests -v
python -m compileall src tests
$env:PYTHONPATH="src"
python -m image_quality.cli --input sample_images --output outputs
```

结果：

- 4 个单元测试通过。
- CLI 成功处理 9 个示例文件。
- 输出 CSV、Markdown 报告和 3 张图表。

### 6.2 CIFAR-10 项目

```powershell
powershell -ExecutionPolicy Bypass -File scripts/prepare_gitcode_cifar.ps1 -Python <python-path>
python src/train.py --config configs/default.yaml --quick-dev-run
python src/test.py --config configs/default.yaml --checkpoint checkpoints/best_model.pth --quick-dev-run
python -m unittest discover -s tests -v
python -m compileall src tests
```

结果：

- CIFAR-10 训练集读取数量：50,000。
- quick-dev 训练通过：最终验证准确率 0.1471。
- quick-dev 测试通过：测试准确率 0.1992，样本数 256。
- 生成训练曲线：`outputs/training_curves.png`。
- 4 个轻量测试通过。
- 语法检查通过。

## 7. 需求表达如何影响代码质量

本项目体现了一个明确结论：需求越具体，AI 生成代码越接近可交付工程。

如果只说“做一个 CIFAR-10 分类程序”，AI 可能只生成一个单文件训练脚本。PDF 需求中明确要求了配置文件、日志、checkpoint、测试、混淆矩阵、README、Git 管理和过程记录，因此项目最终形成了可运行、可复现、可验证的工程结构。

图像质量任务也一样。如果只说“检测图片质量”，代码可能只输出一个分数；明确要求亮度、对比度、清晰度、噪声、分辨率、CSV、图表、报告、中文文件名和损坏文件处理后，系统才具备完整验收能力。

所以 vibe coding 的关键不是让 AI 一次性“写完代码”，而是持续提供清晰需求、运行反馈、错误证据和验收标准，让 AI 沿着工程目标迭代。

## 8. 最终提交说明

当前本地仓库已经准备好提交：

- 源码和文档：工作区当前 `master`
- 源码压缩包：`dist/vibe-coding-homework-source.zip`
- Git 历史包：`dist/vibe-coding-homework-history.bundle`

唯一外部缺口是远程仓库 URL。拿到远程 URL 后执行：

```powershell
git remote add origin <你的远程仓库URL>
git push -u origin master
```
