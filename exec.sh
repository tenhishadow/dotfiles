#!/bin/bash

ANSIBLE_VENV_DIR="./ansible_venv"

# check for venv || create it
[[ ! -r "${ANSIBLE_VENV_DIR}/bin/activate" ]] && virtualenv ${ANSIBLE_VENV_DIR}

# shellcheck disable=SC1090
source ${ANSIBLE_VENV_DIR}/bin/activate

pip install -r requirements.txt

ansible-playbook playbook_install.yml

