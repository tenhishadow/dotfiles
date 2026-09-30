# Development follow-up investigation

Measured on 2026-09-05. This closes the development investigation from the
first pass with isolated measurements, tested proposals, and package
classification. Original dotfiles and system settings remain unchanged.

## Results

Replacing four eager completion generators with packaged deferred loading
reduced the tested shell fragment from 167.92 ms to 17.65 ms median: about
150 ms less work per initialization in this experiment. This is a credible,
specific responsiveness improvement; it is not a measurement of total Kitty
startup or the user's complete interactive shell.

A further defect was reproduced: the managed go-task completion fragment
registers the command name `task`, while this machine uses `go-task`. A tested
deferred completion file fixes the registration and avoids its startup-time
generation. The executable local shell override could compensate for this in
existing sessions; its contents were excluded from inspection.

The 112 orphan candidates occupy approximately 2.941 GiB according to local
package metadata. Most reclaimable space to review is concentrated in browser
runtimes and detached debug symbols. There is no evidence that removing these
inactive packages will improve application execution speed.

## Measurement boundary and method

Each probe ran in Bubblewrap with a new network and process namespace. The
visible host filesystem consisted of read-only `/usr`, the dynamic-loader
cache, and a read-only disposable fixture inside this audit directory. Host
home directories, root's files, credentials, and desktop state were absent.
The environment was cleared; `HOME` was neither set nor repurposed. Explicit
XDG and tool-specific paths pointed into the isolated fixture. There was no
writable host mount or network access.
[Bubblewrap isolation model](https://github.com/containers/bubblewrap).

Shell probes used `/usr/bin/bash --noprofile --norc` with reviewed fragments.
They did not source the real `.bashrc`, start an interactive editor, load
`.env`, contact a Kubernetes cluster, or run a package operation. Temporary
fixtures were created beneath this audit directory and removed afterward;
only this report is retained.

Each timing has three discarded warm-up executions followed by 15 measured
executions using Python's monotonic performance counter. P90 is the 14th
sorted observation. Times include process and sandbox startup; the true/empty
Bash controls expose that overhead. Samples were warm and sequential on the
otherwise active workstation, without dropping caches or controlling CPU
frequency. Individual tool timings should not be added together to predict
full-shell startup.

| Probe | Median, ms | P90, ms |
| --- | ---: | ---: |
| Sandbox plus `true` | 6.29 | 7.37 |
| Sandbox plus empty Bash | 6.90 | 8.92 |
| `gh completion -s bash` | 54.74 | 62.10 |
| `kubectl completion bash` | 70.17 | 82.32 |
| `docker completion bash` | 20.52 | 23.04 |
| `helm completion bash` | 43.30 | 49.00 |
| `go-task --completion bash` | 55.80 | 59.82 |
| Packaged bash-completion initialization | 19.01 | 20.88 |
| Framework plus four current eager generators | 167.92 | 183.44 |
| Framework plus deferred `k` wrapper | 17.65 | 19.87 |

The small difference between the last proposal and framework-only control is
measurement variation, not an optimization introduced by adding a wrapper.
All measured commands returned success without stderr output.

Relevant installed versions: bash-completion 2.18.0, kubectl 1.36.4, Helm
4.2.2, GitHub CLI 2.99.0, Docker 29.7.2, go-task 3.53.1, Bubblewrap 0.12.0,
Ruff 0.16.5, and Lua 5.5.1. These identify the tested implementations; package
databases were not refreshed.

## Tested configuration proposals

The snippets below are reviewable proposals, not applied changes. They replace
the corresponding managed fragments rather than adding another initialization
layer. The shell's legitimate Starship, direnv, fzf, and Kitty integration
remain outside the proposed completion change.

### Deferred completion with the Kubernetes alias retained

Replace the four explicit generator calls and their framework initialization
in `dotfiles/.bashrc` with this fragment, keeping the existing `k=kubectl`
alias. Installed command completion files then load on demand. The small alias
adapter uses bash-completion's existing `_comp_xfunc` helper, available in the
installed version; it loads the packaged kubectl completion when first needed.
[bash-completion 2.18.0 implementation](https://github.com/scop/bash-completion/blob/2.18.0/bash_completion).

```bash
if [[ ! ${BASH_COMPLETION_VERSINFO:-} &&
      -r /usr/share/bash-completion/bash_completion ]]; then
  source /usr/share/bash-completion/bash_completion
fi

if declare -F _comp_xfunc >/dev/null; then
  _dotfiles_complete_k() {
    _comp_xfunc kubectl __start_kubectl "$@"
  }
  complete -o default -F _dotfiles_complete_k k
fi
```

Semantic checks passed: kubectl's completion function was absent before the
first alias completion, loaded when needed, and returned the expected candidate
using a stubbed kubectl command. Packaged gh, Docker, and Helm completion
registrations also loaded successfully. No cluster-aware completion was called.

The helper is version-sensitive outside this Arch environment. Before applying
to the repository's supported non-Arch hosts, retain the existing portability
contract and verify their bash-completion versions. This does not prevent
reviewing or using the tested Arch proposal.

### DV-08: Correct and defer go-task completion registration

With only the current managed fragment loaded, `complete -p go-task` failed
while `complete -p task` returned `complete -F _task task`. The generated
upstream script assigns `TASK_CMD="${TASK_EXE:-task}"`; the input setting is
`TASK_EXE`, not `TASK_CMD`.
[Task 3.53.1 Bash completion source](https://github.com/go-task/task/blob/v3.53.1/completion/bash/task.bash).

The installed go-task package supplies no completion file. A native deferred
file at the user bash-completion location can contain one line:

```bash
TASK_EXE=go-task eval "$(go-task --completion bash)"
```

If approved, add the new relative path `bash-completion/completions/go-task`
under the existing `dotfiles/.local/share/` payload directory, linked by a new
`dotfiles_mapping` entry to the corresponding user data path. Remove the eager
completion generator for Task from `.bashrc` when adding that mapping. No generic command
cache or background updater is needed.

The disposable test proved `_task` was absent before loading, the loader
registered `complete -F _task go-task`, and completing
`go-task --output g` returned `group`. That test uses the completion script's
local flag-value branch and does not parse or execute a Taskfile. The roughly
56 ms isolated generation cost moves to first use; a full-shell saving from
this additional change was not measured.

### Preserve update failure status and separate cache policy

Replace the `archupdate` alias with this function in the managed Bash file:

```bash
unalias archupdate 2>/dev/null || :
archupdate() {
  command yay -Syu "$@"
}
```

This retains the package manager's confirmation behavior by default, accepts
explicit caller flags, and returns the upgrade's exit status. The `unalias`
also handles reloading a shell that still contains the previous alias.
Two tests used a disposable executable named `yay`, not the real package
manager: exit statuses 0 and 37 were preserved, arguments remained
`-Syu --needed`, and exactly one invocation occurred in each test.

Keep retention as an explicit separate maintenance policy, for example retaining
three pacman package versions with paccache and reviewing AUR build-cache
retention separately. No cleanup command was run. As established by the
matching source analysis in [the first development report](03-development.md),
noninteractive full-cache confirmation differs between pacman and yay; the old
alias must not be described as an unconditional pacman-cache wipe.

### Use the repository's Python formatter once

This repository declares Ruff in `pyproject.toml`, configures it in
`.ruff.toml`, and validates formatting with Ruff in its existing task. No
Black configuration was found in those repository configuration sources.
For this contract, the concrete formatter entry is:

```lua
python = { "ruff_format" },
```

It replaces the Python entry in
`dotfiles/.config/nvim/lua/config/languages.lua`. A disposable modified copy
loaded successfully with plain Lua, exposing only Ruff for Python and
preserving the existing Go chain. This did not start Neovim or its plugins.

Four synthetic Python fixtures were formatted through stdin with the repository
Ruff configuration and caching disabled. Ruff was idempotent in all four;
passing the results through Black made no further change in those fixtures.
This supports eliminating the duplicate pass for the tested contract. It does
not establish equivalence for all Python syntax or other projects.
[Conform formatter sequencing](https://github.com/stevearc/conform.nvim#setup),
[Ruff's Black compatibility](https://docs.astral.sh/ruff/formatter/#black-compatibility).

The inventory is shared by all projects. A Black-owned project should select
Black explicitly; do not infer project policy from whichever formatter happens
to be installed. No personal projects were scanned. Keep formatting manual and
validate the actual editor integration with the repository's isolated Neovim
checks only when an implementation is approved.

### Remove ineffective Git-core tuning claims

The installed `git help --config` index recognizes `pack.threads`,
`core.commitGraph`, `core.untrackedCache`, and `core.preloadIndex`; it does not
recognize `gc.threads` or `diff.parallel`. Read the managed file without its
external include when inspecting these settings.

The narrow proposal is to remove only `gc.threads=8` and `diff.parallel=8`
unless an external consumer is identified. Keep the supported settings.
No speed increase is claimed from removing ignored settings, and no additional
Git tuning is justified by these measurements.
[Git configuration reference](https://git-scm.com/docs/git-config).

## Classification of the 112 orphan candidates

The following categories are exhaustive and non-overlapping. Sizes come from
installed-package metadata, not a scan of personal directories. One empty debug
package lacks a raw size field; pacman reports it as 0 B, and it is counted.

| Category | Count | Installed size, MiB | Recommended disposition |
| --- | ---: | ---: | --- |
| Browser/Electron runtimes | 5 | 1490.03 | Review first: CEF and Electron 37/38/39/40; keep any explicitly used runtime |
| Detached debug symbols | 42 | 994.58 | Review first; retain symbols for active debugging and crash investigation |
| Build tools, headers, documentation generators | 14 | 459.69 | Keep pending project/build ownership review; pacman dependencies do not represent every AUR build requirement |
| Older Qt/KDE and account integration | 12 | 35.25 | Review legacy application/plugin needs; low disk benefit |
| Other libraries and utilities | 16 | 21.61 | Review individually; includes useful direct tools such as qpdf |
| Python modules and test/build helpers | 15 | 5.06 | Keep until consumers are identified; very little space is at stake |
| Haskell compatibility libraries | 6 | 3.47 | Low-priority review against retained Haskell tooling |
| Font families | 2 | 2.05 | Keep unless deliberately changing installed fonts |
| Total | 112 | 3011.75 | No removal authorized or performed |

The first two categories account for about 2.43 GiB, or 82.5% of the total.
The largest individual debug packages are build2 (417.71 MiB), terraformer
(116.64 MiB), and botan2 (101.19 MiB). Their presence consumes disk without
establishing CPU or memory usage by the applications.

Within the build group, Clang 21 occupies 222.60 MiB and Boost headers
151.16 MiB. `/usr/bin/clang` is owned by Clang 22.1.8, so Clang 21 is an
additional version rather than the current default compiler. It may still be
needed by explicitly versioned build commands. Fonts and small libraries offer
too little benefit to justify speculative cleanup.

`pacman -Qdtq` identifies packages installed as dependencies that are no longer
required or optionally required by installed package metadata. It does not
identify user intent, manually linked binaries, or unrecorded build needs.
Mark deliberately retained direct-use tools explicit during a future approved
maintenance change; do not remove the whole list mechanically.
[Pacman query and install-reason semantics](https://pacman.archlinux.page/pacman.8.html).

## Settings ownership and runtime writers

| Surface | Effective owner or writer | Concrete management decision |
| --- | --- | --- |
| Bash startup, Kitty, Starship, Neovim source | Repository payload through sampled live symlinks | Make future changes in canonical payloads; avoid editing a second live copy |
| Final shell override | Executable local `.bashrc.d/.env`, intentionally unread | Keep secrets local; move only reviewed non-secret performance settings into the managed layer |
| Neovim plugin commits | Lockfile, explicit Lazy operations, enabled daily restore | Retain current convergence policy unless deliberate manual checkouts need persistence |
| Neovim lockfile | Linked repository file; explicit Lazy update can write it | Treat plugin updates as source changes subject to review |
| LSP/tool selection | Primarily Arch binaries; Mason defaults off | Keep one declared owner per tool rather than introducing another runtime manager |
| Checkov | pipx-managed virtual environment | Existing isolation is useful; its Python 3.14 interpreter target exists |
| goimports | Binary in the user's Go bin directory | Record it as intentionally Go-managed or move ownership to a selected package workflow in a separate approved change |
| gofumpt | Not found in the audit PATH although listed before other Go formatters | Decide whether its stricter formatting is actually desired; its absence alone does not justify installation |
| Git includes | Managed file plus an external project include | Limit this proposal to the managed keys; the external project file was not inspected |

No new daemon, filesystem tuning, compiler replacement, package installation,
or background shell cache is needed for the measured completion improvement.
The remaining unobserved boundary is full interactive behavior with the user's
local override, real projects, and desktop session. The tested proposals are
ready for review without crossing that boundary or applying configuration.
