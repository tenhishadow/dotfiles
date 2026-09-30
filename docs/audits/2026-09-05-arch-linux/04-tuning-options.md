# Tuning Options and Arch Derivatives

This is a first-pass snapshot. The [current audit index](README.md) and
[completed read-only decisions](10-read-only-conclusions.md) include later
measurements, resolved access gaps, and corrected interpretations.

Audit date: 2026-09-05. These are proposals for later evaluation; nothing in
this document was applied or benchmarked. Host facts come from the companion
reports. Performance judgments below are engineering assessments, not measured
speedups.

## Recommendation

Keep this Arch installation. Resolve storage maintenance, recovery, and
dock/sleep faults first, then compare the already installed stock and Zen
kernels under an actual development workload. The current evidence does not
justify a distribution or filesystem migration.

CachyOS is a plausible match for the unnamed distribution in the request;
that identification is an assumption. Its useful ideas can be evaluated
individually. There is no evidence that this machine needs an entirely new
desktop or a system-wide rebuild to become responsive.

## Distribution Comparison

| Choice | Relevant difference | Assessment for this laptop |
| --- | --- | --- |
| Existing Arch | Already working Plasma Wayland, Intel graphics, encrypted ext4/LVM, stock and Zen packages, declarative workstation tooling | Best baseline and lowest migration cost. Fix observed gaps in place. |
| CachyOS | CPU-targeted repositories and a customized kernel with compilation and scheduler changes | A later controlled experiment; adds another package/kernel maintenance and trust surface. No ThinkPad-specific speedup has been measured here. |
| Manjaro | Separate stable, testing, and unstable package branches | A different update policy, not evidence of faster execution on this hardware. Switching branches or distributions does not repair the observed mount, trim, or dock issues. |

CachyOS documents its repository variants and kernel features separately;
changing the kernel and replacing the package base are different experiments.
Manjaro documents its own staged release branches. Sources:
[CachyOS repositories](https://wiki.cachyos.org/features/optimized_repos/),
[CachyOS kernel](https://wiki.cachyos.org/features/kernel/), and
[Manjaro branches](https://wiki.manjaro.org/index.php?title=Switching_Branches).

## What Can Be Borrowed

| Idea | Current evidence | Recommendation |
| --- | --- | --- |
| CPU-targeted packages | The installed dynamic loader reports x86-64-v3 as supported; v4 is listed without the supported marker. CPU flags lack AVX-512. | v3 is the relevant ceiling for this host. Do not select v4 or AMD `znver4` builds. Start with one CPU-bound application if profiling justifies it. |
| Alternative scheduler/kernel | Stock Arch is running and Zen is already installed. No controlled latency comparison exists. | Compare stock versus Zen first. Consider a CachyOS kernel only if the first comparison leaves a defined problem unresolved. |
| Easy power-profile selection | TuneD balanced is active; the Power Profiles compatibility bridge is absent. | Improving Plasma profile integration is a more direct usability candidate than replacing the distribution. See the boot/power report. |
| Recovery before package upgrades | Upgrade/cleanup coupling and an unverified rescue boot path leave recovery-policy gaps. | Define package retention and a tested rescue path first. Keep backups independent of the internal SSD. |
| Snapshot integration | Current filesystems are ext4 inside LVM. | Btrfs snapshots are an operational feature, not a proven speed fix. Do not convert a working encrypted installation solely for snapshots. |

The CPU-target recommendation is supported by the local loader result and
[CachyOS's compatibility guidance](https://wiki.cachyos.org/features/optimized_repos/).
CachyOS documents package-operation snapshots, but also distinguishes them
from independent backups. That recovery model is worth studying without
assuming its filesystem must be adopted.
[CachyOS snapshot documentation](https://wiki.cachyos.org/configuration/btrfs_snapshots/)

## Why Not Copy a Tuning Bundle

The upstream CachyOS settings repository describes zram-related swappiness,
device-specific I/O schedulers, short systemd timeouts, THP settings, and
power-related rules. These settings form a coordinated policy for that
distribution. Importing the package wholesale would introduce additional
writers alongside this repository and TuneD.
[CachyOS settings source](https://github.com/CachyOS/CachyOS-Settings)

For this laptop, especially avoid importing a high swappiness value without
its compressed-swap context, aggressive service timeouts without observing
shutdowns, or hardware rules intended for a different GPU or storage stack.
Prefer a single justified setting, a named owner, and an observable outcome.
The absence of another distribution's setting is not itself a defect.

## Memory and CPU Experiments

The live memory snapshot had approximately 49 GiB available, no used swap,
and zero memory pressure averages. MGLRU was already enabled with mask
`0x0007`. This is not an installation missing modern reclaim support.
The mask's interface is documented in
[the kernel MGLRU guide](https://docs.kernel.org/admin-guide/mm/multigen_lru.html).

| Candidate | When it could help | Why it is not an immediate recommendation |
| --- | --- | --- |
| zram or zswap | Repeated memory pressure with substantial anonymous-page swapping | Current snapshot has neither. Keep disk-backed hibernation available; compressed RAM is not a persistent resume device. |
| THP policy | A measured database, VM, or allocator workload affected by compaction or TLB pressure | Current policy is `always`, with defrag `madvise`. A universal `never` or `always` recommendation is unsupported. Check the actual application's upstream guidance. |
| Higher build concurrency | CPU-bound builds with idle execution capacity | The i7-1370P has heterogeneous cores and laptop power limits. Twenty logical CPUs do not imply that twenty build jobs always win. |
| Build cache | Repeated compilation of overlapping inputs | Measure cache hit rate and wall time; cache space belongs in capacity planning. It cannot accelerate unrelated workloads by itself. |
| Per-application native compilation | A profiled hot path sensitive to code generation | Rebuilding every package adds maintenance and build cost. Machine-specific binaries also lose portability. |
| IRQ affinity, E-core disabling, CPU pinning | Reproducible latency issue attributable to scheduling or IRQ placement | No such issue is demonstrated. Keep the scheduler's ordinary topology handling as the baseline. |

THP has separate allocation and defragmentation controls; its costs depend on
workload. Source:
[kernel THP documentation](https://docs.kernel.org/admin-guide/mm/transhuge.html).

## Storage and Desktop Experiments

| Candidate | Decision |
| --- | --- |
| NVMe queue scheduler | Current `none` is a valid baseline. Compare only after observing a mixed-I/O latency problem; another scheduler's presence is not proof of improvement. |
| dm-crypt workqueue flags | Do not toggle without verified cipher/sector/workqueue state and workload measurements. They can trade throughput against latency and CPU scheduling behavior. |
| NVMe APST or PCIe ASPM | Preserve existing power management until an identified device timeout or resume defect justifies a narrowly scoped change. Disabling either globally can increase heat and battery drain. |
| Faster NVMe link | The Gen5-capable internal SSD currently negotiates Gen4 x4. No filesystem flag can create a Gen5 upstream link. |
| Filesystem conversion | No ext4 corruption or filesystem-specific performance bottleneck has been established. Keep ext4/LVM for this pass. |
| External display refresh | The active docked output is 4K at 60 Hz. Advertised lower-resolution high-refresh modes offer an explicit sharpness-versus-motion tradeoff; test with the actual monitor and link. |
| Browser video acceleration | Installed Intel support does not prove that a particular browser/video path uses hardware decoding. Verify on a representative video through the browser's diagnostics, without exporting profiles. |

These decisions are specific to the observations in
[storage](01-storage.md) and [boot, power, and desktop](02-boot-power-desktop.md).
They do not claim a measured scheduler, codec, or encryption speedup.

## Experiments to Reject for This Pass

- Disabling CPU vulnerability mitigations for a general development laptop.
- Reducing LUKS password-derivation strength to save unlock time.
- Disabling filesystem journaling or flush/barrier protections.
- Increasing dirty-data retention or ext4 commit intervals without a measured
  workload benefit and an explicit durability decision.
- Forcing maximum CPU frequency or disabling all device power saving globally.
- Running raw-device write benchmarks on the installed NVMe.
- Dropping caches as an everyday optimization or deleting caches indiscriminately.
- Treating a benchmark from another CPU, desktop GPU, or desktop cooling system
  as a prediction for this ultrabook.

## Measurement Contract

For every later experiment, keep the same workload revision, kernel package
record, AC/battery state, dock, monitor mode, power profile, and background
activity. Record both interactive latency and work completed; throughput alone
does not describe desktop responsiveness.

Use several repetitions with warm-up and comparable temperatures. Report the
median and observed spread; distinguish cold from warm caches. Log pressure
and thermals alongside elapsed time. Reject a result smaller than the observed
variation, or one that improves throughput by an unacceptable battery, noise,
reliability, or latency cost. These are proposed acceptance rules, not an
experiment already performed.

PSI measures time stalled on CPU, memory, or I/O resources, making it useful
for identifying pressure rather than inferring it from installed package counts.
[Kernel PSI documentation](https://docs.kernel.org/accounting/psi.html)
