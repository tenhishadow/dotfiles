# Scope

Applies to `.test/`.

This directory contains canonical smoke-test fixtures and generated local test
workspaces.

## Canonical Files

- `.test/nvim/smoke.lua`
- `.test/nvim/compat.lua`
- `.test/nvim/treesitter_install.lua`
- `.test/nvim/keymap_docs.lua`
- `.test/nvim/mason_tools.lua`
- `.test/nvim/*` language sample fixtures
- `.test/vint_runner.py`
- `.test/assert_ansible_convergence.py`
- `.test/role_contracts.yml`
- `.test/system/exec.sh`
- `.test/system/local.env.example`
- `.test/system/verify.yml`
- `.test/workstation_report.py`

`.test/vint_runner.py` runs vim-vint with a minimal `pkg_resources`
compatibility shim so the project environment does not need `setuptools`.

`.test/workstation_report.py` provides read-only local reports for adoption,
dotfiles destination review, system paths, and policy file ownership.

`.test/system/exec.sh` is the Arch Linux package-target and convergence harness
used by `go-task test:system` and `go-task verify`. It applies all three layers,
runs the observable-state assertions in `.test/system/verify.yml`, and requires
zero changes or hidden failures on each second playbook run.

## Generated Files

These paths are scratch state created by test runs and must not be treated as
source of truth:

- `.test/nvim/.config`
- `.test/nvim/.data`
- `.test/nvim/.state`
- `.test/nvim/.cache`
- `.test/system/local.env` (optional private test mirrors)

## Editing Rules

- Keep fixtures minimal and deterministic.
- Keep Neovim smoke fixture directories aligned with the `name` values in
  `.test/nvim/smoke.lua`.
- Keep generated workspaces out of git.
- Keep private mirror and package-index URLs in `.test/system/local.env` only.
- Keep `.test/` excluded from Renovate because dependency-like files here are
  fixtures, not repository dependency surfaces.
- Keep Neovim test language lists sourced from the canonical config when
  possible, especially `config.languages`.
- Keep Tree-sitter parser installation optional in the test sandbox and skip
  cleanly when required external tools are missing.
- Keep shell scripts robust with safe flags where practical.
- Keep comments, sample text, and documentation in English.

## Validation

```bash
go-task test:nvim
go-task test:nvim:compat
go-task test:nvim:mason-tools
go-task docs:nvim-keymaps:check
go-task test:contracts
go-task test:system
go-task doctor
```

Run the test that matches the changed fixture area.

## Done Criteria

- Fixture changes still support the smoke tests.
- Generated test workspace content was not mistaken for canonical config.
- No local runtime state was committed.
