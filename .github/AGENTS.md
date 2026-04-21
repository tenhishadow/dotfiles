# Scope

- Applies to GitHub workflows, release config, lint config, PR templates,
  and repository automation under `.github/`.

# Editing Rules

- Preserve CI separation.
- Do not reintroduce super-linter into the ansible-lint-only task flow.
- Keep workflow behavior aligned with `Taskfile.yml`.
- Do not casually change release-please, renovate, or zizmor related
  config.
- Prefer reproducible, pinned, and low-surprise automation changes.

# Validation

- Run `uv run yamllint .` when editing workflow YAML and the tool is
  available.
- Run `go-task lint` when automation changes affect Ansible validation
  paths.
- Run `go-task superlinter` for repo-wide lint pipeline changes.
- Remember that `go-task superlinter` requires Docker.

# Done Means

- Workflow YAML is syntactically clean.
- Existing CI responsibility boundaries are preserved.
- Automation changes match the current repo conventions.
