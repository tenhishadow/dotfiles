# Periodic TRIM and Boot Configuration Review

On 2026-09-05 the user authorized enabling periodic TRIM through this
repository's Ansible role. Root resizing, mount-option changes, kernel
parameter changes, and initramfs changes were reviewed only. No commit or
push was requested or performed.

## Periodic TRIM

`system_fstrim_enabled` defaults to false and is enabled for this host.
The tagged `Fstrim | Enable periodic TRIM` task enables and starts the
packaged `fstrim.timer`, guarded by the existing systemd/CI/container boundary.
Only the `fstrim` tag was applied to the live workstation. One timer changed;
a second apply reported zero changes and zero failures.

The packaged weekly schedule, persistent missed-run handling, one-hour
accuracy window, and randomized delay remain intact. The timer reported its
next run as 2026-09-07 00:58:21 CEST immediately after enablement; this is a
scheduled time rather than a guaranteed exact start time.

The existing NVMe, partition, LUKS mapping, and LVM volumes all expose discard
support. `allow-discards` is already present in the encrypted-root boot
argument. A dry run selected `/boot`, `/home`, and `/` from the existing
filesystem table. No encryption or mount change was needed.

An initial real run was then started through Ansible's
`ansible.builtin.systemd_service` module against the packaged `fstrim.service`.
It completed successfully with exit status 0 in approximately 2 minutes
49 seconds. Its journal explicitly reported:

| Filesystem | Reported discard range |
| --- | --- |
| `/boot` | 903.8 MiB |
| `/home` | 335.6 GiB |
| `/` | 15.4 GiB |

These are already-free filesystem ranges passed to discard, not newly freed
filesystem capacity or a measurement of physical NAND reclaimed. Root usage
does not decrease merely because TRIM ran. No NVMe/ext4 error was logged
during the operation. Future ordinary applies maintain the timer and do not
force another one-time service run.

The prior timer/service state and checksums of unchanged boot/mount files
were saved outside the repository in the root-owned `0700` directory
`/root/fstrim-enable-backup-20260905T111432Z-IVTXqI`.

Rollback stops future scheduling: stop and disable `fstrim.timer`, then set
`system_fstrim_enabled: false` to prevent a later apply from enabling it again.
The flag skips management; it does not undo an earlier apply. Already
discarded free-space contents cannot be restored by disabling the timer.

## Validation and Scope

Passed: `go-task lint`, `go-task yamllint`, scoped `go-task system:check`,
actual scoped apply and zero-change second apply, Markdown validation,
Ansible naming/handler checks, the unchanged agent ownership map, and
`git diff --check`. Explicit Markdown checks include the untracked reports.
Real service completion and per-filesystem journal entries verify the actual
discard path beyond the dry run and timer enablement.

The unchanged broader validation blockers from
[the preceding integration](15-tuned-plasma-integration.md#repository-validation)
remain: the Renovate check requires Node.js 24 while the active runtime is 22,
and the full fresh-container package check cannot resolve `talhelper`.
This narrow timer change does not claim a successful full-repository
validation or container-service test.

Checksums confirm `/etc/fstab`, `/etc/mkinitcpio.conf`, and both existing
kernel-entry files were unchanged by this work. No resize, remount,
initramfs rebuild, or unrelated live system apply was performed.

## ext4 Commit Interval

Both `/` and `/home` currently use `commit=120` in their effective mounts and
fstab entries. Recommend changing both to `commit=5` in a separately approved
change, preserving the remaining options and source identifiers.

This option limits the age of the running journal transaction. The upstream
default is five seconds. A long interval can reduce commit overhead but
increases the exposure of unsynchronized recent changes to a crash or power
loss. It does not mean every write waits 120 seconds: application `fsync`
and other writeback activity have separate effects. Delayed allocation also
means the interval is not a universal upper bound on possible file-data loss.
[Kernel ext4 documentation](https://www.kernel.org/doc/html/latest/admin-guide/ext4.html)

No workload measurement here justifies 120 seconds or an intermediate
30/60-second compromise. There is also no observed SSD-health reason to
prefer this long interval. The recommended five-second default prioritizes
ordinary workstation durability. No fstab edit or remount was performed.

## Kernel Parameters

The current boot arguments are coherent with the actual encrypted LVM root
and swap-backed hibernation setup. Keep the root, cryptdevice, resume, and
read-write arguments. Existing discard permission already supports TRIM;
enabling the timer requires no new argument or initramfs rebuild.
[Arch encrypt hook](https://github.com/archlinux/mkinitcpio/blob/master/hooks/encrypt)

Intel P-state is already active, with the intended `powersave` governor and
`balance_performance` EPP while balanced is selected. Adding a parameter to
force the existing driver mode offers no demonstrated benefit.
[Intel P-state documentation](https://docs.kernel.org/admin-guide/pm/intel_pstate.html)

No observed fault justifies PCIe ASPM, NVMe power-state, CPU-idle, scheduler,
or mitigation overrides. Keep CPU vulnerability protections enabled. In
particular, upstream warns that forcing ASPM can lock up hardware.
[Kernel parameter documentation](https://docs.kernel.org/admin-guide/kernel-parameters.html)

If kernel parameters also means sysctl, the inspected values match the
repository: swappiness 10, dirty background/foreground ratios 5/10, dirty
expiry 30 seconds, writeback polling five seconds, cache pressure 100, zone
reclaim disabled, and heuristic overcommit. There was no sustained memory
or I/O pressure in the inspected samples. Fixed dirty-byte thresholds are
an optional later experiment if heavy writes produce measured stalls;
they are distinct from the ext4 journal commit interval.
[Kernel VM documentation](https://docs.kernel.org/admin-guide/sysctl/vm.html)

## mkinitcpio

Keep the current working BusyBox/udev hook chain. It unlocks encryption before
activating LVM and attempts resume after the swap LV is available. Both actual
stock and Zen initramfs images contain Intel early microcode, cryptsetup, LVM,
i915, NVMe, dm-crypt, and dm-mod, with matching kernel versions. Empty explicit
module/binary/file arrays do not indicate missing components: hooks populate
the images. There are no configuration drop-ins overriding the main file.

Keep the existing zstd compression. No measured boot bottleneck justifies
compression or hook rewrites.
[mkinitcpio configuration reference](https://github.com/archlinux/mkinitcpio/blob/master/man/mkinitcpio.conf.5.adoc)

The pending `/etc/mkinitcpio.conf.pacnew` needs a deliberate later review.
It contains the generic systemd-based hooks without this machine's encrypted
root/LVM support. Blindly accepting that file and rebuilding would remove
required boot components. A deliberate migration would require `sd-encrypt`,
LVM support, matching LUKS arguments or crypttab configuration, and tested
resume/recovery. No performance benefit has been established here.
[Upstream systemd hook](https://github.com/archlinux/mkinitcpio/blob/master/install/systemd)

Both presets currently build only their default image. An additional tested
fallback image/entry could improve recovery options; it would not accelerate
normal operation, and both installed kernels still share the same build
configuration.
