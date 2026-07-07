# Remote Push Instructions

当前本地仓库已经包含完整作业代码、文档、测试、输出和多次有意义提交。

## 当前阻塞点

`git remote -v` 为空，本机没有可用的 GitHub/GitCode CLI 登录工具，因此不能自动创建远程仓库或推送。

## 获取远程仓库 URL 后执行

```powershell
git remote add origin <你的远程仓库URL>
git push -u origin master
```

## 如果老师只需要压缩包

`dist/` 目录中会生成：

- `vibe-coding-homework-source.zip`：从当前 Git HEAD 导出的源码和提交产物，不包含 `.git`、数据集、checkpoint、TensorBoard 日志和临时缓存。
- `vibe-coding-homework-history.bundle`：包含完整 Git 提交历史，可用 `git clone vibe-coding-homework-history.bundle <folder>` 还原本地仓库历史。

## 大文件说明

以下文件是本地验证产物，已被 `.gitignore` 排除，不会进入远程仓库：

- `cifar10-resnet18-vibecoding/data/`
- `cifar10-resnet18-vibecoding/checkpoints/*.pth`
- `cifar10-resnet18-vibecoding/logs/events.out.tfevents*`
- `tmp/`
