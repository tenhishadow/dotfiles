# dotfiles

Special repository for configuring user dotfiles and Arch Linux workstation
state with Ansible.

[![ansible](https://github.com/tenhishadow/dotfiles/actions/workflows/ansible.yml/badge.svg)](https://github.com/tenhishadow/dotfiles/actions/workflows/ansible.yml)


## install deps

```bash
sudo pacman -Sy --noconfirm --needed go-task uv git
```

## install

```bash
_INSTALL_DIR="$HOME/.dotfiles" \
  && git clone https://github.com/tenhishadow/dotfiles.git $_INSTALL_DIR \
  && cd $_INSTALL_DIR \
  && go-task
```

The default `go-task` target is intentionally user-level only. It links the
payload under `dotfiles/` into `$HOME` and does not run the system role.

## system layer

The former `ans-workstation` system provisioning flow is available here as an
explicit opt-in role:

```bash
go-task system:check
go-task system
```

This path uses `playbook_system.yml` and may require sudo.

## browser policies

System-wide browser and VS Code policy management is also opt-in:

```bash
go-task browser-policies:check
go-task browser-policies
```
