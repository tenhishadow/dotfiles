---
applyTo: ".github/**/*.yml,.github/**/*.yaml,.github/**/*.md,renovate.json,Taskfile.yml"
---

# GitHub Automation Review Instructions

- Keep workflow permissions minimal and explicit.
- Require full commit SHAs with version comments for every `uses:` reference.
  Keep those digests managed by Renovate and `go-task deps-upgrade`.
- Keep long-running or PR-triggered workflows covered by concurrency.
- Keep workflow behavior aligned with `Taskfile.yml`.
- Keep `go-task verify:fast` as the no-Docker repository contract and
  `go-task verify` as the local aggregate that adds isolated Neovim checks,
  Arch convergence, and Super-Linter without applying the local workstation.
- Keep `go-task all` as an explicit apply target; it must not replace default
  `go-task` or `go-task verify`.
- Keep the Arch convergence CI job aligned with `go-task test:system`: apply
  `go-task all -- --skip-tags pkg,aur`, assert observable state, and require
  zero-change second playbook runs.
- Do not reintroduce Super-Linter into `go-task lint`; it belongs to
  `go-task superlinter` and the aggregate `go-task verify` path.
- Ensure new versioned GitHub Actions, reusable workflows, Docker images,
  pre-commit hooks, Ansible collections, and future CI includes are detected by
  Renovate or documented as manually updated.
- Keep Renovate scoped to real repository dependency surfaces. `.test/`
  fixtures must stay ignored because they are detector and smoke-test inputs.
- Keep `go-task deps-upgrade` as the explicit local aggregate for Python,
  Ansible Galaxy, pre-commit, managed npm, Neovim, GitHub Actions, reusable
  workflows, and Taskfile tool pins. It may change dependency files only; it
  must not commit, push, or treat `.test/` fixtures as dependency surfaces.
- Keep `go-task deps-report:github-actions` as the read-only Renovate extraction
  report; local Renovate mode must not be presented as a worktree updater.
- Keep `.github/labeler.yml` aligned with current repository paths, including
  AI instructions, provider adapters, and `.agents/skills/`.
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
