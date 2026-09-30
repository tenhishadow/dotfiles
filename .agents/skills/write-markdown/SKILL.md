---
name: write-markdown
description: >-
  Write or revise repository Markdown, agent instructions, or skills. Keep
  canonical contracts, provider discovery, and shared lint rules aligned.
---

# Write Repository Markdown

## Scope

Run commands from the repository root; paths below are relative to that root,
including when loaded through a provider symlink. The root `AGENTS.md` owns
instruction and documentation rules; this workflow covers the edit and its
validation.

## Workflow

1. Identify the changed contract under the root instruction chain; use
   `.github/instructions/documentation.instructions.md` for review criteria.
2. Identify the canonical source. Edit generators instead of generated output,
   instruction owners instead of adapters, and canonical skills instead of
   their provider symlinks.
3. Check documented behavior against current code and actual test output. Keep
   public docs focused on repository contracts and reusable decisions. Follow
   the root privacy rule for host-specific evidence; historical context does
   not justify publishing private observations or unverified completion claims.
4. Document decisions, constraints, ownership, validation, and rollback that an
   operator needs. Reference the README command catalog and existing contracts
   instead of copying them into new tables.
5. For instructions and skills, use precise activation descriptions, concise
   workflows, and observable completion criteria. Verify provider-specific
   fields and discovery paths against current official documentation; preserve
   invocation policy and keep shared workflows portable.
6. Apply `.github/linters/.markdown-lint.yml`; fix content instead of adding
   ignores or rule disables. Use language-tagged fences and working links.
7. Run the `codespell` and `markdownlint-cli2` pre-commit hooks on changed files,
   then `go-task docs:instructions:check` and relevant generated-document checks.
   Include untracked Markdown and check relative links the checker does not
   parse. Documentation-only edits do not need runtime suites.

## Completion

Report the contract corrected, checks run, and blockers. Keep useful conclusions
in their canonical owner; diagnostic logs and session notes remain private.
