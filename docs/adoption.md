# Adoption Guide

The safe first command is:

```bash
go-task
```

That command applies only the user-level dotfiles workflow. It runs
`playbook_install.yml`, links managed files from `dotfiles/` into `$HOME`, and
does not apply system-wide configuration.

Do not blindly run these privileged apply commands:

```bash
go-task system
go-task browser-policies
```

Run check mode first:

```bash
go-task system:check
go-task browser-policies:check
```

Review these host values before privileged use:

- `inventory/host_vars/this_host/dotfiles.yml`
- `inventory/host_vars/this_host/system.yml`
- `inventory/host_vars/this_host/security.yml`
- `inventory/host_vars/this_host/browser_policies.yml`

The local host values are personal workstation choices. They are not a generic
security baseline and should not be copied to servers, shared systems, or other
workstations without review.

For a fork, start by adjusting inventory values and dotfile mappings, then run
the check targets before applying any privileged layer.
