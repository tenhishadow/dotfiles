"""Black-box regression tests for the managed OpenSSH client config."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SSH_CONFIG = ROOT / "dotfiles/.ssh/config"
INCLUDE_GLOBS = ("config.d/*", "conf.d/*")


def _effective_config(
    host: str, include_files: dict[str, str] | None = None
) -> dict[str, str]:
    with tempfile.TemporaryDirectory() as directory:
        test_root = Path(directory)
        config_lines = SSH_CONFIG.read_text(encoding="utf-8").splitlines()
        for include_glob in INCLUDE_GLOBS:
            directive = f"Include {include_glob}"
            matches = [
                index
                for index, line in enumerate(config_lines)
                if line.strip() == directive
            ]
            if len(matches) != 1:
                raise AssertionError(f"expected exactly one {directive!r}")
            config_lines[matches[0]] = f"Include {test_root / include_glob}"

        relative_includes = [
            line
            for line in config_lines
            if line.strip().startswith("Include ")
            and any(not pattern.startswith("/") for pattern in line.split()[1:])
        ]
        if relative_includes:
            raise AssertionError(
                f"test config contains relative includes: {relative_includes}"
            )

        config_path = test_root / "config"
        config_path.write_text("\n".join(config_lines) + "\n", encoding="utf-8")

        for relative_path, content in (include_files or {}).items():
            include_path = test_root / relative_path
            include_path.parent.mkdir(parents=True, exist_ok=True)
            include_path.write_text(content, encoding="utf-8")

        result = subprocess.run(
            ["ssh", "-G", "-F", str(config_path), host],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return {
            key: value
            for line in result.stdout.splitlines()
            for key, value in [line.split(maxsplit=1)]
        }


class SshConfigContractTest(unittest.TestCase):
    """Validate safe defaults and host-specific override precedence."""

    def test_default_host_verification_and_agent_forwarding_are_safe(self) -> None:
        config = _effective_config("default.example")

        self.assertEqual("no", config["forwardagent"])
        self.assertEqual("no", config["compression"])
        self.assertEqual("no", config["checkhostip"])
        self.assertEqual("yes", config["hashknownhosts"])
        self.assertEqual("no", config["kbdinteractiveauthentication"])
        self.assertEqual("no", config["passwordauthentication"])
        self.assertEqual("ask", config["stricthostkeychecking"])
        self.assertEqual("true", config["updatehostkeys"])

        known_hosts_files = config["userknownhostsfile"].split()
        self.assertTrue(
            any(path.endswith("/.ssh/known_hosts") for path in known_hosts_files)
        )
        self.assertNotIn("/dev/null", known_hosts_files)
        self.assertNotIn("none", known_hosts_files)

    def test_included_host_config_precedes_general_defaults(self) -> None:
        for include_dir in ("config.d", "conf.d"):
            with self.subTest(include_dir=include_dir):
                config = _effective_config(
                    "override.example",
                    {
                        f"{include_dir}/10-test.conf": """Host override.example
  ForwardAgent yes
  KbdInteractiveAuthentication yes
  StrictHostKeyChecking yes
"""
                    },
                )

                self.assertEqual("yes", config["forwardagent"])
                self.assertEqual("yes", config["kbdinteractiveauthentication"])
                self.assertEqual("true", config["stricthostkeychecking"])

    def test_all_include_directories_are_evaluated_at_top_level(self) -> None:
        config = _effective_config(
            "second.example",
            {
                "config.d/10-first.conf": """Host first.example
  Port 2201
""",
                "conf.d/10-second.conf": """Host second.example
  Port 2202
""",
            },
        )

        self.assertEqual("2202", config["port"])


if __name__ == "__main__":
    unittest.main()
