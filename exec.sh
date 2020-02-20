#!/bin/bash
set -eo pipefail

# vars
SCRIPT_DIR=$( dirname "$(readlink -f "$0")" )
ANSIBLE_VENV_DIR="${SCRIPT_DIR}/ansible_venv"
MITOGEN_STRATEGY="mitogen_linear"

# functions
function fn_mitogen {
  ANSIBLE_STRATEGY_PLUGINS=$( find "${ANSIBLE_VENV_DIR}" -type d -name strategy | grep mitogen )
  if { [[ -d "${ANSIBLE_STRATEGY_PLUGINS}" ]] &&
       [[ -r "${ANSIBLE_STRATEGY_PLUGINS}/${MITOGEN_STRATEGY}.py" ]]; }
  then
    export ANSIBLE_STRATEGY_PLUGINS
    export ANSIBLE_STRATEGY=${MITOGEN_STRATEGY}
  fi
}

# check for venv || create it
[[ ! -r "${ANSIBLE_VENV_DIR}/bin/activate" ]] && \
  virtualenv "${ANSIBLE_VENV_DIR}" --system-site-packages

# shellcheck disable=SC1090
source "${ANSIBLE_VENV_DIR}/bin/activate"

pip install -r "${SCRIPT_DIR}/requirements.txt"

fn_mitogen

ansible-playbook "${SCRIPT_DIR}/playbook_install.yml" \
  -i "${SCRIPT_DIR}/inventory"

