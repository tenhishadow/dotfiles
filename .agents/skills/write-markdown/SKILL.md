---
name: write-markdown
description: >-
  Write or revise Markdown in this dotfiles repository, including operator
  docs, ADRs, AGENTS instructions, provider adapters, templates, and skills.
  Keep canonical sources, current behavior, and shared markdownlint rules aligned.
---

# Write Repository Markdown

## Scope

Run commands from the repository root; paths below are relative to that root,
including when loaded through a provider symlink. The root `AGENTS.md` owns
instruction and documentation rules; this workflow covers the edit and its
validation.

## Workflow

1. Read the root `AGENTS.md` and every applicable ancestor `AGENTS.md` for each
   changed path, then `.github/instructions/documentation.instructions.md`.
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
7. Run `go-task lint:markdown`, `go-task docs:instructions:check`, and relevant
   generated-document checks. Include untracked Markdown in validation and
   check relative links that the instruction-reference checker does not parse.

## Completion

Run `git diff --check`. Report the contract corrected, checks run, and blockers.
Keep provider adapters and skills aligned without expanding a documentation
task into a host apply or external publication.
