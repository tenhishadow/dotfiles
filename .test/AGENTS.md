# Scope

Applies to `.test/`.

The root `AGENTS.md` owns repository-wide rules and validation selection.

This directory contains canonical smoke-test fixtures and generated local test
workspaces.

## Canonical Surfaces

- `.test/test_*.py` contains pytest regression and contract tests.
- `.test/conftest.py` contains fixtures shared by multiple test modules.
- `.test/nvim/` contains smoke runners and minimal language fixtures.
- `.test/role_contracts.yml` validates Ansible inputs and backend selection.
- `.test/system/` owns container-only apply, state, and convergence checks.
- `.test/check_*.py` and `.test/gen_agents_map.py` validate repository contracts
  and generated documentation.

`.test/vint_runner.py` runs vim-vint with a minimal `pkg_resources`
compatibility shim so the project environment does not need `setuptools`.

The pytest configuration lives in `pyproject.toml`; run the same suite through
`go-task test:python` locally and in CI. Pass selectors after `--` for a focused
run. `test_agent_tooling.py` validates Codex configuration and npm locks;
`test_portable_hook.py` exercises the hook through its JSON interface.

`.test/workstation_report.py` provides read-only local reports for adoption,
dotfiles destination review, system paths, and policy file ownership.

`.test/system/exec.sh` is the Arch Linux package-target and convergence harness
used by `go-task test:system` and `go-task verify`. It validates preventative
time-service masking and Chrony syntax, applies all three layers, runs the
observable-state assertions in `.test/system/verify.yml`, and requires zero
changes or hidden failures on each second playbook run.

## Generated Files

These paths are scratch state created by test runs and must not be treated as
source of truth:

- `.test/nvim/.config`
- `.test/nvim/.data`
- `.test/nvim/.state`
- `.test/nvim/.cache`
- `.test/nvim/.home`
- `.test/system/local.env` (legacy private mirror overrides; the current
  location is `local.env` in the repository root)

## Editing Rules

- Keep fixtures minimal and deterministic.
- Keep Neovim smoke fixture directories aligned with the `name` values in
  `.test/nvim/smoke.lua`.
- Keep private mirror and package-index URLs in `local.env` only.
- Keep `.test/` excluded from Renovate because dependency-like files here are
  fixtures, not repository dependency surfaces.
- Keep Neovim test language lists sourced from the canonical config when
  possible, especially `config.languages`.
- Keep Tree-sitter parser installation optional for ordinary local smoke tests.
  CI must use required mode and fail when tools, parsers, or the success marker
  are missing.
- Keep Python tests discoverable as `test_*.py`, using plain test functions and
  `assert`. Use `pytest.mark.parametrize` for independent cases, and `tmp_path`,
  `monkeypatch`, and capture fixtures for isolated state. Keep specialized
  helpers local; promote a fixture to `conftest.py` only when modules share it.
- Follow the validation ADR for test value, removal criteria, and style. Do not
  replace native Ansible validation with a Python copy of its Jinja expressions.
- Keep Python contracts deterministic, network-free, secret-free, and bounded.
  Networked package compatibility and container integration checks must state
  their prerequisites and run inside the intended disposable environment.
- Never run `.test/system/exec.sh` or its privileged playbooks directly on a
  workstation. Preserve their early container guards.
- Fake service facts and fake `systemctl` prove task logic only; report actual
  VM or hardware evidence separately, with remaining gaps in the validation ADR.

## Validation

Use the focused task for the changed fixture area and the root validation
matrix. Documentation-only edits need documentation checks. Python changes
require `go-task test:python` and `go-task lint:python`;
container apply and convergence changes require `go-task test:system` when
Docker is available. See the README command catalog for entry points.

## Done Criteria

- Fixture changes still support the smoke tests.
- Generated test workspace content was not mistaken for canonical config.
- No local runtime state was committed.
