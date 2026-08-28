# Scope

Applies to GitHub workflows, release configuration, lint configuration, PR
templates, issue templates, labels, CODEOWNERS, Renovate, and repository
automation under `.github/`.

## Editing Rules

- Preserve CI responsibility boundaries.
- Keep workflow behavior aligned with `Taskfile.yml`.
- Keep `go-task verify` aligned with local validation and review automation.
- Keep the Arch convergence job aligned with `go-task test:system`: it checks
  the explicit `go-task all` order, observable state, and zero-change second
  runs while skipping package and AUR installation.
- Do not reintroduce super-linter into the `go-task lint` path.
- Do not casually change release-please, Renovate, CODEOWNERS, or zizmor
  configuration.
- Pin every `uses:` reference to a full commit SHA with a version comment;
  Renovate and `go-task deps-upgrade` maintain the digest.
- Keep workflow permissions minimal and explicit.
- Keep workflow concurrency explicit for long-running or PR-triggered jobs.
- Keep `.github/labeler.yml` aligned with the current repository structure.
- Keep path labels declared in `.github/labeler.yml` present in GitHub, and
  keep the changed-files label limit high enough for broad maintenance PRs.
- Keep `docs/github-labels.md` aligned with labeler rules and issue-template
  labels.
- Keep issue and PR templates aligned with supported workflows and validation
  commands.
- Keep GitHub Copilot custom instructions concise, review-focused, and aligned
  with the current repo structure. Repo-wide rules are canonical in the root
  `AGENTS.md`; `.github/copilot-instructions.md` condenses them for review and
  `.github/instructions/*.instructions.md` carry path-specific rules.
- Keep `.ruff.toml` and `.github/linters/.ruff.toml` synchronized. Local Ruff
  and Super-Linter read config from different paths.
- Keep `.github/linters/.python-lint` shared by local Pylint and the early
  Python validation job.
- Keep `.github/linters/.markdown-lint.yml` as the shared Markdown rule source
  for local pre-commit and Super-Linter. Do not replace fixes with blanket
  file ignores or inline rule disables.
- Keep `.github/linters/.yaml-lint.yml` linked to the canonical
  `dotfiles/.yamllint` configuration.
- Keep documentation-specific Copilot rules in
  `.github/instructions/documentation.instructions.md`.
- Keep AI instructions clear that the former `ans-workstation` layer is now
  opt-in inside this repository, default `go-task` remains sudo-free, and
  personal workstation settings are not a generic hardening benchmark.
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
- Run `go-task lint:markdown` for Markdown rule or template changes.
- Run `go-task lint` when automation changes affect Ansible validation paths.
- Run `go-task verify` when automation changes affect local aggregate
  validation, issue/PR templates, labeler rules, or AI instructions.
  It includes the system role container test and Super-Linter, and requires a
  running Docker daemon.
- For Arch convergence workflow changes, run `go-task test:system` when Docker
  is available.
- Run `go-task superlinter` for repository-wide lint pipeline changes.
- Remember that `go-task superlinter` requires Docker.

## Done Criteria

- Workflow YAML is syntactically clean.
- Existing CI responsibility boundaries are preserved.
- Automation changes match current repository conventions.
- Issue templates, PR templates, labeler rules, Renovate, and AGENTS guidance
  stay in sync when repository structure changes.
