---
name: review-dotfiles-tests
description: Review tests and validation code in this dotfiles repository for correctness, DRY structure, determinism, maintainability, and CI integration. Use for Python tests, Ansible assertions, Neovim smoke tests, container convergence checks, or changes to their Taskfile and GitHub Actions runners.
---

# Review Dotfiles Tests

1. Read the root and nearest `AGENTS.md`,
   `docs/adr/0001-validation-strategy.md`, and the changed production behavior.
2. Check that every test observes a real contract, fails on the pre-fix case,
   and asserts outcomes rather than implementation details. Flag false-positive
   paths before style issues.
3. Review duplication with context. Prefer a data table and `subTest` for the
   same behavior across inputs; extract setup only when a shared helper makes
   multiple tests clearer. Reject speculative base classes and generic fixture
   frameworks.
4. Check isolation: no network dependency, credentials, machine-local paths,
   order coupling, mutable shared state, unbounded subprocesses, or sleeps.
   Require bounded subprocesses and useful failure diagnostics.
5. Check discovery and execution through the focused task,
   `go-task test:python`, `go-task lint:python`, and the appropriate CI check.
   Do not request JUnit, extra reporting actions, or a new runner without a
   concrete consumer.
6. Report ranked findings with file locations, impact, and the smallest valid
   correction. If there are no findings, state which commands and contracts
   were checked.
