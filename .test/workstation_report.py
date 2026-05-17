#!/usr/bin/env python3
"""Read-only workstation reports for dotfiles adoption and review."""

# pylint: disable=missing-function-docstring

from __future__ import annotations

import argparse
import getpass
import grp
import os
import pwd
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOTFILES_VARS = ROOT / "inventory/host_vars/this_host/dotfiles.yml"


def run_check(command: list[str], timeout: int = 5) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        return False, str(error)
    output = (result.stdout or result.stderr).strip()
    return result.returncode == 0, output


def section(title: str) -> None:
    print(f"\n== {title} ==")


def status(path: Path) -> str:
    if path.exists():
        return "exists"
    if path.is_symlink():
        return "broken symlink"
    return "missing"


def read_os_release() -> dict[str, str]:
    values: dict[str, str] = {}
    os_release = Path("/etc/os-release")
    if not os_release.is_file():
        return values
    for line in os_release.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"')
    return values


def tool_line(command: str) -> str:
    path = shutil.which(command)
    return f"{command}: {path or 'missing'}"


def known_dotfiles_vars() -> dict[str, str]:
    home = Path.home()
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    ssh_dir = home / ".ssh"
    nvim_state = home / ".local/state/nvim"
    return {
        "dotfiles_home": str(home),
        "dotfiles_config_dir": str(config_home),
        "dotfiles_bashrc_dir": str(home / ".bashrc.d"),
        "dotfiles_gnupg_dir": str(home / ".gnupg"),
        "dotfiles_ssh_dir": str(ssh_dir),
        "dotfiles_ssh_config_dir": str(ssh_dir / "config.d"),
        "dotfiles_nvim_state_dir": str(nvim_state),
        "dotfiles_nvim_restore_log_path": str(nvim_state / "lazy-restore.log"),
        "dotfiles_nvim_restore_lock_path": str(nvim_state / "lazy-restore.lock"),
    }


def render_value(value: str) -> str:
    value = value.strip().strip('"').strip("'")
    variables = known_dotfiles_vars()

    def replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        return variables.get(key, match.group(0))

    return re.sub(r"\{\{\s*([^}]+?)\s*\}\}", replace, value)


def parse_dotfiles_inventory() -> tuple[list[dict[str, str]], list[str], list[str]]:
    mappings: list[dict[str, str]] = []
    directories: list[str] = []
    cleanup: list[str] = []
    current_section = ""
    current_mapping: dict[str, str] | None = None

    for raw_line in DOTFILES_VARS.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if line.startswith("dotfiles_directories:"):
            current_section = "directories"
            current_mapping = None
            continue
        if line.startswith("dotfiles_mapping:"):
            current_section = "mapping"
            current_mapping = None
            continue
        if line.startswith("dotfiles_cleanup_paths:"):
            current_section = "cleanup"
            current_mapping = None
            continue

        stripped = line.strip()
        if current_section == "directories" and stripped.startswith("- path:"):
            directories.append(render_value(stripped.split(":", 1)[1]))
            continue
        if current_section == "cleanup" and stripped.startswith("- "):
            cleanup.append(render_value(stripped[2:]))
            continue
        if current_section != "mapping":
            continue
        if stripped.startswith("- name:"):
            current_mapping = {"name": stripped.split(":", 1)[1].strip()}
            mappings.append(current_mapping)
            continue
        if current_mapping is None or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        if key in {"payload", "dest"}:
            current_mapping[key] = render_value(value)

    return mappings, directories, cleanup


def print_doctor() -> None:
    os_release = read_os_release()
    section("Host")
    print(f"os: {os_release.get('PRETTY_NAME', 'unknown')}")
    print(f"user: {getpass.getuser()}")
    print(f"home: {Path.home()}")

    section("Tools")
    for command in ("uv", "git", "go-task", "docker", "crontab", "systemctl"):
        print(tool_line(command))

    docker_ok, docker_output = run_check(["docker", "info"])
    print(f"docker daemon: {'available' if docker_ok else 'unavailable'}")
    if not docker_ok and docker_output:
        print(f"docker daemon detail: {docker_output.splitlines()[0]}")

    systemctl_path = shutil.which("systemctl")
    systemd_ok = Path("/run/systemd/system").is_dir()
    print(
        f"systemd runtime: {'available' if systemctl_path and systemd_ok else 'unavailable'}"
    )


def print_dotfiles_plan() -> None:
    mappings, directories, cleanup = parse_dotfiles_inventory()
    section("Dotfiles Destinations")
    for mapping in mappings:
        name = mapping.get("name", "unnamed")
        dest = Path(mapping.get("dest", ""))
        payload = ROOT / "dotfiles" / mapping.get("payload", "")
        if dest.is_symlink() and dest.resolve() == payload.resolve():
            state = "managed symlink"
        elif dest.exists() or dest.is_symlink():
            state = "conflict or existing path"
        else:
            state = "missing"
        print(f"{name}: {dest} -> {state}")

    section("Extra Directories")
    for directory in directories:
        print(f"{directory}: {status(Path(directory))}")

    section("Explicit Cleanup Paths")
    for path in cleanup:
        print(f"{path}: {status(Path(path))}")


def print_system_report() -> None:
    managed_paths = [
        "/etc/pacman.conf",
        "/etc/xdg/reflector/reflector.conf",
        "/etc/locale.gen",
        "/etc/locale.conf",
        "/etc/vconsole.conf",
        "/etc/motd",
        "/etc/issue",
        "/etc/sysctl.d/999-ansible.conf",
        "/etc/security/limits.d/10-dotfiles.conf",
        "/etc/modprobe.d/99-dotfiles-overlay.conf",
        "/etc/docker/daemon.json",
        "/etc/systemd/journald.conf.d/10-dotfiles.conf",
        "/etc/systemd/timesyncd.conf.d/10-dotfiles.conf",
        "/etc/ssh/sshd_config.d/20-dotfiles.conf",
    ]
    section("Managed System Paths")
    for path in managed_paths:
        print(f"{path}: {status(Path(path))}")

    section("Docker Group")
    user = getpass.getuser()
    groups = {group.gr_name for group in grp.getgrall() if user in group.gr_mem}
    try:
        primary_group = grp.getgrgid(pwd.getpwnam(user).pw_gid).gr_name
        groups.add(primary_group)
    except KeyError:
        pass
    print("docker group membership: " + ("present" if "docker" in groups else "absent"))
    print("docker group grants root-equivalent access to the Docker daemon.")

    section("SSHD Include")
    sshd_config = Path("/etc/ssh/sshd_config")
    if not sshd_config.is_file():
        print("/etc/ssh/sshd_config: missing")
        return
    if not os.access(sshd_config, os.R_OK):
        print("/etc/ssh/sshd_config: not readable")
        return
    include_seen = any(
        line.strip() == "Include /etc/ssh/sshd_config.d/*.conf"
        for line in sshd_config.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines()
    )
    print(
        "Include /etc/ssh/sshd_config.d/*.conf: "
        + ("present" if include_seen else "missing")
    )


def print_browser_policies_report() -> None:
    policy_paths = [
        "/etc/brave/policies/managed/10-dotfiles-managed.json",
        "/etc/firefox/policies/policies.json",
        "/etc/thunderbird/policies/policies.json",
        "/etc/vscode/policy.json",
    ]
    section("Policy Files")
    for path in policy_paths:
        print(f"{path}: {status(Path(path))}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "report",
        choices=("doctor", "dotfiles-plan", "system-report", "browser-policies-report"),
    )
    args = parser.parse_args()

    if args.report == "doctor":
        print_doctor()
    elif args.report == "dotfiles-plan":
        print_dotfiles_plan()
    elif args.report == "system-report":
        print_system_report()
    elif args.report == "browser-policies-report":
        print_browser_policies_report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
