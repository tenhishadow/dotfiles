# system

Opt-in Arch Linux workstation provisioning role.

This role manages system-wide state and uses `become: true` for privileged
paths and services. It is intentionally not part of the default dotfiles
workflow. Run it only through `playbook_system.yml` or the matching `go-task`
targets.

## Historical Note

This role supersedes the former standalone `tenhishadow/ans-workstation`
automation layer. Legacy `*-ans-workstation.conf` drop-ins are removed where
applicable to avoid duplicate settings after consolidation. The role remains
opt-in and is not part of the default dotfiles workflow.

## Usage

Review the task list:

```bash
go-task system:list
```

Dry-run the role:

```bash
go-task system:check
```

Apply the role:

```bash
go-task system
```

Run the disposable Arch package, state, and convergence test:

```bash
go-task test:system
```

## Managed Areas

| Area | Notes |
| ---- | ----- |
| Packages | Installs `system_packages` from `vars/archlinux-packages.yml` when `system_packages_enabled` is true. A selected Node.js LTS provider replaces a conflicting installed provider atomically before the manifest is applied. The manifest also includes Neovim support tools such as `tree-sitter-cli`. |
| AUR | Optionally bootstraps the configured AUR helper, `yay` by default, through tasks tagged `aur` in apply mode on non-CI, non-container hosts. |
| Time | Configures `system_timezone`; when the applicable backend flag is enabled, selects Chrony for virtual machines or `systemd-timesyncd` for physical hosts and stops and masks other known NTP services. Disabled applicable backends, containers, and CI select no daemon. |
| Journald | Writes `/etc/systemd/journald.conf.d/10-dotfiles.conf`. |
| SSH daemon | Writes `/etc/ssh/sshd_config.d/20-dotfiles.conf` and validates effective sshd config. |
| Locale and console | Validates locale definitions, owns `/etc/locale.gen`, regenerates locales when it changes, and manages `/etc/locale.conf` and `/etc/vconsole.conf`. |
| Sysctl | Renders the complete sorted merge of `system_sysctl_default_settings` and `system_sysctl_settings` to `/etc/sysctl.d/999-ansible.conf`, then reloads it once. |
| Limits | Writes `/etc/security/limits.d/10-dotfiles.conf` when `system_limits_enabled` is true. |
| Pacman | Renders `/etc/pacman.conf` from the role template with an Ansible backup before replacement. |
| Reflector | Configures reflector and its systemd timer when systemd is available. |
| TRIM | Enables the packaged weekly `fstrim.timer` when this host opts in; keeps the upstream schedule and filesystem selection. |
| Docker | Configures daemon settings and overlay module options when `system_docker_enabled` is true and the host is not CI/container. |
| Laptop | Applies the camera blacklist on explicitly enabled physical hosts and removes the former module-managed entry. |
| TuneD | Optionally connects Plasma power profiles through `tuned-ppd`, manages its mapping and a balanced-derived performance profile, and enables both services on physical systemd hosts outside CI. |
| User services | Configures the user ssh-agent service only when a user systemd manager can be used safely. |

As checked on 2026-09-30, [talhelper](https://aur.archlinux.org/packages/talhelper)
is an optional AUR package and is excluded from the official package manifest.
Install it manually if needed; the role's AUR support bootstraps the helper
only. An existing `talhelper` installation is not removed.

## Role Flow

The role keeps privileged behavior explicit and guarded:

1. Validate the supported OS.
2. Load distro-specific vars and packages.
3. Derive CI, container, virtual machine, systemd, user systemd, time backend,
   and AUR capability guards.
4. Validate public role variables and host overrides.
5. Replace a conflicting Node.js provider in one pacman transaction, then
   install the package manifest under tag `pkg` when packages are enabled.
6. Bootstrap the AUR helper under tag `aur` when AUR is enabled, apply mode is
   active, and the host is safe.
7. Run time, locale, console, login, limits, cron, sysctl, drop-in (journald and
   physical-host timesyncd, described by `system_dropins`), SSHD, OS, Docker,
   laptop, TuneD, and user-service task files according to feature flags.

## Feature Flags

The role is opt-in at the playbook level. General workstation features are
enabled by default; AUR execution and hardware-specific laptop behavior require
explicit host opt-in:

| Variable | Default | Controls |
| -------- | ------- | -------- |
| `system_packages_enabled` | `true` | Arch package manifest installation. |
| `system_aur_enabled` | `false` | AUR helper bootstrap in apply mode on non-CI, non-container hosts; this host opts in explicitly. |
| `system_time_enabled` | `true` | Timezone and guarded time-synchronization management. |
| `system_chrony_enabled` | `true` | Chrony package, configuration, and service management on virtual machines. |
| `system_timesyncd_enabled` | `true` | `systemd-timesyncd` drop-in and service management on physical systemd hosts. |
| `system_sysctl_enabled` | `true` | Kernel parameter drop-in under `/etc/sysctl.d/`. |
| `system_limits_enabled` | `true` | PAM limits drop-in under `/etc/security/limits.d/`. |
| `system_docker_enabled` | `true` | Docker group, daemon config, and user membership. |
| `system_docker_overlay_options_enabled` | `true` | Overlay kernel module options under `/etc/modprobe.d/`. |
| `system_laptop_enabled` | `false` | Laptop-specific system settings on a physical non-CI host. |
| `system_tuned_enabled` | `false` | TuneD profile mapping and configuration; service management requires a physical systemd host outside CI. This host opts in. |
| `system_fstrim_enabled` | `false` | Enables the packaged periodic TRIM timer outside CI and containers. This host opts in. |
| `system_user_services_enabled` | `true` | User-level systemd units managed by the system role. |

Disable a feature in host vars instead of removing tasks from the role.

## Time Synchronization

Virtual machines use `/etc/chrony.conf` with the configured
`system_ntp_servers` as pools. By default, each pool contributes at most one source,
initial measurements use `iburst`, and the drift estimate persists under
`/var/lib/chrony/`. The default `makestep 1.0 -1` permits a VM clock that is
more than one second wrong to step after resume at any update. Review that
workstation-oriented tradeoff before copying it to a server or a host where
backward clock steps would be unsafe. The negative update limit is an explicit
VM policy; see upstream [makestep behavior](https://chrony-project.org/doc/4.8/chrony.conf.html#makestep).

Physical hosts use the same primary servers and the configured fallback list
through the managed `systemd-timesyncd` drop-in.

An existing boot-time synchronization wait follows the selected daemon. If
either `chrony-wait.service` or `systemd-time-wait-sync.service` was enabled,
active, or starting before apply, the role unmasks and enables the matching
native waiter for the next boot, and stops, disables, and masks the other.
The daemon starts immediately; the role does not start a blocking waiter during
apply. Hosts without an existing waiter do not gain a new boot wait. This
preserves ordering through `time-sync.target`
using [Chrony's native waitsync](https://chrony-project.org/doc/4.9/chronyc.html#waitsync)
on VMs; systemd documents its
[fallback detection for Chrony as unreliable](https://github.com/systemd/systemd/blob/main/man/systemd-time-wait-sync.service.xml).

Containers and CI select no daemon and skip timezone changes. Containers use
the host clock; the role does not grant clock-setting capabilities to tests.
VMs never fall back to ntpd. Disabling the applicable backend skips management
without enabling another daemon or undoing previously applied state.

After an authorized apply on a real VM, inspect the selected service and
synchronization state with these read-only commands:

```bash
systemctl is-active chronyd.service
systemctl is-enabled chronyd.service systemd-timesyncd.service ntpd.service
chronyc tracking
chronyc sources -v
```

Expect Chrony enabled and active, competing units masked, and a selected time
source. An active service alone does not prove synchronization. Use
[Chrony's monitoring fields](https://chrony-project.org/doc/4.8/chronyc.html#tracking)
to assess the offset and synchronization state. Repeat that inspection after a
separately scheduled guest suspend/resume test; container assertions cannot
prove recovery. Review hypervisor guest-tool time synchronization so a second
clock owner does not fight Chrony.

For a VM that already required synchronization before boot proceeded, verify
the waiter migration after an authorized guest reboot:

```bash
systemctl is-enabled chrony-wait.service systemd-time-wait-sync.service
systemctl show chrony-wait.service -p ActiveState -p SubState -p Result
systemctl list-jobs
```

Expect `chrony-wait.service` enabled and successfully completed, the old waiter
masked, and no pending time-synchronization job once Chrony has synchronized.
Immediately after apply, the new waiter may be enabled but still inactive;
checking an already running daemon alone does not verify boot ordering.

## Default Tuning

`system_sysctl_default_settings` is role-owned and applies before
host-specific `system_sysctl_settings` overrides:

| Key | Value |
| --- | ----- |
| `kernel.unprivileged_bpf_disabled` | `"1"` |
| `net.core.default_qdisc` | `fq` |
| `net.ipv4.tcp_congestion_control` | `bbr` |
| `net.core.somaxconn` | `"8192"` |
| `net.ipv4.ip_local_port_range` | `"10240 65535"` |

`system_limits_entries` defaults to soft and hard `nofile`/`nproc` limits of
`65535` for `*` and `root`.

Docker overlay options default to:

```text
options overlay metacopy=off redirect_dir=off
```

## Periodic TRIM

`system_fstrim_enabled` enables and starts the packaged `fstrim.timer` through
the `fstrim` tag. The upstream weekly schedule, persistent missed-run handling,
and randomized delay remain unchanged. The service uses its packaged filesystem
selection; the role does not change encryption, mount options, or initramfs.

Use `--tags fstrim` with `playbook_system.yml` for this operation alone. Verify
the timer schedule and service journal; an enabled timer does not prove that
the intended filesystems have completed a discard operation. The execution
guard skips timer management in CI and containers. For rollback, stop and
disable the timer and set the host flag to false to prevent re-enablement.
Changing the flag alone skips management without undoing previous state.

## Plasma Power Profiles

`system_tuned_enabled` manages `/etc/tuned/ppd.conf` and
`/etc/tuned/profiles/workstation-performance/tuned.conf`, with root ownership,
mode `0644`, and backups before replacement. The official `tuned-ppd` package
provides Plasma's power-profile API while TuneD remains the tuning owner.
Review and stop competing power managers before enabling this feature.

The mapping uses `powersave`, `balanced`, and `workstation-performance`.
Balanced selects `balanced-battery` on battery. Performance inherits `balanced`
and changes only the CPU governor preference, EPP, and ACPI platform profile;
it does not inherit `throughput-performance` server tuning. For hosts using
active Intel P-state, consider `system_tuned_performance_governor: powersave`.
The other policy inputs are `system_tuned_performance_energy_preference` and
`system_tuned_performance_platform_profile`, both `performance` by default.
Review these hardware-dependent values when adopting another host.

Use `--tags tuned` with `playbook_system.yml` to select only this feature and
role validation. Add `--check --diff` to review it first. This selection
installs only the bridge and its dependencies when `system_packages_enabled`
is true. It does not select the full manifest. Packages must already exist
when package management is disabled.

The role enables `tuned.service` and `tuned-ppd.service` on physical systemd
hosts outside CI. Config changes notify restart handlers; an unchanged apply
preserves the active profile. Containers verify file rendering and ownership,
while actual profile transitions require host validation. Check the desktop
selector, TuneD's active profile, CPU EPP, and ACPI platform profile together;
AC/battery transitions also need hardware testing.

To roll back, select balanced, stop and mask the newly added bridge to prevent
D-Bus reactivation, and retain the pre-existing TuneD service. Restore the
previous profile selection mode and configuration from the recorded baseline.
Disabling the feature flag alone does not undo applied state.

## Managed Configuration Policy

Use drop-ins for supported system services instead of editing upstream main
files:

- `/etc/systemd/journald.conf.d/10-dotfiles.conf`
- `/etc/systemd/timesyncd.conf.d/10-dotfiles.conf`
- `/etc/ssh/sshd_config.d/20-dotfiles.conf`
- `/etc/security/limits.d/10-dotfiles.conf`
- `/etc/modprobe.d/99-dotfiles-camera.conf`
- `/etc/modprobe.d/99-dotfiles-overlay.conf`

The role removes legacy `*-ans-workstation.conf` drop-ins after writing the
current `*-dotfiles.conf` files to avoid duplicate settings.

Chrony is the deliberate complete-file exception: the role owns
`/etc/chrony.conf`, validates it with `chronyd` when the binary is present, and
does not activate untracked files from `/etc/chrony/sources.d/`. When a virtual
machine selects Chrony, the role removes its exact current and legacy
timesyncd drop-in paths before masking the inactive daemon.

Kernel module options under `/etc/modprobe.d/` take effect after the module is
reloaded or the host is rebooted.

## Variables

Default role values live in `defaults/main.yml`. Arch-specific package and OS
values live in `vars/`. Local host overrides live in:

```text
inventory/host_vars/this_host/system.yml
inventory/host_vars/this_host/security.yml
```

Keep local overrides deterministic and explicit. Do not store secrets in role
defaults, vars, or inventory.

Public role variables use the `system_` prefix. Use `system_journald_settings`,
`system_sshd_settings`, and `system_sysctl_settings` for managed setting maps;
their keys intentionally preserve upstream config option names. The role-owned
`system_sysctl_default_settings` map contains default kernel tuning, while
`system_sysctl_settings` is for host-specific additions and overrides.
User service files are owned by `system_user_service_owner` and
`system_user_service_group`, which default to the real user and group facts.

Example host overrides:

```yaml
system_journald_settings:
  Storage: persistent
  Compress: "yes"
  SystemMaxUse: 50M

system_timezone: Europe/Warsaw
system_packages_enabled: true
system_aur_enabled: true
system_chrony_enabled: true
system_timesyncd_enabled: true
system_docker_enabled: false
system_laptop_enabled: false
system_user_services_enabled: true

system_sshd_settings:
  UseDNS: "no"
  ClientAliveInterval: "300"

system_sysctl_enabled: true
system_sysctl_settings:
  fs.inotify.max_user_watches: "524288"
  net.core.somaxconn: "16384"

system_limits_enabled: true
system_limits_entries:
  - domain: "*"
    type: soft
    item: nofile
    value: "65535"

system_docker_overlay_options_enabled: true
```

Do not rename upstream option keys inside these maps; only the Ansible variable
names use lowercase snake_case.

The default AUR helper bootstrap installs `yay` from
`https://aur.archlinux.org/yay.git` into `/usr/bin/yay`. It installs Arch build
dependencies from `system_aur_build_packages`, builds from
`system_aur_build_root`, refuses root builds, and skips check mode, CI, and
container execution. Use tag `aur` to select or skip this path.

Common disable-only overrides:

```yaml
system_aur_enabled: false
system_sysctl_enabled: false
system_limits_enabled: false
system_docker_overlay_options_enabled: false
```

## Validation

Run these checks for role changes:

```bash
go-task lint
go-task system:check
go-task test:system
git diff --check
```

`go-task test:system` verifies Arch package targets with one pacman query, then
applies the dotfiles, system, and policy layers in a fresh Arch container with
`--skip-tags pkg,aur`. Native Ansible assertions verify observable links,
files, ownership, modes, content, JSON policies, and guarded host-only paths.
Machine-readable second passes must report zero changes, failures, ignored or
rescued failures, and unreachable hosts. A focused package test first replaces
the former Node.js LTS provider with the selected provider, verifies the Node.js
and npm runtime, and requires a zero-change second package pass.

The native role contract test verifies VM, physical-host, disabled, and guarded
time backend selection. The container intentionally cannot cover service
enablement, real NTP synchronization, SSHD, sysctl loading, Docker daemon
restart, AUR execution, VM lifecycle, or hardware behavior. A real guest or
physical host must verify the selected time daemon after check mode. See
`docs/adr/0001-validation-strategy.md` for the test boundary.

## Rollback

Use git to revert role changes before reapplying. For local system state,
inspect Ansible backups for complete-file writes such as `/etc/pacman.conf`
and `/etc/chrony.conf`, then apply the previous revision with:

```bash
go-task system
```

For package changes, review pacman history and any generated `.pacnew` or
`.pacsave` files:

```bash
go-task pacdiff
```

Feature flags stop managing a subsystem; they do not imply deletion of its
previous drop-ins or files. Plan removal explicitly before disabling a feature.

Changing from the physical-host backend to the VM backend is narrower than a
feature disable: it explicitly removes only the role-owned timesyncd drop-in
paths and then activates Chrony.

Do not remove managed drop-ins or snippets manually unless you are intentionally
moving that configuration out of this role.
