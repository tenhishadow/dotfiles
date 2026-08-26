"""Tests for machine-readable Ansible convergence recaps."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import assert_ansible_convergence


def _check_text(content: str) -> list[str]:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "result.json"
        path.write_text(content, encoding="utf-8")
        return assert_ansible_convergence.check_recap(path)


class AnsibleConvergenceTest(unittest.TestCase):
    """Validate clean, dirty, and malformed recap handling."""

    def test_clean_recap_has_no_violations(self) -> None:
        result = {"stats": {"host": {"changed": 0, "failures": 0}}}
        self.assertEqual([], _check_text(json.dumps(result)))

    def test_nonzero_counters_are_reported_together(self) -> None:
        recap = {
            "changed": 1,
            "failures": 2,
            "ignored": 3,
            "rescued": 4,
            "unreachable": 5,
        }
        self.assertEqual(
            ["host: changed=1, failures=2, ignored=3, rescued=4, unreachable=5"],
            _check_text(json.dumps({"stats": {"host": recap}})),
        )

    def test_malformed_results_are_rejected(self) -> None:
        cases = (
            ("not JSON", "cannot read Ansible JSON"),
            (json.dumps({}), "missing the stats mapping"),
            (json.dumps({"stats": {}}), "contains no host stats"),
            (json.dumps({"stats": {"host": []}}), "recap is not a mapping"),
        )
        for content, expected in cases:
            with self.subTest(content=content):
                self.assertTrue(
                    any(expected in violation for violation in _check_text(content))
                )


if __name__ == "__main__":
    unittest.main()
