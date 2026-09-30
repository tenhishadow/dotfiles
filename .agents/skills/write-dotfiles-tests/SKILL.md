---
name: write-dotfiles-tests
description: >-
  Add or fix regression coverage for changed behavior or a demonstrated gap in
  this repository. Use existing native checks and standard-library tests.
---

# Write Dotfiles Tests

## Scope

Run commands from the repository root; paths below are relative to that root.
The root `AGENTS.md` selects checks; `.test/AGENTS.md` owns fixtures and runners.
Use `docs/adr/0001-validation-strategy.md` when choosing a validation layer.
Ordinary documentation or formatting changes do not need new tests.

## Workflow

1. Trace the changed behavior and its current callers.
2. Reproduce the missing behavior and choose the lowest existing validation
   layer that can observe it. Prefer native Ansible assertions, existing smoke
   checks, and generated-output comparisons before Python.
3. Use the existing standard-library `unittest` suite for repository logic and
   CLI contracts that native checks cannot cover clearly. Exercise the real
   command boundary; replace external side effects with temporary fixtures or
   fake executables, not the behavior under test.
4. Include the smallest negative case that fails before the fix. Reproduce it
   in a temporary fixture or disposable checkout. Supply test inputs explicitly:
   optional ignored runtime installs may be absent, while malformed tracked
   manifests must still fail validation.
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

Show that the regression case fails before the fix and passes after it. Run
the focused test and root validation matrix checks; report coverage limits.
