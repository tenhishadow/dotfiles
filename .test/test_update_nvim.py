"""Exercise the plugin updater's process exit contract without a network."""

import json
import os
import shutil

import pytest

NVIM = shutil.which("nvim")
pytestmark = pytest.mark.skipif(
    not NVIM, reason="Neovim is required for updater process tests"
)


@pytest.mark.parametrize(
    ("setup", "outcome"),
    [
        pytest.param(
            "", (0, True, "Updated all 1 Neovim plugins"), id="success"
        ),
        pytest.param(
            (
                "config.plugins.example._.tasks[1].has_errors = "
                "function() return true end"
            ),
            (1, True, "Plugin upgrade failed: example (fetch)"),
            id="task_failure",
        ),
        pytest.param(
            "config.plugins.example._.installed = false",
            (1, True, "Plugin was not installed: example"),
            id="missing_install",
        ),
        pytest.param(
            "config.plugins.example = nil",
            (1, False, "Locked plugin was excluded from the upgrade: example"),
            id="excluded_pin",
        ),
        pytest.param(
            (
                'vim.fn.mkdir(vim.fn.stdpath("data") .. '
                '"/mason/packages/example", "p")'
            ),
            (1, True, "Plugin upgrades must not install Mason tools"),
            id="mason_install",
        ),
        pytest.param(
            "vim.fn.has = function() return 0 end",
            (1, False, "Plugin upgrades require Neovim 0.11.3 or newer"),
            id="old_neovim",
        ),
    ],
)
def test_upgrade_outcomes_control_the_process_exit(
    run_command, setup, outcome, tmp_path, repo_root
):
    expected_status, did_update, message = outcome
    workspace = tmp_path
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
        "NVIM_TEST_UPDATER": str(repo_root / ".github/scripts/update_nvim.lua"),
    }
    completed = run_command(
        (NVIM, "--headless", "--clean", "-u", "NONE", "-l", str(script)),
        env=environment,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == expected_status, output
    assert message in output
    assert marker.exists() is did_update
