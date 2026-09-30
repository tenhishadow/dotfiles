---
applyTo: ".github/**/*.yml,.github/**/*.yaml,.github/scripts/**,.pre-commit-config.yaml,renovate.json,Taskfile.yml"
---

# GitHub Automation Review Instructions

Follow `.github/AGENTS.md` for automation ownership and the root `AGENTS.md`
Code Review Rules and Taskfile conventions.

Use `CONTRIBUTING.md` for commit/PR and release contracts, and
`docs/github-labels.md` for the required-label catalog.

- Trace untrusted PR input into shell commands, credentials, write permissions,
  and artifact handling. Review cancellation and concurrency against the job's
  actual side effects rather than requiring the same policy everywhere.
- Metadata-only `pull_request_target` jobs must not check out or execute PR
  code. Title validation must receive the title as data, not shell syntax,
  and rerun after title edits.
- Check that PR-title syntax, weekly update messages, squash settings, and Release
  Please agree. A PR-body breaking-change footer is lost when the squash body
  is blank; the PR title needs `!` in that workflow.
- Check that changed dependency references remain pinned where required and
  covered by the shared local updater. Distinguish external action digests,
  version comments, and local action paths; Renovate
  extraction is an audit surface, not a parallel PR producer.
- Trace failed subprocesses through pipes, substitutions, task dependencies,
  and workflow gates; an outer success status must not hide a failed check.
- Check locked validation separately from dependency upgrades. Refreshes must
  leave reviewable dependency-file changes; Renovate extraction reports do
  not themselves update the worktree, and `.test/` fixtures are not upgrade
  inputs.
- Trace the three-layer apply and second-run assertions in the Arch harness.
  Package availability, package migration, backend simulation, convergence,
  and real VM synchronization are distinct kinds of evidence.
- Inspect inherited HOME/XDG values, quoted mount paths, temporary workspaces,
  and cleanup. Check fresh-checkout inputs and declared setup; ignored local
  runtimes cannot be required by a static contract check.
- For changed routing, labels, or templates, update the corresponding command
  or ownership contract only where it becomes inaccurate. Markdown-only
  instruction changes do not require runtime or container suites.
