# Task Plan: Vibe Coding Homework

## Goal
Complete both PDF-assigned programming tasks as a managed engineering project, with requirements, planning, implementation, verification, and a final report showing how prompt quality shaped code quality.

## Current Phase
Phase 2

## Phases

### Phase 1: Requirements Discovery
- [x] Extract requirements from `Vibe Coding CIFAR-10 Image Classification.pdf`
- [x] Extract requirements from `图像质量检测与自动报告系统.pdf`
- [x] Identify required deliverables, constraints, and grading signals
- [x] Record discoveries in `findings.md`
- **Status:** complete

### Phase 2: Project Planning
- [x] Split the two homework tasks into independent work packages
- [ ] Decide project structure, runtime, dependencies, and validation strategy
- [ ] Write an implementation plan that can survive multiple sessions
- **Status:** in_progress

### Phase 3: Implementation
- [ ] Build task 1 deliverables
- [ ] Build task 2 deliverables
- [ ] Keep code generated through model-driven edits and record prompts/decisions
- **Status:** pending

### Phase 4: Testing and Verification
- [ ] Run automated tests or smoke checks
- [ ] Verify generated outputs and reports
- [ ] Log failures, fixes, and final evidence in `progress.md`
- **Status:** pending

### Phase 5: Final Packaging
- [ ] Review files for completeness
- [ ] Produce final student-facing handoff notes
- [ ] Mark the goal complete only after all required deliverables exist
- **Status:** pending

## Key Questions
1. What exactly do the two PDF assignments require as final artifacts?
2. Does the CIFAR-10 task require real training, a demo pipeline, a report, or all of these?
3. What does the image-quality task expect: CLI, GUI, report generation, dataset examples, or evaluation metrics?
4. How should the "vibe coding" process be evidenced in the submitted project?

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Use file-based planning files | The homework explicitly asks for engineering project management across multiple conversations. |
| Treat the two PDFs as authoritative requirements | User stated the assignment topics are inside the PDFs. |
| Build two independent project folders | The assignments have different dependencies, commands, outputs, and acceptance criteria. |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| Existing active Codex goal prevented creating a duplicate goal | 1 | Continued under the existing active goal. |
| Default `python` resolved to Windows Store alias | 1 | Used Codex bundled Python for PDF extraction. |
| `pdftoppm` wrapper failed on path resolution | 1 | Called the underlying Poppler executable with absolute paths. |

## Notes
- Keep all generated work in this workspace unless a PDF explicitly requires another location.
- Prefer reproducible local commands and lightweight smoke checks because large ML training may be slow.
- Do not rely on unstated assumptions from the chat when the PDFs provide concrete requirements.
