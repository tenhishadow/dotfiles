"""Regression tests for repository-specific Ansible semantics."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import check_ansible_semantics


def _write(root: Path, relative: str, content: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class NotifyScopeTest(unittest.TestCase):
    """Keep literal notify values scoped to their owning role."""

    def test_handler_in_another_role_does_not_satisfy_notify(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task_path = _write(
                root,
                "roles/alpha/tasks/main.yml",
                """---
- name: Alpha | Run command
  ansible.builtin.debug:
    msg: alpha
  notify: Beta | Restart service
""",
            )
            _write(
                root,
                "roles/beta/handlers/main.yml",
                """---
- name: Beta | Restart service
  ansible.builtin.debug:
    msg: beta
""",
            )

            self.assertEqual(
                [
                    "roles/alpha/tasks/main.yml: notify "
                    "'Beta | Restart service' has no matching handler name"
                ],
                check_ansible_semantics.check_notify(root, [task_path]),
            )


if __name__ == "__main__":
    unittest.main()
