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
| Packages | Installs `system_packages` from `vars/archlinux-packages.yml` when `system_packages_enabled` is true, including Neovim support tools such as `tree-sitter-cli`. |
| AUR | Optionally bootstraps the configured AUR helper, `yay` by default, through tasks tagged `aur` in apply mode on non-CI, non-container hosts. |
| Time | Configures `system_timezone`, which defaults to `UTC` and should be overridden in host vars. Manages `systemd-timesyncd` when `system_timesyncd_enabled` is true and systemd is manageable; VM owners can disable it explicitly. |
| Journald | Writes `/etc/systemd/journald.conf.d/10-dotfiles.conf`. |
| SSH daemon | Writes `/etc/ssh/sshd_config.d/20-dotfiles.conf` and validates effective sshd config. |
| Locale and console | Validates locale definitions, owns `/etc/locale.gen`, regenerates locales when it changes, and manages `/etc/locale.conf` and `/etc/vconsole.conf`. |
| Sysctl | Renders the complete sorted merge of `system_sysctl_default_settings` and `system_sysctl_settings` to `/etc/sysctl.d/999-ansible.conf`, then reloads it once. |
| Limits | Writes `/etc/security/limits.d/10-dotfiles.conf` when `system_limits_enabled` is true. |
| Pacman | Renders `/etc/pacman.conf` from the role template with an Ansible backup before replacement. |
| Reflector | Configures reflector and its systemd timer when systemd is available. |
| Docker | Configures daemon settings and overlay module options when `system_docker_enabled` is true and the host is not CI/container. |
| Laptop | Applies the camera blacklist on explicitly enabled physical hosts and removes the former module-managed entry. |
| User services | Configures the user ssh-agent service only when a user systemd manager can be used safely. |

## Role Flow

The role keeps privileged behavior explicit and guarded:

1. Validate the supported OS.
2. Load distro-specific vars and packages.
3. Derive CI, container, virtual machine, systemd, user systemd, timesyncd, and
   AUR capability guards.
4. Validate public role variables and host overrides.
5. Install the package manifest under tag `pkg` when packages are enabled.
6. Bootstrap the AUR helper under tag `aur` when AUR is enabled, apply mode is
   active, and the host is safe.
7. Run time, locale, console, login, limits, cron, sysctl, drop-in (journald
   and timesyncd, described by `system_dropins`), SSHD, OS, Docker, laptop, and
   user-service task files according to feature flags.

## Feature Flags

The role is opt-in at the playbook level. General workstation features are
enabled by default; AUR execution and hardware-specific laptop behavior require
explicit host opt-in:

| Variable | Default | Controls |
| -------- | ------- | -------- |
| `system_packages_enabled` | `true` | Arch package manifest installation. |
| `system_aur_enabled` | `false` | AUR helper bootstrap in apply mode on non-CI, non-container hosts; this host opts in explicitly. |
| `system_timesyncd_enabled` | `true` | `systemd-timesyncd` drop-in and service management when systemd is available. |
| `system_sysctl_enabled` | `true` | Kernel parameter drop-in under `/etc/sysctl.d/`. |
| `system_limits_enabled` | `true` | PAM limits drop-in under `/etc/security/limits.d/`. |
| `system_docker_enabled` | `true` | Docker group, daemon config, and user membership. |
| `system_docker_overlay_options_enabled` | `true` | Overlay kernel module options under `/etc/modprobe.d/`. |
| `system_laptop_enabled` | `false` | Laptop-specific system settings on a physical non-CI host. |
| `system_user_services_enabled` | `true` | User-level systemd units managed by the system role. |

Disable a feature in host vars instead of removing tasks from the role.

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

## Drop-In Policy

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
rescued failures, and unreachable hosts.

The container intentionally cannot cover systemd, SSHD, sysctl loading, Docker
daemon restart, AUR execution, VM lifecycle, or hardware behavior. See
`docs/adr/0001-validation-strategy.md` for the test boundary.

## Rollback

Use git to revert role changes before reapplying. For local system state,
inspect Ansible backups for complete-file writes such as `/etc/pacman.conf`,
then apply the previous revision with:

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

Do not remove managed drop-ins or snippets manually unless you are intentionally
moving that configuration out of this role.
