---
applyTo: "**/*.md"
---

# Documentation Review Instructions

Follow the root `AGENTS.md` documentation-sync contract and Code Review Rules.
Use `.agents/skills/write-markdown/SKILL.md` when editing documentation.

- Trace each changed claim to its owning code, task, or primary source. Update
  the canonical document that becomes inaccurate; do not demand unrelated
  README, ADR, or historical-report edits for every implementation change.
- Keep instructions scoped to decisions the agent needs in that directory.
  Remove obsolete requirements after verifying current behavior rather than
  preserving them as universal prohibitions.
- Flag validation instructions that run an apply command against the user's
  home or workstation. Distinguish local edits, dry runs, container apply,
  and separately authorized host changes.
- Follow the root privacy rule for investigations and identifying observations.
  Keep public decision history about reusable repository behavior; preserve
  private diagnostic evidence outside the checkout.
- Check generated manuals against their generator; Neovim keymaps follow
  `dotfiles/.config/nvim/AGENTS.md`.
- Check new untracked Markdown as well as tracked documents. Validate relative
  links and distinguish generated-output checks from behavioral proof.
- For changed runtime contracts, cover feature-disable behavior, ownership of
  managed paths, validation limits, and rollback where relevant.
- Keep skills scoped to real workflows, with accurate activation descriptions
  and observable completion criteria. Edit canonical `.agents/skills/`
  content; provider adapters and symlinks must not duplicate it.
- Select Markdown, reference, and applicable generated-document checks for
  documentation-only changes. Do not require host apply, runtime suites, or
  Docker merely because prose lives under a role or automation directory.
