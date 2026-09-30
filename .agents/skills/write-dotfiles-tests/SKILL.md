---
name: write-dotfiles-tests
description: >-
  Add or fix regression tests in this dotfiles repository when behavior changes
  or a coverage gap is demonstrated. Covers Python and CLI contracts, Taskfile
  runners, Ansible assertions, Neovim smoke checks, and container convergence.
  Use review-dotfiles-tests for review without implementation.
---

# Write Dotfiles Tests

## Scope

Run commands from the repository root; paths below are relative to that root.
Use the validation layers in `docs/adr/0001-validation-strategy.md`; ordinary
reversible documentation or formatting changes do not need new tests.

## Workflow

1. Read the root `AGENTS.md` and every applicable ancestor `AGENTS.md` for each
   changed path, then read the changed behavior and its current callers.
2. Reproduce the missing behavior and choose the lowest existing validation
   layer that can observe it. Prefer native Ansible assertions, existing smoke
   checks, and generated-output comparisons before Python.
3. Use the existing standard-library `unittest` suite for repository logic and
   CLI contracts that native checks cannot cover clearly. Exercise the real
   command boundary; replace external side effects with temporary fixtures or
   fake executables, not the behavior under test.
4. Follow `.test/AGENTS.md` for discovery and fixture conventions. Include the
   smallest negative case that would fail before the fix. Verify the broken
   behavior in a temporary fixture or disposable checkout without overwriting
   existing work.
5. Keep Python contracts deterministic, network-free, secret-free, and
   independent of execution order. Use temporary fixtures and bounded
   subprocesses for CLI and hook I/O; avoid sleeps and real user state.
6. Keep networked compatibility checks and disposable container integration
   explicit. Assert backend selection separately from daemon operation; fake
   facts and fake commands cannot prove VM clock recovery or hardware behavior.
7. Add a narrow task to `Taskfile.yml` only when it is useful on its own.
   Ensure the aggregate `go-task test:python` discovers every Python test and
   update the README command table when the public task surface changes.

## Completion

Show that the regression case fails for the broken behavior and passes with the
fix. Run the focused test and the relevant checks from the root validation
matrix, including `go-task test:python` and `go-task lint:python` for Python
test changes. Finish with `git diff --check` and report coverage limits.
