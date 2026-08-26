---
name: write-markdown
description: Write or revise repository Markdown that must pass the shared markdownlint and Super-Linter contract. Use for README files, docs, ADRs, AGENTS instructions, GitHub templates, or Markdown skills.
---

# Write repository Markdown

1. Read the root and nearest `AGENTS.md`. For documentation, also read
   `.github/instructions/documentation.instructions.md`.
2. Find the canonical source before editing generated content. Change its
   generator when one exists.
3. Keep the document concise and use one descriptive H1, sequential headings,
   blank lines around blocks, and language-tagged fences.
4. Fix the content instead of adding ignores, inline disables, or duplicate
   rule configuration.
5. Run `go-task lint:markdown`, the relevant generated-document check, and
   `go-task docs:instructions:check`.
6. Finish with `git diff --check` and report any check that could not run.
