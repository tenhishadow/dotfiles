# Adoption Guide

The lowest-risk first check is:

```bash
go-task dotfiles:check
```

That command runs the user-level dotfiles playbook in check mode with diff
output. The Ansible playbook is sudo-free and uses `become: false`, but
Taskfile dependency bootstrap may install missing local prerequisites such as
`uv` or `git` through `pacman` and `sudo` on Arch Linux before Ansible runs.
It does not apply system-wide configuration.

Review `inventory/host_vars/this_host/dotfiles.yml` before applying the
user-level workflow on another account or fork.

Use the read-only dotfiles report to check current destinations:

```bash
go-task dotfiles:plan
```

The user-level apply command is:

```bash
go-task
```

That command applies only the user-level dotfiles workflow. It runs
`playbook_install.yml`, links managed files from `dotfiles/` into `$HOME`, and
does not apply system-wide configuration. It can still replace managed
destinations with symlinks and remove explicit legacy user paths.

Do not blindly run these privileged apply commands:

```bash
go-task all
go-task system
go-task browser-policies
```

Run check mode first:

```bash
go-task system:check
go-task browser-policies:check
```

`go-task system:check` runs Ansible check mode for the opt-in system playbook
after Taskfile dependency bootstrap.

Read-only reports are available before privileged review:

```bash
go-task doctor
go-task system:report
go-task browser-policies:report
```

Review these host values before privileged use:

- `inventory/host_vars/this_host/dotfiles.yml`
- `inventory/host_vars/this_host/system.yml`
- `inventory/host_vars/this_host/security.yml`
- `inventory/host_vars/this_host/browser_policies.yml`
- `roles/system/defaults/main.yml` AUR helper defaults

The local host values are personal workstation choices. They are not a generic
security baseline and should not be copied to servers, shared systems, or other
workstations without review.

Review `docs/privacy-policy-surfaces.md` before adopting the managed privacy
dotfiles and browser, Thunderbird, or VS Code policies. The repository does not
manage secrets, AI account state, kubeconfigs, mail profiles, browser profiles,
or private registry credentials.

For a fork, start by adjusting inventory values and dotfile mappings, then run
the check targets before applying any privileged layer.
