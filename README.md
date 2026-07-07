# Vibe Coding Homework

本仓库用于提交两个 PDF 编程作业：

1. `cifar10-resnet18-vibecoding/`：基于 CIFAR-10 的 ResNet-18 图像分类训练系统。
2. `image-quality-report-vibecoding/`：图像质量检测与自动报告系统。

本次作业按工程项目方式完成：先做需求对齐，再规划大纲，再分步执行，最后用验收审计表逐项回顾需求。代码和文档均通过 vibe coding 流程生成和迭代，过程记录保存在两个项目的 `docs/vibe_coding_process.md` 中。

## 快速入口

- `TEACHER_HANDOFF.md`：老师/助教检查入口。
- `ACCEPTANCE_AUDIT.md`：逐项需求验收审计表。
- `PROJECT_MANAGEMENT_REPORT.md`：工程项目管理总结。
- `SUBMISSION_CHECKLIST.md`：提交清单。
- `REMOTE_PUSH_INSTRUCTIONS.md`：远程推送说明。

## 一键本地验收

在仓库根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify_submission.ps1 -Python <python-path>
```

该脚本会检查两个项目的单元测试、语法编译、Git bundle、源码 zip 内容和 SHA256 校验。当前没有远程仓库时，脚本会给出 warning；如果要把远程仓库缺失作为失败条件，追加 `-RequireRemote`。

## 刷新离线交付包

如果后续又有本地提交，可以用脚本重建 `dist/`：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/package_submission.ps1 -Python <python-path>
```

想先预览命令、不改动 `dist/`，追加 `-DryRun`。

## 远程推送

拿到空仓库 URL 后，可以用脚本完成 remote 配置、push 和远程条件验收：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/push_remote.ps1 -RemoteUrl <你的远程仓库URL> -Python <python-path>
```

想先看脚本会执行什么命令，可以追加 `-DryRun`。

## 离线提交材料

`dist/` 目录中有离线交付物：

- `vibe-coding-homework-source.zip`
- `vibe-coding-homework-history.bundle`
- `SHA256SUMS.txt`

源码包不包含 `.git`、CIFAR 数据集、checkpoint、TensorBoard 日志或临时缓存。

## 当前外部缺口

本地代码、文档、测试、报告和离线交付包已经准备好。当前唯一外部缺口是远程仓库 URL。拿到空仓库 URL 后也可以手动执行：

```powershell
git remote add origin <你的远程仓库URL>
git push -u origin master
```
