# dotfiles

Special repository for configuring dotfiles with Ansible

[![ansible](https://github.com/tenhishadow/dotfiles/actions/workflows/ansible.yml/badge.svg)](https://github.com/tenhishadow/dotfiles/actions/workflows/ansible.yml)


## install minimal deps

```bash
pacman -Sy --noconfirm go-task uv git
```

## install

```bash
_INSTALL_DIR="$HOME/.dotfiles" \
  && git clone https://github.com/tenhishadow/dotfiles.git $_INSTALL_DIR \
  && cd "$HOME/.dotfiles" \
  && go-task
```

## installation with ans-workstation

[ans-workstation](https://github.com/tenhishadow/ans-workstation)

it configures the workstation and also includes this repository
