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

- 生成 `metrics.py`：亮度、对比度、清晰度、噪点、分辨率。
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

## 第 13 轮：PDF 报告下载与首页放大

我的追加反馈提示词：

```text
点击下载报告并没有下载只是弹出来一些文字。我需要下载下来是规规整整和网页上一样。另外开始界面这个标题居中靠上不要换行，ui大一点
报告不要html要pdf格式
```

AI 输出摘要：

- 将 Web 页面“下载报告”从 Markdown 文本链接改为 `report.pdf` 下载链接，并加上浏览器 `download` 属性。
- 在上传检测完成后额外生成 PDF 报告，PDF 中包含本次汇总、原图预览、质量指标、指标说明和统计图。
- 下载路由对 CSV、Markdown 和 PDF 使用 `Content-Disposition: attachment`，避免浏览器直接打开文本。
- 首页上传界面改成更大的居中单列卡片，标题居中靠上并禁止换行。
- README 同步说明：命令行仍输出 Markdown 报告，Web 演示下载 PDF 报告。

验证结果：

```text
python -m unittest discover -s tests -v
Ran 12 tests
OK

python -m compileall src tests
OK
```

## 第 14 轮：Web 演示服务持久化

我的追加反馈提示词：

```text
永久修复一下
```

AI 输出摘要：

- 新增 `scripts/Start-ImageQualityWeb.ps1`：检查 `127.0.0.1:7860` 是否已监听，未监听时自动后台启动 Web 服务。
- 新增 `scripts/Watch-ImageQualityWeb.ps1`：每 30 秒执行一次健康检查，服务退出后自动恢复。
- 新增 `scripts/Install-ImageQualityWebStartup.ps1`：写入当前用户 Windows 启动项，并立即启动 watchdog。
- 修复后台隐藏环境中 `PATH` 不完整导致找不到 `netstat` 的问题，改为绝对路径调用系统工具。
- 修复 PowerShell `$PID` 只读变量冲突，保证 watchdog 日志不再报错。

验证结果：

```text
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\Start-ImageQualityWeb.ps1 -Port 7860
Image quality web UI is already running: http://127.0.0.1:7860/ PID=110368

手动停止旧服务 PID 后，watchdog 自动恢复新 PID=62040
curl http://127.0.0.1:7860/ 返回首页正常
```

## 第 11 轮：结果页分区与上传页居中

我的追加反馈提示词：

```text
质量指标单独变成一张卡片不要和上面连起来。图片预览部分只要一个框就行。第一页那个输入图像的部分居中屏幕不要顶着上面其他不用动
```

AI 输出摘要：

- 给上传页增加独立页面样式，只让第一页主内容在屏幕中垂直居中。
- 将结果页“质量指标”加上独立卡片间距，和顶部检测完成/预览区域分开。
- 删除原图预览内部卡片的边框、阴影和内边距，只保留外层预览卡片一个框。
- 补充 Web 回归测试，固定上传页居中样式、预览单框样式和质量指标独立卡片结构。

验证结果：

```text
python -m unittest image-quality-report-vibecoding.tests.test_web_app -v
Ran 5 tests
OK
```

## 第 12 轮：真实噪点图片阈值校准

我的截图反馈提示词：

```text
我输入了这个他还是显示都是正常的，噪点和分辨率的阈值改一改，还有噪声改成噪点
```

AI 输出摘要：

- 使用真实输入图片复现问题：图片尺寸为 `447x447`，噪点指标约为 `5.2`，旧规则仍判断为正常。
- 将默认噪点阈值从 `22.0` 调整为 `5.0`，达到阈值即标记为“噪点偏高”。
- 将默认分辨率阈值从 `64x64` 调整为 `512x512`，任一边小于 512 像素即标记为“分辨率偏低”。
- Web 页面、Markdown 报告、统计图问题标签和 README 中的“噪声”统一改为“噪点”。
- 增加回归测试，确保 `noise=5.2` 且 `447x447` 的图片会同时触发“噪点偏高”和“分辨率偏低”。

验证结果：

```text
python -m unittest image-quality-report-vibecoding.tests.test_quality_metrics.QualityMetricsTests.test_default_thresholds_flag_noisy_447px_image_as_problematic image-quality-report-vibecoding.tests.test_web_app image-quality-report-vibecoding.tests.test_cli_outputs.CliOutputTests.test_cli_generates_csv_report_and_two_charts -v
Ran 7 tests
OK
```

## 第 11 轮：原图预览卡片精简

我的截图反馈提示词：

```text
原图预览把离图片最近的框删除，还有这个正常模糊这种检测词语也删了，只留名字和格式居中在图片下面
```

AI 输出摘要：

- 删除预览图片自身的细边框，只保留外层预览卡片结构。
- 原图预览图注只显示文件名和后缀，例如“缆车3.png”。
- 删除预览区里的“正常”“模糊”等检测结论文案，检测结论只保留在质量指标区域。
- 预览图注改为居中显示。
- 增加回归测试，防止预览图注再次混入检测词或图片内框。

验证结果：

```text
python -m unittest image-quality-report-vibecoding.tests.test_web_app -v
Ran 5 tests
OK
```

## 第 10 轮：统计卡片与问题标签优化

我的截图反馈提示词：

```text
图1改成2x2布局，卡片大一点字体大一点；图2：如果有问题就不要写正常，下面那个问题移到左边那个绿色的正常那里，原来的正常删除。图3xxx图标题下面小字大一点要不然看不清
```

AI 输出摘要：

- 顶部统计卡片改为 2x2 布局，并增大卡片高度、数字字号和说明文字字号。
- 质量指标区域新增统一结果徽章：无问题显示“正常”，有问题时直接显示问题标签，例如“模糊”，不再同时显示“正常”和“问题：模糊”。
- 原图预览中的结论也复用同一结果徽章文案，避免出现“正常 · 模糊”。
- 删除质量指标卡片内单独的“问题：”行，让信息集中在右上角结果徽章。
- 放大图表标题下方解释文字，提升课堂投影可读性。

验证结果：

```text
python -m unittest image-quality-report-vibecoding.tests.test_web_app -v
Ran 5 tests
OK
```

## 第 9 轮：顶部统计与图表视觉修正

我的截图反馈提示词：

```text
图标还是一个大色块；把图2这四个移到第一个卡片下方，也就是三个按键的下方
```

AI 输出摘要：

- 将“总文件数、有效图像、跳过文件、损坏/错误”四个统计卡片移动到顶部左侧卡片内，放在“继续上传 / 下载 CSV / 下载报告”三个按钮下方。
- 问题数量图从大面积实心柱改成细标记线、圆点和“次数”标签。
- 亮度、清晰度指标图从实心横条改成坐标轴、参考线、细标记线、圆点和中文结论标签。
- 调整图表底部刻度与数值标签，避免参考线标签和最大值标签挤在一起。
- 增加回归测试，防止统计卡片位置退回、单张图片图表再次变成大色块。

验证结果：

```text
python -m unittest discover -s tests -v
Ran 10 tests
OK

python -m compileall src tests
curl 上传中文文件名图片后，原图预览和图表 URL 均返回 200 image/png
```

## 第 8 轮：页面信息架构调整

我的追加反馈提示词：

```text
质量指标放单独一个卡片和图片预览隔开；图片预览放在原来本次汇总卡片，本次汇总删除。质量指标卡片右下角说明一下数据指标。三张图标没有横纵坐标，而且还是就一根柱子不知道在表达什么（per图表下一个解释），三个表格放在同一行没必要做这么大。
```

AI 输出摘要：

- 顶部右侧卡片从“本次汇总”改为“原图预览”，删除独立预览区。
- “质量指标”保持独立卡片，并在右下角补充数据说明：灰度统计、相对强度和像素单位。
- 三张统计图在桌面端改为同一行较小卡片展示。
- 每张图表下方增加解释，说明横轴、纵轴和单张图片只有一根柱的原因。
- 图表 PNG 内部增加横轴/纵轴说明，避免单独查看图表时看不懂。

验证结果：

```text
python -m unittest discover -s tests -v
Ran 9 tests
OK

python -m compileall src tests
curl 上传中文文件名图片后，预览图返回 200 image/png
```
