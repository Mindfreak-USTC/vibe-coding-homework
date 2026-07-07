# CIFAR-10 ResNet-18 实验报告

## 实验配置摘要
- 模型: ResNet-18
- 数据集: CIFAR-10
- 日志: TensorBoard

## 训练与验证结果
- 最终训练 loss: 2.4022
- 最终训练 accuracy: 0.1602
- 最终验证 loss: 2.2576
- 最终验证 accuracy: 0.1471

## 测试结果
- 测试集整体准确率: 0.1992
- 混淆矩阵: C:\Users\28751\Desktop\ju\cifar10-resnet18-vibecoding\outputs\confusion_matrix.png

## 每类准确率
- airplane: 0.0769
- automobile: 0.1500
- bird: 0.0833
- cat: 0.1304
- deer: 0.4000
- dog: 0.0769
- frog: 0.3448
- horse: 0.0000
- ship: 0.5882
- truck: 0.0333

## 实验分析
- 模型是否正常收敛: 当前记录不足两个 epoch，只能确认流程是否跑通，不能可靠判断收敛趋势。
- 是否出现明显过拟合：未见明显迹象。最终 train/val accuracy 差值为 0.0131。
- 哪些类别容易被混淆: 需要结合 `outputs/confusion_matrix.png` 观察非对角线高值。
- 后续改进方向: 增加训练轮数、加入学习率调度、尝试更强数据增强、比较 MobileNetV2 或 SimpleCNN。
