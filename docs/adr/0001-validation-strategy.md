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

Validation has four layers:

| Layer | Mechanism | Contract |
| ----- | --------- | -------- |
| Static | Existing lint, documentation, instruction, and managed-path checks | Source and repository contracts are structurally valid. |
| Input | `ansible.builtin.assert` in each role plus `.test/role_contracts.yml` | Public variables are valid before mutation; destructive path and filename boundaries reject known-bad inputs. |
| Observable state | `.test/system/verify.yml` in a disposable Arch container | Managed links, files, ownership, modes, selected content, policy JSON, and container guards match the applied configuration. |
| Convergence | `ansible.posix.json` plus `.test/assert_ansible_convergence.py` | A second run of each playbook reports zero changes, failures, ignored failures, rescued failures, and unreachable hosts. |

`go-task test:system` first applies the aggregate `go-task all` order with
package and AUR installation skipped. It then verifies observable state and
runs the dotfiles, system, and browser-policy playbooks separately for the
machine-readable convergence check.

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

## Framework Choice

No additional Python test dependency is used. The repository already has the
required Ansible collection, and Python's standard `json` module is sufficient
for callback validation.

The following frameworks are rejected for the current scope:

- `pytest`: there is no Python application or fixture graph that justifies an
  additional runner.
- Testinfra: the assertions operate on one local disposable target and are more
  directly expressed with native Ansible modules.
- Molecule: the repository already owns the container lifecycle, converge
  playbooks, and task entry points; adopting a scenario lifecycle would
  duplicate them.

## Residual Gaps

The unprivileged container deliberately does not validate:

- systemd service enablement, restart handlers, or boot behavior;
- virtual-machine-specific time synchronization behavior;
- host Docker daemon configuration and effective group access;
- AUR builds or installation of the full workstation package manifest;
- hardware-specific laptop behavior.

Package target availability and container-safe rendering are still checked.
The remaining behavior is covered by explicit host check/apply commands and
manual review appropriate to a personal workstation repository.

## Escalation Criteria

Add the smallest missing layer only after a demonstrated coverage gap:

- add a native Ansible assertion when a new observable invariant is introduced;
- add standard-library `unittest` when reusable Python logic has multiple input
  cases that the command-level checks cannot exercise clearly;
- add Testinfra when the same remote-state assertions must run across multiple
  independently managed hosts;
- add Molecule or a VM runner when two or more maintained lifecycle scenarios
  require create, converge, reboot or side-effect, verify, and destroy phases.

Any heavier runner must replace duplicated test machinery rather than sit
beside it, and its dependency and CI cost must be recorded in a later ADR.

## Consequences

The main privileged smoke test is slower than syntax validation but proves both
state and convergence in one disposable environment. Failures identify the
affected playbook from separate JSON recaps. Host-only service and hardware
behavior remains explicit instead of being simulated with misleading container
facts.
