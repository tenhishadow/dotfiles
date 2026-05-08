---
applyTo: "playbook_*.yml,inventory/**/*.yml,roles/**/*.yml,requirements.yml,ansible.cfg"
---

# Ansible Review Instructions

- Enforce Ansible names as `<Domain> | <Verb> <object>` for plays, tasks, and
  handlers.
- Use short stable domains and preserve product casing, for example `SSHD`,
  `NTP`, `VS Code`, `Neovim`, and `systemd`.
- Use concise imperative verbs from the repo-wide verb set in `AGENTS.md`.
- Name include wrappers as `Run ... tasks`.
- Ensure every `notify` value matches a handler name exactly.
- Keep tags lowercase snake_case.
- Prefix role variables, registered facts, and non-trivial task-local vars with
  `dotfiles_`, `system_`, or `browser_policies_`.
- Use `loop_control.loop_var` for non-trivial loops instead of generic `item`.
- Keep role input validation in `tasks/validate.yml` when a role exposes a
  variable contract.
- Preserve split host vars under `inventory/host_vars/this_host/`.
- Preserve the default dotfiles contract: `playbook_install.yml` stays local,
  user-level, `become: false`, and includes only `roles/dotfiles`.
- Keep `roles/dotfiles` user-level and sudo-free.
- Dotfiles mapping entries must use `name`, relative `payload`, and absolute
  `dest`.
- Keep system and browser policy automation opt-in through their dedicated
  playbooks.
- Prefer FQCN modules and idempotent modules over `command` or `shell`.
- Require explicit owner, group, and mode for managed files under `/etc`.
- Keep package lists, path lists, policy targets, mappings, and cleanup lists
  declarative in inventory, defaults, or vars.
- Preserve upstream option key casing inside settings maps such as
  `system_sshd_settings`, `system_journald_settings`,
  `system_sysctl_settings`, and browser policy dictionaries.
- Prefer supported drop-ins under `/etc/*/*.d/` over direct upstream main-file
  edits.
- Require syntax and narrow behavior validation for touched playbooks or
  roles.
