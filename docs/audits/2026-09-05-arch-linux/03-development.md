# Development environment audit

This is a first-pass snapshot. The [current audit index](README.md) and
[completed read-only decisions](10-read-only-conclusions.md) include later
measurements, resolved access gaps, and corrected interpretations.

Observed on 2026-09-05. Scope: the managed shell, Kitty, Neovim,
development tools, Docker, selected resource limits, and local package
metadata. This is a read-only assessment; recommendations are unapplied.
No interactive shell, editor, build, package refresh, container, or benchmark
was started for this audit.

## Assessment

The development environment has a solid baseline. The sampled live dotfiles
are linked to their repository sources, language runtimes resolve primarily
to Arch packages, installed Neovim plugin commits match the lockfile, and
Docker uses an efficient supported storage configuration. No critical
development-runtime fault or measured system-wide performance bottleneck was
established.

The first workflow improvement is explicit update results and cache policy. The most direct
performance experiment is shell startup: several completion generators run
eagerly despite installed completion files. Python formatting also performs
two overlapping formatter passes. These are more concrete opportunities than
rebuilding the toolchain or raising more kernel limits.

Priorities below mean: P1 = address before relying on the affected workflow;
P2 = focused correction or measurement; P3 = optional maintenance. Confidence
describes the evidence, not the size of a possible speedup.

## Evidence and strengths

| Area | Observed state | Interpretation |
| --- | --- | --- |
| Live configuration | Bash startup files, Kitty configuration, Starship, Neovim entry point/Lua/lockfile, and environment.d file resolve to this repository | No drift at these sampled link destinations |
| Runtime selection | Go, Rust, Cargo, Python, Node, npm, Neovim, and primary LSP binaries resolve under `/usr/bin` in the audit process | No competing runtime manager established |
| Optional managers | No GVM startup script or user Cargo/Rust compiler shim at the checked paths; Mason mode is unset and defaults off | Dormant manager support is not evidence of double initialization |
| Python tooling | Checkov resolves into its own pipx virtual environment | Isolation from system Python packages is already present |
| Neovim | 48 lock entries; all 43 installed plugin repositories have matching HEAD commits | Missing entries are four opt-in Mason plugins and the legacy EditorConfig plugin; their absence is consistent with configuration gates |
| Editor background work | Manual formatting, file-local save linting, optional external tools, disabled unused remote providers | Existing safeguards reduce avoidable editor work |
| Docker | `overlay2`, extfs backing, `Supports d_type=true`, `Native Overlay Diff=true`, metacopy disabled | No slow compatibility fallback was reported |
| Docker resource model | systemd cgroup driver, cgroup v2; two containers running at observation | Native systemd integration is already effective |
| Limits | Open files/processes 65,535 in audit process; inotify watches 524,288; instances 8,192; `vm.max_map_count=1048576` | No evidence that larger limits would improve current performance |
| Pacman | `CheckSpace`, `DownloadUser=alpm`, required package signatures; 20 parallel downloads | Important package-manager safeguards are present |

Selected package versions from the local database were Bash 5.3.15, Kitty
0.48.2, Neovim 0.12.5, Starship 1.26.0, uv 0.12.9, Python 3.14.7, Go 1.27.0,
Rust 1.98.0, Node LTS 22.23.2, and Docker 29.7.2. These observations do not
claim that local packages equal the latest remote repository state.

## Findings

### DV-01: The update alias couples upgrades to conditional cache cleanup

**P2, confirmed configuration and upstream control flow; execution history not inspected.**

The live-linked `dotfiles/.bashrc` defines `archupdate` as
`yay -Syu --noconfirm; yay -Scc --noconfirm`. The semicolon invokes cleanup
regardless of the upgrade exit status; the final cleanup status can also mask
an upgrade failure. However, `--noconfirm` does not mean yes to every question.
Installed pacman is `7.1.0.r9.g54d9411-2`: its matching source uses `noyes` for
complete cache deletion. `noyes` supplies a false default and noninteractive
confirmation returns that default, so full pacman package-cache deletion is
declined by this command.
[Pacman cleanup source](https://gitlab.archlinux.org/pacman/pacman/-/blob/54d9411/src/pacman/sync.c),
[Pacman confirmation source](https://gitlab.archlinux.org/pacman/pacman/-/blob/54d9411/src/pacman/util.c).

Yay 13.0.1 handles its AUR build cache differently: its full-clean question
supplies a true default, which `--noconfirm` accepts if that branch is reached.
In the normal combined repository/AUR mode, it first checks for a valid pacman
cache directory and returns early if none exists. Thus the alias is not an
unconditional full-cache wipe; its results differ by cache type and state.
[Yay 13.0.1 cleanup source](https://github.com/Jguer/yay/blob/v13.0.1/clean.go),
[Yay confirmation source](https://github.com/Jguer/yay/blob/v13.0.1/pkg/text/input.go).

`pacman-conf CacheDir` reports `/var/cache/pacman/pkg/`; that directory was
absent in the system audit. The cause was not determined, and the absence does
not establish that the user ran this alias. With the observed directory state,
the ordinary combined-mode cleanup path returns before AUR cleanup too.

Recommended follow-up: separate upgrade review from cache maintenance and
retain a small number of package versions using the existing ecosystem tool
`paccache`. Review AUR build-cache retention separately. Replacing `;` with
`&&` fixes success gating but does not make the two cache policies equivalent.
The expected benefit is recoverability and less repeated downloading, not
faster steady-state CPU execution.
[Upstream paccache implementation](https://github.com/archlinux/pacman-contrib/blob/master/src/paccache.sh.in).

Validation after approval: inspect the resulting shell command expansion,
exercise failure handling and both confirmation defaults using stub commands,
and confirm cache retention on disposable fixtures. Rollback is the previous
alias. No cleanup command was executed during this audit.

### DV-02: Every interactive shell generates completions already installed

**P2, confirmed redundant startup work; latency unmeasured.**

`dotfiles/.bashrc` starts `gh completion`, `kubectl completion`,
`docker completion`, and `helm completion` during initialization. Local package
file lists confirm matching completion files in
`/usr/share/bash-completion/completions/`. The installed framework documents
that these files load on demand.
[bash-completion upstream](https://github.com/scop/bash-completion).

Other startup work includes the Starship/direnv hooks, go-task completion,
Checkov argument completion, and many separate `tput` calls. Hooks that update
the prompt or directory environment have a real purpose; they should not be
removed simply because they execute commands. The custom Git prompt runs only
as a fallback when Starship is unavailable, so it is not a second active Git
prompt in the observed setup.

Recommended follow-up: first profile startup in a sanitized temporary home,
then use one guarded bash-completion initialization and package-provided
on-demand completions for the four confirmed duplicates. Preserve CLI alias
completion, especially `k`, and test login and non-login interactive shells.
Do not promise a millisecond gain before measurement.

An executable local `.bashrc.d/.env` is sourced last. Its existence was checked
without reading it. It can change PATH and hooks, so the current report cannot
attribute every interactive-shell behavior exclusively to repository code.

### DV-03: Python manual formatting runs Ruff and Black sequentially

**P2, confirmed execution configuration; output conflict not reproduced.**

`dotfiles/.config/nvim/lua/config/languages.lua` maps Python to
`{ "ruff_format", "black" }`. Both commands are installed and available in
the audit PATH. Conform runs such a list sequentially unless
`stop_after_first` or explicit selection changes it; it is not a fallback
list. Manual formatting therefore has two overlapping formatter stages.
[Conform configuration](https://github.com/stevearc/conform.nvim#setup).

Ruff aims for Black compatibility but documents intentional differences.
Select the project's formatter explicitly, or express an actual fallback.
This can remove work and avoid the second formatter undoing the first
formatter's stylistic decisions. No actual formatting conflict was observed.
[Ruff formatter compatibility](https://docs.astral.sh/ruff/formatter/#black-compatibility).

The issue affects an explicit `:Format` invocation, not every save. Keep the
existing manual-only formatting contract. Validate on disposable representative
Python files, including project-specific formatter settings, and inspect the
selected formatter list. Rollback is the previous Python formatter entry in
`dotfiles/.config/nvim/lua/config/languages.lua`.

### DV-04: A daily task deliberately restores plugin revisions

**P2 visibility item, confirmed scheduled behavior; not an unexplained fault.**

The user crontab contains the managed daily Neovim restore job, and Cronie is
active. The job uses `flock`, sets `NVIM_USE_MASON=off`, and calls
`lazy.restore`. Inventory explicitly enables it in
`inventory/host_vars/this_host/dotfiles.yml`.

This is a known writer to the runtime plugin tree: a manual plugin checkout
that disagrees with the lockfile can be restored on the next scheduled run.
Lazy's documented restore behavior is to return plugins to lockfile revisions.
There was no installed plugin HEAD drift in the sampled state.
[Lazy command semantics](https://lazy.folke.io/usage).

The lockfile itself is linked to the repository. An intentional `Lazy update`
can also update that source file. These ownership paths explain where changes
can come from; no evidence established arbitrary background overwriting of
the shell or editor configuration.

Keep daily convergence if it is wanted. If plugin experimentation is common,
consider explicit restore after configuration changes instead. Test a plugin
revision change only in an isolated Neovim data tree. The live cron job was
not executed and its runtime log was not read.

### DV-05: The local package set has a measurable maintenance backlog

**P3, confirmed metadata; no demonstrated runtime performance penalty.**

The local pacman database lists 3,118 installed packages, 150 foreign packages,
and 112 unrequired dependency packages from `pacman -Qdtq`. Forty-two of those
orphans are debug packages. The combined installed-size metadata for all 112
orphans is about 2.94 GiB, including build2 debug symbols, CEF, Clang 21, and Electron majors
37 through 40.

Foreign means absent from the configured sync databases, not automatically
malicious, unsupported, or originally installed from the AUR. Orphan status
also does not prove a binary is never used directly by the user.
[Pacman query semantics](https://pacman.archlinux.page/pacman.8.html).

Recommended follow-up: review this short cleanup set and mark intentionally
used tools explicit before any removal. Debug packages and older toolchains
may still support useful debugging/build workflows. Removing unused packages
reclaims disk and reduces maintenance; it does not speed up inactive code.

The checked makepkg configuration already uses optimized generic compilation,
LTO/debug defaults, and multithreaded zstd compression. Neither ccache nor mold
is installed. Add build caching or a different linker only if a representative
native-code build shows repeated compilation/linking dominates elapsed time.
This audit provides no basis for rebuilding Arch packages globally.

### DV-06: Kitty keeps generous history and overrides its terminal identity

**P3, confirmed configuration; current resource pressure not established.**

The live-linked Kitty file sets 100,000 scrollback lines, a 1,024 MB pager
history ceiling, and `term xterm-256color`. Upstream warns that very large
interactive scrollback can increase memory use and slow terminal operation;
history memory is allocated on demand. One running Kitty process used about
156 MiB RSS at observation. A configured ceiling is not committed memory.
[Kitty scrollback options](https://sw.kovidgoyal.net/kitty/conf/#scrollback).

Keep the generous history if useful. If long-running build/log tabs feel slow,
compare a smaller interactive history while preserving the pager. Separately,
review the global TERM override: Kitty's default describes its capabilities as
`xterm-kitty`. Test a return to the default with local TUIs and the user's SSH
destinations before changing it. No broken key sequence was reproduced.
[Kitty TERM option](https://sw.kovidgoyal.net/kitty/conf/#opt-kitty.term).

### DV-07: Two apparent Git tuning settings have no documented core effect

**P3, confirmed absence from the installed Git configuration index.**

The managed Git configuration sets `gc.threads=8` and `diff.parallel=8`.
Neither key appears in installed `git help --config`; upstream documents
`pack.threads`, which is separately configured here. Do not count the two
unrecognized keys as demonstrated Git-core parallelization. An external tool
could consume arbitrary configuration keys, but no such consumer was found
in this review.
[Git configuration reference](https://git-scm.com/docs/git-config).

No performance edit is urgent. Keep supported settings, remove misleading
ones if their intended consumer cannot be identified, and benchmark Git on a
representative large repository before adding fsmonitor or more tuning.

## Docker interpretation and remaining opportunities

The daemon's selected JSON settings agree with the managed template:
systemd cgroups, journald logs, ten concurrent downloads, five uploads, and
container default `nofile=1048576`. The daemon itself has a different inherited
open-file limit, 524,288; that is a separate process limit, not configuration
drift. `live-restore` is false, which is an availability choice to review if
local containers need to survive daemon maintenance, not a throughput fix.

The retained seven-day journal query returned 323 priority-error records
attributed to `docker.service`. Every record carried container metadata.
They must not be reported as 323 Docker daemon failures. Journald's Docker
driver writes container stdout/stderr with container identifiers; metadata
must distinguish workload output from engine failures. Raw messages and
container identifiers are not included in this report.
[Docker journald driver](https://docs.docker.com/engine/logging/drivers/journald/).

For a later workload-specific review, examine build cache reuse and whether
write-heavy data belongs in a volume instead of the container writable layer.
Docker documents volumes as the more predictable choice for such writes.
No container contents, mounts, credentials, environment, or application
configuration were inspected, so misplaced write-heavy data is a hypothesis.
Do not migrate storage drivers or enable overlay features merely to tune an
already functioning native diff path.
[Docker OverlayFS performance](https://docs.docker.com/engine/storage/drivers/overlayfs-driver/#overlayfs-and-docker-performance).

## Follow-up tasks suitable for an independent agent

| Task | Bounded deliverable | Acceptance criterion |
| --- | --- | --- |
| Shell latency | Profile a sanitized copy of the managed Bash startup, compare package completion loading, and inspect the last-mile local override with user-controlled redaction | Median and tail startup times, preserved completion behavior, no production shell/environment tracing |
| Update recoverability | Prepare a small alias/cache-retention proposal; classify relevant `.pacnew` differences | Reviewable unapplied diff, failure-path check, explicit retained rollback versions |
| Editor behavior | Verify Python formatter selection and Helm-values LSP attachment in disposable fixtures | One intended Python formatter path; client list and diagnostic ownership recorded before suggesting LSP changes |
| Package ownership | Review 112 orphan candidates and foreign package provenance from local metadata | Human-reviewable keep/remove list, disk saving estimate, no bulk removal |
| Build performance | Select one representative build, separate dependency download/compile/link time, compare existing caching | Repeatable timings and an identified dominant stage before selecting ccache, mold, or flags |

Helm-values files are configured for both standalone YAML and Helm LSP
attachment, with Helm's embedded YAML support enabled when available. This may
be intentional because the services provide different features. Runtime client
attachment and overlapping diagnostics were not observed; do not classify it
as proven duplicate work from configuration alone.

## Limits and source quality

Credential files, shell history, full process command lines, process
environments, cloud/Kubernetes account data, local `.env` contents, and editor
runtime logs were excluded. Package queries used existing local metadata only.
No package integrity or security-advisory sweep was performed. Toolchain PATH
observations describe the audit process, not every existing GUI/editor process.

Direct ArchWiki requests for Bash, Pacman, and Pacnew/Pacsave were blocked by
the site's automated-traffic challenge. Their contents were not treated as
verified. The report instead cites reachable official Arch manuals and owning
upstream documentation, corroborated with installed configuration and metadata.
No source-dependent performance percentage is claimed.
