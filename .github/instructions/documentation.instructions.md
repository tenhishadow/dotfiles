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
- Document the former `tenhishadow/ans-workstation` consolidation factually
  where repository history or architecture is relevant.
- Do not imply privileged system or browser policy configuration is part of
  default `go-task`.
- Do not present personal workstation security settings as a generic hardening
  benchmark.
- Keep generated manuals current. For Neovim keymaps, regenerate
  `docs/nvim-keymaps.md` with `go-task docs:nvim-keymaps` and verify it with
  `go-task docs:nvim-keymaps:check`.
- Keep documented variable names aligned with the role contracts:
  `dotfiles_*`, `system_*`, and `browser_policies_*`.
- Document system role feature flags, managed paths, and drop-in/snippet paths
  when privileged runtime behavior changes.
- Update architecture, adoption, security, and migration/history docs when
  system-layer behavior or consolidation wording changes.
- Mention `go-task verify` for broad documentation, automation, inventory, or
  role changes.
