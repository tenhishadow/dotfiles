---
name: write-dotfiles-tests
description: Write or update tests for this dotfiles repository, including Python contract tests, Ansible assertions, Neovim smoke coverage, and container convergence checks. Use when behavior or a regression contract changes under .test/, roles/, dotfiles/, or Taskfile.yml.
---

# Write Dotfiles Tests

1. Read the root and nearest `AGENTS.md`, then read
   `docs/adr/0001-validation-strategy.md`.
2. Reproduce the missing behavior and choose the lowest existing validation
   layer that can observe it. Prefer native Ansible assertions, existing smoke
   checks, and generated-output comparisons before Python.
3. Use standard-library `unittest` only for reusable Python logic with multiple
   meaningful input cases. Do not add another runner, fixture framework, base
   test class, or shared helper module without demonstrated reuse.
4. Name files `test_*.py`, classes after the contract, and methods
   `test_<behavior>_<condition>`. Keep setup local, use `subTest` for data tables,
   and include the smallest negative case that would fail before the fix.
5. Test public behavior and real boundaries. Keep tests deterministic,
   network-free, secret-free, independent of execution order, and free of
   blocking sleeps. Prefer black-box subprocess coverage for CLI and hook I/O.
6. Add the narrow task to `Taskfile.yml` only when it is useful on its own.
   Ensure the aggregate `go-task test:python` discovers every Python test and
   update the README command table when the public task surface changes.
7. Run the focused test, `go-task test:python`, `go-task lint:python`, and
   `git diff --check`. Use `go-task verify` for cross-layer or CI changes.
