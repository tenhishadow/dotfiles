# Scope

Applies to GitHub workflows, release configuration, lint configuration, PR
templates, labels, CODEOWNERS, and repository automation under `.github/`.

## Editing Rules

- Preserve CI responsibility boundaries.
- Keep workflow behavior aligned with `Taskfile.yml`.
- Do not reintroduce super-linter into the `go-task lint` path.
- Do not casually change release-please, Renovate, CODEOWNERS, or zizmor
  configuration.
- Prefer pinned, reproducible, least-privilege automation changes.
- Keep workflow permissions minimal and explicit.
- Keep comments and template text in English.

## Validation

- Run `uv run yamllint .` or `go-task yamllint` for workflow YAML changes.
- Run `go-task lint` when automation changes affect Ansible validation paths.
- Run `go-task superlinter` for repository-wide lint pipeline changes.
- Remember that `go-task superlinter` requires Docker.

## Done Criteria

- Workflow YAML is syntactically clean.
- Existing CI responsibility boundaries are preserved.
- Automation changes match current repository conventions.
