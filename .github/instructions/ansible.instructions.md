---
applyTo: "playbook_*.yml,inventory/**/*.yml,roles/**/*.yml,roles/**/*.j2,.test/**/*.yml,requirements.yml,ansible.cfg"
---

# Ansible Review Instructions

Use the root `AGENTS.md`, `roles/AGENTS.md`, and the nearest role or inventory
instructions for the contract. Naming, role prefixes, and English are checked
mechanically; focus review on behavior the checks cannot prove.

- Trace tag-scoped execution: required variables, guards, and validation must
  still run when only one feature is selected.
- Check check-mode handling when a package, binary, directory, or service does
  not exist yet; a dry run must not make host changes or silently claim apply
  behavior was tested.
- For time changes, compare VM, physical-host, container, CI, and disabled
  backends. VMs require Chrony; inspect service conflicts, validator ordering,
  native waiter migration, and rollback against `roles/system/README.md`.
- Reject cleanup that can remove foreign regular files or links. Trace source
  ownership and destination validation through the dotfiles role.
- Distinguish linked payloads from seeded baselines: runtime writers must not
  write through a repository symlink, and existing baseline files must survive.
- Check cron redirection order, dependency disappearance, and removal of the
  managed entry when disabled.
- Verify Ansible handlers only run after real configuration changes and that
  service guards remain valid when handlers execute.
- Review feature-disable and policy-removal behavior separately; skipping a
  feature is not proof that old files or services were removed.
- Select native contract or observable-state checks that demonstrate the
  changed behavior; document any host or VM validation gap. Do not require
  new tests that merely mirror task structure.
