"""Exercise CI result gates, lint ownership, and PR-title injection handling."""

import json
import os
from pathlib import Path

import pytest
import yaml


def _yaml(repo_root: Path, path: str) -> dict:
    """Read workflow syntax without YAML 1.1 converting the on key to True."""
    return yaml.load(
        (repo_root / path).read_text(encoding="utf-8"), Loader=yaml.BaseLoader
    )


@pytest.fixture(name="workflow", scope="module")
def fixture_workflow(repo_root):
    """Load the validation workflow's real job graph."""
    return _yaml(repo_root, ".github/workflows/ansible.yml")


def test_required_gate_covers_all_validation_jobs(workflow):
    jobs = workflow["jobs"]
    gate = jobs["ci"]
    assert set(gate["needs"]) == set(jobs) - {"ci", "copilot_review"}
    assert gate["if"] == "always()"
    for name, job in jobs.items():
        if name in {"ci", "static", "copilot_review"}:
            continue
        prerequisites = job["needs"]
        if isinstance(prerequisites, str):
            prerequisites = [prerequisites]
        expected = (
            {"static"} if name == "super_linter" else {"static", "super_linter"}
        )
        assert set(prerequisites) == expected, name
        assert "always()" not in job.get("if", ""), name
        assert "continue-on-error" not in job, name
    # Workflow-wide filters leave required checks permanently pending.
    for event in ("pull_request", "push"):
        assert "paths" not in (workflow["on"][event] or {})
        assert "paths-ignore" not in (workflow["on"][event] or {})


@pytest.mark.parametrize(
    ("changed_job", "result", "expected"),
    [(None, "success", True), ("nvim", "skipped", True)]
    + [
        (job, result, False)
        for job in (
            "static",
            "super_linter",
            "ansible_exec",
            "nvim",
            "workstation_convergence",
        )
        for result in ("failure", "cancelled")
    ]
    + [(job, "skipped", False) for job in ("static", "super_linter")],
)
def test_result_gate_rejects_failures_cancellations_and_missing_lint_gates(
    run_command, workflow, changed_job, result, expected
):
    gate = workflow["jobs"]["ci"]
    results = {job: {"result": "success"} for job in gate["needs"]}
    if changed_job is not None:
        results[changed_job]["result"] = result
    completed = run_command(
        ["bash", "-euo", "pipefail", "-c", gate["steps"][0]["run"]],
        env={**os.environ, "RESULTS": json.dumps(results)},
    )
    assert (completed.returncode == 0) is expected, (
        completed.stdout + completed.stderr
    )


def test_super_linter_has_no_independent_trigger_or_write_permissions(
    repo_root,
):
    workflow = _yaml(repo_root, ".github/workflows/github-super-linter.yml")
    assert set(workflow["on"]) == {"workflow_call"}
    assert workflow["permissions"] == {"contents": "read"}


@pytest.mark.parametrize(
    "setting",
    [
        "MULTI_STATUS",
        "VALIDATE_ANSIBLE",
        "VALIDATE_BASH",
        "VALIDATE_GIT_COMMITLINT",
        "VALIDATE_GITHUB_ACTIONS",
        "VALIDATE_GITHUB_ACTIONS_ZIZMOR",
        "VALIDATE_MARKDOWN",
        "VALIDATE_PYTHON_RUFF",
        "VALIDATE_PYTHON_RUFF_FORMAT",
        "VALIDATE_SPELL_CODESPELL",
        "VALIDATE_YAML",
    ],
)
def test_super_linter_leaves_checks_owned_by_static_validation_disabled(
    repo_root, setting
):
    configuration = dict(
        line.split("=", 1)
        for line in (repo_root / ".github/super-linter.env")
        .read_text()
        .splitlines()
        if line and not line.startswith("#")
    )
    assert configuration[setting] == "false"


def test_title_edits_run_only_the_shared_cheap_title_action(
    workflow, repo_root
):
    title = _yaml(repo_root, ".github/workflows/pr-title.yml")
    assert "edited" in title["on"]["pull_request"]["types"]
    assert "edited" not in (workflow["on"]["pull_request"] or {}).get(
        "types", []
    )
    action = "./.github/actions/pr-title"
    assert any(
        step.get("uses") == action
        for step in title["jobs"]["pr-title"]["steps"]
    )
    steps = workflow["jobs"]["static"]["steps"]
    title_index = next(
        i for i, step in enumerate(steps) if step.get("uses") == action
    )
    setup_index = next(
        i
        for i, step in enumerate(steps)
        if step.get("uses") == "./.github/actions/setup"
    )
    assert title_index < setup_index
    assert steps[title_index]["if"] == "github.event_name == 'pull_request'"


@pytest.mark.parametrize("validator_status", [0, 1])
def test_title_action_preserves_untrusted_text_and_validator_exit_status(
    run_command, tmp_path, repo_root, validator_status
):
    steps = _yaml(repo_root, ".github/actions/pr-title/action.yml")["runs"][
        "steps"
    ]
    root = tmp_path
    binaries = root / "bin"
    binaries.mkdir()
    gh = binaries / "gh"
    gh.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        "assert sys.argv[1:] == ['api', 'repos/example/repository/pulls/42', "
        "'--jq', '.title']\n"
        "print(os.environ['CURRENT_TITLE'])\n",
        encoding="utf-8",
    )
    gh.chmod(0o755)
    npm = binaries / "npm"
    npm.write_text(
        "#!/usr/bin/env python3\n"
        "import pathlib, sys\n"
        "assert sys.argv[1] == 'ci'\n"
        "assert set(sys.argv[2:]) == "
        "{'--ignore-scripts', '--no-audit', '--no-fund'}\n"
        "assert pathlib.Path.cwd().parts[-3:] == "
        "('.github', 'tools', 'commitlint')\n",
        encoding="utf-8",
    )
    npm.chmod(0o755)
    validator = root / ".github/tools/commitlint/node_modules/.bin/commitlint"
    validator.parent.mkdir(parents=True)
    validator.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        "assert sys.argv[1:] == "
        "['--config', '.commitlintrc.yaml', '--strict']\n"
        "sys.stdout.write(sys.stdin.read())\n"
        "sys.exit(int(os.environ['VALIDATOR_STATUS']))\n",
        encoding="utf-8",
    )
    validator.chmod(0o755)
    title = 'fix: preserve $(touch "$MARKER") and `touch "$MARKER"` literally'
    environment = {
        **os.environ,
        "PATH": f"{binaries}{os.pathsep}{os.environ['PATH']}",
        "GITHUB_REPOSITORY": "example/repository",
        "GITHUB_WORKSPACE": str(root),
        "RUNNER_TEMP": str(root),
        "PR_NUMBER": "42",
        "PR_TITLE": "stale title from the original workflow event",
        "CURRENT_TITLE": title,
        "MARKER": str(root / "unexpected-command"),
        "VALIDATOR_STATUS": str(validator_status),
    }
    for step in steps:
        if "run" not in step:
            continue
        result = run_command(
            ["bash", "-euo", "pipefail", "-c", step["run"]],
            cwd=root / step.get("working-directory", "."),
            env=environment,
        )
        expected = validator_status if step is steps[-1] else 0
        assert result.returncode == expected, result.stdout + result.stderr
    assert title + "\n" == result.stdout
    assert not (root / "unexpected-command").exists()
