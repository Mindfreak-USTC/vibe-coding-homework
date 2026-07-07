# Findings and Decisions

## Requirements
- User asks to complete two homework tasks defined in two PDFs in this workspace.
- The work must be managed like an engineering project: requirements alignment, outline planning, step-by-step execution, and requirement review.
- The process must reflect "vibe coding": use the large model to drive best-practice code generation rather than manual coding.
- CIFAR-10 data source provided by user: https://gitcode.com/open-source-toolkit/94ecd/blob/main/cifar-10-python.tar.gz
- Task 1 requires a runnable PyTorch CIFAR-10 ResNet-18 image classification training project.
- Task 1 must include data loading/preprocessing, train/validation/test loops, TensorBoard or W&B logging, best/final checkpoints, test accuracy, per-class accuracy, confusion matrix, experiment report, README, requirements, config file, `.gitignore`, and `docs/vibe_coding_process.md`.
- Task 1 must support CPU, optional GPU, configurable batch size, num_workers, epochs, learning rate, optimizer, seed, TensorBoard log dir, checkpoint dir, and Windows/Linux paths.
- Task 1 grading weights: vibe-coding process record 20, runnability 20, deep learning flow completeness 20, logging/visualization 15, engineering quality 15, experiment analysis 10.
- Task 1 acceptance requires installable dependencies, runnable train/test commands, viewable logs, loadable saved weights, test accuracy, confusion matrix, reproducible README, and complete vibe-coding record.
- Task 2 requires a CPU Python image-quality detection and automatic report project.
- Task 2 must read jpg/png/bmp files from a folder, skip non-images, report corrupted images, compute brightness, contrast, sharpness/blur, noise level, and resolution.
- Task 2 must classify issues: too dark, overexposed, blurry, low contrast, high noise, and low resolution.
- Task 2 must output CSV summary, at least two statistical charts, Markdown or HTML report, README, requirements, example input images, and `docs/vibe_coding_process.md`.
- Task 2 acceptance requires successful local run, Chinese filename handling, non-image/corrupted-file handling, complete CSV, clear report, at least two chart types, clean structure, complete README, and reproducible vibe-coding record.

## Research Findings
- `Vibe Coding CIFAR-10 Image Classification.pdf` has 9 pages. Text extraction and visual page checks confirm the main requirements, submission list, scoring table, and acceptance criteria.
- `图像质量检测与自动报告系统.pdf` has 2 pages. Text extraction and visual page checks confirm the functional list, constraints, submission list, and acceptance criteria.
- PDF-rendered images are stored under `tmp/pdfs/` for inspection.

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Keep a persistent `task_plan.md`, `findings.md`, and `progress.md` | Multiple-session work needs durable state outside chat context. |
| Implement two separate project folders | The two PDFs describe independent systems with different dependencies, commands, and deliverables. |
| Prefer TensorBoard over W&B for the CIFAR-10 project | It avoids API-key handling and satisfies the logging requirement locally. |
| Include synthetic/sample data paths for smoke tests | Full CIFAR-10 training and image-quality analysis should be reproducible, but smoke checks must run quickly on CPU. |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| Default `python` points to Windows Store alias | Used Codex bundled Python at `C:\Users\28751\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`. |
| `pdftoppm` wrapper failed with relative paths | Used the underlying Poppler executable with absolute PDF and output paths. |

## Resources
- `Vibe Coding CIFAR-10 Image Classification.pdf`
- `图像质量检测与自动报告系统.pdf`
- CIFAR-10 archive URL: https://gitcode.com/open-source-toolkit/94ecd/blob/main/cifar-10-python.tar.gz

## Visual/Browser Findings
- CIFAR-10 page 1 visually confirms title, background, task goals, and no-handwritten-core-code constraint.
- CIFAR-10 page 8 visually confirms common issue handling, submission contents, and 100-point scoring table.
- Image-quality page 1 visually confirms the full functional requirements list.
- Image-quality page 2 visually confirms constraints, submission contents, and acceptance criteria.
