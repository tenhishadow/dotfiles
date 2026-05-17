# Migration From ans-workstation

The old standalone repository was `tenhishadow/ans-workstation`.

The workstation automation now lives in this repository as the opt-in system
layer:

| Old concern | New location |
| ----------- | ------------ |
| System role | `roles/system/` |
| System playbook | `playbook_system.yml` |
| System host values | `inventory/host_vars/this_host/system.yml` |
| Security-sensitive host values | `inventory/host_vars/this_host/security.yml` |
| Check system layer | `go-task system:check` |
| Apply system layer | `go-task system` |
| Test system role | `go-task test:system` |

The default `go-task` command in this repository does not apply system-wide
configuration. It runs `playbook_install.yml` and remains limited to the
user-level dotfiles workflow.
