---
applyTo: "dotfiles/.config/nvim/**/*,.test/nvim/**/*"
---

# Neovim Review Instructions

The canonical editor contract lives in `dotfiles/.config/nvim/AGENTS.md`.
Use `.test/AGENTS.md` for fixture and test-runner rules. Review changes against
those contracts rather than adding alternate configuration inventories.

- Trace a cold install and the first buffer through bootstrap, filetype
  detection, and lazy loading. Check lockfile preservation and compatibility
  gates against the plugin revisions actually selected.
- Trace language, formatter, linter, and keymap changes back to their canonical
  inventories. Check generated documentation and unknown-tool detection
  instead of maintaining another list in review instructions.
- Inspect save-triggered side effects separately from manual commands.
  Buffer formatters must not expand project globs, and asynchronous failures
  must reach their callbacks. Project scanners remain explicit operations.
- Check missing-tool behavior: ordinary local runs may skip optional parsers;
  required CI mode must fail on missing tools, parsers, or a success marker.
  Startup must not silently install external tooling.
- Check that tests override inherited HOME and XDG variables and operate on a
  copied config. Dependency refresh may copy back only the intended lockfile.
- Select smoke, startup, core-compatibility, Mason, and generated-keymap checks
  from the local `AGENTS.md` according to the behavior changed. A core-only
  simulation does not prove an older Neovim binary works; documentation-only
  changes need documentation checks.
