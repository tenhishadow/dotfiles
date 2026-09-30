# Copilot Repository Guidance

Read the root `AGENTS.md` and path-applicable nested `AGENTS.md` files before
working. They own the repository contracts; the README `Common Tasks` table
owns command discovery. Path-specific review guidance lives in
`.github/instructions/`.
For branches, commits, PRs, releases, and agent handoff, follow
`CONTRIBUTING.md`; preserve the selected base and existing work.

Default `go-task` applies user dotfiles to the current home. It is not a test;
`go-task all` additionally applies privileged layers. Follow the user's
execution scope and use the root validation matrix instead of applying host
configuration to validate repository edits. Documentation-only changes need
documentation checks, not the full Docker aggregate.

When reviewing:

- Report actionable defects introduced or exposed by the change. Give the
  location, triggering condition, and concrete impact; inspect callers and
  guards before claiming a regression.
- Prioritize unsafe destination replacement, scope or privilege escalation,
  secret/runtime-state exposure, non-idempotent apply behavior, and tests that
  write outside their disposable environment.
- Check that the default workflow remains sudo-free and limited to
  `playbook_install.yml`; system and browser-policy apply stay explicit.
- Compare changed behavior with its canonical role or editor contract, then
  check whether the relevant observable behavior is tested. Passing lint,
  check mode, or simulated facts alone does not prove live VM or hardware
  behavior.
- Request documentation changes only where an existing contract becomes
  inaccurate or a new operator decision needs explanation. Do not require
  restating unchanged rules across every adapter or historical report.
- Avoid speculative rewrites, style-only findings already covered by linters,
  and invented validation results. State unresolved assumptions as such.
