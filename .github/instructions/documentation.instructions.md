---
applyTo: "**/*.md,**/AGENTS.md,.github/copilot-instructions.md,.github/instructions/*.instructions.md"
---

# Documentation Review Instructions

- Keep repository documentation in English.
- Update `README.md` when commands, entry points, repository layout,
  validation paths, or runtime behavior change.
- Update role README files when role variables, managed paths, task flow,
  validation, or rollback behavior changes.
- Update the nearest `AGENTS.md` when local editing rules, ownership
  boundaries, validation commands, or done criteria change.
- Keep AI instructions concise and non-duplicative: repo-wide rules in
  `.github/copilot-instructions.md`, path-specific rules in
  `.github/instructions/*.instructions.md`, and local operational rules in
  `AGENTS.md`.
- Preserve the default contract in docs: `go-task` applies user-level
  dotfiles only and must not require sudo.
- Keep documented variable names aligned with the role contracts:
  `dotfiles_*`, `system_*`, and `browser_policies_*`.
- Mention `go-task verify` for broad documentation, automation, inventory, or
  role changes.
