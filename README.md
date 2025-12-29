# dotfiles

Special repository for configuring dotfiles with Ansible

[![ansible](https://github.com/tenhishadow/dotfiles/actions/workflows/ansible.yml/badge.svg)](https://github.com/tenhishadow/dotfiles/actions/workflows/ansible.yml)


## install deps

```bash
sudo pacman -Sy --noconfirm python-pipenv python-setuptools \
|| sudo apt install git pipenv -y
```

## install

```bash

_INSTALL_DIR="$HOME/.dotfiles" \
  && git clone https://github.com/tenhishadow/dotfiles.git $_INSTALL_DIR \
  && cd $_INSTALL_DIR \
  && pipenv install \
  && pipenv run install

```

## installation with ans-workstation

[ans-workstation](https://github.com/tenhishadow/ans-workstation)

it configures the workstation and also includes this repository
