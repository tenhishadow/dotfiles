---
name: review-dotfiles-tests
description: >-
  Review repository tests and validation runners for meaningful assertions,
  isolation, and CI coverage. Use when reviewing tests, Taskfile validation,
  or workflow changes.
---

# Review Dotfiles Tests

## Scope

Run commands from the repository root; paths below are relative to that root.
Review test behavior and the production contract together. Report findings or
apply corrections according to the user's request. Follow the root `AGENTS.md`
review rules and `.test/AGENTS.md` fixture contracts.

## Workflow

1. Trace the changed production behavior and test callers. Consult
   `docs/adr/0001-validation-strategy.md` when evaluating the validation layer.
2. Check that every test observes a real contract and asserts outcomes rather
   than implementation details. For a regression fix, verify that the case
   fails with the broken behavior. Flag false-positive paths before style issues.
3. Review duplication with context. Prefer a data table and `subTest` for the
   same behavior across inputs; extract setup only when a shared helper makes
   multiple tests clearer. Reject speculative base classes and generic fixture
   frameworks.
4. Check isolation and clean-checkout behavior against `.test/AGENTS.md`.
   Required tracked data must fail clearly when malformed; optional installed
   runtime state must not silently change which contracts are exercised.
   Networked integration checks need explicit setup and failure diagnostics.
5. Inspect the real task graph and CI callers. Check environment overrides,
   concurrent dependencies, failure propagation, and skipped branches. For
   convergence, require zero changes and no hidden or rescued failures.
   Treat backend assertions and simulated commands as selection or task logic
   evidence, not proof of real service activation or VM clock recovery.
6. Check discovery through the focused task, `go-task test:python`, and CI;
   use the root matrix to select execution, rather than rerunning every suite.
   Do not request JUnit, extra reporting actions, or a new runner without a
   concrete consumer.

## Completion

Use the root review format and suggest the smallest valid correction. If there
are no findings, state the reviewed contracts, checks, and coverage gaps.
