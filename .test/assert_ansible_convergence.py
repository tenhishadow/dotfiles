"""Fail unless Ansible JSON recaps prove a clean convergence pass."""

from __future__ import annotations

import json
import sys
from pathlib import Path

CONVERGENCE_COUNTERS = (
    "changed",
    "failures",
    "ignored",
    "rescued",
    "unreachable",
)


def check_recap(path: Path) -> list[str]:
    """Return convergence violations found in one Ansible JSON result."""
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"cannot read Ansible JSON: {error}"]

    if not isinstance(result, dict) or not isinstance(result.get("stats"), dict):
        return ["Ansible JSON is missing the stats mapping"]
    if not result["stats"]:
        return ["Ansible JSON contains no host stats"]

    violations = []
    for host, recap in sorted(result["stats"].items()):
        if not isinstance(recap, dict):
            violations.append(f"{host}: recap is not a mapping")
            continue
        nonzero = {
            counter: recap.get(counter, 0)
            for counter in CONVERGENCE_COUNTERS
            if recap.get(counter, 0) != 0
        }
        if nonzero:
            details = ", ".join(f"{key}={value}" for key, value in nonzero.items())
            violations.append(f"{host}: {details}")
    return violations


def main() -> int:
    """Check every result path provided on the command line."""
    if len(sys.argv) < 2:
        print(
            "usage: assert_ansible_convergence.py <ansible-result.json> [...]",
            file=sys.stderr,
        )
        return 2

    failed = False
    for path_arg in sys.argv[1:]:
        path = Path(path_arg)
        violations = check_recap(path)
        if violations:
            failed = True
            print(f"{path.stem}: convergence failed", file=sys.stderr)
            for violation in violations:
                print(f"  {violation}", file=sys.stderr)
        else:
            print(f"{path.stem}: converged with no changes or hidden failures")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
