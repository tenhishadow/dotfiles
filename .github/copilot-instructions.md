# Copilot Code Review

Use the root `AGENTS.md` Code Review Rules and the instructions for changed
paths. Read `CONTRIBUTING.md` only for contribution or release changes, and
load relevant skills on demand. Repository contracts belong to those canonical
sources; this file controls Copilot's review presentation.

- Start with the diff and directly affected callers. Expand the search when a
  concrete dependency or risk requires it, not to produce a repository audit.
- Keep findings concise and attach each to the smallest useful changed range.
  Group duplicate symptoms of one cause; do not repeat passed checks or narrate
  exploration. If no actionable issue remains, say so briefly.
- Offer a minimal GitHub suggestion when the surrounding code proves the fix.
  For an uncertain or multi-file fix, describe the required behavior and check
  instead of inventing a patch. Suggestions remain subject to owner review.
- Respect explicit owner decisions in `dotfiles/AGENTS.md`, including SSH
  policy. Do not turn intentional preferences into unsolicited hardening work.
- Request only checks needed for the changed behavior. Never apply host
  configuration or start a cloud-agent fix, another review, or an external tool
  session merely to complete a review.
