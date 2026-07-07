# Vibe Coding Homework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build two independent, reproducible Python homework projects from the assignment PDFs: a CIFAR-10 ResNet-18 training system and an image-quality detection/report system.

**Architecture:** The workspace root holds planning and submission notes. `cifar10-resnet18-vibecoding/` contains the deep learning project with config-driven training, evaluation, TensorBoard logging, checkpoints, outputs, and process documentation. `image-quality-report-vibecoding/` contains the CPU image-quality analyzer with CLI, metrics, charts, CSV, report generation, examples, tests, and process documentation.

**Tech Stack:** Python, PyTorch/TorchVision/TensorBoard for CIFAR-10; Pillow/NumPy/Pandas for image-quality analysis; Pytest for verification; Git for commit history.

---

## File Structure

- Create `cifar10-resnet18-vibecoding/README.md`: install/run/reproduce instructions.
- Create `cifar10-resnet18-vibecoding/requirements.txt`: deep learning dependencies.
- Create `cifar10-resnet18-vibecoding/.gitignore`: exclude datasets, caches, checkpoints, logs, virtualenvs.
- Create `cifar10-resnet18-vibecoding/configs/default.yaml`: default experiment config.
- Create `cifar10-resnet18-vibecoding/src/*.py`: dataset, model, train, evaluate, test, utilities, logging, reports.
- Create `cifar10-resnet18-vibecoding/tests/*.py`: lightweight config/report tests.
- Create `cifar10-resnet18-vibecoding/docs/vibe_coding_process.md`: process record.
- Create `image-quality-report-vibecoding/README.md`: install/run/reproduce instructions.
- Create `image-quality-report-vibecoding/requirements.txt`: CPU image-processing dependencies.
- Create `image-quality-report-vibecoding/.gitignore`: exclude generated outputs/caches.
- Create `image-quality-report-vibecoding/src/image_quality/*.py`: metrics, analyzer, charts, report, CLI.
- Create `image-quality-report-vibecoding/tests/*.py`: metric and CLI smoke tests.
- Create `image-quality-report-vibecoding/sample_images/`: generated examples including Chinese filename, normal/blur/dark/bright/noisy/low-res/non-image/corrupt cases.
- Create `image-quality-report-vibecoding/docs/vibe_coding_process.md`: process record.
- Create root `SUBMISSION_CHECKLIST.md`: what to submit and what still needs remote Git URL/full CIFAR training on the target machine.

## Task 1: Project Skeleton

- [ ] Create directories for both projects and shared submission docs.
- [ ] Add `.gitignore`, `README.md`, `requirements.txt`, and `docs/vibe_coding_process.md` for each project.
- [ ] Verify `rg --files` shows the expected structure.

## Task 2: Image-Quality Tests First

- [ ] Write tests that create temporary image fixtures and assert brightness, contrast, sharpness, noise, and resolution behavior.
- [ ] Write a CLI smoke test that verifies CSV, Markdown report, and at least two PNG charts are generated.
- [ ] Run tests and confirm they fail because implementation modules do not exist yet.

## Task 3: Image-Quality Implementation

- [ ] Implement Pillow/NumPy metric functions.
- [ ] Implement analyzer traversal with Chinese filename, non-image, and corrupted-image handling.
- [ ] Implement CSV, chart, and Markdown report generation under `outputs/`.
- [ ] Run image-quality tests and fix generated code until they pass.
- [ ] Generate sample outputs from `sample_images/`.

## Task 4: CIFAR-10 Lightweight Tests First

- [ ] Write tests for config loading and automatic Markdown report generation.
- [ ] Run tests and confirm they fail because implementation modules do not exist yet.

## Task 5: CIFAR-10 Implementation

- [ ] Implement config loading with YAML support and a fallback parser for the default config.
- [ ] Implement dataset loading, validation split, transforms, and optional CIFAR-10 archive URL handling.
- [ ] Implement ResNet-18 model creation using TorchVision.
- [ ] Implement train/evaluate/test loops with TensorBoard logging, checkpointing, metrics JSON, per-class accuracy, and confusion matrix output.
- [ ] Implement report generation from history and test metrics.
- [ ] Run lightweight tests. Full train/test execution requires installing PyTorch/TorchVision/TensorBoard.

## Task 6: Documentation and Process Record

- [ ] Update both README files with exact commands.
- [ ] Fill both `docs/vibe_coding_process.md` files with prompt, error, feedback, fix, and verification records.
- [ ] Update root `SUBMISSION_CHECKLIST.md`.

## Task 7: Verification and Git

- [ ] Run available automated tests.
- [ ] Run image-quality CLI on sample images and inspect outputs.
- [ ] Run syntax checks for both projects.
- [ ] Initialize Git if possible and create meaningful staged commits.
- [ ] Record any environment limitations, especially missing deep-learning dependencies or missing remote Git URL.
