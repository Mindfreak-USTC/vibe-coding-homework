# 验收审计表

审计时间：2026-07-08

本表按两个 PDF 题目和用户补充要求逐项核对当前工作区证据。状态含义：

- 已满足：当前文件、输出或命令结果可以直接证明。
- 外部阻塞：本地已经准备好，但需要用户提供外部资源或授权。

## 1. 总体要求

| 要求 | 当前证据 | 状态 |
|---|---|---|
| 完成两个 PDF 作业 | `cifar10-resnet18-vibecoding/`、`image-quality-report-vibecoding/` | 已满足 |
| 以工程项目方式管理任务 | `findings.md`、`task_plan.md`、`progress.md`、`PROJECT_MANAGEMENT_REPORT.md` | 已满足 |
| 做需求对齐、规划大纲、分步执行、需求回顾 | `PROJECT_MANAGEMENT_REPORT.md` 第 2-6 节，`SUBMISSION_CHECKLIST.md` | 已满足 |
| 体现 vibe coding：用自然语言描述需求、反馈错误、迭代完善 | 两个项目的 `docs/vibe_coding_process.md` | 已满足 |
| 提供仓库首页 README | `README.md` | 已满足 |
| 提供老师/助教检查入口 | `TEACHER_HANDOFF.md` | 已满足 |
| 提供一键本地验收脚本 | `scripts/verify_submission.ps1` | 已满足 |
| 提供可离线提交的打包产物 | `dist/vibe-coding-homework-source.zip`、`dist/vibe-coding-homework-history.bundle`、`dist/SHA256SUMS.txt` | 已满足 |

## 2. CIFAR-10 ResNet-18 任务

目录：`cifar10-resnet18-vibecoding/`

| PDF 要求 | 当前证据 | 状态 |
|---|---|---|
| 自动下载或读取 CIFAR-10 数据集 | `scripts/prepare_gitcode_cifar.ps1`；已用老师提供的 GitCode 数据源验证 TorchVision 可读取 50,000 张训练图像 | 已满足 |
| 构建 ResNet-18 图像分类模型 | `src/model.py` | 已满足 |
| 修改分类头适配 CIFAR-10 10 类 | `src/model.py` | 已满足 |
| 支持从头训练 | `src/model.py`、`src/train.py`、`configs/default.yaml` | 已满足 |
| 训练集、验证集、测试集划分 | `src/dataset.py` | 已满足 |
| 训练集数据增强，验证/测试标准化 | `src/dataset.py`、`configs/default.yaml` | 已满足 |
| 完整训练流程 | `src/train.py` | 已满足 |
| 每个 epoch 输出训练 loss 和 accuracy | `src/train.py`、`outputs/history.json` | 已满足 |
| 每个 epoch 后进行验证 | `src/train.py`、`src/evaluate.py` | 已满足 |
| 输出验证 loss 和 accuracy | `src/train.py`、`outputs/history.json` | 已满足 |
| 保存验证表现最好的模型 | `src/train.py`、`checkpoints/README.md` | 已满足 |
| 训练完成后保存最终模型 | `src/train.py`、`checkpoints/README.md` | 已满足 |
| 独立测试流程 | `src/test.py` | 已满足 |
| 输出测试集整体准确率 | `outputs/test_metrics.json`、`outputs/report.md` | 已满足 |
| 输出每一类测试准确率 | `outputs/test_metrics.json`、`outputs/report.md` | 已满足 |
| 输出并保存混淆矩阵 | `outputs/confusion_matrix.png`、`src/visualization.py` | 已满足 |
| 保存测试结果文件 | `outputs/test_metrics.json` | 已满足 |
| 使用 TensorBoard 或 W&B 记录训练曲线 | `src/logger.py`、`logs/README.md`，本项目选择 TensorBoard | 已满足 |
| README 中提供 TensorBoard 启动说明 | `README.md` 的 TensorBoard 小节 | 已满足 |
| 配置文件管理主要参数 | `configs/default.yaml` | 已满足 |
| 训练/验证 loss 和 accuracy 曲线 | `outputs/training_curves.png`、`outputs/report.md` | 已满足 |
| 实验报告包含指标、类别准确率、混淆分析和改进方向 | `outputs/report.md` | 已满足 |
| 记录完整 vibe coding 开发过程 | `docs/vibe_coding_process.md` | 已满足 |
| 提供 README、requirements、脚本和清晰项目结构 | `README.md`、`requirements.txt`、`scripts/`、`src/` | 已满足 |
| 使用 Git 管理，有多次有意义提交 | 本地 Git 历史已包含多次有意义提交，精确数量以 `git rev-list --count HEAD` 为准 | 已满足 |
| 不提交数据集、虚拟环境、大模型权重文件 | `.gitignore`、`data/README.md`、`checkpoints/README.md`、`logs/README.md` | 已满足 |
| 最终推送到远程 Git 仓库 | `REMOTE_PUSH_INSTRUCTIONS.md`；当前 `git remote -v` 为空，需要远程仓库 URL | 外部阻塞 |

### CIFAR-10 当前可复验命令

```powershell
powershell -ExecutionPolicy Bypass -File scripts/prepare_gitcode_cifar.ps1 -Python <python-path>
python src/train.py --config configs/default.yaml --quick-dev-run
python src/test.py --config configs/default.yaml --checkpoint checkpoints/best_model.pth --quick-dev-run
python -m unittest discover -s tests -v
python -m compileall src tests
```

## 3. 图像质量检测与自动报告任务

目录：`image-quality-report-vibecoding/`

| PDF 要求 | 当前证据 | 状态 |
|---|---|---|
| 读取指定文件夹中的图像文件 | `src/image_quality/analyzer.py` | 已满足 |
| 支持 jpg、png、bmp 格式 | `src/image_quality/analyzer.py` 中的 `IMAGE_EXTENSIONS` | 已满足 |
| 自动跳过非图像文件 | `src/image_quality/analyzer.py`、`tests/test_quality_metrics.py` | 已满足 |
| 对损坏图像给出错误提示 | `outputs/quality_results.csv` 中 `corrupt.png` 行，`tests/test_quality_metrics.py` | 已满足 |
| 计算亮度 | `src/image_quality/metrics.py`、`outputs/quality_results.csv` | 已满足 |
| 计算对比度 | `src/image_quality/metrics.py`、`outputs/quality_results.csv` | 已满足 |
| 计算清晰度或模糊度 | `src/image_quality/metrics.py`、`outputs/quality_results.csv` | 已满足 |
| 计算噪声水平 | `src/image_quality/metrics.py`、`outputs/quality_results.csv` | 已满足 |
| 计算分辨率 | `src/image_quality/metrics.py`、`outputs/quality_results.csv` | 已满足 |
| 判断过暗、过曝、模糊、对比度不足、噪声较大、分辨率过低 | `src/image_quality/analyzer.py` 的 `classify_issues()` | 已满足 |
| 输出每张图像检测结果 CSV | `outputs/quality_results.csv` | 已满足 |
| 生成至少两类统计图 | `outputs/issue_counts.png`、`outputs/brightness_distribution.png`、`outputs/sharpness_distribution.png` | 已满足 |
| 自动生成 Markdown 或 HTML 报告 | `outputs/report.md`、`src/image_quality/report.py` | 已满足 |
| 支持命令行运行 | `src/image_quality/cli.py` | 已满足 |
| 提供 README，说明安装、运行、输入输出和示例 | `README.md` | 已满足 |
| 提供示例输入图片 | `sample_images/` | 已满足 |
| 能处理中文文件名 | `sample_images/中文文件名.png`、`outputs/quality_results.csv`、`tests/test_quality_metrics.py` | 已满足 |
| 记录 vibe coding 开发过程 | `docs/vibe_coding_process.md` | 已满足 |

### 图像质量任务当前可复验命令

```powershell
$env:PYTHONPATH="src"
python -m image_quality.cli --input sample_images --output outputs
python -m unittest discover -s tests -v
python -m compileall src tests
```

## 4. 当前未闭合项

| 项目 | 原因 | 后续动作 |
|---|---|---|
| 远程 Git 仓库链接 | 当前本地没有 `origin`，且没有可用的已登录 GitHub/GitCode/Gitee CLI | 用户提供空仓库 URL 后执行 `git remote add origin <url>` 和 `git push -u origin master` |

除远程推送外，本地源码、文档、输出、测试和离线交付包已具备当前可验证证据。

## 5. 一键验收命令

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify_submission.ps1 -Python <python-path>
```

该脚本默认把远程仓库缺失视为警告。若要让远程仓库缺失导致失败，使用：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify_submission.ps1 -Python <python-path> -RequireRemote
```
