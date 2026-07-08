# Vibe Coding 过程记录

## 第 1 轮：需求读取与拆分

我的提示词：

```text
请读取老师提供的两个 PDF 作业要求，按工程项目方式拆解需求、规划、执行和验收。全程使用大模型辅助编程，不手写核心代码。
```

AI 输出摘要：

- 确认本任务是图像质量检测与自动报告系统。
- 提取功能要求：读取图片、跳过非图片、处理损坏图片、计算质量指标、输出 CSV、生成统计图和报告。
- 提取约束：CPU 可运行、常见 Python 库、所有输出保存在 outputs 文件夹。

运行结果：

- 使用 PDF 文本提取和页面渲染确认要求。
- 将需求记录到根目录 `findings.md`。

## 第 2 轮：测试先行

我的提示词：

```text
请先为图像质量系统生成行为测试：指标计算、中文文件名、非图片跳过、损坏图片报错、CLI 输出 CSV/报告/图表。先不要实现业务代码。
```

AI 输出摘要：

- 生成 `tests/test_quality_metrics.py`。
- 生成 `tests/test_cli_outputs.py`。

第一次运行遇到的问题：

```text
No module named pytest
PermissionError: 默认系统 Temp 目录不可写
```

我的反馈提示词：

```text
当前环境没有 pytest，且 Windows 沙箱不允许写默认 Temp。请改成标准库 unittest，并把测试临时目录放在项目内。
```

修改结果：

- 测试改为 `unittest`。
- 临时目录改为项目内 `test_runs/`。
- 红灯变为预期的 `No module named image_quality.*`，说明测试已正确指向待实现模块。

## 第 3 轮：实现核心功能

我的提示词：

```text
请根据测试实现图像质量系统，使用 Pillow 和 NumPy，生成 CSV、问题统计图、亮度分布图、清晰度分布图和 Markdown 报告。
```

AI 输出摘要：

- 生成 `metrics.py`：亮度、对比度、清晰度、噪声、分辨率。
- 生成 `analyzer.py`：文件夹遍历、非图片跳过、损坏图片处理、CSV 输出。
- 生成 `charts.py`：使用 Pillow 绘制统计图。
- 生成 `report.py`：自动生成 Markdown 报告。
- 生成 `cli.py`：命令行入口。

验证结果：

```text
python -m unittest discover -s tests -v
Ran 4 tests
OK
```

## 第 4 轮：文档与验收

我的提示词：

```text
请补齐 README、requirements、示例输入图片、示例输出结果和最终验收记录。
```

AI 输出摘要：

- 生成 README 和 requirements。
- 生成示例图片和输出报告。
- 记录测试与运行命令。

最终验收结果：

- 单元测试通过。
- CLI 能生成 CSV、Markdown 报告和三张图表。
- 支持中文文件名、非图片文件和损坏图片处理。

## 第 5 轮：真实图片上传演示

我的追加提示词：

```text
能做个前端吗，可以上传图片然后输出结果
```

AI 输出摘要：

- 新增 `src/image_quality/web_app.py`，使用标准库 HTTP 服务提供本地上传页面。
- 页面支持上传一张或多张 `jpg`、`png`、`bmp` 图片。
- 上传后复用已有 `analyze_folder()` 检测逻辑，展示统计卡片、检测明细表、统计图，并提供 CSV 和 Markdown 报告下载。
- 新增 `tests/test_web_app.py`，覆盖安全文件名、上传表单和结果页下载链接。

验证结果：

```text
python -m unittest discover -s tests -v
Ran 7 tests
OK

python -m compileall src tests
```

课堂演示命令：

```powershell
$env:PYTHONPATH="src"
python -m image_quality.web_app --host 127.0.0.1 --port 7860
```

## 第 6 轮：结果页演示优化

我的截图反馈提示词：

```text
请放大图表、加原图预览、把指标转成中文结论、增大检测明细的字体（起码放大2倍）、把 ok 改成“正常”
```

AI 输出摘要：

- 结果页新增“原图预览”区，上传后的有效图片可直接在页面确认。
- 检测明细从原始小数改为中文结论，例如“亮度正常”“偏模糊”“分辨率偏低”。
- 状态从英文 `ok` 改为中文“正常”。
- 明细表字体从 14px 放大到 28px，适合投影和课堂演示。
- 统计图改为单列大图，并把生成图尺寸提升到至少 1200x720，标题改为中文。

验证结果：

```text
python -m unittest discover -s tests -v
Ran 8 tests
OK

python -m compileall src tests
```

## 第 7 轮：结果页可读性修正

我的截图反馈提示词：

```text
这个分布图是什么玩意，根本看不懂啊，怎么就一个柱子。另外预览不显示，另外检测明细（改成质量指标）结论放第三行，数据值放第二行，字体大小间距排版要调整，不要出现一个单元格内换行太丑了。指标要换成中文。
```

AI 输出摘要：

- 定位预览不显示的原因：中文文件名直接进入 HTTP `Content-Disposition` 响应头会导致预览请求失败。
- 预览图片 URL 改为百分号编码，响应头改为 ASCII fallback + UTF-8 filename。
- 删除结果页横向大表格，改成“质量指标”卡片：第一行指标名，第二行数据值，第三行中文结论。
- 亮度和清晰度图不再做单张图片分布直方图，改为“指标图”，展示数值、结论和参考阈值。
- Markdown 报告中的状态、问题类型和图表标题改为中文。

验证结果：

```text
python -m unittest discover -s tests -v
Ran 9 tests
OK

python -m compileall src tests
curl 上传中文文件名图片后，预览图返回 200 image/png
```
