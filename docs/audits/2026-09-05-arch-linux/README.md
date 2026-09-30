# Arch Linux Workstation Audit

Completed read-only investigation on 2026-09-05, Europe/Warsaw. The scope is
**the whole ThinkPad workstation**, including boot, firmware, desktop,
network, services, development tools, containers, and storage. Three
specialist agents and a coordinating reviewer performed two passes and
cross-checked their conclusions.

Start with [the final decisions and implementation order](10-read-only-conclusions.md).
The subsequently authorized changes are recorded in
[boot maintenance](14-boot-maintenance.md) and
[TuneD/Plasma integration](15-tuned-plasma-integration.md), followed by
[periodic TRIM](16-trim-and-boot-review.md). Other proposals remain unapplied.
There are no commits or pushes.

This directory is a dated evidence record. Its host measurements, applied-state
claims, and validation results describe the sessions recorded below, not the
current checkout or host. Use the current role manuals and architecture for
the maintained contract; repository-only maintenance does not repeat these
hardware or privileged checks.

The latest requested read-only follow-up is the
[complete audio stack review](17-audio-stack-review.md), with separate
[Bluetooth](18-audio-bluetooth.md) and
[hardware/dock](19-audio-hardware-dock.md) reports. It confirms the modern
baseline, identifies duplicate internal audio endpoints, and narrows the
historical error interpretation. No audio configuration was changed.

## Main Result

The existing Arch installation is a sound baseline with several specific
correctness, maintenance, and usability improvements. Hardware rendering,
modern CPU/memory mechanisms, container integration, and the encrypted boot
stack already work. The observations do not justify reinstalling Arch,
rebuilding every package, or copying a distribution-wide tuning bundle.

The most useful findings are:

| Area | Confirmed finding | Implication |
| --- | --- | --- |
| Boot selection | Initial default did not match the actual entry ID; subsequently corrected to `arch.conf` | Stock kernel is now the explicit baseline; reboot verification remains pending |
| Firmware | BIOS 1.42, ME 16.1.42.2872, and dock 10.20 are offered for the actual devices | Schedule reviewed security/reliability maintenance; no update was applied |
| EFI maintenance | Subsequently updated the ESP loader from systemd-boot 259.1 to installed 261.2 | Existing update mechanism now owns maintenance; see the applied boot record |
| Shell responsiveness | Tested completion fragment improved from 167.92 to 17.65 ms median in isolation | About 150 ms of measured avoidable initialization work, not a full-system speedup |
| CLI correctness | Managed Task completion registers `task` instead of `go-task` | A tested deferred completion proposal fixes the command name |
| Editor | Python formatting runs Ruff and Black consecutively | Use the formatter selected by the project; Ruff alone fits this repository |
| Package maintenance | Fresh official metadata identifies 106 newer package versions; one packaged cache directory is missing | Review a full update and the small directory correction; this is not proof of 106 vulnerable packages |
| Power UI | TuneD/Plasma bridge subsequently implemented in Ansible and verified live | Integration is complete; see its applied change record |
| Audio | Modern PipeWire stack; duplicate internal HDMI/microphone nodes; historical errors follow specific transitions | Investigate graph lifecycle and test routing; no global audio tuning justified |
| Desktop | Hardware-rendered Wayland, disabled animation delays, inactive Baloo, no extra compositor | Preserve this working baseline; consider display refresh/text tradeoffs separately |
| Network | Wired adapter supports 2.5 Gb/s but negotiates 1 Gb/s; link errors are zero | Check the peer port before blaming Arch; no network bottleneck was measured |
| Network policy | IPv6 is disabled, including loopback; Docker forwarding rules are not a host input firewall | Make dev-feature and LAN-exposure policies explicit |
| Capacity | About 65.6 GiB of root allocation is Docker; approximately 2.935 TiB of VG extents are free | Planned root headroom is preferable to indiscriminate cache or volume deletion |
| SSD health | Internal SMART reports 1% used, zero media errors, and no critical warning | No evidence that current use is rapidly wearing out the internal SSD |
| Storage policy | Periodic TRIM subsequently enabled through Ansible; ext4 still uses `commit=120` | TRIM completed successfully; commit-interval change remains a recommendation |

Evidence, qualifications, source links, and validation methods are in the
reports below. Values are dated observations and must be rechecked before
implementation.

## Current Reports

| Report | Coverage |
| --- | --- |
| [Complete audio stack review](17-audio-stack-review.md) | Engine, compatibility paths, services, routing, duplicate nodes, latency, optional JACK integration, and Ansible ownership |
| [Bluetooth audio](18-audio-bluetooth.md) | Intel controller, Sony LDAC/HFP, codec limits, reconnect and voice warnings, and optional desktop preferences |
| [Audio hardware and dock](19-audio-hardware-dock.md) | SOF/ALSA/UCM, microphones, HDMI, USB audio, precise removal chronology, and power behavior |
| [TRIM and boot review](16-trim-and-boot-review.md) | Applied timer, commit-interval recommendation, and read-only kernel/initramfs review |
| [Applied TuneD/Plasma integration](15-tuned-plasma-integration.md) | Desktop profile selection, scoped performance profile, live verification, and backups |
| [Applied boot maintenance](14-boot-maintenance.md) | Explicit stock-kernel default, EFI update, verified backups, and pending reboot verification |
| [Final decisions](10-read-only-conclusions.md) | Whole-system verdict, priorities, what to keep, completed questions, and the boundary of read-only proof |
| [Boot, firmware, and power](08-boot-firmware-power-investigation.md) | Actual boot images and loader, firmware releases, stock/Zen comparison, verified-boot design, power mapping and passive measurements |
| [Desktop experience](12-desktop-investigation.md) | Rendering, display/scaling/fonts, application resource usage, portals, indexers, autostart and settings ownership |
| [Network and services](11-network-services-investigation.md) | Links, routing, DNS, IPv6, ingress policy, services, container limits, OOM and time synchronization |
| [Development follow-up](07-development-investigation.md) | Isolated measurements, tested completion/update/formatter proposals, Git settings, and all 112 orphan candidates classified |
| [Package maintenance](13-maintenance-investigation.md) | Current public-version comparison, database/file-presence checks, selected live libraries, upgrade news and recovery limits |
| [Dock and sleep](06-dock-sleep-investigation.md) | Precise disconnect/sleep chronology and the one post-disconnect audio retry burst |
| [Storage follow-up](09-storage-investigation.md) | SMART, exact LVM capacity, crypto geometry, filesystem reserves, power state, and concrete maintenance proposals |
| [Tuning and distributions](04-tuning-options.md) | CachyOS/Manjaro comparison, conditional experiments and unsupported tuning ideas |

The initial reports remain as dated first-pass snapshots:
[storage](01-storage.md), [boot/power/desktop](02-boot-power-desktop.md),
[development](03-development.md), and [the initial follow-up plan](05-follow-up-tasks.md).
Use the current investigations and final decisions when they supersede an
earlier permission gap or broader initial interpretation.

## Important Corrections After the First Pass

The external enclosure's read errors preceded actual kernel hibernation
entry by approximately 3.55 seconds. This rules out blaming the initial
errors on a kernel sleep transition that had not yet begun. It does not
identify who or what disconnected the hardware. Cross-source timestamps do
not support a stronger precise claim about the desktop's request ordering.

All 231 repeated ALSA errors were concentrated in one post-disconnect retry
burst. The current boot had no matching burst. The evidence does not justify
a global audio-format or device-power workaround.

The full audio follow-up found another brief dock error after removal and
separate Logitech USB headset errors. They must not be merged into hundreds
of independent dock failures. It also independently confirmed duplicate
internal HDMI/microphone nodes in the current graph; their cause and audible
impact remain unproven.

The apparent Docker daemon error count came from container-attributed logs.
Pacman/yay cleanup confirmation semantics were also checked in source:
`--noconfirm` is not unconditional yes. The updated reports reflect these
corrections rather than retaining a more alarming initial interpretation.

## Observed Hardware and Limits

The laptop is a ThinkPad X1 Carbon Gen 11 with an Intel i7-1370P, 14 cores,
20 logical CPUs, and approximately 62 GiB usable RAM. It runs stock Arch
7.2.2-arch1-1 and Plasma Wayland; Zen is also installed. The internal drive is
a Crucial T705 4 TB operating through the laptop's PCIe 4.0 x4 storage link.

Initial observations showed about 49 GiB available memory, unused encrypted
swap, and no sustained pressure. Short follow-up readings found no CPU
thermal-throttle counter increase. These are active-session samples, not a
sustained-build, battery-life, or whole-system latency benchmark.

Read-only sudo access closed the original SMART, LVM, crypto metadata, and
boot-artifact gaps. Public firmware and package catalogs were parsed in memory
without replacing local updater databases. Isolated completion/formatter
probes had no network or host credential access and no writable host mount;
their temporary fixtures were removed.

Actual alternate-kernel boots, cold hibernation restore, firmware application,
resizing, display changes, physical dock reproduction, and backup restore
remain unperformed because they change state or require a specific workload.
TRIM was performed only in its subsequently authorized maintenance task.
This is the completed read-only investigation, not a claim that every proposed
change has already been operationally validated.

## Source and Privacy Boundaries

Explicit credentials, keys, account/profile contents, shell history, private
shell overrides, full process environments, and application data were excluded.
Reports retain curated findings and nonsecret parameters rather than raw
journals, configs, storage headers, or machine-identifier dumps.

Direct ArchWiki retrieval was blocked by automated-traffic protection.
Accessible indexed excerpts were identified as such; technical conclusions
also use retrieved upstream kernel, cryptsetup, systemd, Lenovo/LVFS, Arch
package, and application sources. Sources are linked beside claims in each
investigation. No foreign-hardware benchmark was used to predict a percentage
speedup for this laptop.

## Validation

During the original audit, validation was limited to documentation and the
isolated probes described in the development report. No Ansible apply,
system configuration change, package synchronization, firmware update,
commit, or push was performed during that investigation. The later authorized
boot and power-profile changes and their validation are recorded separately
above.

Completed checks:

- Shared Markdown rules: passed, including an explicit invocation covering
  all 14 untracked audit documents.
- `go-task docs:instructions:check`: passed, 49 documents checked.
- `go-task docs:agents:check`: passed; the ownership map is unchanged.
- `go-task lint:english`: passed; an additional explicit English-letter
  check covered all 14 untracked reports and passed.
- `git diff --check`: passed; explicit trailing-whitespace and final-newline
  checks covered the untracked reports and passed.
- Local report-link checks: passed. No temporary fixtures or non-Markdown
  artifacts remain in the audit directory.

The standard `go-task lint:markdown` task also passed. Explicit untracked-file
checks matter because tracked-file checks alone do not cover new reports.
At the end of the original read-only audit, Git status contained only this
audit directory, with no tracked source or configuration changes. Later
authorized Ansible work remains separately uncommitted in the working tree.

The audio follow-up adds documentation only. Its validation covers all three
new reports and this index, including explicit untracked-file Markdown,
English, whitespace, final-newline, and local-link checks. Aggregate Markdown
and instruction checks are also rerun for this follow-up.
