# Repository Instructions

@AGENTS.md

Repository skills are exposed through `.claude/skills/` symlinks to the
canonical `.agents/skills/` directories. Edit the canonical targets. The root
instruction map identifies the nested `AGENTS.md` files to read before editing
their paths; the root import alone does not load every nested instruction.
