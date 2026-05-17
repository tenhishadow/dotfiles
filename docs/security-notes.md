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
- Sysctl tuning
- Package installation in the opt-in system layer

Do not treat these values as universally secure. Adapt them to the host, threat
model, users, and operational requirements.
