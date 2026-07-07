# Task Plan: Vibe Coding Homework

## Goal
Complete both PDF-assigned programming tasks as a managed engineering project, with requirements, planning, implementation, verification, and a final report showing how prompt quality shaped code quality.

## Current Phase
Phase 5

## Phases

### Phase 1: Requirements Discovery
- [x] Extract requirements from `Vibe Coding CIFAR-10 Image Classification.pdf`
- [x] Extract requirements from `图像质量检测与自动报告系统.pdf`
- [x] Identify required deliverables, constraints, and grading signals
- [x] Record discoveries in `findings.md`
- **Status:** complete

### Phase 2: Project Planning
- [x] Split the two homework tasks into independent work packages
- [x] Decide project structure, runtime, dependencies, and validation strategy
- [x] Write an implementation plan that can survive multiple sessions
- **Status:** complete

### Phase 3: Implementation
- [x] Build task 1 deliverables
- [x] Build task 2 deliverables
- [x] Keep code generated through model-driven edits and record prompts/decisions
- **Status:** complete

### Phase 4: Testing and Verification
- [x] Run automated tests or smoke checks
- [x] Verify generated outputs and reports
- [x] Log failures, fixes, and final evidence in `progress.md`
- **Status:** complete

### Phase 5: Final Packaging
- [x] Review files for completeness
- [x] Produce final student-facing handoff notes
- [ ] Push to remote Git repository after user provides/creates a remote
- **Status:** in_progress

## Key Questions
1. What exactly do the two PDF assignments require as final artifacts? Answered in `findings.md`.
2. Does the CIFAR-10 task require real training, a demo pipeline, a report, or all of these? It requires full CIFAR training; current local verification uses the provided GitCode dataset repo for real CIFAR quick-dev smoke, plus `--offline-smoke` as fallback.
3. What does the image-quality task expect? CLI, CPU image analysis, CSV, charts, report, examples, README, Git history, and vibe-coding record.
4. How should the vibe-coding process be evidenced? Each project includes `docs/vibe_coding_process.md`; root planning files record decisions, failures, and verification.

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Use file-based planning files | The homework explicitly asks for engineering project management across multiple conversations. |
| Treat the two PDFs as authoritative requirements | User stated the assignment topics are inside the PDFs. |
| Build two independent project folders | The assignments have different dependencies, commands, outputs, and acceptance criteria. |
| Use TensorBoard for CIFAR logging | It avoids W&B API key handling and satisfies the assignment. |
| Add `--offline-smoke` for CIFAR pipeline verification | It provides a no-network fallback for train/test/checkpoint/log/report plumbing without misrepresenting real accuracy. |
| Add GitCode CIFAR preparation script | The user supplied GitCode data source; its archive is RAR content with a `.tar.gz` name, so the project documents and scripts the correct preparation path. |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| Existing active Codex goal prevented creating a duplicate goal | 1 | Continued under the existing active goal. |
| Default `python` resolved to Windows Store alias | 1 | Used Codex bundled Python for PDF extraction and verification. |
| `pdftoppm` wrapper failed on path resolution | 1 | Called the underlying Poppler executable with absolute paths. |
| `pytest` was not installed | 1 | Converted tests to standard-library `unittest`. |
| Test temp dirs hit Windows sandbox permissions | 1 | Used project-local `test_runs/` directories. |
| Official CIFAR-10 download timed out | 1 | Used the provided GitCode repo via shallow clone and extracted the archive with Windows `tar.exe`; kept `--offline-smoke` as fallback. |
| Matplotlib tried to write AppData cache | 1 | Set project-local `MPLCONFIGDIR` before importing Matplotlib. |
| Git writes to `.git` were sandbox-blocked | 1 | Used approved escalated Git commands for init, config, add, and commit. |

## Notes
- Local deliverables are complete except remote push, which needs a user-owned remote URL.
- Real CIFAR quick-dev metrics were generated on 256 test samples; higher-quality metrics require longer full training.
- Do not submit `data/`, `checkpoints/*.pth`, `logs/events.out.tfevents*`, or cache directories to remote Git.
