"""Contract tests for read-only workstation reporting."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import workstation_report as report


class WorkstationReportTest(unittest.TestCase):
    """Validate deterministic doctor status and output."""

    @mock.patch.object(report.shutil, "which", return_value="/usr/bin/example")
    @mock.patch.object(report, "run_check", return_value=(True, "example 1.2.3\n"))
    def test_tool_version_status_prints_resolved_path_and_version(
        self,
        run_check: mock.Mock,
        _which: mock.Mock,
    ) -> None:
        available, line = report.tool_version_status("example")

        self.assertTrue(available)
        self.assertEqual(
            "example: path=/usr/bin/example; version=example 1.2.3",
            line,
        )
        run_check.assert_called_once_with(["/usr/bin/example", "--version"], timeout=3)

    @mock.patch.object(report.shutil, "which", return_value=None)
    def test_tool_version_status_marks_missing_component(
        self, _which: mock.Mock
    ) -> None:
        available, line = report.tool_version_status("missing")

        self.assertFalse(available)
        self.assertEqual(
            "missing: path=missing; version=unavailable",
            line,
        )

    @mock.patch.object(report, "tool_version_status")
    def test_tool_group_returns_every_unavailable_component(
        self, status: mock.Mock
    ) -> None:
        status.side_effect = (
            (True, "present: path=/bin/present; version=1"),
            (False, "missing: path=missing; version=unavailable"),
        )
        output = io.StringIO()

        with redirect_stdout(output):
            unavailable = report.print_tool_group(
                (("present", ("--version",)), ("missing", ("--version",)))
            )

        self.assertEqual(["missing"], unavailable)
        self.assertIn("present: path=/bin/present; version=1", output.getvalue())
        self.assertIn("missing: path=missing; version=unavailable", output.getvalue())

    @mock.patch.object(report, "print_doctor", return_value=["codex"])
    def test_doctor_exit_is_nonzero_when_mandatory_component_is_unavailable(
        self, _doctor: mock.Mock
    ) -> None:
        with (
            mock.patch.object(sys, "argv", ["workstation_report.py", "doctor"]),
            mock.patch.object(sys, "stderr", io.StringIO()) as stderr,
        ):
            result = report.main()

        self.assertEqual(1, result)
        self.assertIn("mandatory components unavailable: codex", stderr.getvalue())

    def test_inventory_parser_keeps_baselines_separate_from_symlinks(self) -> None:
        inventory_text = """\
dotfiles_mapping:
  - name: linked
    payload: .config/linked
    dest: /tmp/linked
dotfiles_baseline_files:
  - name: seeded
    payload: .config/seeded
    dest: /tmp/seeded
    mode: "0600"
dotfiles_cleanup_paths:
  - /tmp/obsolete
"""
        with tempfile.TemporaryDirectory() as temporary_directory:
            inventory = Path(temporary_directory) / "dotfiles.yml"
            inventory.write_text(inventory_text, encoding="utf-8")
            with mock.patch.object(report, "DOTFILES_VARS", inventory):
                mappings, baselines, directories, cleanup = (
                    report.parse_dotfiles_inventory()
                )

        self.assertEqual(["linked"], [entry["name"] for entry in mappings])
        self.assertEqual(
            [
                {
                    "name": "seeded",
                    "payload": ".config/seeded",
                    "dest": "/tmp/seeded",
                    "mode": "0600",
                }
            ],
            baselines,
        )
        self.assertEqual([], directories)
        self.assertEqual(["/tmp/obsolete"], cleanup)

    def test_report_paths_match_fixed_role_config_directory(self) -> None:
        with mock.patch.dict(
            report.os.environ,
            {"XDG_CONFIG_HOME": "/tmp/unmanaged-xdg-config"},
        ):
            variables = report.known_dotfiles_vars()

        self.assertEqual(
            str(Path.home() / ".config"),
            variables["dotfiles_config_dir"],
        )

    def test_baseline_report_rejects_foreign_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            foreign_target = temporary_path / "foreign"
            foreign_target.write_text("local state\n", encoding="utf-8")
            destination = temporary_path / "baseline"
            destination.symlink_to(foreign_target)
            output = io.StringIO()

            with redirect_stdout(output):
                report.print_baseline_file(
                    {
                        "name": "baseline",
                        "payload": ".config/htop/htoprc",
                        "dest": str(destination),
                    }
                )

        self.assertIn("conflict or existing path", output.getvalue())


if __name__ == "__main__":
    unittest.main()
