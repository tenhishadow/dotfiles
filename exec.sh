#!/bin/bash

# vars
ANSIBLE_VENV_DIR="./ansible_venv"

# functions
function fn_mitogen {
  ANSIBLE_STRATEGY_PLUGINS=$( find  "${ANSIBLE_VENV_DIR}" -type d -name strategy | grep mitogen )
  if [[ -d $ANSIBLE_STRATEGY_PLUGINS ]]
  then
    export ANSIBLE_STRATEGY_PLUGINS
    export ANSIBLE_STRATEGY="mitogen_linear"
  fi
}

# check for venv || create it
[[ ! -r "${ANSIBLE_VENV_DIR}/bin/activate" ]] && virtualenv ${ANSIBLE_VENV_DIR}

# shellcheck disable=SC1090
source ${ANSIBLE_VENV_DIR}/bin/activate

pip install -r requirements.txt

fn_mitogen

ansible-playbook playbook_install.yml

