"""Exercise the plugin updater's process exit contract without a network."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NVIM = shutil.which("nvim")


@unittest.skipUnless(NVIM, "Neovim is required for its updater process tests")
class NeovimUpdateTest(unittest.TestCase):
    """Lazy task failures must prevent publication of the disposable lock."""

    def test_upgrade_outcomes_control_the_process_exit(self) -> None:
        cases = {
            "success": ("", 0, True, "Updated all 1 Neovim plugins"),
            "task_failure": (
                "config.plugins.example._.tasks[1].has_errors = "
                "function() return true end",
                1,
                True,
                "Plugin upgrade failed: example (fetch)",
            ),
            "missing_install": (
                "config.plugins.example._.installed = false",
                1,
                True,
                "Plugin was not installed: example",
            ),
            "excluded_pin": (
                "config.plugins.example = nil",
                1,
                False,
                "Locked plugin was excluded from the upgrade: example",
            ),
            "mason_install": (
                'vim.fn.mkdir(vim.fn.stdpath("data") .. '
                '"/mason/packages/example", "p")',
                1,
                True,
                "Plugin upgrades must not install Mason tools",
            ),
            "old_neovim": (
                "vim.fn.has = function() return 0 end",
                1,
                False,
                "Plugin upgrades require Neovim 0.11.3 or newer",
            ),
        }
        for name, (setup, expected_status, did_update, message) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                workspace = Path(directory)
                lock = workspace / "lazy-lock.json"
                lock.write_text(json.dumps({"example": {"commit": "old"}}))
                marker = workspace / "updated"
                script = workspace / "test.lua"
                script.write_text(
                    """
local config = {
  options = { lockfile = vim.env.NVIM_TEST_LOCK },
  plugins = { example = { _ = { installed = true, tasks = {
    { name = "fetch", has_errors = function() return false end },
  } } } },
}
package.preload["lazy.core.config"] = function() return config end
package.preload.lazy = function()
  return { update = function(opts)
    assert(opts.wait == true and opts.show == false)
    vim.fn.writefile({ "updated" }, vim.env.NVIM_TEST_MARKER)
  end }
end
"""
                    + setup
                    + "\ndofile(vim.env.NVIM_TEST_UPDATER)\n",
                    encoding="utf-8",
                )
                environment = {
                    **os.environ,
                    "HOME": str(workspace / "home"),
                    "XDG_CONFIG_HOME": str(workspace / "config"),
                    "XDG_DATA_HOME": str(workspace / "data"),
                    "XDG_STATE_HOME": str(workspace / "state"),
                    "XDG_CACHE_HOME": str(workspace / "cache"),
                    "NVIM_APPNAME": "nvim",
                    "NVIM_TEST_LOCK": str(lock),
                    "NVIM_TEST_MARKER": str(marker),
                    "NVIM_TEST_UPDATER": str(ROOT / ".github/scripts/update_nvim.lua"),
                }
                completed = subprocess.run(
                    (NVIM, "--headless", "--clean", "-u", "NONE", "-l", str(script)),
                    env=environment,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                output = completed.stdout + completed.stderr
                self.assertEqual(expected_status, completed.returncode, output)
                self.assertIn(message, output)
                self.assertEqual(did_update, marker.exists())


if __name__ == "__main__":
    unittest.main()
