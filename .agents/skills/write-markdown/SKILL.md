---
name: write-markdown
description: Write or revise repository Markdown that must pass the shared markdownlint and Super-Linter contract. Use for README files, docs, ADRs, AGENTS instructions, GitHub templates, or Markdown skills.
---

# Write repository Markdown

1. Read the root and nearest `AGENTS.md`. For documentation, also read
   `.github/instructions/documentation.instructions.md`.
2. Find the canonical source before editing generated content. Change its
   generator when one exists.
3. Treat the repository and tool output as source material. Document decisions,
   non-obvious constraints, and gotchas instead of caching layout or command
   facts that are cheap to inspect.
4. For agent instructions, make descriptions and context pointers name the
   conditions that should load the guidance. Keep common steps inline, disclose
   branch-specific detail through direct references, and give each workflow an
   observable completion criterion.
5. Keep the document concise and use one descriptive H1, sequential headings,
   blank lines around blocks, and language-tagged fences.
6. Fix the content instead of adding ignores, inline disables, or duplicate
   rule configuration.
7. Run `go-task lint:markdown`, the relevant generated-document check, and
   `go-task docs:instructions:check`.
8. Finish with `git diff --check` and report any check that could not run.
