---
applyTo: ".github/**/*.yml,.github/**/*.yaml,.github/**/*.md,renovate.json,Taskfile.yml"
---

# GitHub Automation Review Instructions

- Keep workflow permissions minimal and explicit.
- Keep long-running or PR-triggered workflows covered by concurrency.
- Keep workflow behavior aligned with `Taskfile.yml`.
- Keep `go-task verify` as the local aggregate validation path for diff,
  Ansible lint, YAML lint, actionlint, Renovate config validation, playbook
  smoke checks, the system role container test, and Super-Linter.
- Keep `go-task all` as an explicit apply target; it must not replace default
  `go-task` or `go-task verify`.
- Keep the `task-all` CI job as an Arch Linux container check of
  `go-task all -- --skip-tags pkg,aur` so aggregate ordering is covered without
  installing the full workstation package manifest or AUR helper on hosted
  runners.
- Do not reintroduce Super-Linter into `go-task lint`; it belongs to
  `go-task superlinter` and the aggregate `go-task verify` path.
- Ensure new versioned GitHub Actions, reusable workflows, Docker images,
  pre-commit hooks, Ansible collections, and future CI includes are detected by
  Renovate or documented as manually updated.
- Keep Renovate scoped to real repository dependency surfaces. `.test/`
  fixtures must stay ignored because they are detector and smoke-test inputs.
- Keep dependency refresh tasks explicit: `go-task deps-upgrade` should update
  local lock/config surfaces such as `uv.lock`, pre-commit revs, Ansible Galaxy
  installed collections, and Neovim `lazy-lock.json`; GitHub Actions version
  bumps should stay Renovate-managed, with `go-task deps-report:github-actions`
  available for local extraction/dry-run checks.
- Keep `.github/labeler.yml` aligned with current repository paths, including
  AI instructions under `AGENTS.md`, `.github/copilot-instructions.md`, and
  `.github/instructions/`.
- Keep labeler path labels present in GitHub and avoid a changed-file label
  limit that makes broad maintenance PRs skip all labels.
- Keep `docs/github-labels.md` aligned with labeler rules and issue-template
  labels.
- Keep issue forms and the PR template aligned with supported workflows and
  validation commands.
- Keep Copilot instructions concise, review-focused, and non-duplicative:
  repo-wide rules are canonical in the root `AGENTS.md`,
  `.github/copilot-instructions.md` condenses them, and path-specific rules
  live in `.github/instructions/*.instructions.md`.
- Keep documentation-specific review rules in
  `.github/instructions/documentation.instructions.md`.
