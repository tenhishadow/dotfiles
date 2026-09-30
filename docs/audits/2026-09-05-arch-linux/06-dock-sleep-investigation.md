# External storage, dock audio, and sleep investigation

Second read-only investigation on 2026-09-05, completing the evidence review
for Task A. This report refines ST-01, BP-02, and BP-03 in the first pass.
No device was connected, disconnected, opened for audio playback, suspended,
reconfigured, repaired, or updated. No reproduction or benchmark was run.

The later [full audio hardware review](19-audio-hardware-dock.md) adds a
second brief dock-removal event, distinguishes Logitech headset errors, and
documents current duplicate internal audio nodes. Use it with this dated
chronology for the latest audio conclusions.

## Conclusions

The initial external NVMe errors happened **before the kernel entered sleep**.
The dock-audio error count describes **one retry burst after dock removal**,
not hundreds of independent failures or an ongoing current-boot fault.
These distinctions substantially narrow what should be fixed.

| ID | Conclusion | Confidence | Decision |
| --- | --- | --- | --- |
| DS-01 | External NVMe disappeared during active reads, about 3.55 seconds before kernel hibernation entry | High | Investigate disconnect circumstances; do not label this a sleep-induced internal SSD failure |
| DS-02 | Hybrid sleep aborted early with `EBUSY`; ordinary suspend then succeeded | High for outcome; cause unresolved | No justified boot, filesystem, or global power-management workaround |
| DS-03 | All 231 ALSA `front:1` invalid-argument records belong to one post-disconnect burst | High | Focus on stale audio-node handling after removal, not sample-rate tuning |
| DS-04 | Current dock uses a coherent generic ACP audio profile and supported format | High for configuration; playback untested | Preserve current audio policy until a reproducible device-present fault exists |

The remaining uncertainty is physical event attribution and reproduction.
Further static configuration inspection cannot prove whether someone unplugged
a cable, a connector lost contact, an enclosure lost power, or firmware reset
a link. Those questions require owner context or an observed recurrence.

## DS-01: precise external-storage chronology

Times below are UTC on 2026-09-03, from narrowly filtered retained kernel and
sleep-service journals.

| Time | Event |
| --- | --- |
| 09:41:13-14 | OWC Express 1M2 appears on Thunderbolt; its downstream PCIe endpoint becomes `nvme1`, with six discovered partitions |
| 09:56:08.330 | The USB tree associated with the dock begins disconnecting; its Thunderbolt connection also disappears |
| 09:56:11.186 | The OWC Thunderbolt connection disappears |
| 09:56:11.206 | The corresponding PCIe hotplug link goes down |
| 09:56:11.224 | Two NVMe reads are host-aborted; block and buffer layers report read errors |
| 09:56:11.323 | The journal records PowerDevil requesting hybrid sleep through logind |
| 09:56:13.283 | The OWC enclosure reconnects |
| 09:56:14.185-14.377 | Its PCIe link returns, ASPM clock configuration is reconciled, and `nvme1` is enumerated again |
| 09:56:14.777 | The kernel enters the hibernation path |
| 09:56:14.815 | Filesystem synchronization completes |
| 09:56:14.890 | Hibernation exits; systemd reports `Device or resource busy` |
| 09:56:15.091 | Systemd's fallback enters ordinary `s2idle` suspend |
| 09:56:22.428 | The system returns from that suspend |
| 09:56:32.035 | The OWC enclosure disconnects again |

Kernel source-monotonic timestamps independently place the read failure
approximately 3.553 seconds before kernel hibernation entry. The much smaller
gap to logind's request uses journal receipt timestamps across different
producers; it is not needed to establish the stronger kernel-to-kernel order.

Consequently, the subsequent kernel sleep transition did not cause the initial
NVMe link loss. Re-enumeration during sleep preparation might still be related
to the later rejection. Manual unplugging or movement is consistent with the
sequence, but logs cannot distinguish it from a connection or power fault.

The OWC enclosure and Lenovo dock were on different Thunderbolt branches in
that historical configuration. Their nearby disconnect times do not prove
that the NVMe was downstream of the dock or that one device caused both
failures. Current topology cannot reconstruct a historical cable layout:
today the dock is on the branch previously used by the enclosure, and no
external NVMe is present. Device names and branch numbers are not permanent
hardware identities. The
[kernel Thunderbolt documentation](https://docs.kernel.org/admin-guide/thunderbolt.html)
describes the topology and separate USB/DisplayPort/PCIe tunneling model.

## Was the external drive mounted or writing?

The retained kernel query found one error episode: two host-aborted read
commands, two block read errors, and ten related buffer read-error messages.
Those fourteen log records are not fourteen independent drive failures.
There were no matching external-NVMe write errors or filesystem-specific
ext4, Btrfs, XFS, NTFS, exFAT, or FAT messages in the queried retained period.

The active reads prove outstanding block I/O at disconnect. They do not prove
an application had an open file or that a filesystem was mounted: partition
and filesystem probing also performs reads. The errors identify the whole
namespace rather than a mounted partition, which does not identify the caller.

UDisks had no retained service records in the surrounding interval. The
systemd manager query found no corresponding mount/unmount records either.
This absence cannot prove the drive was unmounted; direct/manual mounts and
incomplete journal retention remain possible. No process histories, raw
filesystem contents, or private mount labels were inspected.

Decision: no demonstrated filesystem corruption, write loss, or defective
internal SSD follows from this evidence. Do not run repair, reformat the
external drive, or alter internal NVMe power policy in response to this event.

## DS-02: the sleep failure was early, not an image-write failure

The failed attempt reaches hibernation entry and filesystem synchronization,
then exits about 0.11 seconds after entry. The retained messages contain no
task-freezing or image-writing stage for that attempt. A later attempt at
09:58:18 completed without the same error and returned at 10:00:12, after the
enclosure's last recorded disconnect.

This weakens claims that an undersized resume device, slow encryption, or
internal image-write errors caused this particular failure. It does not
identify the exact source of `EBUSY`. Upstream has multiple rejection paths;
for example, an interrupted filesystem-sync stage can return `EBUSY` when a
wakeup is pending. This is a possible mechanism, not a traced diagnosis of
this installed kernel.
[Kernel sleep synchronization source](https://raw.githubusercontent.com/torvalds/linux/master/kernel/power/main.c)
and [hibernation control flow](https://raw.githubusercontent.com/torvalds/linux/master/kernel/power/hibernate.c)
show why the error string alone is insufficient.

Systemd explicitly attempted ordinary suspend after hybrid sleep failed.
Therefore the eventual successful unit status does not prove that a fallback
disk image existed. This fallback is visible in both the local service log
and [systemd's sleep implementation](https://raw.githubusercontent.com/systemd/systemd/main/src/sleep/sleep.c).
Cold restoration from disk remains a different, untested capability.

No blanket ASPM/APST disablement, forced sleep-state override, increased sleep
delay, or custom pre-sleep device reset is justified. The nearby ASPM message
occurs during re-enumeration after link-up; it does not establish an ASPM bug.

## DS-03: dock-audio errors belong to a disappearance/retry episode

The first-pass seven-day query counted 231 `front:1` open failures. Grouping
them by time and correlating the USB topology produces a more useful account:

| UTC time on 2026-09-04 | Event |
| --- | --- |
| 21:52:33 | Dock Thunderbolt and USB tree disconnect; the USB audio endpoint disappears |
| 21:53:34-21:55:34 | Twenty-five dock-node start-error transitions recur approximately every five seconds |
| 21:53-21:55 | All 231 `front:1` invalid-argument records occur in this interval |
| 21:55:37 | WirePlumber and PipeWire stop during session/system shutdown |
| 21:56:18 onward | A new boot begins; no matching current-boot retry burst is present |

Adjacent messages report unknown ALSA PCM/parameters and WirePlumber being
unable to find the ALSA device for the dock node. There is no dock reconnect
between disappearance and the retry burst ending. This strongly supports
attempts to restart a stale/disappeared audio endpoint. The exact reason its
node remained eligible for retries is unverified.

One separate dock-node `No such file or directory` start error exists on
2026-09-03. It should not be merged with the later invalid-argument burst as
if they shared one reproduced cause.

The USB ALSA `front` definition resolves a card and PCM device; failure to
resolve that route is different from proving that a valid device rejected
its sample rate. The installed definition matches the mechanism in
[ALSA's USB-audio configuration](https://raw.githubusercontent.com/alsa-project/alsa-lib/master/src/conf/cards/USB-Audio.conf).

Decision: investigate object removal, route restoration, and pending streams
if the problem recurs. Do not infer a persistent dock-format bug from this
post-disconnect episode, and do not represent 231 retry messages as 231
independent user-visible outages.

## DS-04: current audio configuration is internally consistent

Only selected hardware/card properties were read. No application stream
contents, recording, media title, account state, or saved user profile was
exported.

| Property | Current observation | Interpretation |
| --- | --- | --- |
| Dock audio device | Lenovo USB audio, product class `17ef:30bb`, `snd_usb_audio` | Separate USB endpoint from the external NVMe enclosure |
| Profile mechanism | ACP enabled; generic analog/digital/pro-audio profiles offered | Generic ACP is active; no matching dedicated dock UCM entry found |
| Selected profile | Analog stereo output plus mono input | Matches the device's playback/capture channel capabilities |
| Output PCM | `front:1`, stereo, 48 kHz, 24-bit | The USB descriptor advertises a compatible stereo 48 kHz/24-bit mode |
| Current stream status | Suspended/stopped while unused | Not evidence of playback failure |
| Input route | Microphone currently unavailable | Consistent with no attached input; not proof of an output fault |
| USB runtime power | `control=on`, `runtime_status=active` | No current audio-device autosuspend policy to disable |
| ACP automatic selection | `api.acp.auto-profile=false`, `api.acp.auto-port=false` | Expected with WirePlumber owning profile/route selection |
| Local configuration | No user ALSA overrides or local WirePlumber rules; no PipeWire `.conf` files under `/etc/pipewire` | No inspected local format/profile override explains the old burst |

The apparent custom ACP file `9999-custom.conf` is a package-owned empty
example, not an active private tuning file. No dedicated Lenovo dock mapping
was found in the inspected installed UCM and ACP rules.

UCM preference defaults on when a matching configuration exists; missing
explicit `api.alsa.use-ucm` is not evidence that someone disabled it. Likewise,
ACP's own auto-selection is normally disabled because WirePlumber performs
that policy. These semantics are documented in
[WirePlumber's ALSA configuration guide](https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/alsa.html).

Do not add forced S16/48 kHz, disable UCM globally, switch every device to
Pro Audio, or disable PipeWire node suspension from this evidence. Setting
node suspension timeout to zero keeps ALSA devices open and changes resource
and power behavior; it does not restore physically missing hardware.

## Completed decisions and remaining physical evidence

The read-only investigation has answered the questions available from current
metadata and retained logs:

- The affected NVMe was external, and its initial failure preceded actual
  kernel sleep entry.
- Outstanding reads are confirmed; mount state, writes, and data loss are not.
- Hybrid sleep failed early and systemd fell back to ordinary suspend.
- The dock-audio count came from a single retry burst after disappearance.
- The currently selected audio profile, format, and ownership show no
  demonstrated configuration conflict.
- No device-specific configuration patch is supported strongly enough to
  propose as an established fix.

The parallel [firmware investigation](08-boot-firmware-power-investigation.md)
confirms dock release 10.20 against installed aggregate firmware 10.19,
using cached device matching and retrieved upstream metadata. Its published
fixes concern monitor detection after restart and wake after prolonged
closed-lid sleep. This is a maintenance candidate, not proof of a fix for
OWC disconnects or stale audio nodes; use that investigation's component
matching and source checks.

The smallest useful physical observation would be a normal owner-initiated
dock removal/reconnect, with the external drive safely quiesced, while checking
whether the removed audio device and node disappear together. An enclosure
connection that drops while untouched would justify cable/port/enclosure
isolation before kernel tuning. A stable connection followed by a reproducible
hybrid-sleep rejection would instead justify focused sleep/wakeup tracing.
These outcomes cannot be supplied by more static reads and were not induced
in this session.

Evidence is limited by retained journal coverage. Queries selected kernel,
sleep, UDisks, system-manager mount events, and audio-service records; they
did not copy complete journals or inspect personal filesystem contents.
Current metadata was sampled without starting audio playback or recording.
