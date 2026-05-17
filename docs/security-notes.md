# Security Notes

This repository is a personal Arch Linux workstation baseline, not a generic
hardening benchmark.

Some settings optimize for local workstation usability and may not be
appropriate for servers, shared systems, or regulated environments. Review the
intent and impact before applying privileged layers.

Review especially:

- SSHD authentication and session settings
- Docker group membership
- IPv6 disablement
- Browser extension and policy settings
- Thunderbird policy settings and profile separation
- AI client telemetry and prompt logging settings
- Sysctl tuning
- Package installation in the opt-in system layer
- npm, Yarn, pip, Terraform, K9s, and other user-level tool defaults

Do not treat these values as universally secure. Adapt them to the host, threat
model, users, and operational requirements.

Privacy-focused dotfiles can reduce background checks, notifications, telemetry,
or audit submissions. For example, npm audit submission is disabled by default
in the managed `.npmrc`; run `npm audit` explicitly when you want that registry
check for a project. Terraform checkpoint calls are also disabled; review
Terraform and provider updates explicitly when you want upgrade or security
bulletin signals.
