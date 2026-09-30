# Networking, services, and resource boundaries

Read-only investigation on 2026-09-05, extending the audit beyond storage.
The snapshot covers active network devices, selected resolver settings,
sanitized route and socket metadata, effective firewall chain policies,
service accounting, cgroup limits, and narrowly classified retained logs.
Connection profiles, Wi-Fi credentials, VPN peers or keys, application
payloads, and private endpoints were not inspected or copied.

No configuration, service state, firewall rule, or network link was changed.
No packet capture, network scan, DNS benchmark, or throughput test was run.
Selected privileged reads used `sudo -n`; their reports retain policy and
counter values rather than raw rules, addresses, or journal contents.

## Conclusions and priorities

There is no confirmed network or background-service performance bottleneck
in this evidence. The useful decisions concern network capabilities,
inbound exposure, and future workload isolation. None requires an emergency
performance workaround.

| ID | Finding | Priority and decision |
| --- | --- | --- |
| NS-01 | IPv6 is disabled on loopback and both physical network interfaces | P2 capability decision: determine whether this restriction still matches development and VPN requirements |
| NS-02 | The inspected netfilter state has no host input filtering, while KDE Connect listens on a wildcard TCP socket | P2 exposure decision: define behavior on untrusted networks; no demonstrated compromise or Internet reachability |
| NS-03 | NetworkManager manages a functional LAN resolver configuration without an observed host caching daemon | P3 optional improvement: local caching or split DNS only if a measured problem or VPN requirement warrants it |
| NS-04 | The Ethernet adapter supports 2.5 Gb/s but currently negotiates 1 Gb/s | P3 conditional opportunity: verify the peer and physical path if faster LAN transfers matter |
| NS-05 | User workloads and the two running containers have no explicit memory budgets | P3 preventive choice: constrain particular heavy workloads when needed; no current OOM or limit-pressure evidence |
| NS-06 | Three retained Wi-Fi activation failures concern credentials or network discovery | P3 monitor if recurrent: current connectivity and driver evidence do not justify wireless tuning |

## Healthy baseline

| Area | Observed state | Interpretation |
| --- | --- | --- |
| NetworkManager | Connected, full connectivity; Ethernet and Wi-Fi managed and connected | No current availability failure |
| Default IPv4 routes | Ethernet metric 100; Wi-Fi metric 600 | Wired traffic is preferred; Wi-Fi remains available for undocking |
| Ethernet | `igc`, 1,000 Mb/s, full duplex, autonegotiation enabled, MTU 1,500 | Coherent link configuration |
| Wi-Fi | `iwlwifi`, 5 GHz, approximately -56 dBm, power saving enabled | No weak-signal diagnosis from this snapshot |
| Link errors | Zero RX/TX errors on both physical interfaces | No observed physical-interface error accumulation |
| Ethernet queues | `mq` with `fq` children; zero reported qdisc drops and backlog | No sampled transmit-queue congestion |
| TCP policy | `bbr` congestion control and `fq`; receive-buffer autotuning enabled | Existing policy is coherent; no comparative speed claim |
| Time | `systemd-timesyncd` enabled and active; NTP synchronized | Keep current single active time client |
| Service state | No failed system or user units | No failed-unit cleanup to perform |
| Resource pressure | Sampled memory PSI zero; inspected cgroup OOM and pids-limit events zero | No evidence supporting emergency memory tuning |

Both connected physical links are useful on a laptop. Disabling Wi-Fi merely
because Ethernet is present would remove an existing fallback. The three
observed IPv4 policy-routing rules use the standard local/main/default
tables; no custom policy-routing conflict was identified in that snapshot.

The Wi-Fi transmit rate reported approximately 1,021 Mb/s with an 80 MHz
HE connection. Its reported receive rate was 6 Mb/s. These are recent frame
rates, not a throughput measurement; the receive number does not establish
a download-speed cap. Wi-Fi power saving should remain enabled unless an
actual latency or reconnect problem is reproduced under controlled conditions.

Cumulative link-drop counters were small but nonzero: Ethernet had two
transmit drops; Wi-Fi had 32 receive and 35 transmit drops. Their lifetime
and traffic context do not establish an active fault. Selected TCP counters
showed zero listen overflows, listen drops, and input errors. Retransmissions
and timeouts were present, but cumulative counts across ordinary network
changes do not identify packet-loss rate or a local tuning defect.

## NS-01: broad IPv6 disablement restricts the workstation

The inventory explicitly sets `disable_ipv6=1` for `all`, `default`, and
`lo`. Runtime inspection also verified the value on loopback, Ethernet,
Wi-Fi, and the Docker bridge. This conclusion does not rely on reading
`all.disable_ipv6` alone: the kernel documents that this value is not a
reliable summary of every interface. Disabling an interface's IPv6 support
removes its IPv6 addresses and routes.
[Kernel IP sysctl documentation](https://www.kernel.org/doc/html/latest/networking/ip-sysctl.html)

This is a real functionality restriction, including normal `::1` loopback
use and host dual-stack testing. It may be intentional, but no measured
performance gain or observed application failure supports it in this audit.
Separate container network namespaces were not inspected, so the observation
does not prove that every container has the same setting.

Recommended decision: keep it only as an explicit requirement. If IPv6
development, an IPv6-only network, or a VPN requires it, review loopback and
per-network policy together with the inbound-exposure decision below. A
future change belongs in the privileged system layer and should be checked
on wired, wireless, and relevant VPN connections. No enablement was applied.

## NS-02: Docker forwarding rules do not define host exposure

The effective nftables inspection found Docker NAT and forwarding chains,
an IPv4 `FORWARD` drop policy, an empty `DOCKER-USER` chain, and no host input
hook. Neither firewalld nor nftables service was active. Service inactivity
alone is not the basis of the finding: the active rules were inspected.

Installed `iptables` reports the `nf_tables` backend. Legacy table interfaces
were absent from `/proc/net`, and the inspected module list contained no
registered legacy IPv4/IPv6 filter-table modules. Thus no separate active
legacy ruleset was indicated by those checks. This is consistent with
[Arch's iptables backend transition](https://archlinux.org/news/iptables-now-defaults-to-the-nft-backend/).

The socket snapshot found `kdeconnectd` listening on wildcard TCP port 1716,
with additional UDP sockets. Other identified TCP listeners were loopback
bound. This makes host exposure a policy question; it does not establish
Internet reachability, router forwarding, an exploitable service, or failed
KDE Connect authentication. Device communication is an intentional
[KDE Connect feature](https://kdeconnect.kde.org/).

If this laptop joins untrusted networks, a narrowly defined host input
policy would make the intended exposure explicit. Preserve required local
device discovery and pairing on trusted networks. Do not disable KDE Connect
or install a second rule manager merely to reduce the listener count.

Docker's forwarding chains handle a different traffic path from host input.
Its default forwarding policy can matter when the laptop must route traffic
between a VPN, LAN, or container network. It is not evidence that ordinary
host VPN client traffic is broken. Docker currently uses the iptables
compatibility path backed by nftables; this should not be confused with
Docker's separate native nftables backend.
[Docker firewall documentation](https://docs.docker.com/engine/network/packet-filtering-firewalls/)

A WireGuard interface exists but was not active in NetworkManager and had
zero traffic counters in the snapshot. Its peers, endpoints, keys, and
connection profile were not inspected. No claim about its intended usage
or end-to-end behavior follows from an idle interface.

## NS-03: DNS is functional; local caching is an optional design choice

`/etc/resolv.conf` is a regular NetworkManager-generated file containing one
private LAN nameserver and one search domain. Their values are deliberately
omitted. `systemd-resolved` is disabled and inactive. No active `dnsmasq`,
`unbound`, `named`, `dnsconfd`, or `nscd` service was found.

The NSS hosts sequence includes `resolve [!UNAVAIL=return]` and later `dns`.
An unavailable resolved service permits fallback, so its inactive status
does not by itself make this setup broken. The observed ownership matches
NetworkManager's default resolver-management model; selected configuration
keys contained no explicit alternative DNS plugin.
[NetworkManager configuration reference](https://networkmanager.dev/docs/api/latest/NetworkManager.conf.html)

No host caching daemon was observed, but applications and the LAN resolver
may cache independently. No latency test was performed, and the upstream
resolver's encrypted-transport or DNSSEC behavior was not inspected. It
would be incorrect to infer slow DNS or absent validation from this file.

If recurring lookup latency or VPN split-DNS behavior becomes a real issue,
`systemd-resolved` is a reasonable local caching and routing option. Such a
change must coordinate NetworkManager's DNS plugin, `resolv.conf` ownership,
and VPN routing-domain tests. Replacing the LAN server with a public resolver
without understanding local names can reduce functionality. There is no
evidence requiring that migration now.

## NS-04 and NS-06: physical networking observations

The Ethernet adapter advertises 2.5 Gb/s capability but has negotiated
1 Gb/s. Its link partner's advertised capabilities were not exposed by the
read-only query. The limiting component might be a 1 Gb/s switch port,
the peer configuration, or the physical path; no specific cause was proven.
If high-throughput NAS or LAN transfers matter, confirm both endpoints and
the path before changing software. Increasing TCP buffers cannot turn this
negotiated link into 2.5 Gb/s.

The retained NetworkManager records contained three activation failures:

| UTC time | Sanitized reason | What it establishes |
| --- | --- | --- |
| 2026-09-02 08:08:14 | `no-secrets` | The activation did not obtain required authentication material; no credential contents were inspected |
| 2026-09-05 01:30:22 | `ssid-not-found` | The requested wireless network was not found for that attempt |
| 2026-09-05 01:30:49 | `ssid-not-found` | A second discovery failure occurred 27 seconds later |

These reasons can arise from ordinary connection availability or an
uncompleted authentication interaction. Retained kernel searches since
2026-08-29 found no matching iwlwifi microcode-crash pattern or igc
hang/timeout/error pattern. There is no present basis for forcing another
driver, disabling wireless power saving globally, or changing channel width.
If the same failure recurs while the access point is known to be available,
collect the narrow event sequence then; profiles and secrets are unnecessary
for that first diagnostic step.

## NS-05: resource controls are permissive, without current pressure

The system service slice accounted for approximately 0.9 GiB and 148 tasks;
the active user slice accounted for approximately 21.9 GiB and 2,420 tasks.
These are cgroup charges, including file cache, not sums of private resident
application memory. User and system slices had no CPU quota or explicit
memory maximum. The user's task ceiling was 168,688, with zero recorded
ceiling hits. Sampled memory-pressure and OOM-event counters were also zero.

The two running containers had no explicit memory, CPU, or process-count
limits in the selected configuration fields. No names, environment values,
mount contents, or application settings were read. Unbounded resources are
Docker's default behavior; an individual runaway workload could therefore
compete with the desktop.
[Docker resource constraints](https://docs.docker.com/engine/containers/resource_constraints/)

`systemd-oomd` was disabled and inactive; earlyoom was absent. The inspected
slices used `ManagedOOMSwap=auto` and `ManagedOOMMemoryPressure=auto`. The
kernel OOM mechanism remains available. No retained OOM-kill pattern was
found, so this is not evidence that current memory handling is failing.

Recommended decision: apply a deliberate budget to an actually problematic
container or build workload before adding a global early-kill policy. Cgroup
memory limits are hierarchical; systemd distinguishes a pressure threshold
from a hard maximum. Enabling systemd-oomd also introduces proactive process
group termination and requires deliberate group boundaries.
[Systemd resource-control reference](https://raw.githubusercontent.com/systemd/systemd/main/man/systemd.resource-control.xml)
and [systemd-oomd reference](https://raw.githubusercontent.com/systemd/systemd/main/man/systemd-oomd.service.xml)

The inventory's PAM `nofile` and `nproc` values of 65,535 coexist with
different system-manager defaults and cgroup task ceilings. Those are
different enforcement layers, not necessarily configuration drift. No
observed descriptor or task-limit failure justifies raising them globally.

## Background services: no useful blanket-disable list

The running services have recognizable purposes: networking, Bluetooth,
Thunderbolt authorization, containers, desktop login, storage discovery,
time, hardware policy, and logging. Their presence alone does not demonstrate
a performance problem.

| Service | Approximate cgroup memory | Relevant qualification |
| --- | --- | --- |
| SDDM | 161 MiB | About 131 MiB was file cache; anonymous memory was about 28 MiB |
| Docker | 143 MiB | Daemon accounting; workload resource budgets are a separate decision |
| Cronie | 93 MiB | About 78 MiB was file cache and only 0.8 MiB anonymous memory |
| containerd | 88 MiB | Supports the active container runtime |
| fwupd | 47 MiB | Audit queries can activate the service; this is not an idle-only baseline |
| TuneD | 46 MiB | Desktop/power policy is examined in the power reports |
| atop | 33 MiB | Monitoring and retention are deliberate observability choices |
| NetworkManager | 27 MiB | Manages both active physical connections |
| systemd-timesyncd | 2.7 MiB | Synchronized; no competing active time daemon |
| irqbalance | 1.5 MiB | No measured workload regression establishes a reason to disable it |

Cumulative service CPU counters were modest, but they are not utilization
rates and were not used to promise an improvement. In particular, disabling
Cronie or SDDM based on their total cgroup memory would misread file-cache
accounting as daemon bloat.

IPv4 forwarding is enabled, consistent with Docker. Reverse-path filtering
is loose (`2`) on both physical interfaces even though the `all` value is
zero; the effective setting uses the maximum of the applicable values.
This avoids incorrectly reporting reverse-path filtering as universally
disabled. Existing PMTU discovery and TCP receive autotuning remain enabled.
[Kernel IP sysctl documentation](https://www.kernel.org/doc/html/latest/networking/ip-sysctl.html)

No broad network sysctl bundle, replacement network manager, extra resolver,
blanket service disablement, or global workload limit is justified by this
snapshot. The report closes the available static investigation; physical
throughput, application DNS latency, and VPN operation require a relevant
workload or controlled reproduction rather than additional configuration
guessing.
