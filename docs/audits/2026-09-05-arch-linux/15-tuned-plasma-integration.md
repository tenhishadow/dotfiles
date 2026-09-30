# TuneD and Plasma Integration

Implementation on 2026-09-05 follows explicit user approval to connect the
existing TuneD CPU power management to Plasma's profile selector. The scoped
proposal is [BF-06 in the power investigation](08-boot-firmware-power-investigation.md).

## Configuration

The official Arch `tuned-ppd` 2.28.0-1 package supplies the Power Profiles
D-Bus compatibility API consumed by Plasma. Existing TuneD 2.28.0-1 remains
the power-management owner. The package transaction added only `tuned-ppd`;
all dependencies were already installed. Pacman also recreated its missing
`/var/cache/pacman/pkg` directory with root ownership and mode `0755`.

The applied mapping is:

| Plasma mode | TuneD profile on AC | TuneD profile on battery |
| --- | --- | --- |
| Power saver | `powersave` | `powersave` |
| Balanced | `balanced` | `balanced-battery` |
| Performance | `workstation-performance` | `workstation-performance` |

The custom performance profile inherits `balanced` and selects CPU energy
preference `performance` plus the firmware's `performance` platform profile.
This host retains the `powersave` governor of its active Intel P-state driver.
It avoids the memory/writeback, disk read-ahead, and minimum-CPU-performance
changes in upstream `throughput-performance`.

Power saver retains upstream behavior, including disabling turbo and enabling
Wi-Fi power saving. No competing power-management daemon was active during
preflight. Firmware supports `low-power`, `balanced`, and `performance`.

The packaged bridge configuration enables battery detection and ACPI profile
monitoring. Actual unplug/replug and firmware-hotkey behavior require a later
physical test; no battery-life or performance benchmark is claimed.

## Applied State and Functional Verification

The scoped Ansible apply used `--tags tuned` and the JSON extra variable
`{"system_packages_enabled":false}` after installing the bridge package.
It changed only TuneD directories, the two configuration files, and related
services. Both `tuned.service` and `tuned-ppd.service` are enabled and running
with exit status 0. The existing user `plasma-powerdevil.service` was restarted
once so it could discover the new backend; no session logout or reboot was
needed.

Plasma's own D-Bus interface now exposes all three profile choices. A live
test called its `setProfile` method as the desktop user, first selecting
performance and then restoring balanced in an unconditional cleanup block.
There were no application profile holds before testing.

| Observation | Performance test | Restored state |
| --- | --- | --- |
| Plasma and PPD profile | `performance` | `balanced` |
| TuneD profile | `workstation-performance` | `balanced` |
| EPP on all 20 CPU policies | `performance` | `balance_performance` |
| CPU governor | `powersave` | `powersave` |
| Firmware platform profile | `performance` | `balanced` |

All 16 checked CPU-limit, disk read-ahead, and memory/writeback controls
remained unchanged during the performance test. After returning to balanced,
all 57 settings captured before installation matched exactly. No new TuneD
or bridge warnings were logged during this work.

The installed TuneD parser accepted the AC and battery mappings and verified
that every referenced profile exists. Power saver was verified by parser and
profile inspection, without activating its Wi-Fi and other device changes.
Battery transitions and firmware hotkeys were not physically tested.

The repository now owns the feature behind `system_tuned_enabled`, disabled
by default and enabled in this host's inventory. The bridge package is only
installed through the gated feature, avoiding D-Bus activation on a host
that never opted in. Unchanged applies do not reset the selected profile.
TuneD now reports manual profile selection because the PPD bridge owns the
desktop choice and AC/battery mapping; automatic TuneD recommendation is no
longer the profile-selection owner.

## Repository Validation

Passed: Ansible lint, YAML lint, Python checks, Markdown checks, instruction
references, managed-path checks, and `git diff --check`. The scoped live
`go-task system:check` and a second actual scoped apply both reported zero
changes and zero failures. Existing container assertions cover both new
configuration files and their ownership.

The broad validation commands were attempted and exposed unrelated existing
blockers:

- `go-task verify` reached the Renovate prerequisite check, which requires
  Node.js `^24.11.0`; the active runtime was `v22.23.2`. Earlier static and
  pre-commit stages passed. Later aggregate stages were not reached.
- `go-task test:system` stopped at its full package-manifest check because
  `talhelper` was unavailable in the fresh official Arch repositories. It
  did not reach the repository-wide container apply or convergence checks.

These unrelated toolchain/package policies were not changed as part of the
power-profile integration.

A separate focused test passed in a disposable Arch container using official
`tuned` and `tuned-ppd` packages. It applied the actual repository's `tuned`
tasks with CI guards, checked both files' root ownership, `0644` permissions,
mapping and inherited profile contents, then reapplied the same tasks with
zero changes or failures. Container service management was skipped as
intended; the actual running services and profile transitions were verified
on the laptop above.

## Backup and Rollback

The previous existing TuneD configuration and state files were copied and
verified before mutation in:

`/root/tuned-plasma-backup-20260905T110416Z-ApoHGH`

This root-owned directory has mode `0700` and is outside the repository. It
also records absent target paths, prior service/package state, the newly
installed package's default mapping, and 57 selected nonsecret CPU, platform,
storage, and memory settings. Before integration, TuneD was enabled and
active, with automatic profile selection and `balanced` active on AC.

To roll back the integration, first select balanced, then stop and mask
`tuned-ppd.service`; masking prevents D-Bus from restarting the installed
bridge. Keep the existing TuneD service enabled. `sudo tuned-adm auto_profile`
restores the former automatic selection mode; verify that it selects balanced
on AC. Restart the user's PowerDevil service to refresh desktop capabilities.
The backup records the original file presence and contents if configuration
restoration is needed. These rollback steps have not been executed.

Disable `system_tuned_enabled` in the host inventory before a future system
apply if abandoning the integration. That flag stops management; it does not
uninstall packages or stop services already enabled by an earlier apply.

No commits or pushes were made.

## Sources

- [Official Arch package](https://archlinux.org/packages/extra/any/tuned-ppd/)
- [TuneD 2.28 mapping](https://github.com/redhat-performance/tuned/blob/v2.28.0/tuned/ppd/ppd.conf)
- [KDE PowerDevil integration](https://github.com/KDE/powerdevil/blob/master/daemon/actions/bundled/powerprofile.cpp)
