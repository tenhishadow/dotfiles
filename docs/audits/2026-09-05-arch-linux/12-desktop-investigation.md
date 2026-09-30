# Desktop Experience Investigation

Read-only inspection on 2026-09-05 of the active Plasma Wayland session,
display modes, compositor, rendering flags, fonts, portals, indexing, and
application resource use. No application was launched, restarted, or closed;
no mode, scale, profile, autostart entry, index, or database was changed.
Window titles, browser profiles, mail databases, document names, and session
content were excluded.

## Conclusions

The desktop already uses hardware rendering, native Wayland infrastructure,
and disabled animation delays. There is no observed runaway indexer, second
compositor, portal conflict, or memory-pressure problem to remove. The most
concrete experience choices are display sharpness versus refresh rate,
checking the laptop panel's remembered non-native mode, and completing the
power-profile integration documented in the boot report.

| ID | Result | Recommendation |
| --- | --- | --- |
| DX-01 | Hardware OpenGL rendering is active; animation duration factor is zero | Keep this working compositor baseline |
| DX-02 | External 4K at 60 Hz and scale 1.7; lower-resolution high-refresh modes available | Compare text sharpness against smoother scrolling deliberately |
| DX-03 | Disabled laptop panel remembers 1920x1080 although native mode is 1920x1200 | Check and prefer native mode when the internal panel is actually used |
| DX-04 | Code-OSS uses Electron 42; no selected rendering override or managed X11 window was observed | No evidence requiring global Ozone or scaling flags |
| DX-05 | Fontconfig and KDE use BGR subpixel geometry; physical panel order was not established | Only revisit if text has colored fringes or differs between panels |
| DX-06 | Baloo and LocalSearch inactive; picom explicitly hidden; KDE and GTK portals coexist normally | Do not remove healthy components to reduce process counts |
| DX-07 | Browser/editor dominate sampled application memory but pressure remains negligible | Tune actual workloads if needed, not the desktop by package count |

## DX-01: Rendering and Effects Are Already Sensible

KWin's live support information reports Wayland operation and active OpenGL
compositing on **Mesa Intel Iris Xe Graphics (RPL-P)**, with OpenGL 4.6 and
Mesa 26.2.1. This is hardware rendering, not llvmpipe or another CPU rasterizer.
KWin reports the driver as Intel even though its generic GPU-class field says
unknown; the latter is not evidence of an unsupported GPU.

`AnimationDurationFactor=0` is already present. Removing more transition
animations therefore is not a newly discovered speed opportunity. KWin's
loaded effect list is ordinary desktop functionality; the query did not show
an active effect at that instant. Loaded code is not proof of continuous GPU
work. The current boot's KWin error-priority log is empty.

There is no basis to force a different compositor backend, disable VSync,
disable GPU power management globally, or add historical KWin debug flags.
The existing VA-API capability check also succeeds; see
[BF-07](08-boot-firmware-power-investigation.md#bf-07-passive-thermals-and-video-capability).

## DX-02 and DX-03: Display Choices Have More Visible Potential

| Output | Active state | Current configuration | Relevant alternative |
| --- | --- | --- | --- |
| External DisplayPort | Enabled | 3840x2160 at 60 Hz; scale 1.7 | Advertises 2560x1440 at approximately 144 and 160 Hz |
| Internal panel | Disabled | Remembers 1920x1080 at about 60 Hz; scale 1 | Preferred native mode is 1920x1200 at about 60 Hz |

At 60 Hz, a display refresh interval is about 16.7 ms; at 160 Hz it is about
6.25 ms. Those are physical refresh intervals, not measured end-to-end input
latencies. The faster advertised mode can improve perceived pointer and
scrolling motion, but reduces rendering resolution and may compromise text
sharpness. No 4K high-refresh mode was advertised on the current connection.
Software flags cannot create an unadvertised bandwidth capability.

For this development workstation, retain 4K if reading dense text is the
priority. A controlled comparison with an advertised 1440p high-refresh mode
is a meaningful optional experience experiment, not a fix for a proven
fault. Do not buy a different cable or dock based only on this observation:
the monitor, port, dock path, and supported mode combination all matter.

Fractional scale 1.7 is not itself a configuration error. Modern Wayland
clients can negotiate fractional scaling; clients with different protocol or
toolkit support can still render differently. Do not globally multiply
`QT_SCALE_FACTOR`, `GDK_SCALE`, and application device-scale flags on top of
the compositor's scale. The inspected shared environment settings contain no
such forced overrides. Electron's recent defaults already favor native
Wayland in Wayland sessions.
[Electron 38 rendering changes](https://www.electronjs.org/docs/latest/breaking-changes#removed-electron_ozone_platform_hint-environment-variable)

The internal panel is not currently displaying anything, so its remembered
1080p mode does not explain current external-monitor quality. When undocked,
native 1920x1200 restores the full panel shape and extra vertical space if the
remembered mode is actually reused. Verifying the visible result requires
using that panel; this audit did not change output state.

## DX-04: Electron and Xwayland Do Not Show a Forced Legacy Path

The inspected Code-OSS main process uses the installed Electron 42 binary.
Rendering-related command arguments were filtered to an allowlist; no forced
X11 Ozone backend, disabled-GPU flag, forced device scale, or selected
Wayland/VA-API override was found among the observed browser/Electron
processes. Full command lines and application arguments were not retained.

The Xwayland root client-list query succeeded and returned no managed client
windows. An Xwayland server process still exists. Its presence alone is not
proof that Brave or Code-OSS is rendering through X11, and an empty window
list is only an observation of this moment. It does not certify every
application's behavior at every launch.

Electron 38 changed its default Ozone platform selection to auto and removed
`ELECTRON_OZONE_PLATFORM_HINT`; on a Wayland session, the documented behavior
is native Wayland. Adding that removed variable to modern Electron would not
be a useful optimization. Keep per-application compatibility exceptions only
when an actual input, rendering, or screen-sharing regression requires one.
[Electron breaking changes](https://www.electronjs.org/docs/latest/breaking-changes)

## DX-05: Fonts Resolve Correctly, With a Specific Geometry Choice

Font matching resolves the generic families to Noto Sans, Noto Sans Mono, and
Noto Serif. The managed Kitty configuration requests Hack Regular at size 10,
and the requested Hack font is installed and resolves correctly. There is no
missing-font fallback to repair in these checks.

KDE sets antialiasing on, slight hinting, and BGR subpixel geometry.
Fontconfig's effective result agrees: antialiasing true, hintstyle 1, rgba 2.
BGR is a pixel-order selection, not a higher-quality setting independent of
the screen. Its correctness depends on physical subpixel layout and rendering
path, which this inspection did not establish.
[Fontconfig property definitions](https://fontconfig.pages.freedesktop.org/fontconfig/fontconfig-user.html)

If text exhibits colored edges, compare the correct panel geometry or
grayscale antialiasing on both displays before changing fonts. A global BGR
preference should not be copied to every future display without that check.
No visible defect is claimed without a visual observation, and no font cache
was rebuilt.

## DX-06: Background Components and Autostart

Baloo indexing is explicitly disabled in `baloofilerc`; its actual service is
`kde-baloo.service`, which is disabled and inactive. LocalSearch is also
inactive. Therefore broad advice to disable desktop indexing would repeat an
existing decision rather than unlock CPU performance. The tradeoff is reduced
desktop file/content search capability; re-enabling it would be a usability
choice with a separate index scope, not a prerequisite for a fast laptop.

Akonadi is active, but its processes and associated MariaDB used 0.0% CPU
in the five-second sample. Its service memory accounting was about 352 MiB.
No mail or calendar database content was read. Whether the user wants PIM
integration determines whether it is useful; there is no observed busy-loop
or database-maintenance problem justifying a stop, purge, or rebuild.

User autostart has six desktop entries. Picom and Remmina are hidden; Kitty,
Brave, Nextcloud, and KeePassXC are eligible startup applications. The user's
hidden `picom.desktop` correctly overrides the same system-wide desktop
filename, and no picom process was observed. There is no simultaneous picom
compositor to remove from this Wayland session.
[Freedesktop autostart precedence](https://specifications.freedesktop.org/autostart/latest/)

KDE's portal selection defaults to the KDE backend, allows KDE/GTK for the
settings interface, and uses the respective dedicated secret and notification
backends. Both `plasma-xdg-desktop-portal-kde.service` and the GTK backend
are active, with the main portal service. Current-boot error-priority logs for
the inspected main/KDE portal units are empty. An appearance-setting query
also succeeds. Multiple backends are supported by the per-interface selection
model; their coexistence is not a service conflict.
[XDG portal selection](https://flatpak.github.io/xdg-desktop-portal/docs/portals.conf.html)

Retain the desktop-supplied portal selection. Removing GTK or a wallet backend
based only on process count risks functionality without a demonstrated
resource benefit. No custom portal override or notification/autostart rewrite
is indicated by the present evidence.

## DX-07: Application Resource Use

A five-second passive CPU sample during the active session gave these
approximate values. Percentages use **one logical CPU as 100%**; the host has
20 logical CPUs. Proportional resident memory was read separately, shortly
afterward, and avoids counting the same shared pages fully in every process.
The samples therefore are not a synchronized benchmark.

| Application group | Sampled CPU | Later proportional resident memory |
| --- | --- | --- |
| Brave | 31.3% of one CPU | About 6.32 GiB across 61 processes |
| Electron processes, including Code-OSS | 11.5% of one CPU | About 1.54 GiB across 16 processes |
| Plasmashell | 0.2% of one CPU | About 391 MiB |
| Nextcloud | 0.0% | About 48 MiB |
| Akonadi control/server | 0.0% | About 21 MiB, excluding associated database |
| Associated MariaDB process | 0.0% | About 114 MiB |

Brave's raw summed RSS was much larger, about 14.8 GiB, because that metric
counts shared mappings repeatedly. It should not be presented as unique RAM
consumed or proof of a leak. Service cgroup memory and process PSS are also
different accounting methods and should not be added together.

The accompanying pressure snapshot had zero CPU and memory pressure averages.
I/O pressure was zero over the shorter windows and 0.06% over five minutes.
This is consistent with a system having substantial headroom. The browser and
editor are the larger user-space consumers, but neither these process counts
nor the short CPU sample proves unnecessary work.

If responsiveness later degrades, browser/task or editor/extension diagnostics
on an intentionally selected workload are more useful than stripping desktop
services. This audit did not inspect tabs, installed-extension state, project
contents, or browsing history to manufacture a recommendation.

## Ownership and Final Assessment

`kdeglobals`, `kwinrc`, `baloofilerc`, `kcminputrc`, and the user fontconfig
file are regular runtime configuration files, not repository symlinks. The
repository search found no declared ownership for those desktop files. Their
values can legitimately be written by KDE's settings UI; that is not evidence
of the dotfiles playbook silently overwriting them.

If selected desktop preferences are later made reproducible, manage only
approved keys with a clear ownership decision. Avoid versioning complete KDE
session files containing machine-specific display state or using whole-file
templates that erase unrelated UI preferences.

The strong parts of this setup are already in place: accelerated Wayland,
working fonts and media-driver capabilities, reduced animation delay,
disabled unwanted indexing, correct autostart suppression, and coherent
portal integration. The actionable desktop changes are selective and small;
no evidence supports replacing Plasma or the distribution to obtain them.
