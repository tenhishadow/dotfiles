# Completed Read-only Audit: Decisions and Implementation Order

Completed investigation on 2026-09-05. This is the current decision document
for the whole laptop: operating system, boot, firmware, desktop, network,
services, development tools, containers, and storage. No proposals were applied
during the investigation. The subsequently authorized changes are recorded in
[applied boot maintenance](14-boot-maintenance.md) and
[TuneD/Plasma integration](15-tuned-plasma-integration.md), followed by
[periodic TRIM](16-trim-and-boot-review.md); other proposals remain unapplied.

## Overall Assessment

The machine is already using many of the mechanisms an optimized modern Arch
desktop should have: hardware-rendered Plasma Wayland, Intel P-state and
turbo, modern memory reclaim, native container storage/cgroups, coherent
encrypted-LVM boot images, and deterministic editor configuration. Current
measurements show substantial spare memory and no sustained system-wide
resource pressure. There is no basis for a percentage score such as
"90% optimized" or for claiming another distribution will make everything
faster.

The work did find real corrections and measurable opportunities. The best
first changes are ordinary configuration and maintenance improvements, not
global compilation flags or a new filesystem. The audit is now complete for
what can be established through safe reads and isolated nonpersistent probes;
the explicitly listed reboot, physical, workload, and recovery tests remain
unperformed.

## Coverage and Closed Questions

| Area | Result | Detailed evidence |
| --- | --- | --- |
| Boot selection | Present default pattern omits `.conf` and matches neither kernel entry | [Boot investigation](08-boot-firmware-power-investigation.md) |
| Boot artifacts | Both real initramfs images contain matching kernels, microcode, cryptsetup/LVM and graphics support; ESP loader is older than installed systemd | [Boot investigation](08-boot-firmware-power-investigation.md) |
| Firmware | Device-matched BIOS, ME, and dock updates verified in current public LVFS metadata | [Firmware comparison](08-boot-firmware-power-investigation.md) |
| Kernel choice | Actual stock/Zen configurations compared; stock already has relevant modern capabilities | [Kernel comparison](08-boot-firmware-power-investigation.md) |
| Power and thermals | Functional scaling, short passive power sample, no sampled throttle events; Plasma profile bridge missing | [Power investigation](08-boot-firmware-power-investigation.md) |
| Desktop and rendering | Hardware rendering works; indexing, compositing, portals, animation policy, app memory, and display tradeoffs inspected | [Desktop investigation](12-desktop-investigation.md) |
| Network, DNS, services | Link state/counters, routing priorities, resolver ownership, firewall scope, service cost and OOM policy inspected | [Network and services](11-network-services-investigation.md) |
| Shell | Isolated measurement found about 150 ms removable completion work; go-task registration defect reproduced | [Development investigation](07-development-investigation.md) |
| Editor and Git | Formatter sequencing tested; plugin-writer ownership and ignored Git settings identified | [Development investigation](07-development-investigation.md) |
| Packages | Fresh public-version comparison, package database/presence checks, orphan classification, live deleted-library check | [Maintenance investigation](13-maintenance-investigation.md) |
| Containers | Native storage confirmed; aggregate space, resource boundaries and logging interpretation checked | [Storage accounting](09-storage-investigation.md), [network/services](11-network-services-investigation.md) |
| Internal storage | SMART, KDF/cipher geometry, exact VG free space, reserves, APST and root consumers established | [Storage investigation](09-storage-investigation.md) |
| Dock/sleep/audio | Historical disconnect timeline and stale-audio retry burst narrowed; original generalizations corrected | [Dock investigation](06-dock-sleep-investigation.md) |
| Other distributions | CachyOS features evaluated individually; migration not justified | [Tuning options](04-tuning-options.md) |

## Corrections Ready for a Separate Implementation Pass

These are concrete reviewable proposals, not approvals to change the system.
Each linked investigation contains the exact proposed configuration or
validation method.

| Order | Change | Expected benefit | Relevant limit or risk |
| --- | --- | --- | --- |
| 1 | Make systemd-boot default match `arch.conf` for the existing stock baseline, or `arch-zen.conf` if deliberately choosing Zen | Predictable kernel selection | A boot-selection fix does not prove a performance benefit from Zen |
| 2 | Restore the missing pacman cache directory and use the tested upgrade function preserving failure status | Correct packaged state and understandable maintenance behavior | Cache retention and AUR review remain separate policies |
| 3 | Replace eager shell completions with the tested deferred mechanism; register go-task under its real binary name | About 150 ms lower median for the tested four-generator fragment; correct completion behavior | Full terminal latency and non-Arch portability still need implementation-stage verification |
| 4 | Select Ruff once for this repository's Python formatting contract | Remove a redundant formatter stage | Other projects can require Black; preserve explicit project policy |
| 5 | Maintain the ESP loader alongside systemd packages | Avoid an indefinitely stale bootloader copy | Boot artifact and recovery checks must accompany a later update |
| 6 | Add the missing TuneD PPD bridge with a deliberately scoped laptop performance mapping | Working desktop profile selection without unwanted server-profile changes | Power/thermal behavior after applying must be measured |
| 7 | Apply normal reviewed package and BIOS/ME/dock maintenance in a controlled sequence | Current fixes and security maintenance | No claim that an update resolves a particular historical error without reproduction |
| 8 | Give root planned headroom, restore the normal ext4 commit interval, and establish periodic TRIM | Capacity and durability/maintenance improvements | Resize/TRIM/remount are real state changes; recovery and verification are required |

Remove the two unsupported Git-core tuning keys as a small clarity cleanup
when touching that configuration. It is not a speed optimization by itself.
Review orphan runtimes/debug packages for approximately 2.94 GiB of potential
space, but do not infer that every orphan is unwanted.

## Policy Choices to Make Deliberately

| Choice | Recommendation from this audit |
| --- | --- |
| Desktop smoothness | Compare the advertised lower-resolution high-refresh display mode if motion is more important than native 4K text detail; do not promise both on the current link |
| Fractional scaling and fonts | Inspect visible text first; hardware rendering and native Wayland paths already work, so do not apply global rendering overrides blindly |
| Ethernet throughput | Check the peer port/link before treating 1 Gb/s negotiation on a 2.5 Gb/s-capable adapter as an OS fault |
| DNS caching | Current NetworkManager-to-LAN-resolver path is coherent; add a local resolver only for a demonstrated latency or split-DNS requirement |
| IPv6 | Global and loopback disabling is a deliberate feature limitation; review it before IPv6/dual-stack development, not as a generic speed tweak |
| Host ingress | Docker forwarding policy is not a host input firewall; make KDE Connect/LAN exposure an explicit workstation policy |
| Container limits | Apply workload-specific memory/PID/CPU budgets where needed; current absence of limits is a containment choice, not proof of current pressure |
| Logging | Keep enough journal history to diagnose intermittent problems; avoid another redundant monitoring stack |
| Plugin experimentation | The daily Neovim restore job intentionally enforces the lock; change that policy only if manual plugin checkouts should persist |
| Secure Boot | Treat signing, lockdown, out-of-tree modules, recovery, and hibernation compatibility as a separate design |

## What to Keep

- Keep Arch and the working Plasma Wayland desktop.
- Keep stock as the measured baseline and retain the installed Zen alternative.
- Keep Intel P-state, turbo, ordinary hardware scheduling, and current modern
  memory-reclaim support.
- Keep the working graphics/media-driver stack; installed support and a
  successful VA-API query do not imply every video stream uses it.
- Keep the currently coherent portal fallback and disabled redundant compositor
  and indexer behavior. Do not disable functional services merely to reduce
  the process count.
- Keep native Docker storage and systemd cgroup integration.
- Keep the aligned LUKS2/LVM/ext4 layout, encrypted swap, and present Argon2id
  geometry. There is no reason for reencryption or filesystem migration.
- Keep all privileged behavior behind the repository's explicit system layer;
  the ordinary user-dotfiles workflow remains sudo-free.

## Findings Narrowed by Further Evidence

The follow-up materially changed several first-pass impressions:

1. Internal SSD health is now available: 1% endurance used, zero media errors,
   zero error-log entries, and no critical warning. The historical I/O errors
   belonged to an external enclosure.
2. External read errors preceded actual kernel hibernation entry by about
   3.55 seconds. Cross-source receipt timestamps do not justify claiming an
   exact causal ordering against the desktop's sleep request. Initial
   disconnection cannot be blamed on a kernel sleep transition that had not
   started.
3. The 231 ALSA failures were one retry burst after a dock disappearance,
   not evidence of continually incorrect audio format or hundreds of crashes.
4. The apparent Docker daemon error count was container-attributed journal
   output. It did not establish an unhealthy Docker engine.
5. `--noconfirm` does not mean unconditional yes to all cleanup questions;
   source review corrected that assumption. Failure-status masking and
   inconsistent cache policies are the actual shell concerns.
6. Exact LVM metadata confirms approximately 2.935 TiB free; this is no longer
   merely an inference from active device sizes.
7. Stock and Zen boot images are present and coherent. Actual alternate-kernel
   boot and cold restore are still operational tests, not metadata facts.

These corrections are why symptom counts and isolated tuning suggestions
should not be treated as a root-cause diagnosis.

## What Cannot Be Finished Without Changing State or Workload

| Remaining proof | Why read-only inspection cannot provide it |
| --- | --- |
| Stock versus Zen under an actual build | Requires booting the other host kernel and repeating the workload |
| Safe cold hibernation restore | Requires an intentional sleep/power/recovery transition with saved work |
| Dock disconnect cause | Requires observing or reproducing physical cable, power, dock, and enclosure behavior |
| New display mode, text quality and battery effect | Requires changing a mode or profile and observing the actual display/workload |
| Firmware update result | Requires flashing, rebooting, and checking the device afterward |
| Restorable independent backup | Requires an identified backup source and a restore into an approved destination |
| Successful TRIM, root growth, and new mount interval | Requires actual maintenance operations and post-change checks |
| Full application latency and remote service performance | Requires a representative user workload; synthetic completion timing covers only a narrow fragment |
| Exhaustive security assurance | Requires a separately defined threat model, package/source coverage and assessment; routine diagnostics cannot certify absence of vulnerabilities |

These are completion boundaries of the requested read-only mode, not missing
permission requests that need to interrupt this report. No physical fault,
speedup, restore success, or update success was invented to make the table
look complete.

## Validation and Review

Specialist reports were cross-reviewed for device attribution, timing
semantics, kernel/crypto assumptions, confirmation behavior, and proposed
rollback safety. Read-only diagnostic commands and isolated shell/formatter
checks are distinguished from future host actions in their reports.

The repository contains report changes only. Markdown, instruction links,
the ownership map, English text, and whitespace are checked before delivery;
the [audit index](README.md) records their final results. No Ansible apply,
package sync, configuration change, commit, or push was performed.
