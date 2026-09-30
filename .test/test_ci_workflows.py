"""Exercise the required CI result gate and lint ownership contracts."""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _yaml(path: str) -> dict:
    # GitHub's YAML treats `on` as a string; BaseLoader avoids YAML 1.1 booleans.
    return yaml.load((ROOT / path).read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


class ValidationWorkflowTest(unittest.TestCase):
    """Prevent expensive checks escaping their gate or hiding failures."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = _yaml(".github/workflows/ansible.yml")
        cls.jobs = cls.workflow["jobs"]

    def test_required_gate_covers_all_validation_jobs(self) -> None:
        gate = self.jobs["ci"]
        self.assertEqual(set(self.jobs) - {"ci"}, set(gate["needs"]))
        self.assertEqual("always()", gate["if"])
        for name, job in self.jobs.items():
            if name in {"ci", "static"}:
                continue
            with self.subTest(job=name):
                self.assertEqual("static", job["needs"])
                self.assertNotIn("continue-on-error", job)
        # Workflow-wide path filters leave required checks permanently pending.
        for event in ("pull_request", "push"):
            self.assertNotIn("paths", self.workflow["on"][event] or {})
            self.assertNotIn("paths-ignore", self.workflow["on"][event] or {})

    def test_result_gate_rejects_failures_cancellations_and_missing_static(
        self,
    ) -> None:
        command = self.jobs["ci"]["steps"][0]["run"]
        cases = [("success", None, "success", True)]
        cases.append(("unrelated paths", "nvim", "skipped", True))
        for job in self.jobs["ci"]["needs"]:
            for result in ("failure", "cancelled"):
                cases.append((f"{job} {result}", job, result, False))
        cases.append(("missing static", "static", "skipped", False))

        for name, changed_job, result, expected in cases:
            with self.subTest(case=name):
                results = {
                    job: {"result": "success"} for job in self.jobs["ci"]["needs"]
                }
                if changed_job is not None:
                    results[changed_job]["result"] = result
                completed = subprocess.run(
                    ["bash", "-euo", "pipefail", "-c", command],
                    env={**os.environ, "RESULTS": json.dumps(results)},
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                self.assertEqual(
                    expected,
                    completed.returncode == 0,
                    completed.stdout + completed.stderr,
                )

    def test_super_linter_uses_shared_complementary_checks_without_write_access(
        self,
    ) -> None:
        workflow = _yaml(".github/workflows/github-super-linter.yml")
        self.assertEqual({"workflow_call"}, set(workflow["on"]))
        self.assertEqual({"contents": "read"}, workflow["permissions"])
        configuration = dict(
            line.split("=", 1)
            for line in (ROOT / ".github/super-linter.env").read_text().splitlines()
            if line and not line.startswith("#")
        )
        for key in (
            "MULTI_STATUS",
            "VALIDATE_ANSIBLE",
            "VALIDATE_BASH",
            "VALIDATE_GIT_COMMITLINT",
            "VALIDATE_GITHUB_ACTIONS",
            "VALIDATE_GITHUB_ACTIONS_ZIZMOR",
            "VALIDATE_MARKDOWN",
            "VALIDATE_PYTHON_RUFF",
            "VALIDATE_PYTHON_RUFF_FORMAT",
            "VALIDATE_YAML",
        ):
            with self.subTest(setting=key):
                self.assertEqual("false", configuration[key])
        commands = "\n".join(
            step.get("run", "")
            for step in workflow["jobs"]["github-super-linter"]["steps"]
        )
        self.assertIn(".github/super-linter.env", commands)
        self.assertIn(
            "--env-file .github/super-linter.env", (ROOT / "Taskfile.yml").read_text()
        )

    def test_title_edits_do_not_rerun_integration_and_use_locked_conventional_rules(
        self,
    ) -> None:
        title = _yaml(".github/workflows/pr-title.yml")
        self.assertIn("edited", title["on"]["pull_request"]["types"])
        self.assertNotIn(
            "edited", (self.workflow["on"]["pull_request"] or {}).get("types", [])
        )
        steps = title["jobs"]["pr-title"]["steps"]
        check = next(step for step in steps if "PR_TITLE" in step.get("env", {}))
        self.assertNotIn("${{", check["run"])
        self.assertIn('"${PR_TITLE}"', check["run"])
        self.assertIn("--config .commitlintrc.yaml", check["run"])
        manifest = json.loads(
            (ROOT / ".github/tools/commitlint/package.json").read_text()
        )
        self.assertEqual(
            {"@commitlint/cli", "@commitlint/config-conventional"},
            set(manifest["dependencies"]),
        )
        self.assertTrue(
            any("npm ci --ignore-scripts" in step.get("run", "") for step in steps)
        )


if __name__ == "__main__":
    unittest.main()
