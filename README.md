# dotfiles

Special repository for configuring dotfiles with Ansible

[![lint_vimrc](https://github.com/tenhishadow/dotfiles/workflows/lint_vimrc/badge.svg)](https://github.com/tenhishadow/dotfiles/actions?query=workflow%3Alint_vimrc)
[![ansible_exec](https://github.com/tenhishadow/dotfiles/workflows/ansible_exec/badge.svg)](https://github.com/tenhishadow/dotfiles/actions?query=workflow%3Aansible_exec)
[![github-super-linter](https://github.com/tenhishadow/dotfiles/actions/workflows/github-super-linter.yml/badge.svg)](https://github.com/tenhishadow/dotfiles/actions/workflows/github-super-linter.yml)

## installation

```bash

_INSTALL_DIR="$HOME/.dotfiles" \
  && yay -Sy --noconfirm python-pipenv python-setuptools \
  && git clone https://github.com/tenhishadow/dotfiles.git $_INSTALL_DIR \
  && cd $_INSTALL_DIR \
  && pipenv install \
  && pipenv run install

```

## installation with ans-workstation

[ans-workstation](https://github.com/tenhishadow/ans-workstation)

it configures the workstation and also includes this repo
