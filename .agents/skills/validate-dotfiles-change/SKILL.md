---
name: validate-dotfiles-change
description: >-
  Select and run repository checks after a change or CI failure. Use to verify
  behavior, investigate a failed check, or assess validation coverage.
---

# Validate Dotfiles Changes

## Scope

Run commands from the repository root; paths below are relative to that root,
including when this skill is loaded through a provider symlink. The root
`AGENTS.md` validation matrix owns check selection;
`docs/adr/0001-validation-strategy.md` explains the evidence and environment
boundaries.

## Workflow

1. Inspect the affected diff and untracked files under the root instruction
   chain; identify which behavior changed before selecting checks.
2. Verify changed external behavior against the owning primary source and the
   installed or locked version. Attach a date or version to facts that can
   change, and label unresolved claims as unverified.
3. Map each changed contract to the smallest required check in the matrix.
   Use `go-task verify` for broad cross-layer changes; run independent checks
   separately if a missing prerequisite blocks the aggregate. Run the relevant
   pre-commit spelling and format hooks before expensive jobs.
4. Use locked dependencies. Do not refresh locks to make validation pass unless
   upgrades are part of the user's request. Run apply behavior only in the
   disposable test harness, never as a fallback on the local workstation.
5. Add a regression assertion only for changed behavior or a demonstrated gap.
   Reuse the existing assertion, smoke, or generated-output layer. For a CI
   failure, reproduce its checkout and setup: an ignored local installation
   must not decide whether tracked manifests are valid. Check missing optional
   runtime state separately from malformed required input.
6. Run the selected checks and `git diff --check`; include new files in lint
   coverage even before they are tracked. Resolve failures, then rerun the
   affected checks; do not repeat successful checks without a relevant change.

## Completion

Report passed checks, failed checks, and exact environment blockers separately.
Distinguish check-mode predictions, backend-selection assertions, container
convergence, and actual VM or hardware evidence. Do not claim a skipped check
passed or substitute host apply for unavailable Docker.
