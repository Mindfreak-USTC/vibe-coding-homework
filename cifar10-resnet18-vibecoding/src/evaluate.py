from __future__ import annotations

from typing import Any


def evaluate(model, dataloader, criterion, device: str, num_classes: int = 10) -> dict[str, Any]:
    import torch

    model.eval()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0
    class_correct = torch.zeros(num_classes, dtype=torch.long)
    class_total = torch.zeros(num_classes, dtype=torch.long)
    confusion = torch.zeros((num_classes, num_classes), dtype=torch.long)

    with torch.no_grad():
        for images, targets in dataloader:
            images = images.to(device)
            targets = targets.to(device)
            outputs = model(images)
            loss = criterion(outputs, targets)
            preds = outputs.argmax(dim=1)
            batch_size = targets.size(0)
            total_loss += float(loss.item()) * batch_size
            total_correct += int((preds == targets).sum().item())
            total_samples += batch_size

            for label, pred in zip(targets.cpu(), preds.cpu()):
                class_total[int(label)] += 1
                class_correct[int(label)] += int(label == pred)
                confusion[int(label), int(pred)] += 1

    avg_loss = total_loss / max(1, total_samples)
    accuracy = total_correct / max(1, total_samples)
    per_class_accuracy = [
        float(class_correct[index].item() / class_total[index].item()) if class_total[index].item() else 0.0
        for index in range(num_classes)
    ]
    return {
        "loss": avg_loss,
        "accuracy": accuracy,
        "per_class_accuracy": per_class_accuracy,
        "confusion_matrix": confusion.tolist(),
        "samples": total_samples,
    }

