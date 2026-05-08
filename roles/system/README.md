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
| Packages | Installs `system_packages` from `vars/archlinux-packages.yml` with tag `pkg`. |
| Time | Configures timezone and `systemd-timesyncd` when systemd is available. |
| Journald | Writes `/etc/systemd/journald.conf.d/10-dotfiles.conf`. |
| SSH daemon | Writes `/etc/ssh/sshd_config.d/20-dotfiles.conf` and validates effective sshd config. |
| Locale and console | Manages `/etc/locale.gen`, `/etc/locale.conf`, and `/etc/vconsole.conf`. |
| Sysctl | Manages declared kernel settings in `/etc/sysctl.d/999-ansible.conf`. |
| Pacman | Renders `/etc/pacman.conf` from the role template. |
| Reflector | Configures reflector and its systemd timer when systemd is available. |
| Docker | Configures daemon settings when not running in CI or a container. |
| Laptop | Applies laptop-specific settings such as camera blacklist and user ssh-agent service. |

## Drop-In Policy

Use drop-ins for supported system services instead of editing upstream main
files:

- `/etc/systemd/journald.conf.d/10-dotfiles.conf`
- `/etc/systemd/timesyncd.conf.d/10-dotfiles.conf`
- `/etc/ssh/sshd_config.d/20-dotfiles.conf`

The role removes legacy `*-ans-workstation.conf` drop-ins after writing the
current `*-dotfiles.conf` files to avoid duplicate settings.

## Variables

Default role values live in `defaults/main.yml`. Arch-specific package and OS
values live in `vars/`. Local host overrides live in:

```text
inventory/host_vars/this_host.yml
```

Keep local overrides deterministic and explicit. Do not store secrets in role
defaults, vars, or inventory.

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

Do not remove managed drop-ins manually unless you are intentionally moving
that configuration out of this role.
