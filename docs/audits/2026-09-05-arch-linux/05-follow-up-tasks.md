# Follow-up Tasks and Measurement Plan

This is a first-pass snapshot. The [current audit index](README.md) and
[completed read-only decisions](10-read-only-conclusions.md) include later
measurements, resolved access gaps, and corrected interpretations.

These are bounded handoffs after the read-only audit of 2026-09-05. They are
not authorization to implement changes. No privileged command, reproduction
requiring sleep, benchmark, or maintenance operation below was executed by
this audit unless the corresponding findings report explicitly says so.

## Suggested Parallel Assignment

| Task | Best first owner | Dependency | Deliverable |
| --- | --- | --- | --- |
| A: External NVMe and sleep | A second independent agent, including Claude if available | Existing storage and boot reports | Correlated timeline, competing explanations, smallest safe next diagnostic |
| B: Storage maintenance and recovery | Storage-focused agent | A before any drive-specific workaround | Reviewed proposal for root capacity, commit policy, TRIM, and recovery verification |
| C: Shell and editor latency | Development-focused agent | Independent of A/B | Ranked changes with workload-specific validation plan |
| D: Kernel and power comparison | Performance-focused agent | Recovery path checked; measurement explicitly authorized | Stock versus Zen results, including latency and energy costs |
| E: Boot trust and firmware | Platform/security agent | Recovery method and desired sleep behavior | Separate boot-integrity design, current firmware comparison, rollout and recovery plan |

Tasks A and C can start in parallel. Do not duplicate another repository-wide
audit. The first pass has already identified useful work; investigate the
specific uncertainty assigned to each task.

## Task A: External Storage, Dock, and Hybrid Sleep

Read [ST-01](01-storage.md) and BP-02/BP-03 in
[the boot and desktop report](02-boot-power-desktop.md).

The historical kernel timeline identifies an external OWC Express 1M2
Thunderbolt NVMe enclosure. It disconnects immediately before read and buffer
I/O errors for the then-named `nvme1n1`. Hybrid sleep subsequently falls back
to ordinary suspend. This does not identify failing internal SSD media.

Required work:

1. Independently check the event ordering and which device disappeared. Do
   not use a kernel device number as a permanent hardware identity.
2. Separate possible cable/enclosure power loss, deliberate unplugging,
   controller/firmware behavior, and suspend ordering. Correlation alone
   cannot select the cause.
3. Determine whether filesystems on that enclosure were mounted and busy
   at the time, if retained metadata permits. Do not inspect file contents.
4. Keep the OWC enclosure and ThinkPad dock USB-audio endpoint distinct;
   they may share a topology, but that has not established one common fault.
5. Propose the smallest later reproduction matrix: docked/undocked,
   enclosure present/absent, with work saved and storage safely quiesced.
   Actual sleep, unplug/replug, and filesystem operations need a subsequent
   authorized test session.

Acceptance: explain what is confirmed, what would falsify each explanation,
and whether any device-specific workaround is warranted. Reject blanket
APST/ASPM disablement without device-specific evidence.

Historical kernel queries must use `_TRANSPORT=kernel` across retained boots;
`journalctl -k` normally implies the current boot. Select the short interval
around 2026-09-03 09:56 UTC. Retain only redacted event descriptions, never
serial numbers, identifiers, complete journals, or application contents.

## Task B: Storage Maintenance and Recovery

Read ST-02 through ST-06 in [the storage report](01-storage.md).

The first read-only session lacked access to block-device metadata and `/boot`.
The following targeted commands are examples for an owner-run privileged
read-only session. They are not a request to run all commands indiscriminately:

```bash
sudo vgs --units g -o vg_name,vg_size,vg_free
sudo lvs --units g -o lv_name,lv_size,segtype,devices
sudo cryptsetup status sec
sudo tune2fs -l /dev/mapper/rootvg-root
sudo tune2fs -l /dev/mapper/rootvg-home
sudo nvme smart-log /dev/nvme0
```

Keep only the values needed for the decision. Do not retain filesystem IDs,
raw LUKS metadata or tokens, disk serial numbers, key material, or complete
command dumps in the repository. If the NVMe numbering changed, first map the
current internal device by its topology and model. Do not run `dmsetup table`
with key-display options.

Required output:

- Exact free VG space and the root consumers by top-level size, with explicit
  unreadable-path gaps. Do not recursively inspect personal file contents.
- Proposal for root headroom using verified free capacity; no shrinking or
  partition surgery assumed. Explain backup and failure recovery before any
  future resize. Growth should not be presented as trivially reversible.
- Proposed ext4 commit policy and an explanation of the durability tradeoff.
  A longer interval is not a guarantee of fewer application `fsync` writes.
- TRIM maintenance proposal with active discard propagation and privacy
  implications checked. Enabling a timer or issuing FITRIM is an actual
  state-changing maintenance action, even though it is routine.
- SMART health counters, percentage used, data written, thermal history, and
  relevant model-specific firmware guidance. Do not infer NAND wear from
  filesystem write counters.
- Verified stock/Zen boot entries, usable recovery medium, and independent
  backup/restore strategy. Backup keys, passwords, and backup contents are
  outside the audit's data collection.

Acceptance: produce a concrete patch proposal and ordered operator plan for
review, including validation and failure recovery. Do not apply it.

## Task C: Development Experience

Use [the development report](03-development.md) as the scope boundary.

Required work:

1. Propose a failure-aware upgrade helper with bounded cache retention and
   user review of upgrade prompts. Preserve rollback capability.
2. Identify the packaged Bash completion mechanism for each affected command.
   Compare first-prompt latency and first-completion behavior only in an
   explicitly authorized isolated test; never source an unreviewed local
   secrets override to profile startup.
3. Decide whether Python formatting should use Ruff or Black for the relevant
   projects. Running both consecutively is an observed configuration choice;
   a correction must preserve the intended formatting contract.
4. Explain the daily Neovim lock restoration to the owner and decide whether
   manual runtime plugin updates are expected to persist.
5. Review package/cache size and terminal history separately from CPU cost.
   Do not delete all orphan packages, caches, or terminal state automatically.

Acceptance: narrow proposed changes, first-prompt and representative editor
latency measurements where authorized, and confirmation that completion,
formatting, and plugin reproducibility still work. Repository tests run only
when the implementation stage changes their associated behavior.

## Task D: Stock, Zen, and Power Profiles

Read [the tuning assessment](04-tuning-options.md) before adding a new kernel.
Stock and Zen are already installed, making them the first comparison.

| Scenario | Record | Keep controlled |
| --- | --- | --- |
| Typical interactive session | First prompt, editor open, scrolling/input response | Same project, terminal, plugins, output resolution and refresh |
| Real build or test suite | Wall time, output correctness, CPU/memory/I/O pressure | Same revision, dependencies, cache condition, job count |
| Build plus desktop interaction | Tail latency or repeatable stutter observation, build time | Same foreground/background workload mix |
| Sustained load | Power, temperatures, throttling counters, fan behavior | AC supply, dock, profile, ambient conditions and warm-up |
| Battery and sleep | Discharge over a defined period, wake success, restore behavior | Brightness, radio state, dock state, battery charge range |

Use multiple repetitions and report spread. Do not claim a tail-latency
percentile from a handful of timings. At minimum compare medians and range;
collect enough events before reporting a percentile.

First establish whether the bottleneck is CPU, storage, memory, application
startup, a remote service, or simply display refresh. Then vary one thing.
Do not combine a new kernel, a new scheduler, new repositories, zram, and a
power-profile change in one experiment.

Acceptance: keep a change only if its benefit exceeds run-to-run variation
and its heat, battery, noise, correctness, and recovery costs are acceptable.
Otherwise retain the baseline and close the experiment. No fixed percentage
improvement is promised by this audit.

## Task E: Firmware and Verified Boot

The observed BIOS is Lenovo N3XET65W 1.40 dated 2026-01-27. Secure Boot is
disabled and Setup Mode is enabled. Current firmware availability was not
established. Verify the exact model against Lenovo/LVFS before proposing an
update; do not assume the date alone means the firmware is obsolete.

Design Secure Boot, signing, bootloader/initramfs ownership, recovery, and
hibernation behavior together. Package presence or an enabled firmware toggle
does not prove a verified chain. Do not enroll keys or update firmware as
part of a performance experiment.

Acceptance: a reviewable design with a tested recovery method and explicit
handling of updates and sleep. Handle signing keys outside repository reports.

## Ready-to-Use Prompt for a Second Agent

```text
Perform Task A in docs/audits/2026-09-05-arch-linux/05-follow-up-tasks.md.
Read the existing storage and boot reports and independently challenge their
conclusions. Work read-only: no sudo, host changes, package refresh/install,
sleep transitions, benchmarks, commits, or pushes. Never read credentials,
account state, key files, shell history, or complete process environments.
Use narrowly filtered historical kernel/service evidence and official
documentation. Distinguish the internal Crucial NVMe from the external OWC
Thunderbolt enclosure. Do not assume the enclosure and dock audio share a
root cause. Return confirmed facts, alternative causes, missing evidence,
and the smallest safe next diagnostic. If writing a report is requested,
use English Markdown in this audit directory and preserve existing reports.
```
