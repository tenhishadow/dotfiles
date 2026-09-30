"""Tests for machine-readable Ansible convergence recaps."""

import json
from pathlib import Path

import pytest

import assert_ansible_convergence


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (json.dumps({"stats": {"host": {"changed": 0, "failures": 0}}}), []),
        (
            json.dumps(
                {
                    "stats": {
                        "host": {
                            "changed": 1,
                            "failures": 2,
                            "ignored": 3,
                            "rescued": 4,
                            "unreachable": 5,
                        }
                    }
                }
            ),
            [
                "host: changed=1, failures=2, ignored=3, "
                "rescued=4, unreachable=5"
            ],
        ),
    ],
    ids=["clean", "all-nonzero-counters"],
)
def test_recap_reports_all_violations(tmp_path: Path, content, expected):
    path = tmp_path / "result.json"
    path.write_text(content, encoding="utf-8")
    assert assert_ansible_convergence.check_recap(path) == expected


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("not JSON", "cannot read Ansible JSON"),
        ("{}", "missing the stats mapping"),
        ('{"stats": {}}', "contains no host stats"),
        ('{"stats": {"host": []}}', "recap is not a mapping"),
    ],
    ids=["invalid-json", "missing-stats", "empty-stats", "invalid-host"],
)
def test_malformed_results_are_rejected(tmp_path: Path, content, expected):
    path = tmp_path / "result.json"
    path.write_text(content, encoding="utf-8")
    assert any(
        expected in error
        for error in assert_ansible_convergence.check_recap(path)
    )
