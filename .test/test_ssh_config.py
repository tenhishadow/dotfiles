"""Black-box regression tests for the owner's managed OpenSSH policy."""

from pathlib import Path

import pytest

INCLUDE_GLOBS = ("config.d/*", "conf.d/*")


def _effective_config(
    run_command,
    repo_root: Path,
    tmp_path: Path,
    host: str,
    *extra_args: str,
    include_files: dict[str, str] | None = None,
) -> dict[str, str]:
    """Resolve the real SSH configuration without reading private includes."""
    config_lines = (
        (repo_root / "dotfiles/.ssh/config")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    for include_glob in INCLUDE_GLOBS:
        directive = f"Include {include_glob}"
        matches = [
            index
            for index, line in enumerate(config_lines)
            if line.strip() == directive
        ]
        assert len(matches) == 1, f"expected exactly one {directive!r}"
        config_lines[matches[0]] = f"Include {tmp_path / include_glob}"
    relative_includes = [
        line
        for line in config_lines
        if line.strip().startswith("Include ")
        and any(not pattern.startswith("/") for pattern in line.split()[1:])
    ]
    assert not relative_includes, (
        f"test config contains relative includes: {relative_includes}"
    )
    (tmp_path / "config").write_text(
        "\n".join(config_lines) + "\n", encoding="utf-8"
    )
    for relative_path, content in (include_files or {}).items():
        include_path = tmp_path / relative_path
        include_path.parent.mkdir(parents=True, exist_ok=True)
        include_path.write_text(content, encoding="utf-8")
    result = run_command(
        ["ssh", "-G", "-F", str(tmp_path / "config"), *extra_args, host],
        check=True,
    )
    return dict(line.split(maxsplit=1) for line in result.stdout.splitlines())


def test_default_host_follows_owner_policy(run_command, repo_root, tmp_path):
    config = _effective_config(
        run_command, repo_root, tmp_path, "default.example"
    )
    expected = {
        "forwardagent": "yes",
        "compression": "yes",
        "checkhostip": "no",
        "hashknownhosts": "no",
        "kbdinteractiveauthentication": "no",
        "passwordauthentication": "no",
        "stricthostkeychecking": "false",
        # Keeping no host keys and rewriting host key files are contradictory,
        # so host-key learning stays off. See the comment in the config.
        "updatehostkeys": "false",
        "userknownhostsfile": "/dev/null",
    }
    assert {key: config[key] for key in expected} == expected


def test_a_caller_supplied_known_hosts_file_is_never_rewritten(
    run_command, repo_root, tmp_path
):
    """Proxmox passes its own pmxcfs known_hosts file on the command line.

    pmxcfs cannot hardlink, so any attempt to rewrite that file fails with
    EPERM. The policy must never ask ssh to write host keys, whatever file a
    caller points it at.
    """
    config = _effective_config(
        run_command,
        repo_root,
        tmp_path,
        "cluster.example",
        "-o",
        "UserKnownHostsFile=/etc/pve/nodes/cluster/ssh_known_hosts",
    )
    assert config["userknownhostsfile"] == (
        "/etc/pve/nodes/cluster/ssh_known_hosts"
    )
    assert config["updatehostkeys"] == "false"


@pytest.mark.parametrize("include_dir", ["config.d", "conf.d"])
def test_included_host_config_precedes_general_defaults(
    run_command, repo_root, tmp_path, include_dir
):
    config = _effective_config(
        run_command,
        repo_root,
        tmp_path,
        "override.example",
        include_files={
            f"{include_dir}/10-test.conf": """Host override.example
  ForwardAgent no
  KbdInteractiveAuthentication yes
  StrictHostKeyChecking yes
""",
        },
    )
    assert config["forwardagent"] == "no"
    assert config["kbdinteractiveauthentication"] == "yes"
    assert config["stricthostkeychecking"] == "true"


def test_all_include_directories_are_evaluated_at_top_level(
    run_command, repo_root, tmp_path
):
    config = _effective_config(
        run_command,
        repo_root,
        tmp_path,
        "second.example",
        include_files={
            "config.d/10-first.conf": "Host first.example\n  Port 2201\n",
            "conf.d/10-second.conf": "Host second.example\n  Port 2202\n",
        },
    )
    assert config["port"] == "2202"
