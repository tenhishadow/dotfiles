#!/usr/bin/env python3
"""Assert workstation_report.py managed paths match the Ansible role variables.

Reads the JSON manifest rendered by managed_paths.yml and compares it against
the literal path lists in workstation_report.py. Any drift (a path changed in
the role variables but not in the report, or vice versa) fails, which keeps the
dependency-light report honest without giving it a runtime YAML dependency.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from workstation_report import BROWSER_POLICY_PATHS, SYSTEM_MANAGED_PATHS

GROUPS = {
    "system": SYSTEM_MANAGED_PATHS,
    "browser_policies": BROWSER_POLICY_PATHS,
}


def main() -> int:
    """Compare the rendered manifest with the report path constants."""
    if len(sys.argv) != 2:
        print("usage: check_managed_paths.py <manifest.json>", file=sys.stderr)
        return 2

    manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

    mismatches = []
    for group, report_paths in GROUPS.items():
        ansible_paths = manifest.get(group, [])
        if ansible_paths != report_paths:
            mismatches.append((group, ansible_paths, report_paths))

    if mismatches:
        print("managed path drift between Ansible and workstation_report.py:")
        for group, ansible_paths, report_paths in mismatches:
            only_ansible = [p for p in ansible_paths if p not in report_paths]
            only_report = [p for p in report_paths if p not in ansible_paths]
            print(f"  [{group}]")
            for path in only_ansible:
                print(f"    only in Ansible: {path}")
            for path in only_report:
                print(f"    only in report:  {path}")
            if not only_ansible and not only_report:
                print("    same paths, different order")
        return 1

    total = sum(len(paths) for paths in GROUPS.values())
    print(f"managed paths consistent: {total} paths match the Ansible variables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
