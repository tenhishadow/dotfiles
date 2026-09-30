# Storage Investigation and Concrete Maintenance Proposal

Subsequent status: the user authorized periodic TRIM; see
[the implementation and boot review](16-trim-and-boot-review.md). The findings
below preserve the earlier read-only observations.

Second read-only pass on 2026-09-05. This supersedes the permission gaps in
[the initial storage report](01-storage.md). Existing noninteractive sudo
access allowed targeted diagnostic reads. No resize, TRIM, repair, mount,
encryption change, cleanup, benchmark, or firmware operation was performed.

## Verdict

The internal SSD's available health indicators are good. The encrypted storage
stack is correctly aligned and uses contemporary, sensible parameters. The
main storage improvement is capacity and maintenance policy, not a new
filesystem or cipher. Exact LVM metadata confirms ample space for a modest
root expansion without touching the partition table or shrinking home.

The historical external enclosure incident is examined separately in
[the dock and sleep investigation](06-dock-sleep-investigation.md). It is not
an internal-media-health finding.

## SI-01: Internal SSD Health Is Now Verified

| SMART field | Observed value | Interpretation |
| --- | --- | --- |
| Critical warning | 0 | No current critical-warning bits set |
| Available spare / threshold | 100% / 5% | Spare indicator comfortably above its threshold |
| Percentage used | 1% | Low vendor-estimated endurance consumption; not a lifespan guarantee |
| Media/data integrity errors | 0 | No errors counted in this field |
| Error-log entries | 0 | No entries counted at this reading |
| Composite temperature | 311 K, approximately 38 C | Light-session temperature, not a load maximum |
| Warning / critical-temperature time | 0 / 0 | No recorded time in these temperature conditions |
| Thermal-management transition counters | 0 / 0 | No transitions counted in the exposed fields |
| Power-on hours | 15,521 | Approximately 647 powered-on days, not installation age |
| Unsafe shutdowns | 18 | Historical unclean shutdown events; not equivalent to 18 media failures |
| Power cycles | 123 | Lifetime device counter |
| Host data written | Approximately 33.00 TB decimal, 30.01 TiB | From 64,447,647 NVMe data units; not NAND writes |

The standard data-unit conversion is 512,000 bytes. The kernel-facing NVMe
definitions distinguish host-write counters from endurance estimates.
[libnvme SMART field documentation](https://raw.githubusercontent.com/linux-nvme/libnvme/master/src/nvme/types.h)

The lifetime host-write rate is about 51 GB per powered-on day. It is not a
measured recent daily workload and cannot predict the next year's writes.
Nothing in these counters supports a claim that this setup is rapidly wearing
out the SSD. They also cannot rule out a future failure or replace a backup.

Firmware remains `PACR5111`. The second firmware investigation found no
matching release in the freshly retrieved public LVFS catalog or the device's
LVFS release query. Crucial's direct support content rejected retrieval. This
leaves vendor firmware currency unresolved; absence from LVFS does not mean
the installed firmware is the newest.

## SI-02: LVM Space and Root Consumers Are Established

`vgs`, `pvs`, and `lvs` were run with `--readonly` and selected fields.

| Property | Verified result |
| --- | --- |
| Volume group | One VG, one PV, three LVs |
| VG capacity | 3,999,692,488,704 bytes |
| Free extents | 3,226,598,375,424 bytes: 3,005.00 GiB, approximately 2.935 TiB |
| Root | 150 GiB, linear |
| Home | 500 GiB, linear, represented by two segments |
| Swap | 70 GiB, linear |
| PV extent start | 1 MiB inside the encrypted mapper |

Two segment rows for home describe one 500 GiB LV, not two 500 GiB volumes.
There is no thin pool, RAID layer, or copy-on-write snapshot in this observed
layout. Additional linear segments on an SSD do not themselves prove a
performance problem.

Privileged `du -x` queries read allocation metadata without reading file
contents. The root filesystem's visible allocation was approximately:

| Category | Allocated space |
| --- | --- |
| `/usr` | 49.35 GiB |
| `/var` | 66.57 GiB |
| `/opt` | 4.04 GiB |
| `/root` | 2.14 GiB; contents not inspected |
| Root total reported by `du` | 122.13 GiB |
| Docker within `/var` | 65.59 GiB |
| Logs within `/var` | 0.37 GiB |
| Cache within `/var` | 0.08 GiB |

These complete the earlier unprivileged lower bounds. Filesystem accounting
and directory allocation need not match exactly because of metadata,
reserved blocks, deleted-open files, and concurrent activity. No large
unexplained discrepancy was established here.

Docker's aggregate accounting reported 26 images, two containers, 12 volumes,
and 78 build-cache records. It marked approximately 39.46 GB of images,
14.65 GB of build cache, and 1.99 GB of volumes reclaimable. These figures
are not additive guaranteed disk savings: shared image/build layers and
different accounting views overlap.
[Docker disk-usage semantics](https://docs.docker.com/reference/cli/docker/system/df/)

An unused Docker volume can still contain valuable persistent data. Do not
include volume deletion in an automatic cleanup proposal. Keeping reusable
build layers can also improve developer speed. With approximately 3 TiB of
verified free extents, forcing constant cache deletion is unnecessary.

## SI-03: Encryption Parameters Need No Performance Repair

Only nonsecret performance metadata was selected for the report; no keys,
passphrases, salts, digests, token fields, or raw metadata dump were retained.

| Parameter | Observed state |
| --- | --- |
| Format and cipher | LUKS2, `aes-xts-plain64` |
| Active total key length | 256 bits |
| Encryption sector size | 4096 bytes |
| Data offset | 16 MiB |
| Password derivation | Argon2id, time cost 8, memory 1,048,576 KiB, four lanes |
| Active performance flags | Discards only; no workqueue-bypass or high-priority flags |
| Key placement | Kernel keyring; contents not queried |

XTS uses two keys: a 256-bit total XTS key corresponds to two 128-bit keys,
not AES-256-XTS. A 512-bit total key would be the latter. This distinction
should be documented accurately, but it does not justify a live reencryption
as a speed optimization.
[Cryptsetup's XTS key-size explanation](https://gitlab.com/cryptsetup/cryptsetup/-/raw/main/FAQ.md)

Argon2id's time cost is an iteration/pass parameter, not eight seconds.
Its memory and parallelism apply to unlocking. They do not impose that cost
on every file read after the device is open. Current settings offer no
evidence of an accidentally cheap password KDF or a runtime throughput defect.
Passphrase strength itself was neither requested nor inspected.
[Cryptsetup PBKDF option semantics](https://gitlab.com/cryptsetup/cryptsetup/-/raw/main/man/common_options.adoc)

Keep the present encryption geometry. Test workqueue bypass only if a later
real workload identifies dm-crypt scheduling as a bottleneck. The upstream
high-priority option explicitly trades general responsiveness for crypt I/O;
that is a poor unmeasured default for this laptop.
[Kernel dm-crypt controls](https://www.kernel.org/doc/html/latest/admin-guide/device-mapper/dm-crypt.html)

## SI-04: Mount Policy and Reserves

Both filesystems have journals, extents, 64-bit support, checksums, and online
resize support. The superblocks report a clean state. Mounted-state features
such as `needs_recovery` and `orphan_present` must not be mistaken for a
diagnosis requiring an online repair. No integrity scan was attempted.

The superblock's default error behavior is Continue, but the active mounts
explicitly use `errors=remount-ro`. Mount options override the superblock
default, so this is not contradictory effective behavior.
[E2fsprogs tune2fs manual](https://man7.org/linux/man-pages/man8/tune2fs.8.html)

| Reserve | Verified amount | Decision |
| --- | --- | --- |
| Root | 1,966,080 blocks, 7.5 GiB, 5% | Preserve operating headroom; reserve reduction alone does not solve growth |
| Home | 6,034,503 blocks, about 23.02 GiB, 4.60% | Optional capacity policy; no present shortage justifies changing it |

Mount-count/time-based periodic checks are disabled. That alone is not an
ext4 fault. A future offline check belongs in a recovery/maintenance context,
not a performance cron job against mounted filesystems.

The observed `commit=120` remains the clearest unnecessary durability
tradeoff. Recommend the ordinary five-second transaction interval for the
next approved change. Retain `noatime` and `errors=remount-ro`, and retain
write-flush/journal protections. This is a durability recommendation without
a promised throughput gain.

## SI-05: NVMe Power Management Is Functioning at the APST Layer

The controller supports autonomous power-state transitions, and the current
APST feature is enabled. Its table transitions idle operational states to
power state 4 after 100 ms. The reported low-power exit latency is 3 ms;
these are controller parameters, not measured end-to-end application latency.

The kernel's maximum APST-latency policy is 100,000 microseconds. PCIe ASPM
uses the default policy. The controller PCI function has runtime power control
set to `on`, while APST is enabled internally. These are distinct mechanisms;
the former is not proof that NVMe power saving is wholly disabled. The
namespace's runtime-status field saying unsupported is likewise not a drive
failure.

Keep this baseline. A later laptop power measurement could compare a supported
controller runtime policy, but the present evidence does not justify forcing
one. In particular, do not disable APST on the healthy internal SSD to address
an external Thunderbolt device that disappeared before kernel sleep entry.

## Proposed Storage Changes, Not Applied

### Root capacity

Recommended target: **300 GiB root LV**, leaving approximately 2,855 GiB free
in the VG. This doubles the current root budget and preserves most free
capacity for future explicit uses. It is a capacity-planning judgment, not
a filesystem performance requirement.

The reviewable future operation is an absolute target:

```bash
# Future maintenance only, after backup/recovery preconditions are satisfied.
sudo lvextend --resizefs --size 300G /dev/rootvg/root
```

Before execution, recheck free extents, current sizes, root mount identity,
backup recovery, AC power, and absence of an active storage incident. No
partition, PV, LUKS-container resize, home shrink, or all-free-extents
allocation is needed. LVM can extend the LV and request filesystem growth;
ext4 supports online expansion.
[LVM lvextend manual](https://man7.org/linux/man-pages/man8/lvextend.8.html),
[E2fsprogs resize2fs manual](https://man7.org/linux/man-pages/man8/resize2fs.8.html)

Validate the resulting LV and filesystem sizes, free space, and new kernel
messages. If LV growth succeeds but filesystem growth fails, inspect and
complete filesystem growth; do not automatically reduce the LV. Shrinking
ext4 is an offline, separate risk, so reverting the command text is not a
rollback. Restorable backups and a recovery environment are the recovery path.

### Commit policy

The proposed configuration change is to replace `commit=120` with `commit=5`
on the existing root and home fstab entries, preserving source IDs, mount
points, other options, dump fields, and fsck order. The report intentionally
does not copy machine-specific fstab entries into the repository.

Validate fstab syntax and both effective mounts after the separately approved
remount or reboot. A rollback can restore the old interval; it cannot undo
data lost during an earlier crash. If the policy becomes Ansible-managed,
keep it in the explicit privileged layer with narrowly identified mounts.

### Periodic TRIM

The installed weekly timer is the simplest mechanism. Its current unit uses
`OnCalendar=weekly`, persistence, and randomized delay. The service reads
fstab/mount information and suppresses unsupported-operation failures.

```bash
# Future maintenance only; starting a persistent timer may schedule work soon.
sudo systemctl enable --now fstrim.timer
```

Do not run a second competing cron implementation. In a later managed change,
declare this timer through `ansible.builtin.systemd_service` behind the
existing privileged host/container guards. Default user dotfiles must remain
unaffected. Successful validation must show root and home were actually
processed, not merely an enabled timer or a zero service exit status.
[Upstream fstrim behavior](https://raw.githubusercontent.com/util-linux/util-linux/master/sys-utils/fstrim.8.adoc)

Discard propagation is already active, but actual TRIM can expose allocation
patterns to an offline observer. The user should retain that explicit policy
decision. Stopping/disabling the timer stops future scheduled work; previously
discarded free-space contents cannot be restored by disabling it.

## Remaining Boundary

This closes the live health, geometry, free-space, allocation, and active
crypto-parameter questions. What remains cannot be proved by these reads:
successful TRIM, a completed resize/remount, recovery from backups, cold
hibernation restore, workload speedups, and vendor firmware not available from
the accessible sources. No write operation was used to manufacture such proof.

Installed diagnostic versions: cryptsetup 2.8.7, LVM2 2.03.42, e2fsprogs
1.47.4, nvme-cli 2.16, and util-linux 2.42.2. Measurements are a dated
snapshot and should be rechecked before implementation.
