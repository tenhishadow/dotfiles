# Scope

Applies to GitHub workflows, release configuration, lint configuration, PR
templates, issue templates, labels, CODEOWNERS, Renovate, and repository
automation under `.github/`.

The root `AGENTS.md` owns repository-wide rules and validation selection.
`CONTRIBUTING.md` owns branches, commit/PR titles, release behavior, and agent
handoff; `docs/github-labels.md` is the required-label catalog.

## Editing Rules

- Preserve CI responsibility boundaries.
- Keep workflow behavior aligned with `Taskfile.yml`.
- Keep `go-task verify` aligned with local validation and review automation.
- Keep the Arch convergence job aligned with `go-task test:system`: package
  availability and Node.js migration checks precede the three-layer apply and
  zero-change second runs, which skip the full package manifest and AUR tasks.
- Do not reintroduce super-linter into the `go-task lint` path.
- For release-please, Renovate, CODEOWNERS, and zizmor changes, trace the
  affected release, update, ownership, or security contract before editing.
- Pin external action and reusable-workflow `uses:` references to full commit
  SHAs with version comments; local `./` references have no remote revision.
  `go-task deps-upgrade` and the weekly dependency workflow use pinact to
  maintain those digests.
- Keep workflow permissions minimal and explicit.
- Keep workflow concurrency explicit for long-running or PR-triggered jobs.
- Keep `.github/labeler.yml` aligned with the current repository structure.
- Keep labels consumed by automation present in the catalog. Local rule edits
  do not authorize remote label creation, renaming, or deletion.
- Keep label assignment metadata-only: `pull_request_target` must not check
  out PR code, execute it, or import its artifacts. Scope write permissions to
  the job that needs them and use the PR number for concurrency.
- Keep `docs/github-labels.md` aligned with labeler rules and issue-template
  labels.
- Keep issue and PR templates aligned with supported workflows and validation
  commands.
- Validate PR titles with `.commitlintrc.yaml`; the squash workflow makes that
  title the integration commit. The weekly dependency PR uses `chore(deps)`
  under the same policy.
- Keep Release Please on the integration branch with a parseable generated
  release PR. Do not regenerate its body with the human PR template or change
  release versions incidentally during maintenance.
- Keep GitHub Copilot custom instructions concise, scoped, and aligned
  with the current repo structure. Repo-wide rules are canonical in the root
  `AGENTS.md`; `.github/copilot-instructions.md` controls review presentation and
  `.github/instructions/*.instructions.md` carry path-specific rules.
- Preserve the owner, source-repository, current-head, CI, and deduplication
  gates in Copilot review automation. Keep it metadata-only with a read-only
  Actions token and a separate owner-scoped review credential. Activation and
  budget controls belong to `CONTRIBUTING.md`, not instruction text.
- Follow the root instruction-sync contract for shared Ruff, Pylint, and
  Markdown configurations; local and CI checks must consume the same rules.
- Keep `.github/linters/.yaml-lint.yml` linked to the canonical
  `dotfiles/.yamllint` configuration.
- Keep documentation-specific Copilot rules in
  `.github/instructions/documentation.instructions.md`.
- Give path-specific Copilot files an `applyTo` glob matching their actual
  scope. Use `excludeAgent` only when a rule is intentionally specific to one
  agent; shared instructions apply to review and implementation.
- Keep `.github/scripts/update_dependencies.py` aligned with all managed
  dependency surfaces. The local updater leaves reviewable changes without
  committing or pushing; the explicitly configured weekly workflow publishes
  the single maintenance PR. Keep Renovate extraction read-only and its
  competing PR creation disabled.
- Keep AI-instruction changes discoverable by the `ai-instructions` labeler
  rule.

Consult GitHub's [instruction support matrix](https://docs.github.com/en/copilot/reference/custom-instructions-support)
before changing discovery. Code review reads instructions and skills from the
[PR head](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/request-a-code-review/use-code-review#customizing-copilots-reviews-with-custom-instructions);
keep them concise without inventing a provider character or token limit.

## Validation

- Run `uv run yamllint .` or `go-task yamllint` for workflow YAML changes.
- Run `go-task lint:markdown` for Markdown rule or template changes.
- Run `go-task lint` when automation changes affect Ansible validation paths.
- For Markdown instructions or template prose, run documentation checks only.
  A path under `.github/` does not by itself require Docker or `go-task verify`.
- Use the root matrix for executable automation and aggregate runner changes;
  match checks to changed behavior rather than neighboring file types.
- For Arch convergence workflow changes, run `go-task test:system` when Docker
  is available.
- Run `go-task superlinter` for repository-wide lint pipeline changes.

## Done Criteria

- Workflow YAML is syntactically clean.
- Existing CI responsibility boundaries are preserved.
- Automation changes match current repository conventions.
- Issue templates, PR templates, labeler rules, Renovate, and AGENTS guidance
  stay in sync when repository structure changes.
