"""Contract tests for read-only workstation reporting."""

import sys
from pathlib import Path
from unittest import mock

import workstation_report as report


def test_tool_version_status_prints_resolved_path_and_version(monkeypatch):
    monkeypatch.setattr(report.shutil, "which", lambda _: "/usr/bin/example")
    run_check = mock.Mock(return_value=(True, "example 1.2.3\n"))
    monkeypatch.setattr(report, "run_check", run_check)

    assert report.tool_version_status("example") == (
        True,
        "example: path=/usr/bin/example; version=example 1.2.3",
    )
    run_check.assert_called_once_with(
        ["/usr/bin/example", "--version"], timeout=3
    )


def test_tool_version_status_marks_missing_component(monkeypatch):
    monkeypatch.setattr(report.shutil, "which", lambda _: None)
    assert report.tool_version_status("missing") == (
        False,
        "missing: path=missing; version=unavailable",
    )


def test_tool_group_returns_every_unavailable_component(monkeypatch, capsys):
    status = mock.Mock(
        side_effect=[
            (True, "present: path=/bin/present; version=1"),
            (False, "missing: path=missing; version=unavailable"),
        ]
    )
    monkeypatch.setattr(report, "tool_version_status", status)
    assert report.print_tool_group(
        (("present", ("--version",)), ("missing", ("--version",)))
    ) == ["missing"]
    output = capsys.readouterr().out
    assert "present: path=/bin/present; version=1" in output
    assert "missing: path=missing; version=unavailable" in output


def test_doctor_exit_is_nonzero_when_mandatory_component_is_unavailable(
    monkeypatch, capsys
):
    monkeypatch.setattr(report, "print_doctor", lambda: ["codex"])
    monkeypatch.setattr(sys, "argv", ["workstation_report.py", "doctor"])
    assert report.main() == 1
    assert "mandatory components unavailable: codex" in capsys.readouterr().err


def test_inventory_parser_keeps_baselines_separate_from_symlinks(
    tmp_path: Path, monkeypatch
):
    inventory = tmp_path / "dotfiles.yml"
    inventory.write_text(
        """\
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
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(report, "DOTFILES_VARS", inventory)
    mappings, baselines, directories, cleanup = (
        report.parse_dotfiles_inventory()
    )
    assert [entry["name"] for entry in mappings] == ["linked"]
    assert baselines == [
        {
            "name": "seeded",
            "payload": ".config/seeded",
            "dest": "/tmp/seeded",
            "mode": "0600",
        }
    ]
    assert not directories
    assert cleanup == ["/tmp/obsolete"]


def test_report_paths_match_fixed_role_config_directory(
    monkeypatch, tmp_path: Path
):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "unmanaged"))
    assert report.known_dotfiles_vars()["dotfiles_config_dir"] == str(
        tmp_path / ".config"
    )


def test_baseline_report_rejects_foreign_symlinks(tmp_path: Path, capsys):
    foreign_target = tmp_path / "foreign"
    foreign_target.write_text("local state\n", encoding="utf-8")
    destination = tmp_path / "baseline"
    destination.symlink_to(foreign_target)
    report.print_baseline_file(
        {
            "name": "baseline",
            "payload": ".config/htop/htoprc",
            "dest": str(destination),
        }
    )
    assert "conflict or existing path" in capsys.readouterr().out
