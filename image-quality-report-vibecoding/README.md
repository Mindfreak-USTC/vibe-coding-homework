# 图像质量检测与自动报告系统

这是一个基于 vibe coding 完成的 CPU 图像质量检测项目。程序读取指定文件夹中的 `jpg`、`png`、`bmp` 图片，自动计算亮度、对比度、清晰度、噪声和分辨率，并输出 CSV、统计图和 Markdown 报告。

## 功能

- 读取指定文件夹中的图片文件。
- 自动跳过非图片文件。
- 对损坏图片记录错误信息。
- 支持中文文件名。
- 计算亮度、对比度、清晰度、噪声、分辨率。
- 判断过暗、过曝、模糊、对比度不足、噪声较大、分辨率过低。
- 生成 `outputs/quality_results.csv`。
- 生成问题数量统计图、亮度分布图、清晰度分布图。
- 生成 `outputs/report.md` 自动检测报告。

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

如果已经在 Codex 自带 Python 环境中运行，可以直接使用该 Python 执行命令。

## 运行

```powershell
python -m image_quality.cli --input sample_images --output outputs
```

如果没有安装成包，可以临时设置 `PYTHONPATH`：

```powershell
$env:PYTHONPATH="src"
python -m image_quality.cli --input sample_images --output outputs
```

## 输出文件

- `outputs/quality_results.csv`: 每张图片的检测结果。
- `outputs/report.md`: 自动生成的 Markdown 报告。
- `outputs/issue_counts.png`: 问题类型数量统计图。
- `outputs/brightness_distribution.png`: 亮度分布图。
- `outputs/sharpness_distribution.png`: 清晰度分布图。

## 测试

```powershell
python -m unittest discover -s tests -v
```

## 项目结构

```text
image-quality-report-vibecoding/
├── README.md
├── requirements.txt
├── sample_images/
├── outputs/
├── src/
│   └── image_quality/
│       ├── analyzer.py
│       ├── charts.py
│       ├── cli.py
│       ├── metrics.py
│       └── report.py
├── tests/
└── docs/
    └── vibe_coding_process.md
```

## 阈值说明

默认阈值面向课堂作业和快速巡检，不代表所有业务场景的最佳阈值。实际使用时可以通过命令行参数调整，例如：

```powershell
python -m image_quality.cli --input sample_images --output outputs --dark-threshold 40 --blur-threshold 100
```

