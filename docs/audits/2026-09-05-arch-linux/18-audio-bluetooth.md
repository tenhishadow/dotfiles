# Bluetooth audio audit

Date: 2026-09-05. Scope: the Bluetooth branch of the workstation audio audit.
This report records observations and recommendations; no audio configuration,
pairing, service, firmware, or device state was changed.

## Assessment

The laptop already uses a modern Bluetooth audio stack. The connected Sony
WH-1000XM4 was actively playing through A2DP with LDAC during inspection.
The necessary codecs and the higher-quality mSBC voice profile are available.
No missing Bluetooth package or conflicting local override was found.

The journals contain reconnection and voice-transport warnings. They justify a
focused investigation if they correspond to audible failures, but do not prove
that the working stack needs replacement or global tuning.

## Current implementation

| Component | Observed state | Assessment |
| --- | --- | --- |
| BlueZ | `bluez`, `bluez-libs`, and `bluez-utils` 5.87-2 | Consistent installed versions |
| PipeWire | `pipewire`, `pipewire-audio`, `pipewire-pulse`, and `pipewire-alsa` 1.6.8-1 | Modern audio server and compatibility layers present |
| Session manager | WirePlumber 0.5.16-1 | Current configuration format and built-in Bluetooth policy available |
| Plasma integration | Bluedevil 6.7.4-1 | Native Bluetooth desktop integration installed |
| Bluetooth daemon | Enabled, running, exit status zero | Standard packaged service; no service drop-ins |
| BlueZ configuration | No active nondefault values in the three inspected `/etc/bluetooth` configuration files | No legacy codec or transport override found |
| PipeWire/WirePlumber overrides | No local configuration files in their inspected system and user configuration directories | Upstream policy is the baseline |
| Audio codec dependencies | `libldac`, `libfreeaptx`, `sbc`, `liblc3`, and `libfdk-aac` installed | No missing AAC or LDAC library |
| Codec modules | SPA modules include LDAC, AAC, SBC, aptX, LC3 and HFP voice codecs | Installed capability exceeds this headset's advertised capability |

ArchWiki describes `pipewire-audio` as the Bluetooth audio implementation and
`pipewire-pulse` as the compatibility server for PulseAudio clients. This host
already has both. Adding BlueALSA, `pulseaudio-bluetooth`, another session
manager, or an external HFP backend has no demonstrated benefit here.
[ArchWiki PipeWire](https://wiki.archlinux.org/title/PipeWire#Bluetooth_devices)
and
[ArchWiki Bluetooth headset](https://wiki.archlinux.org/title/Bluetooth_headset).

## Adapter, firmware and connection

| Item | Observation |
| --- | --- |
| Controller | Intel USB `8087:0033`, `btusb` driver, HCI version field 13 |
| Firmware package | `linux-firmware-intel 20260810-2` |
| Loaded firmware | `intel/ibt-0040-0041.sfi`; initialization and Intel DDC application completed successfully |
| Firmware timestamp | 2026.5 in the current kernel journal |
| Controller capabilities | BR/EDR, LE, secure connections, wide-band speech, CIS central and peripheral |
| Availability | Powered, rfkill unblocked, not discoverable, no discovery in progress |
| Pairing | One paired, bonded, trusted and connected audio headset |
| Power management | `btusb.enable_autosuspend=Y`; USB runtime control `auto`, currently active |
| Protocol override | `bluetooth.disable_ertm=N` |

CIS capability is a useful prerequisite for future LE Audio hardware, not proof
that a particular headset, firmware and profile combination will interoperate.
The current headset exposes classic A2DP/HFP profiles; there is no negotiated
LE Audio stream in this snapshot. Installing an LC3 library does not add a
codec to a remote headset.

There is no demonstrated reason to disable Bluetooth runtime power management
or ERTM globally. Such workarounds should follow a reproducible failure on the
affected device and an isolated comparison.

## Negotiated sound and headset limits

The factory model was identified as Sony WH-1000XM4 without retaining a custom
alias or Bluetooth address.

| Property | Observed value |
| --- | --- |
| Active card profile | `a2dp-sink` |
| Actual sink codec | `ldac` |
| Playback state | `RUNNING`, unmuted |
| PipeWire sink format | Float32, stereo, 48 kHz |
| Available music profiles | LDAC, AAC, SBC and SBC-XQ |
| Available voice profiles | HFP with mSBC or CVSD |
| Profile preference | `bluetooth.profile-preference="quality"` |

The displayed `bluez5.profile=off` device property is not evidence that the
headset is disabled. It describes initial profile selection, which the session
manager overrides. The active card profile and sink codec identify the working
connection. Likewise, a reported zero PulseAudio-compatible latency is not an
end-to-end Bluetooth latency measurement.
[PipeWire property reference](https://docs.pipewire.org/page_man_pipewire-props_7.html).

Sony documents SBC, AAC and LDAC for this model's music playback. Its available
profiles match that specification; absent aptX or LC3 choices are not evidence
of missing Linux codec packages.
[Sony supported codecs](https://helpguide.sony.net/mdr/wh1000xm4/v1/en/contents/TP0002752840.html).

Sony also documents a specific tradeoff: enabling connection to two devices
simultaneously disables LDAC and uses AAC or SBC. If LDAC disappears after a
headset setting change, check this setting before modifying Linux. Its current
value in the companion application was not inspected.
[Sony multipoint connection](https://helpguide.sony.net/mdr/wh1000xm4/v1/en/contents/TP0002935899.html).

## Microphone and profile policy

The current WirePlumber settings are:

| Setting | Current value | Recommendation |
| --- | --- | --- |
| `bluetooth.autoswitch-to-headset-profile` | `true` | Keep automatic headset microphone support unless the user deliberately chooses another microphone workflow |
| `bluetooth.use-persistent-storage` | `true` | Keep normal restoration of headset-mode state |
| `bluetooth.profile-preference` | `"quality"` | Appropriate for the current LDAC music use |
| `device.routes.mute-on-bluetooth-playback-removed` | `false` | Optional preference: prevent playback falling back audibly to speakers after headphones disappear |

WirePlumber switches to HFP when an application records through the headset and
restores the earlier profile after capture ends. Voice mode has lower playback
quality than A2DP. A separately selected laptop or USB microphone permits
keeping high-quality headset playback during a call. Muting on Bluetooth
playback removal is a supported convenience option, not a missing correctness
requirement. These settings were queried in the installed version; none was
changed.
[WirePlumber settings](https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/settings.html).

Upstream Bluetooth policy already enables available codecs, uses a native HFP
backend, applies hardware quirks and respects the active graphical session.
Keep those defaults unless a specific failure establishes a need to override
them. Old PulseAudio module instructions or WirePlumber 0.4 configuration
examples should not be copied into this WirePlumber 0.5 installation.
[WirePlumber Bluetooth configuration](https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/bluetooth.html).

LDAC defaults to adaptive bitrate. Forcing its maximum bitrate or increasing
sample rate would be a quality/reliability experiment, not a demonstrated fix.
No such experiment was performed.
[PipeWire LDAC properties](https://docs.pipewire.org/page_man_pipewire-props_7.html).

## Historical warnings and current observations

The Bluetooth service journal query covered the previous 14 days. Its retained
entries in that window begin on August 26. The following counts describe
warning/error messages, not independently verified audible failures:

| Category | Count | Interpretation |
| --- | ---: | --- |
| Cached A2DP `LastUsed` remote endpoint missing | 52 | Previous endpoint reference could not be restored |
| HFP gateway socket disconnected | 50 | Disconnected transport observed; actual call impact unverified |
| Reconnection returned device/resource busy | 4 | Some automatic reconnect attempts failed |
| HFP service lookup returned host down | 3 | Remote service could not be queried at that time |
| A2DP endpoint in bad state for resume | 2 | Stream transition failed |
| AVDTP Start request unanswered | 1 | Remote endpoint did not answer a start request |
| Other messages withheld during sanitization | 2 | Not used to infer a cause |

BlueZ emits the `LastUsed` warning while restoring cached endpoint references.
The code returns from that restoration step if the reference is unavailable;
the warning alone does not establish failed audio. The current boot contains
one such service warning at 08:30:03 UTC, followed later by the observed
working LDAC connection.
[BlueZ 5.87 endpoint restoration](https://github.com/bluez/bluez/blob/5.87/profiles/audio/a2dp.c#L2233).

The current kernel journal separately contains three voice-transport messages:

| Time, UTC | Message category |
| --- | --- |
| 10:45:38 | SCO packet for an unknown connection handle |
| 10:45:47 | Corrupted SCO packet |
| 11:01:11 | SCO packet for an unknown connection handle |

SCO carries the classic Bluetooth voice path. These messages make a real
HFP call/profile-transition test more useful than speculative music-codec
tuning. This audit did not establish their relation to a call, microphone
switch, remote disconnection or sleep transition. The headset's successful
LDAC playback does not validate its microphone path.

Do not delete pairing data or reset BlueZ merely to silence the cache warning.
No pairing store was inspected, and reconnecting successfully after a reset
would not by itself identify the original cause.

## Prioritized follow-up

| Priority | Action | Evidence needed before configuration changes |
| --- | --- | --- |
| Medium if calls have audible failures | Observe one ordinary call using the headset microphone, followed by microphone release | Correlate HFP/mSBC selection, return to A2DP, audible symptoms and new SCO errors |
| Medium if reconnects fail | Observe headset power-cycle or normal resume during a user-approved test | Distinguish remote disconnect, endpoint negotiation, controller reset and routing failure |
| Optional | Select a separate microphone for calls that need stereo headset playback | Confirm the chosen microphone is usable and call audio remains acceptable |
| Optional | Enable mute on Bluetooth playback removal | Confirm the user prefers silence to speaker fallback |
| No current need | Force codecs, maximum LDAC bitrate, sample rate or global power workarounds | Require a measured benefit on this hardware |

There is no demonstrated urgent Bluetooth configuration repair. The most
useful next measurement is the voice/profile transition that the passive
snapshot could not exercise.

## Sources, method and limits

Evidence came from installed package metadata, service properties, safe
configuration files, sysfs, controller capability queries, selected technical
fields from Bluetooth/PipeWire introspection and categorized journal messages.
Direct ArchWiki page retrieval was blocked by its access protection; indexed
ArchWiki material was cross-checked against accessible upstream WirePlumber,
PipeWire, BlueZ and Sony documentation. No forum workaround was treated as a
general best practice.

No playback, recording, active scan, pairing, profile switch, power transition,
restart, installation or system write was performed. Bluetooth addresses,
custom device aliases, media metadata and raw profile objects were not saved.
The Bluetooth pairing store, link keys and identity keys were not read.

Actual acoustic quality, microphone intelligibility, end-to-end latency,
packet-loss rate, reconnect reliability and headset firmware version remain
unverified. A running output node proves graph activity, not what the user
hears. The findings apply to this observation, not all possible Bluetooth
devices or future sessions.
