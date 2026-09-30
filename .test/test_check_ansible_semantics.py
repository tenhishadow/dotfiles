"""Regression tests for repository-specific Ansible semantics."""

from pathlib import Path

import pytest

import check_ansible_semantics


@pytest.mark.parametrize("handler_role", ["alpha", "beta"])
def test_notify_resolves_only_handlers_in_its_role(
    tmp_path: Path, handler_role
):
    task_path = tmp_path / "roles/alpha/tasks/main.yml"
    task_path.parent.mkdir(parents=True)
    task_path.write_text(
        "---\n- name: Alpha | Run command\n"
        "  ansible.builtin.debug:\n    msg: alpha\n"
        "  notify: Service | Restart service\n",
        encoding="utf-8",
    )
    handler_path = tmp_path / f"roles/{handler_role}/handlers/main.yml"
    handler_path.parent.mkdir(parents=True)
    handler_path.write_text(
        "---\n- name: Service | Restart service\n"
        "  ansible.builtin.debug:\n    msg: service\n",
        encoding="utf-8",
    )

    errors = check_ansible_semantics.check_notify(tmp_path, [task_path])

    assert errors == (
        []
        if handler_role == "alpha"
        else [
            "roles/alpha/tasks/main.yml: notify "
            "'Service | Restart service' has no matching handler name"
        ]
    )
