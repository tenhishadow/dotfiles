# Boot, Power, and Desktop Audit

This is a first-pass snapshot. The [current audit index](README.md) and
[completed read-only decisions](10-read-only-conclusions.md) include later
measurements, resolved access gaps, and corrected interpretations.

Read-only observations collected on 2026-09-05. No kernel, boot image,
firmware, service, power setting, display mode, or package was changed.
Findings use observed runtime state; package presence alone does not establish
that a feature works. Severity describes operational importance, independently
of confidence in the observation.

## Assessment

The basic CPU and graphics configuration is sound. The largest actionable
findings are an incomplete Plasma power-profile integration, recurring dock
audio errors, one hybrid-sleep fallback, and opportunities to improve display
smoothness. Nothing measured establishes a CPU performance emergency or a
need to replace Arch, rebuild the kernel, or change CPU scaling drivers.

| Area | Observed state | Assessment |
| --- | --- | --- |
| Hardware | ThinkPad X1 Carbon Gen 11; Intel Core i7-1370P; 20 logical CPUs | Suitable modern upstream driver support |
| Kernel | Running `linux 7.2.2.arch1-1`; matching `linux-zen` and both header packages installed | Stock is active; Zen is an available experiment |
| CPU | `intel_pstate` active; `powersave`; `balance_performance` EPP on all 20 policies; turbo allowed | No accidental fixed low-frequency governor |
| Power owner | TuneD `balanced`; AC connected; platform profile `balanced` | One detected CPU/profile controller |
| Graphics | Plasma Wayland; i915; Mesa; Intel Vulkan and media drivers installed | GuC submission and power control active; HuC authenticated |
| Sleep | Only `[s2idle]` advertised; hybrid sleep used | Disk image creation observed; cold restore unverified |
| Firmware | Lenovo BIOS `N3XET65W (1.40)`, dated 2026-01-27 | Current release availability not established |
| Battery | 45.86 Wh reported full versus 57 Wh design; 471 cycles | About 80.5% reported capacity; not proof of a defective battery |

## Prioritized Findings

### BP-01: Plasma Cannot Reach a Power-Profile Backend

**Priority: medium. Confidence: high for the integration gap.**

`tuned.service` is enabled and active, but `tuned-ppd.service` and
`power-profiles-daemon.service` are not installed. System D-Bus has TuneD and
UPower, but no power-profiles service. Plasma PowerDevil is active. This
leaves the conventional Plasma performance/balanced/power-saver interface
without its backend; it does not mean TuneD itself is broken.

Recommendation for a later approved change: complete the existing TuneD
integration with its `tuned-ppd` compatibility service, then verify the three
desktop modes and AC/battery transitions. This package is available separately
in Arch and exists specifically for applications using the PPD interface.
[Arch tuned-ppd package](https://archlinux.org/packages/extra/any/tuned-ppd/)

Do not enable a second independent CPU tuning controller. Inspect profile
mapping before using performance mode: the installed `throughput-performance`
profile also sets minimum CPU performance to 100%, changes disk read-ahead,
and changes memory writeback behavior. Its effects extend beyond a CPU speed
slider. The installed `balanced-battery` profile provides a more restrained
EPP change to `balance_power` while retaining boost.

### BP-02: One Hybrid-Sleep Attempt Lost Its Hibernation Fallback

**Priority: medium, higher if unattended sleep must survive battery loss.
Confidence: high for the failure; low for its cause.**

On 2026-09-03 at 09:56:14 UTC, systemd logged `Device or resource busy`
during hybrid sleep, then explicitly fell back to ordinary suspend. The
service subsequently completed successfully, so a present-day failed-unit
check cannot reveal this event. Two later retained hybrid-sleep attempts
completed without that error.

The same short interval contains read and buffer I/O errors for `nvme1n1`
and a PCIe ASPM reconfiguration message. The storage investigation mapped
that device to an external OWC Express 1M2 enclosure, with Thunderbolt
disconnect/link-down at 09:56:11 UTC and reconnection at 09:56:13 UTC.
This is evidence of an external disconnect event, not an internal Crucial
SSD error. Its relationship to the sleep rejection remains a correlation;
see ST-01 in the [storage report](01-storage.md).

The current boot records creation of a roughly 8.47 GB logical hibernation
image, compressed to roughly 2.98 GB, with a reported write phase of 5.55 s.
The selected `/sys/power/disk` mode is `suspend`. Hybrid sleep writes an image
and suspends; normal wake can discard that image. These logs establish image
creation and a resumed session, not successful recovery from disk after power
loss. [Kernel sleep-state documentation](https://docs.kernel.org/admin-guide/pm/sleep-states.html)

Next task: correlate dock/storage events around that timestamp; later perform
an explicitly approved docked/undocked sleep and cold-restore test with saved
work. No sleep transition or stress test was run for this audit.

Only `s2idle` is exposed in `mem_sleep`; adding `mem_sleep_default=deep`
cannot manufacture absent platform support. Current suspend counters do not
establish actual low-power residency or overnight discharge. Measure those
before considering wake-source or device power overrides.

### BP-03: Dock Audio Has Repeated Real Start Errors

**Priority: medium for desktop reliability. Confidence: high for the errors;
cause unconfirmed.**

Within the retained seven-day service journal, PipeWire has 231 identical
ALSA `front:1` playback-open failures with `Invalid argument`, plus 25
start-error transitions associated with ThinkPad Thunderbolt 4 Dock USB
audio. Other messages concern disappearing USB/headset devices and Bluetooth
transport errors. Some missing-device messages can accompany normal unplugging;
the repeated invalid-argument errors deserve a targeted audio investigation.

Do not interpret the raw error count as hundreds of application crashes or
evidence that Arch is globally slow. A useful next task is to reproduce
dock reconnect, resume, and output switching while inspecting the chosen
ALSA/UCM profile. WirePlumber exposes per-device ALSA rules, ACP, and UCM
selection; a workaround should match the affected device only after diagnosis.
[WirePlumber ALSA configuration](https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/alsa.html)

PowerDevil's error-level messages are mostly monitor DDC capability probing
and diagnostic timing lines. They are not evidence of repeated PowerDevil
crashes. There is also one i915 selective-fetch warning in the current boot;
the inspected messages do not show a GPU hang or reset loop. Avoid disabling
panel power features or changing GPU drivers solely to silence these logs.

### BP-04: Display Refresh Is a Concrete Smoothness Opportunity

**Priority: optional. Confidence: high for advertised modes, untested for
subjective benefit and link stability.**

The active external monitor runs at 3840x2160 and 60 Hz, with scale 1.7.
It also advertises 2560x1440 at approximately 144 and 160 Hz. Comparing these
modes may change perceived scrolling and pointer smoothness more than kernel
micro-tuning, at the cost of lower resolution and potentially reduced text
sharpness. The current link does not advertise 4K at a higher refresh rate.
Do not assume that a different cable alone would unlock it.

The internal panel is currently disabled. It advertises native 1920x1200,
but its remembered selected mode is 1920x1080. Check the active mode when
undocked: native 1920x1200 would retain vertical workspace and avoid scaling
a non-native aspect ratio. A disabled output is not evidence that current
visible laptop rendering is incorrect. No display changes were made.

### BP-05: Boot Has a Small Measurable Service Delay

**Priority: low. Confidence: high for the observed dependency chain.**

| Boot phase | Reported duration |
| --- | --- |
| Firmware | 11.902 s |
| Loader | 3.112 s |
| Kernel and unseparated early boot | 19.140 s |
| System userspace | 7.560 s |
| Total | 41.716 s |

The userspace critical chain includes NetworkManager wait-online, 3.943 s,
followed by Docker, 0.987 s. Docker explicitly wants and orders itself after
`network-online.target`. This provides a bounded optimization candidate if
Docker need not start immediately. It does not justify indiscriminately
disabling network-online, which can affect services with real network startup
requirements. [NetworkManager wait-online documentation](https://networkmanager.dev/docs/api/latest/NetworkManager-wait-online.service.html)

The roughly 19 s early-boot figure does not separate BusyBox initramfs,
device discovery, and interactive LUKS unlocking. It is not a measurement of
kernel inefficiency. Graphical-target readiness is also not a measurement of
the first usable desktop frame. Unit timings overlap; `blame` values must not
be added into a proposed saving. [systemd-analyze manual](https://man.archlinux.org/man/systemd-analyze.1)

### BP-06: Boot Maintenance Needs Careful Review, Not a Hook Rewrite

**Priority: medium for maintenance safety. Confidence: high for configuration;
built-image verification unavailable.**

The active mkinitcpio configuration has a coherent BusyBox sequence:
`udev`, `microcode`, `kms`, keyboard/keymap support, `block`, `encrypt`,
`lvm2`, `filesystems`, `resume`, and `fsck`. The kernel command line names
the encrypted container, root LV, and resume LV. Actual microcode revision
is `0x00006134`. Compression has no explicit override; there is no evidence
that changing compression or moving to systemd initramfs would improve
interactive performance.

There is a pending `/etc/mkinitcpio.conf.pacnew`. Its default switches to
`systemd`/`sd-vconsole` and contains neither the site's encryption nor LVM
hooks. Replacing the current file with it and rebuilding would drop essential
root-discovery configuration. Preserve the existing working chain unless a
deliberate migration also adapts encrypted-root parameters and recovery.
ArchWiki's indexed guidance explicitly supports both BusyBox and systemd
LVM-on-LUKS recipes. [ArchWiki encrypted-system configuration](https://wiki.archlinux.org/title/Dm-crypt/Encrypting_an_entire_system)

Both installed kernel presets specify only `default`, with no fallback preset;
LTS is not installed. An independently bootable alternate kernel and recovery
medium are more useful resilience improvements than adding unexplained hooks.
The protected `/boot` directory prevented validation of actual boot entries,
generated images, and whether the Zen entry is usable. A package check calling
`/boot/intel-ucode.img` missing actually reported permission denied; it is not
evidence of a missing microcode image.

### BP-07: Battery and Boot Trust Are Separate From Speed

**Priority: optional for battery policy; medium for boot integrity.
Confidence: high for observed state.**

The battery's reported full capacity is approximately 80.5% of design after
471 cycles. Charge thresholds are 0/100 and the sample was taken on AC at
96% charge. If the laptop spends most of its time docked, evaluate a lower
charge ceiling against the user's required unplugged runtime. That may help
the battery use pattern; it cannot recover already lost capacity or increase
CPU throughput. No battery-life baseline was measured.

EFI reports Secure Boot disabled and Setup Mode enabled. Encryption alone
does not provide a verified boot chain. Treat signing, key enrollment,
recovery, and hibernation compatibility as a separate security design task;
do not enable Secure Boot as an incidental tuning change. BIOS release and
firmware update availability were not refreshed or established in this pass.

## Configuration Ownership and Kernel Choice

The repository installs `tuned` in
`roles/system/vars/archlinux-packages.yml`, but does not declare its active
profile or the missing PPD bridge. Its laptop task currently manages the
camera blacklist; it is not a comprehensive ThinkPad power profile. Boot,
firmware, battery thresholds, display modes, and audio behavior remain largely
outside that declared management surface.

The live TuneD balanced profile explains the observed governor, EPP, boost,
and platform profile exactly. Its global configuration has
`dynamic_tuning=0` and `reapply_sysctl=1`. No observed mismatch demonstrates
continuous competing writes. Future manual sysfs adjustments may be restored
on profile reapplication; put approved policy in one deliberate owner.
[TuneD project documentation](https://tuned-project.org/)

`intel_pstate`'s active-mode `powersave` is not the generic governor that fixes
frequency at its minimum. It lets supported hardware choose operating states
using workload and energy/performance hints. Turbo is allowed here. Raising
all minima or disabling power states is not a free laptop performance gain;
thermal and power limits still apply.
[Kernel intel_pstate documentation](https://docs.kernel.org/admin-guide/pm/intel_pstate.html)

The running stock kernel already has preemption support, dynamic preemption,
and `CONFIG_HZ=1000`. Zen's presence alone does not establish an advantage.
Compare stock and the installed Zen using the same real build, desktop
interaction under load, suspend/dock tests, and power profile. Keep stock
available. No trustworthy percentage improvement can be assigned without
measurements. [Zen upstream feature description](https://github.com/zen-kernel/zen-kernel/wiki/Detailed-Feature-List)

An early `kvm_amd` probe warns that this is not an AMD CPU, but `kvm_intel`
is loaded and module loading completes successfully. No matching AMD directive
was found in inspected module-load/modprobe configuration. Treat this as low
priority probe noise unless VM behavior fails. VirtualBox modules also load
and taint the kernel as out-of-tree code; that alone does not mean corruption.

## Evidence Limits

This was an AC-powered, docked snapshot during an active session, not an idle
power or sustained compilation benchmark. CPU package temperature was around
62 C; that reading alone neither proves overheating nor good sustained thermal
headroom. No package C-state residency, fan curve, sustained power limit, or
thermal-throttling benchmark was collected.

Direct ArchWiki pages were blocked by Anubis. ArchWiki comparison above uses
explicitly identified search-index excerpts, not an asserted full-page read.
The linked upstream kernel, TuneD, NetworkManager, WirePlumber, Zen, Arch
package, and systemd manual pages were opened. In addition to the cited
encrypted-system recipe, indexed references checked were
[CPU frequency scaling](https://wiki.archlinux.org/title/CPU_frequency_scaling),
[mkinitcpio](https://wiki.archlinux.org/title/Mkinitcpio), and
[ThinkPad X1 Carbon Gen 11](https://wiki.archlinux.org/title/Lenovo_ThinkPad_X1_Carbon_%28Gen_11%29).

Sensitive account/configuration state was excluded. Reports retain selected
technical findings rather than raw journals, device identifiers, or copied
runtime configuration. Privileged boot-image inspection, firmware queries
requiring elevated access, and changes remain for a separately authorized task.
