# system

Opt-in Arch Linux workstation provisioning role.

This role manages system-wide state and uses `become: true` for privileged
paths and services. It is intentionally not part of the default dotfiles
workflow. Run it only through `playbook_system.yml` or the matching `go-task`
targets.

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

Run the container smoke and idempotency test:

```bash
go-task test:system
```

## Managed Areas

| Area | Notes |
| ---- | ----- |
| Packages | Installs `system_packages` from `vars/archlinux-packages.yml` when `system_packages_enabled` is true, including Neovim support tools such as `tree-sitter-cli`. |
| Time | Configures timezone. Manages `systemd-timesyncd` only when `system_timesyncd_enabled` is true, systemd is manageable, and the host is not a virtual machine. |
| Journald | Writes `/etc/systemd/journald.conf.d/10-dotfiles.conf`. |
| SSH daemon | Writes `/etc/ssh/sshd_config.d/20-dotfiles.conf` and validates effective sshd config. |
| Locale and console | Manages `/etc/locale.gen`, `/etc/locale.conf`, and `/etc/vconsole.conf`. |
| Sysctl | Applies `system_sysctl_default_settings` merged with `system_sysctl_settings` to `/etc/sysctl.d/999-ansible.conf` when `system_sysctl_enabled` is true. |
| Limits | Writes `/etc/security/limits.d/10-dotfiles.conf` when `system_limits_enabled` is true. |
| Pacman | Renders `/etc/pacman.conf` from the role template. |
| Reflector | Configures reflector and its systemd timer when systemd is available. |
| Docker | Configures daemon settings and overlay module options when `system_docker_enabled` is true and the host is not CI/container. |
| Laptop | Applies laptop-specific settings such as camera blacklist when `system_laptop_enabled` is true. |
| User services | Configures the user ssh-agent service when `system_user_services_enabled` is true. |

## Role Flow

The role keeps privileged behavior explicit and guarded:

1. Validate the supported OS.
2. Load distro-specific vars and packages.
3. Derive CI, container, virtual machine, systemd, and timesyncd capability guards.
4. Validate public role variables and host overrides.
5. Install the package manifest under tag `pkg` when packages are enabled.
6. Run time, locale, console, login, limits, cron, sysctl, journald, SSHD, OS,
   Docker, laptop, and user-service task files according to feature flags.

## Feature Flags

The role is opt-in at the playbook level, but these areas are enabled by default
inside the system role:

| Variable | Default | Controls |
| -------- | ------- | -------- |
| `system_packages_enabled` | `true` | Arch package manifest installation. |
| `system_timesyncd_enabled` | `true` | `systemd-timesyncd` drop-in management when the host is not a virtual machine. |
| `system_sysctl_enabled` | `true` | Kernel parameter drop-in under `/etc/sysctl.d/`. |
| `system_limits_enabled` | `true` | PAM limits drop-in under `/etc/security/limits.d/`. |
| `system_docker_enabled` | `true` | Docker group, daemon config, and user membership. |
| `system_docker_overlay_options_enabled` | `true` | Overlay kernel module options under `/etc/modprobe.d/`. |
| `system_laptop_enabled` | `true` | Laptop-specific system settings. |
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

Example host overrides:

```yaml
system_journald_settings:
  Storage: persistent
  Compress: "yes"
  SystemMaxUse: 50M

system_packages_enabled: true
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

Common disable-only overrides:

```yaml
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

`go-task test:system` runs the role twice in a fresh Arch Linux container with
`--skip-tags pkg`; the second pass must be idempotent.

## Rollback

Use git to revert role changes before reapplying. For local system state,
inspect Ansible backups for files rendered with `backup: true`, then apply the
previous revision with:

```bash
go-task system
```

For package changes, review pacman history and any generated `.pacnew` or
`.pacsave` files:

```bash
go-task pacdiff
```

Do not remove managed drop-ins or snippets manually unless you are intentionally
moving that configuration out of this role.
