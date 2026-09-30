# Audio Hardware, Dock, and Sleep Review

Read-only inspection on 2026-09-05 of the ThinkPad X1 Carbon Gen 11 audio
controller, ALSA drivers, SOF firmware, UCM configuration, USB dock, display
audio, power settings, and retained audio-related logs. This report refines
the audio findings in [the dock and sleep investigation](06-dock-sleep-investigation.md).
The [complete audio review](17-audio-stack-review.md) owns the combined
priorities and user-space conclusions.

## Conclusions

The hardware stack uses appropriate automatically selected drivers, packaged
firmware, and ordinary UCM or ACP profiles. No evidence supports replacing
SOF, forcing legacy HDA, or applying global power and sample-rate workarounds.
However, the current PipeWire graph contains duplicate internal audio nodes;
this is a concrete inconsistency to investigate before declaring the entire
audio setup clean.

| ID | Finding | Confidence and decision |
| --- | --- | --- |
| AH-01 | SOF, ALC287, digital microphones, and display audio are detected coherently | High for configuration; preserve automatic selection |
| AH-02 | Five pairs of internal audio nodes represent identical logical endpoints | High for duplication; cause and audible impact remain unproven |
| AH-03 | Both identified dock error episodes follow disappearance of its USB audio endpoint | High for chronology; investigate removal and route restoration |
| AH-04 | Internal audio power saving matches TuneD; dock audio USB autosuspend is disabled | High for snapshot; no global power workaround justified |
| AH-05 | One SOF fast-restore warning and one unmapped HDMI converter do not establish a persistent hardware failure | High for message semantics; retain as conditional follow-up evidence |

The absence of current playback errors does not establish that every output,
microphone, physical jack, or sleep transition works. Listening, recording,
route switching, and reproduction were outside this read-only inspection.

## AH-01: Hardware and Firmware Baseline

| Component | Observation |
| --- | --- |
| Internal controller | Intel Raptor Lake audio, PCI ID `8086:51ca`, Lenovo subsystem `17aa:2315` |
| Active driver | `sof-audio-pci-intel-tgl`, with `snd_intel_dspcfg.dsp_driver=0` |
| Analog codec | Realtek ALC287 |
| Display codec | Intel Raptor Lake P HDMI, bound to i915 |
| Firmware package | `sof-firmware 2025.12.2-1` |
| Loaded DSP firmware | SOF `2:2:0-57864`, using IPC3 |
| Topology | `sof-hda-generic-4ch.tplg`; firmware tables report four digital microphones |
| ALSA userspace | `alsa-lib` and `alsa-ucm-conf 1.2.16.1-1`; `alsa-utils 1.2.16-1`; topology package installed |
| Dock audio | Lenovo USB ID `17ef:30bb`, handled by `snd_usb_audio` |

The kernel detects the digital microphones and selects SOF automatically.
The required firmware and topology files exist and belong to the installed
SOF package. The Raptor Lake firmware path resolves to the package's
Intel-signed Alder Lake binary; this is a packaged platform mapping, not a
locally substituted file. No active audio-driver overrides were found in the
inspected `/etc/modprobe.d` and modules-load configuration.

The loaded firmware's `2.2` version does not mean that the package update
failed. SOF bundles platform-specific firmware branches: Raptor Lake supports
the established IPC3 path alongside newer IPC4 firmware. The inspected
2025.12.2 release includes both families. Forcing IPC4 is not a necessary
modernization step for this working hardware configuration.
[SOF firmware paths and platform conventions](https://github.com/thesofproject/sof-docs/blob/master/getting_started/intel_debug/introduction.rst),
[SOF binary releases](https://github.com/thesofproject/sof-bin/releases).

The log reports firmware/topology ABI `3.22.1` and kernel ABI `3.23.1`.
SOF explicitly permits compatible minor and patch version differences; this
pair alone is not evidence of a broken ABI.
[SOF IPC ABI compatibility rules](https://thesofproject.github.io/latest/api/uapi.html).

The `4ch` topology describes the detected microphone-array configuration.
It is not a reason to force four-channel speaker playback. The internal
UCM configuration exposes separate speaker, headphone, analog-microphone,
digital-microphone, and HDMI endpoints. These are normal logical routes over
the available hardware.

The ArchWiki device page lists audio and Bluetooth as working and refers
readers to the preceding model for shared configuration. That compatibility
summary is contextual evidence, not validation of every local endpoint.
The indexed page was available; its direct response was blocked by Anubis.
[ArchWiki: ThinkPad X1 Carbon Gen 11](https://wiki.archlinux.org/title/Lenovo_ThinkPad_X1_Carbon_%28Gen_11%29).

## AH-02: Duplicate Internal Audio Nodes

Two independent filtered graph inspections found the same duplicate pairs on
2026-09-05. The numbers below are temporary PipeWire object IDs, not stable
identifiers to put in configuration.

| Logical endpoint | Observed object IDs | Shared ALSA PCM |
| --- | --- | --- |
| HDMI / DisplayPort 3 | `50`, `102` | `hw:sofhdadsp,5` |
| HDMI / DisplayPort 2 | `51`, `103` | `hw:sofhdadsp,4` |
| HDMI / DisplayPort 1 | `52`, `104` | `hw:sofhdadsp,3` |
| Analog microphone | `54`, `101` | `hw:sofhdadsp` |
| Digital microphone array | `55`, `110` | `hw:sofhdadsp,6` |

Each pair has the same node name, object path, card association, owning
client, profile name, PCM, and channel layout. The HDMI 2, HDMI 3, and analog
microphone pairs differ only in their object IDs and object serials. HDMI 1
also differs by its PCM-codec property; the digital microphone pair carries
different volume values. All were suspended during inspection.

The parallel user-space review also found that the effective default input
name resolves to both digital-microphone nodes. A remembered preferred input
being absent can legitimately cause fallback to the internal microphone;
having two objects for the same chosen name is the separate inconsistency.

The inspected nodes do not carry SplitPCM properties, and the selected stock
SOF/HDA UCM files do not define a split PCM. Ordinary UCM endpoint splitting
does not explain these identical pairs. PipeWire documents explicit metadata
for UCM split PCMs.
[PipeWire ALSA split properties](https://docs.pipewire.org/spa_2include_2spa_2utils_2keys_8h.html).

The speaker and headphone nodes are different logical routes and are not
counted as duplicates merely because they share an ALSA PCM. Multiple
microphone channels likewise do not explain duplicate four-channel nodes
with the same name.

This graph snapshot supports investigating device and node lifecycle handling.
It does not establish which component created the duplicates, whether sleep
or jack changes triggered them, or whether they caused an audible problem.
No stream, service restart, profile change, or state deletion was used to
test the hypothesis.

## AH-03: Dock and Other USB Audio Events

The currently attached dock provides standard USB audio at full speed.
Its descriptors include stereo 16-bit and 24-bit playback at 44.1 and 48 kHz,
and mono 16-bit capture including 48 kHz. The selected stereo-output plus
mono-input ACP profile is consistent with those capabilities. Full-speed
USB is not itself a throughput problem for this stereo PCM endpoint.

The dock has no matching dedicated UCM configuration in the inspected
installation. Its generic ACP profile is therefore a reasonable active path.
WirePlumber uses UCM when a suitable configuration exists and otherwise can
use ACP; enabling ACP does not require enabling its separate automatic
profile-selection policy when WirePlumber owns selection.
[WirePlumber ALSA configuration](https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/alsa.html).

### Retained Error Chronology

The query covered retained kernel and user audio-unit records from
2026-08-29 onward. Times below are UTC. Counts refer to log records or node
transitions, not independent audible outages.

| Time | Observation | Interpretation |
| --- | --- | --- |
| September 3, 08:18:44-08:18:55 | A Logitech PRO X USB node reports missing `front:2` PCM and retries | Separate USB headset event, not Lenovo dock audio |
| September 3, 09:56:22-09:56:25 | The same headset node has 18 invalid-argument open-error records around return from suspend | Do not attribute these records to the dock or infer an unsupported sample rate |
| September 3, 10:00:29.991 | Dock USB audio endpoint disconnects | Hardware endpoint disappears |
| September 3, 10:00:30.035 | Dock `front:1` node reports a missing PCM and one start-error transition | Error follows disappearance by about 44 milliseconds |
| September 3, 19:58:45 | One browser-input underrun appears in the PulseAudio compatibility service | Isolated stream underrun; no persistent hardware xrun pattern established |
| September 4, 21:52:33 | Dock and its USB audio endpoint disappear | Start of the previously investigated removal episode |
| September 4, 21:53:34-21:55:34 | Twenty-five dock start-error transitions recur; 231 `front:1` invalid-argument records fall within the burst | Repeated attempts against disappeared hardware, not 231 independent faults |
| September 4, 21:55:37 | User audio services stop during shutdown | End of that retry episode |
| Current boot | No matching front-open, start-error, or underrun recurrence was found | Does not prove every idle endpoint is functional |

The earlier report's 231-record count remains correct for the dock burst.
The broader audio review adds the separate Logitech category; these records
must not be merged into that dock count. Both identified Lenovo dock errors
follow USB endpoint disappearance. The logs do not prove whether either
disappearance resulted from intentional unplugging, a cable or power problem,
or firmware behavior.

An unresolved ALSA `front` route after removal is distinct from an existing
device rejecting a valid stream format. Therefore forcing 16-bit audio,
changing every sample rate, disabling UCM globally, or selecting Pro Audio
does not follow from these records.
[ALSA USB audio PCM definitions](https://github.com/alsa-project/alsa-lib/blob/master/src/conf/cards/USB-Audio.conf).

The prior firmware investigation matched dock firmware 10.20 against the
installed aggregate 10.19. Its published fixes concerned display detection
and wake behavior. Retain that as maintenance work; it is not a proven fix
for these audio-node retries or duplicates. No firmware update was performed
or newly authorized by this audio review.
[Firmware evidence and release matching](08-boot-firmware-power-investigation.md).

## AH-04: Power Management Is Internally Consistent

| Layer | Current observation | Decision |
| --- | --- | --- |
| TuneD | Active profile `balanced`; packaged audio timeout is 10 seconds | Matches current policy |
| HDA codec | `power_save=10`, `power_save_controller=Y` | Preserve without a reproduced pop or wake-delay problem |
| Internal audio PCI function | Runtime control `auto`; observed suspended while idle | Expected idle power saving |
| Dock audio USB function | Runtime control `on`; active | Audio-device autosuspend is already disabled |
| Dock USB2 hubs | Active during inspection | No observed suspended ancestor blocking the audio endpoint |
| Idle SuperSpeed hub functions | Some suspended independently | Their state alone does not establish USB audio failure |

The kernel documentation describes automatic codec power saving as useful
for laptops and gives ten seconds as a reasonable normal-operation timeout.
It also identifies audible pops or increased wake latency as reasons for
targeted investigation.
[Kernel audio power-saving guidance](https://docs.kernel.org/sound/designs/powersave.html).

The historical audio episodes precede the TuneD/Plasma integration completed
in this repository. No evidence connects that integration to the old errors.
The actual profile and module value agree; no additional competing audio
power override was identified.
[TuneD integration record](15-tuned-plasma-integration.md).

Disabling all USB, HDA, or PipeWire suspension would change battery and idle
behavior without restoring removed hardware. If normal use reveals a
repeatable pop or delayed start, isolate the affected device and compare one
power setting at a time instead of applying several global workarounds.
[ArchWiki ALSA troubleshooting](https://wiki.archlinux.org/title/Advanced_Linux_Sound_Architecture/Troubleshooting).

## AH-05: SOF Resume and Display-Audio Warnings

On September 3 at 10:00:12.297 UTC, SOF reported that its IMR restore failed
and it was trying a cold boot. Hibernation exited at 10:00:12.456. The selected
retained context contains no subsequent DSP initialization-failure message.
The upstream loader explicitly falls back from the fast IMR path to loading
and booting the firmware. Here, cold boot means restarting the audio DSP,
not rebooting the laptop. This is a real fallback event, not proof of a
permanently failed audio controller; successful audible playback after that
event was not verified.
[Kernel SOF firmware fallback](https://github.com/torvalds/linux/blob/master/sound/soc/sof/intel/hda-loader.c).

The current boot also reports no PCM in the topology for HDMI converter 3.
The converter index is zero-based: the warning concerns a fourth converter,
while the observed topology exposes three HDMI playback PCMs. Upstream
mapping code marks an unmatched converter invalid and continues with the
available controls. This warning does not establish that all display audio
is broken.
[Kernel HDMI PCM mapping](https://github.com/torvalds/linux/blob/master/sound/soc/intel/boards/hda_dsp_common.c).

The currently connected DisplayPort monitor provides valid ELD information:
stereo LPCM, 32/44.1/48 kHz, and 16/20/24-bit capability. This establishes
detected sink capability, not a successful listening test. If one particular
physical HDMI or dock DisplayPort route is silent, compare that route's ELD,
available PCM, selected UCM endpoint, and active graph before altering the
firmware topology.

## Follow-Up Matrix and Inspection Limits

These are proposed owner-assisted checks. None was performed in this audit.
They require temporary playback, recording, route changes, reconnects, or
sleep beyond the authorized read-only scope.

| Scenario | Evidence to collect | Success criterion |
| --- | --- | --- |
| Fresh user audio session | Filtered card/node identities and default-device resolution | One object per logical endpoint; default input resolves unambiguously |
| Internal speakers and headphone jack | Deliberate low-volume output and plug/unplug observation | Correct route, channel balance, mute behavior, and return to speakers |
| Internal microphone and headset microphone | Consensual short local recording without retaining personal audio | Correct input and mute indicator; no unintended input switching |
| Dock output and optional analog microphone | Selected profile, available route, and deliberate local test | Supported stereo playback and intended microphone path |
| Normal dock removal and reconnect | Device/node disappearance, fallback, recreation, and filtered errors | Removed nodes disappear; desired devices return without duplicate objects or repeated retries |
| DisplayPort and physical HDMI audio | Active monitor ELD, selected endpoint, and deliberate listening test | Intended display receives audio at an advertised format |
| Owner-initiated sleep and resume | Before/after node counts, selected route, and narrow SOF/USB logs | Routes recover without duplicate growth or persistent DSP/node errors |
| Normal call plus music transition | Output/input profile and perceived quality | Intended microphone works and output returns to the preferred listening profile |

External storage should be safely quiesced before an owner-initiated dock
removal. Bluetooth-specific profile and codec findings belong to the
[Bluetooth review](18-audio-bluetooth.md).

Evidence collection used filtered device metadata, selected public package
configuration, and narrowly selected log messages. Full journals, hardware
serials, Bluetooth keys, private device aliases, media titles, stream content,
and account state were not stored in this report. No audio playback,
recording, service restart, profile switch, suspend, firmware update, or
system configuration change was performed.
