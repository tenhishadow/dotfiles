# Package Maintenance and System Health Investigation

Read-only follow-up on 2026-09-05. This examines operating-system maintenance,
not only hardware. No package database was refreshed, no package installed or
removed, and no service restarted. Public repository databases were downloaded
into process memory for comparison; they did not replace pacman's local data.

## MT-01: Current Upgrade Candidates Are Known

Fresh official mirror databases represented 2,968 of the 3,118 installed
packages. Comparing versions with the installed libalpm comparator identified
**106 packages with newer versions** and zero represented packages newer than
the public metadata. The remaining 150 packages require separate provenance
and update review; they were not silently counted as up to date.

| Public database | HTTP Last-Modified, UTC |
| --- | --- |
| core | 2026-09-04 22:10:11 |
| extra | 2026-09-05 10:06:45 |
| multilib | 2026-09-05 00:17:55 |

Sources were the official mirror's
[core database](https://geo.mirror.pkgbuild.com/core/os/x86_64/core.db),
[extra database](https://geo.mirror.pkgbuild.com/extra/os/x86_64/extra.db), and
[multilib database](https://geo.mirror.pkgbuild.com/multilib/os/x86_64/multilib.db).
This is a dated version comparison, not a transaction resolver or a guarantee
of an installable upgrade set across subsequent mirror changes.

Selected candidates relevant to this workstation:

| Component | Installed | Available in the sampled database |
| --- | --- | --- |
| Stock kernel | 7.2.2.arch1-1 | 7.2.3.arch1-2 |
| Zen kernel | 7.2.2.zen1-1 | 7.2.3.zen1-2 |
| Mesa / Intel Vulkan | 1:26.2.1-1 | 1:26.2.2-1 |
| WirePlumber | 0.5.16-1 | 0.5.17-1 |
| Arch keyring | 20260727-1 | 20260902-1 |
| Chromium | 152.0.7977.64-1 | 152.0.7977.82-1 |
| Firefox | 154.0.1-1 | 155.0.1-1 |
| Code OSS package | 1.135.0-1 | 1.136.1-1 |
| curl | 8.21.0-1 | 8.22.0-1 |
| BuildKit | 0.32.2-1 | 0.33.0-1 |
| Rust | 1:1.98.0-1 | 1:1.98.1-1 |
| uv | 0.12.9-1 | 0.12.10-1 |

This is normal rolling-release maintenance, not proof of 106 broken or
vulnerable packages. A newer WirePlumber or kernel version is not evidence that
it fixes this user's historical dock event. Read release notes before claiming
a particular fix.

The future recommendation is one reviewed full upgrade after the boot-entry,
recovery, and root-headroom decisions. Do not install selected new libraries
against an intentionally stale system as a tuning shortcut. Kernel headers,
modules, both installed kernels, and generated boot artifacts must remain
consistent. The improved reviewable upgrade helper is in
[the development investigation](07-development-investigation.md).

## MT-02: Package Database Is Consistent; One Managed Directory Is Missing

`pacman -Dk` reported no database errors. A privileged file-presence query
covered approximately 1.09 million paths across all 3,118 packages. It found
exactly one missing packaged path: `/var/cache/pacman/pkg/`, owned by the
pacman package. All other package-presence summaries reported zero missing
files. Its missing directory explains the nonzero check exit.

This does not hash every binary or establish that installed software is
unmodified or nonmalicious. It is a file-presence and database-consistency
check only.

Pacman's installed mtree metadata specifies that directory as root-owned,
group root, mode 0755. The future corrective operation is small:

```bash
# Proposed only; this was not executed during the read-only audit.
sudo install -d -o root -g root -m 0755 /var/cache/pacman/pkg
```

Validate its ownership/mode and rerun `pacman -Qk pacman`. Do not remove a
newly populated cache as a rollback. Existing package-download and helper
behavior may recreate the directory, but the current packaged-path deviation
is confirmed. Its disappearance was not attributed to an unverified command
history.

## MT-03: No Observed Stale Executables in Selected Live Processes

The follow-up again found zero failed system units and zero failed user units.
Selected live desktop/system processes were checked for deleted executable
references and deleted system-library mappings, without reading memory,
arguments, environment contents, or application data.

The sample included systemd, NetworkManager, TuneD, containerd, dockerd,
KWin, Plasma, PipeWire, WirePlumber, Brave, Code OSS, and Electron processes.
It found no deleted executable reference and no deleted `/usr/lib` mapping
in those process classes.

This narrows one common post-upgrade problem: there is no observed stale
deleted executable/library in that sample. It does not prove that every
process or application is fully current, and does not substitute for checking
release-specific restart requirements.

## MT-04: Upgrade Review Is More Useful Than More Tuning Flags

The official Arch news page was checked for current manual-intervention and
maintenance notices. Two points affect policy:

- The June 2026 AUR incident notice explicitly calls for reviewing PKGBUILD and
  install-script changes. This reinforces a reviewed AUR update workflow;
  it is not evidence that any of the user's installed packages is malicious.
  [Arch AUR incident notice](https://archlinux.org/news/active-aur-malicious-packages-incident/)
- The April 2026 iptables transition moved the normal package to the nft
  backend. The inspected machine has that current package family. Ruleset
  interpretation must consider the actual backend, especially with Docker.
  [Arch iptables transition](https://archlinux.org/news/iptables-now-defaults-to-the-nft-backend/)

The July VirtualBox VNC extension migration is package-specific; the named
`virtualbox-ext-vnc` package was not installed in the queried database. It is
not a reason to run its documented removal/overwrite commands here.
[Arch extension migration notice](https://archlinux.org/news/virtualbox-ext-vnc-7212-2-requires-manual-intervention/)

The public Arch security tracker view retrieved during this pass prominently
contained older issues with unknown status. It was not sufficient evidence
for a comprehensive current vulnerability verdict. The audit therefore makes
no claim that a package is secure merely because this tracker did not produce
a current match. [Retrieved Arch security tracker](https://security.archlinux.org/)

## MT-05: Retention, Backups, and Ownership

The journal is intentionally capped at 50 MiB while also receiving Docker
workload output. The existing `atop` recorder retains coarse historical
measurements, but its raw process history was excluded. The simple improvement
is to select retention appropriate to intermittent problems, not to add
another overlapping monitoring stack.

No backup timer matching the checked common backup-tool names was present.
The installed-package query found rclone among the checked backup/sync tools.
Neither fact proves the presence or absence of a real backup: the user may
use external, manual, cloud, or differently scheduled recovery arrangements.
Rclone configuration and backup contents were not read. A restore test remains
a separate operation because it writes data and needs the owner's intended
backup source.

The ownership rule for future changes should stay explicit:

| Responsibility | Proposed owner |
| --- | --- |
| Package upgrades and `.pacnew` review | Deliberate maintenance workflow with prompts and recovery checks |
| Host services, limits, logging, and network policy | Existing explicit privileged Ansible layer |
| User shell, editor, terminal defaults | Existing managed dotfiles and mappings |
| Firmware, boot signing, recovery media | Separately reviewed operator procedure |
| Per-project runtime/compiler choices | Project configuration, not global speculative recompilation |

There is no need to replace Arch, add a second package manager, or turn every
manual choice into a background service. The useful maintenance improvements
are concrete: resolve the known package directory, preserve upgrade failure
status and review, manage cache retention, and keep boot/runtime artifacts in
sync. Every proposed change remains unapplied.
