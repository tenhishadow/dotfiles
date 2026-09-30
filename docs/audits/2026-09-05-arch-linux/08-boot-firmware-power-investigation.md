# Boot, Firmware, and Power Investigation

Subsequent status: BF-02 and BF-03 were addressed with explicit user approval;
see [applied boot maintenance](14-boot-maintenance.md). BF-06 was subsequently
implemented in [TuneD/Plasma integration](15-tuned-plasma-integration.md).
The investigation below preserves the observations made before these changes.

Read-only follow-up on 2026-09-05, covering boot recovery, firmware currency,
kernel differences, power policy, and video acceleration. Narrow privileged
reads became available for EFI files, initramfs metadata, and RAPL energy.
No firmware catalog was installed, no firmware payload was downloaded, and no
boot, kernel, service, power, or desktop setting was changed.

This report supersedes the access-related gaps in
[the first boot and power audit](02-boot-power-desktop.md).
Configuration blocks below are review artifacts only.

## Conclusions

| ID | Finding | Priority and confidence |
| --- | --- | --- |
| BF-01 | New BIOS, Intel ME, and dock firmware are offered for the actual devices and confirmed in the current public LVFS stable catalog | High maintenance priority; high confidence |
| BF-02 | `default arch-zen` does not match the actual `arch-zen.conf` entry; bootctl presently identifies stock Arch as default | Medium correctness priority; high confidence |
| BF-03 | Installed EFI bootloader is systemd-boot 259.1; system package is 261.2; automatic bootloader update unit is disabled | Medium maintenance priority; high confidence |
| BF-04 | Both real boot images contain the needed encrypted-LVM boot components and early Intel microcode | Existing configuration is coherent; high confidence |
| BF-05 | Stock and Zen share the major relevant capabilities; Zen's observed compiler optimization is O3 versus stock O2 | Keep stock baseline; no measured Zen performance advantage |
| BF-06 | TuneD's missing PPD bridge is a confirmed usability gap; a narrow performance profile can avoid server-oriented changes | Medium usability priority; configuration proposal only |
| BF-07 | Passive readings show functional frequency scaling and zero thermal-throttle events; VA-API capability query succeeds | No observed need for thermal or video-driver tuning |

## BF-01: Firmware Releases Are Available

The device-specific `fwupdmgr get-updates` and `get-releases` queries used
JSON and disabled metadata, remote, and unreported-history prompts. They
returned three applicable upgrades. A separate HTTPS GET of the public stable
catalog confirmed the versions; the approximately 2 MB compressed response
was decompressed and parsed in memory without updating fwupd's local state.
Its HTTP Last-Modified was **2026-09-04 05:52:21 UTC**.
[LVFS stable catalog](https://cdn.fwupd.org/downloads/firmware.xml.zst)

| Component | Installed | Latest matching stable release | Catalog release date | Reason to prioritize |
| --- | --- | --- | --- | --- |
| BIOS | 1.40, `N3XET65W` | 1.42, `N3XET67W`; LVFS 0.1.42 | 2026-07-16 | Security fixes; diagnostics update and ME capsule recovery enhancement |
| Embedded controller | 1.22 | BIOS 1.42 still includes ECP 1.22 | Same BIOS release | No separately demonstrated EC version deficit |
| Intel ME | 16.1.40.2765; LVFS 1.40.2765 | 16.1.42.2872; LVFS 1.42.2872 | 2026-08-11 | Security maintenance release |
| ThinkPad Thunderbolt 4 Dock | Aggregate 10.19 | Aggregate 10.20 | 2026-04-28 | Fixes monitor detection after restart and monitor wake after prolonged closed-lid console sleep |

All three upgrade entries carry vendor urgency `high`. Catalog release IDs
are 146439, 143804, and 140972 respectively. BIOS metadata lists
CVE-2026-46659, CVE-2026-46658, and LEN-216342; ME metadata lists
CVE-2026-20734, CVE-2026-20715, CVE-2026-20708, and INTEL-TA-01427.
These identifiers are vendor metadata, not an independent exploitability
assessment of this machine. None of these releases promises a CPU speedup.
[LVFS published release metadata](https://cdn.fwupd.org/downloads/firmware.xml.zst)

The dock's installed component versions include Thunderbolt 44.83.06,
audio 49-0E-41, DisplayPort 5 firmware 5.07.008, DisplayPort 6 firmware
6.05.007, and Power Delivery 12.5.57. The Thunderbolt sysfs value 44.83
and aggregate 10.19 describe different version fields. A duplicate fwupd
Thunderbolt representation reports an authorization limitation, while the
`usi_dock` aggregate is supported and offers 10.20. That duplicate status
does not establish that the connected dock is unusable.

**Verdict:** schedule BIOS and ME security maintenance and evaluate dock
10.20 as a relevant reliability update. It is not a demonstrated fix for the
observed USB audio stale-node behavior or the external NVMe disconnect.
Use device-matched vendor update instructions, stable AC, adequate battery,
saved work, and an uninterrupted update window. Firmware rollback may be
restricted; a backup cannot make an interrupted firmware flash harmless.
No update command was executed.

Current internal USB4 retimer version is 10.00; a newer applicable retimer
release was not established. Crucial T705 reports PACR5111, but fwupd has no
release list for this drive and the public catalog contains no matching
T705/model/firmware string. That absence cannot prove the SSD firmware is
current. Lenovo's general dock download search result lagged behind LVFS,
so the device-matched stable catalog is the stronger version comparison.
LVFS's individual HTML release pages returned HTTP 403; their contents were
not asserted to have been read.

## BF-02 and BF-03: Loader Selection and Update Ownership

The actual loader is **systemd-boot**, with the ESP mounted at `/boot`.
Both the normal EFI loader and the fallback `EFI/BOOT/BOOTX64.EFI` contain
version 259.1-1-arch. The installed systemd package is 261.2-1 and supplies
a newer loader binary. `systemd-boot-update.service` is disabled; no inspected
pacman hook invokes bootctl or that service. Package updates have therefore
not kept the ESP copy current.

The current loader configuration contains `default arch-zen`, `timeout 3`,
and `editor 0`. The real IDs are `arch.conf` and `arch-zen.conf`. The
systemd 259.1 documentation defines the default as a glob matching the entry
filename **including `.conf`**. Neither `LoaderEntryDefault` nor
`LoaderEntryOneShot` was present in EFI variables during inspection.
`bootctl list` identified `arch.conf` as both default and selected.
This establishes a present unmatched configuration; it does not prove whether
the user manually chose stock Arch at an earlier boot.
[systemd 259.1 loader configuration](https://github.com/systemd/systemd/blob/v259.1/man/loader.conf.xml)

Recommended eventual baseline for `/boot/loader/loader.conf`:

```ini
default arch.conf
timeout 3
editor 0
```

If the user explicitly chooses Zen after comparison, the matching default is
`arch-zen.conf`. No wildcard or remembered-entry policy is necessary for two
fixed entries. Retain the three-second menu so the alternate kernel remains
accessible. `editor 0` is a useful interaction restriction, not a substitute
for Secure Boot.

For bootloader maintenance, the installed standard unit already runs
`bootctl --variables=no --graceful update`. Managing that unit is the simplest
future ownership model; it updates the loader rather than rewriting the
kernel entries. A separately approved implementation should update the ESP
copy and enable its standard maintenance path, then verify both EFI copies.
This does not require replacing systemd-boot with GRUB or reinstalling Arch.

Two NVRAM Linux Boot Manager entries reference the same active ESP loader.
This duplication is low priority; it does not explain a slow userspace or
justify deleting firmware entries during this audit. No EFI variable was
modified.

## BF-04: Actual Initramfs Contents and Recovery Design

| Check | Stock image | Zen image |
| --- | --- | --- |
| Embedded kernel version | 7.2.2-arch1-1 | 7.2.2-zen1-1-zen |
| Builder | mkinitcpio 41.1 | mkinitcpio 41.1 |
| Compression | zstd | zstd |
| Early Intel microcode | Present | Present |
| cryptsetup, LVM binary, i915 module | Present | Present |
| Separate matching kernel and entry | Present | Present |

Only image metadata, names, and component-presence results were inspected;
the images were not extracted and no possible key content was read. The
stock image's early CPIO is approximately 16.5 MiB and compressed main image
approximately 17.7 MiB. `lsinitcpio` estimates decompression at about 0.06 s;
this is a tool estimate rather than a timed boot measurement. It gives no
reason to trade compatibility for a different compressor.

The separate `/boot/intel-ucode.img` exists. Loading only the main initramfs
is coherent because early Intel microcode is already embedded. Both boot
entries use the same encrypted container, root LV, and resume LV, with each
entry pointing to its matching kernel and initramfs. This closes the first
pass's inability to inspect `/boot`.

The current kernel's early AMD KVM probe warning cannot be attributed to a
misplaced AMD KVM module in these images: neither image's file listing
contains a KVM AMD or Intel module. The working host loads `kvm_intel`.
No functional correction follows from that warning alone.

**Recommended recovery design:** keep these two separate kernel/image/entry
pairs; keep their common encryption/LVM configuration coherent; maintain the
ESP loader; and retain an external Arch recovery medium plus package rollback
material. The two installed kernels are not independent protection against a
shared bad mkinitcpio configuration: regenerating both from a blindly replaced
`.pacnew` can break both. LTS is an optional third kernel for a diagnosed
regression, not a requirement to fix the present boot chain.

Neither current preset builds a broad hardware fallback image. That is not
the same as having no alternate kernel. The static image checks pass, but
actually booting Zen, testing cold hibernation restore, and proving a rescue
medium require reboot or sleep transitions. Those operational guarantees
cannot be established through read-only inspection.

### Secure Boot and Hibernation

EFI reports Secure Boot disabled in Setup Mode, TPM2 available, and no
measured UKI. Kernel lockdown is currently `none`; the running kernel includes
lockdown support but has `CONFIG_LOCK_DOWN_KERNEL_FORCE_NONE=y`.

Signed Unified Kernel Images are a coherent future way to cover kernel,
initramfs, and command line as one boot artifact. They are not a prerequisite
for correcting the present loader or obtaining good performance. Such a
migration needs signing/update ownership, tested recovery, and a deliberate
policy for loaded out-of-tree VirtualBox modules.

Do not promise that a signed UKI plus the existing LUKS swap automatically
preserves hibernation under kernel lockdown. Upstream hibernation availability
explicitly checks `LOCKDOWN_HIBERNATION`; encrypting a block device is not an
exception to that check. Secure Boot signature validation and kernel lockdown
are related but distinct controls, and actual enablement must be verified.
If integrity lockdown is chosen, ordinary hibernation must be treated as
unavailable unless the exact kernel supplies and validates a supported resume
authentication mechanism. Do not weaken lockdown silently to make a sleep
test pass. [Kernel hibernation implementation](https://github.com/torvalds/linux/blob/master/kernel/power/hibernate.c)

**Verdict:** preserve the present hibernation workflow for this tuning pass;
make verified boot a separate explicit security change. That is a compatibility
decision, not a claim that the current unverified boot chain is secure against
physical modification.

## BF-05: Stock and Zen Are Closer Than Their Names Suggest

The installed headers include both build configurations; this comparison
uses those actual package artifacts rather than a distribution marketing list.

| Build capability | Stock | Zen |
| --- | --- | --- |
| Compiler | GCC 16.2.1 | GCC 16.2.1 |
| Optimization selection | Performance, O2 | Performance, O3 |
| Dynamic preemption and preemptible kernel | Enabled | Enabled |
| Timer frequency | 1000 Hz | 1000 Hz |
| Intel P-state, MGLRU enabled by default | Enabled | Enabled |
| BFQ and mq-deadline availability | Enabled | Enabled |
| sched_ext support | Enabled | Enabled |
| Alternative scheduler configuration | No enabled alternative observed | `CONFIG_SCHED_ALT` disabled |
| LTO | Disabled | Disabled |
| Native CPU target | Disabled | Disabled |
| Hibernation compression default | LZO | LZO |

This is not a complete patch comparison: equal configuration symbols do not
make the kernels identical, and Zen can change defaults in source. It does
rule out claims that this installation needs Zen merely to obtain preemption,
1000 Hz timers, modern reclaim, or BFQ. O3 is not a prediction of a particular
workload speedup. Recompilation or another kernel is unwarranted without a
defined workload bottleneck. A real comparison requires separate boots under
the same workload and power/display conditions; no read-only command can run
both installed kernels simultaneously as the host kernel.

## BF-06: Minimal Plasma Power-Profile Proposal

The standard `tuned-ppd` package is the missing compatibility component.
Its upstream mapping uses `balanced` on AC, `balanced-battery` for the
balanced mode on battery, `powersave` for power saver, and
`throughput-performance` for performance. The latter is a broad server
profile, not simply an EPP change. Existing local settings confirm it also
sets CPU minimum performance to 100%, changes read-ahead and memory writeback.
[Upstream PPD mapping](https://github.com/redhat-performance/tuned/blob/master/tuned/ppd/ppd.conf)

For this Intel laptop, retain the shipped balanced and power-saver behavior
and make performance a small child of balanced. Proposed
`/etc/tuned/profiles/workstation-performance/tuned.conf`:

```ini
[main]
summary=Prefer interactive performance on this Intel workstation
include=balanced

[cpu]
governor=powersave
energy_performance_preference=performance

[acpi]
platform_profile=performance
```

This retains the active Intel P-state scaling driver, the inherited enabled
boost, and the existing minimum-performance policy. It changes the energy
preference and firmware platform profile without importing server writeback,
read-ahead, or minimum-frequency settings. Active Intel P-state `powersave`
permits workload-dependent hardware scaling and does not fix frequency at its
minimum. The proposal is specific to this observed Intel driver.
[Intel P-state semantics](https://docs.kernel.org/admin-guide/pm/intel_pstate.html)

Proposed `/etc/tuned/ppd.conf`:

```ini
[main]
default=balanced
battery_detection=true
sysfs_acpi_monitor=true

[profiles]
power-saver=powersave
balanced=balanced
performance=workstation-performance

[battery]
balanced=balanced-battery
```

Future implementation scope is one package, the two root-owned configuration
files, and the existing TuneD plus PPD units, owned by `roles/system` through
the explicit privileged playbook with its existing CI/container guards.
The default user-level, sudo-free dotfiles workflow remains unchanged.
Do not install and enable
`power-profiles-daemon`, TLP, or auto-cpufreq alongside this owner. Performance
remains explicitly selectable on battery; this proposal does not silently
rename a battery-saving mode as performance. Firmware profile hotkey monitoring
uses the upstream mapping option; its behavior must be checked on this model.

Validation after an approved change should observe D-Bus profile availability,
Plasma's mode selection, all CPU EPP policies, platform profile, AC/battery
mapping, and unchanged storage/memory controls. The performance proposal is
not applied or benchmarked. Rollback is the prior mapping/profile state and
disabling the newly added bridge, not disabling the existing TuneD daemon.

## BF-07: Passive Thermals and Video Capability

A ten-second, six-point passive sample was taken on AC during the existing
desktop session, with no synthetic load:

| Reading | Result |
| --- | --- |
| CPU package energy-derived power | 7.68–16.45 W; mean 9.45 W |
| CPU package temperature | 59–62 C |
| Mean of sampled per-policy frequencies | 0.63–2.02 GHz |
| Sum of all core/package thermal-throttle counters | 0 before, 0 after |
| Package RAPL long/short limits | 64 W / 64 W |
| Platform/lap mode | Balanced; lap mode inactive |

These are CPU package readings, not wall power, total laptop power, an idle
baseline, effective instruction throughput, or proof of sustained 64 W
cooling. Firmware and electrical limits can constrain performance without
incrementing thermal-throttle counters. The observed variation does establish
that CPUs are not stuck at a fixed low frequency in this sample.

The firmware exposes INT340x thermal participants. `thermald` is absent;
kernel and firmware thermal control are present. Some sysfs trip entries
contain an invalid sentinel near -274 C, so treating every exposed trip as a
physical safe operating target would be wrong. There is no observed thermal
failure requiring custom fan curves, raised RAPL limits, MSR writes, or
forced thermald configuration. Intel's thermal daemon supports platform
thermal policies, but its existence alone does not establish a benefit here.
[Intel thermal daemon](https://github.com/intel/thermal_daemon)

`vainfo --display drm --device /dev/dri/renderD128` succeeds using Intel iHD
26.2.4 and lists hardware video decode entry points, including H.264 and HEVC.
The Intel media driver file exists, and the managed Chromium policy explicitly
enables hardware acceleration. Therefore the driver capability layer is
operational and no missing-VA-API-package repair is indicated.
[Intel media driver](https://github.com/intel/media-driver)

A capability listing is not proof that a particular browser video uses that
decoder: codecs, browser sandboxing, and browser selection still matter.
No browser profiles, page content, playback history, or session state were
read, and no browser was launched. The remaining per-video question would
require an intentionally chosen playback observation; it is not evidence of
an existing acceleration defect.

## Read-Only Work Completed and Remaining Boundaries

Firmware comparison, loader identification and selection analysis, actual
boot-image component checks, kernel configuration comparison, policy design,
passive thermal measurement, and VA-API capability enumeration are complete.
The remaining uncertainty is operational: update success, alternate-kernel
behavior, battery discharge, and suspend/resume recovery require the very
changes or transitions excluded from this task. No additional agent can prove
those outcomes by reading more configuration files.
