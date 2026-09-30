# Audio Stack Review

Read-only follow-up on 2026-09-05. This report combines live PipeWire and
desktop inspection with independent Bluetooth and hardware reviews. See
[Bluetooth and headset details](18-audio-bluetooth.md) and
[ALSA, SOF, dock, and display audio](19-audio-hardware-dock.md).

## Verdict and Priorities

The workstation already uses a modern, coherent audio stack. No missing
core component, competing active sound server, or failed real-time scheduling
was found. Wholesale configuration replacement is unwarranted. The most useful
work is to investigate duplicate hardware endpoints, test device transitions,
and make the selected audio packages reproducible in Ansible.

| Priority | Finding | Recommended next step |
| --- | --- | --- |
| First diagnostic task | Five pairs of identical SOF HDMI/microphone endpoints exist in the current PipeWire graph | Compare a fresh audio session with the current graph, then observe dock, jack, and sleep transitions; cause and audible impact remain unproven |
| Reliability follow-up | Dock errors follow USB disappearance; historical Bluetooth voice transport also has warnings | Reproduce removal/return and an actual headset call with synchronized, sanitized observations |
| Reproducibility | The package manifest does not explicitly select the working audio stack | Declare the chosen packages and service ownership in the privileged system layer after review |
| Optional integration | JACK2 libraries are installed; PipeWire's JACK provider is absent | Decide whether installed music applications should join the PipeWire graph or retain a dedicated JACK workflow |
| Optional experience | Headset microphone use switches music playback to a voice profile | Select a laptop or USB microphone while retaining LDAC output when stereo quality matters |

No critical, persistent audio failure was established by this inspection.
That conclusion does not certify microphone quality, speaker sound, or
reliability across untested hardware transitions.

The earlier missing TuneD/Plasma bridge has already been addressed in
[the separately authorized integration](15-tuned-plasma-integration.md).
It is not a remaining audio defect.

## Stack and Ownership

| Layer | Installed or observed state | Assessment |
| --- | --- | --- |
| Engine | PipeWire, audio, ALSA bridge, and PulseAudio bridge: `1:1.6.8-1` | One multimedia engine serves the native, ALSA-default, and PulseAudio client paths |
| Session policy | WirePlumber `0.5.16-1`; one process and one enabled service | Owns hardware profiles, routing, and Bluetooth integration |
| Hardware userspace | ALSA library/UCM `1.2.16.1-1`; utilities `1.2.16-1`; SOF firmware `2025.12.2-1` | Required laptop and USB audio components are present |
| Bluetooth | BlueZ `5.87-2`, codec libraries, Intel firmware | Connected Sony WH-1000XM4 uses A2DP LDAC |
| Plasma controls | `plasma-pa 6.7.4-1`, `bluedevil 1:6.7.4-1`; pavucontrol installed | Compatible controls for the current sound and Bluetooth services |
| JACK clients | `jack2 1.9.22-2`; no running `jackd` or `jackdbus` | Optional client integration remains separate from PipeWire |
| Effects | EasyEffects `8.2.9-1` installed; no running process or observed effects graph | Installation alone does not apply equalization or microphone processing |

The normal paths are:

| Application interface | Path to output or capture |
| --- | --- |
| Native PipeWire | PipeWire, then ALSA/SOF/USB or BlueZ |
| PulseAudio client | `pipewire-pulse`, then PipeWire and the selected device |
| ALSA `default` device | Packaged PipeWire ALSA plugin, then PipeWire |
| Explicit ALSA `hw:` device | Direct hardware access; application-specific selection can bypass desktop mixing |
| JACK client | Currently JACK2 client libraries; PipeWire JACK compatibility is not installed |

This matches the architecture described in [ArchWiki's PipeWire article](https://wiki.archlinux.org/title/PipeWire).
ALSA remains the kernel/hardware foundation; its presence alongside PipeWire
is expected. Likewise, `pactl` and Plasma's PulseAudio interface remain useful
with the compatibility server. `pactl info` explicitly identifies
`PulseAudio (on PipeWire 1.6.8)`; its separate `15.0.0` compatibility version
does not identify an old native PulseAudio daemon.

Both PipeWire sockets are enabled and active. Their corresponding service
units are running but reported as disabled, which is normal socket
activation. WirePlumber is enabled and running. All three services have zero
automatic restarts and successful status in the current boot. No native
PulseAudio server or second session manager was observed.

## Configuration, Routing, and Current Anomaly

No local PipeWire or WirePlumber configuration fragments were found in the
inspected standard user and system paths. There is no user `.asoundrc` or
system `asound.conf`; packaged ALSA fragments route the default PCM and
control interface to PipeWire. Package integrity checks reported zero altered
files for PipeWire, its audio/ALSA/Pulse bridges, WirePlumber, and ALSA UCM.

Future changes should use small supported configuration fragments. Existing
WirePlumber 0.4 Lua examples should not be copied into this 0.5 installation;
the supported configuration model changed. See the upstream
[WirePlumber migration guide](https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/migration.html).

Runtime settings were inspected as well as configuration files: saved
WirePlumber settings can override file defaults. Route/profile restoration,
default-device restoration, moving streams, and Bluetooth headset autoswitch
are enabled. Those are useful ordinary desktop policies; disabling them
globally would not resolve a confirmed cause here. See
[WirePlumber settings and persistence](https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/settings.html).

The selected output is the connected LDAC headset. The saved preferred input
is currently unavailable, and the effective input falls back to the internal
digital microphone. An unavailable saved preference is not itself a fault.
However, the effective microphone name matches two current graph objects.

Two independent inspections found these duplicate pairs on the same SOF
device and the same WirePlumber client:

| Endpoint | Snapshot node IDs | Matching properties |
| --- | --- | --- |
| HDMI 3 | `50`, `102` | Device, client, object path, node name, PCM, channels |
| HDMI 2 | `51`, `103` | Same identity fields |
| HDMI 1 | `52`, `104` | Same identity fields |
| Analog microphone | `54`, `101` | Same identity fields |
| Digital microphone | `55`, `110` | Same identity fields; saved volume values differ |

IDs are temporary diagnostic observations, not stable identifiers suitable
for configuration. These are hardware nodes, not the normal monitor sources
associated with playback sinks. No SplitPCM properties were present, and the
inspected stock SOF/HDA UCM definitions do not declare SplitPCM. The separate
speaker and headphone routes are legitimate and are excluded from this count.

Stale objects after profile or device re-enumeration are a hypothesis. The
snapshot does not establish the creating event, responsible component, or an
upstream fix. A controlled session restart or fresh login would show whether
duplicates exist immediately or accumulate after later transitions, helping
narrow the cause. It was not performed because it would interrupt live audio.
Deleting all saved WirePlumber state,
disabling UCM, or hiding HDMI nodes would be premature.

## Performance and Latency

| Measurement | Observation | Meaning |
| --- | --- | --- |
| Graph clock | 48 kHz; allowed rates `[48000]` | Conventional desktop operating rate |
| Quantum | 1,024 frames; minimum 32, maximum 2,048; no forced rate/quantum | Current graph period is about 21.3 ms; this is not total Bluetooth latency |
| Scheduling | Audio data threads use round-robin real-time scheduling at priority 20 | Actual scheduling works despite low ordinary process resource limits |
| RT helper | RTKit is active and running | No need to add the user to privileged audio/realtime groups to repair an absent problem |
| Memory | About 27/26/32 MiB RSS for PipeWire/Pulse bridge/WirePlumber | No large persistent engine footprint in this snapshot |
| Passive playback sample | LDAC output running; `pw-top` sampled with six refreshes; error counter remained zero | No error observed during this short existing playback interval |

The ALSA hardware nodes were idle during that sample, so it does not test
speakers, dock playback, display audio, or microphone capture. It also does
not measure physical round-trip latency or sustained behavior under a build.

PipeWire supports real-time scheduling through resource limits or its
portal/RTKit fallback. Actual thread scheduling is stronger evidence here than
`ulimit -r` alone. Arbitrary priority 99, unlimited resource privileges, CPU
pinning, and a real-time kernel are not justified by these observations.
See the [PipeWire real-time module](https://pipewire.pages.freedesktop.org/pipewire/page_module_rt.html).

Keep the current graph defaults. A globally forced tiny buffer increases
scheduling demands; 96/192 kHz does not establish better output from this
headset or dock. If a DAW or software instrument needs lower wired latency,
measure that particular application and device with a smaller quantum before
changing the desktop-wide policy. PipeWire documents clock, quantum, and
configuration-fragment controls in its [configuration manual](https://pipewire.pages.freedesktop.org/pipewire/page_man_pipewire_conf_5.html).

Bluetooth transport and headset buffering remain separate latency sources.
LDAC quality settings should be evaluated for radio reliability rather than
treated as a general low-latency switch. See the
[headset-specific assessment](18-audio-bluetooth.md).

## Hardware, Dock, Bluetooth, and Power

The internal controller uses automatic SOF selection with valid firmware and
UCM. The dock uses the standard USB audio driver; its stereo output/mono input
profile matches its capabilities. DisplayPort advertises a valid stereo PCM
path. Required firmware is present; a loaded SOF firmware version of 2.2 is
not evidence that the newer multi-platform package failed to install.
The [hardware report](19-audio-hardware-dock.md) explains the versioning and
HDMI topology warning with upstream source references.

Historical errors are more specific than a general broken-dock conclusion:

- September 4: 231 invalid-argument messages and 25 node-start errors form
  one retry episode after the USB/dock device disappeared.
- September 3: another dock open/start error follows USB removal by about
  44 ms. Separate Logitech PRO X USB headset errors must not be counted as
  Lenovo dock failures.
- No matching dock open/start burst was found in the current boot.
- Bluetooth history includes reconnection warnings and current-boot SCO
  voice-packet warnings. Their relationship to audible call failures is
  unverified; current LDAC playback works.

Device disappearance could mean deliberate unplugging, a link/power problem,
or another event. Logs alone do not distinguish those causes. The next useful
test is removal/return and routing recovery, not a global sample-format change.

TuneD's balanced profile sets the observed HDA power-saving timeout to ten
seconds. The dock audio USB device is already configured with runtime power
control `on`, so disabling its autosuspend would not change this state.
The internal controller suspends while idle. Retain those settings unless
repeatable pops or wake delays justify a device-specific comparison; kernel
documentation describes ten seconds as a reasonable normal value in
[HDA power saving](https://docs.kernel.org/sound/designs/powersave.html).

## Optional Improvements and Ansible Ownership

The repository's package list contains media applications, but does not
explicitly list PipeWire, WirePlumber, the ALSA/Pulse bridges, BlueZ, SOF/UCM,
or Plasma's audio/Bluetooth controls. Dependencies account for part of the
installed stack; `pipewire-alsa` is explicitly installed locally. This is a
reproducibility gap, not proof that a current dependency is broken.

For a later authorized change, declare the chosen baseline packages in the
existing privileged system role and document service ownership. Do not copy
runtime device IDs, Bluetooth addresses, pairing state, or volume databases
into Ansible. Defaults that already work do not need generated replacement
configuration files.

The JACK decision should be separate. Installed JACK2 currently satisfies JACK
dependencies of numerous applications and libraries, including Ardour,
QjackCtl, FFmpeg, and OBS. It is
not currently running a competing server. If the intended workflow is one
desktop audio graph, Arch's `pipewire-jack` provides the JACK client ABI and
conflicts with `jack2`; switching is a reviewed provider transaction, not
blanket removal of JACK-dependent applications. Verify real music workloads
first if a dedicated JACK server is intentional. See the
[official package metadata](https://archlinux.org/packages/extra/x86_64/pipewire-jack/).

Other improvements depend on use:

- For calls with high-quality stereo output, choose the laptop or USB
  microphone while retaining LDAC playback. The WH-1000XM4's own microphone
  requires the lower-bandwidth Bluetooth voice profile.
- Consider WirePlumber's supported mute-on-device-removal preference if
  unexpected fallback to speakers is undesirable; it is currently disabled.
- Add echo cancellation only for a reproduced speakerphone echo problem,
  accounting for processing already performed by the calling application.
- EasyEffects equalization is an optional listening preference. An installed
  effects application is not evidence that an EQ preset is active or needed.
- Add 32-bit compatibility libraries only for actual 32-bit clients that
  require them; their absence does not invalidate the native desktop stack.

The inspected audio processes had Unix listeners and no observed IP listeners.
No network-audio module or extra processing chain was found in the graph.
This is a bounded audio exposure check, not a full application sandbox or
microphone-consent audit.

## Next Operational Checks

These checks were not executed. They require deliberate playback, capture,
device changes, or session interruption and should be performed when the
workstation is not in a call.

| Scenario | Pass condition |
| --- | --- |
| Fresh audio session | No identical duplicate hardware nodes; one unambiguous effective microphone |
| Internal speakers, wired jack, and DMIC | Correct channels, usable capture, predictable mute and jack switching |
| Dock output and microphone | Supported profile works; capture availability matches physical connections |
| Dock removal and return | Streams recover or fall back predictably; retries stop; no accumulating duplicate nodes |
| DisplayPort audio | Selected monitor plays correctly and returns after ordinary reconnection |
| Bluetooth music and call | LDAC playback is stable; HFP microphone works; stereo profile returns after the call |
| Suspend/hibernate and return | SOF, USB, and Bluetooth paths recover with valid default routing |
| AC/battery and CPU/I/O load | No audible glitches or growing error counters in the intended workload |
| Optional JACK application | Application reaches the intended server and device with measured acceptable latency |

Use one changed condition at a time and compare sanitized node identity,
profile/route state, and timestamped error categories. Avoid recording audio,
application media titles, or raw device identifiers in the repository.

## Evidence and Limits

Inspection used installed package metadata and selected package integrity
checks, standard audio configuration paths, service properties, sanitized
PipeWire/PulseAudio metadata, thread scheduling, USB/PCI power state, and
categorized retained journals. Only a short interval of existing playback
was passively observed. No playback or capture was initiated; no pairing,
active scan, restart, profile change, package operation, or system edit was
performed during this follow-up.

Bluetooth keys, custom device names, MAC addresses, serials, private account
state, media titles, full process environments, and audio content were excluded
from report output. No raw runtime dump was saved.

Direct full-page ArchWiki access was blocked by automated-traffic protection.
Indexed ArchWiki excerpts were cross-checked against accessible upstream
PipeWire, WirePlumber, kernel, BlueZ, SOF, Sony, and Arch package documentation.
Recommendations were compared with the installed versions and effective
runtime values; unresolved causality remains explicitly unresolved.
