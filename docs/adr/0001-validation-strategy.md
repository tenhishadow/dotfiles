# ADR 0001: Repository Validation Strategy

- Status: Accepted
- Date: 2026-08-26

## Context

This repository applies three different kinds of state: user-owned dotfiles,
privileged Arch Linux workstation configuration, and root-owned application
policies. Syntax and check mode catch many errors, but neither proves that the
applied state is correct or that a second apply is idle.

The validation path should remain small, reviewable, and usable by humans and
AI agents without introducing a second orchestration framework.

## Decision

Validation has five layers:

| Layer | Mechanism | Contract |
| ----- | --------- | -------- |
| Static | Existing lint, documentation, instruction, and managed-path checks | Source and repository contracts are structurally valid. |
| Logic and CLI contracts | pytest discovered by `go-task test:python` | Reusable validators, security-hook I/O, and real Taskfile/command boundaries accept valid inputs and reject known-bad inputs. |
| Input | `ansible.builtin.assert` in each role plus `.test/role_contracts.yml` | Public variables are valid before mutation; destructive path and filename boundaries reject known-bad inputs. |
| Observable state | `.test/system/verify.yml` in a disposable Arch container | Managed links, files, ownership, modes, selected content, policy JSON, and container guards match the applied configuration. |
| Convergence | `ansible.posix.json` plus `.test/assert_ansible_convergence.py` | A second run of each playbook reports zero changes, failures, ignored failures, rescued failures, and unreachable hosts. |

`go-task test:system` first applies the aggregate `go-task all` order with
package and AUR installation skipped. It then verifies observable state and
runs the dotfiles, system, and browser-policy playbooks separately for the
machine-readable convergence check. The aggregate and system second run use
`CI=false`, with assertions on the actual role facts, so CI guards cannot hide
a broken container guard.

Before that aggregate, focused container contracts validate Chrony syntax,
safe conflict-unit masking, and Node.js provider replacement. The native role
contract also checks time-backend selection for VMs, physical hosts, disabled
features, and guarded environments. These tests do not run a real VM clock or
prove NTP synchronization after suspend.

The harness exits before package installation or Ansible execution unless
`systemd-detect-virt` confirms that it is running inside a container.

The package manifest is checked against the current Arch package database in a
single query. This is an upstream compatibility check, not a reproducible unit
test: Arch Linux and its official container image are rolling surfaces.

Optional local mirrors are transport overrides, not dependency-resolution
inputs. The harness may load an untracked env file for pacman and Python, while
public upstream sources remain the default. Python mirror mode exports exact
versions and hashes from `uv.lock`, installs them through the configured PEP
503 index, and disables later project syncs. This avoids rewriting the shared
lock file with a machine-local registry or artifact URL.

Check mode remains a useful pre-apply smoke test. It is not considered proof of
convergence because unsupported modules may skip work and predicted changes do
not prove the resulting state.

## Python And Lint Ownership

[pytest](https://docs.pytest.org/en/stable/explanation/goodpractices.html) is the
single Python test runner. `pyproject.toml` owns discovery and imports; `uv.lock`
owns resolved dependencies. Use plain functions and assertions, parameterize
independent input cases, and reuse built-in temporary-path, monkeypatch, and
capture fixtures. Shared fixtures live in `.test/conftest.py`; specialized setup
stays beside its tests. Do not add a base-class hierarchy or a second runner.

Follow [Google Python conventions](https://google.github.io/styleguide/pyguide.html)
for naming, imports, readable functions, and useful docstrings. Ruff owns
80-column formatting, import order, Google docstring syntax, and pytest-style
checks. Descriptive test names need no repetitive docstrings. Pylint owns
additional code diagnostics; `.github/linters/.python-lint` is shared everywhere.
The Super-Linter Ruff adapter extends `.ruff.toml` instead of copying its rules.

Pre-commit owns Python lint/format, spelling, Markdown, YAML, shell, and workflow
checks. Python hooks use the locked uv environment; `go-task lint:python`
selects those same hooks. External hook revisions are immutable SHAs with
version comments, refreshed by the weekly dependency updater. PR validation
checks the committed versions and configuration; it does not query latest
versions or upgrade dependencies during a test run.

## CI Execution

On pull requests, GitHub Actions first validates the current title through the
shared local commitlint action. It then runs `go-task ci:static`: whitespace,
instruction references, pre-commit hooks, Python regression tests,
Ansible semantics and lint, and native role contracts. Ruff and Pylint use the
locked project environment. The same task is part of `go-task verify:fast`, so
CI does not maintain a second implementation of those checks.

Complementary Super-Linter checks wait for the static gate. Integration checks
wait for both lint stages, so a lint failure cannot start Arch convergence or
Linux/macOS installation. This sequencing adds the Super-Linter duration to the
successful critical path while avoiding integration minutes on lint failures.
Path filters select Neovim, disposable Arch convergence, and Linux/macOS user
installation checks. Scheduled runs cover rolling Arch dependencies even
without repository changes; pushes to master retain post-merge verification.
A final `ci` job fails on upstream failure or cancellation while accepting
deliberate path skips.

The separate required `pr-title` check also uses the shared action and handles
title edits without rerunning integration. After correcting an initially invalid
title, rerun the failed CI workflow. The action reads the current title from the
GitHub API, so a rerun does not validate stale event text.

Optional review automation runs after successful `ci` and is not one of its
prerequisites. Review availability cannot create a cycle or replace validation.

Super-Linter supplies complementary checks through the same
`.github/super-linter.env` locally and in CI; it does not repeat canonical
pre-commit checks or lint intermediate commits. The PR title becomes the squash
commit. Native Neovim updater tests use the same locked pytest runner in the
Neovim job, where the required executable is installed.

## Test Maintenance

For each PR, explain briefly which changed contract needs tests and why the
selected evidence is sufficient. Documentation or formatting changes may need
only their existing checks. Reviewers, including AI agents, assess the same
criteria rather than asking for more tests by default:

- Identify the observable failure each test detects. Prefer input/output,
  resulting state, and real command boundaries over source spelling, private
  layout, or reimplemented production expressions. Mock external effects,
  not the behavior being asserted.
- Keep one owner for each invariant. Remove duplicated checks, cases already
  covered by lint, and assertions with no meaningful failure. Keep essential
  Ansible runtime validation before mutation; it protects real operators.
- Before deleting a test, identify replacement coverage or a retired contract.
  Age alone does not make a regression test obsolete. Preserve explicit owner
  policies and reproduce a negative case when changing a safety boundary.
- Parameterize meaningful alternatives without multiplying equivalent cases.
  Count collected cases separately from test functions; a larger count is not
  evidence of better coverage. Inspect durations when changing test cost.
- Keep network, tools, temporary state, and timeouts explicit. Required runtime
  coverage needs an owning CI job that installs the tool and executes it.
  The optional MPlayer parse probe runs locally when installed; its skip is not
  CI coverage. Remove obsolete skips when supported behavior changes.

pytest replaces Python test scaffolding; native Ansible and Neovim tests still
exercise their own engines. Testinfra or Molecule would currently duplicate the
single disposable target and its existing lifecycle. Add another framework only
to replace demonstrated duplication or cover an otherwise untested boundary.

## Residual Gaps

The unprivileged container deliberately does not validate:

- systemd service enablement, restart handlers, or boot behavior;
- virtual-machine-specific time synchronization behavior;
- host Docker daemon configuration and effective group access;
- AUR builds or installation of the full workstation package manifest;
- hardware-specific laptop behavior.

Package target availability and container-safe rendering are still checked.
The remaining behavior requires separately authorized host or VM check/apply
verification; unavailable Docker never authorizes using the workstation as a
replacement test target.

## Consequences

The main privileged smoke test is slower than syntax validation but proves both
state and convergence in one disposable environment. Failures identify the
affected playbook from separate JSON recaps. Host-only service and hardware
behavior remains explicit instead of being simulated with misleading container
facts.
