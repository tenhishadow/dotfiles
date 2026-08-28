#!/bin/bash
set -euo pipefail

if ! /usr/bin/systemd-detect-virt --quiet --container; then
  printf '%s\n' 'This destructive integration harness must run inside a container.' >&2
  exit 1
fi

export ANSIBLE_FORCE_COLOR="false"
export ANSIBLE_COLLECTIONS_PATH="/tmp/dotfiles-system-test-collections"
export CI="true"
export UV_PYTHON="/usr/bin/python3"
export UV_PROJECT_ENVIRONMENT="/tmp/dotfiles-system-test-venv"

validate_https_url() {
  local authority
  local variable_name="$1"
  local value="$2"

  authority="${value#https://}"
  authority="${authority%%/*}"
  if [[ "${value}" != https://* || "${value}" =~ [[:space:]] || -z "${authority}" || "${authority}" == *@* ]]; then
    printf '%s must be an HTTPS URL without whitespace or user info.\n' "${variable_name}" >&2
    exit 1
  fi
}

validate_mirror_settings() {
  local arch_placeholder="\$arch"
  local repo_placeholder="\$repo"

  if [[ -n "${DOTFILES_TEST_PACMAN_MIRROR_URL:-}" ]]; then
    validate_https_url DOTFILES_TEST_PACMAN_MIRROR_URL "${DOTFILES_TEST_PACMAN_MIRROR_URL}"
    if [[ "${DOTFILES_TEST_PACMAN_MIRROR_URL}" != *"${repo_placeholder}"* || "${DOTFILES_TEST_PACMAN_MIRROR_URL}" != *"${arch_placeholder}"* ]]; then
      printf '%s\n' "DOTFILES_TEST_PACMAN_MIRROR_URL must contain literal \$repo and \$arch placeholders." >&2
      exit 1
    fi
  fi

  if [[ -n "${DOTFILES_TEST_PYPI_INDEX_URL:-}" ]]; then
    validate_https_url DOTFILES_TEST_PYPI_INDEX_URL "${DOTFILES_TEST_PYPI_INDEX_URL}"
  fi
}

configure_pacman_mirror() {
  if [[ -z "${DOTFILES_TEST_PACMAN_MIRROR_URL:-}" ]]; then
    return
  fi

  printf 'Server = %s\n' "${DOTFILES_TEST_PACMAN_MIRROR_URL}" >/etc/pacman.d/mirrorlist
  printf '%s\n' 'Using the configured pacman mirror.'
}

install_bootstrap_packages() {
  pacman --disable-sandbox -Syu --noconfirm --needed --noprogressbar \
    go-task uv git python sudo
}

prepare_python_environment() {
  if [[ -z "${DOTFILES_TEST_PYPI_INDEX_URL:-}" ]]; then
    return
  fi

  printf '%s\n' 'Installing locked Python dependencies from the configured index.'
  uv --no-config venv --python "${UV_PYTHON}" "${UV_PROJECT_ENVIRONMENT}" --quiet
  if ! uv export \
      --locked \
      --no-dev \
      --no-emit-project \
      --format requirements-txt \
      --quiet \
      | uv --no-config pip sync \
        --python "${UV_PROJECT_ENVIRONMENT}/bin/python" \
        --default-index "${DOTFILES_TEST_PYPI_INDEX_URL}" \
        --require-hashes \
        --no-build \
        --strict \
        --quiet \
        - >/dev/null 2>&1; then
    printf '%s\n' 'The configured Python index could not provide the locked dependencies.' >&2
    exit 1
  fi
  export UV_NO_SYNC="true"
}

check_system_package_targets() {
  local package_targets_file
  local -a system_package_targets

  package_targets_file="$(mktemp)"
  trap 'rm -f "${package_targets_file}"' RETURN

  uv run python - <<'PY' >"${package_targets_file}"
import re
import sys
from pathlib import Path

import yaml

variable_pattern = re.compile(r"^\{\{\s*([a-z0-9_]+)\s*\}\}$")
role_vars = {}

for path in (
    Path("roles/system/defaults/main.yml"),
    Path("roles/system/vars/archlinux.yml"),
    Path("roles/system/vars/archlinux-packages.yml"),
):
    with path.open(encoding="utf-8") as handle:
        role_vars.update(yaml.safe_load(handle) or {})

package_targets = [
    "base",
    "base-devel",
    role_vars["system_reflector_package"],
    role_vars["system_tzdata_package"],
    role_vars["system_chrony_package"],
    *role_vars["system_packages"],
]

seen = set()
for package_target in package_targets:
    if not isinstance(package_target, str):
        sys.exit(f"system package target is not a string: {package_target!r}")

    variable_match = variable_pattern.fullmatch(package_target)
    if variable_match:
        variable_name = variable_match.group(1)
        try:
            package_target = role_vars[variable_name]
        except KeyError:
            sys.exit(f"unresolved system package variable: {variable_name}")
    elif "{{" in package_target:
        sys.exit(f"unsupported templated system package target: {package_target}")

    if not isinstance(package_target, str) or not package_target:
        sys.exit(f"invalid system package target: {package_target!r}")

    if package_target not in seen:
        seen.add(package_target)
        print(package_target)
PY
  mapfile -t system_package_targets <"${package_targets_file}"

  if ((${#system_package_targets[@]} == 0)); then
    printf '%s\n' 'No Arch package targets were found.' >&2
    exit 1
  fi

  printf 'Checking %s Arch package targets...\n' "${#system_package_targets[@]}"
  if ! pacman -Si -- "${system_package_targets[@]}" >/dev/null; then
    printf '%s\n' 'One or more Arch package targets are unavailable.' >&2
    exit 1
  fi
}

check_time_tag_contract() {
  local package_tasks
  local preinstalled_tasks

  package_tasks="$(uv run ansible-playbook --list-tasks --tags pkg playbook_system.yml)"
  preinstalled_tasks="$(uv run ansible-playbook --list-tasks --skip-tags pkg playbook_system.yml)"

  if ! grep -Fq 'Chrony | Install package' <<<"${package_tasks}" \
      || grep -Fq 'Chrony | Render configuration' <<<"${package_tasks}"; then
    printf '%s\n' 'The pkg tag does not isolate time package installation.' >&2
    exit 1
  fi
  if grep -Fq 'Chrony | Install package' <<<"${preinstalled_tasks}" \
      || ! grep -Fq 'Chrony | Render configuration' <<<"${preinstalled_tasks}"; then
    printf '%s\n' 'Skipping pkg also skipped non-package time configuration.' >&2
    exit 1
  fi
}

check_nodejs_package_migration() {
  local -a nodejs_contract
  local nodejs_minimum
  local nodejs_package

  mapfile -t nodejs_contract < <(
    uv run python - <<'PY'
from pathlib import Path

import yaml

with Path("roles/system/vars/archlinux.yml").open(encoding="utf-8") as handle:
    role_vars = yaml.safe_load(handle) or {}
with Path("Taskfile.yml").open(encoding="utf-8") as handle:
    taskfile = yaml.safe_load(handle) or {}

print(role_vars["system_nodejs_package"])
print(taskfile["vars"]["RENOVATE_NODE_MIN_VERSION"])
PY
  )
  nodejs_package="${nodejs_contract[0]}"
  nodejs_minimum="${nodejs_contract[1]}"

  printf '%s\n' 'Verifying the Node.js LTS package migration...'
  pacman --disable-sandbox -S --noconfirm --needed --noprogressbar \
    -- nodejs-lts-jod npm >/dev/null
  uv run ansible-playbook playbook_system.yml \
    --tags pkg \
    -e "{\"system_packages\":[\"${nodejs_package}\"],\"system_time_enabled\":false}"

  pacman -Q -- "${nodejs_package}" >/dev/null
  if pacman -Q -- nodejs-lts-jod >/dev/null 2>&1; then
    printf '%s\n' 'The previous Node.js LTS provider remains installed.' >&2
    exit 1
  fi
  npm --version >/dev/null
  node - "${nodejs_minimum}" <<'JS'
const actual = process.versions.node.split(".").map(Number);
const minimum = process.argv[2].split(".").map(Number);
if (actual[0] !== minimum[0]) process.exit(1);
for (let index = 1; index < minimum.length; index += 1) {
  if (actual[index] > minimum[index]) process.exit(0);
  if (actual[index] < minimum[index]) process.exit(1);
}
JS

  run_convergence_check \
    nodejs-package \
    playbook_system.yml \
    --tags pkg \
    -e "{\"system_packages\":[\"${nodejs_package}\"],\"system_time_enabled\":false}"
}

install_time_contract_package() {
  local time_contract_package

  time_contract_package="$(uv run python - <<'PY'
from pathlib import Path

import yaml

with Path("roles/system/vars/archlinux.yml").open(encoding="utf-8") as handle:
    role_vars = yaml.safe_load(handle) or {}

print(role_vars["system_chrony_package"])
PY
)"
  pacman --disable-sandbox -S --noconfirm --needed --noprogressbar \
    -- "${time_contract_package}" >/dev/null
}

run_convergence_check() {
  local result_name="$1"
  local playbook="$2"
  local result_path
  shift 2

  result_path="${convergence_results_dir}/${result_name}.json"
  printf 'Checking %s convergence...\n' "${result_name}"
  if ! ANSIBLE_JSON_INDENT=0 \
    ANSIBLE_STDOUT_CALLBACK=ansible.posix.json \
    uv run ansible-playbook "${playbook}" "$@" >"${result_path}"; then
    printf 'Ansible convergence run failed; callback output follows:\n' >&2
    sed -n '1,240p' "${result_path}" >&2
    return 1
  fi
  python3 .test/assert_ansible_convergence.py "${result_path}"
}

prepare_dotfiles_cleanup_contract() {
  local removed_target
  local preserved_target="/tmp/dotfiles-user-owned-nvim"

  mkdir -p /root/.config/nvim "${preserved_target}"
  ln -s "${preserved_target}" /root/.nvim
  removed_target="$(realpath --relative-to=/root/.config/nvim "${PWD}/dotfiles/.vimrc")"
  ln -s "${removed_target}" /root/.config/nvim/init.vim
}

check_legacy_ponytail_link_contract() {
  local foreign_target="/tmp/dotfiles-user-owned-ponytail"
  local legacy_path="/root/.agents/skills/ponytail"
  local repository_target="${PWD}/dotfiles/.agents/skills/ponytail"
  local rejection_output

  mkdir -p /root/.agents/skills "${foreign_target}"
  printf '%s\n' 'foreign-ponytail-preserved' >"${foreign_target}/marker"
  ln -s "${foreign_target}" "${legacy_path}"

  if rejection_output="$(
    uv run ansible-playbook playbook_install.yml --tags configs 2>&1
  )"; then
    printf '%s\n' 'A foreign legacy Ponytail link was accepted.' >&2
    exit 1
  fi
  if ! grep -Fq \
    'Refusing foreign legacy directory link: /root/.agents/skills/ponytail' \
    <<<"${rejection_output}"; then
    printf '%s\n' 'The legacy-link rejection did not explain the unsafe path.' >&2
    exit 1
  fi
  if [[ ! -L "${legacy_path}" \
      || "$(readlink -- "${legacy_path}")" != "${foreign_target}" \
      || "$(<"${foreign_target}/marker")" != 'foreign-ponytail-preserved' ]]; then
    printf '%s\n' 'The rejected legacy Ponytail link was modified.' >&2
    exit 1
  fi

  rm -f -- "${legacy_path}"
  ln -s "${repository_target}" "${legacy_path}"
  uv run ansible-playbook playbook_install.yml --check --tags configs >/dev/null
  if [[ ! -L "${legacy_path}" \
      || "$(readlink -- "${legacy_path}")" != "${repository_target}" ]]; then
    printf '%s\n' 'Check mode modified the repository-owned Ponytail link.' >&2
    exit 1
  fi
}

check_foreign_baseline_symlink_rejection() {
  local baseline_path="/root/.config/htop/htoprc"
  local foreign_target="/tmp/dotfiles-user-owned-htoprc"
  local rejection_output

  mkdir -p /root/.config/htop
  printf '%s\n' 'foreign-baseline-preserved' >"${foreign_target}"
  ln -s "${foreign_target}" "${baseline_path}"

  if rejection_output="$(
    uv run ansible-playbook playbook_install.yml --tags configs 2>&1
  )"; then
    printf '%s\n' 'A foreign baseline symlink was accepted.' >&2
    exit 1
  fi
  if ! grep -Fq \
    'Refusing unsafe baseline destination: /root/.config/htop/htoprc' \
    <<<"${rejection_output}"; then
    printf '%s\n' 'The baseline rejection did not explain the unsafe path.' >&2
    exit 1
  fi
  if [[ ! -L "${baseline_path}" \
      || "$(readlink -- "${baseline_path}")" != "${foreign_target}" \
      || "$(<"${foreign_target}")" != 'foreign-baseline-preserved' ]]; then
    printf '%s\n' 'The rejected baseline symlink or its target was modified.' >&2
    exit 1
  fi

  rm -f -- "${baseline_path}" "${foreign_target}"
}

prepare_dotfiles_baseline_contract() {
  local htop_target

  mkdir -p /root/.config/htop /root/.mplayer
  htop_target="$(realpath --relative-to=/root/.config/htop "${PWD}/dotfiles/.config/htop/htoprc")"
  ln -s "${htop_target}" /root/.config/htop/htoprc
  ln -s "${PWD}/dotfiles/.mplayer/config" /root/.mplayer/config
}

check_dotfiles_baseline_check_mode() {
  local baseline_path
  local check_output
  local expected_htop_target
  local seed_output

  expected_htop_target="$(
    realpath --relative-to=/root/.config/htop \
      "${PWD}/dotfiles/.config/htop/htoprc"
  )"
  if ! check_output="$(
    uv run ansible-playbook playbook_install.yml --check --diff --tags configs 2>&1
  )"; then
    printf '%s\n' 'Baseline migration failed in check mode.' >&2
    printf '%s\n' "${check_output}" >&2
    exit 1
  fi
  seed_output="$(
    sed -n \
      '/TASK \[dotfiles : Dotfiles | Seed baseline files\]/,/^TASK \[/p' \
      <<<"${check_output}"
  )"
  for baseline_path in /root/.config/htop/htoprc /root/.mplayer/config; do
    if ! grep -Fq "changed: [this_host] => (item=${baseline_path})" \
      <<<"${seed_output}"; then
      printf 'Check mode did not predict seeding %s.\n' "${baseline_path}" >&2
      exit 1
    fi
  done
  if [[ ! -L /root/.config/htop/htoprc \
      || "$(readlink -- /root/.config/htop/htoprc)" != "${expected_htop_target}" \
      || ! -L /root/.mplayer/config \
      || "$(readlink -- /root/.mplayer/config)" != "${PWD}/dotfiles/.mplayer/config" ]]; then
    printf '%s\n' 'Check mode modified a legacy baseline symlink.' >&2
    exit 1
  fi
}

mutate_dotfiles_baseline() {
  printf '%s\n' '# container-local-baseline-marker' >>/root/.config/htop/htoprc
}

verify_dotfiles_baseline_preserved() {
  if ! grep -Fqx '# container-local-baseline-marker' /root/.config/htop/htoprc; then
    printf '%s\n' 'Dotfiles convergence overwrote a local baseline change.' >&2
    exit 1
  fi
}

validate_mirror_settings
configure_pacman_mirror
if [[ -n "${DOTFILES_TEST_PACMAN_MIRROR_URL:-}" ]]; then
  if ! install_bootstrap_packages >/dev/null 2>&1; then
    printf '%s\n' 'The configured pacman mirror could not provide the bootstrap packages.' >&2
    exit 1
  fi
else
  install_bootstrap_packages >/dev/null
fi
prepare_python_environment
check_system_package_targets
check_time_tag_contract
install_time_contract_package
check_legacy_ponytail_link_contract
check_foreign_baseline_symlink_rejection
prepare_dotfiles_cleanup_contract
prepare_dotfiles_baseline_contract
check_dotfiles_baseline_check_mode
convergence_results_dir="$(mktemp -d)"
check_nodejs_package_migration

if [[ -e /usr/lib/systemd/system/dotfiles-absent-ntpd.service || -L /etc/systemd/system/dotfiles-absent-ntpd.service ]]; then
  printf '%s\n' 'The absent-unit time contract fixture unexpectedly exists.' >&2
  exit 1
fi

printf '%s\n' 'Verifying preventative time-service masking and Chrony syntax...'
uv run ansible-playbook .test/system/time_contract.yml
# The package is installed only to provide chronyd for template validation.
# Remove its vendor config so the full role test can still prove that container
# guards do not create the host-only managed Chrony path.
rm -f -- /etc/chrony.conf

printf '%s\n' 'Applying all repository layers in the Arch container...'
go-task all -- --skip-tags pkg,aur

printf '%s\n' 'Verifying observable post-install state...'
uv run ansible-playbook .test/system/verify.yml

mutate_dotfiles_baseline
run_convergence_check \
  time-contract \
  .test/system/time_contract.yml \
  -e system_time_contract_negative_tests=false
run_convergence_check dotfiles playbook_install.yml
verify_dotfiles_baseline_preserved
run_convergence_check system playbook_system.yml --skip-tags pkg,aur
run_convergence_check browser-policies playbook_browser_policies.yml
