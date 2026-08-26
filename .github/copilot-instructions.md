# Copilot Review Deltas

The root and nearest `AGENTS.md` files are canonical. Use this file only for
review checks that automation cannot prove.

- Flag any change that makes default `go-task` privileged, routes
  `roles/system` or `roles/browser_policies` through `playbook_install.yml`, or
  describes `go-task all` as the default.
- Flag committed secrets, credentials, profiles, histories, caches,
  kubeconfigs, AI/MCP account state, generated workspaces, or copied
  machine-local configuration.
- Flag undocumented AI-client, privacy, or policy keys and broadened cleanup or
  removal paths.
- For Ansible, focus on idempotence, unsafe shell or command behavior, missing
  ownership or modes under `/etc`, missing role-input validation, and
  privileged behavior without CI, container, and VM guards.
- Flag direct edits to upstream main configuration when a supported drop-in or
  snippet path exists.
- Flag docs that present personal workstation settings as a generic hardening
  benchmark or claim supported environments without matching evidence.
- For Neovim, flag save-time mutation, lockfile drift, first-buffer filetype
  regressions, duplicated language or tool inventories, and keymap changes
  missing their specification and generated manual update.
- For GitHub automation, flag broadened permissions, missing concurrency,
  unpinned or Renovate-unmanaged dependencies, and changes that merge
  Super-Linter into `go-task lint`.
- Require documentation or ADR updates when architecture, managed paths,
  validation, rollback, or runtime behavior changes.
- Recommend the narrowest validation from the root `AGENTS.md`; use
  `go-task verify` for broad cross-layer changes.
