# Scope

Applies to GitHub workflows, release configuration, lint configuration, PR
templates, issue templates, labels, CODEOWNERS, Renovate, and repository
automation under `.github/`.

## Editing Rules

- Preserve CI responsibility boundaries.
- Keep workflow behavior aligned with `Taskfile.yml`.
- Keep `go-task verify` aligned with local validation and review automation.
- Do not reintroduce super-linter into the `go-task lint` path.
- Do not casually change release-please, Renovate, CODEOWNERS, or zizmor
  configuration.
- Prefer pinned, reproducible, least-privilege automation changes.
- Keep workflow permissions minimal and explicit.
- Keep workflow concurrency explicit for long-running or PR-triggered jobs.
- Keep `.github/labeler.yml` aligned with the current repository structure.
- Keep issue and PR templates aligned with supported workflows and validation
  commands.
- Keep GitHub Copilot custom instructions concise, review-focused, and aligned
  with the current repo structure. Put repo-wide rules in
  `.github/copilot-instructions.md` and path-specific rules in
  `.github/instructions/*.instructions.md`.
- Keep documentation-specific Copilot rules in
  `.github/instructions/documentation.instructions.md`.
- Keep Neovim keymap review rules aligned with
  `docs/nvim-keymaps.md`, `dotfiles/.config/nvim/lua/config/keymaps_spec.lua`,
  and `Taskfile.yml`.
- Keep each Copilot review instruction file below 4,000 characters; Copilot
  code review ignores content past that limit. Instruction changes affect PR
  reviews after they exist on the PR base branch.
- When adding a versioned GitHub Action, reusable workflow, Docker image,
  pre-commit hook, Ansible collection, or future GitLab CI include, make sure
  Renovate can update it. Add a Renovate manager or custom manager when the
  dependency is not detected by a built-in manager.
- Keep AI-instruction changes discoverable by the `ai-instructions` labeler
  rule.
- Keep comments and template text in English.

## Validation

- Run `uv run yamllint .` or `go-task yamllint` for workflow YAML changes.
- Run `go-task lint` when automation changes affect Ansible validation paths.
- Run `go-task verify` when automation changes affect local aggregate
  validation, issue/PR templates, labeler rules, or AI instructions.
  It includes Super-Linter and requires a running Docker daemon.
- Run `go-task superlinter` for repository-wide lint pipeline changes.
- Remember that `go-task superlinter` requires Docker.

## Done Criteria

- Workflow YAML is syntactically clean.
- Existing CI responsibility boundaries are preserved.
- Automation changes match current repository conventions.
- Issue templates, PR templates, labeler rules, Renovate, and AGENTS guidance
  stay in sync when repository structure changes.
