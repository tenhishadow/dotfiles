# Storage, encryption, and filesystem audit

This is a first-pass snapshot. The [current audit index](README.md) and
[completed read-only decisions](10-read-only-conclusions.md) include later
measurements, resolved access gaps, and corrected interpretations.

Read-only assessment on 2026-09-05. No storage settings, services, filesystems,
encryption metadata, or packages were changed. No TRIM, benchmark, filesystem
repair, or privileged command was run. Values below are curated observations,
not configuration backups. Sizes use binary units unless stated otherwise.

## Assessment

The existing NVMe -> LUKS2 -> LVM -> ext4 design is coherent. Current internal
storage observations do not demonstrate corruption, alignment trouble,
swapping pressure, or an active bottleneck. Historical logs do show real read
failures on an external Thunderbolt NVMe during a problematic sleep interval.
Investigate that incident, establish periodic TRIM, review the unusually long
journal interval, and give root more headroom after checking LVM.

The SSD is a Crucial T705 4 TB running at the laptop's PCIe 4.0 x4 link speed.
Its PCIe 5.0 capability cannot be unlocked through Arch tuning. Thermal behavior
under the owner's normal workload and actual SSD health remain open questions.

| ID | Priority | Finding | Confidence | Recommended next step |
| --- | --- | --- | --- | --- |
| ST-01 | High | External Thunderbolt NVMe read failures during a sleep incident | Confirmed errors and link loss; initiating cause unknown | Investigate enclosure/cable/power and sleep sequence before further attached-device sleep tests |
| ST-02 | High | Both ext4 mounts use `commit=120` | Confirmed | Review durability requirement; prefer the upstream default unless a measured benefit justifies the tradeoff |
| ST-03 | High | Root has about 17 GiB available and is 88% used | Confirmed | Identify coarse space consumers and verify free LVM extents before considering growth |
| ST-04 | Medium | Weekly TRIM timer disabled; no continuous discard | Confirmed configuration gap; previous manual TRIM unknown | Establish one documented periodic TRIM mechanism in a separately approved change |
| ST-05 | Medium | SSD wear, media errors, and firmware currency unverified | Permission/source gap | Obtain a minimal owner-approved health summary |
| ST-06 | Low | Crypto workqueue and I/O scheduler tuning might help a particular workload | Unproven | Measure workload latency before proposing an experiment |

“High” means address before further tuning, not evidence of imminent internal
SSD failure. Historical errors should not be confused with current corruption.

## ST-01: external NVMe disappeared during the sleep incident

Historical kernel records on 2026-09-03 establish this sequence in UTC:

| Time | Curated event |
| --- | --- |
| 09:41:13-14 | An OWC Express 1M2 Thunderbolt device appears; its PCIe path enumerates `nvme1` and six partitions on `nvme1n1` |
| 09:56:11 | The Thunderbolt device disconnects and its PCIe hotplug link goes down |
| 09:56:11 | `nvme1n1` reports host-aborted reads, read I/O errors, and buffer I/O errors |
| 09:56:13-14 | The same enclosure reconnects and the same PCIe path enumerates `nvme1` again |
| 09:56:32 | The enclosure disconnects again |

The consistent Thunderbolt and PCIe path strongly attributes these historical
errors to an external NVMe enclosure. They are not evidence that the current
internal Crucial drive failed. The current boot contains no matching NVMe I/O
fault records in the checked journal.

The events overlap the hybrid-sleep failure investigated in the boot report.
They do not establish whether manual unplugging, the cable, enclosure power,
firmware, or sleep sequencing caused the disconnect. A later ASPM reconfiguration
message alone does not justify globally disabling PCIe power management.

Before a later reproduction, identify whether the drive was mounted or being
read when sleep began and establish an owner-approved backup/recovery plan for
that external drive. Compare the same normal sleep scenario with the enclosure
detached, then attached, only when interruption is acceptable. No reproduction,
external filesystem scan, or repair was attempted here.

## Observed layout and healthy properties

| Layer | Observation | Interpretation |
| --- | --- | --- |
| NVMe | 4,000,787,030,016 bytes; non-rotational | Approximately 3.64 TiB physical capacity |
| EFI partition | 1 GiB FAT32; about 118 MiB used | No current boot-partition space pressure |
| Encryption | LUKS2 partition, one active crypt mapping | Root, home, and swap share the encryption boundary |
| Root LV | 150 GiB; ext4; 88% used | Approximately 123 GiB used and 17 GiB available to ordinary users |
| Home LV | 500 GiB; ext4; 34% used | Approximately 156 GiB used and 313 GiB available |
| Swap LV | 70 GiB; zero usage at sampling | No observed swapping pressure |
| Sectors | 4096-byte logical and physical sectors throughout `lsblk` | No exposed 512-byte emulation mismatch |
| Alignment | Zero reported alignment offset; partition starts at MiB boundaries | No visible reason to repartition for alignment |
| Filesystems | 4096-byte blocks; ext4 error and warning counters zero | No recorded error in these counters; not a full integrity check |
| Inodes | Root 22% used, home 7% used | Space, rather than inode exhaustion, is the root concern |
| Queue | Scheduler `none`; read-ahead 128 KiB | No evidence that a different scheduler is necessary |
| Temporary files | `/tmp` is tmpfs | This existing choice already avoids ordinary `/tmp` disk writes |

The visible LVs total 720 GiB, whereas the active encrypted device is roughly
3.64 TiB. About 2.94 TiB is therefore not represented by those visible LVs.
This is an inference from active topology, **not proof of free VG space**:
inactive LVs or a smaller PV can change the explanation. Unprivileged
`lvs --readonly` could not access device mapper.

The difference between free and user-available filesystem blocks is roughly
7.5 GiB on root and 23 GiB on home. That is consistent with reserved space,
but the exact superblock reserve configuration was not readable. Reclaiming
the home reserve would offer capacity, not a demonstrated speed increase.
Root needs operating headroom even if its reserve is retained.

## Journal interval: a real durability tradeoff

Both active mounts and their persistent fstab entries specify
`noatime,commit=120,errors=remount-ro`. The kernel's documented journal
transaction interval defaults to five seconds. A longer interval can reduce
commit frequency but increases exposure for recent unsynchronized changes
during a crash or power loss. It is not an exact “120 seconds of every file”
loss guarantee: application synchronization, dirty-page writeback, and
delayed allocation affect what reaches storage.
[Kernel ext4 documentation](https://docs.kernel.org/admin-guide/ext4.html#options)
describes these semantics.

Recommendation: prefer the default commit interval in the next authorized
change unless a representative measurement supports retaining 120 seconds.
The laptop battery does not protect against every kernel crash or forced
power-off. Keep journaling and write barriers; do not combine performance
experiments with reduced crash consistency.

There is no observed reason to replace ext4 or flatten LVM for performance.
The existing layout already provides encrypted swap and independently sized
filesystems. Such migrations would create considerably more operational work
than the evidence justifies.

## TRIM: propagation configured, routine execution missing

The relevant observations agree:

- The active kernel command line explicitly includes `allow-discards` for the
  encrypted mapping.
- `lsblk` advertises a 4 KiB discard granularity and nonzero discard maximum
  through NVMe, encryption, and each LV.
- Neither ext4 mount advertises continuous `discard`.
- `fstrim.timer` is disabled and inactive, with no last-trigger timestamp.
- The available journal has no `fstrim.service` records. Searches of the
  inspected system service and cron locations found no alternative schedule.

This establishes the missing standard schedule, not that the SSD has never
been trimmed. Previous manual invocations and inaccessible history remain
unknown. Advertising discard also does not prove a completed hardware TRIM.

The straightforward future choice is the packaged weekly timer, which already
includes persistence for missed runs. Its source is the
[upstream util-linux timer](https://github.com/util-linux/util-linux/blob/master/sys-utils/fstrim.timer).
The [upstream fstrim manual](https://raw.githubusercontent.com/util-linux/util-linux/master/sys-utils/fstrim.8.adoc)
supports weekly trimming for typical desktops. Enabling the service alone
does not establish a recurring schedule. Successful service exit is also
insufficient evidence: the installed service suppresses unsupported-operation
errors, so validation should verify the intended root and home filesystems.

TRIM makes unused filesystem ranges available to the SSD; it does not delete
live filesystem content. It can disclose allocation patterns through an
encrypted block device. This host already permits propagation, but the privacy
decision should still be documented when actual scheduled discards are added.
See the [kernel dm-crypt discard documentation](https://docs.kernel.org/admin-guide/device-mapper/dm-crypt.html).

Do not claim a specific endurance or throughput improvement without health and
workload measurements. Filesystem free space, unallocated LVM extents, and
controller-visible unused flash are different quantities. No whole-device
discard operation belongs in this remediation.

## NVMe capability, temperature, and endurance

Sysfs identifies model `CT4000T705SSD3`, firmware `PACR5111`, and a live
controller. The endpoint supports 32 GT/s x4; the negotiated link is
16 GT/s x4. Lenovo specifies a PCIe 4.0 x4 storage slot for this laptop,
consistent with that observation.
[Lenovo PSREF](https://psref.lenovo.com/syspool/Sys/PDF/ThinkPad/ThinkPad_X1_Carbon_Gen_11/ThinkPad_X1_Carbon_Gen_11_Spec.pdf)
is the hardware reference. A different filesystem or kernel cannot turn
this platform link into PCIe 5.0.

The readable composite temperature was about 37 C with the temperature alarm
clear. This was light activity, not a sustained-load thermal test. A two-second
passive I/O sample showed very little activity, and the available I/O pressure
averages were zero. Neither observation establishes compile-time or
container-build performance.

The useful measurement is SSD temperature and latency during a normal build,
large checkout, or container operation the owner already intends to run.
Observe whether throughput falls while temperature rises before attributing a
slowdown to thermal throttling. Physical cooling contact was not inspected.

`nvme smart-log` was denied access to the root-owned controller device. The
following remain unknown: percentage used, available spare, media errors,
critical warnings, unsafe shutdown count, lifetime host writes, and thermal
management events. Firmware currency could not be established because the
vendor support pages rejected direct access. No firmware update is recommended
solely from the version string.

The ext4 lifetime write counters correspond to roughly 5.44 TB for root and
21.42 TB for home, in decimal bytes after converting the reported KiB. These
measure filesystem writes, not NAND writes or remaining SSD life. They omit
other activity and provide no age-normalized daily rate. Do not infer SSD wear
percentage or write amplification from them. The counter meaning is documented
in [ext4 sysfs documentation](https://docs.kernel.org/admin-guide/ext4.html#sys-entries).

## Encryption tuning and recovery gaps

LUKS2 is confirmed, but active cipher, key size, internal encryption sector
size, KDF costs, and persisted performance flags were not verified.
`cryptsetup status` requires access unavailable to this session. A 4096-byte
logical block report is useful evidence but does not independently certify
every LUKS format parameter. Keys, keyslot contents, tokens, and headers were
not read.

Workqueue bypass flags are possible experiments only after establishing an
I/O-bound workload. Upstream explicitly treats them as low-level tuning.
`high_priority` can improve crypt I/O while degrading overall responsiveness,
which conflicts with the goal of a responsive developer laptop.
[Cryptsetup option documentation](https://gitlab.com/cryptsetup/cryptsetup/-/raw/main/man/common_options.adoc)
also shows why an absent command-line flag cannot prove an absent persisted
LUKS2 flag.

Changing the password KDF is not a general application-I/O optimization:
unlocking and the already-open block-encryption path are different stages.
Do not weaken the KDF or reencrypt the drive for hypothetical gains. Recovery
media, a restorable backup, and protected header recovery arrangements were
outside this inspection and remain unverified.

## Swap, hibernation, and writeback policy

The swap LV is inside LUKS2. The kernel's configured resume device matches
the active swap device; the resume offset is zero, appropriate for this
partition-backed LV. The configured mkinitcpio hook order places encryption
and LVM activation before `resume`. These are positive configuration signs,
not proof that the built initramfs or a full hibernate/resume cycle works.

The configured image-size value is about 24.9 GiB; this is not a measurement
of the actual image. The 70 GiB swap volume offers substantial nominal
headroom, but successful hibernation also depends on available swap, drivers,
and early device activation. Resume must happen before filesystems are used.
[Kernel hibernation documentation](https://www.kernel.org/doc/html/latest/power/swsusp.html)
explains the initramfs/LVM dependency. No sleep-state test was performed.

The live values match the repository's memory policy:

| Setting | Live value | Assessment |
| --- | --- | --- |
| `vm.swappiness` | 10 | Low swapping preference; no current pressure to justify changing it |
| `vm.dirty_background_ratio` | 5 | Background flushing threshold is proportional to dirtyable memory |
| `vm.dirty_ratio` | 10 | Writers may participate in flushing at a higher proportional threshold |
| Dirty-byte overrides | Both zero | Ratio thresholds are in use |
| Dirty expiry / writeback interval | 30 seconds / 5 seconds | Separate from the ext4 journal interval |
| `vm.vfs_cache_pressure` | 100 | No observed reason for a cache-pressure adjustment |

On a 64 GiB laptop, ratio thresholds can allow substantial dirty data, but
they are not fixed percentages of installed RAM. Change to byte thresholds
only if real copy/build activity shows long writeback stalls. Avoid periodic
cache dropping: it forces useful cached data to be fetched again.
[Kernel VM documentation](https://docs.kernel.org/admin-guide/sysctl/vm.html)
defines these thresholds and cache behavior.

## Repository ownership and next investigation

The relevant VM settings are declared in
`inventory/host_vars/this_host/security.yml`, and they match the live values.
The inspected repository roles and inventory contain no management of
`fstrim`, the observed mount options, LUKS, or LVM. These storage choices appear
to sit outside the repository's current apply contract. No evidence here shows
the repository repeatedly overwriting them.

Any future managed TRIM service or mount-policy change belongs behind the
explicit privileged system workflow. The default user-dotfiles workflow
should remain unaffected.

The next storage task can be delegated independently:

1. Obtain an owner-approved, minimal privileged read-only summary of SSD health,
   actual PV/VG free space and LV types, ext4 reserved blocks, and nonsecret
   active crypt parameters. Do not request raw headers, tokens, serials, or
   configuration dumps.
2. Identify root space use by coarse category without inspecting private file
   contents. Decide whether modest root growth is appropriate after confirming
   free extents; do not allocate all remaining capacity speculatively.
3. Prepare a narrow proposed change for the journal interval and weekly TRIM,
   with explicit validation and rollback. Applying it requires a later decision.
4. Observe an ordinary development workload using bounded passive sampling,
   for example `iostat -d -x -m -y 1 10`, plus current I/O pressure and SSD
   temperature. Only then decide whether a scheduler or crypt workqueue trial
   has a measurable target.

ArchWiki SSD, dm-crypt, and LVM pages were requested, but direct page access
returned an anti-bot denial. Search indexing exposed partial material; it was
not treated as a complete page review. The recommendations above rely on the
linked upstream documents that were successfully opened, local installed
units, and observed runtime state.
