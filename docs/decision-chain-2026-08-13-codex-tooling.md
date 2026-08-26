# Portable Codex Tooling Decision Chain

Date: 2026-08-13

Status: accepted; amended 2026-08-26

This record explains why portable agent configuration is separated from local,
writable account state. Current architecture and validation decisions live in
`docs/architecture.md` and `docs/adr/0001-validation-strategy.md`.

## Claim And Falsifier

Claim: common Codex profiles, hooks, skills, launchers, and exact npm dependency
graphs can be shared across workstations without committing credentials or
turning writable Codex state into repository content.

Falsifier: reject the rollout if a tracked payload contains a credential or
machine-only path, if the default play would replace the live
`~/.codex/config.toml`, if a launcher performs a session-time package download,
or if check mode reaches a managed or privileged host.

The checks are path-only secret scanning, TOML and JSON parsing, npm lock
inspection, black-box hook tests, Ansible validation, and the repository's
native validation tasks.

## Evidence

- Codex loads task profiles from `~/.codex/<name>.config.toml`, above the user
  config layer. The profile files therefore stay small and deterministic.
- The current user config is an owner-only regular file. Its key structure
  includes Codex-managed project and hook trust state plus local Grafana
  environment values, so linking it into Git would mix portable policy with
  writable machine state.
- Context7, Playwright, and the Codex CLI are frozen by npm lockfiles whose
  resolved artifacts use the HTTPS npm registry and include integrity data.
- MCP and CLI wrappers execute only already-installed local binaries. Package
  installation remains an explicit `go-task codex:install` operation and uses
  `--ignore-scripts`.
- The portable hook is dependency-free, reads only the hook event from standard
  input, and emits generic denial reasons. Standard-library tests exercise its
  real JSON interface under normal and optimized Python.

## Alternatives

1. Link `~/.codex/config.toml` directly. Rejected because Codex writes trust
   state there and the host keeps local Grafana values in that file.
2. Add a merge generator or a new Ansible seed-file abstraction. Rejected for
   now because it adds ownership and migration logic for one file; the checked
   example plus local config is smaller and easier to recover.
3. Use `npx -y` from MCP configuration. Rejected because it downloads mutable
   dependency graphs during an agent session.
4. Enable every MCP server and write-capable app by default. Rejected because
   it increases startup work, context pressure, and the accidental-write
   surface.

## Decision

- Keep `~/.codex/config.toml` local, regular, and owner-only. Never map it from
  this repository. Use `dotfiles/.codex/config.example.toml` only to bootstrap
  a new host, then add that host's values locally.
- Link immutable task profiles, hooks, the pinned Ponytail skill, launchers,
  package manifests, and lockfiles through the existing user-level mapping.
- Keep public SSH and GnuPG config paths readable while the Bash hook blocks
  direct references to `.env`, Kubernetes config, GnuPG private keys, the
  Grafana token-file variable, and non-public `.ssh` paths.
- Keep Context7 and the official OpenAI documentation server in the portable
  example. Keep Playwright, Grafana, and GitHub writes opt-in through dedicated
  profiles.
- Install exact lock-recorded artifacts only through explicit Taskfile targets;
  do not download dependencies when Codex starts.

## Verification

Use the repository validation workflow rather than recording machine-specific
rollout evidence in Git. `go-task test:agent-tooling` parses all managed TOML
and JSON, checks exact npm manifest/lock agreement and artifact integrity, and
tests hook allow and deny decisions through its JSON interface. Also run the
user-level dotfiles check. Broad changes require `go-task verify`, which adds
container convergence and Super-Linter. No privileged playbook substitutes for
an unavailable isolated check.

## Rollback

Revert the scoped change in version control and reapply the user-level
playbook. Remove only mappings introduced by that change. The live
`~/.codex/config.toml`, authentication, histories, databases, hook trust, and
local service values remain outside the managed payload.

## Residual Risk

- A new host needs an explicit one-time copy and local review of the example
  config; later example changes are intentionally not merged automatically.
- `go-task codex:install` requires npm network access and trusts the exact
  registry artifacts represented by the checked lockfiles.
- Hook trust remains a Codex-controlled local decision and must be reviewed
  again whenever a managed hook changes.
