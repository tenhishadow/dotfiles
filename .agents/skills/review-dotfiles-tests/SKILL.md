---
name: review-dotfiles-tests
description: >-
  Review this dotfiles repository's tests and validation runners for meaningful
  assertions, isolation, determinism, DRY structure, and CI integration. Use
  for Python, Ansible, Neovim, container, Taskfile, or workflow test changes.
---

# Review Dotfiles Tests

## Scope

Run commands from the repository root; paths below are relative to that root.
Review test behavior and the production contract together. Report findings or
apply corrections according to the user's request; test review never requires
host apply.

## Workflow

1. Read the root `AGENTS.md` and every applicable ancestor `AGENTS.md` for each
   changed path, `docs/adr/0001-validation-strategy.md`, and the changed
   production behavior.
2. Check that every test observes a real contract and asserts outcomes rather
   than implementation details. For a regression fix, verify that the case
   fails with the broken behavior. Flag false-positive paths before style issues.
3. Review duplication with context. Prefer a data table and `subTest` for the
   same behavior across inputs; extract setup only when a shared helper makes
   multiple tests clearer. Reject speculative base classes and generic fixture
   frameworks.
4. Check Python-contract isolation: no network dependency, credentials, real
   user state, order coupling, unbounded subprocesses, or sleeps. For networked
   integration checks, verify explicit prerequisites, disposable state, and
   failure diagnostics instead of pretending the check is a pure unit test.
5. Inspect the real task graph and CI callers. Check environment overrides,
   concurrent dependencies, failure propagation, and skipped branches. For
   convergence, require zero changes and no hidden or rescued failures.
   Treat backend assertions and simulated commands as selection or task logic
   evidence, not proof of real service activation or VM clock recovery.
6. Check discovery and execution through the focused task,
   `go-task test:python`, `go-task lint:python`, and the appropriate CI check.
   Do not request JUnit, extra reporting actions, or a new runner without a
   concrete consumer.

## Completion

Report ranked findings with file locations, concrete failure cases, impact,
and the smallest valid correction. Separate observed failures from untested
risks. If there are no findings, state the reviewed contracts, executed checks,
and residual coverage gaps.
