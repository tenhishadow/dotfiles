#!/bin/bash
set -euxo pipefail

export UV_PROJECT_ENVIRONMENT="/tmp/${RANDOM}"
export ANSIBLE_FORCE_COLOR="true"

check_system_package_targets() {
  local package
  local package_targets_file
  local -a system_package_targets
  local -a missing_package_targets=()

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

  for package in "${system_package_targets[@]}"; do
    if ! pacman -Si -- "${package}" >/dev/null 2>&1; then
      missing_package_targets+=("${package}")
    fi
  done

  if ((${#missing_package_targets[@]} > 0)); then
    printf '%s\n' 'Missing Arch package targets:' >&2
    printf '  - %s\n' "${missing_package_targets[@]}" >&2
    exit 1
  fi
}

pacman --disable-sandbox -Sy --noconfirm --needed --noprogressbar reflector go-task uv git sudo >/dev/null

sudo reflector \
  --ipv4 \
  --protocol https \
  --completion-percent 95 \
  --score 10 \
  --latest 30 \
  --fastest 10 \
  --threads 8 \
  --connection-timeout 1 \
  --download-timeout 2 \
  --save /etc/pacman.d/mirrorlist

pacman --disable-sandbox -Sy --noconfirm --noprogressbar >/dev/null
check_system_package_targets

go-task system -- --skip-tags pkg,aur

# idempotency
go-task system -- --skip-tags pkg,aur
