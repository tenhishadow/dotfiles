---
applyTo: ".github/**/*.yml,.github/**/*.yaml,.github/**/*.md,renovate.json,Taskfile.yml"
---

# GitHub Automation Review Instructions

- Keep workflow permissions minimal and explicit.
- Keep long-running or PR-triggered workflows covered by concurrency.
- Keep workflow behavior aligned with `Taskfile.yml`.
- Keep `go-task verify` as the local aggregate validation path for diff,
  Ansible lint, YAML lint, actionlint, Renovate config validation, and
  playbook smoke checks.
- Do not reintroduce Super-Linter into `go-task lint`; it belongs to
  `go-task superlinter`.
- Ensure new versioned GitHub Actions, reusable workflows, Docker images,
  pre-commit hooks, Ansible collections, and future CI includes are detected by
  Renovate or documented as manually updated.
- Keep dependency refresh tasks explicit: `go-task deps-upgrade` should update
  local lock/config surfaces such as `uv.lock`, pre-commit revs, Ansible Galaxy
  installed collections, and Neovim `lazy-lock.json`; GitHub Actions version
  bumps should stay Renovate-managed, with `go-task deps-report:github-actions`
  available for local extraction/dry-run checks.
- Keep `.github/labeler.yml` aligned with current repository paths, including
  AI instructions under `AGENTS.md`, `.github/copilot-instructions.md`, and
  `.github/instructions/`.
- Keep issue forms and the PR template aligned with supported workflows and
  validation commands.
- Keep Copilot instructions concise, review-focused, and non-duplicative:
  repo-wide rules in `.github/copilot-instructions.md`, path-specific rules in
  `.github/instructions/*.instructions.md`.
- Keep documentation-specific review rules in
  `.github/instructions/documentation.instructions.md`.
